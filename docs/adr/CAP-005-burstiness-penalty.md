# CAP-005: Burstiness Penalty — Explicit Spikiness Factor in Fitness Formula
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

f_2 introduced p95 latency as the latency input to the fitness formula (replacing avg). This penalised bursty blobs somewhat: a blob with high p95 scores worse than one with low p95 even at the same average. But p95 and avg are correlated — using p95 alone doesn't explicitly penalise the ratio between peak and average, only the absolute value.

f_3 added an explicit burstiness factor in Planning v4.

## What It Measures

Burstiness = p95 / avg_latency, capped at 3×.

A blob with mean=2ms and p95=6ms has burstiness=3.0 (spiky). A blob with mean=2ms and p95=2.5ms has burstiness=1.25 (consistent). The cap at 3× prevents extreme outliers from collapsing scores to near-zero.

## Why Burstiness as a Separate Factor

p95 alone captures the absolute tail latency. Burstiness captures the ratio — how much worse the tail is compared to typical behaviour. Two blobs might have the same p95=10ms:
- Blob A: avg=9ms, p95=10ms → burstiness=1.11 (very consistent)
- Blob B: avg=2ms, p95=10ms → burstiness=3.0 (very bursty)

With p95 in the latency slot only, both score identically on latency. With burstiness as a multiplier in the denominator, Blob B is penalised significantly more.

## Fitness Formula After f_3 (Planning v4)

```
f = (sr × integrity) / (latency × burstiness × cost)
```

where `burstiness = min(p95 / avg, 3.0)` when both are available; defaults to 1.0 when p95 is absent.

## f_3 Outcome for Blobs That Used This

Planning v4 (which introduced burstiness) was promoted at f_3. Discovery v4 and Telemetry-Reader v4 were not — their candidate payloads paid overhead costs that lost in benchmark, independent of burstiness.

## Consequences

- Consistent blobs (low p95/avg ratio) are explicitly preferred over bursty blobs with the same average latency. This matters most in scheduling/arbitration contexts where tail latency degrades caller experience.
- The 3× cap is a design choice without strong empirical grounding. [HYPOTHESIS: a cap of 3× prevents penalising blobs that have a single outlier run from an otherwise clean record. Uncapped, one 60ms spike on a 2ms-average blob would produce burstiness=30, collapsing its score.]
- Defaults to 1.0 (neutral) when `p95_latency_ms` is unavailable — new blobs with no telemetry history are not penalised.
- Burstiness and p95 in the latency slot are partially redundant: both penalise tail latency. The combination means high-p95, high-burstiness blobs are penalised quadratically. [INFERRED: this may over-penalise spiky blobs in some regimes. Worth monitoring across future iterations.]

## Evidence Basis

- [MEASURED] `PLANNING_V4` blob payload in `evolve.py` at commit ec285e3 (f_3). Burstiness formula `min(float(p95) / avg, 3.0)` appears verbatim.
- [MEASURED] f_3 commit message: "Planning v4: adds burstiness factor (p95 / avg_latency, capped at 3×) as an explicit multiplier. Spiky blobs are penalised beyond what p95 alone captures. → Promoted."
- [INFERRED] The 3× cap was set by the author at f_3 without a measured distribution of observed burstiness values. [HYPOTHESIS: empirical burstiness distribution would inform a better cap value.]
