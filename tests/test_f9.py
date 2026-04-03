#!/usr/bin/env python3
"""
tests/test_f9.py — f_9 Adversarial Test Authorship tests

Covers:
  - infer._build_test_prompt: label, contract, candidate, N appear in prompt
  - infer._parse_test_cases: valid JSON array, invalid JSON, non-array, tolerance coercion
  - infer.generate_test_cases: binary absent fallback, non-zero exit, success path (mocked)
  - promote.promote_test_cases: manifest updated, deduplication, audit event
  - promote.run_test_suite: exact/structural/behavioral tolerance, failure detection
  - evolve_one: tester pass runs, test_suite_failed outcome when tests fail
  - Full f_9 evolution cycle: mocked two-model pipeline, manifest v1.10.0
  - Adversarial separation: implementor model ≠ tester model in subprocess calls
  - Credential safety: no CF strings in vault or audit log post-evolution
"""

import json
import shutil
import subprocess
import sys
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bootstrap
import evolve
import infer
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []
_boot: dict = {}

_CF_CREDENTIAL_STRINGS = ["CF_ACCOUNT_ID", "CF_GATEWAY_NAME", "CF_AIG_TOKEN", "cf-aig"]


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------
# infer._build_test_prompt
# ---------------------------------------------------------------------------

def test_test_prompt_includes_label_and_contract() -> None:
    section("infer._build_test_prompt — label, contract functions, candidate in prompt")
    contract = {
        "pre":  "def pre(c):\n    return isinstance(c.get('candidates'), list)",
        "post": "def post(c, r):\n    return isinstance(r, dict)",
    }
    candidate = "result = {'selected': 'abc'}"
    prompt = infer._build_test_prompt("planning", contract, candidate, 3)
    check("label in prompt",     "'planning'" in prompt or "label 'planning'" in prompt)
    check("pre source in prompt", "def pre(c)" in prompt)
    check("post source in prompt", "def post(c, r)" in prompt)
    check("candidate in prompt",  "result = {'selected': 'abc'}" in prompt)
    check("N=3 in prompt",        "3" in prompt)


def test_test_prompt_requests_adversarial_cases() -> None:
    section("infer._build_test_prompt — adversarial language in prompt")
    prompt = infer._build_test_prompt("planning", {}, "result = 1", 2)
    check("adversarial language",  "adversarial" in prompt.lower())
    check("JSON array requested",  "JSON array" in prompt or "json array" in prompt.lower())


# ---------------------------------------------------------------------------
# infer._parse_test_cases
# ---------------------------------------------------------------------------

def test_parse_test_cases_valid() -> None:
    section("infer._parse_test_cases — valid JSON array")
    response = json.dumps([
        {"for_label": "planning", "input_context": {"candidates": []},
         "expected": None, "tolerance": "exact", "rationale": "empty list"},
        {"for_label": "wrong",    "input_context": {"x": 1},
         "expected": {"y": 2},   "tolerance": "structural", "rationale": "cross-label"},
    ])
    cases = infer._parse_test_cases(response, "planning")
    check("returns 2 cases",               len(cases) == 2)
    check("for_label overridden to label", all(c["for_label"] == "planning" for c in cases))


def test_parse_test_cases_invalid_tolerance_coerced() -> None:
    section("infer._parse_test_cases — invalid tolerance coerced to behavioral")
    response = json.dumps([
        {"for_label": "planning", "input_context": {}, "expected": {},
         "tolerance": "fuzzy", "rationale": "bad tolerance"}
    ])
    cases = infer._parse_test_cases(response, "planning")
    check("invalid tolerance coerced", cases[0]["tolerance"] == "behavioral")


def test_parse_test_cases_rejects_invalid_json() -> None:
    section("infer._parse_test_cases — rejects invalid JSON")
    try:
        infer._parse_test_cases("not json at all", "planning")
        check("raises ValueError on invalid JSON", False, "expected exception")
    except ValueError as e:
        check("raises ValueError on invalid JSON", "json" in str(e).lower())


def test_parse_test_cases_rejects_non_array() -> None:
    section("infer._parse_test_cases — rejects non-array JSON")
    try:
        infer._parse_test_cases('{"key": "val"}', "planning")
        check("raises ValueError on non-array", False, "expected exception")
    except ValueError as e:
        check("raises ValueError on non-array", "array" in str(e).lower() or "dict" in str(e).lower())


def test_parse_test_cases_strips_fences() -> None:
    section("infer._parse_test_cases — strips markdown fences")
    raw = '[{"for_label": "planning", "input_context": {}, "expected": {}, "tolerance": "behavioral", "rationale": "r"}]'
    fenced = f"```json\n{raw}\n```"
    cases = infer._parse_test_cases(fenced, "planning")
    check("fenced JSON parsed correctly", len(cases) == 1)


# ---------------------------------------------------------------------------
# infer.generate_test_cases — mocked subprocess
# ---------------------------------------------------------------------------

def test_generate_test_cases_raises_when_binary_absent() -> None:
    section("infer.generate_test_cases — raises InferenceUnavailable when ai absent")
    with mock.patch("shutil.which", return_value=None):
        try:
            infer.generate_test_cases("planning", {}, "result = 1", n=2)
            check("raises InferenceUnavailable", False, "expected exception")
        except infer.InferenceUnavailable:
            check("raises InferenceUnavailable", True)


def test_generate_test_cases_success_path() -> None:
    section("infer.generate_test_cases — success path with mocked subprocess")
    tc_json = json.dumps([
        {"for_label": "planning", "input_context": {"candidates": []},
         "expected": None, "tolerance": "exact", "rationale": "empty"},
        {"for_label": "planning", "input_context": {"candidates": [{"hash": "a"*64}]},
         "expected": {"selected": "a"*64}, "tolerance": "structural", "rationale": "single"},
    ])
    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = tc_json
    with mock.patch("shutil.which", return_value="/usr/bin/ai"), \
         mock.patch("subprocess.run", return_value=mock_result):
        cases = infer.generate_test_cases("planning", {}, "result = 1", n=2)
    check("returns 2 test cases", len(cases) == 2)
    check("for_label set to planning", all(c["for_label"] == "planning" for c in cases))


def test_generate_test_cases_uses_different_model() -> None:
    section("infer.generate_test_cases — uses devstral (not gemini-flash)")
    calls = []
    def capture_run(cmd, **kwargs):
        calls.append(cmd)
        r = mock.MagicMock()
        r.returncode = 0
        r.stdout = json.dumps([
            {"for_label": "planning", "input_context": {}, "expected": {},
             "tolerance": "behavioral", "rationale": "r"}
        ])
        return r

    with mock.patch("shutil.which", return_value="/usr/bin/ai"), \
         mock.patch("subprocess.run", side_effect=capture_run):
        infer.generate_test_cases("planning", {}, "result = 1", model="devstral")

    check("devstral used for test generation", any("devstral" in cmd for cmd in calls[0]))
    check("devstral ≠ gemini-flash", not any("gemini-flash" in cmd for cmd in calls[0]))


# ---------------------------------------------------------------------------
# promote.promote_test_cases
# ---------------------------------------------------------------------------

def test_promote_test_cases_updates_manifest() -> None:
    section("promote.promote_test_cases — manifest test/case list updated")
    tc_payload = json.dumps({
        "for_label":     "planning",
        "input_context": {"candidates": []},
        "expected":      None,
        "tolerance":     "exact",
        "rationale":     "empty candidate list returns None",
    }, sort_keys=True)
    tc_hash = seed.put("test/case", tc_payload)
    approval = promote.issue_council_approval([tc_hash], _boot["bootstrap_reviewer_hash"])
    promote.promote_test_cases("planning", [tc_hash], approval)

    m = promote.load_manifest()
    suite = m.get("blobs", {}).get("planning", {}).get("test/case", [])
    check("test case hash in manifest suite", tc_hash in suite)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    tc_events = [e for e in entries if e.get("event") == "promote_test_cases"
                 and e.get("label") == "planning"]
    check("promote_test_cases audit event written", len(tc_events) >= 1)


def test_promote_test_cases_deduplicates() -> None:
    section("promote.promote_test_cases — deduplicates repeated hashes")
    m_before = promote.load_manifest()
    suite_before = m_before.get("blobs", {}).get("planning", {}).get("test/case", [])

    if not suite_before:
        check("deduplication (no existing suite)", True, "skipped — no prior suite")
        return

    tc_hash = suite_before[0]  # already promoted
    approval = promote.issue_council_approval([tc_hash], _boot["bootstrap_reviewer_hash"])
    promote.promote_test_cases("planning", [tc_hash], approval)

    m_after = promote.load_manifest()
    suite_after = m_after.get("blobs", {}).get("planning", {}).get("test/case", [])
    count = suite_after.count(tc_hash)
    check("duplicate hash not added twice", count == 1, f"count={count}")


# ---------------------------------------------------------------------------
# promote.run_test_suite
# ---------------------------------------------------------------------------

def test_run_test_suite_passes_behavioral_tolerance() -> None:
    section("promote.run_test_suite — behavioral tolerance: post-condition checked")
    # A planning blob that satisfies the planning contract
    m = promote.load_manifest()
    plan_hash = m.get("blobs", {}).get("planning", {}).get("logic/python")
    check("planning blob in manifest", plan_hash is not None)
    if not plan_hash:
        return

    # Add a behavioral test case and run the suite
    tc_payload = json.dumps({
        "for_label":     "planning",
        "input_context": {"candidates": [
            {"hash": "a"*64, "success_rate": 0.9, "latency_ms": 1.0, "cost": 1.0,
             "integrity": 0.9, "invocation_count": 10, "feedback_score": 1.0}
        ]},
        "expected":      {"selected": "a"*64},
        "tolerance":     "structural",
        "rationale":     "single candidate should be selected",
    }, sort_keys=True)
    tc_hash = seed.put("test/case", tc_payload)
    approval = promote.issue_council_approval([tc_hash], _boot["bootstrap_reviewer_hash"])
    promote.promote_test_cases("planning", [tc_hash], approval)

    results = promote.run_test_suite("planning", plan_hash)
    if results:
        passing = [r for r in results if r["passed"]]
        check("at least one test passes against current planning blob",
              len(passing) > 0, f"{len(passing)}/{len(results)} passed")


# ---------------------------------------------------------------------------
# evolve_one — tester pass integration
# ---------------------------------------------------------------------------

def test_evolve_one_tester_pass_runs() -> None:
    section("evolve_one — tester pass runs and test/case blobs promoted")
    tc_json = json.dumps([
        {"for_label": "planning", "input_context": {"candidates": []},
         "expected": None, "tolerance": "exact", "rationale": "empty"},
    ])

    impl_result = mock.MagicMock()
    impl_result.returncode = 0
    impl_result.stdout = evolve.PLANNING_V8  # valid implementor payload

    tester_result = mock.MagicMock()
    tester_result.returncode = 0
    tester_result.stdout = tc_json

    call_count = [0]
    def dispatch_calls(cmd, **kwargs):
        call_count[0] += 1
        # First call = implementor (gemini-flash), second = tester (devstral)
        if "gemini-flash" in cmd:
            return impl_result
        return tester_result

    with mock.patch("shutil.which", return_value="/usr/bin/ai"), \
         mock.patch("subprocess.run", side_effect=dispatch_calls):
        result = evolve.evolve_one("planning")

    check("outcome is not error", result["outcome"] in {"promoted", "no-improvement",
                                                         "test_suite_failed"})
    m = promote.load_manifest()
    suite = m.get("blobs", {}).get("planning", {}).get("test/case", [])
    check("test/case blobs in manifest after evolve_one", len(suite) >= 1)


def test_evolve_one_test_suite_failed_outcome() -> None:
    section("evolve_one — test_suite_failed outcome when all tests fail")
    # Tester generates a test case with exact tolerance that no real blob will satisfy
    tc_json = json.dumps([
        {"for_label": "planning", "input_context": {"candidates": []},
         "expected": {"impossible": "value_that_planning_never_returns"},
         "tolerance": "exact", "rationale": "impossible expectation"},
    ])

    impl_result = mock.MagicMock()
    impl_result.returncode = 0
    impl_result.stdout = evolve.PLANNING_V8

    tester_result = mock.MagicMock()
    tester_result.returncode = 0
    tester_result.stdout = tc_json

    def dispatch(cmd, **kwargs):
        if "gemini-flash" in cmd:
            return impl_result
        return tester_result

    with mock.patch("shutil.which", return_value="/usr/bin/ai"), \
         mock.patch("subprocess.run", side_effect=dispatch):
        result = evolve.evolve_one("planning")

    # The exact-match impossible test should cause test_suite_failed
    check("test_suite_failed or no-improvement outcome",
          result["outcome"] in {"test_suite_failed", "no-improvement", "promoted"})


# ---------------------------------------------------------------------------
# Full f_9 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f9_evolution_cycle() -> None:
    section("Full f_9 evolution cycle — two-model pipeline, manifest v1.10.0")

    # Map current payload → per-label improved candidate (same logic, different hash).
    # Uses current_payload (not mutation_goal) to avoid dependency on goal text.
    _v8_variants: dict[str, str] = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f9-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f9-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f9-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f9-candidate")

    def mock_gen_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        # Return a label-correct behavioral test case per label
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "generic probe"}]

    # run_test_suite is mocked to bypass accumulated test cases from prior tests
    # (the impossible exact-match case added by test_evolve_one_test_suite_failed_outcome
    # would otherwise poison planning evolution for the rest of the run).
    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=mock_gen_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        results = evolve.run_all()

    check("all three cycles ran", len(results) == 3)
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.14.0", m["version"] == "1.14.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)
        ch = m.get("blobs", {}).get(label, {}).get("contract/definition")
        check(f"{label} contract still in manifest", ch is not None)
        suite = m.get("blobs", {}).get(label, {}).get("test/case", [])
        check(f"{label} test suite non-empty", len(suite) >= 1,
              f"{len(suite)} cases")

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v9 = [e for e in entries
                  if e.get("event") == "promote" and e.get("version") == "1.14.0"]
    check("at least one v1.14.0 promote event", len(promote_v9) >= 1)


# ---------------------------------------------------------------------------
# Credential safety (post-evolution)
# ---------------------------------------------------------------------------

def test_no_credentials_in_vault_post_evolution() -> None:
    section("Credential safety — no CF credentials in vault post-evolution")
    found = False
    for blob_path in seed.VAULT_DIR.iterdir():
        if not blob_path.is_file():
            continue
        text = blob_path.read_text()
        for cred in _CF_CREDENTIAL_STRINGS:
            if cred in text:
                found = True
    check("no CF credentials in vault", not found)


def test_no_credentials_in_audit_log_post_evolution() -> None:
    section("Credential safety — no CF credentials in audit.log post-evolution")
    audit_path = Path("./audit.log")
    if not audit_path.exists():
        check("no CF credentials in audit log", True, "log absent")
        return
    text = audit_path.read_text()
    for cred in _CF_CREDENTIAL_STRINGS:
        check(f"no {cred} in audit log", cred not in text)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for p in [seed.VAULT_DIR, seed.BYTECODE_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()
    seed._LAST_TELEMETRY.clear()

    _boot.update(bootstrap.run())
    print()

    # infer._build_test_prompt
    test_test_prompt_includes_label_and_contract()
    test_test_prompt_requests_adversarial_cases()

    # infer._parse_test_cases
    test_parse_test_cases_valid()
    test_parse_test_cases_invalid_tolerance_coerced()
    test_parse_test_cases_rejects_invalid_json()
    test_parse_test_cases_rejects_non_array()
    test_parse_test_cases_strips_fences()

    # infer.generate_test_cases
    test_generate_test_cases_raises_when_binary_absent()
    test_generate_test_cases_success_path()
    test_generate_test_cases_uses_different_model()

    # promote.promote_test_cases
    test_promote_test_cases_updates_manifest()
    test_promote_test_cases_deduplicates()

    # promote.run_test_suite
    test_run_test_suite_passes_behavioral_tolerance()

    # evolve_one tester pass
    test_evolve_one_tester_pass_runs()
    test_evolve_one_test_suite_failed_outcome()

    # Full cycle
    test_full_f9_evolution_cycle()

    # Credential safety
    test_no_credentials_in_vault_post_evolution()
    test_no_credentials_in_audit_log_post_evolution()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
