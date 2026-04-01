#!/usr/bin/env python3
"""
tests/test_f2.py — f_2 self-modification cycle tests
Covers: p95 wired through linker enrichment, v3 blob correctness,
        integrity signal in telemetry-reader v3, manifest v1.2.0
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bootstrap
import evolve
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

def test_p95_in_linker_enrichment() -> None:
    section("Linker enrichment — p95_latency_ms forwarded")
    h = seed.put("logic/python", "result = context['x'] + 1")
    for _ in range(5):
        linker.invoke(h, {"x": 1})

    # Manually call enrichment path
    telem = linker.read_telemetry()
    measured = telem.get(h, {})
    check("p95_latency_ms present in telemetry (v2 reader)", "p95_latency_ms" in measured)

    # Enrich a candidate and verify p95 is forwarded
    result = linker.arbitrate([{"hash": h}])
    check("arbitration completes with p95 enrichment", result is not None)
    check("selected hash correct", result["selected"] == h)


def test_planning_v3_uses_p95() -> None:
    section("Planning v3 — prefers p95 over avg latency")
    plan_v3_hash = seed.put("logic/python", evolve.PLANNING_V3)

    # Candidate A: low avg but high p95 (bursty) → should lose
    # Candidate B: higher avg but low p95 (consistent) → should win
    result = seed.invoke(plan_v3_hash, {"candidates": [
        {"hash": "bursty",     "success_rate": 1.0, "latency_ms": 1.0, "p95_latency_ms": 20.0, "cost": 1.0, "invocation_count": 10},
        {"hash": "consistent", "success_rate": 1.0, "latency_ms": 3.0, "p95_latency_ms":  4.0, "cost": 1.0, "invocation_count": 10},
    ]})
    check("planning v3 selects consistent over bursty", result["selected"] == "consistent",
          f"selected={result['selected']!r}")


def test_planning_v3_fallback_no_p95() -> None:
    section("Planning v3 — falls back to avg when p95 absent")
    plan_v3_hash = seed.put("logic/python", evolve.PLANNING_V3)
    result = seed.invoke(plan_v3_hash, {"candidates": [
        {"hash": "a", "success_rate": 0.95, "latency_ms": 1.0, "cost": 1.0, "invocation_count": 10},
        {"hash": "b", "success_rate": 0.80, "latency_ms": 5.0, "cost": 1.0, "invocation_count": 10},
    ]})
    check("planning v3 works without p95 field", result["selected"] == "a")


def test_telemetry_reader_v3_integrity() -> None:
    section("Telemetry-reader v3 — integrity signal")
    telem_v3_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V3)

    # Run a known blob 6 times (all success → streak builds)
    h_clean = seed.put("logic/python", "result = 'clean'")
    for _ in range(6):
        seed.invoke(h_clean, {})

    result = seed.invoke(telem_v3_hash, {"vault_dir": str(seed.VAULT_DIR)})
    check("telemetry-reader v3 returns dict", isinstance(result, dict))
    if h_clean in result:
        entry = result[h_clean]
        check("integrity field present", "integrity" in entry)
        check("integrity > 0", entry["integrity"] > 0)
        check("p95_latency_ms present", "p95_latency_ms" in entry)
        check("success_rate = 1.0 for clean blob", entry["success_rate"] == 1.0)


def test_full_f2_evolution_cycle() -> None:
    section("Full f_2 evolution cycle — 3/3 promoted")
    results = evolve.run_all(reviewer="test-f2")
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three blobs promoted", len(promoted) == 3, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.2.0", m["version"] == "1.2.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} updated in manifest", h is not None)


def test_post_f2_arbitration_integrity_aware() -> None:
    section("Post-f_2: arbitration uses integrity + p95 signals")
    h_good = seed.put("logic/python", "result = 1")
    h_bad  = seed.put("logic/python", "result = 2")

    # Build good history: 10 clean invocations for h_good, 1 for h_bad
    # Both have measured integrity; h_good's streak (0.80) beats h_bad's cold start (0.50 default)
    for _ in range(10):
        linker.invoke(h_good, {})
    linker.invoke(h_bad, {})

    result = linker.arbitrate([{"hash": h_good}, {"hash": h_bad}])
    check("post-f2 arbitration selects well-proven blob", result["selected"] == h_good)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import shutil

    for p in [seed.VAULT_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()

    bootstrap.run(reviewer="test-bootstrap")
    print()

    test_planning_v3_uses_p95()
    test_planning_v3_fallback_no_p95()
    test_telemetry_reader_v3_integrity()
    test_full_f2_evolution_cycle()
    # These two tests require v3 blobs in the manifest (promoted by evolution above)
    test_p95_in_linker_enrichment()
    test_post_f2_arbitration_integrity_aware()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
