# ADR-012: Multi-Tenant Manifest and Tenant Identity

**Date:** 2026-04-02
**Status:** Proposed
**Supersedes:** —
**Superseded by:** —

---

## Context

The D-JIT Logic Fabric is currently single-tenant: one vault, one manifest, one governance
authority. All expressions are global. There is no concept of ownership, isolation, or
federation between independent parties.

As the system matures, multiple independent tenants need to:
- Maintain their own view of "current" expressions (separate manifests)
- Govern their own promotions (separate governance)
- Share the content-addressed vault without coordination (natural deduplication)
- Optionally recognize each other's promotions (federation via alliance)

The vault is naturally multi-tenant by construction: `blake3(envelope) = address` means
any two tenants who independently produce the same expression store it once at the same
address. No coordination required. The vault is a commons.

The manifest is where tenancy breaks. One manifest = one tenant's view of current state.

---

## Decision

**Tenant identity is dual: a genesis blob hash and an embedded public key.**

```json
{
  "type": "governance/genesis",
  "payload": {
    "public_key": "<ed25519-public-key-hex>",
    "name":       "<human-readable-label>",
    "governance": "<initial-governance-blob-hash>",
    "founded":    "<ISO-8601-timestamp>"
  }
}
```

`tenant_id = blake3(genesis_envelope)`

- **Content-addressed identity**: the genesis blob defines who the tenant is. Identity is
  derived, not assigned. No central registry.
- **Cryptographic ownership**: the public key inside the genesis blob allows the tenant to
  prove ownership by signing governance artifacts.
- **Auditable founding**: the genesis blob is in the vault forever. Anyone can verify when
  and how a tenant was established.

**The manifest gains tenant and governance fields:**

```json
{
  "tenant":     "<genesis-blob-hash>",
  "governance": "<governance-blob-hash>",
  "blobs": {
    "<label>": {
      "<type>": "<expression-hash>",
      "governance": "<label-override-hash>"
    }
  },
  "version": "...",
  "hash":    "<self-seal>"
}
```

- `manifest.governance` — the default governance authority for all promotions
- `manifest.blobs[label].governance` — optional per-label override (hybrid layering)
- `manifest.tenant` — the tenant this manifest belongs to
- `manifest.hash` — self-sealing (excludes the hash field from its own preimage, unchanged)

**The vault remains shared.** No per-tenant vault. Content-addressed deduplication is free
and automatic. Two tenants who independently produce identical expressions store one copy.

---

## Alternatives Considered

### Per-tenant vault (complete isolation)
- **Pro:** No cross-tenant visibility at rest
- **Con:** Loses deduplication; two identical expressions cost twice the storage
- **Con:** Cross-tenant blob usage requires explicit copying, not hash reference
- **Verdict:** Rejected. The commons model is strictly better when identity is content-addressed.

### Assigned tenant IDs (string labels, central registry)
- **Pro:** Human-readable, easy to type
- **Con:** Requires a registry (who assigns names? — a new centralization point)
- **Con:** Inconsistent with the system's identity philosophy (identity is derived, not assigned)
- **Verdict:** Rejected. Genesis blob hash is self-describing and requires no external registry.

### Public key as sole identity (no genesis blob)
- **Pro:** Simpler — just a key pair
- **Con:** Public key carries no metadata about founding conditions, initial governance, or timestamp
- **Con:** Loses the content-addressed founding record
- **Verdict:** Rejected as sole mechanism. Combined with genesis blob, the public key proves
  ownership while the genesis blob records founding conditions.

---

## Consequences

**Immediate:**
- Manifest schema gains `tenant`, `governance` fields
- Genesis blob type `governance/genesis` is defined
- Single-tenant operation remains valid: `tenant` field may be omitted for backward compatibility,
  defaulting to a well-known bootstrap genesis hash

**Ongoing:**
- All new tenants start by creating a genesis blob and publishing its hash as their tenant ID
- Governance promotions must be signed by the key in the genesis blob
- The vault's deduplication benefit increases as more tenants share common expressions

**Remaining:**
- Key rotation protocol (what happens when a tenant's private key is compromised)
- Multi-key genesis (a tenant whose identity is itself a quorum of keys)
- Tenant discovery (how do you find other tenants? — requires an index or directory expression)

---

## Evidence Basis

- **[INFERRED]** Content-addressed identity = no registry required; follows from vault identity model (ADR-004)
- **[CITED]** Bitcoin address derivation: `address = hash(public_key)` — same pattern, no central assignment
- **[MEASURED]** Current vault is append-only, naturally multi-tenant; deduplication is automatic
- **[INFERRED]** Shared vault + separate manifests = maximum efficiency with tenant isolation at governance layer
