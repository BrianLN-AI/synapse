# CAP-BARE-007: Multi-Vault Discovery — Distributed Tiers
**Date:** 2026-04-01
**Status:** Accepted
**Flag:** CHERRY-PICK — merged to main
**Source:** bare/f_N (commit 9e4a10c, f_1 Phase 1)

## Context

Commit 9e4a10c (f_1 Phase 1) extended the discovery layer to search multiple vault tiers rather than a single local `blob_vault/`. The motivation: as the fabric scales, not all blobs will live on the same node. Local-first resolution with remote fallback is the basic distributed systems pattern.

## What Was Built / Decided

`_raw_get()` now passes `vault_tiers` to the L2 discovery blob:

```python
vault_tiers = ["blob_vault", "remote_vault"]
l2_scope = {"context": {"target": h, "vault_tiers": vault_tiers}, ...}
```

The L2 blob (`l2_discovery.py`) iterates through the tier list in order, checking each directory for the target hash. First match wins. If no tier resolves the hash, falls back to BIOS.

This is a simulated multi-tier setup (both tiers are local directories), but the L2 blob's interface was designed to accept any ordered list of vault paths — the linker does not know the topology.

Commit narrative: "Tiered resolution allows the fabric to scale. Local cache (vault) first, then remote discovery."

## What It Enables

- Hash resolution is topology-aware: blobs can live in cold storage, remote vaults, or peer nodes
- L2 blob controls the search order: the linker passes the tier list, the blob decides how to search
- Foundation for P2P and federated discovery (f_3 builds directly on this pattern)
- Cache-aside pattern: local vault functions as a cache in front of remote tiers

## Why Not In council/f_N

The council tree's discovery layer was not extended to multiple vaults. Council/f_N focuses on local content-addressed storage with fitness evaluation. The council tree's implicit assumption is single-vault operation. [INFERRED — no vault_tiers parameter in council/f_3 seed.py or discovery blob]

## Direction: Multi-Layer Requirement

The flat tier list (`["blob_vault", "remote_vault"]`) is a first step, not the end state. The design must be explicitly multi-layer — not just horizontally ordered, but hierarchically composable:

- Each tier can itself be a discovery strategy (local filesystem, DHT, peer broadcast, CDN)
- Tiers should be pluggable blobs, not hard-coded paths — the L2 blob resolves using a tier-specific resolver blob
- The resolution protocol must support heterogeneous backends at each layer without the linker knowing the topology
- Example: L1 (in-process cache) → L2 (local vault) → L3 (peer mesh) → L4 (cold archive), each layer delegating to the next on miss

This is a capability boundary: the current `vault_tiers` list interface is the right shape, but each entry needs to be a resolver descriptor rather than a path string to achieve true multi-layer extensibility. This is an explicit design requirement for the council tree adoption.

## Evidence Basis

- Commit 9e4a10c diff read directly [MEASURED]
- Tier iteration logic in l2_discovery.py diff confirmed [MEASURED]
- Council vault: single-vault confirmed by inspection of council/f_3 [MEASURED]
- Multi-layer direction: captured from Brian Lloyd-Newberry, 2026-04-02 [MEASURED]
