#!/usr/bin/env python3
"""
bootstrap.py — D-JIT Logic Fabric Bootstrap
f_0 closure: PUT Discovery, Planning, and Telemetry-Reader blobs.
Triple-Pass Review, Council Approval, manifest promotion to v1.0.0.

After this runs:
  - linker.py routes through all three self-hosted blobs
  - arbitrate() auto-enriches from live telemetry (feedback loop closed)
  - Manifest at v1.0.0 — f_0 is defined
"""

import json
import sys

import promote
import seed

# ---------------------------------------------------------------------------
# Discovery blob (Layer 2 — The Librarian)
# ---------------------------------------------------------------------------

DISCOVERY_PAYLOAD = """\
import json
from pathlib import Path

vault_dir = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context["hash"]
blob_path = vault_dir / target_hash

if not blob_path.exists():
    raise FileNotFoundError(f"Discovery L1: {target_hash} not found in vault")

log(f"discovery: resolved {target_hash[:8]}... from L1")
result = json.loads(blob_path.read_text())
"""

# ---------------------------------------------------------------------------
# Planning blob (Layer 3 — The Broker)
# Fitness: f(Link) = SuccessRate × Integrity / Latency × ComputeCost
# ---------------------------------------------------------------------------

PLANNING_PAYLOAD = """\
candidates = context.get("candidates", [])

if not candidates:
    result = None
else:
    def _score(c):
        sr = float(c.get("success_rate", 1.0))
        integrity = float(c.get("integrity", 1.0))
        latency = max(float(c.get("latency_ms", 1.0)), 0.001)
        cost = max(float(c.get("cost", 1.0)), 0.001)
        return (sr * integrity) / (latency * cost)

    ranked = sorted(candidates, key=_score, reverse=True)
    best = ranked[0]
    best_score = _score(best)

    log(f"planning: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

    result = {
        "selected": best["hash"],
        "score": best_score,
        "rationale": (
            f"f(Link)={best_score:.4f} vs runner-up {_score(ranked[1]):.4f}"
            if len(ranked) > 1
            else "sole candidate"
        ),
        "ranked": [{"hash": c["hash"], "score": _score(c)} for c in ranked],
    }
"""

# ---------------------------------------------------------------------------
# Telemetry-Reader blob (feedback layer)
# Scans vault, aggregates per-blob fitness signals from telemetry artifacts.
# Closes the loop: measured performance → Planning arbitration inputs.
# ---------------------------------------------------------------------------

TELEMETRY_READER_PAYLOAD = """\
import json
from pathlib import Path

vault_dir = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context.get("hash")  # optional: filter to one blob

stats = {}

for blob_path in vault_dir.iterdir():
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
    if target_hash and invoked != target_hash:
        continue
    s = stats.setdefault(invoked, {"total": 0, "success": 0, "latency_sum": 0.0, "memory_sum": 0.0})
    s["total"] += 1
    if record.get("error") is None:
        s["success"] += 1
    s["latency_sum"] += record.get("latency_ms", 0.0)
    s["memory_sum"] += record.get("memory_kb", 0.0)

result = {
    h: {
        "success_rate": s["success"] / s["total"],
        "avg_latency_ms": s["latency_sum"] / s["total"],
        "avg_memory_kb": s["memory_sum"] / s["total"],
        "invocation_count": s["total"],
    }
    for h, s in stats.items()
    if s["total"] > 0
}

log(f"telemetry-reader: {len(result)} blob(s) with recorded history")
"""


def run(reviewer: str = "bootstrap") -> dict:
    """
    Full f_0 bootstrap:
      1. PUT Discovery, Planning, Telemetry-Reader blobs
      2. Triple-Pass Review each
      3. Council Approval + promote all three
      4. Manifest → v1.0.0
    """
    print("── Bootstrap: f_0 Closure")

    blobs = [
        ("discovery",        DISCOVERY_PAYLOAD),
        ("planning",         PLANNING_PAYLOAD),
        ("telemetry-reader", TELEMETRY_READER_PAYLOAD),
    ]

    hashes: dict[str, str] = {}
    for label, payload in blobs:
        h = seed.put("logic/python", payload)
        hashes[label] = h
        print(f"  PUT {label:<18} {h[:16]}...")

    print()
    for label, h in hashes.items():
        try:
            promote.triple_pass_review(h)
            print(f"  PASS  {label}")
        except promote.ReviewError as e:
            print(f"  FAIL  {label} [{e.pass_name}] {e.detail}")
            sys.exit(1)

    print()
    # Single approval covers all three
    approval_hash = promote.issue_council_approval(
        list(hashes.values()), reviewer=reviewer
    )
    print(f"  Council approval  {approval_hash[:16]}...")

    print()
    manifest_hash = None
    for label, h in hashes.items():
        # Each promotion needs an approval that covers that blob
        blob_approval = promote.issue_council_approval([h], reviewer=reviewer)
        manifest_hash = promote.promote(
            label=label,
            blob_hashes=[h],
            council_approval_hash=blob_approval,
            version="1.0.0",
        )
        print(f"  promoted {label:<18} manifest.hash={manifest_hash[:16]}...")

    print(f"\n  f_0 defined. Manifest v1.0.0  hash={manifest_hash[:16]}...")
    print("  Feedback loop: telemetry → SuccessRate → Planning arbitration ✓")

    return {**hashes, "manifest_hash": manifest_hash}


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
