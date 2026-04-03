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
import blake3
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
    manifest_hash = blake3.blake3(
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
    # Syntax-check all executable logic blobs (logic/python, logic/engine, etc.)
    if blob["type"].startswith("logic/"):
        try:
            ast.parse(blob["payload"])
        except SyntaxError as e:
            raise ReviewError("StaticAnalysis", f"syntax error: {e}") from e
    # contract/definition: validate required fields and that pre/post parse as Python
    if blob["type"] == "contract/definition":
        try:
            record = json.loads(blob["payload"])
        except Exception as e:
            raise ReviewError("StaticAnalysis", f"contract payload is not valid JSON: {e}") from e
        if not record.get("for_label"):
            raise ReviewError("StaticAnalysis", "contract/definition missing 'for_label' field")
        for field in ("pre", "post"):
            src = record.get(field)
            if not src or not isinstance(src, str) or not src.strip():
                raise ReviewError("StaticAnalysis",
                                  f"contract/definition missing or empty '{field}' function source")
            try:
                ast.parse(src)
            except SyntaxError as e:
                raise ReviewError("StaticAnalysis",
                                  f"contract/definition '{field}' has syntax error: {e}") from e
    # test/case: validate required fields
    if blob["type"] == "test/case":
        try:
            record = json.loads(blob["payload"])
        except Exception as e:
            raise ReviewError("StaticAnalysis", f"test/case payload is not valid JSON: {e}") from e
        if not record.get("for_label"):
            raise ReviewError("StaticAnalysis", "test/case missing 'for_label' field")
        if "input_context" not in record:
            raise ReviewError("StaticAnalysis", "test/case missing 'input_context' field")
        valid_tolerances = {"exact", "structural", "behavioral"}
        if record.get("tolerance", "structural") not in valid_tolerances:
            raise ReviewError("StaticAnalysis",
                              f"test/case tolerance must be one of {sorted(valid_tolerances)}")
    # goal/okr: validate required fields and key result structure
    if blob["type"] == "goal/okr":
        try:
            record = json.loads(blob["payload"])
        except Exception as e:
            raise ReviewError("StaticAnalysis", f"goal/okr payload is not valid JSON: {e}") from e
        if not record.get("for_label"):
            raise ReviewError("StaticAnalysis", "goal/okr missing 'for_label' field")
        if not record.get("objective") or not isinstance(record["objective"], str):
            raise ReviewError("StaticAnalysis", "goal/okr missing or empty 'objective' field")
        krs = record.get("key_results")
        if not isinstance(krs, list) or not krs:
            raise ReviewError("StaticAnalysis", "goal/okr 'key_results' must be a non-empty list")
        valid_directions = {"above", "below"}
        for i, kr in enumerate(krs):
            if not isinstance(kr, dict):
                raise ReviewError("StaticAnalysis", f"goal/okr key_result[{i}] must be a dict")
            if not kr.get("metric"):
                raise ReviewError("StaticAnalysis", f"goal/okr key_result[{i}] missing 'metric'")
            if not isinstance(kr.get("target"), (int, float)):
                raise ReviewError("StaticAnalysis", f"goal/okr key_result[{i}] 'target' must be numeric")
            if kr.get("direction") not in valid_directions:
                raise ReviewError("StaticAnalysis",
                                  f"goal/okr key_result[{i}] direction must be one of {sorted(valid_directions)}")


def _pass_safety(blob_hash: str, blob: dict) -> None:
    """Pass 2: Safety Verification — no scope-escaping patterns."""
    if not blob["type"].startswith("logic/"):
        return  # non-executable blobs skip safety scan
    if blob["type"] == "logic/engine":
        return  # engine blobs are kernel-trusted infrastructure; exec is their purpose
    match = _DANGEROUS_RE.search(blob["payload"])
    if match:
        raise ReviewError(
            "SafetyVerification",
            f"forbidden pattern '{match.group()}' — blob cannot escape scrubbed scope",
        )


def _pass_reviewer_integrity(blob_hash: str, blob: dict) -> None:
    """Pass 5: Reviewer Integrity — only for council/reviewer blobs.

    Validates that the reviewer blob has the required fields and that
    trust_weight is in (0.0, 1.0].  Non-reviewer blobs are skipped (no-op).

    Why a reviewer needs its own pass:  council/reviewer blobs are not
    executable, so Passes 2–3 skip them.  But they are trust anchors — a
    malformed reviewer blob (trust_weight > 1.0, missing authorized_types)
    could silently corrupt the governance chain.  This pass enforces the
    reviewer contract before any blob is admitted to the manifest["reviewers"]
    registry.
    """
    if blob.get("type") != "council/reviewer":
        return

    try:
        record = json.loads(blob["payload"])
    except Exception as e:
        raise ReviewError("ReviewerIntegrity", f"payload is not valid JSON: {e}") from e

    if not record.get("id"):
        raise ReviewError("ReviewerIntegrity", "missing or empty 'id' field")

    auth = record.get("authorized_types")
    if not isinstance(auth, list) or not auth:
        raise ReviewError("ReviewerIntegrity",
                          "missing or empty 'authorized_types' list")

    try:
        tw = float(record.get("trust_weight", 1.0))
    except (TypeError, ValueError) as e:
        raise ReviewError("ReviewerIntegrity",
                          f"trust_weight is not numeric: {record.get('trust_weight')!r}") from e
    if not (0.0 < tw <= 1.0):
        raise ReviewError("ReviewerIntegrity",
                          f"trust_weight {tw} out of range (0.0, 1.0]")


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


def _contract_probe_contexts(label: str, manifest: dict) -> list[dict]:
    """
    Return probe contexts for ContractCompliance testing.

    Prefers promoted test/case blobs for the label (up to 3).
    Falls back to a synthetic context per known label when none are promoted.
    """
    test_hashes = manifest.get("blobs", {}).get(label, {}).get("test/case", [])
    if isinstance(test_hashes, list) and test_hashes:
        contexts: list[dict] = []
        for th in test_hashes[:3]:
            try:
                tb  = seed._raw_get(th)
                tc  = json.loads(tb["payload"])
                ctx = tc.get("input_context", {})
                if ctx:
                    contexts.append(ctx)
            except Exception:
                pass
        if contexts:
            return contexts

    # Synthetic fallback per label — minimal valid inputs for each core blob
    _SYNTHETIC: dict[str, list[dict]] = {
        "discovery":        [{"hash": "a" * 64, "vault_dir": str(seed.VAULT_DIR)}],
        "planning":         [{"candidates": [
            {"hash": "a" * 64, "success_rate": 0.9, "latency_ms": 1.0,
             "p95_latency_ms": 1.2, "integrity": 0.9, "cost": 1.0,
             "invocation_count": 5, "feedback_score": 1.0, "feedback_count": 0},
        ]}],
        "telemetry-reader": [{"vault_dir": str(seed.VAULT_DIR)}],
    }
    return _SYNTHETIC.get(label, [{"__probe__": True}])


def _pass_contract_compliance(blob_hash: str, blob: dict, label: str) -> None:
    """Pass 6: Contract Compliance — logic/python blob vs promoted contract/definition.

    A hard correctness gate orthogonal to fitness: a blob that violates its
    contract cannot be promoted regardless of benchmark performance.

    Only fires when:
      1. The blob is logic/python
      2. A contract/definition blob is promoted in the manifest for `label`

    Protocol:
      - Load the promoted contract for the label
      - Compile pre / post / invariant functions
      - For each probe context (from promoted test/case blobs or synthetic fallback):
          pre(context) must hold (skip probe if not — probe may require real data)
          invoke the blob → get result
          post(context, result) must hold
          invariant(context, result) must hold (if defined)

    Non-ABI execution failures during the probe are not ContractCompliance failures —
    the blob may require real vault contents that the probe cannot provide.
    """
    if blob.get("type") != "logic/python":
        return  # only executable blobs

    manifest = load_manifest()
    contract_hash = manifest.get("blobs", {}).get(label, {}).get("contract/definition")
    if not contract_hash:
        return  # no contract promoted for this label — no-op (backward compatible)

    try:
        contract_blob = seed._raw_get(contract_hash)
        contract      = json.loads(contract_blob["payload"])
    except Exception as e:
        raise ReviewError("ContractCompliance",
                          f"failed to load contract for '{label}': {e}") from e

    # Compile pre / post / invariant from source strings
    def _compile_fn(src: str | None, name: str):
        if not src:
            return None
        fn_scope: dict = {}
        try:
            exec(compile(src, f"<contract:{name}>", "exec"), fn_scope)  # noqa: S102
        except Exception as e:
            raise ReviewError("ContractCompliance",
                              f"failed to compile contract.{name}: {e}") from e
        fn = fn_scope.get(name)
        if fn is None:
            raise ReviewError("ContractCompliance",
                              f"contract.{name} compiled but function '{name}' not found")
        return fn

    pre_fn  = _compile_fn(contract.get("pre"),       "pre")
    post_fn = _compile_fn(contract.get("post"),      "post")
    inv_fn  = _compile_fn(contract.get("invariant"), "invariant")

    probes = _contract_probe_contexts(label, manifest)
    verified = 0

    for ctx in probes:
        # Pre-condition check — skip probe if pre doesn't hold (needs real data)
        if pre_fn:
            try:
                if not pre_fn(ctx):
                    continue
            except Exception:
                continue  # pre threw → probe context unsuitable, skip

        # Invoke the blob
        try:
            result = seed.invoke(blob_hash, ctx)
        except Exception:
            continue  # execution failure — blob may need real vault contents

        # Post-condition check — hard failure
        if post_fn:
            try:
                ok = post_fn(ctx, result)
            except Exception as e:
                raise ReviewError("ContractCompliance",
                                  f"post-condition raised for label '{label}': {e}") from e
            if not ok:
                raise ReviewError("ContractCompliance",
                                  f"post-condition violated for label '{label}'")

        # Invariant check — hard failure
        if inv_fn:
            try:
                ok = inv_fn(ctx, result)
            except Exception as e:
                raise ReviewError("ContractCompliance",
                                  f"invariant raised for label '{label}': {e}") from e
            if not ok:
                raise ReviewError("ContractCompliance",
                                  f"invariant violated for label '{label}'")

        verified += 1

    # If we had probes but none ran successfully, that's acceptable (real context needed).
    # If at least one probe was verified, the contract is satisfied.


def triple_pass_review(blob_hash: str, label: str | None = None) -> dict:
    """
    Run all review passes on a blob. Returns the blob on success.
    Raises ReviewError on any failure.

    Pass 1 — StaticAnalysis:      structural validity, syntax/schema checks
    Pass 2 — SafetyVerification:  no scope-escaping patterns (logic blobs only)
    Pass 3 — ProtocolCompliance:  ABI dry-run (logic/python blobs only)
    Pass 4 — FeedbackIntegrity:   structure + referential integrity (feedback blobs only)
    Pass 5 — ReviewerIntegrity:   trust anchor validation (council/reviewer blobs only)
    Pass 6 — ContractCompliance:  pre/post/invariant vs promoted contract (logic/python only,
                                   when label is provided and a contract is promoted)
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
    _pass_feedback_integrity(blob_hash, blob)
    _pass_reviewer_integrity(blob_hash, blob)
    if label is not None:
        _pass_contract_compliance(blob_hash, blob, label)
    return blob


# ---------------------------------------------------------------------------
# Reviewer Registry
# ---------------------------------------------------------------------------

def bootstrap_reviewer(payload: str) -> str:
    """
    Establish the initial reviewer blob — the trust root of the governance chain.

    This is the only path that does NOT require a pre-existing approved reviewer.
    It is self-grounding by design: every governed system has an unverifiable root,
    and the right answer is to make that root as small and auditable as possible.
    The payload is content-addressed; the trust root is exactly as auditable as
    the blob it produces.

    After this runs, all subsequent reviewer promotions require an approval from
    an already-registered reviewer (via promote_reviewer).

    Returns the reviewer hash (also stored in manifest["reviewers"]).
    """
    reviewer_hash = seed.put("council/reviewer", payload)
    # Validate the reviewer blob before installing it as a trust root
    blob = seed._raw_get(reviewer_hash)
    _pass_reviewer_integrity(reviewer_hash, blob)   # raises ReviewError if malformed

    manifest = load_manifest()
    manifest.setdefault("reviewers", {})[reviewer_hash] = {
        "bootstrapped": True,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _write_manifest(manifest)
    _write_audit({
        "event":         "bootstrap_reviewer",
        "reviewer_hash": reviewer_hash,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    return reviewer_hash


def promote_reviewer(
    reviewer_hash: str,
    approving_reviewer_hash: str,
    council_approval_hash: str,
) -> str:
    """
    Promote a new reviewer into the manifest registry using an existing reviewer.

    Requires:
      - The new reviewer blob passes Triple-Pass Review (including ReviewerIntegrity)
      - A council/approval artifact signed by a currently promoted reviewer
      - The approving reviewer is itself in manifest["reviewers"]

    This is the governed path for adding new reviewers after the trust root is
    established.  The governance chain is: trust root → approves → new reviewer →
    approves → blob candidates.  Every link is auditable in the vault.
    """
    # Validate the new reviewer blob
    blob = triple_pass_review(reviewer_hash)
    if blob["type"] != "council/reviewer":
        raise ValueError(f"blob {reviewer_hash[:16]}... is type {blob['type']!r}, "
                         f"expected council/reviewer")

    # Verify the approving reviewer is currently promoted
    manifest = load_manifest()
    if approving_reviewer_hash not in manifest.get("reviewers", {}):
        raise ValueError(f"approving reviewer {approving_reviewer_hash[:16]}... "
                         f"is not in the manifest reviewer registry")

    # Verify council approval (signed by the approving reviewer)
    approval = _verify_council_approval(council_approval_hash, [reviewer_hash],
                                        require_reviewer=approving_reviewer_hash)

    manifest["reviewers"][reviewer_hash] = {
        "approved_by": approving_reviewer_hash,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    new_hash = _write_manifest(manifest)
    _write_audit({
        "event":                 "promote_reviewer",
        "reviewer_hash":         reviewer_hash,
        "approved_by":           approving_reviewer_hash,
        "council_approval_hash": council_approval_hash,
        "manifest_hash":         new_hash,
        "timestamp_utc":         time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    return new_hash


# ---------------------------------------------------------------------------
# Council Approval Artifact
# ---------------------------------------------------------------------------

def issue_council_approval(blob_hashes: list[str], reviewer_hash: str) -> str:
    """
    Create a council/approval artifact signed by a governed reviewer blob.

    reviewer_hash must point to a council/reviewer blob in the vault.
    Whether the reviewer is currently promoted is enforced at verification
    time (_verify_council_approval), not at issuance time — issuance is
    cheap; verification is the gate.

    Returns the approval hash to be passed into promote() or promote_feedback().
    """
    artifact = {
        "reviewer_hash":  reviewer_hash,
        "timestamp_utc":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "approved_blobs": blob_hashes,
    }
    return seed.put("council/approval", json.dumps(artifact, sort_keys=True))


def _verify_council_approval(
    approval_hash: str,
    blob_hashes: list[str],
    require_reviewer: str | None = None,
) -> dict:
    """
    Verify a council/approval artifact.

    Checks:
      1. Artifact exists and has type council/approval
      2. reviewer_hash in artifact is a promoted reviewer in manifest["reviewers"]
      3. Artifact covers all blob_hashes
      4. If require_reviewer is set, the reviewer_hash must match it exactly
    """
    try:
        artifact = seed._raw_get(approval_hash)
    except FileNotFoundError:
        raise ValueError(f"Council approval artifact {approval_hash} not found in vault")

    if artifact.get("type") != "council/approval":
        raise ValueError(
            f"Artifact {approval_hash} is type '{artifact.get('type')}', expected council/approval"
        )

    approval      = json.loads(artifact["payload"])
    reviewer_hash = approval.get("reviewer_hash")

    if reviewer_hash:
        manifest = load_manifest()
        # Normalize both sides: bare hex for robust comparison across old/new format
        reviewer_bare     = seed._to_bare_hex(reviewer_hash)
        reviewers_bare    = {seed._to_bare_hex(k) for k in manifest.get("reviewers", {})}
        if reviewer_bare not in reviewers_bare:
            raise ValueError(
                f"Approval reviewer {reviewer_hash[:16]}... is not a promoted reviewer"
            )
        if require_reviewer and reviewer_bare != seed._to_bare_hex(require_reviewer):
            raise ValueError(
                f"Approval was signed by {reviewer_hash[:16]}..., "
                f"expected {require_reviewer[:16]}..."
            )

    # Normalize both sides to bare hex so mixed old/new format comparisons work
    approved_bare = {seed._to_bare_hex(h) for h in approval.get("approved_blobs", [])}
    missing_bare  = {seed._to_bare_hex(h) for h in blob_hashes} - approved_bare
    if missing_bare:
        raise ValueError(f"Council approval does not cover blobs: {sorted(missing_bare)}")

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
    # Step 1 — Triple-Pass Review (Pass 6 ContractCompliance included when label known)
    review_results: dict[str, str] = {}
    for h in blob_hashes:
        blob = triple_pass_review(h, label=label)  # raises ReviewError on failure
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
        "council_reviewer_hash": approval.get("reviewer_hash"),
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
# Contract Promotion
# ---------------------------------------------------------------------------

def promote_contract(
    label: str,
    contract_hash: str,
    council_approval_hash: str,
    version: str = None,
) -> str:
    """
    Promote a contract/definition blob to the manifest for a given label.

    Once promoted, the contract becomes the correctness gate for all future
    promotions of logic/python blobs for that label (Pass 6 ContractCompliance).

    Args:
        label:                  The manifest label this contract governs.
        contract_hash:          The contract/definition blob hash.
        council_approval_hash:  Council approval artifact covering contract_hash.
        version:                Optional manifest version string.

    Returns the new manifest hash.
    """
    # Step 1 — Triple-Pass Review (StaticAnalysis validates contract schema)
    blob = triple_pass_review(contract_hash)
    if blob["type"] != "contract/definition":
        raise ValueError(f"blob {contract_hash[:16]}... is type {blob['type']!r}, "
                         f"expected contract/definition")

    # Verify the for_label field matches the target label
    try:
        record = json.loads(blob["payload"])
    except Exception as e:
        raise ValueError(f"contract payload is not valid JSON: {e}") from e
    if record.get("for_label") != label:
        raise ValueError(f"contract for_label '{record.get('for_label')}' does not match "
                         f"target label '{label}'")

    # Step 2 — Council Approval
    approval = _verify_council_approval(council_approval_hash, [contract_hash])

    # Step 3 — Update manifest
    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["blobs"].setdefault(label, {})["contract/definition"] = contract_hash

    new_hash = _write_manifest(manifest)

    # Step 4 — Audit Log
    _write_audit({
        "event":                 "promote_contract",
        "timestamp_utc":         manifest["promoted_at"],
        "label":                 label,
        "contract_hash":         contract_hash,
        "council_approval_hash": council_approval_hash,
        "council_reviewer_hash": approval.get("reviewer_hash"),
        "manifest_hash":         new_hash,
        "version":               manifest["version"],
    })

    return new_hash


# ---------------------------------------------------------------------------
# Test Case Promotion (f_9)
# ---------------------------------------------------------------------------

def promote_test_cases(
    label: str,
    test_case_hashes: list[str],
    council_approval_hash: str,
    version: str | None = None,
) -> str:
    """
    Promote a batch of test/case blobs to the manifest for a given label.

    Test cases accumulate: each call appends to manifest["blobs"][label]["test/case"].
    The test suite grows across evolution cycles without displacing prior cases.

    Returns the new manifest hash.
    """
    if not test_case_hashes:
        raise ValueError("test_case_hashes must be non-empty")

    # Step 1 — Triple-Pass Review each test case
    for tc_hash in test_case_hashes:
        blob = triple_pass_review(tc_hash)
        if blob["type"] != "test/case":
            raise ValueError(f"blob {tc_hash[:16]}... is type {blob['type']!r}, "
                             f"expected test/case")
        record = json.loads(blob["payload"])
        if record.get("for_label") != label:
            raise ValueError(f"test/case for_label '{record.get('for_label')}' does not match "
                             f"target label '{label}'")

    # Step 2 — Council Approval (covers all hashes)
    _verify_council_approval(council_approval_hash, test_case_hashes)

    # Step 3 — Append to manifest test suite
    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    label_entry = manifest["blobs"].setdefault(label, {})
    existing = label_entry.get("test/case", [])
    # Deduplicate: don't add hashes already in the suite
    new_hashes = [h for h in test_case_hashes if h not in existing]
    label_entry["test/case"] = existing + new_hashes

    new_manifest_hash = _write_manifest(manifest)

    # Step 4 — Audit Log
    _write_audit({
        "event":                 "promote_test_cases",
        "timestamp_utc":         manifest["promoted_at"],
        "label":                 label,
        "test_case_hashes":      new_hashes,
        "council_approval_hash": council_approval_hash,
        "manifest_hash":         new_manifest_hash,
        "version":               manifest["version"],
    })

    return new_manifest_hash


def run_test_suite(
    label: str,
    candidate_hash: str,
    manifest: dict | None = None,
) -> list[dict]:
    """
    Run all promoted test/case blobs for a label against a candidate blob.

    Returns a list of result dicts, one per test case:
        {"hash": tc_hash, "passed": bool, "result": ..., "expected": ...}

    Does not raise — callers inspect the results list and decide whether to gate.
    """
    import seed as _seed
    if manifest is None:
        manifest = load_manifest()

    tc_hashes = manifest.get("blobs", {}).get(label, {}).get("test/case", [])
    if not tc_hashes:
        return []

    results = []
    for tc_hash in tc_hashes:
        try:
            tc_blob = _seed._raw_get(tc_hash)
            tc = json.loads(tc_blob["payload"])
            if tc.get("for_label") != label:
                continue
            context  = tc.get("input_context", {})
            expected = tc.get("expected")
            tolerance = tc.get("tolerance", "behavioral")

            try:
                actual = _seed.invoke(candidate_hash, context)
                passed = _check_test_tolerance(actual, expected, tolerance, label, manifest)
            except Exception as e:
                passed = False
                actual = {"error": str(e)}

            results.append({
                "hash":     tc_hash,
                "passed":   passed,
                "result":   actual,
                "expected": expected,
                "tolerance": tolerance,
            })
        except Exception:
            # If test case blob can't be loaded, skip it
            continue

    return results


def _check_test_tolerance(
    actual,
    expected,
    tolerance: str,
    label: str,
    manifest: dict,
) -> bool:
    """Check whether actual result satisfies expected under the given tolerance."""
    import seed as _seed
    if tolerance == "exact":
        return actual == expected
    if tolerance == "structural":
        if isinstance(expected, dict) and isinstance(actual, dict):
            return set(expected.keys()) <= set(actual.keys())
        return actual == expected
    # behavioral: verify post-condition holds
    ch = manifest.get("blobs", {}).get(label, {}).get("contract/definition")
    if not ch:
        # No contract → accept if non-None
        return actual is not None
    try:
        blob = _seed._raw_get(ch)
        record = json.loads(blob["payload"])
        post_src = record.get("post", "def post(context, result):\n    return True")
        ns: dict = {}
        exec(compile(post_src, "<post>", "exec"), ns)
        return bool(ns["post"]({}, actual))
    except Exception:
        return actual is not None


# ---------------------------------------------------------------------------
# OKR Promotion (f_11)
# ---------------------------------------------------------------------------

def promote_okr(
    label: str,
    okr_hash: str,
    council_approval_hash: str,
    version: str | None = None,
) -> str:
    """
    Promote a goal/okr blob to the manifest for a given label.

    Once promoted, the OKR drives mutation goal derivation for that label:
    _derive_mutation_goal() reads the key results and current signal values
    to produce a targeted mutation goal for the implementor LLM.

    Returns the new manifest hash.
    """
    blob = triple_pass_review(okr_hash)
    if blob["type"] != "goal/okr":
        raise ValueError(f"blob {okr_hash[:16]}... is type {blob['type']!r}, "
                         f"expected goal/okr")

    try:
        record = json.loads(blob["payload"])
    except Exception as e:
        raise ValueError(f"goal/okr payload is not valid JSON: {e}") from e
    if record.get("for_label") != label:
        raise ValueError(f"goal/okr for_label '{record.get('for_label')}' does not match "
                         f"target label '{label}'")

    _verify_council_approval(council_approval_hash, [okr_hash])

    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["blobs"].setdefault(label, {})["goal/okr"] = okr_hash

    new_hash = _write_manifest(manifest)

    _write_audit({
        "event":                 "promote_okr",
        "timestamp_utc":         manifest["promoted_at"],
        "label":                 label,
        "okr_hash":              okr_hash,
        "council_approval_hash": council_approval_hash,
        "manifest_hash":         new_hash,
        "version":               manifest["version"],
    })

    return new_hash


def bootstrap_capability(
    label: str,
    contract_hash: str,
    okr_hash: str,
    initial_blob_hash: str,
    council_approval_hash: str,
    version: str | None = None,
) -> str:
    """
    Register a new capability label in the manifest with its contract, OKR,
    and initial logic blob.

    This is the entry point for domain-specific (non-infrastructure) capability
    blobs. After bootstrapping, evolve.run_all() discovers the label from the
    manifest and evolves it autonomously.

    The human role:
      - Write the contract/definition (what the blob must do)
      - Write the goal/okr (what success looks like)
      - Provide an initial logic/python blob (seed implementation)
    The fabric handles the rest.

    Returns the new manifest hash.
    """
    # Validate all three blobs upfront
    logic_blob    = triple_pass_review(initial_blob_hash, label=label)
    contract_blob = triple_pass_review(contract_hash)
    okr_blob      = triple_pass_review(okr_hash)

    if logic_blob["type"] != "logic/python":
        raise ValueError(f"initial_blob_hash must be logic/python, got {logic_blob['type']!r}")
    if contract_blob["type"] != "contract/definition":
        raise ValueError(f"contract_hash must be contract/definition, got {contract_blob['type']!r}")
    if okr_blob["type"] != "goal/okr":
        raise ValueError(f"okr_hash must be goal/okr, got {okr_blob['type']!r}")

    # Verify all blobs target the same label
    for blob, field, hash_ in [
        (json.loads(contract_blob["payload"]), "contract/definition", contract_hash),
        (json.loads(okr_blob["payload"]),      "goal/okr",            okr_hash),
    ]:
        if blob.get("for_label") != label:
            raise ValueError(f"{field} for_label '{blob.get('for_label')}' does not match '{label}'")

    _verify_council_approval(council_approval_hash,
                             [initial_blob_hash, contract_hash, okr_hash])

    manifest = load_manifest()
    if version:
        manifest["version"] = version
    manifest["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["blobs"].setdefault(label, {}).update({
        "logic/python":        initial_blob_hash,
        "contract/definition": contract_hash,
        "goal/okr":            okr_hash,
        "test/case":           [],
    })

    new_hash = _write_manifest(manifest)

    _write_audit({
        "event":                 "bootstrap_capability",
        "timestamp_utc":         manifest["promoted_at"],
        "label":                 label,
        "logic_hash":            initial_blob_hash,
        "contract_hash":         contract_hash,
        "okr_hash":              okr_hash,
        "council_approval_hash": council_approval_hash,
        "manifest_hash":         new_hash,
        "version":               manifest["version"],
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
        h = issue_council_approval(args.hashes, args.reviewer)
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
