# CAP-BARE-005: Interface Leap — Normalization Proxy
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

With discovery (L2) and planning (L3) as blobs, the raw `invoke()` call still received un-normalized caller context. Commit 5aa058f migrated request normalization into L1 — making the Interface layer a blob that shapes all incoming context before any other layer sees it.

## What Was Built / Decided

`invoke()` gained a pre-broker step: consult L1 (the proxy) before L3. L1 receives `{"request": context}` and returns a normalized `request_envelope`. The envelope is then passed to L3 (broker) and injected into the target blob's scope.

L1 normalization in the initial implementation:
- Lowercase all param keys
- (Later) inject `trace_id` and protocol version metadata

The full four-layer execution sequence established here: L1 (normalize) → L3 (plan) → L2 (resolve) → L4 (bind/execute).

Telemetry records `request_envelope`, making normalization decisions visible per invocation.

Commit narrative: "Layered composition allows the Linker to remain small while the intelligence (normalization, policy, resolution) grows as immutable Blobs."

## What It Enables

- Callers can send any shape of context; L1 normalizes to canonical form
- Protocol versioning: L1 injects `protocol` tag into every envelope
- The Linker (`seed.py`) does not need to know normalization rules — they live in L1 blobs

## Why Not In council/f_N

The council tree has no direct equivalent of a runtime normalization proxy. Council/f_N focuses on blob fitness evaluation, not request shaping. The interface layer concept from the bare tree is closer to what PROTOCOL.md (added in council/f_3) describes as the schema-blob-as-interface pattern — but the runtime proxy mechanism itself was not carried forward. [INFERRED — no L1 consultation visible in council/f_3 seed.py]

This is a candidate for future adoption if the council tree ever needs to support heterogeneous callers (MCP, REST, gRPC) that need request normalization at runtime.

## Evidence Basis

- Commit 5aa058f diff read directly [MEASURED]
- Four-layer order confirmed in diff (L1 before L3 before L2 before L4) [MEASURED]
- Council absence of runtime proxy: inferred from council/f_3 seed.py [INFERRED]
