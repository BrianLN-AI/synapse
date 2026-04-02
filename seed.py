#!/usr/bin/env python3
"""
seed.py — D-JIT Logic Fabric Kernel
f_13: engine-as-expression — kernel split.

Kernel invariants:
  - vault: _raw_get + put (content-addressed store)
  - one fixed dispatch: exec(engine_payload, scope)  [_load_engine]
  - invoke / record_feedback: delegate to engine if loaded, else kernel fallback

The engine expression (manifest.blobs["engine"]["logic/python"]) holds all
execution policy: telemetry, bytecode cache, ABI enforcement.  It is
promotable, governed, and swappable without changing this file.

ABI contract (unchanged from f_12):
  - Inputs:  context (dict), log (callable)
  - Outputs: result variable in blob local scope
  - Scope:   scrubbed — blob cannot see kernel internals
"""

import blake3
import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

VAULT_DIR     = Path("./blob_vault")
BYTECODE_DIR  = Path("./blob_bytecode")   # persistent compiled code objects
MANIFEST_PATH = Path("./manifest.json")   # for engine bootstrap

# Shared between kernel and engine — engine updates this dict by reference.
# Logic: _LAST_TELEMETRY[logic_hash] = most recent telemetry/artifact hash.
_LAST_TELEMETRY: dict[str, str] = {}

# Engine scope cache — keyed by engine blob hash.
# Content-addressed blobs are immutable, so same hash → same scope is always safe.
_ENGINE: dict[str, Any] | None = None
_ENGINE_HASH: str | None = None

# Kernel-level code cache — L1 only, no disk persistence.
# Used only on the kernel-fallback path (bootstrap / pre-engine).
_CODE_CACHE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# VAULT — core content-addressed store
# ---------------------------------------------------------------------------

def _raw_get(content_hash: str) -> dict:
    """
    BIOS-level blob retrieval.  Reads directly from filesystem.
    Never delegates to any blob — prevents infinite recursion during bootstrap.
    """
    blob_path = VAULT_DIR / content_hash
    if not blob_path.exists():
        raise FileNotFoundError(f"BIOS: blob {content_hash} not found in vault")
    with open(blob_path, "r", encoding="utf-8") as f:
        return json.load(f)


def put(blob_type: str, payload: str) -> str:
    """
    Accept type/payload → compute blake3 → store in blob_vault/.
    Returns the content hash.  Idempotent: same content → same address.
    """
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
    content_hash = blake3.blake3(envelope.encode("utf-8")).hexdigest()

    blob_path = VAULT_DIR / content_hash
    if not blob_path.exists():
        with open(blob_path, "w", encoding="utf-8") as f:
            f.write(envelope)

    return content_hash


# ---------------------------------------------------------------------------
# ENGINE BOOTSTRAP — one fixed dispatch
# ---------------------------------------------------------------------------

def _load_engine() -> dict[str, Any] | None:
    """
    Load the engine expression from manifest.blobs["engine"]["logic/python"].
    Exec it with kernel scope to obtain invoke(), record_feedback(), etc.

    Returns the engine scope dict, or None if no engine is promoted yet.
    Cached by engine blob hash — immutable content guarantees stable cache.
    """
    global _ENGINE, _ENGINE_HASH
    try:
        manifest = json.loads(MANIFEST_PATH.read_text())
        engine_hash = manifest.get("blobs", {}).get("engine", {}).get("logic/python")
        if not engine_hash:
            return None
        if engine_hash == _ENGINE_HASH and _ENGINE is not None:
            return _ENGINE
        engine_blob = _raw_get(engine_hash)
        scope: dict[str, Any] = {
            "_raw_get":        _raw_get,
            "put":             put,
            "_LAST_TELEMETRY": _LAST_TELEMETRY,
            "_exec":           exec,          # primitive dispatch — injected, not called by name
            "BYTECODE_DIR":    BYTECODE_DIR,
        }
        exec(compile(engine_blob["payload"], "<engine>", "exec"), scope)  # noqa: S102 — ONE fixed dispatch
        _ENGINE = scope
        _ENGINE_HASH = engine_hash
        return _ENGINE
    except Exception:
        return None


# ---------------------------------------------------------------------------
# KERNEL FALLBACK — used during bootstrap before engine is in the manifest
# ---------------------------------------------------------------------------

def _record_telemetry_kernel(
    content_hash: str,
    latency_ms: float,
    memory_kb: float,
    log_lines: list[str],
    error: str | None,
) -> str:
    """Minimal telemetry writer — kernel path only."""
    record = {
        "invoked":       content_hash,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "latency_ms":    round(latency_ms, 3),
        "memory_kb":     round(memory_kb, 3),
        "log":           log_lines,
        "error":         error,
    }
    telem_hash = put("telemetry/artifact", json.dumps(record))
    _LAST_TELEMETRY[content_hash] = telem_hash
    return telem_hash


def _invoke_kernel(content_hash: str, context: dict | None = None) -> Any:
    """
    Kernel-path invoke — no engine delegation.
    Used during bootstrap before the engine expression is promoted.
    Full ABI enforcement and telemetry; L1-only bytecode cache (no disk persistence).
    """
    blob = _raw_get(content_hash)
    payload = blob["payload"]

    if context is None:
        context = {}

    log_lines: list[str] = []

    def _log(msg: str) -> None:
        log_lines.append(str(msg))

    scope: dict[str, Any] = {"context": context, "log": _log}

    tracemalloc.start()
    start_ns = time.perf_counter_ns()

    try:
        if content_hash not in _CODE_CACHE:
            _CODE_CACHE[content_hash] = compile(
                payload, f"<blob:{content_hash[:8]}>", "exec"
            )
        exec(_CODE_CACHE[content_hash], scope)  # noqa: S102
    except Exception as exc:
        elapsed = (time.perf_counter_ns() - start_ns) / 1e6
        tracemalloc.stop()
        _record_telemetry_kernel(content_hash, elapsed, 0, log_lines, str(exc))
        raise

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1e6
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_kb = peak / 1024

    if "result" not in scope:
        _record_telemetry_kernel(
            content_hash, elapsed_ms, memory_kb, log_lines,
            "ABI violation: result variable not set",
        )
        raise RuntimeError(
            f"ABI violation: blob {content_hash} did not set 'result'"
        )

    _record_telemetry_kernel(content_hash, elapsed_ms, memory_kb, log_lines, None)
    return scope["result"]


# ---------------------------------------------------------------------------
# PUBLIC API — delegates to engine, falls back to kernel path
# ---------------------------------------------------------------------------

def invoke(content_hash: str, context: dict | None = None) -> Any:
    """
    Invoke a blob by hash.
    Delegates to the engine expression when one is promoted in the manifest;
    falls back to the kernel-path invoke during bootstrap and review.
    """
    engine = _load_engine()
    if engine and "invoke" in engine:
        return engine["invoke"](content_hash, context)
    return _invoke_kernel(content_hash, context)


def record_feedback(
    logic_hash: str,
    outcome: str,
    confidence: float = 1.0,
    reviewer: str = "caller",
    reviewer_hash: str | None = None,
) -> str:
    """
    Record caller-observed outcome for a logic blob.
    Delegates to the engine expression when loaded; kernel fallback otherwise.

    The proven-execution anchor (_LAST_TELEMETRY) is shared between kernel
    and engine via the injected dict reference — feedback recorded via either
    path links to the same telemetry records.
    """
    engine = _load_engine()
    if engine and "record_feedback" in engine:
        return engine["record_feedback"](
            logic_hash, outcome, confidence, reviewer, reviewer_hash
        )
    # Kernel fallback
    invocation_telem = _LAST_TELEMETRY.get(logic_hash)
    record = {
        "invoked":          logic_hash,
        "invocation_telem": invocation_telem,
        "outcome":          outcome,
        "confidence":       round(float(confidence), 4),
        "reviewer":         reviewer,
        "reviewer_hash":    reviewer_hash,
        "timestamp_utc":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return put("feedback/outcome", json.dumps(record, sort_keys=True))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="seed",
        description="D-JIT Logic Fabric Kernel CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_put = sub.add_parser("put", help="Hash and store a blob")
    p_put.add_argument("type", help="Blob type (e.g. logic/python)")
    p_put.add_argument("payload", help="Blob payload string (or - to read stdin)")

    p_inv = sub.add_parser("invoke", help="Invoke a blob by content hash")
    p_inv.add_argument("hash", help="Content hash")
    p_inv.add_argument(
        "--context", default="{}", help="JSON context object (default: {})"
    )

    args = parser.parse_args()

    if args.cmd == "put":
        payload = sys.stdin.read() if args.payload == "-" else args.payload
        h = put(args.type, payload)
        print(h)

    elif args.cmd == "invoke":
        ctx = json.loads(args.context)
        result = invoke(args.hash, ctx)
        print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)


if __name__ == "__main__":
    _cli()
