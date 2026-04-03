#!/usr/bin/env python3
"""
tests/test_f13.py — f_13 engine-as-expression kernel split

Covers:
  - Engine expression is stored in the vault after bootstrap
  - manifest.blobs["engine"]["logic/python"] is set
  - seed.invoke() delegates to the engine (not kernel-fallback) post-bootstrap
  - Engine scope contains invoke and record_feedback
  - Kernel fallback works when engine is absent (pre-engine invoke)
  - Engine blob passes Triple-Pass Review
  - Full f_13 evolution cycle: manifest v1.14.0
  - Backward compat: all prior blob types still reviewable
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
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []
_boot: dict = {}


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------
# Bootstrap + vault/manifest setup
# ---------------------------------------------------------------------------

def setup() -> None:
    for d in [seed.VAULT_DIR, seed.BYTECODE_DIR]:
        if d.exists():
            shutil.rmtree(d)
    if promote.MANIFEST_PATH.exists():
        promote.MANIFEST_PATH.unlink()
    if Path("audit.log").exists():
        Path("audit.log").unlink()

    # Reset engine cache so each test starts fresh
    seed._ENGINE = None
    seed._ENGINE_HASH = None

    global _boot
    _boot = bootstrap.run()
    print("\n── Bootstrap: f_0 + f_7 + f_13 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:16]}...")
    print(f"\n  f_0 + f_7 + f_13 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# Engine expression in vault
# ---------------------------------------------------------------------------

def test_engine_in_vault() -> None:
    section("Engine expression — blob stored in vault after bootstrap")
    engine_hash = _boot.get("engine_hash")
    check("bootstrap returned engine_hash", engine_hash is not None)
    if engine_hash:
        vault_file = seed.VAULT_DIR / engine_hash
        check("engine blob exists in vault", vault_file.exists())
        blob = seed._raw_get(engine_hash)
        check("engine blob type is logic/engine", blob.get("type") == "logic/engine")


def test_engine_in_manifest() -> None:
    section("Engine expression — manifest.blobs['engine']['logic/engine'] set")
    m = promote.load_manifest()
    engine_entry = m.get("blobs", {}).get("engine", {})
    engine_hash = engine_entry.get("logic/engine")
    check("manifest.blobs.engine exists", engine_entry != {})
    check("manifest.blobs.engine.logic/engine set", engine_hash is not None)
    if engine_hash:
        check("engine hash is 64-char hex", len(engine_hash) == 64)
        check("engine hash matches bootstrap return", engine_hash == _boot.get("engine_hash"))


# ---------------------------------------------------------------------------
# Engine delegation
# ---------------------------------------------------------------------------

def test_invoke_delegates_to_engine() -> None:
    section("Engine delegation — seed.invoke() uses engine post-bootstrap")
    # _load_engine() should return a non-None scope after bootstrap
    engine = seed._load_engine()
    check("_load_engine() returns scope", engine is not None)
    if engine:
        check("engine scope has invoke", "invoke" in engine)
        check("engine scope has record_feedback", "record_feedback" in engine)
        check("engine scope has _load_code", "_load_code" in engine)
        check("engine scope has _CODE_CACHE", "_CODE_CACHE" in engine)


def test_engine_invoke_executes_blob() -> None:
    section("Engine delegation — invoke() via engine executes a logic blob correctly")
    # Use the discovery blob as a real logic blob we know passes ABI
    m = promote.load_manifest()
    discovery_hash = m["blobs"]["discovery"]["logic/python"]

    result = seed.invoke(discovery_hash, {
        "hash": discovery_hash,
        "vault_dir": str(seed.VAULT_DIR),
    })
    check("invoke via engine returns dict", isinstance(result, dict))
    check("result has 'type' key", "type" in result)
    check("result has 'payload' key", "payload" in result)


def test_engine_telemetry_written() -> None:
    section("Engine delegation — engine path writes telemetry to vault")
    m = promote.load_manifest()
    discovery_hash = m["blobs"]["discovery"]["logic/python"]

    telem_before = set(
        f.name for f in seed.VAULT_DIR.iterdir()
        if f.is_file() and
        json.loads(f.read_text()).get("type") == "telemetry/artifact"
    )

    seed.invoke(discovery_hash, {
        "hash": discovery_hash,
        "vault_dir": str(seed.VAULT_DIR),
    })

    telem_after = set(
        f.name for f in seed.VAULT_DIR.iterdir()
        if f.is_file() and
        json.loads(f.read_text()).get("type") == "telemetry/artifact"
    )
    check("new telemetry blob written", len(telem_after) > len(telem_before))
    check("_LAST_TELEMETRY updated", discovery_hash in seed._LAST_TELEMETRY)


# ---------------------------------------------------------------------------
# Kernel fallback (pre-engine path)
# ---------------------------------------------------------------------------

def test_kernel_fallback_works_without_engine() -> None:
    section("Kernel fallback — _invoke_kernel() works when engine absent")
    # Use a simple blob that sets result
    payload = "result = context.get('x', 42)"
    h = seed.put("logic/python", payload)

    # Temporarily clear engine cache to force kernel path
    saved_engine = seed._ENGINE
    saved_hash = seed._ENGINE_HASH
    seed._ENGINE = None
    seed._ENGINE_HASH = None

    try:
        # Also need to make manifest appear to have no engine
        # We'll call _invoke_kernel directly
        result = seed._invoke_kernel(h, {"x": 99})
        check("kernel fallback returns correct result", result == 99)
    except Exception as e:
        check("kernel fallback returns correct result", False, str(e))
    finally:
        seed._ENGINE = saved_engine
        seed._ENGINE_HASH = saved_hash


# ---------------------------------------------------------------------------
# Engine blob passes Triple-Pass Review
# ---------------------------------------------------------------------------

def test_engine_blob_passes_review() -> None:
    section("Engine blob — passes Triple-Pass Review")
    engine_hash = _boot.get("engine_hash")
    if not engine_hash:
        check("engine_hash available for review", False)
        return
    try:
        promote.triple_pass_review(engine_hash, label="engine")
        check("engine blob passes triple_pass_review", True)
    except promote.ReviewError as e:
        check("engine blob passes triple_pass_review", False, f"[{e.pass_name}] {e.detail}")


def test_engine_blob_safety_scanner() -> None:
    section("Engine blob — safety scanner: no forbidden patterns")
    engine_hash = _boot.get("engine_hash")
    if not engine_hash:
        check("engine_hash available", False)
        return
    blob = seed._raw_get(engine_hash)
    payload = blob["payload"]
    import re
    _DANGEROUS_RE = re.compile(
        r"\bimport\s+os\b|\bimport\s+sys\b|\b__import__\b|\bopen\s*\("
        r"|\beval\s*\(|\bexec\s*\(|\bsubprocess\b|\bshutil\b|\bVAULT_DIR\b"
    )
    # logic/engine is exempt from the exec-forbidden check; only check the other patterns
    _OTHER_DANGEROUS_RE = re.compile(
        r"\bimport\s+os\b|\bimport\s+sys\b|\b__import__\b|\bopen\s*\("
        r"|\beval\s*\(|\bsubprocess\b|\bshutil\b|\bVAULT_DIR\b"
    )
    match = _OTHER_DANGEROUS_RE.search(payload)
    check("no non-exec forbidden patterns in engine payload", match is None,
          f"found: {match.group()!r}" if match else "")
    # f_14: engine uses exec() directly (logic/engine type exempts it from scanner)
    check("engine payload uses exec() directly", "exec(" in payload)


# ---------------------------------------------------------------------------
# Full f_13 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f13_evolution_cycle() -> None:
    section("Full f_13 evolution cycle — engine active, manifest v1.14.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f13-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f13-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f13-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f13-candidate")

    def mock_gen_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "probe"}]

    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=mock_gen_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        results = evolve.run_all()

    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.14.0", m["version"] == "1.14.0")

    # Engine still present after evolution (logic/engine key, not logic/python)
    engine_hash = m.get("blobs", {}).get("engine", {}).get("logic/engine")
    check("engine blob still in manifest after evolution", engine_hash is not None)

    # Promoted blob hashes are valid
    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)
        if lh:
            check(f"{label} vault file exists", (seed.VAULT_DIR / lh).exists())

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v13 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.14.0"]
    check("at least one v1.14.0 promote event", len(promote_v13) >= 1)


# ---------------------------------------------------------------------------
# Backward compat — prior blob types still reviewable
# ---------------------------------------------------------------------------

def test_prior_blob_types_reviewable() -> None:
    section("Backward compat — prior blob types pass Triple-Pass Review")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        if not h:
            check(f"{label} in manifest", False)
            continue
        try:
            promote.triple_pass_review(h, label=label)
            check(f"{label} passes review", True)
        except promote.ReviewError as e:
            check(f"{label} passes review", False, f"[{e.pass_name}] {e.detail}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_engine_in_vault()
    test_engine_in_manifest()
    test_invoke_delegates_to_engine()
    test_engine_invoke_executes_blob()
    test_engine_telemetry_written()
    test_kernel_fallback_works_without_engine()
    test_engine_blob_passes_review()
    test_engine_blob_safety_scanner()
    test_full_f13_evolution_cycle()
    test_prior_blob_types_reviewable()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
