#!/usr/bin/env python3
"""
linker.py — D-JIT Logic Fabric Linker
f_0: Self-hosted Discovery, Planning, and Telemetry-Reader layers.

Layer stack (per f(undefined).md §3):
  Interface → Discovery (Librarian) → Planning (Broker) → Binding (Engine)

Feedback loop (f_0 closure):
  invoke() → telemetry blob → read_telemetry() → enriched SuccessRate/latency
           → arbitrate() → Planning blob fitness → best candidate selected

The loop is closed: measured performance informs every future arbitration.
"""

from typing import Any

import promote
import seed

# ---------------------------------------------------------------------------
# Telemetry Reader — reads vault, aggregates fitness signals per blob hash
# ---------------------------------------------------------------------------

# Inline fallback used when telemetry-reader blob is not yet in the manifest.
# Keeps bootstrap safe — read_telemetry() works before the blob is promoted.
def _telemetry_fallback(vault_dir: str) -> dict:
    import json
    from pathlib import Path

    stats: dict[str, dict] = {}
    for blob_path in Path(vault_dir).iterdir():
        if not blob_path.is_file():
            continue
        try:
            envelope = json.loads(blob_path.read_text())
        except Exception:
            continue
        if envelope.get("type") != "telemetry/artifact":
            continue
        record = json.loads(envelope["payload"])
        invoked = record.get("invoked")
        if not invoked:
            continue
        s = stats.setdefault(invoked, {"total": 0, "success": 0, "latency_sum": 0.0, "memory_sum": 0.0})
        s["total"] += 1
        if record.get("error") is None:
            s["success"] += 1
        s["latency_sum"] += record.get("latency_ms", 0.0)
        s["memory_sum"] += record.get("memory_kb", 0.0)

    return {
        h: {
            "success_rate": s["success"] / s["total"],
            "avg_latency_ms": s["latency_sum"] / s["total"],
            "avg_memory_kb": s["memory_sum"] / s["total"],
            "invocation_count": s["total"],
        }
        for h, s in stats.items()
        if s["total"] > 0
    }


def read_telemetry() -> dict:
    """
    Aggregate telemetry blobs → fitness signals per blob hash.

    Routes through the promoted telemetry-reader blob when available.
    Falls back to inline implementation — bootstrap safe.

    Passes approved_feedback from the manifest so the telemetry reader
    only counts governed feedback blobs toward FeedbackScore (f_5).
    Unpromoted feedback blobs in the vault are silently ignored.

    Returns: {blob_hash: {success_rate, avg_latency_ms, ..., feedback_score}}
    """
    manifest = promote.load_manifest()
    telem_hash = (
        manifest.get("blobs", {})
        .get("telemetry-reader", {})
        .get("logic/python")
    )
    # Build reviewer trust weights from the manifest reviewer registry (f_6).
    # Each council/reviewer blob may declare a trust_weight in [0.0, 1.0].
    # The telemetry reader uses this to weight approved feedback by reviewer authority.
    reviewer_trust: dict[str, float] = {}
    for rh in manifest.get("reviewers", {}):
        try:
            rev_blob = seed._raw_get(rh)
            rev_data = json.loads(rev_blob["payload"])
            reviewer_trust[rh] = float(rev_data.get("trust_weight", 1.0))
        except Exception:
            reviewer_trust[rh] = 1.0

    import json as _json
    ctx = {
        "vault_dir":         str(seed.VAULT_DIR),
        "approved_feedback": manifest.get("approved_feedback", {}),
        "reviewer_trust":    reviewer_trust,
    }
    if telem_hash:
        return seed.invoke(telem_hash, ctx)
    return _telemetry_fallback(str(seed.VAULT_DIR))


# ---------------------------------------------------------------------------
# Layer 2: Discovery (The Librarian)
# ---------------------------------------------------------------------------

def resolve(content_hash: str) -> dict:
    """
    Resolve a content hash to its blob envelope.

    Uses the promoted Discovery blob if in the manifest.
    Falls back to BIOS _raw_get — prevents bootstrap recursion.
    """
    manifest = promote.load_manifest()
    disc_hash = (
        manifest.get("blobs", {})
        .get("discovery", {})
        .get("logic/python")
    )
    if disc_hash:
        return seed.invoke(disc_hash, {
            "hash": content_hash,
            "vault_dir": str(seed.VAULT_DIR),
        })
    return seed._raw_get(content_hash)  # BIOS fallback


# ---------------------------------------------------------------------------
# Layer 3: Planning (The Broker) — with telemetry enrichment
# ---------------------------------------------------------------------------

def arbitrate(candidates: list[dict], auto_enrich: bool = True) -> dict | None:
    """
    Market Arbitrage: select the best candidate blob.

    Fitness: f(Link) = SuccessRate × Integrity / Latency × ComputeCost

    auto_enrich=True (default): reads live telemetry to populate SuccessRate,
    latency_ms, and cost (memory proxy) from measured data before scoring.
    Caller-provided values are used only as fallback when no history exists.

    This closes the feedback loop: every past invocation informs future selection.
    """
    if not candidates:
        return None

    if auto_enrich:
        telem = read_telemetry()
        enriched = []
        for c in candidates:
            h = c["hash"]
            measured = telem.get(h, {})
            enriched.append({
                **c,
                # Measured values take precedence over caller defaults
                "success_rate":     measured.get("success_rate",    c.get("success_rate", 1.0)),
                "latency_ms":       measured.get("avg_latency_ms",  c.get("latency_ms", 1.0)),
                "cost":             max(measured.get("avg_memory_kb", c.get("cost", 1.0)), 0.001),
                # invocation_count for Bayesian smoothing (Planning v2+)
                "invocation_count": measured.get("invocation_count", c.get("invocation_count", 0)),
                # p95_latency_ms from telemetry-reader v2 — conservative tail-latency signal
                # Planning v3 uses this as the latency input instead of avg_latency_ms
                "p95_latency_ms":   measured.get("p95_latency_ms",  c.get("p95_latency_ms", None)),
                # integrity from telemetry-reader v3 — recency-weighted success streak
                # Default 0.5: unknown blobs are uncertain; proven blobs earn > 0.5 through use
                "integrity":        measured.get("integrity",       c.get("integrity", 0.5)),
                # feedback_score from telemetry-reader v5 — governed downstream outcome signal
                # Default 1.0: no approved feedback → neutral, not penalised
                "feedback_score":   measured.get("feedback_score",  c.get("feedback_score", 1.0)),
                "feedback_count":   measured.get("feedback_count",  c.get("feedback_count", 0)),
            })
        candidates = enriched

    manifest = promote.load_manifest()
    plan_hash = (
        manifest.get("blobs", {})
        .get("planning", {})
        .get("logic/python")
    )
    if plan_hash:
        return seed.invoke(plan_hash, {"candidates": candidates})

    # Default: no arbitrage
    return {
        "selected": candidates[0]["hash"],
        "score": None,
        "rationale": "default (planning not promoted)",
    }


# ---------------------------------------------------------------------------
# Layer 4: Binding (The Engine) — full linker invoke
# ---------------------------------------------------------------------------

def invoke(content_hash: str, context: dict | None = None) -> Any:
    """
    Full linker invoke: Discovery → Binding.

    resolve() validates the blob exists (via Discovery blob or BIOS).
    seed.invoke() executes it with ABI enforcement and telemetry.
    """
    resolve(content_hash)  # raises FileNotFoundError if hash unknown
    return seed.invoke(content_hash, context)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        prog="linker",
        description="D-JIT Logic Fabric Linker CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inv = sub.add_parser("invoke", help="Invoke a blob through the full layer stack")
    p_inv.add_argument("hash")
    p_inv.add_argument("--context", default="{}")

    p_arb = sub.add_parser("arbitrate", help="Run Planning arbitrage over candidates")
    p_arb.add_argument("candidates_json", help="JSON array of candidate objects")
    p_arb.add_argument("--no-enrich", action="store_true", help="Skip telemetry enrichment")

    p_res = sub.add_parser("resolve", help="Resolve a hash via Discovery layer")
    p_res.add_argument("hash")

    sub.add_parser("telemetry", help="Dump aggregated telemetry fitness signals")

    args = parser.parse_args()

    if args.cmd == "invoke":
        ctx = json.loads(args.context)
        result = invoke(args.hash, ctx)
        print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)

    elif args.cmd == "arbitrate":
        candidates = json.loads(args.candidates_json)
        result = arbitrate(candidates, auto_enrich=not args.no_enrich)
        print(json.dumps(result, indent=2))

    elif args.cmd == "resolve":
        blob = resolve(args.hash)
        print(json.dumps(blob, indent=2))

    elif args.cmd == "telemetry":
        print(json.dumps(read_telemetry(), indent=2))


if __name__ == "__main__":
    _cli()
