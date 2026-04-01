# CAP-BARE-011: Self-Correction — Autonomous Retries in L4
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit 8f44395 (f_2 Phase 1) moved failure recovery from the caller into the fabric itself. L4 (the binding layer) gained exponential backoff retry logic, driven by a `retry_policy` provided by L3. Transient failures in blob execution no longer propagate to callers by default.

## What Was Built / Decided

L3 now includes `retry_policy` in the execution plan:

```python
{"max_attempts": 3, "backoff": 0.1}
```

L4 implements a retry loop:
- Attempts execution up to `max_attempts` times
- On failure: logs the error, sleeps `backoff * 2^(attempt-1)` seconds (exponential backoff)
- On success: breaks immediately
- If all attempts fail: raises with last error message

Changes exist only in `l3_planning.py` and `l4_binding.py` — `seed.py` was untouched. This is notable: the retry capability was added entirely within blobs, not the Linker.

Commit narrative: "Moving the retry responsibility into the Binding layer (L4) makes the fabric resilient without requiring the original caller to implement complex error handling."

## What It Enables

- Caller-transparent resilience: transient failures are absorbed by the fabric
- Policy-driven retry: L3 controls retry parameters; different blob types or priorities can have different policies
- Self-healing without Linker changes: demonstrates that the blob architecture can evolve system behavior without touching seed.py

## Why Not In council/f_N

The council tree handles failures differently: the fitness function penalizes blobs that produce failures and selects better blob versions at promote-time. The council tree's answer to self-correction is "select a better blob," not "retry the same blob." [INFERRED — council/f_N fitness signals include error rates]

Both approaches are valid but solve different problems. The bare tree's retry is good for transient failures (network, flaky dependencies). The council tree's fitness selection is good for systematic failures (a blob version that consistently underperforms). A production fabric needs both.

## Evidence Basis

- Commit 8f44395 diff read directly [MEASURED]
- l4_binding.py retry loop confirmed [MEASURED]
- seed.py unchanged confirmed [MEASURED]
- Council fitness-based selection: inferred from council commit messages and structure [INFERRED]
