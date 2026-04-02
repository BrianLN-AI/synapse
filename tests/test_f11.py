#!/usr/bin/env python3
"""
tests/test_f11.py — f_11 goal/okr + capability bootstrap + GOKR execution

Covers:
  - goal/okr StaticAnalysis: valid blob passes, missing fields rejected
  - promote_okr: manifest updated, audit event written
  - _mutation_goal_from_okr: gap detection, all-met case, objective in goal
  - _derive_mutation_goal: OKR-driven when goal/okr promoted, fallback otherwise
  - bootstrap_capability: manifest populated with logic/contract/okr/test entries
  - evolve_one: uses OKR-derived goal when goal/okr present in manifest
  - run_all: discovers capability labels from manifest (not hardcoded)
  - Full f_11 evolution cycle: manifest v1.11.0
  - Credential safety: no CF strings in vault or audit log
"""

import json
import shutil
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
# goal/okr StaticAnalysis
# ---------------------------------------------------------------------------

_VALID_OKR = json.dumps({
    "for_label":   "planning",
    "objective":   "Select the highest-quality blob with the lowest operational cost",
    "key_results": [
        {"metric": "success_rate", "target": 0.95, "direction": "above"},
        {"metric": "avg_latency_ms", "target": 2.0, "direction": "below"},
        {"metric": "volatility", "target": 0.3, "direction": "below"},
    ],
    "supersedes": None,
})


def test_goal_okr_passes_static_analysis() -> None:
    section("goal/okr — valid blob passes StaticAnalysis")
    h = seed.put("goal/okr", _VALID_OKR)
    try:
        promote.triple_pass_review(h)
        check("valid goal/okr passes", True)
    except promote.ReviewError as e:
        check("valid goal/okr passes", False, str(e))


def test_goal_okr_rejects_missing_for_label() -> None:
    section("goal/okr — rejects missing for_label")
    bad = json.dumps({"objective": "x", "key_results": [
        {"metric": "success_rate", "target": 0.9, "direction": "above"}]})
    h = seed.put("goal/okr", bad)
    try:
        promote.triple_pass_review(h)
        check("rejects missing for_label", False)
    except promote.ReviewError:
        check("rejects missing for_label", True)


def test_goal_okr_rejects_empty_objective() -> None:
    section("goal/okr — rejects empty objective")
    bad = json.dumps({"for_label": "planning", "objective": "",
                      "key_results": [{"metric": "m", "target": 1.0, "direction": "above"}]})
    h = seed.put("goal/okr", bad)
    try:
        promote.triple_pass_review(h)
        check("rejects empty objective", False)
    except promote.ReviewError:
        check("rejects empty objective", True)


def test_goal_okr_rejects_invalid_direction() -> None:
    section("goal/okr — rejects invalid direction in key_result")
    bad = json.dumps({"for_label": "planning", "objective": "obj",
                      "key_results": [{"metric": "m", "target": 1.0, "direction": "sideways"}]})
    h = seed.put("goal/okr", bad)
    try:
        promote.triple_pass_review(h)
        check("rejects invalid direction", False)
    except promote.ReviewError:
        check("rejects invalid direction", True)


def test_goal_okr_rejects_missing_target() -> None:
    section("goal/okr — rejects non-numeric target")
    bad = json.dumps({"for_label": "planning", "objective": "obj",
                      "key_results": [{"metric": "m", "target": "high", "direction": "above"}]})
    h = seed.put("goal/okr", bad)
    try:
        promote.triple_pass_review(h)
        check("rejects non-numeric target", False)
    except promote.ReviewError:
        check("rejects non-numeric target", True)


# ---------------------------------------------------------------------------
# promote_okr
# ---------------------------------------------------------------------------

def test_promote_okr_updates_manifest() -> None:
    section("promote_okr — manifest['blobs']['planning']['goal/okr'] set")
    h = seed.put("goal/okr", _VALID_OKR)
    evolve_reviewer_hash = _boot.get("evolve_reviewer_hash", "")
    approval = promote.issue_council_approval([h], reviewer_hash=evolve_reviewer_hash)
    promote.promote_okr("planning", h, approval)

    m = promote.load_manifest()
    stored = m.get("blobs", {}).get("planning", {}).get("goal/okr")
    check("goal/okr in manifest", stored == h)


def test_promote_okr_writes_audit_event() -> None:
    section("promote_okr — audit event written")
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    okr_events = [e for e in entries if e.get("event") == "promote_okr"]
    check("promote_okr audit event present", len(okr_events) >= 1)


# ---------------------------------------------------------------------------
# _mutation_goal_from_okr
# ---------------------------------------------------------------------------

def test_mutation_goal_from_okr_identifies_gaps() -> None:
    section("_mutation_goal_from_okr — identifies gap metrics")
    okr = json.loads(_VALID_OKR)
    # success_rate below target (0.95), latency above target (2.0)
    signals = {"success_rate": 0.70, "avg_latency_ms": 5.0, "volatility": 0.1}
    goal = evolve._mutation_goal_from_okr("planning", okr, signals)
    check("success_rate gap in goal", "success_rate" in goal)
    check("avg_latency_ms gap in goal", "avg_latency_ms" in goal)
    check("objective verbatim in goal", "lowest operational cost" in goal)


def test_mutation_goal_from_okr_all_met() -> None:
    section("_mutation_goal_from_okr — all key results met → robustness goal")
    okr = json.loads(_VALID_OKR)
    signals = {"success_rate": 0.99, "avg_latency_ms": 1.0, "volatility": 0.1}
    goal = evolve._mutation_goal_from_okr("planning", okr, signals)
    check("all-met goal non-empty", len(goal) > 10)
    check("mentions robustness", "robustness" in goal.lower() or "all key results met" in goal.lower())


# ---------------------------------------------------------------------------
# _derive_mutation_goal — OKR vs fallback
# ---------------------------------------------------------------------------

def test_derive_mutation_goal_uses_okr_when_promoted() -> None:
    section("_derive_mutation_goal — uses OKR goal when goal/okr in manifest")
    # goal/okr was promoted in test_promote_okr_updates_manifest
    signals = {"success_rate": 0.70, "avg_latency_ms": 5.0, "volatility": 0.1}
    goal = evolve._derive_mutation_goal("planning", signals)
    # OKR goal should include the objective text
    check("OKR objective in derived goal", "lowest operational cost" in goal or
          "key result" in goal.lower() or "success_rate" in goal)


def test_derive_mutation_goal_falls_back_without_okr() -> None:
    section("_derive_mutation_goal — falls back to signal-threshold without OKR")
    # Use a label with no goal/okr in manifest
    signals = {"success_rate": 0.70, "avg_latency_ms": 5.0, "volatility": 0.1}
    goal = evolve._derive_mutation_goal("discovery", signals)
    # Should still produce a goal (threshold-based)
    check("fallback goal non-empty", len(goal) > 10)


# ---------------------------------------------------------------------------
# bootstrap_capability
# ---------------------------------------------------------------------------

_SUMMARIZER_BLOB = """\
document  = context.get("document", "")
max_words = context.get("max_words", 100)
words     = document.split()[:max_words]
result    = {"summary": " ".join(words), "word_count": len(words)}
"""

_SUMMARIZER_CONTRACT = json.dumps({
    "for_label": "summarizer",
    "pre":  "def pre(c):\n    return isinstance(c.get('document', ''), str)",
    "post": "def post(c, r):\n    return isinstance(r, dict) and 'summary' in r",
})

_SUMMARIZER_OKR = json.dumps({
    "for_label": "summarizer",
    "objective": "Produce concise, accurate summaries within the word limit",
    "key_results": [
        {"metric": "success_rate",   "target": 0.95, "direction": "above"},
        {"metric": "avg_latency_ms", "target": 5.0,  "direction": "below"},
    ],
    "supersedes": None,
})


def test_bootstrap_capability_registers_label() -> None:
    section("bootstrap_capability — registers summarizer in manifest")
    blob_h     = seed.put("logic/python",        _SUMMARIZER_BLOB)
    contract_h = seed.put("contract/definition", _SUMMARIZER_CONTRACT)
    okr_h      = seed.put("goal/okr",            _SUMMARIZER_OKR)

    evolve_reviewer_hash = _boot.get("evolve_reviewer_hash", "")
    approval = promote.issue_council_approval(
        [blob_h, contract_h, okr_h], reviewer_hash=evolve_reviewer_hash
    )
    promote.bootstrap_capability("summarizer", contract_h, okr_h, blob_h, approval)

    m = promote.load_manifest()
    entry = m.get("blobs", {}).get("summarizer", {})
    check("logic/python in manifest",        entry.get("logic/python") == blob_h)
    check("contract/definition in manifest", entry.get("contract/definition") == contract_h)
    check("goal/okr in manifest",            entry.get("goal/okr") == okr_h)
    check("test/case initialized as list",   isinstance(entry.get("test/case"), list))


def test_bootstrap_capability_audit_event() -> None:
    section("bootstrap_capability — audit event written")
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    bc_events = [e for e in entries if e.get("event") == "bootstrap_capability"]
    check("bootstrap_capability audit event present", len(bc_events) >= 1)
    if bc_events:
        check("audit event has label=summarizer",
              bc_events[-1].get("label") == "summarizer")


# ---------------------------------------------------------------------------
# run_all — discovers capability labels
# ---------------------------------------------------------------------------

def test_run_all_includes_capability_labels() -> None:
    section("run_all — discovers summarizer capability label from manifest")
    # summarizer is now in manifest from test_bootstrap_capability_registers_label
    _iu = infer.InferenceUnavailable("mocked")
    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f11-run",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f11-run",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f11-run",
        _SUMMARIZER_BLOB:           _SUMMARIZER_BLOB + "\n# f11-run",
    }
    def _mock_gen(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f11-run")

    with mock.patch("infer.generate_candidate", side_effect=_mock_gen), \
         mock.patch("infer.generate_test_cases", side_effect=_iu), \
         mock.patch("promote.run_test_suite", return_value=[]):
        results = evolve.run_all()

    labels_evolved = {r["label"] for r in results}
    check("summarizer label evolved", "summarizer" in labels_evolved)
    check("discovery label evolved",  "discovery" in labels_evolved)
    check("planning label evolved",   "planning" in labels_evolved)
    check("at least one promoted",    any(r["outcome"] == "promoted" for r in results))


# ---------------------------------------------------------------------------
# Full f_11 evolution cycle — manifest v1.11.0
# ---------------------------------------------------------------------------

def test_full_f11_evolution_cycle() -> None:
    section("Full f_11 evolution cycle — GOKR execution, manifest v1.11.0")
    _iu = infer.InferenceUnavailable("mocked")
    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f11-cycle",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f11-cycle",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f11-cycle",
        _SUMMARIZER_BLOB:           _SUMMARIZER_BLOB + "\n# f11-cycle",
    }
    def _mock_gen(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        # OKR goal should be used for labels with goal/okr in manifest
        return _v8_variants.get(current_payload, current_payload + "\n# f11-cycle")

    def _mock_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "probe"}]

    with mock.patch("infer.generate_candidate", side_effect=_mock_gen), \
         mock.patch("infer.generate_test_cases", side_effect=_mock_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        results = evolve.run_all()

    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.13.0", m["version"] == "1.13.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        check(f"{label} logic blob present", m["blobs"].get(label, {}).get("logic/python") is not None)
    check("summarizer logic blob present", m["blobs"].get("summarizer", {}).get("logic/python") is not None)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v11 = [e for e in entries if e.get("event") == "promote" and e.get("version") == "1.13.0"]
    check("at least one v1.13.0 promote event", len(promote_v11) >= 1)


# ---------------------------------------------------------------------------
# Credential safety
# ---------------------------------------------------------------------------

def test_no_credentials_in_vault_post_evolution() -> None:
    section("Credential safety — no CF credentials in vault post-evolution")
    found = False
    for blob_path in seed.VAULT_DIR.iterdir():
        if not blob_path.is_file():
            continue
        content = blob_path.read_text(errors="replace")
        if any(cred in content for cred in _CF_CREDENTIAL_STRINGS):
            found = True
            break
    check("no CF credentials in vault", not found)


def test_no_credentials_in_audit_log_post_evolution() -> None:
    section("Credential safety — no CF credentials in audit.log post-evolution")
    text = Path("./audit.log").read_text()
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

    # goal/okr StaticAnalysis
    test_goal_okr_passes_static_analysis()
    test_goal_okr_rejects_missing_for_label()
    test_goal_okr_rejects_empty_objective()
    test_goal_okr_rejects_invalid_direction()
    test_goal_okr_rejects_missing_target()

    # promote_okr
    test_promote_okr_updates_manifest()
    test_promote_okr_writes_audit_event()

    # _mutation_goal_from_okr
    test_mutation_goal_from_okr_identifies_gaps()
    test_mutation_goal_from_okr_all_met()

    # _derive_mutation_goal
    test_derive_mutation_goal_uses_okr_when_promoted()
    test_derive_mutation_goal_falls_back_without_okr()

    # bootstrap_capability
    test_bootstrap_capability_registers_label()
    test_bootstrap_capability_audit_event()

    # run_all
    test_run_all_includes_capability_labels()

    # Full cycle
    test_full_f11_evolution_cycle()

    # Credential safety
    test_no_credentials_in_vault_post_evolution()
    test_no_credentials_in_audit_log_post_evolution()

    total   = len(_results)
    passing = sum(1 for _, ok in _results if ok)
    print(f"\n{'─' * 40}")
    print(f"  {passing}/{total} passed")
    if passing < total:
        raise SystemExit(1)
