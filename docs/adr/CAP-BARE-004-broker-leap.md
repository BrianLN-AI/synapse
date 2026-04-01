# CAP-BARE-004: Broker Leap — Programmable Planning
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

With discovery working as a blob, the next question was: who decides how to execute? In commit 0b8dd34, planning (the "where and how" decision) was migrated from hardcoded logic in `invoke()` into an L3 blob — the Broker.

## What Was Built / Decided

`invoke()` gained a pre-execution step: before loading the target blob, it consults the L3 planning blob. L3 receives `{"target": h, "priority": context.priority}` and returns an `execution_plan` dict. The initial plan schema:

```python
{"method": "local_exec", "sandbox": "standard|high_isolation"}
```

The `execution_plan` is injected into the target blob's scope alongside `context`. Telemetry records the plan used, making execution decisions auditable per invocation.

Anti-recursion guard: if the target hash IS the L3 blob, skip broker consultation (the broker cannot plan its own execution via itself).

The initial L3 blob (`l3_planning.py`) returned `high_isolation` sandbox for high-priority requests, `standard` otherwise — a trivial policy, but the hook was in place for expansion.

## What It Enables

- Execution policy is now a blob: upgradeable without changing `seed.py`
- Blob scope receives `execution_plan` — blobs can inspect how they were scheduled
- Audit trail: telemetry records `execution_plan` alongside result, enabling post-hoc policy analysis

## Why Not In council/f_N

The council tree absorbed the broker concept but implemented it differently. Council's L3 is never directly consulted in `invoke()` — instead, the council tree exposes a fitness function that runs at promote-time (not invocation-time). The bare tree's per-invocation broker consultation adds latency on every call; the council tree trades invocation-time planning for promote-time fitness evaluation. [INFERRED — council/f_3 seed.py does not show L3 consultation in `invoke()`]

The bare tree's approach (runtime brokering) is more flexible for dynamic routing; the council tree's approach (compile-time fitness) is more predictable and lower-overhead. This is a genuine design fork, not a discarded idea.

## Evidence Basis

- Commit 0b8dd34 diff read directly [MEASURED]
- `execution_plan` injection into blob scope confirmed [MEASURED]
- Council fitness-at-promote-time approach: inferred from council/f_3 structure [INFERRED]
