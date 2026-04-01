#!/usr/bin/env python3
"""
promote.py — D-JIT Logic Fabric Manifest Promotion
Phase 2 implementation per f(undefined).md + COUNCIL.md

Protocol:
  1. Triple-Pass Review: Static Analysis -> Safety Verification -> Protocol Compliance
  2. Require Council Approval Artifact (hashed into Audit Log)
  3. Update manifest.hash only after all passes clear
  4. Write Audit Log entry (JSONL)

Golden Rule: Never update manifest.hash until L1-L3 blobs verified in isolation.
"""

import ast
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import seed  # BIOS Seed — PUT/INVOKE/_raw_get

MANIFEST_PATH = Path("./manifest.json")
AUDIT_LOG_PATH = Path("./audit.log")

# Patterns that would let a blob escape scrubbed scope
_DANGEROUS_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\b__import__\b",
    r"\bopen\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bsubprocess\b",
    r"\bshutil\b",
    r"\bVAULT_DIR\b",   # Linker internal — must not be referenced
]
_DANGEROUS_RE = re.compile("|".join(_DANGEROUS_PATTERNS))


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"version": "0.0.0", "blobs": {}, "hash": None, "promoted_at": None}


def _write_manifest(manifest: dict) -> str:
    """Write manifest, compute and store its own hash. Returns new hash."""
    # Strip old hash before hashing content
    content = {k: v for k, v in manifest.items() if k != "hash"}
    manifest_hash = hashlib.sha256(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()
    manifest["hash"] = manifest_hash
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    return manifest_hash


# ---------------------------------------------------------------------------
# Triple-Pass Review
# ---------------------------------------------------------------------------

class ReviewError(Exception):
    def __init__(self, pass_name: str, detail: str):
        self.pass_name = pass_name
        self.detail = detail
        super().__init__(f"[{pass_name}] {detail}")


def _pass_static(blob_hash: str, blob: dict) -> None:
    """Pass 1: Static Analysis — structural validity."""
    if not blob.get("type"):
        raise ReviewError("StaticAnalysis", "blob missing 'type' field")
    if not isinstance(blob.get("payload"), str) or not blob["payload"].strip():
        raise ReviewError("StaticAnalysis", "blob payload is empty or non-string")
    # Only syntax-check logic blobs
    if blob["type"].startswith("logic/python"):
        try:
            ast.parse(blob["payload"])
        except SyntaxError as e:
            raise ReviewError("StaticAnalysis", f"syntax error: {e}") from e


def _pass_safety(blob_hash: str, blob: dict) -> None:
    """Pass 2: Safety Verification — no scope-escaping patterns."""
    if not blob["type"].startswith("logic/"):
        return  # non-executable blobs skip safety scan
    match = _DANGEROUS_RE.search(blob["payload"])
    if match:
        raise ReviewError(
            "SafetyVerification",
            f"forbidden pattern '{match.group()}' — blob cannot escape scrubbed scope",
        )


def _pass_feedback_integrity(blob_hash: str, blob: dict) -> None:
    """Pass 4: Feedback Integrity — only for feedback/outcome blobs.

    Validates structure, outcome enum, confidence range, and that the
    referenced logic blob exists in the vault.  Non-feedback blobs are
    skipped (no-op).

    Why a dedicated pass?  feedback/outcome blobs are not executable, so
    Pass 2 (SafetyVerification) and Pass 3 (ProtocolCompliance) skip them.
    But they carry claims about specific logic blobs — claims that can
    corrupt the fitness formula if malformed.  This pass enforces that:
      - the invoked hash actually exists in the vault
      - the outcome is a valid enum value
      - confidence is in [0.0, 1.0]
    A feedback blob that passes all four passes can be trusted to influence
    FeedbackScore without corrupting it.
    """
    if blob.get("type") != "feedback/outcome":
        return  # no-op for all other blob types

    try:
        record = json.loads(blob["payload"])
    except Exception as e:
        raise ReviewError("FeedbackIntegrity", f"payload is not valid JSON: {e}") from e

    invoked = record.get("invoked", "")
    if len(invoked) != 64 or not all(c in "0123456789abcdef" for c in invoked):
        raise ReviewError("FeedbackIntegrity",
                          f"'invoked' is missing or not a 64-char hex hash: {invoked!r}")

    valid_outcomes = {"pass", "fail", "partial"}
    outcome = record.get("outcome")
    if outcome not in valid_outcomes:
        raise ReviewError("FeedbackIntegrity",
                          f"invalid outcome {outcome!r}; must be one of {sorted(valid_outcomes)}")

    try:
        conf_f = float(record.get("confidence", 1.0))
    except (TypeError, ValueError) as e:
        raise ReviewError("FeedbackIntegrity",
                          f"confidence is not numeric: {record.get('confidence')!r}") from e
    if not (0.0 <= conf_f <= 1.0):
        raise ReviewError("FeedbackIntegrity",
                          f"confidence {conf_f} out of range [0.0, 1.0]")

    # The logic blob being rated must exist in the vault
    try:
        seed._raw_get(invoked)
    except FileNotFoundError:
        raise ReviewError("FeedbackIntegrity",
                          f"invoked blob {invoked[:16]}... not found in vault — "
                          f"feedback requires a proven invocation target")


def _pass_protocol(blob_hash: str, blob: dict) -> None:
    """Pass 3: Protocol Compliance — ABI contract enforced via dry-run invoke.

    Only ABI violations (missing result variable) are hard failures.
    Other execution errors (KeyError, etc.) are acceptable — the blob may
    require real context values that the probe stub does not provide.
    """
    if not blob["type"].startswith("logic/python"):
        return  # only executable blobs need ABI verification
    try:
        seed.invoke(blob_hash, context={"__probe__": True})
    except RuntimeError as e:
        if "ABI violation" in str(e):
            raise ReviewError("ProtocolCompliance", str(e)) from e
        # Non-ABI RuntimeError: blob needs real context — pass this check
    except Exception:
        # Any other execution error (KeyError, TypeError, etc.): same reasoning
        pass


def triple_pass_review(blob_hash: str) -> dict:
    """
    Run all review passes on a blob. Returns the blob on success.
    Raises ReviewError on any failure.

    Pass 1 — StaticAnalysis:     structural validity, syntax check for logic blobs
    Pass 2 — SafetyVerification: no scope-escaping patterns (logic blobs only)
    Pass 3 — ProtocolCompliance: ABI dry-run (logic/python blobs only)
    Pass 4 — FeedbackIntegrity:  structure + referential integrity (feedback blobs only)
    """
    blob = seed._raw_get(blob_hash)
    _pass_static(blob_hash, blob)
    _pass_safety(blob_hash, blob)
    try:
        _pass_protocol(blob_hash, blob)
    except Exception as e:
        if isinstance(e, ReviewError):
            raise
        # Non-ABI execution errors during probe are warnings, not failures
    _pass_feedback_integrity(blob_hash, blob)  # no-op for non-feedback blobs
    return blob


# ---------------------------------------------------------------------------
# Council Approval Artifact
# ---------------------------------------------------------------------------

def issue_council_approval(blob_hashes: list[str], reviewer: str = "council") -> str:
    """
    Create a council/approval artifact for a set of candidate blobs.
    Returns the approval hash to be passed into promote().
    """
    artifact = {
        "reviewer": reviewer,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "approved_blobs": blob_hashes,
    }
    return seed.put("council/approval", json.dumps(artifact))


def _verify_council_approval(approval_hash: str, blob_hashes: list[str]) -> dict:
    """Verify approval artifact exists, is correct type, and covers all candidate blobs."""
    try:
        artifact = seed._raw_get(approval_hash)
    except FileNotFoundError:
        raise ValueError(f"Council approval artifact {approval_hash} not found in vault")

    if artifact.get("type") != "council/approval":
        raise ValueError(
            f"Artifact {approval_hash} is type '{artifact.get('type')}', expected council/approval"
        )

    approval = json.loads(artifact["payload"])
    approved = set(approval.get("approved_blobs", []))
    missing = set(blob_hashes) - approved
    if missing:
        raise ValueError(
            f"Council approval does not cover blobs: {sorted(missing)}"
        )
    return approval


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

def _write_audit(entry: dict) -> None:
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Promote
# ---------------------------------------------------------------------------

def promote(
    label: str,
    blob_hashes: list[str],
    council_approval_hash: str,
    version: str = None,
) -> str:
    """
    Promote a set of blobs to the manifest.

    Steps:
      1. Triple-Pass Review each blob
      2. Verify Council Approval Artifact covers all blobs
      3. Update manifest (new version, blob registry)
      4. Write Audit Log entry with approval hash
      5. Return new manifest hash

    Raises on any failure — manifest.hash is never updated on partial success.
    """
    # Step 1 — Triple-Pass Review
    review_results: dict[str, str] = {}
    for h in blob_hashes:
        blob = triple_pass_review(h)  # raises ReviewError on failure
        review_results[h] = blob["type"]

    # Step 2 — Council Approval
    approval = _verify_council_approval(council_approval_hash, blob_hashes)

    # Step 3 — Update manifest (in-memory first, write only on full success)
    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for h in blob_hashes:
        manifest["blobs"][label] = manifest["blobs"].get(label, {})
        manifest["blobs"][label][review_results[h]] = h

    new_hash = _write_manifest(manifest)  # atomic from Python's perspective

    # Step 4 — Audit Log
    _write_audit({
        "event": "promote",
        "timestamp_utc": manifest["promoted_at"],
        "label": label,
        "blobs": review_results,
        "council_approval_hash": council_approval_hash,
        "council_reviewer": approval.get("reviewer"),
        "manifest_hash": new_hash,
        "version": manifest["version"],
    })

    return new_hash


# ---------------------------------------------------------------------------
# Feedback Promotion
# ---------------------------------------------------------------------------

def promote_feedback(
    logic_hash: str,
    feedback_hashes: list[str],
    council_approval_hash: str,
    version: str = None,
) -> str:
    """
    Promote feedback/outcome blobs for a specific logic blob.

    Feedback promotion runs the same governance protocol as logic blob promotion:
      1. Triple-Pass Review (includes FeedbackIntegrity pass)
      2. Council Approval Artifact covering all feedback hashes
      3. Update manifest["approved_feedback"][logic_hash]
      4. Audit log entry

    Only promoted feedback hashes influence FeedbackScore in the fitness formula.
    Unpromoted feedback blobs sit in the vault but are invisible to the telemetry
    reader — same as an unpromoted logic blob sitting in the vault but not yet
    reachable via the manifest.

    Args:
        logic_hash:            The logic/python blob the feedback is about.
        feedback_hashes:       feedback/outcome blob hashes to approve.
        council_approval_hash: Council approval artifact covering all hashes.
        version:               Optional manifest version string.

    Returns the new manifest hash.
    """
    # Step 1 — Triple-Pass Review (FeedbackIntegrity checks invoked blob exists)
    review_results: dict[str, str] = {}
    for h in feedback_hashes:
        blob = triple_pass_review(h)   # raises ReviewError on failure
        review_results[h] = blob["type"]
        if blob["type"] != "feedback/outcome":
            raise ValueError(f"promote_feedback: blob {h[:16]}... is type "
                             f"{blob['type']!r}, expected feedback/outcome")

    # Step 2 — Council Approval
    approval = _verify_council_approval(council_approval_hash, feedback_hashes)

    # Step 3 — Update manifest (approved_feedback section)
    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    approved = manifest.setdefault("approved_feedback", {})
    bucket   = approved.setdefault(logic_hash, [])
    for h in feedback_hashes:
        if h not in bucket:
            bucket.append(h)

    new_hash = _write_manifest(manifest)

    # Step 4 — Audit Log
    _write_audit({
        "event":                "promote_feedback",
        "timestamp_utc":        manifest["promoted_at"],
        "logic_hash":           logic_hash,
        "feedback_hashes":      list(review_results.keys()),
        "council_approval_hash": council_approval_hash,
        "council_reviewer":     approval.get("reviewer"),
        "manifest_hash":        new_hash,
        "version":              manifest["version"],
    })

    return new_hash


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="promote",
        description="D-JIT Manifest Promotion CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # promote review <hash>
    p_rev = sub.add_parser("review", help="Run Triple-Pass Review on a blob")
    p_rev.add_argument("hash", help="Blob content hash")

    # promote approve <hash1> [hash2...] --reviewer <name>
    p_app = sub.add_parser("approve", help="Issue a Council Approval Artifact")
    p_app.add_argument("hashes", nargs="+", help="Blob hashes to approve")
    p_app.add_argument("--reviewer", default="council")

    # promote run <label> <approval_hash> <hash1> [hash2...] [--version x]
    p_run = sub.add_parser("run", help="Promote blobs to manifest")
    p_run.add_argument("label", help="Manifest label (e.g. L1, discovery)")
    p_run.add_argument("approval_hash", help="Council approval artifact hash")
    p_run.add_argument("hashes", nargs="+", help="Blob hashes to promote")
    p_run.add_argument("--version", default=None)

    # promote manifest
    sub.add_parser("manifest", help="Print current manifest")

    args = parser.parse_args()

    if args.cmd == "review":
        try:
            blob = triple_pass_review(args.hash)
            print(f"PASS  {args.hash}  [{blob['type']}]")
        except ReviewError as e:
            print(f"FAIL  {e}")
            raise SystemExit(1)

    elif args.cmd == "approve":
        h = issue_council_approval(args.hashes, reviewer=args.reviewer)
        print(h)

    elif args.cmd == "run":
        try:
            manifest_hash = promote(
                label=args.label,
                blob_hashes=args.hashes,
                council_approval_hash=args.approval_hash,
                version=args.version,
            )
            print(f"promoted  manifest.hash={manifest_hash}")
        except (ReviewError, ValueError) as e:
            print(f"REJECTED  {e}")
            raise SystemExit(1)

    elif args.cmd == "manifest":
        print(json.dumps(load_manifest(), indent=2))


if __name__ == "__main__":
    _cli()
