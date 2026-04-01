# CAP-BARE-008: Polyglot Runtimes — Execution Beyond Python
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit 7daff80 (f_1 Phase 2) extended the L4 binding blob to execute blobs in runtimes other than Python. Specifically: JavaScript via Node.js subprocess. The motivation was to allow the fabric to host logic written in any language, not just the language of the Linker.

## What Was Built / Decided

L3 (broker) was updated to include `runtime` in the execution plan:

```python
{"method": "local_exec", "node": "...", "runtime": "python|javascript", ...}
```

L4 (binding) was updated to branch on `runtime`:
- `python`: existing `exec()` path
- `javascript`: wraps payload in a Node.js script template, runs via `subprocess.run(['node', '-e', ...])`, parses stdout as JSON to extract `result`

`seed.py` injected `subprocess` and `json` into the L4 scope to enable subprocess calls from within L4.

The JavaScript wrapper template enforces the same ABI contract: `result` variable, `log()` function (mapped to `console.error`), `context` object available.

Commit narrative: "Passing the full 'request_envelope' to L3 is critical for accurate planning. Layered normalization (L1) ensures L3 receives clean parameters."

## What It Enables

- Language-heterogeneous blob vault: JavaScript logic blobs alongside Python blobs
- ABI contract is language-agnostic: the result/log/context contract translates across runtimes
- Foundation for WASM, shell scripts, or other runtimes via the same L4 extension point

## Why Not In council/f_N

The council tree is Python-only. Council/f_N uses compiled Python code objects (`marshal`, `_load_code()`) as its performance primitive — this is fundamentally incompatible with polyglot execution. The council tree's optimization path went deeper into Python-specific performance rather than broader into language support. [MEASURED — council/f_3 uses marshal/compile, no subprocess runtime branching]

The polyglot approach has a significant weakness: the JavaScript execution path uses an inline string template injected via subprocess, with no sandbox or resource limits. This is a security concern. The council tree's choice to stay Python-only avoided this problem. [INFERRED]

## Evidence Basis

- Commit 7daff80 diff and l4_binding.py diff read directly [MEASURED]
- JavaScript wrapper template structure confirmed [MEASURED]
- Council Python-only approach: confirmed by marshal usage in council/f_3 [MEASURED]
- Security concern (unsandboxed subprocess): inferred from design [INFERRED]
