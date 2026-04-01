#!/usr/bin/env python3
"""
tests/test_f6.py — f_6 council governance tests
Covers: _pass_reviewer_integrity, bootstrap_reviewer(), promote_reviewer(),
        issue_council_approval with reviewer_hash, _verify_council_approval
        manifest["reviewers"] chain, reviewer trust weighting in telemetry-reader v7,
        full f_6 evolution cycle, manifest v1.6.0.
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bootstrap
import evolve
import linker
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []

# Bootstrap result populated at __main__ time
_boot: dict = {}


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------

def test_bootstrap_reviewer_creates_trust_root() -> None:
    section("bootstrap_reviewer — manifest['reviewers'] populated as trust root")
    m = promote.load_manifest()
    bootstrap_hash = _boot.get("bootstrap_reviewer_hash", "")

    check("bootstrap_reviewer_hash returned from run()", len(bootstrap_hash) == 64)
    check("reviewer hash in manifest['reviewers']",
          bootstrap_hash in m.get("reviewers", {}))
    entry = m.get("reviewers", {}).get(bootstrap_hash, {})
    check("bootstrapped flag is True", entry.get("bootstrapped") is True)
    check("registered_at present", "registered_at" in entry)

    # Audit log must have a bootstrap_reviewer event
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    boot_events = [e for e in entries if e.get("event") == "bootstrap_reviewer"]
    check("bootstrap_reviewer event in audit log", len(boot_events) >= 1)
    last = boot_events[-1]
    check("reviewer_hash in audit entry", last.get("reviewer_hash") == bootstrap_hash)


def test_evolve_reviewer_promoted_by_bootstrap() -> None:
    section("promote_reviewer — evolve-engine reviewer promoted by bootstrap reviewer")
    m = promote.load_manifest()
    evolve_hash = _boot.get("evolve_reviewer_hash", "")
    bootstrap_hash = _boot.get("bootstrap_reviewer_hash", "")

    check("evolve_reviewer_hash returned from run()", len(evolve_hash) == 64)
    check("evolve reviewer in manifest['reviewers']",
          evolve_hash in m.get("reviewers", {}))
    entry = m.get("reviewers", {}).get(evolve_hash, {})
    check("approved_by == bootstrap_reviewer_hash",
          entry.get("approved_by") == bootstrap_hash)

    # Audit log must have a promote_reviewer event for the evolve reviewer
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    prom_events = [e for e in entries
                   if e.get("event") == "promote_reviewer"
                   and e.get("reviewer_hash") == evolve_hash]
    check("promote_reviewer event in audit log for evolve reviewer",
          len(prom_events) >= 1)


def test_reviewer_integrity_pass_valid() -> None:
    section("ReviewerIntegrity — valid council/reviewer blob passes all passes")
    payload = json.dumps({
        "id":               "test-reviewer",
        "authorized_types": ["logic/python"],
        "trust_weight":     0.7,
        "criteria":         "test",
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)
    try:
        blob = promote.triple_pass_review(rh)
        check("valid council/reviewer passes triple_pass_review",
              blob["type"] == "council/reviewer")
    except promote.ReviewError as e:
        check("valid council/reviewer passes triple_pass_review", False, str(e))


def test_reviewer_integrity_rejects_bad_trust_weight_above_one() -> None:
    section("ReviewerIntegrity — rejects trust_weight > 1.0")
    payload = json.dumps({
        "id":               "bad-reviewer",
        "authorized_types": ["logic/python"],
        "trust_weight":     1.5,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)
    try:
        promote.triple_pass_review(rh)
        check("rejects trust_weight 1.5", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects trust_weight 1.5",
              e.pass_name == "ReviewerIntegrity" and "trust_weight" in str(e).lower())


def test_reviewer_integrity_rejects_zero_trust_weight() -> None:
    section("ReviewerIntegrity — rejects trust_weight = 0.0 (not in (0, 1])")
    payload = json.dumps({
        "id":               "zero-reviewer",
        "authorized_types": ["logic/python"],
        "trust_weight":     0.0,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)
    try:
        promote.triple_pass_review(rh)
        check("rejects trust_weight 0.0", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects trust_weight 0.0",
              e.pass_name == "ReviewerIntegrity" and "trust_weight" in str(e).lower())


def test_reviewer_integrity_rejects_missing_id() -> None:
    section("ReviewerIntegrity — rejects reviewer with no id")
    payload = json.dumps({
        "authorized_types": ["logic/python"],
        "trust_weight":     0.9,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)
    try:
        promote.triple_pass_review(rh)
        check("rejects missing id", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects missing id",
              e.pass_name == "ReviewerIntegrity" and "id" in str(e).lower())


def test_reviewer_integrity_rejects_empty_authorized_types() -> None:
    section("ReviewerIntegrity — rejects reviewer with empty authorized_types")
    payload = json.dumps({
        "id":               "empty-types",
        "authorized_types": [],
        "trust_weight":     0.9,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)
    try:
        promote.triple_pass_review(rh)
        check("rejects empty authorized_types", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects empty authorized_types",
              e.pass_name == "ReviewerIntegrity" and "authorized_types" in str(e).lower())


def test_promote_reviewer_requires_existing_reviewer() -> None:
    section("promote_reviewer — cannot promote with an unregistered approver")
    payload = json.dumps({
        "id":               "orphan-reviewer",
        "authorized_types": ["logic/python"],
        "trust_weight":     0.5,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)

    # Issue approval from a hash that is NOT in manifest["reviewers"]
    fake_approver = "a" * 64
    approval = promote.issue_council_approval([rh], fake_approver)
    try:
        promote.promote_reviewer(rh, fake_approver, approval)
        check("rejects unknown approver", False, "expected ValueError")
    except ValueError as e:
        check("rejects unknown approver", "not in the manifest reviewer registry" in str(e))


def test_issue_council_approval_stores_reviewer_hash() -> None:
    section("issue_council_approval — approval artifact stores reviewer_hash field")
    evolve_hash = _boot.get("evolve_reviewer_hash", "")
    h_blob = seed.put("logic/python", "result = 'approval-test'")
    approval_hash = promote.issue_council_approval([h_blob], evolve_hash)

    blob = seed._raw_get(approval_hash)
    check("approval type is council/approval", blob["type"] == "council/approval")
    artifact = json.loads(blob["payload"])
    check("reviewer_hash field present", "reviewer_hash" in artifact)
    check("reviewer_hash equals evolve reviewer", artifact["reviewer_hash"] == evolve_hash)
    check("approved_blobs includes blob hash", h_blob in artifact.get("approved_blobs", []))


def test_verify_council_approval_rejects_unregistered_reviewer() -> None:
    section("_verify_council_approval — approval from unregistered reviewer is rejected")
    fake_reviewer = "b" * 64   # not in manifest["reviewers"]
    h_blob = seed.put("logic/python", "result = 'verify-test'")
    approval_hash = promote.issue_council_approval([h_blob], fake_reviewer)
    try:
        promote.promote(
            label="verify-test",
            blob_hashes=[h_blob],
            council_approval_hash=approval_hash,
        )
        check("rejects unregistered reviewer in promote()", False, "expected ValueError")
    except ValueError as e:
        check("rejects unregistered reviewer in promote()",
              "not a promoted reviewer" in str(e))


def test_require_reviewer_enforcement() -> None:
    section("_verify_council_approval — require_reviewer rejects wrong signer")
    bootstrap_hash = _boot.get("bootstrap_reviewer_hash", "")
    evolve_hash    = _boot.get("evolve_reviewer_hash", "")

    payload = json.dumps({
        "id":               "third-reviewer",
        "authorized_types": ["logic/python"],
        "trust_weight":     0.6,
    }, sort_keys=True)
    rh = seed.put("council/reviewer", payload)

    # Issue approval signed by evolve-engine, but promote_reviewer expects bootstrap
    approval = promote.issue_council_approval([rh], evolve_hash)
    try:
        promote.promote_reviewer(rh, bootstrap_hash, approval)
        check("require_reviewer rejects wrong signer", False, "expected ValueError")
    except ValueError as e:
        check("require_reviewer rejects wrong signer",
              bootstrap_hash[:16] in str(e) or "expected" in str(e).lower())


def test_reviewer_trust_weighting_in_telemetry_reader() -> None:
    section("TELEMETRY_READER_V7 — high-trust reviewer feedback weighs more than low-trust")
    telem_v7_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V7)

    # Two blobs — each gets one 'pass' feedback from reviewers with different trust weights.
    # high_blob: reviewed by bootstrap reviewer (trust_weight=1.0)
    # low_blob:  reviewed by evolve reviewer (trust_weight=0.8)
    # Both have confidence=1.0, outcome=pass, 1 telemetry hit each.
    # FeedbackScore formula: pos_w / total_w where pos_w = confidence * trust
    # Both get score = 1.0 (single pass feedback each), but high_blob's weight is larger.
    # For a fair test, compare a pass+fail mix:
    # high_blob: pass(c=1.0, trust=1.0) + fail(c=1.0, trust=1.0) → score = 0.5
    # low_blob:  pass(c=1.0, trust=0.8) + fail(c=1.0, trust=0.8) → score = 0.5
    # Same scores. Let's distinguish by weighting asymmetry:
    # high_blob: pass(c=1.0, trust=1.0) → score = 1.0
    # low_blob:  pass(c=1.0, trust=0.8) → score = 1.0 (both all-pass → same score)
    # Better test: one fail from high-trust reviewer hurts more.
    # high_blob: pass(c=1.0, trust=1.0) + fail(c=1.0, trust=1.0) → 1.0/(2.0)  = 0.5
    # low_blob:  pass(c=1.0, trust=0.8) + fail(c=1.0, trust=1.0) → 0.8/(1.8)  ≈ 0.444
    # So a high-trust pass + low-trust fail produces a higher score than low-trust pass + high-trust fail.

    bootstrap_hash = _boot.get("bootstrap_reviewer_hash", "")  # trust_weight=1.0
    evolve_hash    = _boot.get("evolve_reviewer_hash", "")     # trust_weight=0.8

    h_high = seed.put("logic/python", "result = 'trust-high'")
    h_low  = seed.put("logic/python", "result = 'trust-low'")
    seed.invoke(h_high, {})
    seed.invoke(h_low,  {})

    # h_high: pass from bootstrap (trust=1.0), fail from evolve (trust=0.8)
    # → pos_w=1.0, total_w=1.8, score = 1.0/1.8 ≈ 0.556
    fb_high_pass = seed.put("feedback/outcome", json.dumps({
        "invoked": h_high, "invocation_telem": None,
        "outcome": "pass", "confidence": 1.0,
        "reviewer": "bootstrap", "reviewer_hash": bootstrap_hash,
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }, sort_keys=True))
    fb_high_fail = seed.put("feedback/outcome", json.dumps({
        "invoked": h_high, "invocation_telem": None,
        "outcome": "fail", "confidence": 1.0,
        "reviewer": "evolve", "reviewer_hash": evolve_hash,
        "timestamp_utc": "2026-01-01T00:00:01Z",
    }, sort_keys=True))

    # h_low: pass from evolve (trust=0.8), fail from bootstrap (trust=1.0)
    # → pos_w=0.8, total_w=1.8, score = 0.8/1.8 ≈ 0.444
    fb_low_pass = seed.put("feedback/outcome", json.dumps({
        "invoked": h_low, "invocation_telem": None,
        "outcome": "pass", "confidence": 1.0,
        "reviewer": "evolve", "reviewer_hash": evolve_hash,
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }, sort_keys=True))
    fb_low_fail = seed.put("feedback/outcome", json.dumps({
        "invoked": h_low, "invocation_telem": None,
        "outcome": "fail", "confidence": 1.0,
        "reviewer": "bootstrap", "reviewer_hash": bootstrap_hash,
        "timestamp_utc": "2026-01-01T00:00:01Z",
    }, sort_keys=True))

    # Promote all four feedback blobs
    reviewer_hash = bootstrap_hash
    for h_logic, fbs in [(h_high, [fb_high_pass, fb_high_fail]),
                          (h_low,  [fb_low_pass,  fb_low_fail])]:
        approval = promote.issue_council_approval(fbs, reviewer_hash)
        promote.promote_feedback(h_logic, fbs, approval)

    m = promote.load_manifest()
    reviewer_trust = {bootstrap_hash: 1.0, evolve_hash: 0.8}

    result = seed.invoke(telem_v7_hash, {
        "vault_dir":         str(seed.VAULT_DIR),
        "approved_feedback": m.get("approved_feedback", {}),
        "reviewer_trust":    reviewer_trust,
    })

    high_score = result.get(h_high, {}).get("feedback_score", None)
    low_score  = result.get(h_low,  {}).get("feedback_score", None)

    check("h_high FeedbackScore present", high_score is not None)
    check("h_low  FeedbackScore present", low_score  is not None)
    check("high-trust pass + low-trust fail > low-trust pass + high-trust fail",
          (high_score is not None and low_score is not None and high_score > low_score),
          f"high={high_score}, low={low_score}")


def test_full_f6_evolution_cycle() -> None:
    section("Full f_6 evolution cycle — reviewer trust active, manifest v1.6.0")
    results = evolve.run_all()

    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three cycles ran", len(results) == 3)
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.7.0", m["version"] == "1.7.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} in manifest", h is not None)

    # Audit log must show promotions signed by the evolve-engine reviewer
    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_events = [e for e in entries if e.get("event") == "promote" and e.get("version") == "1.7.0"]
    check("at least one promote event with version 1.7.0", len(promote_events) >= 1)
    evolve_hash = _boot.get("evolve_reviewer_hash", "")
    if promote_events and evolve_hash:
        check("f_6 promotions signed by evolve-engine reviewer",
              any(e.get("council_reviewer_hash") == evolve_hash for e in promote_events))


def test_end_to_end_reviewer_chain() -> None:
    section("End-to-end: bootstrap → evolve-engine → blob promotion chain")
    bootstrap_hash = _boot.get("bootstrap_reviewer_hash", "")
    evolve_hash    = _boot.get("evolve_reviewer_hash", "")

    # Create a new logic blob and promote it through the full chain
    h_blob = seed.put("logic/python", "result = 'chain-test'")
    approval = promote.issue_council_approval([h_blob], evolve_hash)
    manifest_hash = promote.promote(
        label="chain-test",
        blob_hashes=[h_blob],
        council_approval_hash=approval,
        version=None,  # keep existing version
    )
    check("promote() succeeded with governed approval", len(manifest_hash) == 64)

    m = promote.load_manifest()
    stored = m.get("blobs", {}).get("chain-test", {}).get("logic/python")
    check("chain-test blob in manifest", stored == h_blob)

    # Verify the reviewer chain is correct: manifest has both reviewers
    check("bootstrap reviewer in manifest", bootstrap_hash in m.get("reviewers", {}))
    check("evolve reviewer in manifest",    evolve_hash    in m.get("reviewers", {}))
    evolve_entry = m["reviewers"][evolve_hash]
    check("evolve reviewer approved_by bootstrap",
          evolve_entry.get("approved_by") == bootstrap_hash)


def test_linker_passes_reviewer_trust_to_telemetry() -> None:
    section("linker.read_telemetry() — passes reviewer_trust context to telemetry reader")
    # read_telemetry() builds reviewer_trust from manifest["reviewers"] entries.
    # Since both reviewers are registered, their trust weights should propagate.
    # We can't easily introspect the context dict, but we can verify that
    # read_telemetry() returns a valid dict without error (integration smoke test).
    try:
        telem = linker.read_telemetry()
        check("read_telemetry() returns dict", isinstance(telem, dict))
        # At minimum, blobs that have been invoked during this test run are present
        check("telemetry dict is non-empty", len(telem) > 0)
    except Exception as e:
        check("read_telemetry() returns dict", False, str(e))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for p in [seed.VAULT_DIR, seed.BYTECODE_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()
    seed._LAST_TELEMETRY.clear()

    _boot.update(bootstrap.run())
    print()

    test_bootstrap_reviewer_creates_trust_root()
    test_evolve_reviewer_promoted_by_bootstrap()
    test_reviewer_integrity_pass_valid()
    test_reviewer_integrity_rejects_bad_trust_weight_above_one()
    test_reviewer_integrity_rejects_zero_trust_weight()
    test_reviewer_integrity_rejects_missing_id()
    test_reviewer_integrity_rejects_empty_authorized_types()
    test_promote_reviewer_requires_existing_reviewer()
    test_issue_council_approval_stores_reviewer_hash()
    test_verify_council_approval_rejects_unregistered_reviewer()
    test_require_reviewer_enforcement()
    test_reviewer_trust_weighting_in_telemetry_reader()
    test_full_f6_evolution_cycle()
    test_end_to_end_reviewer_chain()
    test_linker_passes_reviewer_trust_to_telemetry()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
