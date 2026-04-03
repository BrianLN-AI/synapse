# ADR-003: Manifest Self-Sealing — The Manifest Hashes Its Own Content
**Date:** 2026-04-01
**Status:** Accepted — implemented in f_0 (council/f_0, v1.0.0)
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

The manifest (`manifest.json`) records which blob hash is canonical for each named role (discovery, planning, telemetry-reader). It is the system's single source of truth for which code is active. If the manifest can be modified without detection, the entire content-addressed trust chain breaks: a caller reading the manifest could receive a different hash than what was promoted.

At Phase 2, a `promote()` function was written. The question was: should the manifest include its own integrity check?

## Decision

The manifest includes a `hash` field computed from the manifest's own content (excluding the `hash` field itself). On every write, `_write_manifest()` strips the existing `hash`, serialises the remaining content with `sort_keys=True`, computes SHA-256, and writes it back.

```python
content = {k: v for k, v in manifest.items() if k != "hash"}
manifest_hash = hashlib.sha256(
    json.dumps(content, sort_keys=True).encode()
).hexdigest()
manifest["hash"] = manifest_hash
```

This means the manifest is self-sealing: any out-of-band modification to the manifest content invalidates the `hash` field. The manifest hash is also returned by `promote()` and recorded in the audit log, creating an audit trail that links each promotion event to the manifest state it produced.

## Alternatives Considered

- **No manifest hash:** Simple but undetectable tampering. Any process with write access to `manifest.json` could change which blob hash is active without leaving a signal.
- **External signature (separate file):** Separates the integrity proof from the content it covers. Complicates reads; the proof and manifest can drift out of sync.
- **Merkle tree over all blobs:** More robust but far more complex. The blobs themselves are already content-addressed; the manifest only needs to cover its own entries.

## Consequences

- `_write_manifest()` is the only function that writes to `manifest.json`. All promotion paths call it through `promote()`.
- The returned manifest hash is logged to `audit.log` on every promotion, creating a chain: approval hash → manifest hash → blob hashes.
- Any process that modifies `manifest.json` directly breaks the self-seal. Detection requires re-computing the hash, which is cheap.
- The `sort_keys=True` constraint means manifest serialisation is deterministic: the same content always produces the same hash, regardless of dict insertion order.

## Evidence Basis

- [MEASURED] `_write_manifest()` in `promote.py` at commit 7613107 (Phase 2). The strip-and-hash pattern is present in the original implementation.
- [INFERRED] The audit log entry includes `manifest_hash` in each `promote` event — the chain of custody is structural, not incidental.
- [INFERRED] The README (added at commit a525869) states: "Requiring a `council/approval` blob — a content-addressed artifact recording who approved what and when — creates a chain of custody. Every manifest entry traces back to an approval."
