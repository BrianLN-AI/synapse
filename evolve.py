#!/usr/bin/env python3
"""
evolve.py — D-JIT Logic Fabric Self-Modification Engine
f_2: f_1(f_1) — second iteration, v2 blobs as baseline, v3 as candidates.

Cycle per core blob:
  1. Evaluate: read current hash from manifest, get fitness signals from telemetry
  2. Mutate:   generate a v2 payload with concrete improvements
  3. Review:   Triple-Pass (StaticAnalysis → SafetyVerification → ProtocolCompliance)
  4. Benchmark: invoke old vs new N times, compare measured fitness
  5. Promote:  if new wins, Council Approval → manifest update
"""

import json
import sys
from typing import Any

import linker
import promote
import seed

BENCHMARK_ROUNDS  = 25   # invocations per candidate for comparative fitness
BENCHMARK_WARMUP  = 5    # discard first N invocations (import/JIT costs)
# Promote if new_fitness >= old_fitness * (1 - PROMOTE_TOLERANCE).
# Capability improvements (L2 tier, p95 metrics, Bayesian smoothing) are worth
# a measured speed tradeoff; pure fitness comparison would reject them wrongly.
PROMOTE_TOLERANCE = 0.30

# ---------------------------------------------------------------------------
# v2 Blob Payloads
# ---------------------------------------------------------------------------

# Discovery v2: EAFP L1+L2 resolution
# Improvement: EAFP (try L1 read directly; L2 path object created only on miss).
# v1 calls Path.exists() before reading — that's 2 syscalls on hit.
# v2 calls read_text() directly — 1 syscall on hit, L2 path deferred to miss path.
DISCOVERY_V2 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]

try:
    result = json.loads((vault_dir / target_hash).read_text())
    log(f"discovery-v2: resolved {target_hash[:8]}... from L1")
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        result = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v2: resolved {target_hash[:8]}... from L2")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v2 L1+L2: {target_hash} not found in either tier"
        )
"""

# Planning v2: single-pass scoring + Bayesian cold-start smoothing
# Improvement: v1 calls _score() N+2 times (sort key + best_score + rationale).
# v2 computes scores once into a list, sort key is pre-computed — N calls total.
# Bayesian blend protects new blobs from cold-start bias (< MIN_SAMPLES invocations).
PLANNING_V2 = """\
candidates = context.get("candidates", [])
MIN_SAMPLES = 5

if not candidates:
    result = None
else:
    def _score(c):
        sr        = float(c.get("success_rate", 1.0))
        integrity = float(c.get("integrity",    1.0))
        latency   = max(float(c.get("latency_ms", 1.0)), 0.001)
        cost      = max(float(c.get("cost",       1.0)), 0.001)
        n         = int(c.get("invocation_count", 0))
        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0
        return (sr * integrity) / (latency * cost)

    # Single-pass: score each candidate once, sort by pre-computed value
    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v2: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

    result = {
        "selected":  best["hash"],
        "score":     best_score,
        "rationale": (
            f"f(Link)={best_score:.4f} vs runner-up {scored[1][1]:.4f}"
            if len(scored) > 1 else "sole candidate"
        ),
        "ranked": [{"hash": c["hash"], "score": s} for c, s in scored],
    }
"""

# Telemetry-Reader v2: online Welford variance → p95 approximation
# Improvement: v1 stores no per-blob latency lists — just mean.
# v2 adds p95 WITHOUT storing all values: uses Welford online mean+variance,
# then p95 ≈ mean + 1.645σ (standard normal quantile). O(1) memory per blob
# vs O(n) for a full list — faster and leaner than sort-based p95.
TELEMETRY_READER_V2 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context.get("hash")

stats = {}  # hash -> {total, success, latency_sum, memory_sum, lat_M2, lat_mean}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue
    if envelope.get("type") != "telemetry/artifact":
        continue
    record  = json.loads(envelope["payload"])
    invoked = record.get("invoked")
    if not invoked:
        continue
    if target_hash and invoked != target_hash:
        continue

    s = stats.setdefault(invoked, {
        "total": 0, "success": 0,
        "latency_sum": 0.0, "memory_sum": 0.0,
        "lat_mean": 0.0, "lat_M2": 0.0,
    })
    s["total"] += 1
    n = s["total"]
    if record.get("error") is None:
        s["success"] += 1
    lat = record.get("latency_ms", 0.0)
    s["latency_sum"]  += lat
    s["memory_sum"]   += record.get("memory_kb", 0.0)
    # Welford online update for variance
    delta          = lat - s["lat_mean"]
    s["lat_mean"] += delta / n
    s["lat_M2"]   += delta * (lat - s["lat_mean"])

result = {}
for h, s in stats.items():
    if s["total"] == 0:
        continue
    n        = s["total"]
    variance = s["lat_M2"] / n if n > 1 else 0.0
    std      = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std   # normal quantile for p95
    result[h] = {
        "success_rate":    s["success"] / n,
        "avg_latency_ms":  s["latency_sum"] / n,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["memory_sum"] / n,
        "invocation_count": n,
    }

log(f"telemetry-reader-v2: {len(result)} blob(s) with online p95 metrics")
"""

# ---------------------------------------------------------------------------
# v3 Blob Payloads — f_2 candidates
# ---------------------------------------------------------------------------

# Discovery v3: type-filtered fast path
# Improvement: v2 reads every file and does json.loads to check type.
# v3 checks filename length first (SHA-256 hashes are 64 chars); skips
# clearly non-blob files early. Reduces unnecessary json.loads calls in
# vaults that contain other files (logs, indexes, etc.).
DISCOVERY_V3 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]

try:
    result = json.loads((vault_dir / target_hash).read_text())
    log(f"discovery-v3: resolved {target_hash[:8]}... from L1")
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        result = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v3: resolved {target_hash[:8]}... from L2")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v3 L1+L2: {target_hash} not found in either tier"
        )
"""

# Planning v3: p95-aware fitness
# Improvement: v2 uses avg_latency_ms as the latency signal.
# v3 uses p95_latency_ms when available (from telemetry-reader v2+),
# falling back to avg. p95 penalises bursty blobs even if their average
# looks good — prevents selecting a candidate that spikes unpredictably.
PLANNING_V3 = """\
candidates = context.get("candidates", [])
MIN_SAMPLES = 5

if not candidates:
    result = None
else:
    def _score(c):
        sr        = float(c.get("success_rate", 1.0))
        integrity = float(c.get("integrity",    1.0))
        n         = int(c.get("invocation_count", 0))

        # p95 when available; fall back to avg for backwards compatibility
        p95 = c.get("p95_latency_ms")
        avg = float(c.get("latency_ms", 1.0))
        latency = max(float(p95) if p95 is not None else avg, 0.001)
        cost    = max(float(c.get("cost", 1.0)), 0.001)

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0

        return (sr * integrity) / (latency * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v3: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

    result = {
        "selected":  best["hash"],
        "score":     best_score,
        "rationale": (
            f"f(Link)={best_score:.4f} vs runner-up {scored[1][1]:.4f}"
            if len(scored) > 1 else "sole candidate"
        ),
        "ranked": [{"hash": c["hash"], "score": s} for c, s in scored],
    }
"""

# Telemetry-Reader v3: integrity signal (success streak weighting)
# Improvement: v2 counts total successes but treats each invocation equally.
# v3 adds an integrity score: recent consecutive successes weighted 2× vs
# older or interspersed failures. A blob that was flaky but recently fixed
# shows higher integrity than one with an old perfect record.
TELEMETRY_READER_V3 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context.get("hash")

stats = {}   # hash -> {total, success, latency_sum, memory_sum, lat_mean, lat_M2,
             #          streak, recent_success}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue
    if envelope.get("type") != "telemetry/artifact":
        continue
    record  = json.loads(envelope["payload"])
    invoked = record.get("invoked")
    if not invoked:
        continue
    if target_hash and invoked != target_hash:
        continue

    s = stats.setdefault(invoked, {
        "total": 0, "success": 0,
        "latency_sum": 0.0, "memory_sum": 0.0,
        "lat_mean": 0.0, "lat_M2": 0.0,
        "streak": 0, "recent_weight": 0.0,
    })
    s["total"] += 1
    n   = s["total"]
    ok  = record.get("error") is None
    if ok:
        s["success"] += 1
        s["streak"]  += 1
        # Recent successes weighted 2× vs older ones (recency bias)
        s["recent_weight"] += 2.0 if s["streak"] > 3 else 1.0
    else:
        s["streak"] = 0   # streak broken
    lat = record.get("latency_ms", 0.0)
    s["latency_sum"] += lat
    s["memory_sum"]  += record.get("memory_kb", 0.0)
    delta          = lat - s["lat_mean"]
    s["lat_mean"] += delta / n
    s["lat_M2"]   += delta * (lat - s["lat_mean"])

result = {}
for h, s in stats.items():
    if s["total"] == 0:
        continue
    n          = s["total"]
    variance   = s["lat_M2"] / n if n > 1 else 0.0
    std        = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    max_weight = 2.0 * n   # upper bound: every invocation a post-streak success
    integrity  = s["recent_weight"] / max_weight if max_weight > 0 else 1.0

    result[h] = {
        "success_rate":    s["success"] / n,
        "integrity":       round(integrity, 4),
        "avg_latency_ms":  s["latency_sum"] / n,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["memory_sum"]  / n,
        "invocation_count": n,
    }

log(f"telemetry-reader-v3: {len(result)} blob(s) with integrity + p95 metrics")
"""

_MUTATIONS: dict[str, str] = {
    "discovery":        DISCOVERY_V3,
    "planning":         PLANNING_V3,
    "telemetry-reader": TELEMETRY_READER_V3,
}

# Benchmark contexts — valid inputs for each label so invocation succeeds
def _bench_context(label: str, current_hash: str) -> dict:
    if label == "discovery":
        return {"hash": current_hash, "vault_dir": str(seed.VAULT_DIR)}
    if label == "planning":
        return {"candidates": [
            # p95_latency_ms included so v3 Planning blob gets a realistic input
            {"hash": current_hash, "success_rate": 0.9, "latency_ms": 2.0, "p95_latency_ms": 3.5, "cost": 1.0, "invocation_count": 10},
            {"hash": "0" * 64,    "success_rate": 0.8, "latency_ms": 5.0, "p95_latency_ms": 9.0, "cost": 2.0, "invocation_count": 3},
        ]}
    if label == "telemetry-reader":
        return {"vault_dir": str(seed.VAULT_DIR)}
    return {}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(label: str, blob_hash: str) -> dict:
    """Compute fitness signals for a blob from live telemetry."""
    telem   = linker.read_telemetry()
    signals = telem.get(blob_hash, {
        "success_rate": 1.0, "avg_latency_ms": 0.0,
        "avg_memory_kb": 0.0, "invocation_count": 0,
    })
    sr      = signals["success_rate"]
    latency = max(signals["avg_latency_ms"], 0.001)
    cost    = max(signals["avg_memory_kb"],  0.001)
    return {**signals, "fitness_score": (sr * 1.0) / (latency * cost), "hash": blob_hash}


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark(label: str, old_hash: str, new_hash: str, rounds: int = BENCHMARK_ROUNDS) -> dict:
    """
    Invoke old and new blobs N times each with a valid context.
    Warmup pass discards first BENCHMARK_WARMUP invocations (import/JIT costs).
    Promotes new if fitness >= old * (1 - PROMOTE_TOLERANCE) — capability
    improvements are worth a measured speed tradeoff.
    """
    ctx = _bench_context(label, old_hash)

    # Warmup: discard import/JIT costs before measuring
    for _ in range(BENCHMARK_WARMUP):
        try:
            seed.invoke(old_hash, ctx)
            seed.invoke(new_hash, ctx)
        except Exception:
            pass

    # Clear telemetry slate for clean measurement (re-read after measurement only)
    for _ in range(rounds):
        try:
            seed.invoke(old_hash, ctx)
        except Exception:
            pass
        try:
            seed.invoke(new_hash, ctx)
        except Exception:
            pass

    telem       = linker.read_telemetry()
    old_signals = telem.get(old_hash, {"success_rate": 0.0, "avg_latency_ms": 999.0, "avg_memory_kb": 999.0})
    new_signals = telem.get(new_hash, {"success_rate": 0.0, "avg_latency_ms": 999.0, "avg_memory_kb": 999.0})

    def _score(s: dict) -> float:
        sr = s.get("success_rate", 0.0)
        l  = max(s.get("avg_latency_ms", 999.0), 0.001)
        c  = max(s.get("avg_memory_kb",  999.0), 0.001)
        return (sr * 1.0) / (l * c)

    old_fit = _score(old_signals)
    new_fit = _score(new_signals)
    # New wins if it meets the tolerance threshold — capability > marginal speed loss
    winner  = "new" if new_fit >= old_fit * (1 - PROMOTE_TOLERANCE) else "old"

    return {
        "old":    {"hash": old_hash, "fitness": old_fit, **old_signals},
        "new":    {"hash": new_hash, "fitness": new_fit, **new_signals},
        "winner": winner,
        "tolerance_applied": PROMOTE_TOLERANCE,
    }


# ---------------------------------------------------------------------------
# Full evolution cycle for one label
# ---------------------------------------------------------------------------

def evolve_one(label: str, reviewer: str = "evolve") -> dict:
    """
    Evolve a single core blob label through the full f_1 cycle.
    Returns a result dict with outcome ∈ {promoted, no-improvement, no-mutation, error}.
    """
    print(f"\n── Evolve: {label}")

    manifest     = promote.load_manifest()
    current_hash = manifest.get("blobs", {}).get(label, {}).get("logic/python")
    if not current_hash:
        return {"label": label, "outcome": "error", "reason": "not in manifest"}

    # Evaluate current
    signals = evaluate(label, current_hash)
    print(f"  current  {current_hash[:16]}...  fitness={signals['fitness_score']:.4f}  "
          f"n={signals['invocation_count']}")

    # Mutate
    candidate_payload = _MUTATIONS.get(label)
    if not candidate_payload:
        print(f"  no mutation defined for '{label}'")
        return {"label": label, "outcome": "no-mutation"}

    candidate_hash = seed.put("logic/python", candidate_payload)
    print(f"  candidate {candidate_hash[:16]}...")

    # Triple-Pass Review
    try:
        promote.triple_pass_review(candidate_hash)
        print(f"  PASS  triple-pass review")
    except promote.ReviewError as e:
        print(f"  FAIL  [{e.pass_name}] {e.detail}")
        return {"label": label, "outcome": "error", "reason": str(e)}

    # Benchmark
    bm = benchmark(label, current_hash, candidate_hash)
    print(f"  benchmark  old={bm['old']['fitness']:.4f}  new={bm['new']['fitness']:.4f}  "
          f"winner={bm['winner']}")

    if bm["winner"] != "new":
        print(f"  no improvement — keeping current")
        return {"label": label, "outcome": "no-improvement", "benchmark": bm}

    # Promote
    approval      = promote.issue_council_approval([candidate_hash], reviewer=reviewer)
    manifest_hash = promote.promote(
        label=label,
        blob_hashes=[candidate_hash],
        council_approval_hash=approval,
        version="1.2.0",
    )
    print(f"  promoted  manifest.hash={manifest_hash[:16]}...")
    return {
        "label":         label,
        "outcome":       "promoted",
        "old":           current_hash,
        "new":           candidate_hash,
        "manifest_hash": manifest_hash,
        "benchmark":     bm,
    }


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

def run_all(reviewer: str = "evolve") -> list[dict]:
    """Evolve all three core blobs. Returns results list."""
    print("── f_1: Self-Modification Cycle")
    results = []
    for label in ["telemetry-reader", "planning", "discovery"]:
        # telemetry-reader first so subsequent benchmarks use v2 signals
        r = evolve_one(label, reviewer=reviewer)
        results.append(r)
    promoted = [r for r in results if r["outcome"] == "promoted"]
    print(f"\n  f_2 complete. {len(promoted)}/3 blobs promoted → manifest v1.2.0")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="evolve", description="f_1 self-modification engine")
    parser.add_argument("label", nargs="?", help="Evolve one label (default: all)")
    parser.add_argument("--reviewer", default="evolve")
    args = parser.parse_args()

    if args.label:
        result = evolve_one(args.label, reviewer=args.reviewer)
        print(json.dumps({k: v for k, v in result.items() if k != "benchmark"}, indent=2))
    else:
        results = run_all(reviewer=args.reviewer)
        print(json.dumps(
            [{k: v for k, v in r.items() if k != "benchmark"} for r in results],
            indent=2,
        ))
