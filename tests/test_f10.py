#!/usr/bin/env python3
"""
tests/test_f10.py — f_10 Guided Mutation Goals + Multi-Candidate tests

Covers:
  - _derive_mutation_goal: signal-driven goal strings (sr, lat, vol, trend)
  - N_CANDIDATES constant present and == 3
  - _MUTATIONS removed (no longer present in evolve module)
  - _MUTATION_GOALS removed (no longer present in evolve module)
  - evolve_one: returns inference-unavailable when inference fails (no fallback)
  - evolve_one: N=3 candidates generated, failed ones discarded, best promoted
  - evolve_one: audit log records candidate_index and n_candidates fields
  - Full f_10 evolution cycle: mocked two-model pipeline, manifest v1.10.0
  - Backward compat: _derive_mutation_goal produces non-empty string for all labels
  - Credential safety: no CF strings in vault or audit log post-evolution
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

_CF_CREDENTIAL_STRINGS = ["CF_ACCOUNT_ID", "CF_GATEWAY_NAME", "CF_AIG_TOKEN", "cf-aig"]


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    print(f"  {status}  {name}" + (f"  ({detail})" if detail else ""))
    _results.append((name, condition))


def section(title: str) -> None:
    print(f"\n── {title}")


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------

def test_n_candidates_constant() -> None:
    section("evolve.N_CANDIDATES == 3")
    check("N_CANDIDATES present",  hasattr(evolve, "N_CANDIDATES"))
    check("N_CANDIDATES == 3",     getattr(evolve, "N_CANDIDATES", None) == 3)


def test_mutations_removed() -> None:
    section("_MUTATIONS dict removed")
    check("_MUTATIONS not in module", not hasattr(evolve, "_MUTATIONS"))


def test_mutation_goals_removed() -> None:
    section("_MUTATION_GOALS dict removed")
    check("_MUTATION_GOALS not in module", not hasattr(evolve, "_MUTATION_GOALS"))


# ---------------------------------------------------------------------------
# _derive_mutation_goal — signal-driven goals
# ---------------------------------------------------------------------------

def test_derive_goal_low_success_rate() -> None:
    section("_derive_mutation_goal — low success rate triggers sr goal")
    goal = evolve._derive_mutation_goal("planning", {"success_rate": 0.6, "avg_latency_ms": 2.0, "volatility": 0.1})
    check("mentions success_rate", "success rate" in goal.lower() or "success_rate" in goal)
    check("non-empty", len(goal) > 10)


def test_derive_goal_high_volatility() -> None:
    section("_derive_mutation_goal — high volatility triggers vol goal")
    goal = evolve._derive_mutation_goal("planning", {"success_rate": 0.95, "avg_latency_ms": 2.0, "volatility": 0.8})
    check("mentions volatility", "volatil" in goal.lower())


def test_derive_goal_high_latency() -> None:
    section("_derive_mutation_goal — high latency triggers latency goal")
    goal = evolve._derive_mutation_goal("planning", {"success_rate": 0.95, "avg_latency_ms": 50.0, "volatility": 0.1})
    check("mentions latency", "latency" in goal.lower() or "latenc" in goal.lower())


def test_derive_goal_all_ok() -> None:
    section("_derive_mutation_goal — healthy signals produce generic improvement goal")
    goal = evolve._derive_mutation_goal("planning", {"success_rate": 0.95, "avg_latency_ms": 2.0, "volatility": 0.1})
    check("non-empty fallback goal", len(goal) > 10)


def test_derive_goal_all_labels() -> None:
    section("_derive_mutation_goal — non-empty for all three labels")
    signals = {"success_rate": 0.95, "avg_latency_ms": 2.0, "volatility": 0.1}
    for label in ["discovery", "planning", "telemetry-reader"]:
        goal = evolve._derive_mutation_goal(label, signals)
        check(f"{label} goal non-empty", len(goal) > 10, f"len={len(goal)}")


# ---------------------------------------------------------------------------
# evolve_one — inference-unavailable (no fallback)
# ---------------------------------------------------------------------------

def test_evolve_one_inference_unavailable_returns_skip() -> None:
    section("evolve_one — returns inference-unavailable when inference fails (no fallback)")
    _iu = infer.InferenceUnavailable("ai binary not found")
    with mock.patch("infer.generate_candidate", side_effect=_iu):
        result = evolve.evolve_one("planning")
    check("outcome is inference-unavailable",
          result["outcome"] == "inference-unavailable")
    check("not no-mutation (legacy removed)",
          result["outcome"] != "no-mutation")


# ---------------------------------------------------------------------------
# evolve_one — multi-candidate N=3
# ---------------------------------------------------------------------------

def test_evolve_one_multi_candidate_discards_failed_review() -> None:
    section("evolve_one — failed review candidates discarded, passing ones accumulate")
    call_count = [0]

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        call_count[0] += 1
        # First call returns invalid Python (will fail StaticAnalysis)
        if call_count[0] == 1:
            return "def broken( = invalid syntax"
        # Subsequent calls return valid planning V8
        return evolve.PLANNING_V8 + f"\n# candidate-{call_count[0]}"

    _iu = infer.InferenceUnavailable("mocked")
    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=_iu), \
         mock.patch("promote.run_test_suite", return_value=[]):
        result = evolve.evolve_one("planning")

    check("N_CANDIDATES calls made", call_count[0] == evolve.N_CANDIDATES,
          f"got {call_count[0]}")
    check("outcome not error", result["outcome"] in {"promoted", "no-improvement"})


def test_evolve_one_all_candidates_fail_review() -> None:
    section("evolve_one — all candidates fail review → no-improvement")
    _iu = infer.InferenceUnavailable("mocked")
    with mock.patch("infer.generate_candidate",
                    return_value="def broken( = invalid syntax"), \
         mock.patch("infer.generate_test_cases", side_effect=_iu):
        result = evolve.evolve_one("planning")

    check("outcome is no-improvement", result["outcome"] == "no-improvement")


def test_evolve_one_audit_log_records_candidate_metadata() -> None:
    section("evolve_one — audit log records candidate_index and n_candidates")

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return evolve.PLANNING_V8 + "\n# audit-test"

    _iu = infer.InferenceUnavailable("mocked")
    with mock.patch("infer.generate_candidate", side_effect=mock_gen_candidate), \
         mock.patch("infer.generate_test_cases", side_effect=_iu), \
         mock.patch("promote.run_test_suite", return_value=[]):
        evolve.evolve_one("planning")

    audit_path = Path("./audit.log")
    entries = [json.loads(l) for l in audit_path.read_text().splitlines() if l.strip()]
    bm_entries = [e for e in entries
                  if e.get("event") == "benchmark" and e.get("label") == "planning"]
    # At least one benchmark entry should have candidate metadata
    has_meta = any("candidate_index" in e and "n_candidates" in e for e in bm_entries)
    check("audit log has candidate_index", has_meta)


# ---------------------------------------------------------------------------
# Full f_10 evolution cycle
# ---------------------------------------------------------------------------

def test_full_f10_evolution_cycle() -> None:
    section("Full f_10 evolution cycle — guided goals, N=3, manifest v1.10.0")

    call_counts: dict[str, int] = {"discovery": 0, "planning": 0, "telemetry-reader": 0}
    _v8_variants = {
        evolve.DISCOVERY_V8:        evolve.DISCOVERY_V8 + "\n# f10-candidate",
        evolve.PLANNING_V8:         evolve.PLANNING_V8 + "\n# f10-candidate",
        evolve.TELEMETRY_READER_V8: evolve.TELEMETRY_READER_V8 + "\n# f10-candidate",
    }

    def mock_gen_candidate(current_payload, contract, fitness, mutation_goal, model="gemini-flash"):
        return _v8_variants.get(current_payload, current_payload + "\n# f10-candidate")

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

    check("all three cycles ran", len(results) == 3)
    promoted = [r for r in results if r["outcome"] == "promoted"]
    check("at least one blob promoted", len(promoted) >= 1, f"got {len(promoted)}")

    m = promote.load_manifest()
    check("manifest version 1.12.0", m["version"] == "1.12.0")
    for label in ["discovery", "planning", "telemetry-reader"]:
        lh = m.get("blobs", {}).get(label, {}).get("logic/python")
        check(f"{label} logic blob in manifest", lh is not None)
        ch = m.get("blobs", {}).get(label, {}).get("contract/definition")
        check(f"{label} contract still in manifest", ch is not None)

    entries = [json.loads(l) for l in Path("./audit.log").read_text().splitlines() if l.strip()]
    promote_v11 = [e for e in entries
                   if e.get("event") == "promote" and e.get("version") == "1.12.0"]
    check("at least one v1.12.0 promote event", len(promote_v11) >= 1)


# ---------------------------------------------------------------------------
# Credential safety
# ---------------------------------------------------------------------------

def test_no_credentials_in_vault_post_evolution() -> None:
    section("Credential safety — no CF credentials in vault post-evolution")
    found = False
    for blob_path in seed.VAULT_DIR.iterdir():
        if not blob_path.is_file():
            continue
        content = blob_path.read_text(errors="replace")
        if any(cred in content for cred in _CF_CREDENTIAL_STRINGS):
            found = True
            break
    check("no CF credentials in vault", not found)


def test_no_credentials_in_audit_log_post_evolution() -> None:
    section("Credential safety — no CF credentials in audit.log post-evolution")
    audit_path = Path("./audit.log")
    text = audit_path.read_text()
    for cred in _CF_CREDENTIAL_STRINGS:
        check(f"no {cred} in audit log", cred not in text)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    for p in [seed.VAULT_DIR, seed.BYTECODE_DIR, Path("./manifest.json"), Path("./audit.log")]:
        if isinstance(p, Path) and p.is_dir():
            shutil.rmtree(p)
        elif isinstance(p, Path) and p.exists():
            p.unlink()
    seed._CODE_CACHE.clear()
    seed._LAST_TELEMETRY.clear()

    _boot.update(bootstrap.run())
    print()

    # Module invariants
    test_n_candidates_constant()
    test_mutations_removed()
    test_mutation_goals_removed()

    # _derive_mutation_goal
    test_derive_goal_low_success_rate()
    test_derive_goal_high_volatility()
    test_derive_goal_high_latency()
    test_derive_goal_all_ok()
    test_derive_goal_all_labels()

    # inference-unavailable (no fallback)
    test_evolve_one_inference_unavailable_returns_skip()

    # multi-candidate
    test_evolve_one_multi_candidate_discards_failed_review()
    test_evolve_one_all_candidates_fail_review()
    test_evolve_one_audit_log_records_candidate_metadata()

    # Full cycle
    test_full_f10_evolution_cycle()

    # Credential safety
    test_no_credentials_in_vault_post_evolution()
    test_no_credentials_in_audit_log_post_evolution()

    total   = len(_results)
    passing = sum(1 for _, ok in _results if ok)
    print(f"\n{'─' * 40}")
    print(f"  {passing}/{total} passed")
    if passing < total:
        raise SystemExit(1)
