# ADR-007: Bytecode Cache Keyed by Content Hash — Immutable Blobs Mean the Cache Never Goes Stale
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

f_1 discovered that Python's `exec()` recompiles source text on every call. The benchmark showed v2 blobs losing to v1 blobs despite being algorithmically better — the per-call compilation tax was masking true runtime performance.

f_1 fixed this with an in-process `_CODE_CACHE` dict: `compile()` once per blob hash, reuse the code object. This solved the benchmark issue, but the cache was process-local and ephemeral: a cold start (new process, new benchmark run) paid the full compilation cost again.

f_3 extended the cache to disk.

## Decision (f_1: In-Process Cache)

Add `_CODE_CACHE: dict[str, Any] = {}` to `seed.py`. The first `invoke()` for a given hash compiles the payload and stores the code object in the dict, keyed by content hash. Subsequent calls reuse it.

## Decision (f_3: Persistent On-Disk Cache)

Add `BYTECODE_DIR = Path("./blob_bytecode/")`. After the first `compile()`, serialise the code object via `marshal.dumps()` and write it to `BYTECODE_DIR / content_hash`. On subsequent calls (including across process restarts), check `BYTECODE_DIR / content_hash` first and deserialise with `marshal.loads()`.

The key design insight: because blobs are immutable (content-addressed), the bytecode cache needs no invalidation logic. If the hash is the same, the content is the same, the bytecode is the same. The cache never goes stale by construction.

## Alternatives Considered

- **No cache (recompile on every call):** The benchmark showed this masks blob performance. Discovered empirically at f_1.
- **In-process cache only (f_1 solution):** Sufficient for long-running processes and benchmarks in a single run, but cold-start cost still exists. f_3 extended to disk to eliminate cold-start cost across process boundaries.
- **`pickle` instead of `marshal`:** `pickle` is a general-purpose serialiser; `marshal` is the Python bytecode serialiser and is the correct tool for code objects. `pickle` cannot serialise code objects.
- **Cache invalidation based on mtime or version:** Not needed. Content hash is the identity. A "new version" of a blob is a different hash stored as a different file.

## Consequences

- Cold-start performance after f_3 is significantly better — process restarts no longer pay compilation cost for already-cached blobs.
- `BYTECODE_DIR` (`./blob_bytecode/`) is a runtime artifact, like `blob_vault/`. It is git-ignored.
- The persistent cache creates a dependency between the Python interpreter version and the cached bytecode. `marshal` bytecode is not portable across Python versions. [HYPOTHESIS: if the runtime Python version changes, stale bytecode in BYTECODE_DIR could cause errors. The fix is to clear the directory, which is safe — blobs are re-compiled on next invoke.]
- The evolution benchmarks after f_3 measure true blob logic performance, not compilation overhead.

## Evidence Basis

- [MEASURED] `_CODE_CACHE` added to `seed.py` at commit cf6ddd4 (f_1). Commit message: "Eliminates per-call compilation tax that was masking v2 blobs' true runtime performance. Discovered by the evolution cycle itself — f_1 found the engine gap."
- [MEASURED] `BYTECODE_DIR` and `marshal`-based persistence added to `seed.py` at commit ec285e3 (f_3). Commit message: "Compile cache was ephemeral (_CODE_CACHE resets on process restart). seed.py: adds BYTECODE_DIR (./blob_bytecode/) as an on-disk L2 cache using marshal serialisation. Immutable blobs guarantee the cached bytecode is always valid — no invalidation needed."
- [INFERRED] The no-invalidation property follows directly from content-addressing. The commit message states it explicitly.
