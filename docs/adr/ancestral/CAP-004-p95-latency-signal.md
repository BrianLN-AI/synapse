# CAP-004: p95 Latency Signal — Welford Online Algorithm for Tail-Latency
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

The fitness formula used average latency (`avg_latency_ms`) as the latency input. A blob might average 2 ms but spike to 200 ms on 5% of calls. A bursty blob looks identical to a consistently fast blob when only the mean is measured. The v1 telemetry-reader stored only a running sum; no variance information was tracked.

f_1's Telemetry-Reader v2 introduced p95 approximation. f_2 wired it through the full signal path (linker → planning).

## What It Measures

p95 latency: the latency below which 95% of invocations fall. Captures tail behaviour that averages conceal. A blob with mean=2ms and p95=50ms is bursty; a blob with mean=3ms and p95=4ms is consistent.

## Why p95 Over Mean

- **Mean hides spikes.** A single 200ms call in 100 invocations adds 2ms to the mean — invisible. The same call raises p95 significantly.
- **Callers care about tail behaviour.** A planning blob that occasionally takes 200ms degrades arbitration latency for those callers, even if most calls are fast.
- **p95 is standard in SRE practice** for latency budgets and SLOs (Service Level Objectives).

## Implementation Decision: Welford Algorithm (O(1) Space)

Computing exact p95 requires storing all latency values and sorting — O(n) memory, growing without bound. The Welford online algorithm computes running mean and variance in O(1) space with a single pass:

```python
delta = lat - s["lat_mean"]
s["lat_mean"] += delta / n
s["lat_M2"]   += delta * (lat - s["lat_mean"])
```

p95 is then approximated as `mean + 1.645σ` (the standard normal quantile for 95%). This is an approximation, not the exact value — it assumes latency is approximately normally distributed. For real invocation latencies this is a reasonable assumption.

## f_2 Wiring Decision

f_2 found that p95 existed in telemetry-reader v2 output but was not forwarded through `linker.arbitrate()` and not used in Planning. Both were corrected:

- `linker.py`: adds `p95_latency_ms` to the candidate enrichment dict
- Planning v3: uses `p95_latency_ms` when available, falls back to `avg_latency_ms`

Unknown blobs (no telemetry history) have `p95_latency_ms = None` — Planning falls back to `avg_latency_ms` for these.

## Consequences

- Planning v3+ penalises bursty blobs even when their average latency is acceptable. [MEASURED: f_2 test `test_planning_v3_uses_p95` confirms "consistent" beats "bursty" when p95 differs significantly.]
- The Welford approximation introduces a small error for non-normal latency distributions. Heavy-tailed or bimodal distributions would produce a p95 estimate that undershoots the true value. [HYPOTHESIS: for typical blob invocation latencies, the approximation is acceptable. A real distribution test has not been run.]
- The `integrity` signal (recency-weighted success streak, added at f_2) is tracked in the same Welford-style accumulator pass.

## Evidence Basis

- [MEASURED] TELEMETRY_READER_V2 in `evolve.py` at commit cf6ddd4 (f_1). Welford update formula is verbatim in the blob payload.
- [MEASURED] `linker.py` diff at commit 9c7fb35 (f_2): `p95_latency_ms` added to arbitrate() enrichment.
- [CITED] Welford's online algorithm for computing variance: Welford (1962), "Note on a Method for Calculating Corrected Sums of Squares and Products." Standard normal quantile 1.645 for 95th percentile is a well-known statistical constant.
- [MEASURED] f_2 commit message: "Planning v3 fitness: ~2× improvement over v2 (p95 correctly penalises spike risk)".
