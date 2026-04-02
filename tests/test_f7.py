#!/usr/bin/env python3
"""
tests/test_f7.py — f_7 Design-by-Contract tests
Covers: contract/definition blob type, Pass 6 ContractCompliance, promote_contract(),
        bootstrap contracts for core blobs, v8 mutations, post-condition violation
        detection, test/case blob type, full f_7 evolution cycle, manifest v1.10.0.
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


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------

def test_bootstrap_promotes_contracts() -> None:
    section("bootstrap — contract/definition blobs promoted for all three core labels")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        ch = m.get("blobs", {}).get(label, {}).get("contract/definition")
        check(f"{label} contract in manifest", ch is not None and len(ch) == 64,
              f"hash={ch[:16] if ch else None}")
        if ch:
            blob = seed._raw_get(ch)
            check(f"{label} contract blob type is contract/definition",
                  blob["type"] == "contract/definition")
            record = json.loads(blob["payload"])
            check(f"{label} contract for_label matches", record["for_label"] == label)

    # Audit log must have promote_contract events for all three
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    contract_events = [e for e in entries if e.get("event") == "promote_contract"]
    check("three promote_contract events in audit log", len(contract_events) >= 3)


def test_contract_static_analysis_valid() -> None:
    section("Pass 1 — valid contract/definition passes StaticAnalysis")
    payload = json.dumps({
        "for_label": "test-blob",
        "pre":  "def pre(context):\n    return True",
        "post": "def post(context, result):\n    return result is not None",
    }, sort_keys=True)
    ch = seed.put("contract/definition", payload)
    try:
        blob = promote.triple_pass_review(ch)
        check("valid contract passes triple_pass_review", blob["type"] == "contract/definition")
    except promote.ReviewError as e:
        check("valid contract passes triple_pass_review", False, str(e))


def test_contract_static_analysis_rejects_missing_for_label() -> None:
    section("Pass 1 — rejects contract/definition without for_label")
    payload = json.dumps({
        "pre":  "def pre(context):\n    return True",
        "post": "def post(context, result):\n    return True",
    }, sort_keys=True)
    ch = seed.put("contract/definition", payload)
    try:
        promote.triple_pass_review(ch)
        check("rejects missing for_label", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects missing for_label",
              e.pass_name == "StaticAnalysis" and "for_label" in str(e).lower())


def test_contract_static_analysis_rejects_syntax_error_in_pre() -> None:
    section("Pass 1 — rejects contract/definition with syntax error in pre function")
    payload = json.dumps({
        "for_label": "test-blob",
        "pre":  "def pre(context):\n    return !!!",  # syntax error
        "post": "def post(context, result):\n    return True",
    }, sort_keys=True)
    ch = seed.put("contract/definition", payload)
    try:
        promote.triple_pass_review(ch)
        check("rejects syntax error in pre", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects syntax error in pre",
              e.pass_name == "StaticAnalysis" and "pre" in str(e).lower())


def test_contract_compliance_pass_satisfied() -> None:
    section("Pass 6 ContractCompliance — valid blob satisfies its contract")
    # Promote a contract for a test label
    contract_payload = json.dumps({
        "for_label": "compliance-test",
        "pre":  "def pre(context):\n    return 'x' in context",
        "post": "def post(context, result):\n    return isinstance(result, int)",
    }, sort_keys=True)
    ch = seed.put("contract/definition", contract_payload)
    evolve_hash = _boot.get("evolve_reviewer_hash", "")
    approval = promote.issue_council_approval([ch], _boot["bootstrap_reviewer_hash"])
    promote.promote_contract("compliance-test", ch, approval)

    # A logic blob that satisfies the contract
    logic_payload = "result = len(context.get('x', ''))"
    lh = seed.put("logic/python", logic_payload)
    try:
        promote.triple_pass_review(lh, label="compliance-test")
        check("satisfying blob passes ContractCompliance", True)
    except promote.ReviewError as e:
        check("satisfying blob passes ContractCompliance", False, str(e))


def test_contract_compliance_catches_violation() -> None:
    section("Pass 6 ContractCompliance — detects post-condition violation")
    # Contract: post requires result is a dict
    contract_payload = json.dumps({
        "for_label": "violation-test",
        "pre":  "def pre(context):\n    return True",
        "post": "def post(context, result):\n    return isinstance(result, dict)",
    }, sort_keys=True)
    ch = seed.put("contract/definition", contract_payload)
    approval = promote.issue_council_approval([ch], _boot["bootstrap_reviewer_hash"])
    promote.promote_contract("violation-test", ch, approval)

    # A logic blob that returns a string (violates the dict post-condition)
    logic_payload = 'result = "not a dict"'
    lh = seed.put("logic/python", logic_payload)
    try:
        promote.triple_pass_review(lh, label="violation-test")
        check("post-condition violation detected", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("post-condition violation detected",
              e.pass_name == "ContractCompliance" and "post-condition" in str(e).lower())


def test_contract_compliance_no_contract_is_noop() -> None:
    section("Pass 6 ContractCompliance — no-op when no contract is promoted for label")
    # Any logic blob with a label that has no promoted contract — should pass fine
    lh = seed.put("logic/python", "result = 'no-contract'")
    try:
        promote.triple_pass_review(lh, label="label-with-no-contract")
        check("no contract = no-op (backward compatible)", True)
    except promote.ReviewError as e:
        check("no contract = no-op (backward compatible)", False, str(e))


def test_promote_contract_updates_manifest() -> None:
    section("promote_contract — manifest['blobs'][label]['contract/definition'] updated")
    contract_payload = json.dumps({
        "for_label": "promote-test",
        "pre":  "def pre(context):\n    return True",
        "post": "def post(context, result):\n    return True",
    }, sort_keys=True)
    ch = seed.put("contract/definition", contract_payload)
    approval = promote.issue_council_approval([ch], _boot["bootstrap_reviewer_hash"])
    manifest_hash = promote.promote_contract("promote-test", ch, approval)

    check("promote_contract returns manifest hash", len(manifest_hash) == 64)
    m = promote.load_manifest()
    stored = m.get("blobs", {}).get("promote-test", {}).get("contract/definition")
    check("contract hash in manifest", stored == ch)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    contract_events = [e for e in entries
                       if e.get("event") == "promote_contract"
                       and e.get("label") == "promote-test"]
    check("promote_contract audit event written", len(contract_events) >= 1)


def test_promote_contract_rejects_wrong_for_label() -> None:
    section("promote_contract — rejects contract whose for_label mismatches target label")
    contract_payload = json.dumps({
        "for_label": "label-A",
        "pre":  "def pre(context):\n    return True",
        "post": "def post(context, result):\n    return True",
    }, sort_keys=True)
    ch = seed.put("contract/definition", contract_payload)
    approval = promote.issue_council_approval([ch], _boot["bootstrap_reviewer_hash"])
    try:
        promote.promote_contract("label-B", ch, approval)
        check("rejects for_label mismatch", False, "expected ValueError")
    except ValueError as e:
        check("rejects for_label mismatch", "does not match" in str(e))


def test_test_case_blob_static_analysis_valid() -> None:
    section("test/case blob — valid blob passes StaticAnalysis")
    payload = json.dumps({
        "for_label":     "planning",
        "input_context": {"candidates": [{"hash": "a"*64, "success_rate": 0.9,
                                          "latency_ms": 1.0, "cost": 1.0}]},
        "expected":      {"selected": "a"*64},
        "tolerance":     "structural",
        "rationale":     "single-candidate planning selects the only candidate",
    }, sort_keys=True)
    th = seed.put("test/case", payload)
    try:
        blob = promote.triple_pass_review(th)
        check("valid test/case passes triple_pass_review", blob["type"] == "test/case")
    except promote.ReviewError as e:
        check("valid test/case passes triple_pass_review", False, str(e))


def test_test_case_blob_rejects_invalid_tolerance() -> None:
    section("test/case blob — rejects invalid tolerance value")
    payload = json.dumps({
        "for_label":     "planning",
        "input_context": {},
        "tolerance":     "fuzzy",  # not in {exact, structural, behavioral}
    }, sort_keys=True)
    th = seed.put("test/case", payload)
    try:
        promote.triple_pass_review(th)
        check("rejects invalid tolerance", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects invalid tolerance",
              e.pass_name == "StaticAnalysis" and "tolerance" in str(e).lower())


def test_planning_contract_satisfied_by_bootstrap_blob() -> None:
    section("Planning contract — bootstrap planning blob satisfies promoted contract")
    m = promote.load_manifest()
    plan_hash = m.get("blobs", {}).get("planning", {}).get("logic/python")
    check("planning blob in manifest", plan_hash is not None)
    if plan_hash:
        try:
            promote.triple_pass_review(plan_hash, label="planning")
            check("bootstrap planning blob satisfies planning contract", True)
        except promote.ReviewError as e:
            check("bootstrap planning blob satisfies planning contract", False, str(e))


def test_discovery_contract_satisfied_by_bootstrap_blob() -> None:
    section("Discovery contract — bootstrap discovery blob satisfies promoted contract")
    m = promote.load_manifest()
    disc_hash = m.get("blobs", {}).get("discovery", {}).get("logic/python")
    check("discovery blob in manifest", disc_hash is not None)
    if disc_hash:
        try:
            promote.triple_pass_review(disc_hash, label="discovery")
            check("bootstrap discovery blob satisfies discovery contract", True)
        except promote.ReviewError as e:
            check("bootstrap discovery blob satisfies discovery contract", False, str(e))


def test_v8_discovery_rejects_invalid_hash() -> None:
    section("Discovery v8 — rejects invalid hash format")
    dh = seed.put("logic/python", evolve.DISCOVERY_V8)
    try:
        seed.invoke(dh, {"hash": "not-a-hash", "vault_dir": str(seed.VAULT_DIR)})
        check("rejects invalid hash", False, "expected ValueError")
    except (ValueError, Exception) as e:
        check("rejects invalid hash", "invalid hash" in str(e).lower() or "Discovery v8" in str(e))


def test_v8_planning_burstiness_penalty() -> None:
    section("Planning v8 — bursty blob penalised vs stable blob with same avg latency")
    ph = seed.put("logic/python", evolve.PLANNING_V8)
    result = seed.invoke(ph, {"candidates": [
        # stable: avg=1.0, p95=1.5 → burstiness=1.5 (below threshold 3.0) → no penalty
        {"hash": "stable00" + "a"*56, "success_rate": 0.9, "latency_ms": 1.0,
         "p95_latency_ms": 1.5, "integrity": 0.9, "cost": 1.0,
         "invocation_count": 10, "feedback_score": 1.0, "feedback_count": 0},
        # bursty: avg=1.0, p95=4.0 → burstiness=4.0 (above 3.0) → penalty applied
        {"hash": "burstybb" + "b"*56, "success_rate": 0.9, "latency_ms": 1.0,
         "p95_latency_ms": 4.0, "integrity": 0.9, "cost": 1.0,
         "invocation_count": 10, "feedback_score": 1.0, "feedback_count": 0},
    ]})
    check("stable blob selected over bursty blob with same avg latency",
          result["selected"].startswith("stable"),
          f"selected={result['selected'][:16]}")


def test_v8_telemetry_reader_includes_volatility() -> None:
    section("Telemetry-reader v8 — result includes volatility metric")
    th = seed.put("logic/python", evolve.TELEMETRY_READER_V8)
    h_blob = seed.put("logic/python", "result = 'volatility-test'")
    for _ in range(5):
        seed.invoke(h_blob, {})
    result = seed.invoke(th, {"vault_dir": str(seed.VAULT_DIR)})
    if h_blob in result:
        check("volatility field present in telemetry output",
              "volatility" in result[h_blob])
        check("volatility is numeric",
              isinstance(result[h_blob]["volatility"], (int, float)))


def test_full_f7_evolution_cycle() -> None:
    section("Full f_7 evolution cycle — ContractCompliance active, manifest v1.10.0")
    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f7-bc",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f7-bc",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f7-bc",
    }
    def _mock_gen(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f7-bc")
    _iu = infer.InferenceUnavailable("mocked")
    with mock.patch("infer.generate_candidate", side_effect=_mock_gen), \
         mock.patch("infer.generate_test_cases", side_effect=_iu), \
         mock.patch("promote.run_test_suite", return_value=[]):
        results = evolve.run_all()
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three cycles ran", len(results) == 3)
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.11.0", m["version"] == "1.11.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", h is not None)
        # Contracts must still be present after evolution
        ch = m.get("blobs", {}).get(label, {}).get("contract/definition")
        check(f"{label} contract still in manifest after evolution", ch is not None)

    # Promoted blobs were checked by ContractCompliance (Pass 6)
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v7 = [e for e in entries
                  if e.get("event") == "promote" and e.get("version") == "1.11.0"]
    check("at least one v1.11.0 promote event in audit log", len(promote_v7) >= 1)


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

    test_bootstrap_promotes_contracts()
    test_contract_static_analysis_valid()
    test_contract_static_analysis_rejects_missing_for_label()
    test_contract_static_analysis_rejects_syntax_error_in_pre()
    test_contract_compliance_pass_satisfied()
    test_contract_compliance_catches_violation()
    test_contract_compliance_no_contract_is_noop()
    test_promote_contract_updates_manifest()
    test_promote_contract_rejects_wrong_for_label()
    test_test_case_blob_static_analysis_valid()
    test_test_case_blob_rejects_invalid_tolerance()
    test_planning_contract_satisfied_by_bootstrap_blob()
    test_discovery_contract_satisfied_by_bootstrap_blob()
    test_v8_discovery_rejects_invalid_hash()
    test_v8_planning_burstiness_penalty()
    test_v8_telemetry_reader_includes_volatility()
    test_full_f7_evolution_cycle()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
