#!/usr/bin/env python3
"""
tests/test_f5.py — f_5 feedback governance tests
Covers: _pass_feedback_integrity, promote_feedback(), approved_feedback in
        manifest, governance filter in telemetry-reader v6, Bayesian
        FeedbackScore smoothing in planning v6, full f_5 evolution cycle,
        manifest v1.5.0.
"""

import json
import shutil
import sys
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import bootstrap
import evolve
import infer
import linker
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []

# Reviewer hash populated by bootstrap at __main__ time; used by tests that need
# a governed approval artifact (issue_council_approval requires reviewer_hash in f_6).
_evolve_reviewer_hash: str = ""


def _reviewer() -> str:
    """Return a promoted reviewer hash for use in test approvals."""
    if _evolve_reviewer_hash:
        return _evolve_reviewer_hash
    # Fallback: find any reviewer in the manifest
    m = promote.load_manifest()
    return next(iter(m.get("reviewers", {})), "")


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------

def test_feedback_integrity_pass_valid() -> None:
    section("FeedbackIntegrity — valid feedback blob passes review")
    h_logic = seed.put("logic/python", "result = 'integrity-test'")
    seed.invoke(h_logic, {})
    fb_hash = seed.record_feedback(h_logic, "pass", confidence=0.8, reviewer="test")

    try:
        blob = promote.triple_pass_review(fb_hash)
        check("valid feedback/outcome passes all passes", blob["type"] == "feedback/outcome")
    except promote.ReviewError as e:
        check("valid feedback/outcome passes all passes", False, str(e))


def test_feedback_integrity_rejects_bad_outcome() -> None:
    section("FeedbackIntegrity — rejects invalid outcome value")
    h_logic = seed.put("logic/python", "result = 'bad-outcome'")
    seed.invoke(h_logic, {})

    # Craft a feedback blob with an invalid outcome
    bad_record = {
        "invoked":       h_logic,
        "outcome":       "maybe",   # not in {"pass", "fail", "partial"}
        "confidence":    1.0,
        "reviewer":      "test",
        "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    fb_hash = seed.put("feedback/outcome", json.dumps(bad_record, sort_keys=True))
    try:
        promote.triple_pass_review(fb_hash)
        check("rejects invalid outcome 'maybe'", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects invalid outcome 'maybe'",
              e.pass_name == "FeedbackIntegrity" and "outcome" in str(e).lower())


def test_feedback_integrity_rejects_bad_confidence() -> None:
    section("FeedbackIntegrity — rejects confidence out of range")
    h_logic = seed.put("logic/python", "result = 'bad-confidence'")
    seed.invoke(h_logic, {})
    bad_record = {
        "invoked": h_logic, "outcome": "pass",
        "confidence": 1.5,   # > 1.0
        "reviewer": "test", "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    fb_hash = seed.put("feedback/outcome", json.dumps(bad_record, sort_keys=True))
    try:
        promote.triple_pass_review(fb_hash)
        check("rejects confidence 1.5", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects confidence 1.5",
              e.pass_name == "FeedbackIntegrity" and "confidence" in str(e).lower())


def test_feedback_integrity_rejects_missing_invoked() -> None:
    section("FeedbackIntegrity — rejects feedback for nonexistent blob")
    bad_record = {
        "invoked": "a" * 64,   # valid format but does not exist in vault
        "outcome": "pass", "confidence": 1.0,
        "reviewer": "test", "timestamp_utc": "2026-01-01T00:00:00Z",
    }
    fb_hash = seed.put("feedback/outcome", json.dumps(bad_record, sort_keys=True))
    try:
        promote.triple_pass_review(fb_hash)
        check("rejects feedback for nonexistent blob", False, "expected ReviewError")
    except promote.ReviewError as e:
        check("rejects feedback for nonexistent blob",
              e.pass_name == "FeedbackIntegrity" and "not found" in str(e).lower())


def test_promote_feedback_updates_manifest() -> None:
    section("promote_feedback — approved_feedback written to manifest")
    h_logic = seed.put("logic/python", "result = 'promote-test'")
    seed.invoke(h_logic, {})
    fb_hash = seed.record_feedback(h_logic, "pass", confidence=1.0, reviewer="test")

    approval = promote.issue_council_approval([fb_hash], _reviewer())
    manifest_hash = promote.promote_feedback(
        logic_hash=h_logic,
        feedback_hashes=[fb_hash],
        council_approval_hash=approval,
    )
    check("promote_feedback returns manifest hash", len(manifest_hash) == 64)

    m = promote.load_manifest()
    approved = m.get("approved_feedback", {})
    check("approved_feedback key present in manifest", h_logic in approved)
    check("feedback hash in approved list", fb_hash in approved.get(h_logic, []))


def test_promote_feedback_audit_log() -> None:
    section("promote_feedback — audit log entry written")
    h_logic  = seed.put("logic/python", "result = 'audit-test'")
    seed.invoke(h_logic, {})
    fb_hash  = seed.record_feedback(h_logic, "pass", confidence=1.0, reviewer="test")
    approval = promote.issue_council_approval([fb_hash], _reviewer())
    promote.promote_feedback(h_logic, [fb_hash], approval)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines()
               if l.strip()]
    feedback_entries = [e for e in entries if e.get("event") == "promote_feedback"]
    check("promote_feedback event in audit log", len(feedback_entries) >= 1)
    last = feedback_entries[-1]
    check("logic_hash in audit entry", last.get("logic_hash") == h_logic)
    check("feedback_hashes in audit entry", fb_hash in last.get("feedback_hashes", []))


def test_governance_filter_blocks_unapproved() -> None:
    section("Governance filter — unapproved feedback invisible to telemetry-reader v6")
    telem_v6_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V6)

    h_blob = seed.put("logic/python", "result = 'ungoverned'")
    for _ in range(3):
        seed.invoke(h_blob, {})
        # Record feedback but do NOT promote it
        seed.record_feedback(h_blob, "fail", confidence=1.0, reviewer="test")

    # approved_feedback is empty — no feedback promoted
    result = seed.invoke(telem_v6_hash, {
        "vault_dir":         str(seed.VAULT_DIR),
        "approved_feedback": {},
    })
    if h_blob in result:
        entry = result[h_blob]
        check("feedback_score is 1.0 when no approved feedback (governance blocks all)",
              entry["feedback_score"] == 1.0, f"got {entry['feedback_score']}")


def test_governance_filter_counts_approved() -> None:
    section("Governance filter — approved feedback counts toward FeedbackScore")
    telem_v6_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V6)

    h_blob = seed.put("logic/python", "result = 'governed'")
    seed.invoke(h_blob, {})
    fb_hash  = seed.record_feedback(h_blob, "fail", confidence=1.0, reviewer="test")
    approval = promote.issue_council_approval([fb_hash], _reviewer())
    promote.promote_feedback(h_blob, [fb_hash], approval)

    m      = promote.load_manifest()
    result = seed.invoke(telem_v6_hash, {
        "vault_dir":         str(seed.VAULT_DIR),
        "approved_feedback": m.get("approved_feedback", {}),
    })
    if h_blob in result:
        entry = result[h_blob]
        check("approved fail feedback lowers FeedbackScore below 1.0",
              entry["feedback_score"] < 1.0, f"got {entry['feedback_score']}")
        check("feedback_count reflects approved count",
              entry["feedback_count"] >= 1)


def test_planning_v6_bayesian_feedback_smoothing() -> None:
    section("Planning v6 — Bayesian smoothing for sparse FeedbackScore")
    plan_v6_hash = seed.put("logic/python", evolve.PLANNING_V6)

    # With feedback_count < MIN_FEEDBACK (3), a single negative feedback should
    # not completely destroy the score — it blends toward 1.0 neutral prior.
    result = seed.invoke(plan_v6_hash, {"candidates": [
        # 1 approved negative feedback, but smoothed — should still compete
        {"hash": "smoothed", "success_rate": 0.95, "latency_ms": 1.0, "p95_latency_ms": 1.2,
         "integrity": 0.9, "cost": 1.0, "invocation_count": 10,
         "feedback_score": 0.0, "feedback_count": 1},  # single fail, smoothed
        # No feedback, but higher latency
        {"hash": "raw",      "success_rate": 0.95, "latency_ms": 5.0, "p95_latency_ms": 5.2,
         "integrity": 0.9, "cost": 1.0, "invocation_count": 10,
         "feedback_score": 1.0, "feedback_count": 0},
    ]})
    # smoothed blob: feedback_score = (1/3)*0.0 + (2/3)*1.0 = 0.667
    # score = 0.95 * 0.9 * 0.667 / (1.2 * 1.0 * 1.0) ≈ 0.476
    # raw blob:     score = 0.95 * 0.9 * 1.0  / (5.2 * 1.04 * 1.0) ≈ 0.158
    check("Bayesian-smoothed blob wins over high-latency no-feedback blob",
          result["selected"] == "smoothed", f"selected={result['selected']!r}")


def test_planning_v6_full_feedback_trusted_above_threshold() -> None:
    section("Planning v6 — raw FeedbackScore used when feedback_count >= MIN_FEEDBACK")
    plan_v6_hash = seed.put("logic/python", evolve.PLANNING_V6)

    result = seed.invoke(plan_v6_hash, {"candidates": [
        # 5 approved feedbacks, mix — score is taken raw (not smoothed)
        {"hash": "rated",    "success_rate": 1.0, "latency_ms": 1.0, "p95_latency_ms": 1.1,
         "integrity": 1.0, "cost": 1.0, "invocation_count": 20,
         "feedback_score": 0.80, "feedback_count": 5},
        # identical but no feedback
        {"hash": "unrated",  "success_rate": 1.0, "latency_ms": 1.0, "p95_latency_ms": 1.1,
         "integrity": 1.0, "cost": 1.0, "invocation_count": 20,
         "feedback_score": 1.0,  "feedback_count": 0},
    ]})
    # unrated: smoothed toward 1.0 (0 count → full prior = 1.0) → wins over rated (0.80)
    check("unrated blob (neutral prior) beats rated blob with 0.80 feedback_score",
          result["selected"] == "unrated", f"selected={result['selected']!r}")


def test_full_f5_evolution_cycle() -> None:
    section("Full f_5 evolution cycle — governance filter active")
    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f5-bc",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f5-bc",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f5-bc",
    }
    def _mock_gen(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f5-bc")
    _iu = infer.InferenceUnavailable("mocked")
    with mock.patch("infer.generate_candidate", side_effect=_mock_gen), \
         mock.patch("infer.generate_test_cases", side_effect=_iu), \
         mock.patch("promote.run_test_suite", return_value=[]):
        results = evolve.run_all()

    # f_5 pattern: planning v6 (Bayesian smoothing, minimal overhead) should promote.
    # Telemetry-reader v6 correctly held vs sparse-vault baseline.
    # Discovery v6 correctly held vs minimal bootstrap baseline.
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three cycles ran", len(results) == 3)
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.11.0", m["version"] == "1.11.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} in manifest", h is not None)


def test_end_to_end_governed_feedback_loop() -> None:
    section("End-to-end: invoke → record → promote feedback → FeedbackScore visible")
    telem_v6_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V6)

    h_good = seed.put("logic/python", "result = 'e2e-good'")
    h_bad  = seed.put("logic/python", "result = 'e2e-bad'")

    # Invoke both, record feedback
    for _ in range(5):
        seed.invoke(h_good, {})
        seed.record_feedback(h_good, "pass", confidence=1.0, reviewer="test")
    for _ in range(5):
        seed.invoke(h_bad, {})
        seed.record_feedback(h_bad, "fail",  confidence=1.0, reviewer="test")

    # Before governance: both show feedback_score = 1.0 (no approved feedback)
    result_pre = seed.invoke(telem_v6_hash, {
        "vault_dir": str(seed.VAULT_DIR), "approved_feedback": {}
    })
    pre_good = result_pre.get(h_good, {}).get("feedback_score", 1.0)
    pre_bad  = result_pre.get(h_bad,  {}).get("feedback_score", 1.0)
    check("before governance: both FeedbackScores neutral",
          pre_good == 1.0 and pre_bad == 1.0)

    # Promote the feedback
    good_fbs = [h for h, env in
                [(p.name, json.loads(p.read_text())) for p in seed.VAULT_DIR.iterdir() if p.is_file()]
                if env.get("type") == "feedback/outcome"
                and json.loads(env["payload"]).get("invoked") == h_good]
    bad_fbs  = [h for h, env in
                [(p.name, json.loads(p.read_text())) for p in seed.VAULT_DIR.iterdir() if p.is_file()]
                if env.get("type") == "feedback/outcome"
                and json.loads(env["payload"]).get("invoked") == h_bad]

    if good_fbs:
        approval = promote.issue_council_approval(good_fbs, _reviewer())
        promote.promote_feedback(h_good, good_fbs, approval)
    if bad_fbs:
        approval = promote.issue_council_approval(bad_fbs, _reviewer())
        promote.promote_feedback(h_bad, bad_fbs, approval)

    # After governance: feedback_score reflects approved outcomes
    m = promote.load_manifest()
    result_post = seed.invoke(telem_v6_hash, {
        "vault_dir": str(seed.VAULT_DIR),
        "approved_feedback": m.get("approved_feedback", {}),
    })
    post_good = result_post.get(h_good, {}).get("feedback_score", 1.0)
    post_bad  = result_post.get(h_bad,  {}).get("feedback_score", 1.0)
    check("after governance: h_good FeedbackScore = 1.0 (all pass)",
          post_good == 1.0, f"got {post_good}")
    check("after governance: h_bad FeedbackScore = 0.0 (all fail)",
          post_bad == 0.0, f"got {post_bad}")
    check("governed FeedbackScore distinguishes good from bad",
          post_good > post_bad)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for p in [seed.VAULT_DIR, seed.BYTECODE_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()
    seed._LAST_TELEMETRY.clear()

    boot = bootstrap.run()
    _evolve_reviewer_hash = boot["evolve_reviewer_hash"]
    print()

    test_feedback_integrity_pass_valid()
    test_feedback_integrity_rejects_bad_outcome()
    test_feedback_integrity_rejects_bad_confidence()
    test_feedback_integrity_rejects_missing_invoked()
    test_promote_feedback_updates_manifest()
    test_promote_feedback_audit_log()
    test_governance_filter_blocks_unapproved()
    test_governance_filter_counts_approved()
    test_planning_v6_bayesian_feedback_smoothing()
    test_planning_v6_full_feedback_trusted_above_threshold()
    test_full_f5_evolution_cycle()
    test_end_to_end_governed_feedback_loop()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
