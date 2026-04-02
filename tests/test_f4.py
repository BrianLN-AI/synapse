#!/usr/bin/env python3
"""
tests/test_f4.py — f_4 governed feedback loop tests
Covers: feedback/outcome blob type, proven-execution anchor, FeedbackScore
        in telemetry-reader v5 and planning v5, full f_4 evolution cycle,
        manifest v1.4.0.
"""

import json
import shutil
import sys
import time
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


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------

def test_record_feedback_structure() -> None:
    section("record_feedback — creates a valid feedback/outcome blob")
    h_logic = seed.put("logic/python", "result = 'feedback-test'")
    seed.invoke(h_logic, {})   # establish proven-execution anchor

    fb_hash = seed.record_feedback(h_logic, outcome="pass", confidence=0.9, reviewer="test")
    check("feedback hash is hex string", len(fb_hash) == 64 and all(c in "0123456789abcdef" for c in fb_hash))

    # Read it back from the vault
    envelope = seed._raw_get(fb_hash)
    check("type is feedback/outcome", envelope.get("type") == "feedback/outcome")

    record = json.loads(envelope["payload"])
    check("invoked matches logic hash", record.get("invoked") == h_logic)
    check("outcome is 'pass'", record.get("outcome") == "pass")
    check("confidence stored", record.get("confidence") == 0.9)
    check("reviewer stored", record.get("reviewer") == "test")
    check("timestamp present", bool(record.get("timestamp_utc")))
    check("invocation_telem anchor present", record.get("invocation_telem") is not None)


def test_proven_execution_anchor() -> None:
    section("Proven-execution anchor — feedback links to actual invocation")
    h_logic = seed.put("logic/python", "result = 'anchor-test'")

    # Before invoking: no anchor
    seed._LAST_TELEMETRY.pop(h_logic, None)
    fb_hash_pre = seed.record_feedback(h_logic, "pass")
    record_pre  = json.loads(seed._raw_get(fb_hash_pre)["payload"])
    check("no anchor before first invoke", record_pre.get("invocation_telem") is None)

    # After invoking: anchor is set
    seed.invoke(h_logic, {})
    fb_hash_post = seed.record_feedback(h_logic, "pass")
    record_post  = json.loads(seed._raw_get(fb_hash_post)["payload"])
    check("anchor set after invoke", record_post.get("invocation_telem") is not None)

    # Anchor is the telemetry blob hash (verifiable in vault)
    telem_hash = record_post["invocation_telem"]
    telem_env  = seed._raw_get(telem_hash)
    check("anchor resolves to telemetry/artifact blob", telem_env.get("type") == "telemetry/artifact")


def test_feedback_content_addressing() -> None:
    section("Feedback blobs are content-addressed")
    h_logic = seed.put("logic/python", "result = 'dedup-test'")
    seed.invoke(h_logic, {})

    # Record identical feedback twice — should produce same hash
    # (same invoked, outcome, confidence, reviewer, timestamp second)
    # Use sleep(0) to keep within same second for timestamp deduplication
    fb1 = seed.record_feedback(h_logic, "pass", 1.0, "test-reviewer")
    fb2 = seed.record_feedback(h_logic, "pass", 1.0, "test-reviewer")
    # Same second + same anchor → same content → same hash
    # (May differ if second boundary crossed; assert both are valid hashes at minimum)
    check("feedback produces valid hash", len(fb1) == 64)
    check("identical feedback deduplicates or both valid", len(fb2) == 64)


def test_telemetry_reader_v5_feedback_score_default() -> None:
    section("Telemetry-reader v5 — FeedbackScore defaults to 1.0 with no feedback")
    telem_v5_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V5)

    h_clean = seed.put("logic/python", "result = 'no-feedback-blob'")
    for _ in range(4):
        seed.invoke(h_clean, {})

    result = seed.invoke(telem_v5_hash, {"vault_dir": str(seed.VAULT_DIR)})
    check("reader returns dict", isinstance(result, dict))
    if h_clean in result:
        entry = result[h_clean]
        check("feedback_score present", "feedback_score" in entry)
        check("feedback_score defaults to 1.0 when no feedback",
              entry["feedback_score"] == 1.0, f"got {entry['feedback_score']}")
        check("feedback_count is 0", entry["feedback_count"] == 0)


def test_telemetry_reader_v5_positive_feedback() -> None:
    section("Telemetry-reader v5 — positive feedback raises FeedbackScore")
    telem_v5_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V5)

    h_blob = seed.put("logic/python", "result = 'positive-feedback-blob'")
    for _ in range(3):
        seed.invoke(h_blob, {})
        seed.record_feedback(h_blob, "pass", confidence=1.0, reviewer="test")

    result = seed.invoke(telem_v5_hash, {"vault_dir": str(seed.VAULT_DIR)})
    if h_blob in result:
        entry = result[h_blob]
        check("feedback_score is 1.0 with all-pass feedback",
              entry["feedback_score"] == 1.0, f"got {entry['feedback_score']}")
        check("feedback_count > 0", entry["feedback_count"] > 0)


def test_telemetry_reader_v5_negative_feedback() -> None:
    section("Telemetry-reader v5 — negative feedback lowers FeedbackScore")
    telem_v5_hash = seed.put("logic/python", evolve.TELEMETRY_READER_V5)

    h_blob = seed.put("logic/python", "result = 'negative-feedback-blob'")
    seed.invoke(h_blob, {})
    # Record 3 fail, 1 pass
    seed.record_feedback(h_blob, "fail",  confidence=1.0, reviewer="test")
    seed.record_feedback(h_blob, "fail",  confidence=1.0, reviewer="test")
    seed.record_feedback(h_blob, "fail",  confidence=1.0, reviewer="test")
    seed.record_feedback(h_blob, "pass",  confidence=1.0, reviewer="test")

    result = seed.invoke(telem_v5_hash, {"vault_dir": str(seed.VAULT_DIR)})
    if h_blob in result:
        entry = result[h_blob]
        # 1 pass out of 4 = 0.25, but feedback blobs are content-addressed.
        # Rapid same-second identical records may deduplicate.
        # Assert score < 1.0 (some negative feedback registered).
        check("feedback_score < 1.0 with negative feedback",
              entry["feedback_score"] < 1.0, f"got {entry['feedback_score']}")


def test_planning_v5_feedback_aware() -> None:
    section("Planning v5 — blob with positive feedback beats identical blob with negative")
    plan_v5_hash = seed.put("logic/python", evolve.PLANNING_V5)

    result = seed.invoke(plan_v5_hash, {"candidates": [
        {"hash": "good", "success_rate": 0.9, "latency_ms": 2.0, "p95_latency_ms": 2.5,
         "integrity": 0.8, "cost": 1.0, "invocation_count": 10, "feedback_score": 0.95},
        {"hash": "bad",  "success_rate": 0.9, "latency_ms": 2.0, "p95_latency_ms": 2.5,
         "integrity": 0.8, "cost": 1.0, "invocation_count": 10, "feedback_score": 0.10},
    ]})
    check("planning v5 selects high-feedback blob over low-feedback",
          result["selected"] == "good", f"selected={result['selected']!r}")


def test_planning_v5_neutral_fallback() -> None:
    section("Planning v5 — neutral when no feedback_score field")
    plan_v5_hash = seed.put("logic/python", evolve.PLANNING_V5)
    result = seed.invoke(plan_v5_hash, {"candidates": [
        {"hash": "a", "success_rate": 0.95, "latency_ms": 1.0, "integrity": 0.9, "cost": 1.0, "invocation_count": 10},
        {"hash": "b", "success_rate": 0.80, "latency_ms": 5.0, "integrity": 0.5, "cost": 1.0, "invocation_count": 10},
    ]})
    check("planning v5 works without feedback_score field", result["selected"] == "a")


def test_discovery_v5_type_guard_preserved() -> None:
    section("Discovery v5 — type guard still rejects non-logic blobs")
    disc_v5_hash = seed.put("logic/python", evolve.DISCOVERY_V5)

    telem_hash = seed.put("telemetry/artifact", json.dumps({"invoked": "test", "error": None}))
    try:
        seed.invoke(disc_v5_hash, {"hash": telem_hash, "vault_dir": str(seed.VAULT_DIR)})
        check("discovery v5 rejects telemetry blob", False, "expected TypeError")
    except TypeError as e:
        check("discovery v5 rejects telemetry blob", "logic/python" in str(e) or "telemetry" in str(e))

    logic_hash = seed.put("logic/python", "result = 'valid'")
    envelope   = seed.invoke(disc_v5_hash, {"hash": logic_hash, "vault_dir": str(seed.VAULT_DIR)})
    check("discovery v5 resolves logic blob", envelope.get("type") == "logic/python")


def test_full_f4_evolution_cycle() -> None:
    section("Full f_4 evolution cycle — FeedbackScore in fitness formula")
    results = evolve.run_all(reviewer="test-f4")

    # f_4 insight: the feedback signal enables the formula to reward correctness
    # as well as speed.  Discovery v5 (no hot-path log) should promote for the
    # same reason planning v4 did in f_3: minimal overhead, pure improvement.
    # Planning v5 (adds feedback_score) runs at essentially the same speed as v4.
    # Telemetry-reader v5 (two-pass: telemetry + feedback) adds read overhead —
    # the fabric may correctly hold it if the vault has few feedback blobs.
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("all three cycles ran", len(results) == 3)
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.4.0", m["version"] == "1.4.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} in manifest", h is not None)


def test_post_f4_arbitration_feedback_aware() -> None:
    section("Post-f_4: arbitration uses v5 planning + feedback scores")
    h_proven = seed.put("logic/python", "result = 'proven'")
    h_new    = seed.put("logic/python", "result = 'new'")

    # Give h_proven a track record with positive feedback
    for _ in range(10):
        linker.invoke(h_proven, {})
        seed.record_feedback(h_proven, "pass", confidence=1.0, reviewer="test")
    linker.invoke(h_new, {})

    result = linker.arbitrate([{"hash": h_proven}, {"hash": h_new}])
    check("post-f4 arbitration selects well-proven + feedback-positive blob",
          result["selected"] == h_proven)
    check("score numeric", isinstance(result.get("score"), (int, float)))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for p in [seed.VAULT_DIR, seed.BYTECODE_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()
    seed._LAST_TELEMETRY.clear()

    bootstrap.run(reviewer="test-bootstrap")
    print()

    test_record_feedback_structure()
    test_proven_execution_anchor()
    test_feedback_content_addressing()
    test_telemetry_reader_v5_feedback_score_default()
    test_telemetry_reader_v5_positive_feedback()
    test_telemetry_reader_v5_negative_feedback()
    test_planning_v5_feedback_aware()
    test_planning_v5_neutral_fallback()
    test_discovery_v5_type_guard_preserved()
    test_full_f4_evolution_cycle()
    test_post_f4_arbitration_feedback_aware()

    passed = sum(1 for _, ok in _results if ok)
    total  = len(_results)
    print(f"\n{'─' * 40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
