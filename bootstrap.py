#!/usr/bin/env python3
"""
bootstrap.py — D-JIT Logic Fabric Bootstrap
f_0 closure: PUT Discovery, Planning, and Telemetry-Reader blobs.
Triple-Pass Review, Council Approval, manifest promotion to v1.0.0.

After this runs:
  - linker.py routes through all three self-hosted blobs
  - arbitrate() auto-enriches from live telemetry (feedback loop closed)
  - Manifest at v1.0.0 — f_0 is defined
  - Two reviewers are registered: bootstrap (trust root) and evolve-engine

f_6: the bootstrap reviewer is the explicit trust root.  It has no prior
approver — it is self-grounding by design.  The evolve-engine reviewer is
promoted by the bootstrap reviewer during the same run.  After bootstrap,
all further reviewer promotions require a registered reviewer's approval.

f_8: evolve engine generates candidates via `ai` binary (Cloudflare AI Gateway).
Bootstrap is unchanged — it seeds the system; inference is an evolve-engine concern.
"""

import json
import sys

import promote
import seed

# ---------------------------------------------------------------------------
# Engine expression payload (f_14/f_15)
# Type: logic/engine — kernel-trusted infrastructure blob.
# Exec'd by the kernel with injected scope:
#   _raw_get, put, _LAST_TELEMETRY, BYTECODE_DIR
# Defines: invoke(), record_feedback() — the full execution policy.
# exec() is called directly; the logic/engine type exempts this blob from
# the safety scanner's exec-forbidden check (Pass 2 skipped for logic/engine).
# After bootstrap, evolve_engine() in evolve.py provides the governed upgrade path.
# ---------------------------------------------------------------------------

ENGINE_PAYLOAD = '''\
import json
import marshal
import time
import tracemalloc

# Injected by kernel: _raw_get, put, _LAST_TELEMETRY, BYTECODE_DIR

_CODE_CACHE = {}


def _load_code(content_hash, payload):
    """Two-level bytecode cache: L1 in-process, L2 on-disk via marshal."""
    if content_hash in _CODE_CACHE:
        return _CODE_CACHE[content_hash]

    BYTECODE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = BYTECODE_DIR / f"{content_hash}.pyc"

    if cache_path.exists():
        try:
            code = marshal.loads(cache_path.read_bytes())
            _CODE_CACHE[content_hash] = code
            return code
        except Exception:
            pass  # corrupt or incompatible — fall through to recompile

    code = compile(payload, f"<blob:{content_hash[:8]}>", "exec")
    try:
        cache_path.write_bytes(marshal.dumps(code))
    except Exception:
        pass  # disk write failure is non-fatal; L1 cache still works
    _CODE_CACHE[content_hash] = code
    return code


def _record_telemetry(content_hash, latency_ms, memory_kb, log_lines, error):
    record = {
        "invoked":       content_hash,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "latency_ms":    round(latency_ms, 3),
        "memory_kb":     round(memory_kb, 3),
        "log":           log_lines,
        "error":         error,
    }
    telem_hash = put("telemetry/artifact", json.dumps(record))
    _LAST_TELEMETRY[content_hash] = telem_hash
    return telem_hash


def invoke(content_hash, context=None):
    blob = _raw_get(content_hash)
    payload = blob["payload"]

    if context is None:
        context = {}

    log_lines = []
    scope = {"context": context, "log": lambda msg: log_lines.append(str(msg))}

    tracemalloc.start()
    start_ns = time.perf_counter_ns()

    try:
        exec(_load_code(content_hash, payload), scope)  # noqa: S102
    except Exception as exc:
        _record_telemetry(
            content_hash,
            (time.perf_counter_ns() - start_ns) / 1e6,
            0, log_lines, str(exc),
        )
        raise

    elapsed_ms = (time.perf_counter_ns() - start_ns) / 1e6
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if "result" not in scope:
        _record_telemetry(content_hash, elapsed_ms, peak / 1024, log_lines,
                          "ABI violation: result variable not set")
        raise RuntimeError(f"ABI violation: blob {content_hash} did not set \'result\'")

    _record_telemetry(content_hash, elapsed_ms, peak / 1024, log_lines, None)
    return scope["result"]


def record_feedback(logic_hash, outcome, confidence=1.0, reviewer="caller", reviewer_hash=None):
    invocation_telem = _LAST_TELEMETRY.get(logic_hash)
    record = {
        "invoked":          logic_hash,
        "invocation_telem": invocation_telem,
        "outcome":          outcome,
        "confidence":       round(float(confidence), 4),
        "reviewer":         reviewer,
        "reviewer_hash":    reviewer_hash,
        "timestamp_utc":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return put("feedback/outcome", json.dumps(record, sort_keys=True))
'''

# ---------------------------------------------------------------------------
# Discovery blob (Layer 2 — The Librarian)
# ---------------------------------------------------------------------------

DISCOVERY_PAYLOAD = """\
import json
import urllib.request
import blake3 as _blake3
from pathlib import Path

vault_dir = Path(context.get("vault_dir", "./blob_vault"))
raw_hash  = context["hash"]
# Normalize multihash address (e.g. "blake3:<hex>") to bare hex for vault lookup
target_hash = raw_hash.split(":", 1)[1] if ":" in raw_hash else raw_hash
blob_path = vault_dir / target_hash

if blob_path.exists():
    log(f"discovery: resolved {target_hash[:8]}... from L1")
    result = json.loads(blob_path.read_text())
else:
    vault_url_remote = context.get("vault_url_remote", "").rstrip("/")
    if vault_url_remote:
        try:
            url  = f"{vault_url_remote}/{target_hash}"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            # Content-addressed verification: hash must match the address
            actual = _blake3.blake3(data).hexdigest()
            if actual != target_hash:
                raise ValueError(
                    f"Discovery remote: hash mismatch for {target_hash[:8]}... "
                    f"(got {actual[:8]}...)"
                )
            # Cache to local vault
            vault_dir.mkdir(parents=True, exist_ok=True)
            blob_path.write_bytes(data)
            log(f"discovery: fetched {target_hash[:8]}... from remote, cached locally")
            result = json.loads(data.decode("utf-8"))
        except (urllib.error.URLError, ValueError) as exc:
            raise FileNotFoundError(
                f"Discovery: {raw_hash} not found in L1 or remote ({exc})"
            ) from exc
    else:
        raise FileNotFoundError(f"Discovery L1: {raw_hash} not found in vault")
"""

# ---------------------------------------------------------------------------
# Planning blob (Layer 3 — The Broker)
# Fitness: f(Link) = SuccessRate × Integrity / Latency × ComputeCost
# ---------------------------------------------------------------------------

PLANNING_PAYLOAD = """\
candidates = context.get("candidates", [])

if not candidates:
    result = None
else:
    def _score(c):
        sr = float(c.get("success_rate", 1.0))
        integrity = float(c.get("integrity", 1.0))
        latency = max(float(c.get("latency_ms", 1.0)), 0.001)
        cost = max(float(c.get("cost", 1.0)), 0.001)
        return (sr * integrity) / (latency * cost)

    ranked = sorted(candidates, key=_score, reverse=True)
    best = ranked[0]
    best_score = _score(best)

    log(f"planning: {len(candidates)} candidates, best={best['hash'][:8]}... score={best_score:.4f}")

    result = {
        "selected": best["hash"],
        "score": best_score,
        "rationale": (
            f"f(Link)={best_score:.4f} vs runner-up {_score(ranked[1]):.4f}"
            if len(ranked) > 1
            else "sole candidate"
        ),
        "ranked": [{"hash": c["hash"], "score": _score(c)} for c in ranked],
    }
"""

# ---------------------------------------------------------------------------
# Telemetry-Reader blob (feedback layer)
# Scans vault, aggregates per-blob fitness signals from telemetry artifacts.
# Closes the loop: measured performance → Planning arbitration inputs.
# ---------------------------------------------------------------------------

TELEMETRY_READER_PAYLOAD = """\
import json
from pathlib import Path

vault_dir = Path(context.get("vault_dir", "./blob_vault"))
target_hash = context.get("hash")  # optional: filter to one blob

stats = {}

for blob_path in vault_dir.iterdir():
    if not blob_path.is_file():
        continue
    try:
        envelope = json.loads(blob_path.read_text())
    except Exception:
        continue
    if envelope.get("type") != "telemetry/artifact":
        continue
    record = json.loads(envelope["payload"])
    invoked = record.get("invoked")
    if not invoked:
        continue
    if target_hash and invoked != target_hash:
        continue
    s = stats.setdefault(invoked, {"total": 0, "success": 0, "latency_sum": 0.0, "memory_sum": 0.0})
    s["total"] += 1
    if record.get("error") is None:
        s["success"] += 1
    s["latency_sum"] += record.get("latency_ms", 0.0)
    s["memory_sum"] += record.get("memory_kb", 0.0)

result = {
    h: {
        "success_rate": s["success"] / s["total"],
        "avg_latency_ms": s["latency_sum"] / s["total"],
        "avg_memory_kb": s["memory_sum"] / s["total"],
        "invocation_count": s["total"],
    }
    for h, s in stats.items()
    if s["total"] > 0
}

log(f"telemetry-reader: {len(result)} blob(s) with recorded history")
"""


# ---------------------------------------------------------------------------
# Reviewer payloads — trust root + evolve engine
# ---------------------------------------------------------------------------

BOOTSTRAP_REVIEWER_PAYLOAD = json.dumps({
    "id":               "bootstrap",
    "description":      "Bootstrap reviewer — explicit trust root for the f_0 closure. "
                        "Self-grounding; no prior approver exists.",
    "authorized_types": ["logic/python", "logic/engine", "feedback/outcome", "council/reviewer",
                         "contract/definition", "test/case", "adr/decision", "meta/hash-bridge"],
    "trust_weight":     1.0,
    "criteria":         "f_0 bootstrapped blobs verified by BIOS",
}, sort_keys=True)

EVOLVE_REVIEWER_PAYLOAD = json.dumps({
    "id":               "evolve-engine",
    "description":      "Automated f_n evolution engine — benchmarks candidates and "
                        "promotes those that win against the current baseline.",
    "authorized_types": ["logic/python", "logic/engine"],
    "trust_weight":     0.8,
    "criteria":         "Triple-Pass Review pass + benchmark win vs current manifest blob",
}, sort_keys=True)

# ---------------------------------------------------------------------------
# Contract payloads — behavioral contracts for the three core blobs (f_7)
# ---------------------------------------------------------------------------

DISCOVERY_CONTRACT_PAYLOAD = json.dumps({
    "for_label": "discovery",
    "pre":  "def pre(context):\n"
            "    h = str(context.get('hash', ''))\n"
            "    return len(h) == 64 and all(c in '0123456789abcdef' for c in h.lower())",
    "post": "def post(context, result):\n"
            "    return isinstance(result, dict) and 'type' in result and 'payload' in result",
    "invariant": None,
}, sort_keys=True)

PLANNING_CONTRACT_PAYLOAD = json.dumps({
    "for_label": "planning",
    "pre":  "def pre(context):\n"
            "    return isinstance(context.get('candidates'), list)",
    "post": "def post(context, result):\n"
            "    candidates = context.get('candidates', [])\n"
            "    if not candidates:\n"
            "        return result is None\n"
            "    return (isinstance(result, dict)\n"
            "            and 'selected' in result\n"
            "            and result['selected'] in [c['hash'] for c in candidates])",
    "invariant": None,
}, sort_keys=True)

TELEMETRY_READER_CONTRACT_PAYLOAD = json.dumps({
    "for_label": "telemetry-reader",
    "pre":  "def pre(context):\n"
            "    return True  # vault_dir has a default; always valid",
    "post": "def post(context, result):\n"
            "    return isinstance(result, dict)",
    "invariant": None,
}, sort_keys=True)


def run(reviewer: str = "bootstrap") -> dict:
    """
    Full bootstrap:
      1. Bootstrap the trust root reviewer (no prior approver required)
      2. Promote the evolve-engine reviewer using the bootstrap reviewer
      3. PUT Discovery, Planning, Telemetry-Reader blobs
      4. Triple-Pass Review each
      5. Council Approval (signed by evolve-engine reviewer) + promote all three
      6. PUT and promote behavioral contracts for all three core blobs (f_7)
      7. Manifest → v1.0.0
    """
    print("── Bootstrap: f_0 + f_7 Closure")

    # --- Step 1: trust root ---
    bootstrap_reviewer_hash = promote.bootstrap_reviewer(BOOTSTRAP_REVIEWER_PAYLOAD)
    print(f"  bootstrap reviewer  {bootstrap_reviewer_hash[:16]}...  (trust root)")

    # --- Step 2: evolve-engine reviewer, approved by bootstrap reviewer ---
    evolve_reviewer_hash = seed.put("council/reviewer", EVOLVE_REVIEWER_PAYLOAD)
    evolve_approval = promote.issue_council_approval(
        [evolve_reviewer_hash], reviewer_hash=bootstrap_reviewer_hash
    )
    promote.promote_reviewer(evolve_reviewer_hash, bootstrap_reviewer_hash, evolve_approval)
    print(f"  evolve reviewer     {evolve_reviewer_hash[:16]}...  (approved by bootstrap)")

    # --- Step 3: engine expression (f_13) ---
    # Promote BEFORE the logic blobs so subsequent triple_pass_review calls
    # (which invoke blobs) go through the engine path.
    engine_hash = seed.put("logic/engine", ENGINE_PAYLOAD)
    engine_approval = promote.issue_council_approval(
        [engine_hash], reviewer_hash=evolve_reviewer_hash
    )
    promote.promote(
        label="engine",
        blob_hashes=[engine_hash],
        council_approval_hash=engine_approval,
        version="1.0.0",
    )
    # Invalidate engine cache so the next invoke() loads the freshly promoted engine.
    seed._ENGINE = None
    seed._ENGINE_HASH = None
    print(f"  engine expression   {engine_hash[:16]}...  (execution policy)")

    blobs = [
        ("discovery",        DISCOVERY_PAYLOAD),
        ("planning",         PLANNING_PAYLOAD),
        ("telemetry-reader", TELEMETRY_READER_PAYLOAD),
    ]

    print()
    hashes: dict[str, str] = {}
    for label, payload in blobs:
        h = seed.put("logic/python", payload)
        hashes[label] = h
        print(f"  PUT {label:<18} {h[:16]}...")

    print()
    for label, h in hashes.items():
        try:
            promote.triple_pass_review(h)
            print(f"  PASS  {label}")
        except promote.ReviewError as e:
            print(f"  FAIL  {label} [{e.pass_name}] {e.detail}")
            sys.exit(1)

    print()
    manifest_hash = None
    for label, h in hashes.items():
        blob_approval = promote.issue_council_approval(
            [h], reviewer_hash=evolve_reviewer_hash
        )
        manifest_hash = promote.promote(
            label=label,
            blob_hashes=[h],
            council_approval_hash=blob_approval,
            version="1.0.0",
        )
        print(f"  promoted {label:<18} manifest.hash={manifest_hash[:16]}...")

    # --- Step 6: promote behavioral contracts for the three core blobs (f_7) ---
    print()
    contracts = [
        ("discovery",        DISCOVERY_CONTRACT_PAYLOAD),
        ("planning",         PLANNING_CONTRACT_PAYLOAD),
        ("telemetry-reader", TELEMETRY_READER_CONTRACT_PAYLOAD),
    ]
    contract_hashes: dict[str, str] = {}
    for label, payload in contracts:
        ch = seed.put("contract/definition", payload)
        contract_hashes[label] = ch
        print(f"  PUT contract/{label:<14} {ch[:16]}...")

    print()
    for label, ch in contract_hashes.items():
        try:
            promote.triple_pass_review(ch)
            print(f"  PASS  contract/{label}")
        except promote.ReviewError as e:
            print(f"  FAIL  contract/{label} [{e.pass_name}] {e.detail}")
            sys.exit(1)

    print()
    for label, ch in contract_hashes.items():
        contract_approval = promote.issue_council_approval(
            [ch], reviewer_hash=bootstrap_reviewer_hash
        )
        manifest_hash = promote.promote_contract(
            label=label,
            contract_hash=ch,
            council_approval_hash=contract_approval,
        )
        print(f"  promoted contract/{label:<14} manifest.hash={manifest_hash[:16]}...")

    # --- Step 7: register core blobs as capabilities (f_20) ---
    promote.register_capability(
        "discovery",
        "Content-addressed blob resolution: L1→L2→remote→federation peers",
        tags=["infrastructure", "resolution"],
    )
    promote.register_capability(
        "planning",
        "Fitness-guided blob evolution scheduling and arbitration",
        tags=["infrastructure", "evolution"],
    )
    promote.register_capability(
        "telemetry-reader",
        "Invocation telemetry aggregation and fitness scoring",
        tags=["infrastructure", "telemetry"],
    )

    print(f"\n  f_0 + f_7 defined. Manifest v1.0.0  hash={manifest_hash[:16]}...")
    print("  Feedback loop: telemetry → SuccessRate → Planning arbitration ✓")
    print(f"  Reviewer chain: bootstrap → evolve-engine ✓")
    print(f"  Contracts: discovery, planning, telemetry-reader ✓")
    print(f"  Capabilities registered: discovery, planning, telemetry-reader ✓")

    return {
        **hashes,
        "engine_hash":              engine_hash,
        "manifest_hash":            manifest_hash,
        "bootstrap_reviewer_hash":  bootstrap_reviewer_hash,
        "evolve_reviewer_hash":     evolve_reviewer_hash,
        **{f"contract_{k.replace('-','_')}": v for k, v in contract_hashes.items()},
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2))
