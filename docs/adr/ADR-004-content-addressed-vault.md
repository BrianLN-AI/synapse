# ADR-004: Content-Addressed Vault — Blob Identity Is Its Hash
**Date:** 2026-04-01
**Status:** Accepted — implemented in f_0 (council/f_0, v1.0.0)
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

The fabric needed a storage model for blobs. Options ranged from a relational database to a key-value store to a simple filesystem directory. The fundamental question was: what is the identity of a blob?

In traditional systems, identity is assigned (a UUID, a sequence number, a path). In the D-JIT fabric, the content and the identity needed to be unified to enable deduplication, caching, and distributed access without coordination.

## Decision

A blob's identity is the SHA-256 hash of its content (type + payload, serialised as JSON with `sort_keys=True`). The vault is a directory (`./blob_vault/`) where each blob is stored as a file named by its hash. `put()` is idempotent: if the file already exists, it is not overwritten.

```python
envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
content_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
blob_path = VAULT_DIR / content_hash
if not blob_path.exists():
    with open(blob_path, "w") as f:
        f.write(envelope)
return content_hash
```

The hash is both the storage address and the integrity proof. Any node that holds a hash and can reach a vault can retrieve and verify the blob without trusting the transport.

## Alternatives Considered

- **UUID-keyed storage:** Identity is assigned, not derived. Identical blobs stored twice get different IDs. No deduplication. No integrity proof at lookup time.
- **Database (SQLite, Postgres):** Adds a dependency and a mutable store. Content-addressing on top of a mutable DB is possible but redundant.
- **Named/labeled storage only:** The manifest uses labels (`discovery`, `planning`). If the vault were label-addressed, you could not store multiple versions of the same blob type, and the hash would need to be tracked separately.

## Consequences

- Blobs are immutable. A put with the same content always returns the same hash. There is no update operation — only new puts.
- The bytecode cache (added in f_3) relies on this: `BYTECODE_DIR / content_hash` is always valid because the blob it was compiled from can never change.
- `_raw_get()` is a direct filesystem read by hash. No index, no query — O(1) lookup.
- Telemetry artifacts, council approvals, and feedback blobs are all stored in the same vault as logic blobs. The vault is a universal blob store, not typed storage.
- Distributed vaults are structurally natural: the hash works as an address on any node. The content and the address are the same thing.

## Evidence Basis

- [MEASURED] `put()` and `_raw_get()` in `seed.py` at commit 059925a (Phase 1 BIOS). The idempotent write and hash-as-filename pattern are present from the first commit.
- [CITED] The README (a525869) states: "If the hash matches, the content is identical — deduplication is free, caching is trivially correct, and no blob can be silently modified."
- [INFERRED] The `sort_keys=True` constraint in `json.dumps` ensures deterministic serialisation — same content, same hash, regardless of Python dict ordering.
