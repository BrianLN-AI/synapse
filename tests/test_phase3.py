#!/usr/bin/env python3
"""
tests/test_phase3.py — Phase 3: Recursive Leap tests
Covers: linker routing, Discovery blob, Planning arbitrage, BIOS fallback
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bootstrap
import linker
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------

def test_bootstrap() -> None:
    section("Bootstrap — promote Discovery + Planning blobs")
    result = bootstrap.run(reviewer="test-bootstrap")
    manifest = promote.load_manifest()

    disc_hash = manifest.get("blobs", {}).get("discovery", {}).get("logic/python")
    plan_hash = manifest.get("blobs", {}).get("planning", {}).get("logic/python")

    check("manifest version 1.0.0", manifest["version"] == "1.0.0")
    check("discovery blob in manifest", disc_hash is not None)
    check("planning blob in manifest", plan_hash is not None)
    check("returned discovery hash matches manifest", result["discovery"] == disc_hash)
    check("returned planning hash matches manifest", result["planning"] == plan_hash)


def test_linker_invoke_routes_discovery() -> None:
    section("Linker invoke — routes through Discovery blob")
    h = seed.put("logic/python", "result = context['n'] + 1")
    out = linker.invoke(h, {"n": 41})
    check("result correct via linker", out == 42, f"got {out!r}")

    # Confirm Discovery blob logged the resolution
    blobs = list(seed.VAULT_DIR.iterdir())
    disc_logs = []
    for b in blobs:
        env = json.loads(b.read_text())
        if env["type"] == "telemetry/artifact":
            payload = json.loads(env["payload"])
            if any("discovery:" in l for l in payload.get("log", [])):
                disc_logs.append(payload)

    check("Discovery blob telemetry present", len(disc_logs) >= 1)
    resolved_in_log = any(h[:8] in l for d in disc_logs for l in d.get("log", []))
    check("Discovery log references target hash", resolved_in_log)


def test_linker_invoke_unknown_hash() -> None:
    section("Linker invoke — unknown hash raises")
    raised = False
    try:
        linker.invoke("0" * 64, {})
    except FileNotFoundError:
        raised = True
    check("FileNotFoundError on unknown hash", raised)


def test_planning_arbitrage_fitness() -> None:
    section("Planning blob — fitness function")
    # Low latency/cost candidate should win despite lower success_rate
    candidates = [
        {"hash": "slow", "success_rate": 0.99, "integrity": 1.0, "latency_ms": 100.0, "cost": 5.0},
        {"hash": "fast", "success_rate": 0.90, "integrity": 1.0, "latency_ms": 1.0,   "cost": 0.5},
    ]
    result = linker.arbitrate(candidates)
    check("planning selects fast candidate", result["selected"] == "fast", f"got {result['selected']!r}")
    check("score is numeric", isinstance(result["score"], (int, float)))
    check("rationale present", bool(result.get("rationale")))
    check("ranked list returned", len(result.get("ranked", [])) == 2)


def test_planning_single_candidate() -> None:
    section("Planning blob — sole candidate")
    candidates = [{"hash": "only", "success_rate": 1.0, "integrity": 1.0, "latency_ms": 10.0, "cost": 1.0}]
    result = linker.arbitrate(candidates)
    check("sole candidate selected", result["selected"] == "only")
    check("rationale says sole candidate", "sole candidate" in result.get("rationale", ""))


def test_planning_empty() -> None:
    section("Planning blob — empty candidates")
    result = linker.arbitrate([])
    check("empty candidates returns None", result is None)


def test_bios_fallback_without_manifest() -> None:
    section("BIOS fallback — resolve() falls back when manifest has no discovery")
    # Temporarily clear the manifest blob registry
    import copy
    m = promote.load_manifest()
    original_blobs = copy.deepcopy(m.get("blobs", {}))

    # Patch in-memory only — write a stripped manifest
    m_stripped = {**m, "blobs": {}}
    promote.MANIFEST_PATH.write_text(json.dumps(m_stripped, indent=2))

    try:
        h = seed.put("logic/python", "result = 'bios-path'")
        blob = linker.resolve(h)
        check("BIOS fallback resolves correctly", blob["payload"] == "result = 'bios-path'")
    finally:
        # Restore manifest
        m["blobs"] = original_blobs
        promote.MANIFEST_PATH.write_text(json.dumps(m, indent=2))


def test_promote_fix_non_abi_errors() -> None:
    section("promote._pass_protocol — non-ABI errors do not fail review")
    # Discovery blob requires context['hash'] — probe sends {'__probe__': True}
    # This causes KeyError, which must NOT count as a ReviewError
    h = seed.put("logic/python", "result = context['required_key']")
    try:
        promote.triple_pass_review(h)
        passed = True
    except promote.ReviewError as e:
        passed = e.pass_name != "ProtocolCompliance"
    check("KeyError during probe does not fail ProtocolCompliance", passed)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import shutil

    for p in [seed.VAULT_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()

    test_bootstrap()
    test_linker_invoke_routes_discovery()
    test_linker_invoke_unknown_hash()
    test_planning_arbitrage_fitness()
    test_planning_single_candidate()
    test_planning_empty()
    test_bios_fallback_without_manifest()
    test_promote_fix_non_abi_errors()

    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)


def test_feedback_loop() -> None:
    section("Feedback loop — telemetry → arbitration")
    import time

    h_fast = seed.put("logic/python", "result = context['x'] * 2")
    h_slow = seed.put("logic/python", """
import time as _t
_t.sleep(0.01)
result = context['x'] * 2
""")

    # Build history: fast invoked 3x, slow invoked 1x
    for _ in range(3):
        linker.invoke(h_fast, {"x": 5})
    linker.invoke(h_slow, {"x": 5})

    telem = linker.read_telemetry()
    check("telemetry-reader returns data", len(telem) >= 2)
    check("h_fast has invocation_count=3", telem.get(h_fast, {}).get("invocation_count") == 3)
    check("h_slow has higher avg_latency", telem.get(h_slow, {}).get("avg_latency_ms", 0) > telem.get(h_fast, {}).get("avg_latency_ms", 999))

    result = linker.arbitrate([{"hash": h_fast}, {"hash": h_slow}])
    check("arbitration selects h_fast (lower latency)", result["selected"] == h_fast)
    check("score is numeric", isinstance(result.get("score"), (int, float)))


def test_read_telemetry_via_blob() -> None:
    section("Telemetry-reader blob — routes through vault")
    h = seed.put("logic/python", "result = 'telem-blob-test'")
    linker.invoke(h, {})

    telem = linker.read_telemetry()
    check("telemetry-reader blob invoked successfully", h in telem)
    check("success_rate is 1.0 after clean run", telem[h]["success_rate"] == 1.0)


def test_manifest_v1() -> None:
    section("Manifest v1.0.0 — f_0 defined")
    m = promote.load_manifest()
    check("manifest version is 1.0.0", m["version"] == "1.0.0")
    check("discovery in manifest", "discovery" in m.get("blobs", {}))
    check("planning in manifest", "planning" in m.get("blobs", {}))
    check("telemetry-reader in manifest", "telemetry-reader" in m.get("blobs", {}))
