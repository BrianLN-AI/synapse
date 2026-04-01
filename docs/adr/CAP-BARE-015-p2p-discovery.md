# CAP-BARE-015: P2P Discovery — Collective Vault Tier
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit e3059ec (f_3 Phase 1) extended multi-vault discovery (CAP-BARE-007) with a third tier: `collective_vault`. This tier represents the shared substrate of a P2P network of Synapse nodes. Any blob deposited into the collective vault is discoverable by any node that shares access to it.

This commit also introduced a significant refactor: the manifest schema changed from `layers` (l1/l2/l3/l4) to `capabilities` (proxy/librarian/broker/engine), and `_resolve_capability()` was added to the Linker as a semantic name resolver.

## What Was Built / Decided

Discovery tier list extended:

```python
vault_tiers = ["blob_vault", "remote_vault", "collective_vault"]
```

Manifest schema refactored from positional layers to named capabilities:

```json
{
  "capabilities": {
    "proxy":     {"stable": "<hash>"},
    "librarian": {"stable": "<hash>"},
    "broker":    {"stable": "<hash>"},
    "engine":    {"stable": "<hash>"}
  }
}
```

New `_resolve_capability(name, version)` function: translates semantic names to content hashes via the manifest. `invoke()` now uses `_resolve_capability("proxy")`, `_resolve_capability("broker")`, etc. instead of `manifest.get("layers", {}).get("l1")`.

The `src/` directory was introduced for layer blob source files — separating layer source from the seed and config files.

Commit narrative: "Tiered discovery is the key to global scale. Local first, then remote, then collective. Each step increases the 'Synaptic Weight' of the network."

## What It Enables

- Shared blob discovery across nodes: a blob promoted on one Synapse node is findable by others via `collective_vault`
- Semantic capability resolution: `_resolve_capability("broker")` is more maintainable than hardcoded manifest key names
- Versioned capabilities: the `{"stable": hash, "beta": hash}` schema enables blue/green blob versions
- Foundation for true P2P: the `collective_vault` tier is simulated as a local directory but the interface is topology-agnostic

## Why Not In council/f_N

The council tree has no P2P or collective discovery. The council tree is a single-node fabric. [MEASURED — no `collective_vault` in any council branch]

The `_resolve_capability()` refactor is independently valuable and council-compatible. The capability registry pattern (named capabilities with version slots) is cleaner than the bare tree's original l1/l2/l3/l4 naming. This pattern is a candidate for council adoption independently of P2P.

## Evidence Basis

- Commit e3059ec diff read directly [MEASURED]
- Three-tier list confirmed [MEASURED]
- Manifest schema change (layers → capabilities) confirmed [MEASURED]
- `_resolve_capability()` function confirmed [MEASURED]
- Council single-vault: confirmed by inspection [MEASURED]
