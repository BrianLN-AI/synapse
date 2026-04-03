#!/usr/bin/env python3
"""
tests/test_f19.py — f_19 federation: cross-vault blob resolution

Covers:
  - promote.register_peer() stores peer URL in manifest["federation"]["peers"]
  - register_peer() is idempotent (duplicate URL not added twice)
  - promote.list_peers() returns registered peer URLs
  - promote.remove_peer() removes peer, returns True
  - promote.remove_peer() returns False for unknown URL
  - register_peer() writes register_peer audit log entry
  - remove_peer() writes remove_peer audit log entry
  - Discovery V9 resolves from L1 normally (no peers queried)
  - Discovery V9 fetches from federation peer when L1 missing
  - Discovery V9 verifies content hash (rejects tampered response)
  - Discovery V9 caches fetched blob in L1 vault
  - Discovery V9 tries next peer if first peer raises URLError
  - Discovery V9 raises FileNotFoundError when all peers fail
  - Full f_19 evolution cycle: manifest v1.19.0
"""

import json
import shutil
import sys
import unittest.mock as mock
from pathlib import Path
from urllib.error import URLError

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
    print("\n── Bootstrap: f_0 + f_7 + f_18 + f_19 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:24]}...")
    print(f"\n  f_0 + f_7 + f_18 + f_19 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# register_peer / list_peers / remove_peer
# ---------------------------------------------------------------------------

def test_register_peer_stores_in_manifest() -> None:
    section("register_peer — stores peer URL in manifest[federation][peers]")
    url = "https://vault-alpha.example.com"
    promote.register_peer(url)

    peers = promote.list_peers()
    check("peer stored in manifest", url in peers, str(peers))


def test_register_peer_idempotent() -> None:
    section("register_peer — idempotent: duplicate URL not added twice")
    url = "https://vault-beta.example.com"
    promote.register_peer(url)
    promote.register_peer(url)

    peers = promote.list_peers()
    count = sum(1 for p in peers if p == url)
    check("URL appears exactly once", count == 1, f"count={count}")


def test_list_peers_returns_all() -> None:
    section("list_peers — returns all registered peers")
    # register two fresh peers
    promote.register_peer("https://peer-x.example.com")
    promote.register_peer("https://peer-y.example.com")

    peers = promote.list_peers()
    check("at least two peers registered", len(peers) >= 2, str(peers))


def test_remove_peer_returns_true() -> None:
    section("remove_peer — returns True and removes the URL")
    url = "https://vault-to-remove.example.com"
    promote.register_peer(url)

    result = promote.remove_peer(url)
    check("remove_peer returns True", result is True)

    peers = promote.list_peers()
    check("URL no longer in peers", url not in peers)


def test_remove_peer_returns_false_unknown() -> None:
    section("remove_peer — returns False for unregistered URL")
    unknown = "https://does-not-exist.example.com"
    result = promote.remove_peer(unknown)
    check("remove_peer returns False for unknown", result is False)


def test_register_peer_writes_audit_log() -> None:
    section("register_peer — writes register_peer event to audit log")
    url = "https://audit-log-peer.example.com"
    promote.register_peer(url)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    events = [e for e in entries if e.get("event") == "register_peer" and e.get("url") == url]
    check("register_peer event in audit log", len(events) >= 1)


def test_remove_peer_writes_audit_log() -> None:
    section("remove_peer — writes remove_peer event to audit log")
    url = "https://audit-log-remove.example.com"
    promote.register_peer(url)
    promote.remove_peer(url)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    events = [e for e in entries if e.get("event") == "remove_peer" and e.get("url") == url]
    check("remove_peer event in audit log", len(events) >= 1)


# ---------------------------------------------------------------------------
# Discovery V9 — federation resolution
# ---------------------------------------------------------------------------

def _put_blob_raw(blob_type: str, payload: str) -> tuple[str, bytes]:
    """Store a blob and return (bare_hex, raw_json_bytes)."""
    import blake3 as _blake3
    envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
    raw = envelope.encode("utf-8")
    bare_hex = _blake3.blake3(raw).hexdigest()
    blob_path = seed.VAULT_DIR / bare_hex
    seed.VAULT_DIR.mkdir(parents=True, exist_ok=True)
    blob_path.write_bytes(raw)
    return bare_hex, raw


def _promote_discovery_v9() -> str:
    """Promote DISCOVERY_V9 so it is the active discovery blob."""
    reviewer_hash = _boot.get("bootstrap_reviewer_hash") or _boot.get("evolve_reviewer_hash")
    v9_hash = seed.put("logic/python", evolve.DISCOVERY_V9)
    promote.triple_pass_review(v9_hash)
    approval = promote.issue_council_approval([v9_hash], reviewer_hash=reviewer_hash)
    promote.promote(
        label="discovery",
        blob_hashes=[v9_hash],
        council_approval_hash=approval,
        version="1.19.0",
    )
    return v9_hash


def test_discovery_v9_resolves_from_l1() -> None:
    section("Discovery V9 — resolves blob from L1 (no peers queried)")
    v9_hash = _promote_discovery_v9()

    bare_hex, _ = _put_blob_raw("logic/python", "result = 'l1-only'")

    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        result = seed.invoke(v9_hash, {
            "hash": f"blake3:{bare_hex}",
            "vault_dir": str(seed.VAULT_DIR),
        })
        check("L1 resolve succeeds", result.get("type") == "logic/python")
        check("urlopen not called for L1", not mock_urlopen.called)


def test_discovery_v9_fetches_from_federation_peer() -> None:
    section("Discovery V9 — fetches blob from federation peer")
    v9_hash = _promote_discovery_v9()

    # Create a blob that does NOT exist in the local vault
    import blake3 as _blake3
    payload = "result = 'from-federation-peer'"
    envelope = json.dumps({"type": "logic/python", "payload": payload}, sort_keys=True)
    raw = envelope.encode("utf-8")
    bare_hex = _blake3.blake3(raw).hexdigest()

    # Ensure it's NOT in the local vault
    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    def mock_urlopen(url, timeout=5):
        resp = mock.MagicMock()
        resp.read.return_value = raw
        resp.__enter__ = lambda s: s
        resp.__exit__ = mock.MagicMock(return_value=False)
        return resp

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        result = seed.invoke(v9_hash, {
            "hash": f"blake3:{bare_hex}",
            "vault_dir": str(seed.VAULT_DIR),
            "vault_federation_peers": ["https://peer-a.example.com"],
        })
    check("result fetched via federation peer", result.get("type") == "logic/python")


def test_discovery_v9_rejects_tampered_response() -> None:
    section("Discovery V9 — rejects blob with hash mismatch from peer")
    v9_hash = _promote_discovery_v9()

    import blake3 as _blake3
    real_payload = "result = 'original'"
    envelope = json.dumps({"type": "logic/python", "payload": real_payload}, sort_keys=True)
    bare_hex = _blake3.blake3(envelope.encode()).hexdigest()

    # Ensure not in L1
    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    # Peer returns tampered data
    tampered = b'{"type": "logic/python", "payload": "result = \'tampered\'"}'

    def mock_urlopen(url, timeout=5):
        resp = mock.MagicMock()
        resp.read.return_value = tampered
        resp.__enter__ = lambda s: s
        resp.__exit__ = mock.MagicMock(return_value=False)
        return resp

    raised = False
    try:
        with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
            seed.invoke(v9_hash, {
                "hash": f"blake3:{bare_hex}",
                "vault_dir": str(seed.VAULT_DIR),
                "vault_federation_peers": ["https://peer-tamper.example.com"],
            })
    except (FileNotFoundError, RuntimeError):
        raised = True
    check("tampered response raises error", raised)


def test_discovery_v9_caches_fetched_blob() -> None:
    section("Discovery V9 — caches blob in L1 after federation fetch")
    v9_hash = _promote_discovery_v9()

    import blake3 as _blake3
    payload = "result = 'to-be-cached'"
    envelope = json.dumps({"type": "logic/python", "payload": payload}, sort_keys=True)
    raw = envelope.encode("utf-8")
    bare_hex = _blake3.blake3(raw).hexdigest()

    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    def mock_urlopen(url, timeout=5):
        resp = mock.MagicMock()
        resp.read.return_value = raw
        resp.__enter__ = lambda s: s
        resp.__exit__ = mock.MagicMock(return_value=False)
        return resp

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        seed.invoke(v9_hash, {
            "hash": f"blake3:{bare_hex}",
            "vault_dir": str(seed.VAULT_DIR),
            "vault_federation_peers": ["https://peer-cache.example.com"],
        })

    check("blob cached in L1 after peer fetch", local_path.exists())


def test_discovery_v9_tries_next_peer_on_error() -> None:
    section("Discovery V9 — tries next peer after URLError from first peer")
    v9_hash = _promote_discovery_v9()

    import blake3 as _blake3
    payload = "result = 'found-on-second-peer'"
    envelope = json.dumps({"type": "logic/python", "payload": payload}, sort_keys=True)
    raw = envelope.encode("utf-8")
    bare_hex = _blake3.blake3(raw).hexdigest()

    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    call_count = [0]

    def mock_urlopen(url, timeout=5):
        call_count[0] += 1
        if call_count[0] == 1:
            raise URLError("peer-1 down")
        resp = mock.MagicMock()
        resp.read.return_value = raw
        resp.__enter__ = lambda s: s
        resp.__exit__ = mock.MagicMock(return_value=False)
        return resp

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        result = seed.invoke(v9_hash, {
            "hash": f"blake3:{bare_hex}",
            "vault_dir": str(seed.VAULT_DIR),
            "vault_federation_peers": [
                "https://peer-1-down.example.com",
                "https://peer-2-up.example.com",
            ],
        })
    check("blob resolved from second peer after first fails",
          result.get("type") == "logic/python")
    check("both peers were tried", call_count[0] >= 2)


def test_discovery_v9_raises_when_all_peers_fail() -> None:
    section("Discovery V9 — raises FileNotFoundError when all peers fail")
    v9_hash = _promote_discovery_v9()

    import blake3 as _blake3
    bare_hex = "a" * 64  # unlikely to be in vault

    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    def mock_urlopen(url, timeout=5):
        raise URLError("all peers down")

    raised = False
    try:
        with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
            seed.invoke(v9_hash, {
                "hash": f"blake3:{bare_hex}",
                "vault_dir": str(seed.VAULT_DIR),
                "vault_federation_peers": [
                    "https://peer-down-1.example.com",
                    "https://peer-down-2.example.com",
                ],
            })
    except (FileNotFoundError, RuntimeError):
        raised = True
    check("FileNotFoundError raised when all peers fail", raised)


# ---------------------------------------------------------------------------
# Full f_19 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f19_evolution_cycle() -> None:
    section("Full f_19 evolution cycle — manifest v1.19.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V9,
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f19-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f19-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f19-candidate")

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
    check("manifest version 1.19.0", m["version"] == "1.19.0")

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v19 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.19.0"]
    check("at least one v1.19.0 promote event", len(promote_v19) >= 1)

    # Verify the promoted discovery blob is V9 (has federation peer support)
    disc_hash = m["blobs"].get("discovery", {}).get("logic/python")
    if disc_hash:
        disc_blob = seed._raw_get(disc_hash)
        check("promoted discovery has vault_federation_peers support",
              "vault_federation_peers" in disc_blob["payload"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_register_peer_stores_in_manifest()
    test_register_peer_idempotent()
    test_list_peers_returns_all()
    test_remove_peer_returns_true()
    test_remove_peer_returns_false_unknown()
    test_register_peer_writes_audit_log()
    test_remove_peer_writes_audit_log()
    test_discovery_v9_resolves_from_l1()
    test_discovery_v9_fetches_from_federation_peer()
    test_discovery_v9_rejects_tampered_response()
    test_discovery_v9_caches_fetched_blob()
    test_discovery_v9_tries_next_peer_on_error()
    test_discovery_v9_raises_when_all_peers_fail()
    test_full_f19_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
