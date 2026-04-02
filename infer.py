#!/usr/bin/env python3
"""
infer.py — Inference interface for the D-JIT Logic Fabric evolve engine (f_9)

Generates candidate blob payloads by calling the `ai` CLI binary (subprocess).
Credentials are managed by the ai daemon's routing configuration — they never
appear in subprocess arguments, vault blobs, or audit log entries.

Model selection: use a non-CLI-Claude alias (e.g. gemini-flash, devstral) so
the ai daemon routes through Cloudflare AI Gateway rather than cli/claude.
The cli/claude route injects the CLAUDE.md context which includes TypeScript-only
skill development constraints — those constraints must not apply to blob generation.

If the `ai` binary is unavailable or returns a non-zero exit code, raises
InferenceUnavailable so the caller can fall back to a deterministic mutation.
"""

import os
import re
import shutil
import subprocess


class InferenceUnavailable(Exception):
    """Raised when the ai binary is not on PATH or returns a non-zero exit code."""


def generate_candidate(
    current_payload: str,
    contract: dict,
    fitness: dict,
    mutation_goal: str,
    model: str = "gemini-flash",
) -> str:
    """
    Generate a candidate blob payload via LLM inference.

    Args:
        current_payload: Python source of the current baseline blob.
        contract:        Parsed contract/definition record with 'pre' and 'post' keys.
        fitness:         Dict with keys success_rate, avg_latency_ms, invocation_count.
        mutation_goal:   One-line description of what the candidate should improve.
        model:           ai binary model alias. Must route through Cloudflare AI Gateway
                         (not cli/claude) to avoid CLAUDE.md skill constraints. Default:
                         gemini-flash (fast, no system prompt injection).

    Returns:
        Python source string suitable for seed.put("logic/python", ...).

    Raises:
        InferenceUnavailable: if ai binary is absent or fails.
    """
    if shutil.which("ai") is None:
        raise InferenceUnavailable("ai binary not found on PATH")

    prompt = _build_prompt(current_payload, contract, fitness, mutation_goal)

    result = subprocess.run(
        ["ai", model, prompt],
        capture_output=True,
        text=True,
        timeout=90,
        env=os.environ,  # credentials managed by ai daemon config, not env vars here
    )

    if result.returncode != 0:
        raise InferenceUnavailable(
            f"ai binary exited {result.returncode}: {result.stderr[:300]}"
        )

    source = _extract_source(result.stdout)
    if not source:
        raise InferenceUnavailable("ai binary returned empty response")

    return source


def _build_prompt(
    current_payload: str,
    contract: dict,
    fitness: dict,
    mutation_goal: str,
) -> str:
    pre_src  = contract.get("pre",  "def pre(context):\n    return True")
    post_src = contract.get("post", "def post(context, result):\n    return result is not None")

    sr  = fitness.get("success_rate",    0.0)
    lat = fitness.get("avg_latency_ms",  0.0)
    n   = fitness.get("invocation_count", 0)

    return (
        "You are generating a candidate blob for the D-JIT Logic Fabric.\n\n"
        "CURRENT IMPLEMENTATION:\n"
        "```python\n"
        f"{current_payload.strip()}\n"
        "```\n\n"
        "BEHAVIORAL CONTRACT:\n"
        f"  pre:\n{_indent(pre_src, 4)}\n\n"
        f"  post:\n{_indent(post_src, 4)}\n\n"
        "FITNESS SIGNALS:\n"
        f"  success_rate:     {sr:.3f}\n"
        f"  avg_latency_ms:   {lat:.2f}\n"
        f"  invocation_count: {n}\n\n"
        f"MUTATION GOAL: {mutation_goal}\n\n"
        "ABI RULES (must be followed exactly):\n"
        "  - `context` dict is the only input\n"
        "  - `log()` callable is available for diagnostic output\n"
        "  - `result` variable must be set before the blob exits\n"
        "  - Only Python stdlib is available (no third-party imports)\n"
        "  - No file system writes; no network calls; no subprocess\n\n"
        "Return ONLY the Python source. No explanation, no markdown, no prose."
    )


def _extract_source(response: str) -> str:
    """Strip markdown code fences if present; return raw Python source."""
    # ```python ... ``` (complete fence)
    match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # ``` ... ```  (no language tag, complete fence)
    match = re.search(r"```\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fence opened but never closed — strip the opening line and return rest
    lines = response.strip().splitlines()
    if lines and lines[0].strip() in ("```python", "```"):
        return "\n".join(lines[1:]).strip()
    return response.strip()


def generate_test_cases(
    label: str,
    contract: dict,
    candidate_payload: str,
    n: int = 3,
    model: str = "devstral",
) -> list[dict]:
    """
    Generate adversarial test/case blobs for a candidate implementation.

    Uses a different model than generate_candidate (devstral vs gemini-flash) to
    enforce adversarial separation: the tester cannot share blind spots with the
    implementor.

    Args:
        label:             The blob label being tested (e.g. "planning").
        contract:          Parsed contract/definition record with 'pre' and 'post' keys.
        candidate_payload: Python source of the candidate to be tested.
        n:                 Number of test cases to generate.
        model:             ai alias for the tester model. Must differ from implementor.

    Returns:
        List of test/case payload dicts (not yet PUT into the vault).
        Each dict has: for_label, input_context, expected, tolerance, rationale.

    Raises:
        InferenceUnavailable: if ai binary absent or fails.
        ValueError: if the LLM response cannot be parsed as a JSON array.
    """
    if shutil.which("ai") is None:
        raise InferenceUnavailable("ai binary not found on PATH")

    prompt = _build_test_prompt(label, contract, candidate_payload, n)

    result = subprocess.run(
        ["ai", model, prompt],
        capture_output=True,
        text=True,
        timeout=120,
        env=os.environ,
    )

    if result.returncode != 0:
        raise InferenceUnavailable(
            f"ai binary (tester) exited {result.returncode}: {result.stderr[:300]}"
        )

    return _parse_test_cases(result.stdout, label)


def _build_test_prompt(
    label: str,
    contract: dict,
    candidate_payload: str,
    n: int,
) -> str:
    import json as _json
    pre_src  = contract.get("pre",  "def pre(context):\n    return True")
    post_src = contract.get("post", "def post(context, result):\n    return result is not None")

    example = _json.dumps({
        "for_label":     label,
        "input_context": {"example_key": "example_value"},
        "expected":      {"example_field": "example_value"},
        "tolerance":     "structural",
        "rationale":     "why this input is adversarial",
    }, indent=2)

    return (
        f"You are an adversarial tester for the D-JIT Logic Fabric, label '{label}'.\n\n"
        "BEHAVIORAL CONTRACT:\n"
        f"  pre:\n{_indent(pre_src, 4)}\n\n"
        f"  post:\n{_indent(post_src, 4)}\n\n"
        "CANDIDATE IMPLEMENTATION:\n"
        "```python\n"
        f"{candidate_payload.strip()}\n"
        "```\n\n"
        f"Generate {n} adversarial test cases that probe boundary conditions, edge cases,\n"
        "and inputs the implementor may not have considered. Each case must be a JSON object:\n"
        f"{example}\n\n"
        "tolerance values: 'exact' (result==expected), 'structural' (same keys), "
        "'behavioral' (post-condition holds).\n\n"
        f"Return a JSON array of exactly {n} test case objects. "
        "No prose, no markdown, no explanation — only the JSON array."
    )


def _parse_test_cases(response: str, label: str) -> list[dict]:
    """Parse LLM response into a list of test/case payload dicts."""
    import json as _json

    # Strip markdown fences if present
    text = response.strip()
    match = re.search(r"```(?:json)?\n(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    # Handle unclosed fence
    lines = text.splitlines()
    if lines and lines[0].strip() in ("```json", "```"):
        text = "\n".join(lines[1:]).strip()

    try:
        cases = _json.loads(text)
    except _json.JSONDecodeError as e:
        raise ValueError(f"test case response is not valid JSON: {e}\nResponse: {text[:300]}")

    if not isinstance(cases, list):
        raise ValueError(f"expected JSON array, got {type(cases).__name__}")

    valid_tolerances = {"exact", "structural", "behavioral"}
    result = []
    for i, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        # Enforce for_label and tolerance
        case["for_label"] = label
        if case.get("tolerance") not in valid_tolerances:
            case["tolerance"] = "behavioral"
        result.append(case)

    return result


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
