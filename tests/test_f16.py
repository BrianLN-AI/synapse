#!/usr/bin/env python3
"""
tests/test_f16.py — f_16 multihash address format (ADR-015)

Covers:
  - seed._to_bare_hex() strips function prefix
  - seed._to_multihash() adds blake3: prefix
  - seed._to_multihash() is idempotent
  - seed.put() returns blake3:<hex> address
  - seed.put() is idempotent: same content → same address
  - seed._raw_get() accepts blake3:<hex> address
  - seed._raw_get() accepts bare hex address (backward compat)
  - seed._raw_get() raises FileNotFoundError for unknown hash (both forms)
  - seed._invoke_kernel() accepts blake3:<hex> hash
  - seed._invoke_kernel() accepts bare hex hash (backward compat)
  - seed._load_engine() works with blake3:<hex> manifest entries
  - seed.invoke() delegates to engine with blake3:<hex> hashes
  - promote.triple_pass_review() accepts blake3:<hex> hash
  - promote._verify_council_approval() handles mixed bare/prefixed hashes
  - Full bootstrap: all returned hashes are blake3:<hex>
  - Full f_16 evolution cycle: manifest v1.16.0
  - Vault files stored under bare hex names (no colon in filename)
"""

import json
import re
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

BLAKE3_PREFIX_RE = re.compile(r"^blake3:[0-9a-f]{64}$")
BARE_HEX_RE      = re.compile(r"^[0-9a-f]{64}$")


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


def setup() -> None:
    for d in [seed.VAULT_DIR, seed.BYTECODE_DIR]:
        if d.exists():
            shutil.rmtree(d)
    if promote.MANIFEST_PATH.exists():
        promote.MANIFEST_PATH.unlink()
    if Path("audit.log").exists():
        Path("audit.log").unlink()

    seed._ENGINE = None
    seed._ENGINE_HASH = None

    global _boot
    _boot = bootstrap.run()
    print("\n── Bootstrap: f_0 + f_7 + f_16 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:24]}...")
    engine_h = m["blobs"].get("engine", {}).get("logic/engine", "MISSING")
    print(f"  engine (logic/engine)      manifest.hash={engine_h[:24]}...")
    print(f"\n  f_0 + f_7 + f_16 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# Address helpers
# ---------------------------------------------------------------------------

def test_to_bare_hex_strips_prefix() -> None:
    section("_to_bare_hex — strips function prefix")
    bare = "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
    check("blake3: prefix stripped", seed._to_bare_hex(f"blake3:{bare}") == bare)
    check("sha256: prefix stripped", seed._to_bare_hex(f"sha256:{bare}") == bare)
    check("bare hex unchanged",      seed._to_bare_hex(bare) == bare)


def test_to_multihash_adds_prefix() -> None:
    section("_to_multihash — adds blake3: prefix")
    bare = "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
    result = seed._to_multihash(bare)
    check("result starts with blake3:", result.startswith("blake3:"))
    check("result has correct bare hex", result == f"blake3:{bare}")


def test_to_multihash_idempotent() -> None:
    section("_to_multihash — idempotent on already-prefixed address")
    addr = "blake3:af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
    check("idempotent", seed._to_multihash(addr) == addr)


# ---------------------------------------------------------------------------
# put() returns multihash address
# ---------------------------------------------------------------------------

def test_put_returns_multihash() -> None:
    section("put() — returns blake3:<hex> address")
    h = seed.put("logic/python", "result = 42")
    check("returns blake3: prefix", bool(BLAKE3_PREFIX_RE.match(h)), h)
    check("64-char hex after prefix", len(h) == len("blake3:") + 64)


def test_put_idempotent() -> None:
    section("put() — idempotent: same content → same address")
    h1 = seed.put("logic/python", "result = 99")
    h2 = seed.put("logic/python", "result = 99")
    check("same address for same content", h1 == h2)


def test_put_vault_file_uses_bare_hex() -> None:
    section("put() — vault file stored under bare hex (no colon in filename)")
    h = seed.put("logic/python", "result = 'vault-path-check'")
    bare = seed._to_bare_hex(h)
    bare_path = seed.VAULT_DIR / bare
    prefixed_path = seed.VAULT_DIR / h   # would include colon — should NOT exist
    check("vault file at bare hex path exists", bare_path.exists())
    check("vault file at prefixed path does NOT exist", not prefixed_path.exists(),
          "colon in filename" if prefixed_path.exists() else "")


# ---------------------------------------------------------------------------
# _raw_get() accepts both forms
# ---------------------------------------------------------------------------

def test_raw_get_accepts_multihash() -> None:
    section("_raw_get — accepts blake3:<hex> address")
    h = seed.put("logic/python", "result = 'multihash-get-test'")
    check("h is prefixed", bool(BLAKE3_PREFIX_RE.match(h)), h)
    blob = seed._raw_get(h)
    check("blob retrieved with prefixed address", blob.get("payload") == "result = 'multihash-get-test'")


def test_raw_get_accepts_bare_hex() -> None:
    section("_raw_get — accepts bare hex address (backward compat)")
    h = seed.put("logic/python", "result = 'bare-hex-get-test'")
    bare = seed._to_bare_hex(h)
    check("bare is 64-char hex", bool(BARE_HEX_RE.match(bare)), bare)
    blob = seed._raw_get(bare)
    check("blob retrieved with bare hex address", blob.get("payload") == "result = 'bare-hex-get-test'")


def test_raw_get_raises_for_unknown() -> None:
    section("_raw_get — raises FileNotFoundError for unknown hash")
    fake_bare = "0" * 64
    try:
        seed._raw_get(fake_bare)
        check("raises for unknown bare hex", False, "no exception raised")
    except FileNotFoundError:
        check("raises for unknown bare hex", True)

    fake_prefixed = f"blake3:{'0' * 64}"
    try:
        seed._raw_get(fake_prefixed)
        check("raises for unknown blake3: address", False, "no exception raised")
    except FileNotFoundError:
        check("raises for unknown blake3: address", True)


# ---------------------------------------------------------------------------
# _invoke_kernel() accepts both forms
# ---------------------------------------------------------------------------

def test_invoke_kernel_accepts_multihash() -> None:
    section("_invoke_kernel — accepts blake3:<hex> hash")
    h = seed.put("logic/python", "result = context.get('x', 7)")
    check("h is prefixed", bool(BLAKE3_PREFIX_RE.match(h)), h)

    saved_engine = seed._ENGINE
    saved_hash   = seed._ENGINE_HASH
    seed._ENGINE = None
    seed._ENGINE_HASH = None
    try:
        result = seed._invoke_kernel(h, {"x": 42})
        check("invoke with prefixed hash returns correct result", result == 42, str(result))
    except Exception as e:
        check("invoke with prefixed hash returns correct result", False, str(e))
    finally:
        seed._ENGINE = saved_engine
        seed._ENGINE_HASH = saved_hash


def test_invoke_kernel_accepts_bare_hex() -> None:
    section("_invoke_kernel — accepts bare hex hash (backward compat)")
    h = seed.put("logic/python", "result = context.get('y', 0)")
    bare = seed._to_bare_hex(h)

    saved_engine = seed._ENGINE
    saved_hash   = seed._ENGINE_HASH
    seed._ENGINE = None
    seed._ENGINE_HASH = None
    try:
        result = seed._invoke_kernel(bare, {"y": 77})
        check("invoke with bare hex returns correct result", result == 77, str(result))
    except Exception as e:
        check("invoke with bare hex returns correct result", False, str(e))
    finally:
        seed._ENGINE = saved_engine
        seed._ENGINE_HASH = saved_hash


# ---------------------------------------------------------------------------
# Bootstrap hashes are all blake3:<hex>
# ---------------------------------------------------------------------------

def test_bootstrap_hashes_are_multihash() -> None:
    section("Bootstrap — all blob hashes returned by bootstrap are blake3:<hex>")
    # manifest_hash is the manifest file's own checksum (not a blob address) — skip it
    skip_keys = {"manifest_hash"}
    for key, value in _boot.items():
        if key in skip_keys:
            continue
        if isinstance(value, str) and len(value) > 10:
            is_prefixed = bool(BLAKE3_PREFIX_RE.match(value))
            check(f"bootstrap[{key}] is blake3:<hex>", is_prefixed, value[:30])


def test_manifest_blob_hashes_are_multihash() -> None:
    section("Manifest — all blob hashes stored as blake3:<hex>")
    m = promote.load_manifest()
    for label, entry in m.get("blobs", {}).items():
        for blob_type, h in entry.items():
            if isinstance(h, str):
                is_prefixed = bool(BLAKE3_PREFIX_RE.match(h))
                check(f"manifest.blobs.{label}.{blob_type} is blake3:<hex>",
                      is_prefixed, h[:30])


# ---------------------------------------------------------------------------
# triple_pass_review accepts multihash
# ---------------------------------------------------------------------------

def test_triple_pass_review_accepts_multihash() -> None:
    section("triple_pass_review — accepts blake3:<hex> hash")
    h = seed.put("logic/python", "result = {'ok': True}")
    check("h is prefixed", bool(BLAKE3_PREFIX_RE.match(h)), h)
    try:
        promote.triple_pass_review(h)
        check("triple_pass_review passes with blake3: hash", True)
    except promote.ReviewError as e:
        check("triple_pass_review passes with blake3: hash", False, f"[{e.pass_name}] {e.detail}")


# ---------------------------------------------------------------------------
# _verify_council_approval handles mixed forms
# ---------------------------------------------------------------------------

def test_verify_council_approval_handles_mixed_hashes() -> None:
    section("_verify_council_approval — mixed bare/prefixed hashes normalized")
    h = seed.put("logic/python", "result = 'mixed-hash-test'")
    m = promote.load_manifest()
    # Find a promoted reviewer hash
    reviewer_hash = _boot.get("evolve_reviewer_hash")
    if not reviewer_hash:
        check("evolve_reviewer_hash available", False)
        return

    # Issue approval with prefixed hash
    approval_hash = promote.issue_council_approval([h], reviewer_hash=reviewer_hash)

    # Verify using bare hex form of the blob hash — should still pass
    bare_h = seed._to_bare_hex(h)
    try:
        promote._verify_council_approval(approval_hash, [bare_h])
        check("approval verifies with bare hex blob hash", True)
    except ValueError as e:
        check("approval verifies with bare hex blob hash", False, str(e))

    # Verify using prefixed form — should also pass
    try:
        promote._verify_council_approval(approval_hash, [h])
        check("approval verifies with blake3: blob hash", True)
    except ValueError as e:
        check("approval verifies with blake3: blob hash", False, str(e))


# ---------------------------------------------------------------------------
# invoke() routes through engine with multihash addresses
# ---------------------------------------------------------------------------

def test_invoke_via_engine_with_multihash() -> None:
    section("invoke() — delegates to engine with blake3:<hex> hashes")
    m = promote.load_manifest()
    discovery_hash = m["blobs"]["discovery"]["logic/python"]
    check("discovery_hash is blake3:<hex>", bool(BLAKE3_PREFIX_RE.match(discovery_hash)),
          discovery_hash[:30])
    result = seed.invoke(discovery_hash, {
        "hash": discovery_hash,
        "vault_dir": str(seed.VAULT_DIR),
    })
    check("invoke returns dict", isinstance(result, dict))
    check("result has type key", "type" in result)


# ---------------------------------------------------------------------------
# Full f_16 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f16_evolution_cycle() -> None:
    section("Full f_16 evolution cycle — manifest v1.16.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f16-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f16-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f16-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f16-candidate")

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
    check("manifest version 1.16.0", m["version"] == "1.16.0")

    # All promoted hashes in manifest are blake3:<hex>
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} hash is blake3:<hex>",
              h is not None and bool(BLAKE3_PREFIX_RE.match(h)),
              str(h)[:30] if h else "missing")

    engine_hash = m.get("blobs", {}).get("engine", {}).get("logic/engine")
    check("engine hash is blake3:<hex>",
          engine_hash is not None and bool(BLAKE3_PREFIX_RE.match(engine_hash)),
          str(engine_hash)[:30] if engine_hash else "missing")

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v16 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.16.0"]
    check("at least one v1.16.0 promote event", len(promote_v16) >= 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_to_bare_hex_strips_prefix()
    test_to_multihash_adds_prefix()
    test_to_multihash_idempotent()
    test_put_returns_multihash()
    test_put_idempotent()
    test_put_vault_file_uses_bare_hex()
    test_raw_get_accepts_multihash()
    test_raw_get_accepts_bare_hex()
    test_raw_get_raises_for_unknown()
    test_invoke_kernel_accepts_multihash()
    test_invoke_kernel_accepts_bare_hex()
    test_bootstrap_hashes_are_multihash()
    test_manifest_blob_hashes_are_multihash()
    test_triple_pass_review_accepts_multihash()
    test_verify_council_approval_handles_mixed_hashes()
    test_invoke_via_engine_with_multihash()
    test_full_f16_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
