# CAP-BARE-001: Original BIOS/ABI Seed Design
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

The genesis commit. The bare tree began with a blank slate and a single objective: get a content-addressed, executable blob fabric running in the simplest possible form. The problem being solved was: how do you execute arbitrary logic blobs without the loader itself being a hardcoded dependency?

## What Was Built / Decided

`seed.py` introduced three primitives:

- `put(payload)` — SHA-256 content-addressed storage to `blob_vault/`
- `_raw_get(h)` — direct filesystem read, no indirection (the BIOS fallback)
- `invoke(h, context)` — executes a blob in a scrubbed `exec()` scope; ABI contract: blob must assign `result`; telemetry written as a blob artifact

Key ABI invariant: blob scope is scrubbed (`{"__builtins__": __builtins__}` only). The blob receives `context`, `log()`, and must produce `result`. Violating this raises a hard `ValueError`.

Telemetry is captured as a blob itself (put to vault), returning `telemetry_hash` alongside `result`.

## What It Enables

- Cold boot without recursion: BIOS is a direct filesystem read, not a blob invocation
- ABI enforcement: callers cannot assume implicit state; blobs are pure functions of context
- Telemetry as first-class artifact: latency, logs, errors captured at invocation time, content-addressed

## Why Not In council/f_N

The council tree's `seed.py` (council/f_0) is functionally identical at the BIOS level — same `put()`, same `_raw_get()`, same ABI contract. The council tree absorbed this design completely. [MEASURED — both trees share the three-primitive structure at their genesis commits]

The difference is implementation quality: council/f_0 added type annotations, docstrings, and an explicit ABI comment block. The bare tree treated the genesis as a working prototype, not a spec.

## Evidence Basis

- Structure confirmed by reading commit 739a228 diff [MEASURED]
- Council parallel confirmed by reading council/f_0 `seed.py` [MEASURED]
- ABI contract (result variable, scrubbed scope) visible in both trees [MEASURED]
