#!/usr/bin/env python3
"""
tests/test_f14.py — f_14 logic/engine type: honest kernel trust boundary

Covers:
  - Engine blob is stored with type logic/engine (not logic/python)
  - manifest.blobs["engine"]["logic/engine"] is set (not logic/python)
  - Engine blob passes Triple-Pass Review under new type rules
  - Safety scanner: logic/engine is exempt from exec-forbidden check
  - Safety scanner: logic/engine exec() call is present and allowed
  - Safety scanner: logic/python blobs still blocked from exec()
  - Syntax check still applies to logic/engine blobs
  - logic/engine does NOT appear in evolve run_all() cycle (not a user blob)
  - seed._load_engine() finds the engine via logic/engine key
  - invoke() still delegates to engine post-bootstrap
  - Full f_14 evolution cycle: manifest v1.14.0
"""

import json
import re
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
    print("\n── Bootstrap: f_0 + f_7 + f_14 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:16]}...")
    engine_h = m["blobs"].get("engine", {}).get("logic/engine", "MISSING")
    print(f"  engine (logic/engine)      manifest.hash={engine_h[:16]}...")
    print(f"\n  f_0 + f_7 + f_14 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# Engine type is logic/engine
# ---------------------------------------------------------------------------

def test_engine_type_is_logic_engine() -> None:
    section("Engine type — blob stored as logic/engine (not logic/python)")
    engine_hash = _boot.get("engine_hash")
    check("bootstrap returned engine_hash", engine_hash is not None)
    if engine_hash:
        blob = seed._raw_get(engine_hash)
        check("engine blob type is logic/engine", blob.get("type") == "logic/engine")
        check("engine blob type is NOT logic/python", blob.get("type") != "logic/python")


def test_manifest_uses_logic_engine_key() -> None:
    section("Manifest key — manifest.blobs['engine']['logic/engine'] set")
    m = promote.load_manifest()
    engine_entry = m.get("blobs", {}).get("engine", {})
    check("logic/engine key present", "logic/engine" in engine_entry)
    check("logic/python key absent", "logic/python" not in engine_entry)
    engine_hash = engine_entry.get("logic/engine")
    check("engine hash is 64-char hex", engine_hash is not None and len(engine_hash) == 64)
    check("engine hash matches bootstrap return", engine_hash == _boot.get("engine_hash"))


def test_load_engine_finds_logic_engine() -> None:
    section("seed._load_engine() — finds engine via logic/engine key")
    engine = seed._load_engine()
    check("_load_engine() returns scope", engine is not None)
    if engine:
        check("scope has invoke", "invoke" in engine)
        check("scope has record_feedback", "record_feedback" in engine)
        check("scope does NOT have _exec", "_exec" not in engine)


# ---------------------------------------------------------------------------
# Safety scanner: exec() allowed in logic/engine, blocked in logic/python
# ---------------------------------------------------------------------------

def test_engine_payload_uses_exec_directly() -> None:
    section("Engine payload — calls exec() directly (no _exec workaround)")
    engine_hash = _boot.get("engine_hash")
    if not engine_hash:
        check("engine_hash available", False)
        return
    blob = seed._raw_get(engine_hash)
    payload = blob["payload"]
    _EXEC_RE = re.compile(r"\bexec\s*\(")
    has_exec = bool(_EXEC_RE.search(payload))
    has_exec_workaround = "_exec(" in payload
    check("engine payload calls exec() directly", has_exec)
    check("engine payload does NOT use _exec() workaround", not has_exec_workaround)


def test_safety_scanner_exempts_logic_engine() -> None:
    section("Safety scanner — logic/engine exempt from exec-forbidden check")
    # A payload with exec() that would fail for logic/python must pass for logic/engine
    exec_payload = 'exec("result = 1", {})\nresult = True'
    h_engine = seed.put("logic/engine", exec_payload)
    h_python = seed.put("logic/python", exec_payload)
    try:
        promote.triple_pass_review(h_engine)
        check("logic/engine with exec() passes safety scan", True)
    except promote.ReviewError as e:
        check("logic/engine with exec() passes safety scan", False, f"[{e.pass_name}] {e.detail}")
    try:
        promote.triple_pass_review(h_python)
        check("logic/python with exec() fails safety scan", False, "should have raised ReviewError")
    except promote.ReviewError as e:
        check("logic/python with exec() fails safety scan",
              e.pass_name == "SafetyVerification", f"[{e.pass_name}] {e.detail}")


def test_syntax_check_applies_to_logic_engine() -> None:
    section("Syntax check — still applied to logic/engine blobs")
    bad_payload = "def foo(:\n    pass"
    h = seed.put("logic/engine", bad_payload)
    try:
        promote.triple_pass_review(h)
        check("logic/engine syntax error rejected", False, "should have raised ReviewError")
    except promote.ReviewError as e:
        check("logic/engine syntax error rejected",
              e.pass_name == "StaticAnalysis", f"[{e.pass_name}] {e.detail}")


# ---------------------------------------------------------------------------
# Engine not in evolve cycle
# ---------------------------------------------------------------------------

def test_engine_not_evolved() -> None:
    section("Evolve cycle — logic/engine label skipped (not a user blob)")
    # evolve_one("engine") should return no-improvement because it looks for
    # logic/python key, which is absent for the engine label
    result = evolve.evolve_one("engine")
    # evolve_one looks for logic/python key — engine uses logic/engine, so it
    # returns "error: not in manifest" and exits early. That IS the expected behavior.
    check("evolve_one('engine') exits early (not a logic/python blob)",
          result.get("outcome") in {"error", "no-improvement"},
          f"got outcome={result.get('outcome')}")
    check("evolve_one('engine') does not promote engine",
          result.get("outcome") != "promoted")


# ---------------------------------------------------------------------------
# End-to-end: invoke still works via engine
# ---------------------------------------------------------------------------

def test_invoke_via_engine() -> None:
    section("invoke() — delegates to logic/engine engine post-bootstrap")
    m = promote.load_manifest()
    discovery_hash = m["blobs"]["discovery"]["logic/python"]
    result = seed.invoke(discovery_hash, {
        "hash": discovery_hash,
        "vault_dir": str(seed.VAULT_DIR),
    })
    check("invoke via engine returns dict", isinstance(result, dict))
    check("result has type key", "type" in result)


# ---------------------------------------------------------------------------
# Full f_14 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f14_evolution_cycle() -> None:
    section("Full f_14 evolution cycle — manifest v1.14.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f14-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f14-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f14-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f14-candidate")

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

    # Engine label must NOT appear in promoted results
    engine_promoted = [r for r in results if r.get("label") == "engine"]
    check("engine not in evolve results", len(engine_promoted) == 0,
          f"engine appeared in results: {engine_promoted}")

    m = promote.load_manifest()
    check("manifest version 1.14.0", m["version"] == "1.14.0")

    # Engine still present and still logic/engine after evolution
    engine_hash = m.get("blobs", {}).get("engine", {}).get("logic/engine")
    check("engine blob still in manifest (logic/engine key)", engine_hash is not None)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v14 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.14.0"]
    check("at least one v1.14.0 promote event", len(promote_v14) >= 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_engine_type_is_logic_engine()
    test_manifest_uses_logic_engine_key()
    test_load_engine_finds_logic_engine()
    test_engine_payload_uses_exec_directly()
    test_safety_scanner_exempts_logic_engine()
    test_syntax_check_applies_to_logic_engine()
    test_engine_not_evolved()
    test_invoke_via_engine()
    test_full_f14_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
