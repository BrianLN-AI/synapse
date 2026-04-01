#!/usr/bin/env python3
"""
seed.py — D-JIT Logic Fabric BIOS Seed
Phase 1 implementation per f(undefined).md v1.2.1-Alpha

ABI contract:
  - Inputs:  context (dict), log (callable)
  - Outputs: result variable in blob local scope
  - Scope:   scrubbed — blob cannot see Linker internals
"""

import hashlib
import json
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any

VAULT_DIR = Path("./blob_vault")

# Compilation cache — compile each blob's payload once, reuse the code object.
# exec() recompiles source on every call; caching eliminates that tax for hot blobs.
# f_1 discovery: longer v2 blobs paid a per-call compilation cost that masked
# their true runtime performance. Cache keyed by content_hash (immutable blobs).
_CODE_CACHE: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# BIOS Fallback — _raw_get bypasses blob-based Discovery
# This is the bootstrap root. It MUST be self-contained. No blob calls here.
# ---------------------------------------------------------------------------

def _raw_get(content_hash: str) -> dict:
    """
    BIOS-level blob retrieval. Reads directly from filesystem.
    Never delegates to Discovery layer — prevents infinite recursion.
    """
    blob_path = VAULT_DIR / content_hash
    if not blob_path.exists():
        raise FileNotFoundError(f"BIOS: blob {content_hash} not found in vault")
    with open(blob_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# PUT — content-address a blob and store it
# ---------------------------------------------------------------------------

def put(blob_type: str, payload: str) -> str:
    """
    Accept type/payload → compute SHA-256 → store in blob_vault/.
    Returns the content hash.
    """
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
    content_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()

    blob_path = VAULT_DIR / content_hash
    if not blob_path.exists():
        with open(blob_path, "w", encoding="utf-8") as f:
            f.write(envelope)

    return content_hash


# ---------------------------------------------------------------------------
# INVOKE — load, bind into scrubbed scope, enforce result contract
# ---------------------------------------------------------------------------

def invoke(content_hash: str, context: dict | None = None) -> Any:
    """
    Load blob by hash → exec in scrubbed scope → verify result → return.
    Wraps every run with telemetry (stored as blob).
    Raises if result variable is absent (ABI violation).
    """
    blob = _raw_get(content_hash)
    payload = blob["payload"]

    if context is None:
        context = {}

    log_lines: list[str] = []

    def _log(msg: str) -> None:
        log_lines.append(str(msg))

    # Scrubbed scope — only context and log() injected; no Linker internals
    scope: dict[str, Any] = {
        "context": context,
        "log": _log,
    }

    tracemalloc.start()
    start_ns = time.perf_counter_ns()

    try:
        if content_hash not in _CODE_CACHE:
            _CODE_CACHE[content_hash] = compile(payload, f"<blob:{content_hash[:8]}>", "exec")
        exec(_CODE_CACHE[content_hash], scope)  # noqa: S102 — intentional; this IS the engine
    except Exception as exc:
        _record_telemetry(
            content_hash=content_hash,
            latency_ms=(time.perf_counter_ns() - start_ns) / 1e6,
            memory_kb=0,
            log_lines=log_lines,
            error=str(exc),
        )
        raise

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1e6
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    memory_kb = peak / 1024

    # ABI enforcement — result MUST be set
    if "result" not in scope:
        _record_telemetry(
            content_hash=content_hash,
            latency_ms=elapsed_ms,
            memory_kb=memory_kb,
            log_lines=log_lines,
            error="ABI violation: result variable not set",
        )
        raise RuntimeError(
            f"ABI violation: blob {content_hash} did not set 'result'"
        )

    _record_telemetry(
        content_hash=content_hash,
        latency_ms=elapsed_ms,
        memory_kb=memory_kb,
        log_lines=log_lines,
        error=None,
    )

    return scope["result"]


# ---------------------------------------------------------------------------
# TELEMETRY — record every invocation as a blob artifact
# ---------------------------------------------------------------------------

def _record_telemetry(
    content_hash: str,
    latency_ms: float,
    memory_kb: float,
    log_lines: list[str],
    error: str | None,
) -> str:
    """
    PUT a telemetry/artifact blob for every invocation.
    Self-contained — uses put() directly, never invoke().
    """
    record = {
        "invoked": content_hash,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "latency_ms": round(latency_ms, 3),
        "memory_kb": round(memory_kb, 3),
        "log": log_lines,
        "error": error,
    }
    return put("telemetry/artifact", json.dumps(record))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="seed",
        description="D-JIT Logic Fabric BIOS Seed CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # seed put <type> <payload>
    p_put = sub.add_parser("put", help="Hash and store a blob")
    p_put.add_argument("type", help="Blob type (e.g. logic/python)")
    p_put.add_argument("payload", help="Blob payload string (or - to read stdin)")

    # seed invoke <hash> [--context '{"key":"val"}']
    p_inv = sub.add_parser("invoke", help="Invoke a blob by content hash")
    p_inv.add_argument("hash", help="SHA-256 content hash")
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
