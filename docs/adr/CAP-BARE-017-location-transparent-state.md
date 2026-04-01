# CAP-BARE-017: Location-Transparent State — Collective State Synchronization
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit 1b2db18 (f_3 Phase 3) is the final commit in the bare tree. It extended persistent memory (CAP-BARE-014) to work across nodes: state is stored in `collective_vault/state/` and synchronized between local and collective substrates. An agent's memory is no longer tied to a single machine.

## What Was Built / Decided

State resolution order (modified from Phase 4):

1. Check `collective_vault/state/<state_id>` first (shared/primary)
2. If found: load state, cache locally in `blob_vault/state/<state_id>`
3. If not found in collective: fall back to local `blob_vault/state/<state_id>`
4. If neither: start with empty state `{}`

State persistence after execution (both local and collective):

```python
# Local
with open(state_file, "w") as f: f.write(state_h)
# Collective push
collective_state_file.parent.mkdir(parents=True, exist_ok=True)
with open(collective_state_file, "w") as f: f.write(state_h)
```

The test scenario: Counter blob increments from 0→1, local state cache is wiped, Counter invoked again with same `state_id` — successfully resumes from 1→2 by pulling from collective vault.

Commit narrative: "An agent is no longer tied to a physical disk; it exists wherever its state can be resolved."

## What It Enables

- State migration: agents can move between nodes and resume where they left off
- Shared agent memory: multiple nodes can read the same state (though write concurrency is undefined)
- Collective substrate as truth: collective vault is the authoritative source; local vault is a cache

## Why Not In council/f_N

The council tree has no collective state. [MEASURED]

**Critical weakness**: the collective push/pull is implemented as local directory operations on `collective_vault/`. This is a simulation, not a distributed system. In a real P2P scenario, `collective_vault/` would need to be a shared filesystem, IPFS mount, or replicated store. The implementation does not address write conflicts, consistency, or network partitions. [MEASURED — collective_vault is a local Path, no network layer]

This is the frontier where the bare tree stopped. The design is conceptually sound — collective-first state resolution with local caching is a correct distributed systems pattern. The implementation is a working proof-of-concept on a single machine. Turning it into a real distributed state system would require a substantial new layer (network transport, consensus, conflict resolution).

## Evidence Basis

- Commit 1b2db18 diff read directly [MEASURED]
- Collective-first resolution order confirmed [MEASURED]
- Local-path implementation of collective_vault confirmed [MEASURED]
- Council absence of collective state confirmed [MEASURED]
- Distributed systems completeness concerns: inferred from implementation structure [INFERRED]
