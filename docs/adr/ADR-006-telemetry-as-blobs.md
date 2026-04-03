# ADR-006: Telemetry as Blobs — Invocation Records Stored in the Vault
**Date:** 2026-04-01
**Status:** Accepted — implemented in f_0 (council/f_0, v1.0.0)
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

Every blob invocation needed to produce a performance record: latency, memory usage, log lines, error state. The question was where to store these records. Options included a separate database, an append-only log file, or the content-addressed vault itself.

The vault was already the universal store for logic blobs. The telemetry decision determined whether it would remain universal or bifurcate into typed storage.

## Decision

Every invocation records a `telemetry/artifact` blob in the vault via `_record_telemetry()` in `seed.py`. The telemetry blob contains the invoked hash, timestamp, latency (ms), memory (KB), log lines, and error state — all serialised as JSON. It is stored by `put()` like any other blob.

```python
record = {
    "invoked": content_hash,
    "timestamp_utc": ...,
    "latency_ms": ...,
    "memory_kb": ...,
    "log": log_lines,
    "error": error,
}
return put("telemetry/artifact", json.dumps(record))
```

The telemetry-reader blob (itself a promoted logic blob) scans the vault for files with `type == "telemetry/artifact"` and aggregates them into per-blob fitness signals.

## Alternatives Considered

- **Separate append-only log file (JSONL):** Faster for sequential writes, but not content-addressed, not immutable, and not accessible through the same blob invocation path. Would require a second read mechanism.
- **SQLite database:** Queryable but a dependency, mutable, and creates a two-tier storage model.
- **In-memory accumulator:** Lost on process restart. The feedback loop requires persistence across invocations.
- **Separate directory from blob_vault:** Would allow telemetry to be purged independently, but adds complexity without benefit. The vault already handles deduplication — duplicate telemetry records for identical invocations are automatically deduplicated.

## Consequences

- The vault grows with every invocation. There is no TTL or eviction mechanism (runtime artifacts are git-ignored but accumulate on disk).
- The telemetry-reader blob iterates the entire vault directory to find telemetry artifacts. This is O(vault size), not O(blob count). [MEASURED: f_3 and f_4 both saw telemetry-reader candidates rejected because vault-iteration overhead dominated in sparse-vault benchmark conditions.]
- Telemetry blobs are content-addressed: if the same invocation produces identical results (same latency, same log), the second `put()` is a no-op. In practice, latency varies, so most invocations produce unique blobs.
- The unified vault means the telemetry-reader, approval verifier, and blob executor all use the same `_raw_get()` path — one read mechanism for all data.
- Feedback blobs (`feedback/outcome`, f_4) and reviewer blobs (`council/reviewer`, f_6) follow the same pattern, confirming that the vault-as-universal-store decision compounds across iterations.

## Evidence Basis

- [MEASURED] `_record_telemetry()` in `seed.py` at commit 059925a (Phase 1). Telemetry is stored via `put()` from the BIOS seed's first commit.
- [MEASURED] Telemetry-reader blob at commit fadcf3c (f_0) scans vault for `type == "telemetry/artifact"`. Same pattern replicated in v2–v7.
- [MEASURED] f_3 and f_4 commit messages explicitly note that telemetry-reader candidates were rejected due to two-pass vault-iteration overhead vs sparse-vault baseline.
- [INFERRED] The decision to store telemetry in the vault rather than a separate log was structural from Phase 1, before the cost of vault iteration was measured.
