# Design Memo: Engine as Expression

**Date:** 2026-04-02
**Status:** Design — pre-ADR
**Target implementation:** f_13 (Track A)

---

## The problem

`seed.py` is ~260 lines. It conflates two distinct things:

**Kernel** — the irreducible minimum, cannot be generated, never changes:
- `vault.put(type, payload) → hash`
- `vault.get(hash) → envelope`
- Load manifest → find engine expression hash → one `exec(payload, scope)` call → derive `invoke`

**Policy** — execution semantics, should be evolvable:
- Bytecode cache (compile once, reuse across invocations)
- Scrubbed scope construction (what is injected: `context`, `log`)
- Telemetry wrapping (start/stop timing, memory measurement)
- ABI enforcement (`result` must be present after execution)
- Error capture and telemetry recording

Policy is currently hardcoded in the kernel. This means: changing execution semantics
(sandboxing strategy, telemetry format, ABI enforcement rules) requires modifying the
kernel and redeploying. The execution model cannot be evolved via the governance gate.

---

## The target state

The kernel is ~30 lines:

```python
import blake3, json
from pathlib import Path
from typing import Any

VAULT   = Path("./blob_vault")
MANIFEST = Path("./manifest.json")

def _get(h: str) -> dict:
    return json.loads((VAULT / h).read_text())

def _put(type_: str, payload: Any) -> str:
    envelope = json.dumps({"type": type_, "payload": payload}, sort_keys=True)
    h = blake3.blake3(envelope.encode()).hexdigest()
    (VAULT / h).write_text(envelope)
    return h

def bootstrap() -> callable:
    manifest    = json.loads(MANIFEST.read_text())
    engine_hash = manifest["blobs"]["engine"]["logic/python"]
    payload     = _get(engine_hash)["payload"]
    scope: dict = {"_get": _get, "_put": _put}
    exec(payload, scope)               # ONE fixed exec() call — loads the engine
    return scope["invoke"]

invoke = bootstrap()
```

Everything else — bytecode cache, telemetry, scrubbed scope, ABI enforcement — lives in
the engine expression in the vault.

---

## What the engine expression contains

The engine expression (`logic/python`, promoted to `manifest.blobs.engine`) is the current
execution policy. Its payload is Python source that defines `invoke`:

```python
# engine expression payload (sketch)
import tracemalloc, time

_bytecode_cache = {}

def invoke(content_hash: str, context: dict | None = None) -> dict:
    blob    = _get(content_hash)
    payload = blob["payload"]
    
    if content_hash not in _bytecode_cache:
        _bytecode_cache[content_hash] = compile(payload, f"<expr:{content_hash[:8]}>", "exec")
    
    scope = {"context": context or {}, "log": lambda msg: log_lines.append(str(msg))}
    log_lines = []
    
    tracemalloc.start()
    t0 = time.perf_counter_ns()
    
    try:
        exec(_bytecode_cache[content_hash], scope)
    except Exception as exc:
        _record_telemetry(content_hash, ...)
        raise
    
    if "result" not in scope:
        raise ABIViolation(f"expression {content_hash[:8]} did not set result")
    
    result = scope["result"]
    _record_telemetry(content_hash, latency_ms=..., result=result)
    
    return {"result": result, "attestation": _attest(content_hash)}
```

---

## Why this matters

**1. The engine is evolvable.**
Changing sandboxing strategy = promote a new engine expression. Changing telemetry format
= promote a new engine expression. Changing ABI enforcement rules = promote a new engine
expression. No kernel change required.

**2. The engine is content-addressed.**
`engine_hash = blake3(engine_payload)`. The ZK circuit can prove `engine_hash == blake3(engine_content)`.
You can prove *which engine version ran which expression*. Engine version becomes a governed,
auditable artifact.

**3. Multi-runtime support becomes natural.**
A WASM engine expression dispatches to a WASM runtime. A JS engine expression spawns a
Node subprocess. Different tenants can have different engine expressions. The kernel
doesn't change.

**4. The kernel becomes the universal constant.**
Any implementation of this system in any language has the same ~30-line kernel. The engine
expression is the implementation-specific part. The vault + one `exec` equivalent is the
minimum required to bootstrap.

---

## Implementation path

1. Extract policy code from `seed.py` into a new engine expression blob
2. Promote the engine expression to `manifest.blobs.engine`
3. Slim `seed.py` down to the kernel (~30 lines)
4. All existing tests must pass without modification (the behavior is identical)

**Acceptance criterion:** the engine can be swapped by promoting a new engine expression
without modifying any kernel code.

---

## Open questions

- Should the engine expression have access to `_put` (can it store telemetry directly)?
  Current answer: yes — telemetry blobs are written by the engine, not the kernel.
- Key rotation for the engine expression: if the engine is compromised, the kernel must
  still be trusted. The kernel's one `exec()` call is the only fixed execution boundary.
- Multi-engine: can a manifest have multiple engine expressions for different expression types
  (`engine/python`, `engine/wasm`)? Likely yes — requires per-type dispatch in the kernel.
