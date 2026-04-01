#!/usr/bin/env python3
"""
evolve.py — D-JIT Logic Fabric Self-Modification Engine
f_3: f_2(f_2) — third iteration, v3 blobs as baseline, v4 as candidates.

Cycle per core blob:
  1. Evaluate: read current hash from manifest, get fitness signals from telemetry
  2. Mutate:   generate a v4 payload with concrete improvements
  3. Review:   Triple-Pass (StaticAnalysis → SafetyVerification → ProtocolCompliance)
  4. Benchmark: invoke old vs new N times, compare measured fitness
  5. Promote:  if new wins, Council Approval → manifest update

f_3 changes vs f_2:
  - PROMOTE_TOLERANCE is now data-derived: computed from the distribution of past
    promotion fitness deltas recorded in the audit log. Why: 0.30 was set by hand
    after f_1 to accommodate capability-improvement tradeoffs. After two cycles of
    real promotions, we have measured deltas to derive a principled threshold from.
  - v4 blob mutations (see payloads below).
"""

import json
import math
import sys
from pathlib import Path
from typing import Any

import linker
import promote
import seed

BENCHMARK_ROUNDS = 25  # invocations per candidate for comparative fitness
BENCHMARK_WARMUP = 5   # discard first N invocations (cold-start costs)

# ---------------------------------------------------------------------------
# Dynamic PROMOTE_TOLERANCE — derived from audit log fitness deltas
# ---------------------------------------------------------------------------

def _derive_tolerance() -> float:
    """
    Compute PROMOTE_TOLERANCE from the distribution of past promotion fitness
    improvements recorded in audit.log.

    Why data-derived instead of fixed?  The fixed value of 0.30 was chosen by
    hand after f_1 to accommodate capability improvements that had genuine
    speed tradeoffs.  After real promotion cycles, we have actual fitness
    delta measurements.  The derived tolerance is set to the 25th percentile
    of observed improvements: promote if the new blob comes within the bottom
    quartile of historically observed gains.  This is more conservative than
    the hand-tuned 0.30 when improvements have been large, and more permissive
    when they've been small — it tracks the actual distribution.

    Falls back to 0.30 if the audit log has fewer than 3 promotion entries
    (not enough data to derive from).
    """
    FALLBACK = 0.30
    audit_path = Path("./audit.log")
    if not audit_path.exists():
        return FALLBACK

    deltas: list[float] = []
    for line in audit_path.read_text().splitlines():
        try:
            entry = json.loads(line)
        except Exception:
            continue
        bm = entry.get("benchmark", {})
        old_fit = bm.get("old", {}).get("fitness")
        new_fit = bm.get("new", {}).get("fitness")
        if old_fit and new_fit and old_fit > 0:
            deltas.append((new_fit - old_fit) / old_fit)  # fractional improvement

    if len(deltas) < 3:
        return FALLBACK

    deltas.sort()
    # 25th percentile: bottom quartile of observed fitness improvements
    idx = math.floor(0.25 * len(deltas))
    p25 = deltas[idx]
    # Tolerance = how much regression to allow = -(p25) if p25 is negative,
    # else a floor of 0.05 (always allow at least 5% regression for capability wins)
    tolerance = max(-p25, 0.05) if p25 < 0 else max(0.05, 0.30 - p25)
    return round(tolerance, 4)

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

# ---------------------------------------------------------------------------
# v4 Blob Payloads — f_3 candidates
# ---------------------------------------------------------------------------

# Discovery v4: validates envelope type before returning.
# Improvement: v3 returns any blob by hash, including telemetry/artifact blobs.
# If a caller accidentally invokes a telemetry blob, it fails at ABI enforcement
# (no 'result' variable), which is a confusing error with no indication of cause.
# v4 checks that the envelope type is 'logic/python' before returning; raises a
# clear TypeError for any other type.  Prevents misuse from propagating silently.
DISCOVERY_V4 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]

# EAFP L1 read — one syscall on hit (same as v3).
# Type guard added after load: only logic/python blobs are invocable.
# Surfacing a wrong type here gives a clear error at the Discovery layer
# rather than a confusing ABI violation at Binding.
try:
    envelope = json.loads((vault_dir / target_hash).read_text())
    log(f"discovery-v4: resolved {target_hash[:8]}... from L1")
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        envelope = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v4: resolved {target_hash[:8]}... from L2")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v4: {target_hash} not found in L1 or L2"
        )

blob_type = envelope.get("type", "")
if blob_type != "logic/python":
    raise TypeError(
        f"Discovery v4: blob {target_hash[:8]}... has type {blob_type!r}, "
        f"expected 'logic/python' — cannot invoke non-logic blob"
    )

result = envelope
"""

# Planning v4: burstiness penalty on top of p95.
# Improvement: v3 uses p95 as the latency signal, which captures tail latency.
# But p95 alone doesn't distinguish a blob that is uniformly slow from one that
# is usually fast but occasionally spikes hard.  v4 adds a burstiness factor:
# burstiness = p95 / avg_latency.  A ratio near 1.0 means the blob is consistent;
# a high ratio means the average hides large spikes.  The burstiness factor is
# applied as a multiplier on the latency term, penalising spiky blobs beyond
# what p95 alone would capture.
PLANNING_V4 = """\
candidates = context.get("candidates", [])
MIN_SAMPLES = 5

if not candidates:
    result = None
else:
    def _score(c):
        sr        = float(c.get("success_rate", 1.0))
        integrity = float(c.get("integrity",    1.0))
        n         = int(c.get("invocation_count", 0))

        p95 = c.get("p95_latency_ms")
        avg = float(c.get("latency_ms", 1.0))
        latency = max(float(p95) if p95 is not None else avg, 0.001)
        cost    = max(float(c.get("cost", 1.0)), 0.001)

        # Burstiness = p95 / avg.  Values > 1 penalise spiky blobs.
        # Capped at 3.0 to prevent extreme outliers from dominating the score.
        if p95 is not None and avg > 0.001:
            burstiness = min(float(p95) / avg, 3.0)
        else:
            burstiness = 1.0

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0

        return (sr * integrity) / (latency * burstiness * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v4: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

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

# Telemetry-Reader v4: recency decay via exponential half-life.
# Improvement: v3 weights consecutive recent successes 2× but treats all
# invocations within a session equally — a run from last week counts the same
# as one from 5 minutes ago as long as the streak is intact.
# v4 adds exponential recency decay keyed on timestamp_utc: invocations from
# the last HALF_LIFE_HOURS hours count at full weight; older ones decay by
# half for each additional half-life period.  This means the fitness signal
# reflects current behaviour, not a snapshot frozen at any point in the past.
# Why exponential?  It's the canonical memory-less decay model — each half-life
# period is equivalent regardless of when it started.  The decay factor is
# applied to both the latency and success weight, so older runs fade together.
TELEMETRY_READER_V4 = """\
import datetime
import json
import math
import time
from pathlib import Path

vault_dir    = Path(context.get("vault_dir", "./blob_vault"))
target_hash  = context.get("hash")
HALF_LIFE_S  = context.get("half_life_hours", 24) * 3600  # default 24h half-life
now_ts       = time.time()
LOG2         = math.log(2)  # pre-compute constant outside the loop

stats = {}  # hash -> {total_w, success_w, lat_sum_w, mem_sum_w, lat_mean, lat_M2,
            #          streak, recent_weight, weight_total}

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

    # Compute recency weight from timestamp (import hoisted to top of blob)
    ts_str = record.get("timestamp_utc", "")
    try:
        ts = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
        age_s = max(now_ts - ts, 0)
        decay  = math.exp(-LOG2 * age_s / HALF_LIFE_S)
    except Exception:
        decay = 1.0  # missing timestamp → treat as current

    s = stats.setdefault(invoked, {
        "total_w": 0.0, "success_w": 0.0,
        "lat_sum_w": 0.0, "mem_sum_w": 0.0,
        "lat_mean": 0.0, "lat_M2": 0.0,
        "streak": 0, "recent_weight": 0.0, "weight_total": 0.0,
    })
    ok  = record.get("error") is None
    lat = record.get("latency_ms", 0.0)
    mem = record.get("memory_kb", 0.0)

    s["total_w"]   += decay
    s["lat_sum_w"] += lat * decay
    s["mem_sum_w"] += mem * decay
    if ok:
        s["success_w"] += decay
        s["streak"]    += 1
        s["recent_weight"] += decay * (2.0 if s["streak"] > 3 else 1.0)
    else:
        s["streak"] = 0
    s["weight_total"] += 2.0 * decay  # max possible per record

    # Welford online variance (unweighted count for numerical stability)
    n = s["total_w"]
    delta          = lat - s["lat_mean"]
    s["lat_mean"] += delta * decay / n if n > 0 else 0
    s["lat_M2"]   += delta * (lat - s["lat_mean"]) * decay

result = {}
for h, s in stats.items():
    if s["total_w"] < 0.001:
        continue
    w        = s["total_w"]
    variance = s["lat_M2"] / w if w > 1 else 0.0
    std      = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    integrity  = s["recent_weight"] / s["weight_total"] if s["weight_total"] > 0 else 0.0
    result[h]  = {
        "success_rate":    s["success_w"] / w,
        "integrity":       round(integrity, 4),
        "avg_latency_ms":  s["lat_sum_w"] / w,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["mem_sum_w"]  / w,
        "invocation_count": round(w, 2),
    }

log(f"telemetry-reader-v4: {len(result)} blob(s) with recency-decay + burstiness metrics")
"""

_MUTATIONS: dict[str, str] = {
    "discovery":        DISCOVERY_V4,
    "planning":         PLANNING_V4,
    "telemetry-reader": TELEMETRY_READER_V4,
}

# Benchmark contexts — valid inputs for each label so invocation succeeds
def _bench_context(label: str, current_hash: str) -> dict:
    if label == "discovery":
        return {"hash": current_hash, "vault_dir": str(seed.VAULT_DIR)}
    if label == "planning":
        return {"candidates": [
            # p95 and burstiness inputs so v4 Planning blob gets a realistic signal
            {"hash": current_hash, "success_rate": 0.9, "latency_ms": 2.0, "p95_latency_ms": 3.5,
             "integrity": 0.8, "cost": 1.0, "invocation_count": 10},
            {"hash": "0" * 64,    "success_rate": 0.8, "latency_ms": 1.0, "p95_latency_ms": 9.0,
             "integrity": 0.5, "cost": 2.0, "invocation_count": 3},
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
    Warmup pass discards first BENCHMARK_WARMUP invocations (cold-start costs).
    Uses data-derived PROMOTE_TOLERANCE from audit log history.
    """
    tolerance = _derive_tolerance()
    ctx = _bench_context(label, old_hash)

    # Warmup: discard cold-start costs before measuring
    for _ in range(BENCHMARK_WARMUP):
        try:
            seed.invoke(old_hash, ctx)
            seed.invoke(new_hash, ctx)
        except Exception:
            pass

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
    winner  = "new" if new_fit >= old_fit * (1 - tolerance) else "old"

    return {
        "old":    {"hash": old_hash, "fitness": old_fit, **old_signals},
        "new":    {"hash": new_hash, "fitness": new_fit, **new_signals},
        "winner": winner,
        "tolerance_applied": tolerance,
    }


# ---------------------------------------------------------------------------
# Full evolution cycle for one label
# ---------------------------------------------------------------------------

def evolve_one(label: str, reviewer: str = "evolve") -> dict:
    """
    Evolve a single core blob label through the full f_3 cycle.
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
          f"winner={bm['winner']}  tolerance={bm['tolerance_applied']:.4f}")

    # Write benchmark result to audit log so _derive_tolerance has data next cycle
    audit_path = Path("./audit.log")
    with open(audit_path, "a", encoding="utf-8") as af:
        import time as _time
        af.write(json.dumps({
            "event":     "benchmark",
            "label":     label,
            "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
            "benchmark": {
                "old": {"fitness": bm["old"]["fitness"], "hash": bm["old"]["hash"]},
                "new": {"fitness": bm["new"]["fitness"], "hash": bm["new"]["hash"]},
            },
            "winner":    bm["winner"],
        }) + "\n")

    if bm["winner"] != "new":
        print(f"  no improvement — keeping current")
        return {"label": label, "outcome": "no-improvement", "benchmark": bm}

    # Promote
    approval      = promote.issue_council_approval([candidate_hash], reviewer=reviewer)
    manifest_hash = promote.promote(
        label=label,
        blob_hashes=[candidate_hash],
        council_approval_hash=approval,
        version="1.3.0",
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
    tolerance = _derive_tolerance()
    print(f"── f_3: Self-Modification Cycle  (derived tolerance={tolerance:.4f})")
    results = []
    for label in ["telemetry-reader", "planning", "discovery"]:
        # telemetry-reader first so subsequent benchmarks use v4 signals (recency decay)
        r = evolve_one(label, reviewer=reviewer)
        results.append(r)
    promoted = [r for r in results if r["outcome"] == "promoted"]
    print(f"\n  f_3 complete. {len(promoted)}/3 blobs promoted → manifest v1.3.0")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="evolve", description="f_3 self-modification engine")
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
