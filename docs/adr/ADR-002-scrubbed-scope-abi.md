# ADR-002: Scrubbed-Scope ABI — `context` In, `result` Out
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

The fabric needs a contract between the runtime engine (seed.py) and the blob payloads it executes. Without a strict boundary, a blob could reference linker internals, read from the filesystem, or modify global state — any of which would break content-addressed isolation and make behaviour non-deterministic across nodes.

The choice of Python's `exec()` as the execution primitive was settled early (Phase 1 BIOS seed). The ABI question was: what does the scope injected into `exec()` contain, and what is the blob's output contract?

## Decision

The blob ABI is exactly two inputs and one output:

- **Inputs:** `context` (caller-provided dict) and `log` (a callable for structured output)
- **Output:** the local variable `result` must be set before the blob exits

The scope passed to `exec()` is constructed from scratch and contains nothing else. No `__builtins__` override is made (standard library is available via `import` statements inside the blob), but linker internals (`VAULT_DIR`, `seed`, `promote`, `linker`) are absent. The ABI violation check — `"result" not in scope` — raises a `RuntimeError` before the caller sees any response.

The `result` variable name was chosen over a `return` statement because `exec()` does not surface return values from the code it runs. Using `result` makes the output contract explicit and detectable at the engine level.

## Alternatives Considered

- **`return` statement:** Structurally impossible — `exec()` does not capture return values from top-level code. Would require wrapping every blob in a function definition, adding boilerplate to every payload.
- **Injecting linker internals into scope:** Rejected. Would allow blobs to call `seed.put()`, modify `VAULT_DIR`, or reach into `promote.py`. Destroys isolation and makes behaviour node-dependent.
- **Output via side-channel (e.g. a mutable dict in scope):** More complex, same result. `result =` is the simplest form of the same contract.

## Consequences

- All blob payloads must set `result` before exiting. Blobs that raise an exception before setting `result` are recorded as failures in telemetry.
- Safety Pass 2 (SafetyVerification) enforces this at review time by scanning for patterns that would escape the scrubbed scope (`import os`, `import sys`, `open(`, `exec(`, `subprocess`, `VAULT_DIR`).
- Pass 3 (ProtocolCompliance) enforces it at promotion time via a dry-run invocation that checks for the ABI violation RuntimeError.
- Blobs are structurally incapable of side effects beyond their `result`. This is a safety property, not a convention.

## Evidence Basis

- [MEASURED] The `exec()` scope construction and `result` check appear in `seed.py` at the Phase 1 BIOS commit (059925a). The ABI violation error message is `"ABI violation: blob {hash} did not set 'result'"`.
- [MEASURED] Safety filter patterns are defined in `promote.py` at the Phase 2 commit (7613107) as `_DANGEROUS_PATTERNS`.
- [INFERRED] The `result` vs `return` choice is explained in the Phase 2 README: "Explicit output makes ABI violations detectable at the engine level. If a blob runs without setting `result`, the engine raises an error before the caller ever sees a response."
- [CITED] Python docs: `exec()` does not return values from executed code — return statements are no-ops at module scope.
