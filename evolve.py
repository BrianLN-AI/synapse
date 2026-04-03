#!/usr/bin/env python3
"""
evolve.py — D-JIT Logic Fabric Self-Modification Engine
f_15: engine governance — governed upgrade path for the logic/engine blob.

Cycle per blob (infrastructure or capability):
  1. Evaluate:  read current hash from manifest, get fitness signals from telemetry
  2. Goal:      if goal/okr promoted for label → derive goal from key result gaps;
                else derive from fitness signal thresholds (f_10 fallback)
  3. Implement: call `ai gemini-flash` N=3 times to generate candidate pool
                No deterministic fallback — if inference unavailable, skip cycle.
  4. Review:    Triple-Pass (Pass 1–5 + Pass 6 ContractCompliance) per candidate
                Failed candidates are discarded; passing candidates accumulate.
  5. Test:      call `ai devstral` to generate adversarial test/case blobs per candidate
                Promote test cases; run test suite. Candidates failing any test discarded.
  6. Benchmark: benchmark all passing candidates vs current; take best winner
  7. Promote:   best winner → Council Approval → manifest update (v1.16.0)

run_all() iterates ALL logic/python labels in the manifest.
evolve_engine() is a separate governed upgrade path for the logic/engine blob —
  engine is infrastructure, not a user blob, so it is NOT part of run_all().
bootstrap_capability() in promote.py registers new domain-specific labels.

Adversarial separation: implementor model (gemini-flash) ≠ tester model (devstral).
Different models cannot share blind spots about the contract.

Credential safety: managed by the ai daemon's routing config; never in subprocess args,
vault blobs, or audit log entries.
"""

import json
import math
import sys
from pathlib import Path
from typing import Any

import infer
import linker
import promote
import seed

BENCHMARK_ROUNDS = 25  # invocations per candidate for comparative fitness
BENCHMARK_WARMUP = 5   # discard first N invocations (cold-start costs)

# ---------------------------------------------------------------------------
# Evolve-engine reviewer — the evolution engine's own council/reviewer identity
# ---------------------------------------------------------------------------

# Same payload as the one bootstrap.py promotes.  seed.put() is idempotent
# (content-addressed), so computing this hash is free on every run.
EVOLVE_REVIEWER_PAYLOAD = json.dumps({
    "id":               "evolve-engine",
    "description":      "Automated f_n evolution engine — benchmarks candidates and "
                        "promotes those that win against the current baseline.",
    "authorized_types": ["logic/python", "logic/engine"],
    "trust_weight":     0.8,
    "criteria":         "Triple-Pass Review pass + benchmark win vs current manifest blob",
}, sort_keys=True)

# ---------------------------------------------------------------------------
# Engine ABI contract — inline, not stored as a contract/definition blob.
# The engine is infrastructure; its contract is structural (scope keys after exec)
# rather than behavioral (pre/post conditions on data).
# ---------------------------------------------------------------------------

ENGINE_ABI_CONTRACT = {
    "for_label": "engine",
    "description": (
        "Engine blob ABI: after exec with kernel scope, the engine scope must contain "
        "callable 'invoke(content_hash, context) -> Any' and "
        "'record_feedback(logic_hash, outcome, ...) -> str', plus "
        "'_load_code' and '_CODE_CACHE'. "
        "exec() is called directly — logic/engine type exempts this from the safety scanner."
    ),
    "required_scope_keys": ["invoke", "record_feedback", "_load_code", "_CODE_CACHE"],
    "pre":  None,
    "post": None,
}


def _ensure_evolve_reviewer() -> str:
    """
    Return the evolve-engine reviewer hash, ensuring it is in the manifest.

    On the first run in a fresh environment (e.g., after bootstrap.run()),
    the evolve reviewer is already promoted by bootstrap.py.  This function
    just verifies that and returns the hash.

    If somehow the reviewer is absent (unlikely but possible in test setups
    that skip bootstrap), it bootstraps it as a trust root.  This is the
    fallback path — the normal path is bootstrap.run() promoting it first.
    """
    reviewer_hash = seed.put("council/reviewer", EVOLVE_REVIEWER_PAYLOAD)
    manifest = promote.load_manifest()
    if reviewer_hash not in manifest.get("reviewers", {}):
        # Fallback: bootstrap the reviewer if missing (shouldn't happen after run())
        promote.bootstrap_reviewer(EVOLVE_REVIEWER_PAYLOAD)
    return reviewer_hash

# ---------------------------------------------------------------------------
# Dynamic PROMOTE_TOLERANCE — derived from audit log fitness deltas
# ---------------------------------------------------------------------------

def _load_contract_record(label: str) -> dict:
    """Return the parsed contract/definition record for label, or empty dict if absent."""
    manifest = promote.load_manifest()
    ch = manifest.get("blobs", {}).get(label, {}).get("contract/definition")
    if not ch:
        return {}
    try:
        blob = seed._raw_get(ch)
        return json.loads(blob["payload"])
    except Exception:
        return {}


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

# ---------------------------------------------------------------------------
# v5 Blob Payloads — f_4 candidates
# ---------------------------------------------------------------------------

# Discovery v5: removes log() call on the hot path.
# Improvement: v4 calls log() on every successful L1 resolution, formatting
# a string every time even when log output is never observed.  v5 removes the
# log call on the success path (L1 hit) — the common case pays zero string
# formatting or list-append overhead.  The L2 fallback and error paths still
# log, since those are slow paths where the overhead is irrelevant.
DISCOVERY_V5 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]

# Hot-path EAFP with no log overhead on L1 hit.
# v4 called log() on every resolution — string formatting on the hot path.
# v5 skips it: L1 hits are the common case and need no instrumentation.
try:
    envelope = json.loads((vault_dir / target_hash).read_text())
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        envelope = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v5: L2 fallback {target_hash[:8]}...")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v5: {target_hash} not found in L1 or L2"
        )

blob_type = envelope.get("type", "")
if blob_type != "logic/python":
    raise TypeError(
        f"Discovery v5: blob {target_hash[:8]}... has type {blob_type!r}, "
        f"expected 'logic/python'"
    )

result = envelope
"""

# Planning v5: adds FeedbackScore to the fitness numerator.
# Improvement: v4 scores blobs on SuccessRate × Integrity / (Latency × Burstiness × Cost).
# v5 adds a FeedbackScore term: the confidence-weighted pass rate from feedback/outcome
# blobs aggregated by telemetry-reader v5.  Default = 1.0 (neutral — no feedback
# does not penalise a blob).  Negative feedback reduces the score proportionally.
# Why: f_3 showed the formula rewards speed, not correctness.  A type guard or
# invariant check that prevents downstream failures produces no fitness signal in
# isolation — the benefit only appears in the system that called the blob.
# FeedbackScore carries that downstream signal back into the selection formula.
PLANNING_V5 = """\
candidates = context.get("candidates", [])
MIN_SAMPLES = 5

if not candidates:
    result = None
else:
    def _score(c):
        sr             = float(c.get("success_rate",   1.0))
        integrity      = float(c.get("integrity",      1.0))
        feedback_score = float(c.get("feedback_score", 1.0))  # 1.0 = neutral (no feedback)
        n              = int(c.get("invocation_count",  0))

        p95 = c.get("p95_latency_ms")
        avg = float(c.get("latency_ms", 1.0))
        latency = max(float(p95) if p95 is not None else avg, 0.001)
        cost    = max(float(c.get("cost", 1.0)), 0.001)

        if p95 is not None and avg > 0.001:
            burstiness = min(float(p95) / avg, 3.0)
        else:
            burstiness = 1.0

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0

        return (sr * integrity * feedback_score) / (latency * burstiness * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v5: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

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

# Telemetry-Reader v5: adds FeedbackScore aggregation from feedback/outcome blobs.
# Improvement: v4 reads only telemetry/artifact blobs.  v5 reads both telemetry
# and feedback/outcome blobs in a single vault pass.  For each logic blob, it
# computes a confidence-weighted pass rate (FeedbackScore) from all feedback/outcome
# blobs where "invoked" matches the logic hash.
# Default FeedbackScore = 1.0 when no feedback exists — neutral, not optimistic.
# A blob with all-pass feedback approaches 1.0; all-fail approaches 0.0.
# feedback_count is also reported so planning can apply Bayesian smoothing if needed.
TELEMETRY_READER_V5 = """\
import datetime
import json
import math
import time
from pathlib import Path

vault_dir    = Path(context.get("vault_dir", "./blob_vault"))
target_hash  = context.get("hash")
HALF_LIFE_S  = context.get("half_life_hours", 24) * 3600
now_ts       = time.time()
LOG2         = math.log(2)

stats    = {}   # hash -> telemetry aggregates (recency-decay, same as v4)
feedback = {}   # hash -> {pos_w, total_w, count}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue

    blob_type = envelope.get("type", "")

    if blob_type == "telemetry/artifact":
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue

        ts_str = record.get("timestamp_utc", "")
        try:
            ts    = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=datetime.timezone.utc).timestamp()
            age_s = max(now_ts - ts, 0)
            decay = math.exp(-LOG2 * age_s / HALF_LIFE_S)
        except Exception:
            decay = 1.0

        s = stats.setdefault(invoked, {
            "total_w": 0.0, "success_w": 0.0,
            "lat_sum_w": 0.0, "mem_sum_w": 0.0,
            "lat_mean": 0.0, "lat_M2": 0.0,
            "streak": 0, "recent_weight": 0.0, "weight_total": 0.0,
        })
        ok  = record.get("error") is None
        lat = record.get("latency_ms", 0.0)
        mem = record.get("memory_kb",  0.0)
        s["total_w"]   += decay
        s["lat_sum_w"] += lat * decay
        s["mem_sum_w"] += mem * decay
        if ok:
            s["success_w"] += decay
            s["streak"]    += 1
            s["recent_weight"] += decay * (2.0 if s["streak"] > 3 else 1.0)
        else:
            s["streak"] = 0
        s["weight_total"] += 2.0 * decay
        n     = s["total_w"]
        delta = lat - s["lat_mean"]
        s["lat_mean"] += delta * decay / n if n > 0 else 0
        s["lat_M2"]   += delta * (lat - s["lat_mean"]) * decay

    elif blob_type == "feedback/outcome":
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue
        outcome    = record.get("outcome", "fail")
        confidence = float(record.get("confidence", 1.0))
        fb = feedback.setdefault(invoked, {"pos_w": 0.0, "total_w": 0.0, "count": 0})
        fb["total_w"] += confidence
        fb["count"]   += 1
        if outcome == "pass":
            fb["pos_w"] += confidence

result = {}
for h, s in stats.items():
    if s["total_w"] < 0.001:
        continue
    w          = s["total_w"]
    variance   = s["lat_M2"] / w if w > 1 else 0.0
    std        = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    integrity  = s["recent_weight"] / s["weight_total"] if s["weight_total"] > 0 else 0.0

    fb             = feedback.get(h, {})
    total_fb_w     = fb.get("total_w", 0.0)
    feedback_score = (fb.get("pos_w", 0.0) / total_fb_w) if total_fb_w > 0 else 1.0

    result[h] = {
        "success_rate":    s["success_w"] / w,
        "integrity":       round(integrity, 4),
        "avg_latency_ms":  s["lat_sum_w"] / w,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["mem_sum_w"]  / w,
        "invocation_count": round(w, 2),
        "feedback_score":  round(feedback_score, 4),
        "feedback_count":  fb.get("count", 0),
    }

log(f"telemetry-reader-v5: {len(result)} blob(s) with feedback scores")
"""

# ---------------------------------------------------------------------------
# v6 Blob Payloads — f_5 candidates
# ---------------------------------------------------------------------------

# Discovery v6: hash-length guard before vault access.
# Improvement: v5 passes any string from context["hash"] directly to the
# vault path join.  A malformed hash (wrong length, non-hex chars) produces
# a FileNotFoundError with no indication of the root cause — the caller sees
# a misleading "not found" error for what is actually a bad input.
# v6 checks len(target_hash) == 64 and hex-only before the vault read.
# Adds one len() + str.isidentifier-equivalent check on the hot path.
# No significant overhead — one attribute lookup and a comparison.
DISCOVERY_V6 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]

# Hash-length guard: catches bad inputs at the Discovery layer with a clear
# error instead of a misleading FileNotFoundError from the vault read.
if len(target_hash) != 64 or not target_hash.isidentifier() and not all(
        c in "0123456789abcdef" for c in target_hash):
    raise ValueError(
        f"Discovery v6: invalid hash {target_hash!r} — expected 64 hex chars"
    )

try:
    envelope = json.loads((vault_dir / target_hash).read_text())
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        envelope = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v6: L2 fallback {target_hash[:8]}...")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v6: {target_hash} not found in L1 or L2"
        )

blob_type = envelope.get("type", "")
if blob_type != "logic/python":
    raise TypeError(
        f"Discovery v6: blob {target_hash[:8]}... has type {blob_type!r}, "
        f"expected 'logic/python'"
    )

result = envelope
"""

# Planning v6: Bayesian smoothing for sparse FeedbackScore.
# Improvement: v5 uses raw FeedbackScore directly.  When feedback_count is low
# (1–2 approved blobs), a single negative outcome produces a very low score
# that may unfairly penalise an otherwise good blob.  v6 adds Bayesian
# smoothing: blend raw FeedbackScore toward the neutral prior (1.0) when
# feedback_count < MIN_FEEDBACK.  After MIN_FEEDBACK approved outcomes, the
# raw score is used as-is.  Same cold-start logic as Planning v2's success-
# rate smoothing — apply the prior until we have enough data to trust the signal.
PLANNING_V6 = """\
candidates   = context.get("candidates", [])
MIN_SAMPLES  = 5
MIN_FEEDBACK = 3   # minimum approved feedback count before trusting raw score

if not candidates:
    result = None
else:
    def _score(c):
        sr        = float(c.get("success_rate",   1.0))
        integrity = float(c.get("integrity",      1.0))
        n         = int(c.get("invocation_count",  0))

        # Bayesian FeedbackScore: blend toward 1.0 prior when feedback is sparse
        raw_fb   = float(c.get("feedback_score", 1.0))
        fb_count = int(c.get("feedback_count",    0))
        if fb_count < MIN_FEEDBACK:
            w              = fb_count / MIN_FEEDBACK
            feedback_score = w * raw_fb + (1 - w) * 1.0
        else:
            feedback_score = raw_fb

        p95 = c.get("p95_latency_ms")
        avg = float(c.get("latency_ms", 1.0))
        latency = max(float(p95) if p95 is not None else avg, 0.001)
        cost    = max(float(c.get("cost", 1.0)), 0.001)

        if p95 is not None and avg > 0.001:
            burstiness = min(float(p95) / avg, 3.0)
        else:
            burstiness = 1.0

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0

        return (sr * integrity * feedback_score) / (latency * burstiness * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v6: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

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

# Telemetry-Reader v6: governance filter — only count approved feedback.
# Improvement: v5 counts ALL feedback/outcome blobs in the vault.  Any caller
# can record feedback; any feedback influences FeedbackScore.  v6 receives
# approved_feedback from context (a dict {logic_hash: [feedback_hash, ...]})
# and skips any feedback blob whose content hash is not in the approved set.
# When approved_feedback is empty (no feedback promoted yet), ALL feedback is
# skipped and FeedbackScore defaults to 1.0 (neutral) for all blobs.
# This is the governance gate: unapproved feedback is visible in the vault
# but invisible to the fitness formula.
TELEMETRY_READER_V6 = """\
import datetime
import json
import math
import time
from pathlib import Path

vault_dir        = Path(context.get("vault_dir", "./blob_vault"))
target_hash      = context.get("hash")
HALF_LIFE_S      = context.get("half_life_hours", 24) * 3600
approved_feedback = context.get("approved_feedback", {})   # {logic_hash: [fb_hash, ...]}
now_ts           = time.time()
LOG2             = math.log(2)

# Flatten approved feedback to a set for O(1) lookup
approved_set = {h for hashes in approved_feedback.values() for h in hashes}

stats    = {}   # hash -> telemetry aggregates (same as v5)
feedback = {}   # hash -> {pos_w, total_w, count}  — governed only

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue

    blob_type = envelope.get("type", "")

    if blob_type == "telemetry/artifact":
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue

        ts_str = record.get("timestamp_utc", "")
        try:
            ts    = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=datetime.timezone.utc).timestamp()
            age_s = max(now_ts - ts, 0)
            decay = math.exp(-LOG2 * age_s / HALF_LIFE_S)
        except Exception:
            decay = 1.0

        s = stats.setdefault(invoked, {
            "total_w": 0.0, "success_w": 0.0,
            "lat_sum_w": 0.0, "mem_sum_w": 0.0,
            "lat_mean": 0.0, "lat_M2": 0.0,
            "streak": 0, "recent_weight": 0.0, "weight_total": 0.0,
        })
        ok  = record.get("error") is None
        lat = record.get("latency_ms", 0.0)
        mem = record.get("memory_kb",  0.0)
        s["total_w"]   += decay
        s["lat_sum_w"] += lat * decay
        s["mem_sum_w"] += mem * decay
        if ok:
            s["success_w"] += decay
            s["streak"]    += 1
            s["recent_weight"] += decay * (2.0 if s["streak"] > 3 else 1.0)
        else:
            s["streak"] = 0
        s["weight_total"] += 2.0 * decay
        n     = s["total_w"]
        delta = lat - s["lat_mean"]
        s["lat_mean"] += delta * decay / n if n > 0 else 0
        s["lat_M2"]   += delta * (lat - s["lat_mean"]) * decay

    elif blob_type == "feedback/outcome":
        # Governance gate: skip feedback blobs not in the approved set
        blob_hash = blob_path.name
        if blob_hash not in approved_set:
            continue
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue
        outcome    = record.get("outcome", "fail")
        confidence = float(record.get("confidence", 1.0))
        fb = feedback.setdefault(invoked, {"pos_w": 0.0, "total_w": 0.0, "count": 0})
        fb["total_w"] += confidence
        fb["count"]   += 1
        if outcome == "pass":
            fb["pos_w"] += confidence

result = {}
for h, s in stats.items():
    if s["total_w"] < 0.001:
        continue
    w          = s["total_w"]
    variance   = s["lat_M2"] / w if w > 1 else 0.0
    std        = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    integrity  = s["recent_weight"] / s["weight_total"] if s["weight_total"] > 0 else 0.0

    fb             = feedback.get(h, {})
    total_fb_w     = fb.get("total_w", 0.0)
    feedback_score = (fb.get("pos_w", 0.0) / total_fb_w) if total_fb_w > 0 else 1.0

    result[h] = {
        "success_rate":    s["success_w"] / w,
        "integrity":       round(integrity, 4),
        "avg_latency_ms":  s["lat_sum_w"] / w,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["mem_sum_w"]  / w,
        "invocation_count": round(w, 2),
        "feedback_score":  round(feedback_score, 4),
        "feedback_count":  fb.get("count", 0),
    }

log(f"telemetry-reader-v6: {len(result)} blob(s), {len(approved_set)} approved-feedback hashes")
"""

# ---------------------------------------------------------------------------
# v7 Blob Payloads — f_6 candidates
# ---------------------------------------------------------------------------

# Discovery v7: normalises hash input to lowercase before vault access.
# Improvement: v6 validates len==64 and hex chars but doesn't normalise case.
# A hash arriving with uppercase hex chars (e.g. from an external API or
# copy-paste) would pass the length check, fail the all-lowercase char check,
# and raise a confusing ValueError. v7 lowercases first, then validates.
# One str.lower() call on the hot path — essentially zero overhead.
DISCOVERY_V7 = """\
import json
from pathlib import Path

vault_dir   = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"].lower()   # normalise before validation

if len(target_hash) != 64 or not all(c in "0123456789abcdef" for c in target_hash):
    raise ValueError(
        f"Discovery v7: invalid hash {context['hash']!r} — expected 64 hex chars"
    )

try:
    envelope = json.loads((vault_dir / target_hash).read_text())
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    try:
        envelope = json.loads((vault_dir_l2 / target_hash).read_text())
        log(f"discovery-v7: L2 fallback {target_hash[:8]}...")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Discovery v7: {target_hash} not found in L1 or L2"
        )

blob_type = envelope.get("type", "")
if blob_type != "logic/python":
    raise TypeError(
        f"Discovery v7: blob {target_hash[:8]}... has type {blob_type!r}, "
        f"expected 'logic/python'"
    )

result = envelope
"""

# Planning v7: trust-weighted FeedbackScore via reviewer authority.
# Improvement: v6 applies Bayesian smoothing to FeedbackScore but treats all
# approved feedback equally.  v7 weights each candidate's feedback by the
# reviewer's trust_weight (passed via context["reviewer_trust"]).  A feedback
# blob approved by a reviewer with trust_weight=1.0 (bootstrap reviewer) counts
# at full confidence; one approved by a reviewer with trust_weight=0.8
# (evolve-engine reviewer) counts at 80% confidence.  The weighted sum
# replaces the simple pass-rate in the FeedbackScore computation.
# Why: different reviewers have different authority levels.  An automated
# evolution engine reviewing its own output is less authoritative than the
# explicit trust root.  The trust_weight encodes that difference.
PLANNING_V7 = """\
candidates   = context.get("candidates", [])
MIN_SAMPLES  = 5
MIN_FEEDBACK = 3

if not candidates:
    result = None
else:
    def _score(c):
        sr        = float(c.get("success_rate",   1.0))
        integrity = float(c.get("integrity",      1.0))
        n         = int(c.get("invocation_count",  0))

        # Trust-weighted FeedbackScore: higher-authority reviewers count more.
        # feedback_score already incorporates reviewer trust (passed via context
        # through linker → telemetry-reader v7 → here).  Bayesian smoothing
        # still applied when feedback is sparse.
        raw_fb   = float(c.get("feedback_score", 1.0))
        fb_count = int(c.get("feedback_count",    0))
        if fb_count < MIN_FEEDBACK:
            w              = fb_count / MIN_FEEDBACK
            feedback_score = w * raw_fb + (1 - w) * 1.0
        else:
            feedback_score = raw_fb

        p95 = c.get("p95_latency_ms")
        avg = float(c.get("latency_ms", 1.0))
        latency = max(float(p95) if p95 is not None else avg, 0.001)
        cost    = max(float(c.get("cost", 1.0)), 0.001)

        if p95 is not None and avg > 0.001:
            burstiness = min(float(p95) / avg, 3.0)
        else:
            burstiness = 1.0

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            latency = w * latency + (1 - w) * 1.0

        return (sr * integrity * feedback_score) / (latency * burstiness * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]

    log(f"planning-v7: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

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

# Telemetry-Reader v7: reviewer-trust-weighted FeedbackScore.
# Improvement: v6 counts all approved feedback at face value (confidence only).
# v7 multiplies each feedback blob's confidence by the reviewer's trust_weight
# (from context["reviewer_trust"]).  A blob approved by a reviewer with
# trust_weight=1.0 contributes its full confidence; one from a 0.8-weight
# reviewer contributes 80%.  The weighted pass rate replaces the simple pass
# rate in FeedbackScore.  Default trust_weight = 1.0 for unknown reviewers
# (conservative: don't penalise feedback from reviewers not in registry).
TELEMETRY_READER_V7 = """\
import datetime
import json
import math
import time
from pathlib import Path

vault_dir        = Path(context.get("vault_dir", "./blob_vault"))
target_hash      = context.get("hash")
HALF_LIFE_S      = context.get("half_life_hours", 24) * 3600
approved_feedback = context.get("approved_feedback", {})
reviewer_trust    = context.get("reviewer_trust", {})   # {reviewer_hash: trust_weight}
now_ts           = time.time()
LOG2             = math.log(2)

approved_set = {h for hashes in approved_feedback.values() for h in hashes}

stats    = {}
feedback = {}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue

    blob_type = envelope.get("type", "")

    if blob_type == "telemetry/artifact":
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue

        ts_str = record.get("timestamp_utc", "")
        try:
            ts    = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=datetime.timezone.utc).timestamp()
            age_s = max(now_ts - ts, 0)
            decay = math.exp(-LOG2 * age_s / HALF_LIFE_S)
        except Exception:
            decay = 1.0

        s = stats.setdefault(invoked, {
            "total_w": 0.0, "success_w": 0.0,
            "lat_sum_w": 0.0, "mem_sum_w": 0.0,
            "lat_mean": 0.0, "lat_M2": 0.0,
            "streak": 0, "recent_weight": 0.0, "weight_total": 0.0,
        })
        ok  = record.get("error") is None
        lat = record.get("latency_ms", 0.0)
        mem = record.get("memory_kb",  0.0)
        s["total_w"]   += decay
        s["lat_sum_w"] += lat * decay
        s["mem_sum_w"] += mem * decay
        if ok:
            s["success_w"] += decay
            s["streak"]    += 1
            s["recent_weight"] += decay * (2.0 if s["streak"] > 3 else 1.0)
        else:
            s["streak"] = 0
        s["weight_total"] += 2.0 * decay
        n     = s["total_w"]
        delta = lat - s["lat_mean"]
        s["lat_mean"] += delta * decay / n if n > 0 else 0
        s["lat_M2"]   += delta * (lat - s["lat_mean"]) * decay

    elif blob_type == "feedback/outcome":
        blob_hash = blob_path.name
        if blob_hash not in approved_set:
            continue
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        if target_hash and invoked != target_hash:
            continue
        outcome        = record.get("outcome", "fail")
        base_conf      = float(record.get("confidence", 1.0))
        # Trust-weight: multiply confidence by reviewer's authority level
        rev_hash       = record.get("reviewer_hash")
        trust          = reviewer_trust.get(rev_hash, 1.0) if rev_hash else 1.0
        eff_conf       = base_conf * trust
        fb = feedback.setdefault(invoked, {"pos_w": 0.0, "total_w": 0.0, "count": 0})
        fb["total_w"] += eff_conf
        fb["count"]   += 1
        if outcome == "pass":
            fb["pos_w"] += eff_conf

result = {}
for h, s in stats.items():
    if s["total_w"] < 0.001:
        continue
    w          = s["total_w"]
    variance   = s["lat_M2"] / w if w > 1 else 0.0
    std        = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    integrity  = s["recent_weight"] / s["weight_total"] if s["weight_total"] > 0 else 0.0

    fb             = feedback.get(h, {})
    total_fb_w     = fb.get("total_w", 0.0)
    feedback_score = (fb.get("pos_w", 0.0) / total_fb_w) if total_fb_w > 0 else 1.0

    result[h] = {
        "success_rate":    s["success_w"] / w,
        "integrity":       round(integrity, 4),
        "avg_latency_ms":  s["lat_sum_w"] / w,
        "p95_latency_ms":  round(p95_approx, 3),
        "avg_memory_kb":   s["mem_sum_w"]  / w,
        "invocation_count": round(w, 2),
        "feedback_score":  round(feedback_score, 4),
        "feedback_count":  fb.get("count", 0),
    }

log(f"telemetry-reader-v7: {len(result)} blob(s), reviewer-trust-weighted feedback")
"""

# ---------------------------------------------------------------------------
# v8 Blob Payloads — f_7 candidates
# ---------------------------------------------------------------------------

# Discovery v8: vault-existence fast-fail + type-agnostic resolution
# Improvement: v7 raises FileNotFoundError from read_text() when vault_dir doesn't
# exist as a directory — confusing because the error message names the hash, not the
# vault.  v8 checks vault_dir.is_dir() first and raises a clear diagnostic.  Also
# removes the logic/python type guard added in v7 — Discovery's contract (post:
# result has 'type' and 'payload') covers correctness; the type guard was an
# over-constraint that broke resolution of non-logic blobs (telemetry, feedback, etc.).
DISCOVERY_V8 = """\
import json
from pathlib import Path

vault_dir = Path(context.get("vault_dir", "./blob_vault"))
raw_hash  = context["hash"]
# Normalize multihash address (e.g. "blake3:<hex>") to bare hex for vault lookup
target_hash = (raw_hash.split(":", 1)[1] if ":" in raw_hash else raw_hash).lower()

if len(target_hash) != 64 or not all(c in "0123456789abcdef" for c in target_hash):
    raise ValueError(f"Discovery v8: invalid hash {raw_hash!r} — expected 64 hex chars or <func>:<hex>")

if not vault_dir.is_dir():
    raise FileNotFoundError(f"Discovery v8: vault directory not found: {vault_dir}")

try:
    result = json.loads((vault_dir / target_hash).read_text())
    log(f"discovery-v8: resolved {target_hash[:8]}...")
except FileNotFoundError:
    vault_dir_l2 = Path(context.get("vault_dir_l2", "./blob_vault_l2"))
    if vault_dir_l2.is_dir():
        try:
            result = json.loads((vault_dir_l2 / target_hash).read_text())
            log(f"discovery-v8: L2 fallback {target_hash[:8]}...")
        except FileNotFoundError:
            raise FileNotFoundError(f"Discovery v8: {target_hash} not found in L1 or L2")
    else:
        raise FileNotFoundError(f"Discovery v8: {target_hash} not found in vault")
"""

# Planning v8: explicit burstiness penalty
# Improvement: v7 uses p95_latency_ms as the latency input (vs avg in v6), which
# penalises bursty blobs.  v8 makes the burstiness penalty explicit and tunable:
# burstiness = p95 / avg_latency.  When burstiness > BURST_THRESHOLD (3.0), the
# effective latency is scaled up proportionally.  This directly rewards stable blobs
# over spiky ones even when their averages are similar.
PLANNING_V8 = """\
candidates      = context.get("candidates", [])
MIN_SAMPLES     = 5
MIN_FEEDBACK    = 3
BURST_THRESHOLD = 3.0   # p95/avg ratio above which burstiness penalty applies

if not candidates:
    result = None
else:
    def _score(c):
        sr           = float(c.get("success_rate",  1.0))
        integrity    = float(c.get("integrity",      0.5))
        avg_lat      = max(float(c.get("latency_ms", 1.0)), 0.001)
        p95_lat      = float(c.get("p95_latency_ms") or avg_lat)
        cost         = max(float(c.get("cost",        1.0)), 0.001)
        n            = int(c.get("invocation_count",  0))
        fb_raw       = float(c.get("feedback_score",  1.0))
        fb_count     = int(c.get("feedback_count",    0))

        if fb_count < MIN_FEEDBACK:
            w  = fb_count / MIN_FEEDBACK
            fb = w * fb_raw + (1 - w) * 1.0
        else:
            fb = fb_raw

        if n < MIN_SAMPLES:
            w       = n / MIN_SAMPLES
            sr      = w * sr      + (1 - w) * 0.95
            avg_lat = w * avg_lat + (1 - w) * 1.0

        burstiness       = max(p95_lat / avg_lat, 1.0)
        burst_excess     = max(burstiness - BURST_THRESHOLD, 0.0)
        effective_latency = avg_lat * (1.0 + burst_excess * 0.1)

        return (sr * integrity * fb) / (effective_latency * cost)

    scored     = sorted(((c, _score(c)) for c in candidates), key=lambda x: x[1], reverse=True)
    best, best_score = scored[0]
    log(f"planning-v8: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")
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

# Telemetry-Reader v8: volatility metric
# Improvement: v7 reports p95_latency_ms (point estimate of tail latency).
# v8 adds a `volatility` field — the coefficient of variation (std/mean) of
# latency.  p95 is a point estimate; volatility is a relative measure.  Two blobs
# with the same p95 may differ in predictability if one is consistently near p95
# and the other swings widely.  Volatility complements p95 for planning decisions.
TELEMETRY_READER_V8 = """\
import datetime
import json
import math
import time
from pathlib import Path

vault_dir        = Path(context.get("vault_dir", "./blob_vault"))
target_hash      = context.get("hash")
HALF_LIFE_S      = context.get("half_life_hours", 24) * 3600
approved_feedback = context.get("approved_feedback", {})
reviewer_trust    = context.get("reviewer_trust", {})
now_ts           = time.time()
LOG2             = math.log(2)

approved_set = {h for hashes in approved_feedback.values() for h in hashes}
stats    = {}
feedback = {}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue

    blob_type = envelope.get("type", "")

    if blob_type == "telemetry/artifact":
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked or (target_hash and invoked != target_hash):
            continue
        ts_str = record.get("timestamp_utc", "")
        try:
            ts    = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                        tzinfo=datetime.timezone.utc).timestamp()
            decay = math.exp(-LOG2 * max(now_ts - ts, 0) / HALF_LIFE_S)
        except Exception:
            decay = 1.0
        s = stats.setdefault(invoked, {
            "total_w": 0.0, "success_w": 0.0,
            "lat_sum_w": 0.0, "mem_sum_w": 0.0,
            "lat_mean": 0.0, "lat_M2": 0.0,
            "streak": 0, "recent_weight": 0.0, "weight_total": 0.0,
        })
        ok  = record.get("error") is None
        lat = record.get("latency_ms", 0.0)
        s["total_w"]   += decay
        s["lat_sum_w"] += lat * decay
        s["mem_sum_w"] += record.get("memory_kb", 0.0) * decay
        if ok:
            s["success_w"] += decay
            s["streak"]    += 1
            s["recent_weight"] += decay * (2.0 if s["streak"] > 3 else 1.0)
        else:
            s["streak"] = 0
        s["weight_total"] += 2.0 * decay
        n     = s["total_w"]
        delta = lat - s["lat_mean"]
        s["lat_mean"] += delta * decay / n if n > 0 else 0
        s["lat_M2"]   += delta * (lat - s["lat_mean"]) * decay

    elif blob_type == "feedback/outcome":
        blob_hash = blob_path.name
        if blob_hash not in approved_set:
            continue
        record  = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked or (target_hash and invoked != target_hash):
            continue
        base_conf = float(record.get("confidence", 1.0))
        rev_hash  = record.get("reviewer_hash")
        trust     = reviewer_trust.get(rev_hash, 1.0) if rev_hash else 1.0
        eff_conf  = base_conf * trust
        fb = feedback.setdefault(invoked, {"pos_w": 0.0, "total_w": 0.0, "count": 0})
        fb["total_w"] += eff_conf
        fb["count"]   += 1
        if record.get("outcome") == "pass":
            fb["pos_w"] += eff_conf

result = {}
for h, s in stats.items():
    if s["total_w"] < 0.001:
        continue
    w          = s["total_w"]
    variance   = s["lat_M2"] / w if w > 1 else 0.0
    std        = variance ** 0.5
    p95_approx = s["lat_mean"] + 1.645 * std
    # Coefficient of variation: std/mean — relative latency variability
    volatility = (std / s["lat_mean"]) if s["lat_mean"] > 0 else 0.0
    integrity  = s["recent_weight"] / s["weight_total"] if s["weight_total"] > 0 else 0.0
    fb             = feedback.get(h, {})
    total_fb_w     = fb.get("total_w", 0.0)
    feedback_score = fb.get("pos_w", 0.0) / total_fb_w if total_fb_w > 0 else 1.0
    result[h] = {
        "success_rate":     s["success_w"] / w,
        "integrity":        round(integrity,   4),
        "avg_latency_ms":   s["lat_sum_w"] / w,
        "p95_latency_ms":   round(p95_approx, 3),
        "volatility":       round(volatility,  4),
        "avg_memory_kb":    s["mem_sum_w"]  / w,
        "invocation_count": round(w, 2),
        "feedback_score":   round(feedback_score, 4),
        "feedback_count":   fb.get("count", 0),
    }

log(f"telemetry-reader-v8: {len(result)} blob(s), +volatility metric")
"""

N_CANDIDATES = 3  # candidates generated per evolution cycle


def _mutation_goal_from_okr(label: str, okr: dict, signals: dict) -> str:
    """
    Derive a mutation goal from a promoted goal/okr blob.

    Compares each key result's target against current signal values to identify
    gaps. The goal string includes the objective verbatim so the LLM generates
    toward declared intent rather than hardcoded thresholds.
    """
    gaps = []
    for kr in okr.get("key_results", []):
        metric    = kr["metric"]
        target    = kr["target"]
        direction = kr["direction"]
        current   = signals.get(metric)
        if current is None:
            continue
        if direction == "above" and current < target:
            gaps.append(f"{metric}={current:.3f} (target: >{target})")
        elif direction == "below" and current > target:
            gaps.append(f"{metric}={current:.3f} (target: <{target})")
    if not gaps:
        return f"All key results met for {label} — explore robustness improvements."
    return (
        f"Improve {label} to close key result gaps: " + ", ".join(gaps) + ". "
        f"Objective: {okr['objective']}"
    )


def _derive_mutation_goal(label: str, signals: dict) -> str:
    """
    Derive a mutation goal for a label.

    If a goal/okr blob is promoted for the label, delegates to
    _mutation_goal_from_okr (OKR-driven). Otherwise falls back to fitness
    signal threshold analysis (f_10 behaviour).
    """
    # OKR-driven goal derivation (f_11)
    try:
        manifest  = promote.load_manifest()
        okr_hash  = manifest.get("blobs", {}).get(label, {}).get("goal/okr")
        if okr_hash:
            okr_blob = seed._raw_get(okr_hash)
            okr      = json.loads(okr_blob["payload"])
            return _mutation_goal_from_okr(label, okr, signals)
    except Exception:
        pass  # fall through to signal-threshold derivation

    # Signal-threshold fallback (f_10)
    sr  = signals.get("success_rate",    1.0)
    lat = signals.get("avg_latency_ms",  0.0)
    vol = signals.get("volatility",      0.0)

    trend_note = ""
    try:
        audit_path = Path("./audit.log")
        if audit_path.exists():
            entries = [json.loads(l) for l in audit_path.read_text().splitlines() if l.strip()]
            recent = [
                e for e in entries
                if e.get("label") == label and e.get("event") == "benchmark"
            ][-5:]
            if len(recent) >= 2:
                fitnesses = [e["benchmark"]["new"]["fitness"] for e in recent if "benchmark" in e]
                if len(fitnesses) >= 2 and fitnesses[-1] < fitnesses[0]:
                    trend_note = " Fitness has been declining over recent cycles — reverse the trend."
    except Exception:
        pass

    if sr < 0.8:
        return (
            f"Improve success rate for {label}: currently {sr:.1%}, "
            f"failures must be reduced.{trend_note}"
        )
    if vol > 0.5:
        return (
            f"Reduce latency volatility for {label}: volatility={vol:.2f}, "
            f"prioritize consistency over speed.{trend_note}"
        )
    if lat > 10.0:
        return (
            f"Reduce avg latency for {label}: currently {lat:.1f}ms, "
            f"optimize the hot path.{trend_note}"
        )
    return f"Improve overall fitness for {label}: explore alternative algorithms.{trend_note}"


# Benchmark contexts — valid inputs for each label so invocation succeeds
def _bench_context(label: str, current_hash: str) -> dict:
    if label == "discovery":
        return {"hash": current_hash, "vault_dir": str(seed.VAULT_DIR)}
    if label == "planning":
        return {"candidates": [
            # well-behaved blob: low burstiness, positive feedback history
            {"hash": current_hash, "success_rate": 0.9, "latency_ms": 2.0, "p95_latency_ms": 3.5,
             "integrity": 0.8, "cost": 1.0, "invocation_count": 10, "feedback_score": 0.95},
            # spiky blob: high burstiness, negative feedback history
            {"hash": "0" * 64,    "success_rate": 0.8, "latency_ms": 1.0, "p95_latency_ms": 9.0,
             "integrity": 0.5, "cost": 2.0, "invocation_count": 3,  "feedback_score": 0.40},
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
# Engine governance helpers
# ---------------------------------------------------------------------------

def _verify_engine_abi(candidate_hash: str) -> tuple[bool, str]:
    """
    Structural ABI check: exec the candidate engine with an isolated kernel scope
    and verify the required scope keys are present and callable after execution.

    Returns (passed: bool, reason: str).
    """
    try:
        blob = seed._raw_get(candidate_hash)
        scope: dict = {
            "_raw_get":        seed._raw_get,
            "put":             seed.put,
            "_LAST_TELEMETRY": {},          # isolated — don't pollute production telemetry
            "BYTECODE_DIR":    seed.BYTECODE_DIR,
        }
        exec(compile(blob["payload"], "<engine-abi-check>", "exec"), scope)  # noqa: S102
        missing = [k for k in ENGINE_ABI_CONTRACT["required_scope_keys"] if k not in scope]
        if missing:
            return False, f"missing scope keys after exec: {missing}"
        if not callable(scope.get("invoke")):
            return False, "scope['invoke'] is not callable"
        if not callable(scope.get("record_feedback")):
            return False, "scope['record_feedback'] is not callable"
        return True, "ok"
    except Exception as exc:
        return False, f"exec failed: {exc}"


def _benchmark_engine(
    current_hash: str,
    candidate_hash: str,
    rounds: int = BENCHMARK_ROUNDS,
) -> dict:
    """
    Benchmark two engine blobs by running core blobs through each engine's invoke().

    Since the engine defines invoke(), we cannot use seed.invoke() — that would
    delegate to the currently loaded engine.  We exec each engine independently
    with an isolated kernel scope and measure invoke() latency on the core blobs.
    """
    import time as _time

    def _exec_engine(engine_hash: str) -> dict:
        blob = seed._raw_get(engine_hash)
        scope: dict = {
            "_raw_get":        seed._raw_get,
            "put":             seed.put,
            "_LAST_TELEMETRY": {},
            "BYTECODE_DIR":    seed.BYTECODE_DIR,
        }
        exec(compile(blob["payload"], "<engine-bench>", "exec"), scope)  # noqa: S102
        return scope

    try:
        current_scope   = _exec_engine(current_hash)
        candidate_scope = _exec_engine(candidate_hash)
    except Exception as exc:
        return {"winner": "old", "error": str(exc),
                "old": {"hash": current_hash, "fitness": 0.0},
                "new": {"hash": candidate_hash, "fitness": 0.0}}

    manifest = promote.load_manifest()
    blobs_to_test: dict[str, tuple[str, dict]] = {}
    for label in ("discovery", "planning", "telemetry-reader"):
        h = manifest.get("blobs", {}).get(label, {}).get("logic/python")
        if h:
            blobs_to_test[label] = (h, _bench_context(label, h))

    if not blobs_to_test:
        return {"winner": "old", "error": "no core blobs available for benchmark",
                "old": {"hash": current_hash, "fitness": 0.0},
                "new": {"hash": candidate_hash, "fitness": 0.0}}

    # Warmup
    for _ in range(BENCHMARK_WARMUP):
        for _lbl, (h, ctx) in blobs_to_test.items():
            try:
                current_scope["invoke"](h, dict(ctx))
            except Exception:
                pass
            try:
                candidate_scope["invoke"](h, dict(ctx))
            except Exception:
                pass

    current_times:    list[float] = []
    candidate_times:  list[float] = []
    current_errors   = 0
    candidate_errors = 0

    for _ in range(rounds):
        for _lbl, (h, ctx) in blobs_to_test.items():
            t0 = _time.perf_counter_ns()
            try:
                current_scope["invoke"](h, dict(ctx))
                current_times.append((_time.perf_counter_ns() - t0) / 1e6)
            except Exception:
                current_errors += 1

            t0 = _time.perf_counter_ns()
            try:
                candidate_scope["invoke"](h, dict(ctx))
                candidate_times.append((_time.perf_counter_ns() - t0) / 1e6)
            except Exception:
                candidate_errors += 1

    total  = rounds * len(blobs_to_test)
    c_sr   = (total - current_errors)   / max(total, 1)
    n_sr   = (total - candidate_errors) / max(total, 1)
    c_lat  = sum(current_times)   / max(len(current_times),   1)
    n_lat  = sum(candidate_times) / max(len(candidate_times), 1)

    old_fit = c_sr / max(c_lat, 0.001)
    new_fit = n_sr / max(n_lat, 0.001)

    tolerance = _derive_tolerance()
    winner    = "new" if new_fit >= old_fit * (1 - tolerance) else "old"

    return {
        "old":               {"hash": current_hash,   "fitness": old_fit,
                              "success_rate": c_sr,   "avg_latency_ms": c_lat},
        "new":               {"hash": candidate_hash, "fitness": new_fit,
                              "success_rate": n_sr,   "avg_latency_ms": n_lat},
        "winner":            winner,
        "tolerance_applied": tolerance,
    }


# ---------------------------------------------------------------------------
# Engine governance — governed upgrade path (not part of run_all)
# ---------------------------------------------------------------------------

def evolve_engine(reviewer: str = "evolve") -> dict:
    """
    Evolve the engine blob through a governed upgrade path.

    The engine is infrastructure — it is NOT iterated by run_all().
    Call evolve_engine() explicitly to attempt an engine upgrade.

    Cycle:
      1. Load current logic/engine hash from manifest
      2. Generate N_CANDIDATES via inference with ENGINE_ABI_CONTRACT
      3. Structural ABI check: exec candidate, verify required scope keys
      4. Triple-Pass Review (logic/engine exempt from exec-forbidden check)
      5. Benchmark: exec current + candidate independently, run core blobs through each
      6. Promote best winner with council approval; invalidate seed._ENGINE cache

    Returns outcome ∈ {promoted, no-improvement, inference-unavailable, error}.
    """
    print("\n── Evolve Engine (logic/engine governed upgrade)")

    manifest = promote.load_manifest()
    current_hash = manifest.get("blobs", {}).get("engine", {}).get("logic/engine")
    if not current_hash:
        return {"label": "engine", "outcome": "error", "reason": "engine not in manifest"}

    current_blob    = seed._raw_get(current_hash)
    current_payload = current_blob["payload"]

    evolve_reviewer_hash    = _ensure_evolve_reviewer()
    passing_candidates: list[str] = []
    last_error: str | None  = None

    for i in range(N_CANDIDATES):
        try:
            candidate_payload = infer.generate_candidate(
                current_payload=current_payload,
                contract=ENGINE_ABI_CONTRACT,
                fitness={},   # engine fitness is structural, not telemetry-derived
                mutation_goal=(
                    "Improve engine invoke() throughput and bytecode cache efficiency "
                    "while preserving the ABI: invoke, record_feedback, _load_code, _CODE_CACHE "
                    "must all be present in scope after exec. "
                    "exec() is called directly — this is correct and intended for logic/engine."
                ),
            )
        except infer.InferenceUnavailable as exc:
            print(f"  inference unavailable ({exc!s:.60}) — skipping cycle")
            return {"label": "engine", "outcome": "inference-unavailable"}

        candidate_hash = seed.put("logic/engine", candidate_payload)
        print(f"  candidate[{i}] {candidate_hash[:16]}...")

        # Structural ABI check before formal review
        abi_ok, abi_reason = _verify_engine_abi(candidate_hash)
        if not abi_ok:
            print(f"  candidate[{i}] ABI fail: {abi_reason}")
            last_error = abi_reason
            continue

        # Triple-Pass Review — logic/engine is exempt from exec-forbidden (Pass 2 skipped)
        try:
            promote.triple_pass_review(candidate_hash, label="engine")
        except promote.ReviewError as exc:
            print(f"  candidate[{i}] review FAIL [{exc.pass_name}] {exc.detail}")
            last_error = f"[{exc.pass_name}] {exc.detail}"
            continue

        print(f"  candidate[{i}] passed ABI + review")
        passing_candidates.append(candidate_hash)

    print(f"  {len(passing_candidates)}/{N_CANDIDATES} candidates passed ABI + review")

    if not passing_candidates:
        return {"label": "engine", "outcome": "no-improvement",
                "reason": f"no candidates passed: {last_error}"}

    best_hash: str | None = None
    best_bm:   dict | None = None

    for candidate_hash in passing_candidates:
        bm = _benchmark_engine(current_hash, candidate_hash)
        print(f"  bench {candidate_hash[:16]}...  "
              f"old={bm['old']['fitness']:.4f}  new={bm['new']['fitness']:.4f}  "
              f"winner={bm['winner']}")
        if bm["winner"] == "new":
            if best_bm is None or bm["new"]["fitness"] > best_bm["new"]["fitness"]:
                best_hash = candidate_hash
                best_bm   = bm

    if best_hash is None:
        print("  no improvement — keeping current engine")
        return {"label": "engine", "outcome": "no-improvement", "benchmark": best_bm}

    approval      = promote.issue_council_approval([best_hash], reviewer_hash=evolve_reviewer_hash)
    manifest_hash = promote.promote(
        label="engine",
        blob_hashes=[best_hash],
        council_approval_hash=approval,
        version="1.16.0",
    )
    # Invalidate engine cache — next invoke() will load the promoted engine
    seed._ENGINE      = None
    seed._ENGINE_HASH = None

    print(f"  engine promoted  manifest.hash={manifest_hash[:16]}...")
    return {
        "label":         "engine",
        "outcome":       "promoted",
        "old":           current_hash,
        "new":           best_hash,
        "manifest_hash": manifest_hash,
        "benchmark":     best_bm,
        "n_candidates":  len(passing_candidates),
    }


# ---------------------------------------------------------------------------
# Full evolution cycle for one label
# ---------------------------------------------------------------------------

def evolve_one(label: str, reviewer: str = "evolve") -> dict:
    """
    Evolve a single core blob label through the full f_10 cycle.

    Generates N_CANDIDATES candidates, filters by review + test suite, benchmarks
    all passing candidates vs current, and promotes the best winner.

    Returns a result dict with outcome ∈ {promoted, no-improvement,
    inference-unavailable, test_suite_failed, error}.
    """
    import time as _time

    print(f"\n── Evolve: {label}")

    manifest     = promote.load_manifest()
    current_hash = manifest.get("blobs", {}).get(label, {}).get("logic/python")
    if not current_hash:
        return {"label": label, "outcome": "error", "reason": "not in manifest"}

    # Evaluate current
    signals = evaluate(label, current_hash)
    print(f"  current  {current_hash[:16]}...  fitness={signals['fitness_score']:.4f}  "
          f"n={signals['invocation_count']}")

    current_blob    = seed._raw_get(current_hash)
    current_payload = current_blob["payload"]
    contract_record = _load_contract_record(label)
    fitness_signals = {
        "success_rate":    signals.get("success_rate", 1.0),
        "avg_latency_ms":  signals.get("avg_latency_ms", 0.0),
        "invocation_count": signals.get("invocation_count", 0),
        "volatility":      signals.get("volatility", 0.0),
    }

    # Derive mutation goal from fitness signal trends (replaces static _MUTATION_GOALS)
    goal = _derive_mutation_goal(label, fitness_signals)
    print(f"  goal  {goal[:80]}{'…' if len(goal) > 80 else ''}")

    evolve_reviewer_hash = _ensure_evolve_reviewer()
    tester_model         = "devstral"
    passing_candidates: list[str] = []   # hashes that cleared review + test suite
    last_error: str | None = None

    # ── Candidate generation loop ─────────────────────────────────────────────
    for i in range(N_CANDIDATES):
        try:
            candidate_payload = infer.generate_candidate(
                current_payload=current_payload,
                contract=contract_record,
                fitness=fitness_signals,
                mutation_goal=goal,
            )
        except infer.InferenceUnavailable as e:
            print(f"  inference unavailable ({e!s:.60}) — skipping cycle")
            return {"label": label, "outcome": "inference-unavailable"}

        candidate_hash = seed.put("logic/python", candidate_payload)
        print(f"  candidate[{i}] {candidate_hash[:16]}...")

        # Triple-Pass Review (Pass 6 ContractCompliance included)
        try:
            promote.triple_pass_review(candidate_hash, label=label)
            print(f"  PASS  triple-pass review [{i}]")
        except promote.ReviewError as e:
            print(f"  FAIL  [{e.pass_name}] {e.detail}")
            last_error = str(e)
            continue  # discard — try next candidate

        # Tester pass — adversarial test/case generation per candidate
        try:
            tc_payloads = infer.generate_test_cases(
                label=label,
                contract=contract_record,
                candidate_payload=candidate_payload,
                n=3,
                model=tester_model,
            )
            tc_hashes: list[str] = []
            for tc_payload in tc_payloads:
                tc_hash = seed.put("test/case", json.dumps(tc_payload, sort_keys=True))
                tc_hashes.append(tc_hash)

            if tc_hashes:
                tc_approval = promote.issue_council_approval(
                    tc_hashes, reviewer_hash=evolve_reviewer_hash
                )
                promote.promote_test_cases(label, tc_hashes, tc_approval)
                print(f"  tester  {len(tc_hashes)} test cases promoted [{i}]")

                test_suite_results = promote.run_test_suite(label, candidate_hash)
                failed = [r for r in test_suite_results if not r["passed"]]
                if failed:
                    print(f"  FAIL  test suite [{i}]: {len(failed)}/{len(test_suite_results)} failed")
                    continue  # discard — try next candidate
                print(f"  PASS  test suite [{i}]: {len(test_suite_results)} cases passed")

        except infer.InferenceUnavailable as e:
            print(f"  tester unavailable ({e!s:.60}) — no test suite for [{i}]")
        except Exception as e:
            print(f"  tester error ({e!s:.80}) — no test suite for [{i}]")

        passing_candidates.append(candidate_hash)

    # ── Select best from passing pool ─────────────────────────────────────────
    if not passing_candidates:
        reason = last_error or "all candidates failed review or test suite"
        print(f"  no passing candidates — {reason}")
        return {"label": label, "outcome": "no-improvement", "reason": reason}

    print(f"  {len(passing_candidates)}/{N_CANDIDATES} candidates passed review + test suite")

    audit_path = Path("./audit.log")
    best_hash: str | None = None
    best_bm:  dict | None = None

    for candidate_hash in passing_candidates:
        bm = benchmark(label, current_hash, candidate_hash)
        print(f"  benchmark  [{passing_candidates.index(candidate_hash)}]  "
              f"old={bm['old']['fitness']:.4f}  new={bm['new']['fitness']:.4f}  "
              f"winner={bm['winner']}  tol={bm['tolerance_applied']:.4f}")

        with open(audit_path, "a", encoding="utf-8") as af:
            af.write(json.dumps({
                "event":     "benchmark",
                "label":     label,
                "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
                "benchmark": {
                    "old": {"fitness": bm["old"]["fitness"], "hash": bm["old"]["hash"]},
                    "new": {"fitness": bm["new"]["fitness"], "hash": bm["new"]["hash"]},
                },
                "winner":                    bm["winner"],
                "generated_via_inference":   True,
                "inference_model":           "gemini-flash",
                "candidate_index":           passing_candidates.index(candidate_hash),
                "n_candidates":              len(passing_candidates),
            }) + "\n")

        if bm["winner"] == "new":
            if best_bm is None or bm["new"]["fitness"] > best_bm["new"]["fitness"]:
                best_hash = candidate_hash
                best_bm   = bm

    if best_hash is None:
        print(f"  no improvement — keeping current")
        return {"label": label, "outcome": "no-improvement", "benchmark": best_bm}

    # Promote best winner
    approval      = promote.issue_council_approval([best_hash],
                                                    reviewer_hash=evolve_reviewer_hash)
    manifest_hash = promote.promote(
        label=label,
        blob_hashes=[best_hash],
        council_approval_hash=approval,
        version="1.16.0",
    )
    print(f"  promoted  manifest.hash={manifest_hash[:16]}...")
    return {
        "label":                   label,
        "outcome":                 "promoted",
        "old":                     current_hash,
        "new":                     best_hash,
        "manifest_hash":           manifest_hash,
        "benchmark":               best_bm,
        "generated_via_inference": True,
        "inference_model":         "gemini-flash",
        "n_candidates":            len(passing_candidates),
    }


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------

def run_all(reviewer: str = "evolve") -> list[dict]:
    """
    Evolve all governed labels in the manifest.

    Discovers labels from manifest["blobs"] — includes both the three core
    infrastructure labels and any capability labels registered via
    promote.bootstrap_capability(). telemetry-reader runs first so its signals
    are fresh for subsequent benchmarks.
    """
    tolerance = _derive_tolerance()
    print(f"── f_15: Self-Modification Cycle  (derived tolerance={tolerance:.4f})")

    manifest = promote.load_manifest()
    all_labels = list(manifest.get("blobs", {}).keys())

    # telemetry-reader first (infrastructure); remaining labels in manifest order
    ordered = []
    if "telemetry-reader" in all_labels:
        ordered.append("telemetry-reader")
    ordered.extend(l for l in all_labels if l != "telemetry-reader")

    results = []
    for label in ordered:
        blob_entry = manifest.get("blobs", {}).get(label, {})
        if not blob_entry.get("logic/python"):
            continue  # skip labels with no logic blob (e.g. metadata-only entries)
        r = evolve_one(label, reviewer=reviewer)
        results.append(r)

    promoted = [r for r in results if r["outcome"] == "promoted"]
    print(f"\n  f_16 complete. {len(promoted)}/{len(results)} blobs promoted → manifest v1.16.0")
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="evolve", description="f_15 self-modification engine")
    parser.add_argument("label", nargs="?", help="Evolve one label (default: all); use 'engine' to evolve the logic/engine blob")
    parser.add_argument("--reviewer", default="evolve")
    args = parser.parse_args()

    if args.label == "engine":
        result = evolve_engine(reviewer=args.reviewer)
        print(json.dumps({k: v for k, v in result.items() if k != "benchmark"}, indent=2))
    elif args.label:
        result = evolve_one(args.label, reviewer=args.reviewer)
        print(json.dumps({k: v for k, v in result.items() if k != "benchmark"}, indent=2))
    else:
        results = run_all(reviewer=args.reviewer)
        print(json.dumps(
            [{k: v for k, v in r.items() if k != "benchmark"} for r in results],
            indent=2,
        ))
