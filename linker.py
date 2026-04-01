#!/usr/bin/env python3
"""
linker.py — D-JIT Logic Fabric Linker
Phase 3: Self-hosted Discovery and Planning layers.

Layer stack (per f(undefined).md §3):
  Interface → Discovery (Librarian) → Planning (Broker) → Binding (Engine)

When Discovery/Planning blobs are in the manifest the fabric is self-hosting:
invocation routes through blobs stored inside the vault itself.
Falls back to BIOS (_raw_get) when not yet promoted — bootstrap safe.
"""

from typing import Any

import promote
import seed

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
    # BIOS fallback
    return seed._raw_get(content_hash)


# ---------------------------------------------------------------------------
# Layer 3: Planning (The Broker)
# ---------------------------------------------------------------------------

def arbitrate(candidates: list[dict]) -> dict | None:
    """
    Market Arbitrage: select the best candidate blob.

    Fitness: f(Link) = SuccessRate × Integrity / Latency × ComputeCost

    Uses the promoted Planning blob if in the manifest.
    Falls back to first candidate when not yet promoted.
    """
    if not candidates:
        return None
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

    p_res = sub.add_parser("resolve", help="Resolve a hash via Discovery layer")
    p_res.add_argument("hash")

    args = parser.parse_args()

    if args.cmd == "invoke":
        ctx = json.loads(args.context)
        result = invoke(args.hash, ctx)
        print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)

    elif args.cmd == "arbitrate":
        candidates = json.loads(args.candidates_json)
        result = arbitrate(candidates)
        print(json.dumps(result, indent=2))

    elif args.cmd == "resolve":
        blob = resolve(args.hash)
        print(json.dumps(blob, indent=2))


if __name__ == "__main__":
    _cli()
