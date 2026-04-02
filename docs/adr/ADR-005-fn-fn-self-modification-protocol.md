# ADR-005: f(N)(f(N)) Self-Modification Protocol — Recursive Self-Application
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

After f_0 established the closed feedback loop, the next question was: how does the fabric improve? Options were manual blob authoring (human writes better blobs), automated mutation without measurement, or a structured self-application cycle.

The f_0 spec described a fixed-point iteration: `f_n = f_{n-1}(f_{n-1})`. This meant the fabric would apply its own evaluation/promotion process to its own core blobs. The self-modification engine (`evolve.py`) was introduced at f_1.

## Decision

Each iteration follows a fixed five-step cycle per core blob:

1. **Evaluate** — read current blob hash from manifest, retrieve fitness signals from telemetry
2. **Mutate** — use a handcrafted v_next payload (the improvement candidate)
3. **Review** — run Triple-Pass Review on the candidate (same governance as any blob)
4. **Benchmark** — invoke old and new N=25 times (with 5 warmup discards), compare fitness
5. **Promote** — if new fitness ≥ old × (1 - PROMOTE_TOLERANCE), issue council approval and update manifest

The iteration terminates: there is a fixed set of core blobs (discovery, planning, telemetry-reader), a fixed mutation per iteration (hardcoded v_next payloads in `evolve.py`), and a promotion gate. If the candidate does not win, the current blob stays. The fixed-point is reached when no further improvements pass the gate.

PROMOTE_TOLERANCE was set at 0.30 for f_1/f_2 to allow capability improvements (L2 tier, p95 metrics, Bayesian smoothing) that have genuine speed tradeoffs to be promoted. Starting at f_3, this value is derived from the audit log's distribution of past fitness deltas.

## Alternatives Considered

- **Manual blob authoring only:** No feedback loop between measurement and mutation. Improvements are blind to actual runtime behaviour.
- **Automated mutation without governance:** Could generate and promote arbitrary code without Triple-Pass Review. Removes the safety guarantees established at Phase 2.
- **Genetic algorithm / random mutation:** Requires a larger candidate population, more benchmark rounds, and a mutation operator. The current design uses intentional, reasoned mutations (written by the author at each iteration). [HYPOTHESIS: random mutation would be viable once the fitness function is more complete — after f_4's FeedbackScore addition.]
- **Pure fitness comparison (no tolerance):** Rejected at f_1 because the v2 blobs (EAFP Discovery, Bayesian Planning, Welford p95 Telemetry-Reader) introduced genuine capability improvements that paid a measured speed cost. Without tolerance, all three would have been rejected.

## Consequences

- The self-modification cycle is bounded by the number of hardcoded mutation payloads in `evolve.py`. Adding a new mutation requires a human commit.
- The promotion gate (fitness × (1 - tolerance)) means the fabric can reject its own candidates. f_3 saw 1/3 blobs promoted; f_4 saw 1/3. The system correctly holds back regressions.
- The warmup pass (5 invocations discarded) was added because `exec()` without a compile cache was paying a per-call compilation tax. The compile cache (_CODE_CACHE, then BYTECODE_DIR) was added at f_1 after the warmup revealed the cost.
- f_1 found its own performance problem by running: the benchmark showed v2 blobs losing due to compilation overhead, which led to the compile cache addition. [MEASURED: commit cf6ddd4 message confirms this.]
- The evolve cycle runs telemetry-reader first so subsequent benchmark rounds use v_next signals.

## Evidence Basis

- [MEASURED] `evolve.py` introduced at commit cf6ddd4 (f_1). BENCHMARK_ROUNDS=25, BENCHMARK_WARMUP=5, PROMOTE_TOLERANCE=0.30 are explicit constants with inline comments.
- [MEASURED] f_1 commit message: "f_1 found the engine gap" — the compile cache was discovered by the evolution cycle, not designed in advance.
- [MEASURED] f_3 commit message: "1/3 promoted → manifest v1.3.0" — the gate correctly rejected Discovery v4 (type guard overhead) and Telemetry-Reader v4 (datetime parsing overhead).
- [INFERRED] The five-step cycle is a fixed protocol — not adaptive. The fabric does not change how it evolves, only what it evolves into.
