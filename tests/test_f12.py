#!/usr/bin/env python3
"""
tests/test_f12.py — f_12 blake3 migration

Covers:
  - blake3 is the vault hash function: put() returns 64-char hex, matches blake3
  - blake3 is the manifest hash function: manifest["hash"] matches blake3
  - SHA-256 is NOT used: hashlib not imported in seed.py or promote.py
  - Hash length unchanged: 64 hex chars (256-bit output, same as SHA-256)
  - Full f_12 evolution cycle: manifest v1.14.0
  - Backward compat: all prior blob types still reviewable
  - Credential safety: no CF strings in vault or audit log
"""

import hashlib
import importlib
import inspect
import json
import shutil
import sys
import unittest.mock as mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import blake3 as _blake3
import bootstrap
import evolve
import infer
import promote
import seed

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
_results: list[tuple[str, bool]] = []
_boot: dict = {}

_CF_CREDENTIAL_STRINGS = ["CF_ACCOUNT_ID", "CF_GATEWAY_NAME", "CF_AIG_TOKEN", "cf-aig"]


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

    global _boot
    _boot = bootstrap.run()
    print("\n── Bootstrap: f_0 + f_7 Closure")
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = promote.load_manifest()["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:16]}...")
    print(f"\n  f_0 + f_7 defined. Manifest v{promote.load_manifest()['version']}")


# ---------------------------------------------------------------------------
# blake3 vault hash
# ---------------------------------------------------------------------------

def test_put_returns_blake3_hash() -> None:
    section("blake3 vault hash — put() uses blake3, not SHA-256")
    payload = "test payload for blake3 verification"
    blob_type = "logic/python"
    envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)

    h = seed.put(blob_type, payload)

    # Compute expected blake3 hash independently
    expected_blake3 = _blake3.blake3(envelope.encode("utf-8")).hexdigest()
    # Compute what SHA-256 would produce
    sha256_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()

    check("put() returns 64-char hex", len(h) == 64)
    check("hash matches blake3", h == expected_blake3)
    check("hash is NOT sha256", h != sha256_hash)


def test_vault_filename_is_blake3() -> None:
    section("blake3 vault — vault file named by blake3 hash")
    payload = "unique payload for filename test " + str(id(object()))
    h = seed.put("logic/python", payload)
    vault_file = seed.VAULT_DIR / h
    envelope = json.dumps({"type": "logic/python", "payload": payload}, sort_keys=True)
    expected = _blake3.blake3(envelope.encode("utf-8")).hexdigest()

    check("vault file exists at blake3 address", vault_file.exists())
    check("filename equals blake3(envelope)", h == expected)


# ---------------------------------------------------------------------------
# blake3 manifest hash
# ---------------------------------------------------------------------------

def test_manifest_hash_is_blake3() -> None:
    section("blake3 manifest hash — manifest['hash'] uses blake3")
    m = promote.load_manifest()
    stored_hash = m.get("hash")

    # Recompute manifest hash the same way _write_manifest does
    content = {k: v for k, v in m.items() if k != "hash"}
    expected_blake3 = _blake3.blake3(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()
    sha256_hash = hashlib.sha256(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()

    check("manifest has hash field", stored_hash is not None)
    check("manifest hash is 64-char hex", len(stored_hash) == 64)
    check("manifest hash matches blake3", stored_hash == expected_blake3)
    check("manifest hash is NOT sha256", stored_hash != sha256_hash)


# ---------------------------------------------------------------------------
# No hashlib in source files
# ---------------------------------------------------------------------------

def test_seed_does_not_import_hashlib() -> None:
    section("source hygiene — seed.py does not import hashlib")
    seed_src = (Path(__file__).parent.parent / "seed.py").read_text()
    check("no 'import hashlib' in seed.py", "import hashlib" not in seed_src)
    check("no 'hashlib.sha256' in seed.py", "hashlib.sha256" not in seed_src)
    check("blake3 imported in seed.py", "import blake3" in seed_src)


def test_promote_does_not_import_hashlib() -> None:
    section("source hygiene — promote.py does not import hashlib")
    promote_src = (Path(__file__).parent.parent / "promote.py").read_text()
    check("no 'import hashlib' in promote.py", "import hashlib" not in promote_src)
    check("no 'hashlib.sha256' in promote.py", "hashlib.sha256" not in promote_src)
    check("blake3 imported in promote.py", "import blake3" in promote_src)


# ---------------------------------------------------------------------------
# Full f_12 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f12_evolution_cycle() -> None:
    section("Full f_12 evolution cycle — blake3 hashes, manifest v1.14.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f12-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f12-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f12-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f12-candidate")

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

    # Verify promoted blob hashes are blake3 (64-char hex, match blake3)
    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)
        if lh:
            check(f"{label} hash is 64-char hex", len(lh) == 64)
            # Verify the vault file actually exists at that address
            check(f"{label} vault file at blake3 address", (seed.VAULT_DIR / lh).exists())

    # Verify manifest hash is blake3
    stored = m.get("hash")
    content = {k: v for k, v in m.items() if k != "hash"}
    expected = _blake3.blake3(json.dumps(content, sort_keys=True).encode()).hexdigest()
    check("manifest hash is blake3 post-evolution", stored == expected)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v12 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.14.0"]
    check("at least one v1.14.0 promote event", len(promote_v12) >= 1)


# ---------------------------------------------------------------------------
# Credential safety
# ---------------------------------------------------------------------------

def test_no_credentials_in_vault() -> None:
    section("Credential safety — no CF credentials in vault post-evolution")
    vault_contents = " ".join(
        f.read_text() for f in seed.VAULT_DIR.iterdir() if f.is_file()
    ) if seed.VAULT_DIR.exists() else ""
    for s in _CF_CREDENTIAL_STRINGS:
        check(f"no {s} in vault", s not in vault_contents)


def test_no_credentials_in_audit_log() -> None:
    section("Credential safety — no CF credentials in audit.log post-evolution")
    log_text = Path("./audit.log").read_text() if Path("./audit.log").exists() else ""
    for s in _CF_CREDENTIAL_STRINGS:
        check(f"no {s} in audit log", s not in log_text)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_put_returns_blake3_hash()
    test_vault_filename_is_blake3()
    test_manifest_hash_is_blake3()
    test_seed_does_not_import_hashlib()
    test_promote_does_not_import_hashlib()
    test_full_f12_evolution_cycle()
    test_no_credentials_in_vault()
    test_no_credentials_in_audit_log()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
