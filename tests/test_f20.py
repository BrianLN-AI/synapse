#!/usr/bin/env python3
"""
tests/test_f20.py — f_20 capability registry: list_capabilities(), inspectable fabric

Covers:
  - bootstrap registers discovery, planning, telemetry-reader as capabilities
  - promote.register_capability() stores description, tags in manifest["capabilities"]
  - register_capability() is idempotent (re-register overwrites, no duplicates)
  - promote.list_capabilities() returns all registered capabilities sorted by label
  - promote.get_capability() returns record for registered label
  - promote.get_capability() returns None for unregistered label
  - list_capabilities() includes current_hash from manifest["blobs"]
  - register_capability() writes register_capability audit log entry
  - list-capabilities blob bootstrapped in manifest by run_all()
  - invoking list-capabilities blob returns sorted capability list
  - list-capabilities result contains correct labels
  - Full f_20 evolution cycle: manifest v1.20.0
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
    print("\n── Bootstrap: f_0 + f_7 + f_20 Closure")
    m = promote.load_manifest()
    caps = promote.list_capabilities()
    print(f"  capabilities registered: {[c['label'] for c in caps]}")
    print(f"\n  Manifest v{m['version']}")


# ---------------------------------------------------------------------------
# Bootstrap registers core capabilities
# ---------------------------------------------------------------------------

def test_bootstrap_registers_core_capabilities() -> None:
    section("bootstrap — registers discovery, planning, telemetry-reader as capabilities")
    caps = {c["label"]: c for c in promote.list_capabilities()}
    for label in ["discovery", "planning", "telemetry-reader"]:
        check(f"{label} registered as capability", label in caps)
        if label in caps:
            check(f"{label} has description", bool(caps[label]["description"]))
            check(f"{label} has tags", len(caps[label]["tags"]) > 0,
                  str(caps[label]["tags"]))


# ---------------------------------------------------------------------------
# register_capability / list_capabilities / get_capability
# ---------------------------------------------------------------------------

def test_register_capability_stores_in_manifest() -> None:
    section("register_capability — stores description and tags in manifest")
    promote.register_capability(
        "test-widget",
        "A test widget for f_20 validation",
        tags=["test", "widget"],
    )
    cap = promote.get_capability("test-widget")
    check("capability stored", cap is not None)
    if cap:
        check("description matches", cap["description"] == "A test widget for f_20 validation")
        check("tags stored", cap["tags"] == ["test", "widget"])
        check("registered_at set", bool(cap["registered_at"]))


def test_register_capability_idempotent() -> None:
    section("register_capability — re-registering overwrites, no duplicates")
    promote.register_capability("idempotent-cap", "first description", tags=["v1"])
    promote.register_capability("idempotent-cap", "second description", tags=["v2"])

    caps = [c for c in promote.list_capabilities() if c["label"] == "idempotent-cap"]
    check("exactly one entry after two registrations", len(caps) == 1, f"count={len(caps)}")
    if caps:
        check("description updated to latest", caps[0]["description"] == "second description")
        check("tags updated to latest", caps[0]["tags"] == ["v2"])


def test_list_capabilities_returns_sorted() -> None:
    section("list_capabilities — returns capabilities sorted by label")
    caps = promote.list_capabilities()
    labels = [c["label"] for c in caps]
    check("list is sorted alphabetically", labels == sorted(labels), str(labels))


def test_get_capability_returns_record() -> None:
    section("get_capability — returns record for registered label")
    promote.register_capability("queryable-cap", "for get_capability test", tags=["get"])
    cap = promote.get_capability("queryable-cap")
    check("record returned", cap is not None)
    if cap:
        check("label matches", cap["label"] == "queryable-cap")


def test_get_capability_returns_none_unknown() -> None:
    section("get_capability — returns None for unregistered label")
    result = promote.get_capability("no-such-capability-xyz")
    check("returns None for unknown label", result is None)


def test_list_capabilities_includes_current_hash() -> None:
    section("list_capabilities — current_hash reflects manifest[blobs]")
    m = promote.load_manifest()
    caps = {c["label"]: c for c in promote.list_capabilities()}

    if "discovery" in caps:
        expected_hash = m.get("blobs", {}).get("discovery", {}).get("logic/python", "")
        check("discovery current_hash matches manifest blob",
              caps["discovery"]["current_hash"] == expected_hash,
              caps["discovery"]["current_hash"][:24])


def test_register_capability_writes_audit_log() -> None:
    section("register_capability — writes register_capability event to audit log")
    promote.register_capability("audit-cap", "audit test", tags=["audit"])

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    events = [e for e in entries
              if e.get("event") == "register_capability" and e.get("label") == "audit-cap"]
    check("register_capability event in audit log", len(events) >= 1)
    if events:
        check("event has description", bool(events[-1].get("description")))
        check("event has tags", "tags" in events[-1])


# ---------------------------------------------------------------------------
# list-capabilities blob
# ---------------------------------------------------------------------------

def test_run_all_bootstraps_list_capabilities_label() -> None:
    section("run_all — bootstraps list-capabilities label in manifest")
    _v_variants = {
        evolve.DISCOVERY_V9:        evolve.DISCOVERY_V9 + "\n# f20-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f20-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f20-candidate",
        evolve.LIST_CAPABILITIES_V1: evolve.LIST_CAPABILITIES_V1 + "\n# f20-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v_variants.get(current_payload, current_payload + "\n# f20-candidate")

    def mock_gen_test_cases(label, contract, candidate_payload, n=3, model="devstral"):
        return [{"for_label": label, "input_context": {}, "expected": None,
                 "tolerance": "behavioral", "rationale": "probe"}]

    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=mock_gen_test_cases), \
         mock.patch("promote.run_test_suite",
                    return_value=[{"hash": "mock", "passed": True,
                                   "result": {}, "expected": None,
                                   "tolerance": "behavioral"}]):
        evolve.run_all()

    m = promote.load_manifest()
    check("list-capabilities in manifest[blobs]",
          "list-capabilities" in m.get("blobs", {}))
    check("list-capabilities registered as capability",
          promote.get_capability("list-capabilities") is not None)


def test_invoke_list_capabilities_blob() -> None:
    section("list-capabilities blob — invocable, returns sorted capability list")
    m = promote.load_manifest()
    lc_hash = m.get("blobs", {}).get("list-capabilities", {}).get("logic/python")
    if not lc_hash:
        check("list-capabilities blob exists in manifest", False, "blob not found — run test_run_all first")
        return

    capabilities = m.get("capabilities", {})
    blobs        = m.get("blobs", {})

    result = seed.invoke(lc_hash, {
        "capabilities": capabilities,
        "blobs":        blobs,
    })

    check("result is a list", isinstance(result, list))
    if isinstance(result, list) and result:
        labels = [r["label"] for r in result]
        check("result is sorted by label", labels == sorted(labels), str(labels))
        check("each entry has required fields",
              all("description" in r and "tags" in r and "current_hash" in r for r in result))
        core = {"discovery", "planning", "telemetry-reader"}
        present = {r["label"] for r in result}
        check("core capabilities present", core.issubset(present),
              f"missing: {core - present}")


# ---------------------------------------------------------------------------
# Full f_20 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f20_evolution_cycle() -> None:
    section("Full f_20 evolution cycle — manifest v1.20.0")

    _v_variants = {
        evolve.DISCOVERY_V9:         evolve.DISCOVERY_V9 + "\n# f20-evo",
        evolve.PLANNING_V8:          evolve.PLANNING_V8 + "\n# f20-evo",
        evolve.TELEMETRY_READER_V8:  evolve.TELEMETRY_READER_V8 + "\n# f20-evo",
        evolve.LIST_CAPABILITIES_V1: evolve.LIST_CAPABILITIES_V1 + "\n# f20-evo",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v_variants.get(current_payload, current_payload + "\n# f20-evo")

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
    check("manifest version 1.20.0", m["version"] == "1.20.0")

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v20 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.20.0"]
    check("at least one v1.20.0 promote event", len(promote_v20) >= 1)

    caps = promote.list_capabilities()
    cap_labels = {c["label"] for c in caps}
    check("list-capabilities registered as capability",
          "list-capabilities" in cap_labels, str(sorted(cap_labels)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)

    setup()

    test_bootstrap_registers_core_capabilities()
    test_register_capability_stores_in_manifest()
    test_register_capability_idempotent()
    test_list_capabilities_returns_sorted()
    test_get_capability_returns_record()
    test_get_capability_returns_none_unknown()
    test_list_capabilities_includes_current_hash()
    test_register_capability_writes_audit_log()
    test_run_all_bootstraps_list_capabilities_label()
    test_invoke_list_capabilities_blob()
    test_full_f20_evolution_cycle()

    print(f"\n{'─' * 40}")
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"  {passed}/{total} passed")
    if passed < total:
        sys.exit(1)
