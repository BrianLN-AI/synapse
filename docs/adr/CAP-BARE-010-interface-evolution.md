# CAP-BARE-010: Interface Evolution — Standardized Proxy with Trace Identity
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** bare/f_N

## Context

Commit 02b14dd (f_1 Phase 4) matured the L1 interface blob from a simple normalizer into a formal request proxy. The key addition: every invocation is tagged with a `trace_id` and protocol version at entry. The Linker, not the caller, generates the identity.

## What Was Built / Decided

`seed.py` generates a `trace_id` before calling L1:

```python
"trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]
```

L1 receives this alongside `timestamp` and injects them into the normalized envelope as `metadata`. The envelope schema:

```python
{
    "protocol": "D-JIT/1.2-Beta (MCP-Enabled)",
    "intent": intent.upper(),
    "params": normalized_params,
    "metadata": {
        "origin": "seed_mcp_proxy",
        "timestamp": ...,
        "trace_id": "syn-XXXXXXXX"
    }
}
```

Every blob now executes with a canonical request envelope that includes distributed-tracing-style identity, regardless of what the caller passed.

Commit narrative: "Moving the 'Identity' of the request (trace_id, protocol) into the Interface layer allows the rest of the fabric to remain focused on logic."

## What It Enables

- Distributed tracing: every execution is tagged with a `trace_id` from entry
- Protocol versioning: callers can detect fabric version from the envelope
- Intent normalization: `intent` is uppercased canonical form — downstream layers do not need to handle case variants
- Telemetry correlation: `trace_id` in the telemetry artifact enables cross-invocation tracing

## Why Not In council/f_N

The council tree does not have an L1 normalization step. Council/f_N's `invoke()` takes raw context and passes it directly to blob scope. The council tree has telemetry but not per-invocation trace identity at the protocol level. [MEASURED — council/f_3 seed.py invoke() has no L1 consultation step]

The `trace_id` pattern is a clean, low-cost improvement that the council tree could adopt without architectural disruption. This is a cherry-pick candidate for the council tree's telemetry system.

## Evidence Basis

- Commit 02b14dd diff read directly [MEASURED]
- trace_id generation in seed.py confirmed [MEASURED]
- L1 envelope schema confirmed in l1_interface.py diff [MEASURED]
- Council tree absence of trace_id: confirmed by inspection [MEASURED]
