# CAP-BARE-006: Binding Leap — Delegated Execution
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

The final leap of the genesis generation: commit 7725c7f moved the actual `exec()` call out of `seed.py` and into L4 — a Binding blob. After this commit, `seed.py` no longer directly executes target blobs. It delegates to L4, which receives the payload and executes it.

## What Was Built / Decided

`invoke()` now passes `target_payload`, `target_context`, and `execution_plan` to the L4 blob via its context. L4 receives the full payload string and executes it:

```python
l4_scope = {
    "context": {
        "target_payload": payload,
        "target_context": request_envelope,
        "execution_plan": execution_plan
    },
    "log": log,
    "result": None
}
exec(l4_payload, {"__builtins__": __builtins__}, l4_scope)
```

L4's `log` sink is shared with the Linker, so L4 execution traces appear in the same telemetry stream.

Anti-recursion guard: if target hash equals L4 hash, fall back to direct execution in the Linker.

Commit narrative: "Delegating execution to a blob allows the 'Engine' to evolve (e.g., switching from exec() to a containerized sandbox) without changing the core Linker logic."

## What It Enables

- Execution strategy is now a blob: L4 can be replaced with a container executor, WASM runtime, or remote dispatcher without touching `seed.py`
- L4 can add its own pre/post-execution logic (later: retries, runtime selection)
- Full four-layer chain is self-hosted: all four system capabilities are blobs, none are hardcoded in the Linker beyond the BIOS fallback

## Why Not In council/f_N

The council tree did not delegate execution to an L4 blob. Council/f_N's `seed.py` retains direct `exec()` with a compiled code object (`_load_code()`). The council tree chose performance and simplicity (one `exec()` call with a cached code object) over the bare tree's extensibility-by-delegation model. [MEASURED — council/f_3 seed.py contains direct exec of compiled blob]

The bare tree's delegated binding is architecturally purer but adds two nested `exec()` calls per invocation (L4 + target). The council tree's choice to keep execution in the Linker is a deliberate performance-over-extensibility tradeoff.

## Evidence Basis

- Commit 7725c7f diff read directly [MEASURED]
- Shared log sink confirmed in diff [MEASURED]
- Council direct exec confirmed in council/f_3 seed.py [MEASURED]
