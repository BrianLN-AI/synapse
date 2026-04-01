# CAP-BARE-012: Performance Feedback — Dynamic Plasticity
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit b261120 (f_2 Phase 2) added a feedback loop: L3 (the broker) reads recent telemetry artifacts to penalize nodes that produced failures. Node selection adapts over time based on observed execution outcomes. The commit calls this "Dynamic Plasticity."

## What Was Built / Decided

L3's "Plasticity Routine" scans `blob_vault/*` for recent telemetry artifacts:
- Reads up to the 20 most-recently-modified blobs
- Parses each as JSON, checks for `execution_plan.node` and `status`
- If `status == "failure"` for a node: `nodes[node]['latency'] *= 5` (latency penalty)

After plasticity, normal arbitrage runs with penalized latency weights — failing nodes are deprioritized automatically.

`seed.py` was updated to inject `glob`, `os`, and `json` into the L3 scope to enable telemetry scanning from within the broker blob.

Commit narrative: "High-frequency feedback loops within the fabric allow it to self-correct without human intervention. The 'gaps' (L3 decisions) are now truly active."

## What It Enables

- Autonomous routing adaptation: no human intervention needed to route around failing nodes
- Telemetry-as-signal: the telemetry blobs already being written by `invoke()` become input to the planner
- Demonstrates the core loop: execute → telemetry → adapt → execute

## Why Not In council/f_N

The council tree implements a more sophisticated version of this pattern. Council/f_1 ("first self-modification cycle") applies the fabric's fitness evaluation to itself — `f_0` applied to `f_0`. Council/f_3 adds p95 latency signals and burstiness penalties. The council tree's feedback loop operates on blob fitness (which blob version wins) rather than node selection (which node wins). [MEASURED — council commit messages: "p95 + integrity signals", "burstiness penalty", "dynamic tolerance"]

The bare tree's plasticity is simpler and more direct — scan telemetry, penalize failures, adapt. The council tree's approach is more principled but more complex to implement. The bare tree demonstrated the feedback loop concept first; the council tree formalized it.

## Evidence Basis

- Commit b261120 diff and l3_planning.py diff read directly [MEASURED]
- Telemetry scan logic (glob, mtime sort, penalty) confirmed [MEASURED]
- Council p95/burstiness signals: confirmed in council commit messages [MEASURED]
- Council self-modification cycle: confirmed in "f_1 — first self-modification cycle" commit [MEASURED]
