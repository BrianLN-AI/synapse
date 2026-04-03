#!/usr/bin/env python3
"""
tests/test_f18.py — f_18 hash-bridge expression (ADR-015)

Covers:
  - seed.put_bridge() stores a meta/hash-bridge blob
  - put_bridge() normalizes vault_address to canonical multihash form
  - put_bridge() returns blake3:<hex> address
  - put_bridge() with proof=None stores null in record
  - put_bridge() with proof string stores it
  - seed.resolve_bridge() finds bridge by vault_address
  - seed.resolve_bridge() finds bridge by zk_address
  - seed.resolve_bridge() returns None when no bridge exists
  - promote.triple_pass_review passes for valid meta/hash-bridge blob
  - promote.triple_pass_review rejects bridge missing vault_address
  - promote.triple_pass_review rejects bridge with invalid vault_address hex
  - promote.triple_pass_review rejects bridge with empty proof string
  - promote.promote_bridge() stores bridge in manifest["bridges"]
  - promote.lookup_bridge() returns bridge record from manifest
  - promote.lookup_bridge() returns None for unknown address
  - Full f_18 evolution cycle: manifest v1.18.0
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
    print("\n── Bootstrap: f_0 + f_7 + f_18 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:24]}...")
    print(f"\n  f_0 + f_7 + f_18 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# put_bridge()
# ---------------------------------------------------------------------------

def test_put_bridge_stores_blob() -> None:
    section("put_bridge — stores meta/hash-bridge blob in vault")
    vault_addr = seed.put("logic/python", "result = 'bridge-test'")
    zk_addr    = "poseidon:" + "ab" * 32

    bridge_hash = seed.put_bridge(vault_addr, zk_addr)
    check("returns blake3:<hex>", bridge_hash.startswith("blake3:"), bridge_hash[:30])

    blob = seed._raw_get(bridge_hash)
    check("blob type is meta/hash-bridge", blob.get("type") == "meta/hash-bridge")

    record = json.loads(blob["payload"])
    check("vault_address in record", "vault_address" in record)
    check("zk_address in record", "zk_address" in record)
    check("proof is None (default)", record.get("proof") is None)


def test_put_bridge_normalizes_vault_address() -> None:
    section("put_bridge — normalizes vault_address to canonical blake3:<hex>")
    bare = "a" * 64
    vault_addr = f"blake3:{bare}"
    bridge_hash = seed.put_bridge(vault_addr, "poseidon:" + "0" * 64)
    blob = seed._raw_get(bridge_hash)
    record = json.loads(blob["payload"])
    check("vault_address stored as blake3:<hex>",
          record["vault_address"] == vault_addr, record["vault_address"])


def test_put_bridge_bare_hex_normalized() -> None:
    section("put_bridge — bare hex vault_address normalized to blake3:<hex>")
    bare = "b" * 64
    bridge_hash = seed.put_bridge(bare, "poseidon:" + "0" * 64)
    blob = seed._raw_get(bridge_hash)
    record = json.loads(blob["payload"])
    check("bare hex normalized to blake3:<hex>",
          record["vault_address"] == f"blake3:{bare}", record["vault_address"])


def test_put_bridge_with_proof() -> None:
    section("put_bridge — stores proof string when provided")
    vault_addr  = "blake3:" + "c" * 64
    proof_str   = "pi_a=...,pi_b=...,pi_c=..."
    bridge_hash = seed.put_bridge(vault_addr, "poseidon:" + "0" * 64, proof=proof_str)
    blob   = seed._raw_get(bridge_hash)
    record = json.loads(blob["payload"])
    check("proof stored correctly", record.get("proof") == proof_str)


# ---------------------------------------------------------------------------
# resolve_bridge()
# ---------------------------------------------------------------------------

def test_resolve_bridge_by_vault_address() -> None:
    section("resolve_bridge — finds bridge by vault_address")
    vault_addr  = "blake3:" + "d" * 64
    zk_addr     = "poseidon:" + "e" * 64
    seed.put_bridge(vault_addr, zk_addr)

    record = seed.resolve_bridge(vault_addr)
    check("bridge found by vault_address", record is not None)
    if record:
        check("zk_address matches", record.get("zk_address") == zk_addr)


def test_resolve_bridge_by_zk_address() -> None:
    section("resolve_bridge — finds bridge by zk_address")
    vault_addr = "blake3:" + "f" * 64
    zk_addr    = "poseidon:unique" + "1" * 57
    seed.put_bridge(vault_addr, zk_addr)

    record = seed.resolve_bridge(zk_addr)
    check("bridge found by zk_address", record is not None)
    if record:
        check("vault_address matches", record.get("vault_address") == vault_addr)


def test_resolve_bridge_returns_none_when_absent() -> None:
    section("resolve_bridge — returns None when no bridge exists")
    unknown = "blake3:" + "9" * 64
    result = seed.resolve_bridge(unknown)
    check("returns None for unknown address", result is None)


def test_resolve_bridge_by_bare_hex() -> None:
    section("resolve_bridge — finds bridge when queried with bare hex")
    bare        = "1" * 64
    vault_addr  = f"blake3:{bare}"
    zk_addr     = "poseidon:" + "2" * 64
    seed.put_bridge(vault_addr, zk_addr)

    record = seed.resolve_bridge(bare)   # bare hex lookup
    check("bridge found with bare hex query", record is not None)


# ---------------------------------------------------------------------------
# triple_pass_review validates meta/hash-bridge
# ---------------------------------------------------------------------------

def test_review_passes_valid_bridge() -> None:
    section("triple_pass_review — passes valid meta/hash-bridge")
    vault_addr  = "blake3:" + "aa" * 32
    bridge_hash = seed.put_bridge(vault_addr, "poseidon:" + "bb" * 32)
    try:
        promote.triple_pass_review(bridge_hash)
        check("valid bridge passes review", True)
    except promote.ReviewError as e:
        check("valid bridge passes review", False, f"[{e.pass_name}] {e.detail}")


def test_review_rejects_missing_vault_address() -> None:
    section("triple_pass_review — rejects bridge missing vault_address")
    bad_payload = json.dumps({"zk_address": "poseidon:" + "0" * 64, "proof": None})
    h = seed.put("meta/hash-bridge", bad_payload)
    try:
        promote.triple_pass_review(h)
        check("missing vault_address rejected", False, "no error raised")
    except promote.ReviewError as e:
        check("missing vault_address rejected",
              e.pass_name == "StaticAnalysis", f"[{e.pass_name}] {e.detail}")


def test_review_rejects_invalid_vault_address() -> None:
    section("triple_pass_review — rejects bridge with non-hex vault_address")
    bad_payload = json.dumps({
        "vault_address": "blake3:not-hex-at-all",
        "zk_address": "poseidon:" + "0" * 64,
        "proof": None,
    })
    h = seed.put("meta/hash-bridge", bad_payload)
    try:
        promote.triple_pass_review(h)
        check("invalid vault_address hex rejected", False, "no error raised")
    except promote.ReviewError as e:
        check("invalid vault_address hex rejected",
              e.pass_name == "StaticAnalysis", f"[{e.pass_name}] {e.detail}")


def test_review_rejects_empty_proof_string() -> None:
    section("triple_pass_review — rejects bridge with empty proof string")
    bad_payload = json.dumps({
        "vault_address": "blake3:" + "cc" * 32,
        "zk_address":    "poseidon:" + "dd" * 32,
        "proof":         "   ",    # whitespace-only string
    })
    h = seed.put("meta/hash-bridge", bad_payload)
    try:
        promote.triple_pass_review(h)
        check("empty proof string rejected", False, "no error raised")
    except promote.ReviewError as e:
        check("empty proof string rejected",
              e.pass_name == "StaticAnalysis", f"[{e.pass_name}] {e.detail}")


# ---------------------------------------------------------------------------
# promote_bridge() and lookup_bridge()
# ---------------------------------------------------------------------------

def test_promote_bridge_stores_in_manifest() -> None:
    section("promote_bridge — stores bridge hash in manifest[bridges]")
    vault_addr  = seed.put("logic/python", "result = 'promoted-bridge-test'")
    zk_addr     = "poseidon:" + "ee" * 32
    bridge_hash = seed.put_bridge(vault_addr, zk_addr)

    reviewer_hash = _boot.get("bootstrap_reviewer_hash") or _boot.get("evolve_reviewer_hash")
    approval_hash = promote.issue_council_approval([bridge_hash], reviewer_hash=reviewer_hash)

    promote.promote_bridge(bridge_hash, approval_hash)

    m = promote.load_manifest()
    canonical_vault = f"blake3:{seed._to_bare_hex(vault_addr)}"
    stored = m.get("bridges", {}).get(canonical_vault)
    check("bridge stored in manifest[bridges]", stored == bridge_hash,
          f"expected {bridge_hash[:16]}..., got {str(stored)[:16]}")


def test_lookup_bridge_returns_record() -> None:
    section("lookup_bridge — returns bridge record from manifest")
    vault_addr  = seed.put("logic/python", "result = 'lookup-bridge-test'")
    zk_addr     = "poseidon:" + "ff" * 32
    bridge_hash = seed.put_bridge(vault_addr, zk_addr)

    reviewer_hash = _boot.get("bootstrap_reviewer_hash") or _boot.get("evolve_reviewer_hash")
    approval_hash = promote.issue_council_approval([bridge_hash], reviewer_hash=reviewer_hash)
    promote.promote_bridge(bridge_hash, approval_hash)

    record = promote.lookup_bridge(vault_addr)
    check("lookup_bridge returns record", record is not None)
    if record:
        check("record contains zk_address", record.get("zk_address") == zk_addr)


def test_lookup_bridge_returns_none_unknown() -> None:
    section("lookup_bridge — returns None for unregistered address")
    unknown = "blake3:" + "7" * 64
    result = promote.lookup_bridge(unknown)
    check("returns None for unknown address", result is None)


# ---------------------------------------------------------------------------
# Audit log records bridge promotion
# ---------------------------------------------------------------------------

def test_promote_bridge_writes_audit_log() -> None:
    section("promote_bridge — writes promote_bridge event to audit log")
    vault_addr  = seed.put("logic/python", "result = 'audit-bridge-test'")
    zk_addr     = "poseidon:" + "12" * 32
    bridge_hash = seed.put_bridge(vault_addr, zk_addr)

    reviewer_hash = _boot.get("bootstrap_reviewer_hash") or _boot.get("evolve_reviewer_hash")
    approval_hash = promote.issue_council_approval([bridge_hash], reviewer_hash=reviewer_hash)
    promote.promote_bridge(bridge_hash, approval_hash)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    bridge_events = [e for e in entries if e.get("event") == "promote_bridge"]
    check("promote_bridge event in audit log", len(bridge_events) >= 1)
    if bridge_events:
        ev = bridge_events[-1]
        check("event has vault_address", "vault_address" in ev)
        check("event has zk_address",    "zk_address" in ev)
        check("event has bridge_hash",   ev.get("bridge_hash") == bridge_hash)


# ---------------------------------------------------------------------------
# Full f_18 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f18_evolution_cycle() -> None:
    section("Full f_18 evolution cycle — manifest v1.18.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f18-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f18-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f18-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f18-candidate")

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
    check("manifest version 1.18.0", m["version"] == "1.18.0")

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v18 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.18.0"]
    check("at least one v1.18.0 promote event", len(promote_v18) >= 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_put_bridge_stores_blob()
    test_put_bridge_normalizes_vault_address()
    test_put_bridge_bare_hex_normalized()
    test_put_bridge_with_proof()
    test_resolve_bridge_by_vault_address()
    test_resolve_bridge_by_zk_address()
    test_resolve_bridge_returns_none_when_absent()
    test_resolve_bridge_by_bare_hex()
    test_review_passes_valid_bridge()
    test_review_rejects_missing_vault_address()
    test_review_rejects_invalid_vault_address()
    test_review_rejects_empty_proof_string()
    test_promote_bridge_stores_in_manifest()
    test_lookup_bridge_returns_record()
    test_lookup_bridge_returns_none_unknown()
    test_promote_bridge_writes_audit_log()
    test_full_f18_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
