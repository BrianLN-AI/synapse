#!/usr/bin/env python3
"""
seed.py — D-JIT Logic Fabric BIOS Seed
Phase 1 implementation per f(undefined).md v1.2.1-Alpha

ABI contract:
  - Inputs:  context (dict), log (callable)
  - Outputs: result variable in blob local scope
  - Scope:   scrubbed — blob cannot see Linker internals
"""

import blake3
import json
import marshal
import os
import time
import tracemalloc
from pathlib import Path
from typing import Any

VAULT_DIR    = Path("./blob_vault")
BYTECODE_DIR = Path("./blob_bytecode")   # persistent on-disk compiled code objects

# In-process compilation cache — compile each blob's payload once per process,
# reuse the code object. exec() recompiles source on every call; caching eliminates
# that tax for hot blobs.
# f_1 discovery: longer v2 blobs paid a per-call compilation cost that masked
# their true runtime performance. Cache keyed by content_hash (immutable blobs).
_CODE_CACHE: dict[str, Any] = {}

# Tracks the most recent telemetry blob hash per logic blob invoked in this process.
# Used by record_feedback() to anchor feedback to a proven execution (f_4).
_LAST_TELEMETRY: dict[str, str] = {}  # logic_hash → most recent telemetry/artifact hash


def _load_code(content_hash: str, payload: str) -> Any:
    """
    Return a compiled code object for payload, using a two-level cache:
      L1 — in-process _CODE_CACHE (dict in memory, reset on restart)
      L2 — on-disk BYTECODE_DIR/<hash>.pyc (persists across restarts)

    Why a persistent L2?  _CODE_CACHE is ephemeral: the first invocation of any
    blob in a new process always paid the compile() tax.  For the core blobs
    (discovery, planning, telemetry-reader) that are invoked thousands of times
    across many short-lived processes, that cold-start cost compounds.  marshal
    serialises Python code objects to bytes; storing and reloading them eliminates
    recompilation entirely after the first run ever.

    Blobs are immutable (content_hash is the SHA-256 of the envelope), so a
    cached bytecode file for a given hash is always valid — it can never go stale.
    """
    if content_hash in _CODE_CACHE:
        return _CODE_CACHE[content_hash]

    BYTECODE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = BYTECODE_DIR / f"{content_hash}.pyc"

    if cache_path.exists():
        try:
            code = marshal.loads(cache_path.read_bytes())
            _CODE_CACHE[content_hash] = code
            return code
        except Exception:
            pass  # corrupt or incompatible bytecode — fall through to recompile

    code = compile(payload, f"<blob:{content_hash[:8]}>", "exec")
    try:
        cache_path.write_bytes(marshal.dumps(code))
    except Exception:
        pass  # disk write failure is non-fatal; L1 cache still works
    _CODE_CACHE[content_hash] = code
    return code


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
    Accept type/payload → compute blake3 → store in blob_vault/.
    Returns the content hash.
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
        exec(_load_code(content_hash, payload), scope)  # noqa: S102 — intentional; this IS the engine
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
    telem_hash = put("telemetry/artifact", json.dumps(record))
    _LAST_TELEMETRY[content_hash] = telem_hash
    return telem_hash


# ---------------------------------------------------------------------------
# FEEDBACK — record caller-observed outcomes as governed blobs
# ---------------------------------------------------------------------------

def record_feedback(
    logic_hash: str,
    outcome: str,
    confidence: float = 1.0,
    reviewer: str = "caller",
    reviewer_hash: str | None = None,
) -> str:
    """
    Store a feedback/outcome blob for a logic blob.

    Why feedback as a blob?  The fitness formula (f_0–f_3) only observes local
    signals: latency, memory, success/failure of the invocation itself.  It cannot
    see whether the downstream system that used the blob's output succeeded.  A
    type guard that prevents silent failures shows no measurable fitness improvement
    in isolation — its benefit only appears in downstream outcomes.  Feedback blobs
    carry that downstream signal back into the vault.

    Proven-execution anchor:  feedback is tied to _LAST_TELEMETRY[logic_hash], the
    most recent telemetry hash produced by invoking this blob in the current process.
    This means feedback can only be recorded after an actual invocation — it cannot
    be fabricated without running the blob first.

    Governance:  feedback blobs are content-addressed and immutable.  Whether they
    count toward fitness depends on whether the governing process (Triple-Pass +
    Council Approval) has promoted them — same mechanism as every other blob type.
    Recording a feedback blob places it in the vault; promotion is a separate step.

    Args:
        logic_hash:  SHA-256 hash of the logic/python blob being rated.
        outcome:     "pass", "fail", or "partial".
        confidence:  0.0–1.0 weight applied when aggregating feedback scores.
        reviewer:      Free-form string identifier (legacy / informal).
        reviewer_hash: Content hash of a council/reviewer blob (f_6+ governed path).
                       When present, the telemetry reader can weight this feedback
                       by the reviewer's trust_weight field.

    Returns the content hash of the feedback/outcome blob.
    """
    invocation_telem = _LAST_TELEMETRY.get(logic_hash)
    record = {
        "invoked":          logic_hash,
        "invocation_telem": invocation_telem,   # proven-execution anchor
        "outcome":          outcome,
        "confidence":       round(float(confidence), 4),
        "reviewer":         reviewer,
        "reviewer_hash":    reviewer_hash,      # governed reviewer blob hash (f_6+)
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
