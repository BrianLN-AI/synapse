# CAP-BARE-014: Persistent Memory — Stateful Blob Substrate
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** bare/f_N

## Context

Commit 2cd3f15 (f_2 Phase 4) enabled blobs to maintain state across invocations. Without this, every blob invocation is a pure function: same inputs, same outputs, no memory. With persistent state, blobs become agents — they accumulate knowledge and behavior over time.

## What Was Built / Decided

State is stored as content-addressed blobs (via `put()`), referenced by a mutable `state_id` pointer file.

**State resolution** (before execution):
1. Caller passes `state_id` in `params`
2. Linker checks `blob_vault/state/<state_id>` for a state hash pointer
3. If found: reads state hash, resolves state blob, loads JSON into `state` dict
4. `state` dict injected into L4 scope alongside `target_context`

**State persistence** (after execution):
1. L4 (or fallback direct exec) places updated `state` back into `l4_scope["context"]["state"]`
2. Linker reads updated state from L4 scope
3. Stores updated state as a new blob (`put(json.dumps(state), "system/state")`)
4. Overwrites `blob_vault/state/<state_id>` pointer file with new hash

State evolution is content-addressed: every state version is a distinct blob. The pointer file is the only mutable artifact.

Commit narrative: "Memory transforms transient functions into persistent agents. The 'state' is itself a content-addressed blob, maintaining the integrity of the substrate."

## What It Enables

- **Stateful blobs**: a Counter blob can increment across calls; a cache blob can accumulate entries
- **Audit trail**: every state version is an immutable blob — you can reconstruct the state history by following pointer file changes
- **State is vault-native**: state uses the same content-addressing as blobs — no separate storage system needed
- **Agent persistence**: blobs that track conversation history, learned preferences, or accumulated telemetry across sessions

## Why Not In council/f_N

The council tree has no per-blob state mechanism. Council/f_N blobs are pure functions. The council tree's architecture is stateless by design — blob fitness is evaluated on fresh invocations, which requires state-free execution for reproducibility. [INFERRED — council/f_7 has no state_id parameter or state injection in invoke()]

The persistent memory design is compatible with the council tree's pure-function assumption: state is opt-in (only if `state_id` is provided). Blobs that don't use state continue to be pure functions. This makes it a low-risk cherry-pick candidate.

**Relationship to f_3 location-transparent state (CAP-BARE-017):** this commit establishes local state; f_3 extends it to collective/distributed state.

## Evidence Basis

- Commit 2cd3f15 diff read directly [MEASURED]
- State pointer file pattern (`blob_vault/state/<state_id>`) confirmed [MEASURED]
- Content-addressed state blobs confirmed (uses `put()`) [MEASURED]
- Council stateless design: inferred from council/f_7 structure [INFERRED]
