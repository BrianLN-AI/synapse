#!/usr/bin/env python3
"""
tests/test_f17.py — f_17 remote vault tier in Discovery

Covers:
  - Discovery resolves from L1 (local vault) as before
  - Discovery falls back to remote when L1 misses and vault_url_remote is set
  - Discovery verifies content hash of remote fetch (rejects tampered content)
  - Discovery caches remote fetch to local vault
  - Discovery raises FileNotFoundError when L1 misses and no remote configured
  - Discovery raises when remote returns wrong hash (tampered)
  - Discovery raises when remote URL is unreachable
  - Full bootstrap: discovery blob has remote tier (triple_pass_review passes)
  - DISCOVERY_V8 in evolve.py has same remote tier behavior
  - Full f_17 evolution cycle: manifest v1.17.0
"""

import json
import shutil
import sys
import unittest.mock as mock
from io import BytesIO
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
    print("\n── Bootstrap: f_0 + f_7 + f_17 Closure")
    m = promote.load_manifest()
    for label in ["discovery", "planning", "telemetry-reader"]:
        h = m["blobs"][label]["logic/python"]
        print(f"  promoted {label:<25} manifest.hash={h[:24]}...")
    print(f"\n  f_0 + f_7 + f_17 defined. Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# Discovery L1 path (unchanged)
# ---------------------------------------------------------------------------

def test_discovery_l1_still_works() -> None:
    section("Discovery — L1 (local vault) path unchanged")
    m = promote.load_manifest()
    discovery_hash = m["blobs"]["discovery"]["logic/python"]
    result = seed.invoke(discovery_hash, {
        "hash": discovery_hash,
        "vault_dir": str(seed.VAULT_DIR),
    })
    check("L1 resolve returns dict", isinstance(result, dict))
    check("result has type key", "type" in result)


def test_discovery_no_remote_raises_on_miss() -> None:
    section("Discovery — no vault_url_remote → FileNotFoundError on L1 miss")
    fake_hash = "blake3:" + "a" * 64
    try:
        seed.invoke(_boot["discovery"], {
            "hash": fake_hash,
            "vault_dir": str(seed.VAULT_DIR),
            # no vault_url_remote
        })
        check("raises FileNotFoundError without remote", False, "no exception raised")
    except FileNotFoundError:
        check("raises FileNotFoundError without remote", True)
    except Exception as e:
        check("raises FileNotFoundError without remote", False, type(e).__name__ + ": " + str(e))


# ---------------------------------------------------------------------------
# Remote tier — happy path
# ---------------------------------------------------------------------------

def test_discovery_remote_fetch_and_cache() -> None:
    section("Discovery — remote tier: fetch, verify, cache locally")
    # Create a blob that is NOT in local vault
    envelope_content = json.dumps({"type": "logic/python", "payload": "result = 'remote-blob'"}, sort_keys=True)
    envelope_bytes   = envelope_content.encode("utf-8")

    import blake3 as _blake3
    bare_hex = _blake3.blake3(envelope_bytes).hexdigest()
    remote_hash = f"blake3:{bare_hex}"

    # Ensure blob is NOT in local vault
    local_path = seed.VAULT_DIR / bare_hex
    if local_path.exists():
        local_path.unlink()

    # Mock urlopen to return the blob bytes
    class _MockResponse:
        def read(self): return envelope_bytes
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with mock.patch("urllib.request.urlopen", return_value=_MockResponse()):
        result = seed.invoke(_boot["discovery"], {
            "hash": remote_hash,
            "vault_dir": str(seed.VAULT_DIR),
            "vault_url_remote": "http://mock-remote-vault",
        })

    check("remote fetch returns correct blob", result.get("payload") == "result = 'remote-blob'")
    check("blob cached in local vault after remote fetch", local_path.exists())


def test_discovery_remote_cache_serves_l1_on_retry() -> None:
    section("Discovery — cached remote blob served from L1 on second call")
    # Run test_discovery_remote_fetch_and_cache first to populate cache
    envelope_content = json.dumps({"type": "logic/python", "payload": "result = 'remote-blob'"}, sort_keys=True)
    envelope_bytes   = envelope_content.encode("utf-8")
    import blake3 as _blake3
    bare_hex = _blake3.blake3(envelope_bytes).hexdigest()
    remote_hash = f"blake3:{bare_hex}"
    local_path = seed.VAULT_DIR / bare_hex

    if not local_path.exists():
        # Cache it first
        class _MockResponse:
            def read(self): return envelope_bytes
            def __enter__(self): return self
            def __exit__(self, *a): pass
        with mock.patch("urllib.request.urlopen", return_value=_MockResponse()):
            seed.invoke(_boot["discovery"], {
                "hash": remote_hash,
                "vault_dir": str(seed.VAULT_DIR),
                "vault_url_remote": "http://mock-remote-vault",
            })

    check("blob is cached locally", local_path.exists())

    # Second call — no remote needed, should hit L1
    call_count = 0
    original_urlopen = __import__("urllib.request", fromlist=["urlopen"]).urlopen
    def counting_urlopen(*a, **kw):
        nonlocal call_count
        call_count += 1
        return original_urlopen(*a, **kw)

    with mock.patch("urllib.request.urlopen", side_effect=counting_urlopen):
        result = seed.invoke(_boot["discovery"], {
            "hash": remote_hash,
            "vault_dir": str(seed.VAULT_DIR),
            "vault_url_remote": "http://mock-remote-vault",
        })

    check("L1 serves cached blob (no remote call)", call_count == 0, f"urlopen called {call_count} times")
    check("cached blob returns correct payload", result.get("payload") == "result = 'remote-blob'")


# ---------------------------------------------------------------------------
# Remote tier — hash mismatch (tampered content)
# ---------------------------------------------------------------------------

def test_discovery_remote_rejects_tampered_content() -> None:
    section("Discovery — remote tier: rejects content with wrong hash")
    # Claim to fetch blake3:aaa...aaa but return different bytes
    fake_target = "blake3:" + "a" * 64
    tampered_bytes = b'{"type": "logic/python", "payload": "result = \'tampered\'"}'

    # Ensure not in local vault
    local_path = seed.VAULT_DIR / ("a" * 64)
    if local_path.exists():
        local_path.unlink()

    class _MockResponse:
        def read(self): return tampered_bytes
        def __enter__(self): return self
        def __exit__(self, *a): pass

    try:
        with mock.patch("urllib.request.urlopen", return_value=_MockResponse()):
            seed.invoke(_boot["discovery"], {
                "hash": fake_target,
                "vault_dir": str(seed.VAULT_DIR),
                "vault_url_remote": "http://mock-remote-vault",
            })
        check("tampered content raises FileNotFoundError", False, "no exception raised")
    except FileNotFoundError as e:
        check("tampered content raises FileNotFoundError", True)
        check("error mentions mismatch or hash", "mismatch" in str(e).lower() or "not found" in str(e).lower(),
              str(e)[:60])
    except Exception as e:
        check("tampered content raises FileNotFoundError", False, type(e).__name__ + ": " + str(e)[:60])


# ---------------------------------------------------------------------------
# Remote tier — network error
# ---------------------------------------------------------------------------

def test_discovery_remote_unreachable() -> None:
    section("Discovery — remote tier: network error raises FileNotFoundError")
    import blake3 as _blake3
    # A hash that definitely isn't local
    missing_bare = "b" * 64
    missing_hash = f"blake3:{missing_bare}"
    local_path = seed.VAULT_DIR / missing_bare
    if local_path.exists():
        local_path.unlink()

    try:
        with mock.patch("urllib.request.urlopen", side_effect=URLError("connection refused")):
            seed.invoke(_boot["discovery"], {
                "hash": missing_hash,
                "vault_dir": str(seed.VAULT_DIR),
                "vault_url_remote": "http://mock-remote-vault",
            })
        check("network error raises FileNotFoundError", False, "no exception raised")
    except FileNotFoundError:
        check("network error raises FileNotFoundError", True)
    except Exception as e:
        check("network error raises FileNotFoundError", False, type(e).__name__ + ": " + str(e)[:60])


# ---------------------------------------------------------------------------
# DISCOVERY_V8 has same behavior (triple-pass review passes)
# ---------------------------------------------------------------------------

def test_discovery_v8_passes_triple_pass_review() -> None:
    section("DISCOVERY_V8 — passes Triple-Pass Review (remote tier, import urllib OK)")
    h = seed.put("logic/python", evolve.DISCOVERY_V8)
    try:
        promote.triple_pass_review(h, label="discovery")
        check("DISCOVERY_V8 passes triple_pass_review", True)
    except promote.ReviewError as e:
        check("DISCOVERY_V8 passes triple_pass_review", False, f"[{e.pass_name}] {e.detail}")


# ---------------------------------------------------------------------------
# Full f_17 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f17_evolution_cycle() -> None:
    section("Full f_17 evolution cycle — manifest v1.17.0")

    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f17-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f17-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f17-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f17-candidate")

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
    check("manifest version 1.17.0", m["version"] == "1.17.0")

    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v17 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.17.0"]
    check("at least one v1.17.0 promote event", len(promote_v17) >= 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_discovery_l1_still_works()
    test_discovery_no_remote_raises_on_miss()
    test_discovery_remote_fetch_and_cache()
    test_discovery_remote_cache_serves_l1_on_retry()
    test_discovery_remote_rejects_tampered_content()
    test_discovery_remote_unreachable()
    test_discovery_v8_passes_triple_pass_review()
    test_full_f17_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
