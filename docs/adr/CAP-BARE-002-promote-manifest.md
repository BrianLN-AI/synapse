# CAP-BARE-002: Promote/Manifest Root Pointer
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

After the BIOS seed worked, the next problem was: how does the system know which blobs are the "system" blobs (discovery, planning, binding)? The answer needed to be safe — promoting a bad set of layer hashes should fail before corrupting the running system.

## What Was Built / Decided

Two artifacts introduced in commit f26c048:

- `manifest.json` — declares layer hashes by name (`l1`, `l2`, `l3`, `l4`)
- `manifest.hash` — a single-file root pointer containing the SHA-256 of the promoted manifest blob

The `promote` command in `seed.py`:
1. Reads `manifest.json`
2. Verifies every listed hash exists in `blob_vault/` (integrity check)
3. Stores the manifest as a blob via `put()`
4. Overwrites `manifest.hash` only after all hashes verified

This is an atomic-ish promotion: if any hash is missing, the system exits before touching `manifest.hash`. The running system is never corrupted.

Layer fixtures (`l1_interface.py`, `l2_discovery.py`, `l3_planning.py`, `l4_binding.py`) were added as stub files — not blobs yet, just source placeholders to be put into the vault.

## What It Enables

- Safe hot-swap of system blobs: the manifest is itself content-addressed, so any promotion is auditable
- Root-of-trust: `manifest.hash` is the single external mutable pointer; everything else is immutable
- Integrity gate: you cannot promote a manifest that references missing blobs

## Why Not In council/f_N

The council tree took a different path. Council/f_0 (`fadcf3c`) uses a `manifest.json` with a fitness feedback loop and telemetry integration — the promote concept evolved into a scored promotion cycle. The bare tree's simple `promote` command (verify + write) was absorbed conceptually but the council tree never shipped a `promote` CLI verb in the same form. [INFERRED — council/f_3 manifest is runtime-generated, not manually promoted]

## Evidence Basis

- Commit f26c048 diff read directly [MEASURED]
- Integrity-check-before-write logic confirmed in seed.py diff [MEASURED]
- Council tree promote comparison: council/f_0 uses manifest but no `promote` command [MEASURED]
