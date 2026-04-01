#!/usr/bin/env python3
"""
tests/test_fabric.py — D-JIT Logic Fabric test suite
Covers: PUT, INVOKE, ABI enforcement, Triple-Pass Review, promote flow
"""

import json
import os
import sys
from pathlib import Path

# Run from project root
sys.path.insert(0, str(Path(__file__).parent.parent))
import seed
import promote

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

def test_put_idempotent() -> None:
    section("PUT")
    h1 = seed.put("logic/python", "result = 1")
    h2 = seed.put("logic/python", "result = 1")
    check("same payload → same hash", h1 == h2)
    check("hash is 64-char hex", len(h1) == 64 and all(c in "0123456789abcdef" for c in h1))
    blob_path = seed.VAULT_DIR / h1
    check("blob written to vault", blob_path.exists())


def test_invoke_basic() -> None:
    section("INVOKE — basic")
    h = seed.put("logic/python", "result = context['a'] + context['b']")
    out = seed.invoke(h, {"a": 10, "b": 32})
    check("arithmetic result correct", out == 42, f"got {out!r}")


def test_invoke_log() -> None:
    section("INVOKE — log() sink")
    h = seed.put("logic/python", "log('hello'); result = 'done'")
    out = seed.invoke(h, {})
    check("result returned", out == "done")
    # Telemetry blob should contain log line
    blobs = list(seed.VAULT_DIR.iterdir())
    telem = [
        json.loads(json.loads(b.read_text())["payload"])
        for b in blobs
        if json.loads(b.read_text())["type"] == "telemetry/artifact"
        and json.loads(json.loads(b.read_text())["payload"])["invoked"] == h
    ]
    check("telemetry captured log line", any("hello" in t.get("log", []) for t in telem))


def test_abi_violation() -> None:
    section("ABI enforcement")
    h = seed.put("logic/python", "x = 42  # no result")
    raised = False
    try:
        seed.invoke(h, {})
    except RuntimeError as e:
        raised = "ABI violation" in str(e)
    check("RuntimeError raised on missing result", raised)


def test_telemetry_blob() -> None:
    section("TELEMETRY")
    h = seed.put("logic/python", "result = 'telem-test'")
    seed.invoke(h, {})
    blobs = list(seed.VAULT_DIR.iterdir())
    telem_blobs = [
        b for b in blobs
        if json.loads(b.read_text())["type"] == "telemetry/artifact"
    ]
    check("at least one telemetry blob exists", len(telem_blobs) >= 1)
    latest = json.loads(json.loads(telem_blobs[-1].read_text())["payload"])
    check("telemetry has latency_ms", "latency_ms" in latest)
    check("telemetry has memory_kb", "memory_kb" in latest)


def test_triple_pass_clean() -> None:
    section("Triple-Pass — clean blob")
    h = seed.put("logic/python", "result = context.get('x', 0) * 2")
    blob = promote.triple_pass_review(h)
    check("clean blob passes all three passes", blob is not None)


def test_triple_pass_abi_violation() -> None:
    section("Triple-Pass — ABI violation caught")
    h = seed.put("logic/python", "x = 99  # no result")
    raised = False
    try:
        promote.triple_pass_review(h)
    except promote.ReviewError as e:
        raised = e.pass_name == "ProtocolCompliance"
    check("ProtocolCompliance pass catches missing result", raised)


def test_triple_pass_safety() -> None:
    section("Triple-Pass — safety violation caught")
    h = seed.put("logic/python", "import os\nresult = os.getcwd()")
    raised = False
    try:
        promote.triple_pass_review(h)
    except promote.ReviewError as e:
        raised = e.pass_name == "SafetyVerification"
    check("SafetyVerification pass catches import os", raised)


def test_triple_pass_syntax() -> None:
    section("Triple-Pass — syntax error caught")
    h = seed.put("logic/python", "result = (((  # broken")
    raised = False
    try:
        promote.triple_pass_review(h)
    except promote.ReviewError as e:
        raised = e.pass_name == "StaticAnalysis"
    check("StaticAnalysis pass catches syntax error", raised)


def test_promote_full_flow() -> None:
    section("PROMOTE — full flow")
    h = seed.put("logic/python", "result = context['v'] ** 2")

    # Issue Council Approval
    approval_hash = promote.issue_council_approval([h], reviewer="test-council")
    check("council approval artifact created", len(approval_hash) == 64)

    # Promote
    manifest_hash = promote.promote(
        label="L1",
        blob_hashes=[h],
        council_approval_hash=approval_hash,
        version="0.1.0",
    )
    check("manifest hash returned", len(manifest_hash) == 64)

    # Verify manifest written
    m = promote.load_manifest()
    check("manifest version updated", m["version"] == "0.1.0")
    check("blob registered in manifest", h in m["blobs"]["L1"].values())
    check("manifest hash matches", m["hash"] == manifest_hash)

    # Verify audit log entry
    entries = [
        json.loads(line)
        for line in Path("./audit.log").read_text().splitlines()
        if line.strip()
    ]
    last = entries[-1]
    check("audit log event=promote", last["event"] == "promote")
    check("audit log has council_approval_hash", last["council_approval_hash"] == approval_hash)
    check("audit log has manifest_hash", last["manifest_hash"] == manifest_hash)


def test_promote_no_approval() -> None:
    section("PROMOTE — rejected without valid approval")
    h = seed.put("logic/python", "result = 'no-approval'")
    raised = False
    try:
        promote.promote("L1", [h], council_approval_hash="0" * 64)
    except (ValueError, FileNotFoundError):
        raised = True
    check("promote blocked without valid council approval", raised)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Clean vault for reproducible run
    import shutil
    for p in [seed.VAULT_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()

    test_put_idempotent()
    test_invoke_basic()
    test_invoke_log()
    test_abi_violation()
    test_telemetry_blob()
    test_triple_pass_clean()
    test_triple_pass_abi_violation()
    test_triple_pass_safety()
    test_triple_pass_syntax()
    test_promote_full_flow()
    test_promote_no_approval()

    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"\n{'─'*40}")
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
