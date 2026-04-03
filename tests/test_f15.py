#!/usr/bin/env python3
"""
tests/test_f15.py — f_15 engine governance: governed upgrade path for logic/engine

Covers:
  - ENGINE_ABI_CONTRACT is defined and has required fields
  - _verify_engine_abi() passes for a valid engine payload
  - _verify_engine_abi() fails for a payload missing required scope keys
  - _verify_engine_abi() fails for a payload that raises on exec
  - evolve_engine() returns inference-unavailable when inference is down
  - evolve_engine() returns no-improvement when candidate fails ABI check
  - evolve_engine() returns no-improvement when candidate fails review
  - evolve_engine() promotes when candidate wins benchmark
  - evolve_engine() invalidates seed._ENGINE cache on promotion
  - run_all() still does NOT include the engine label
  - Full f_15 evolution cycle: manifest v1.15.0
  - EVOLVE_REVIEWER_PAYLOAD now includes logic/engine in authorized_types
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


def setup() -> None:
    for d in [seed.VAULT_DIR, seed.BYTECODE_DIR]:
        if d.exists():
            shutil.rmtree(d)
    if promote.MANIFEST_PATH.exists():
        promote.MANIFEST_PATH.unlink()
    if Path("audit.log").exists():
        Path("audit.log").unlink()

    seed._ENGINE = None
    seed._ENGINE_HASH = None

    global _boot
    _boot = bootstrap.run()
    print("\n── Bootstrap: f_0 + f_7 + f_15 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:16]}...")
    engine_h = m["blobs"].get("engine", {}).get("logic/engine", "MISSING")
    print(f"  engine (logic/engine)      manifest.hash={engine_h[:16]}...")
    print(f"\n  f_0 + f_7 + f_15 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# ENGINE_ABI_CONTRACT
# ---------------------------------------------------------------------------

def test_engine_abi_contract_defined() -> None:
    section("ENGINE_ABI_CONTRACT — defined with required fields")
    c = evolve.ENGINE_ABI_CONTRACT
    check("ENGINE_ABI_CONTRACT exists", c is not None)
    check("for_label is 'engine'", c.get("for_label") == "engine")
    check("required_scope_keys present", "required_scope_keys" in c)
    required = c.get("required_scope_keys", [])
    for key in ["invoke", "record_feedback", "_load_code", "_CODE_CACHE"]:
        check(f"required key '{key}' listed", key in required)


# ---------------------------------------------------------------------------
# _verify_engine_abi
# ---------------------------------------------------------------------------

def test_verify_engine_abi_passes_valid_engine() -> None:
    section("_verify_engine_abi — passes for valid engine payload")
    engine_hash = _boot.get("engine_hash")
    if not engine_hash:
        check("engine_hash available", False)
        return
    ok, reason = evolve._verify_engine_abi(engine_hash)
    check("valid engine passes ABI check", ok, reason)


def test_verify_engine_abi_fails_missing_keys() -> None:
    section("_verify_engine_abi — fails for payload missing required scope keys")
    # Minimal payload: has invoke but not record_feedback, _load_code, _CODE_CACHE
    minimal = "def invoke(h, ctx=None):\n    return None"
    h = seed.put("logic/engine", minimal)
    ok, reason = evolve._verify_engine_abi(h)
    check("missing-keys payload fails ABI check", not ok)
    check("reason mentions missing keys", "missing" in reason.lower() or "callable" in reason.lower(),
          reason)


def test_verify_engine_abi_fails_exec_error() -> None:
    section("_verify_engine_abi — fails for payload that raises on exec")
    bad_payload = "raise RuntimeError('intentional failure')"
    h = seed.put("logic/engine", bad_payload)
    ok, reason = evolve._verify_engine_abi(h)
    check("exec-error payload fails ABI check", not ok)
    check("reason mentions exec failure", "exec" in reason.lower() or "intentional" in reason.lower(),
          reason)


# ---------------------------------------------------------------------------
# evolve_engine — inference unavailable
# ---------------------------------------------------------------------------

def test_evolve_engine_inference_unavailable() -> None:
    section("evolve_engine — inference unavailable → returns inference-unavailable")
    with mock.patch("infer.generate_candidate",
                    side_effect=infer.InferenceUnavailable("test: ai binary not found")):
        result = evolve.evolve_engine()
    check("outcome is inference-unavailable",
          result.get("outcome") == "inference-unavailable",
          f"got {result.get('outcome')}")


# ---------------------------------------------------------------------------
# evolve_engine — candidate fails ABI
# ---------------------------------------------------------------------------

def test_evolve_engine_candidate_fails_abi() -> None:
    section("evolve_engine — all candidates fail ABI → no-improvement")
    # Returns a valid Python payload but missing required scope keys
    bad_engine = "def invoke(h, ctx=None):\n    return None\n# missing record_feedback etc."

    with mock.patch("infer.generate_candidate", return_value=bad_engine):
        result = evolve.evolve_engine()
    check("outcome is no-improvement (ABI failure)",
          result.get("outcome") == "no-improvement",
          f"got {result.get('outcome')}: {result.get('reason', '')}")


# ---------------------------------------------------------------------------
# evolve_engine — candidate fails review (syntax error)
# ---------------------------------------------------------------------------

def test_evolve_engine_candidate_fails_review() -> None:
    section("evolve_engine — candidate with syntax error → no-improvement")
    # Valid scope keys but syntax error
    syntax_error_engine = (
        "def invoke(h, ctx=None):\n"
        "    return None\n"
        "def record_feedback(lh, outcome, confidence=1.0, reviewer='caller', reviewer_hash=None):\n"
        "    return ''\n"
        "def _load_code(h, p):\n"
        "    return compile(p, '<b>', 'exec')\n"
        "_CODE_CACHE = {}\n"
        "def broken(:\n"   # syntax error
        "    pass\n"
    )
    with mock.patch("infer.generate_candidate", return_value=syntax_error_engine):
        result = evolve.evolve_engine()
    check("outcome is no-improvement (review failure)",
          result.get("outcome") == "no-improvement",
          f"got {result.get('outcome')}: {result.get('reason', '')}")


# ---------------------------------------------------------------------------
# evolve_engine — promotion path
# ---------------------------------------------------------------------------

def test_evolve_engine_promotes_winner() -> None:
    section("evolve_engine — winning candidate is promoted, cache invalidated")
    m = promote.load_manifest()
    current_engine_hash = m["blobs"]["engine"]["logic/engine"]

    # Build a valid candidate payload (identical to current but with a comment)
    current_blob = seed._raw_get(current_engine_hash)
    candidate_payload = current_blob["payload"] + "\n# f15-candidate"

    with mock.patch("infer.generate_candidate", return_value=candidate_payload), \
         mock.patch.object(evolve, "_benchmark_engine",
                           return_value={
                               "winner": "new",
                               "old": {"hash": current_engine_hash, "fitness": 1.0,
                                       "success_rate": 1.0, "avg_latency_ms": 5.0},
                               "new": {"hash": "placeholder", "fitness": 2.0,
                                       "success_rate": 1.0, "avg_latency_ms": 2.5},
                               "tolerance_applied": 0.05,
                           }):
        result = evolve.evolve_engine()

    check("outcome is promoted", result.get("outcome") == "promoted",
          f"got {result.get('outcome')}: {result.get('reason', '')}")
    if result.get("outcome") == "promoted":
        new_hash = result.get("new")
        check("new engine hash in manifest",
              promote.load_manifest()["blobs"]["engine"].get("logic/engine") == new_hash)
        check("seed._ENGINE cache invalidated after promotion", seed._ENGINE is None)
        check("seed._ENGINE_HASH cache invalidated after promotion", seed._ENGINE_HASH is None)


# ---------------------------------------------------------------------------
# run_all() does not include engine
# ---------------------------------------------------------------------------

def test_run_all_skips_engine() -> None:
    section("run_all() — engine label not included in results")
    # Re-setup fresh state so run_all has a clean manifest
    for d in [seed.VAULT_DIR, seed.BYTECODE_DIR]:
        if d.exists():
            shutil.rmtree(d)
    if promote.MANIFEST_PATH.exists():
        promote.MANIFEST_PATH.unlink()
    if Path("audit.log").exists():
        Path("audit.log").unlink()
    seed._ENGINE = None
    seed._ENGINE_HASH = None
    bootstrap.run()

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f15-skip-check",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f15-skip-check",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f15-skip-check",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f15-skip-check")

    def mock_gen_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "probe"}]

    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=mock_gen_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        results = evolve.run_all()

    engine_results = [r for r in results if r.get("label") == "engine"]
    check("engine not in run_all results", len(engine_results) == 0,
          f"engine appeared: {engine_results}")
    check("at least one logic/python blob in results", len(results) >= 1)


# ---------------------------------------------------------------------------
# EVOLVE_REVIEWER_PAYLOAD includes logic/engine
# ---------------------------------------------------------------------------

def test_evolve_reviewer_authorizes_logic_engine() -> None:
    section("EVOLVE_REVIEWER_PAYLOAD — authorized_types includes logic/engine")
    payload = json.loads(evolve.EVOLVE_REVIEWER_PAYLOAD)
    authorized = payload.get("authorized_types", [])
    check("logic/engine in authorized_types", "logic/engine" in authorized,
          f"got {authorized}")
    check("logic/python in authorized_types", "logic/python" in authorized)


# ---------------------------------------------------------------------------
# Full f_15 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f15_evolution_cycle() -> None:
    section("Full f_15 evolution cycle — manifest v1.15.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f15-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f15-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f15-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f15-candidate")

    def mock_gen_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "probe"}]

    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=mock_gen_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        results = evolve.run_all()

    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.15.0", m["version"] == "1.15.0")

    # Engine still present and logic/engine key intact after run_all
    engine_hash = m.get("blobs", {}).get("engine", {}).get("logic/engine")
    check("engine blob still in manifest (logic/engine key)", engine_hash is not None)

    # No logic/python key on engine entry
    engine_entry = m.get("blobs", {}).get("engine", {})
    check("engine entry has no logic/python key", "logic/python" not in engine_entry)

    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v15 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.15.0"]
    check("at least one v1.15.0 promote event", len(promote_v15) >= 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_engine_abi_contract_defined()
    test_verify_engine_abi_passes_valid_engine()
    test_verify_engine_abi_fails_missing_keys()
    test_verify_engine_abi_fails_exec_error()
    test_evolve_engine_inference_unavailable()
    test_evolve_engine_candidate_fails_abi()
    test_evolve_engine_candidate_fails_review()
    test_evolve_engine_promotes_winner()
    test_run_all_skips_engine()
    test_evolve_reviewer_authorizes_logic_engine()
    test_full_f15_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
