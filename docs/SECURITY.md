# Security Audit — D-JIT Logic Fabric
**Date:** 2026-04-04
**Scope:** Phases 1-3 (Seed, Judge, Linker — Python + JS)

## Critical

### 1. Unsandboxed Execution
`exec()` / `eval()` give blobs full process access. Any blob can read sensitive files, exfiltrate env vars, delete files, spawn reverse shells. Zero containment at the binding layer.

### 2. Manifest Trust Bootstrapping
`manifest.json` on disk is trusted without integrity verification. An attacker who can write to the working directory can replace it with a manifest pointing to malicious discovery/planning blobs. The linker never verifies that the file content matches `manifest_hash`.

### 3. Telemetry Spoofing
Anyone can `PUT` a fake `telemetry/artifact` blob with a forged `predecessor` pointing to any target hash. This inflates `success_rate` and manipulates trust scores. No authentication on telemetry emission.

## High

### 4. No Blob Size Limits
`PUT` accepts arbitrary payloads. A 10GB blob fills the disk. No validation anywhere.

### 5. No Rate Limiting
Rapid-fire `PUT` calls create unlimited files. Easy DoS.

### 6. Race Conditions
File-based KV with no locking. Two concurrent `PUT`s for the same hash could partially write. Two concurrent `INVOKE`s could read a half-written blob.

### 7. Lineage Forgery
`predecessor` is user-controlled with no validation. You can claim any blob is a descendant of any other blob, faking version history.

## Medium

### 8. Signature Field is Dead Code
The schema defines `metadata.signature` but it's never populated, verified, or enforced. Gives a false sense of provenance.

### 9. Information Leakage via Telemetry
Latency and memory metrics are stored in the vault as readable JSON. Side-channel: an attacker could infer what code is running, how complex it is, or detect when sensitive operations occur.

### 10. Revert.sh Single-Backup
Each `bootstrap()` overwrites `manifest.json.bak`. If you bootstrap twice, the original is gone. No chain of history.

## Low

### 11. Type Field Unvalidated
`PUT` accepts any string as `type`. Could store `type: "../../../etc/passwd"` — harmless as a filename key (hash-based), but confusing for downstream consumers.

### 12. Error Messages Leak Internals
`FileNotFoundError("blob not found: {hash}")` and `KeyError("function 'X' not found in blob {hash}")` expose vault structure and blob internals.

## Fundamental Tension

The system is designed for a trusted environment where blobs are authored by the operator. It has no threat model for untrusted blobs. If the goal is to eventually execute third-party or LLM-generated blobs, the current architecture needs a sandbox layer before the binding engine.
