#!/usr/bin/env python3
"""
infer.py — Inference interface for the D-JIT Logic Fabric evolve engine (f_8)

Generates candidate blob payloads by calling the `ai` CLI binary (subprocess).
Credentials (CF_ACCOUNT_ID, CF_GATEWAY_NAME, CF_AIG_TOKEN) are consumed by the
`ai` binary from os.environ — they never appear in subprocess arguments, vault
blobs, or audit log entries.

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
    model: str = "haiku",
) -> str:
    """
    Generate a candidate blob payload via LLM inference.

    Args:
        current_payload: Python source of the current baseline blob.
        contract:        Parsed contract/definition record with 'pre' and 'post' keys.
        fitness:         Dict with keys success_rate, avg_latency_ms, invocation_count.
        mutation_goal:   One-line description of what the candidate should improve.
        model:           ai binary model alias (default: haiku for speed).

    Returns:
        Python source string suitable for seed.put("logic/python", ...).

    Raises:
        InferenceUnavailable: if ai binary is absent or fails.
    """
    if shutil.which("ai") is None:
        raise InferenceUnavailable("ai binary not found on PATH")

    prompt = _build_prompt(current_payload, contract, fitness, mutation_goal)

    result = subprocess.run(
        ["ai", "--no-daemon", model, prompt],
        capture_output=True,
        text=True,
        timeout=90,
        env=os.environ,  # CF credentials live here; never passed as arguments
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
    # ```python ... ```
    match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    # ``` ... ```  (no language tag)
    match = re.search(r"```\n(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response.strip()


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
