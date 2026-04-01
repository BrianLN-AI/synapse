# CAP-BARE-003: Recursive Leap — Self-Referential Discovery
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

The system had a manifest but `_raw_get()` was still a dumb filesystem read. The Recursive Leap made the fabric self-referential: the blob that resolves other blobs is itself a blob. This creates a bootstrapping challenge identical to a BIOS: you need to load the loader.

## What Was Built / Decided

Commit 0358dee refactored `_raw_get()` to a two-path resolver:

1. **BIOS path** (`is_bios=True` or no manifest present): direct filesystem read, no recursion possible
2. **Recursive path**: reads `manifest.hash` → loads manifest via BIOS → extracts `l2` hash → executes the L2 discovery blob to resolve the target

Anti-recursion guard: if the target hash IS the L2 blob, fall back to BIOS (the loader cannot load itself via itself).

The L2 discovery blob (`l2_discovery.py`) takes `context.target` (a hash) and returns `{"path": <filesystem path>}`. The resolver then reads from that path.

Key design insight captured in the commit narrative: "Managing infinite recursion requires careful isolation. The L2 Blob must be accessible via BIOS even if it's the primary resolution engine for everything else."

## What It Enables

- Discovery logic is now upgradeable without modifying seed.py — promote a new L2 hash, and resolution behavior changes
- The loader is itself a blob: it can be inspected, audited, versioned
- Establishes the pattern all subsequent leaps follow: consult manifest → find layer hash → exec layer blob → use result

## Why Not In council/f_N

The council tree implemented the same recursive resolution concept in council/f_0 (`d5b06b5`: "Phase 3 — Recursive Leap"). The capability was adopted. The implementation diverges at f_1: the council tree introduced a compiled code cache (`_CODE_CACHE`, `_load_code()`), replacing bare `exec()` for hot blobs. The bare tree never added compilation caching. [MEASURED]

## Evidence Basis

- Commit 0358dee diff read directly [MEASURED]
- Anti-recursion guard (`if h == l2_h`) confirmed in diff [MEASURED]
- Council parallel at d5b06b5 confirmed [MEASURED]
- Council bytecode cache: confirmed in council/f_3 `seed.py` [MEASURED]
