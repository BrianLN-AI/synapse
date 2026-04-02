#!/usr/bin/env python3
"""
tests/test_f1.py — f_1 self-modification cycle tests
Covers: compile cache, evolution cycle, v2 blob correctness, manifest v1.1.0
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

def test_compile_cache() -> None:
    section("Compile cache — code object reuse")
    h = seed.put("logic/python", "result = context['x'] ** 2")

    # Clear cache for clean test
    seed._CODE_CACHE.pop(h, None)

    seed.invoke(h, {"x": 3})
    check("code object cached after first invoke", h in seed._CODE_CACHE)

    code_obj = seed._CODE_CACHE[h]
    seed.invoke(h, {"x": 4})
    check("same code object reused on second invoke", seed._CODE_CACHE[h] is code_obj)


def test_linker_invocation_count_passed() -> None:
    section("Linker enrichment — invocation_count forwarded to Planning")
    h = seed.put("logic/python", "result = context['v'] + 1")

    # Build some history
    for _ in range(3):
        linker.invoke(h, {"v": 10})

    telem = linker.read_telemetry()
    # invocation_count is the key signal — verify it is forwarded (>= 1 confirms telemetry is live)
    check("invocation_count forwarded in telemetry", telem.get(h, {}).get("invocation_count", 0) >= 1)

    result = linker.arbitrate([
        {"hash": h},
        {"hash": "0" * 64, "success_rate": 0.5, "latency_ms": 99.0, "cost": 99.0},
    ])
    # The enriched candidate should win via fitness
    check("arbitration selects measured candidate", result["selected"] == h)


def test_evolve_triple_pass_all_v2() -> None:
    section("Triple-Pass Review — all v2 blobs pass")
    for label, payload in [
        ("discovery",        evolve.DISCOVERY_V2),
        ("planning",         evolve.PLANNING_V2),
        ("telemetry-reader", evolve.TELEMETRY_READER_V2),
    ]:
        h = seed.put("logic/python", payload)
        try:
            promote.triple_pass_review(h)
            check(f"{label} v2 passes triple-pass", True)
        except promote.ReviewError as e:
            check(f"{label} v2 passes triple-pass", False, str(e))


def test_discovery_v2_l1_hit() -> None:
    section("Discovery v2 — L1 hit (EAFP path)")
    h_target = seed.put("logic/python", "result = 'discovery-target'")
    disc_v2_hash = seed.put("logic/python", evolve.DISCOVERY_V2)

    result = seed.invoke(disc_v2_hash, {
        "hash": h_target,
        "vault_dir": str(seed.VAULT_DIR),
    })
    check("discovery v2 resolves L1 hash", result["payload"] == "result = 'discovery-target'")


def test_planning_v2_bayesian_smoothing() -> None:
    section("Planning v2 — Bayesian smoothing on sparse candidates")
    plan_v2_hash = seed.put("logic/python", evolve.PLANNING_V2)

    # cold: n=0 → Bayesian blend sets sr=0.95, latency=1.0 (prior); cost stays at 3.0
    #   blended_score = 0.95 / (1.0 × 3.0) = 0.317
    # warm: n=20 ≥ MIN_SAMPLES → raw values used
    #   raw_score    = 0.90 / (2.0 × 1.0) = 0.450  ← wins
    # Without blending: cold raw = 0.99 / (0.5 × 3.0) = 0.660 → cold would win
    result = seed.invoke(plan_v2_hash, {"candidates": [
        {"hash": "cold", "success_rate": 0.99, "latency_ms": 0.5, "cost": 3.0, "invocation_count": 0},
        {"hash": "warm", "success_rate": 0.90, "latency_ms": 2.0, "cost": 1.0, "invocation_count": 20},
    ]})
    check("Bayesian smoothing causes warm candidate to beat cold spike", result["selected"] == "warm")


def test_telemetry_reader_v2_p95() -> None:
    section("Telemetry-reader v2 — p95 metric present")
    telem_v2_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V2)
    result = seed.invoke(telem_v2_hash, {"vault_dir": str(seed.VAULT_DIR)})
    check("telemetry-reader v2 returns result dict", isinstance(result, dict))
    if result:
        sample = next(iter(result.values()))
        check("p95_latency_ms field present", "p95_latency_ms" in sample)
        check("p95_latency_ms is numeric", isinstance(sample["p95_latency_ms"], (int, float)))


def test_full_evolution_cycle() -> None:
    section("Full evolution cycle — 3/3 promoted")
    results = evolve.run_all(reviewer="test-f1")
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three blobs promoted", len(promoted) == 3, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.1.0", m["version"] == "1.1.0")

    for label in ["discovery", "planning", "telemetry-reader"]:
        new_hash = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} updated in manifest", new_hash is not None)


def test_post_f1_arbitration() -> None:
    section("Post-f_1 arbitration uses v2 Planning + Telemetry-Reader")
    h_a = seed.put("logic/python", "result = context['x'] + 1")
    h_b = seed.put("logic/python", "result = context['x'] - 1")

    for _ in range(8):
        linker.invoke(h_a, {"x": 5})
    linker.invoke(h_b, {"x": 5})

    result = linker.arbitrate([{"hash": h_a}, {"hash": h_b}])
    check("post-f1 arbitration selects h_a (more history)", result["selected"] == h_a)
    check("score numeric", isinstance(result.get("score"), (int, float)))


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

    test_compile_cache()
    test_linker_invocation_count_passed()
    test_evolve_triple_pass_all_v2()
    test_discovery_v2_l1_hit()
    test_planning_v2_bayesian_smoothing()
    test_telemetry_reader_v2_p95()
    test_full_evolution_cycle()
    test_post_f1_arbitration()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
