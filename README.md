# Synapse: The D-JIT Logic Fabric

> **f_0 → f_1 → ... → f_20**
> *Each branch is a mutation. Each tag is a stable collapse of potential into form.*

---

## What It Is

**Synapse** is a **Distributed Just-In-Time (D-JIT) Logic Fabric** — a content-addressed,
self-evolving compute runtime where every piece of executable logic is stored by hash,
governed through a reviewer chain, and evolved by measuring fitness against behavioral contracts.

The core thesis: **logic is fungible when it is content-addressed.** Any algorithm defined once
can be referenced by hash, federated across vaults, and executed in a scrubbed scope with
enforced I/O contracts. The same governance infrastructure that governs user-written blobs
governs the evolution engine that rewrites them.

---

## Current State (f_20, v1.20.0)

This branch (`council/f_20`) is the checkpoint at the end of the 20-generation council lineage.
It includes:

- **Core infrastructure blobs:** `discovery` (federation-aware, v9), `planning` (burstiness-aware, v8), `telemetry-reader` (v8)
- **Engine governance:** `logic/engine` blob with isolated ABI check and benchmark
- **Multihash addresses (ADR-015):** `blake3:<hex>` canonical; backward-compatible with bare hex
- **Hash-bridge expression (f_18):** `meta/hash-bridge` links blake3 vault addresses to ZK addresses (Poseidon)
- **Federation (f_19):** multi-peer blob resolution with blake3 content verification
- **Capability registry (f_20):** `manifest["capabilities"]` + `list-capabilities` as an invocable, governed blob

The manifest at this tag is `v1.20.0`.

---

## Architecture

For the full current-state reference — components, data flows, blob types, protocols — see:

**[ARCHITECTURE.md](ARCHITECTURE.md)**

Short summary:

```
seed.py       — kernel: vault, BIOS read, engine dispatch, hash-bridge
promote.py    — linker: triple-pass review, promotion, capability registry, federation
evolve.py     — evolution engine: run_all, evolve_one, evolve_engine
bootstrap.py  — seeds the system to v1.0.0
infer.py      — LLM bridge: candidate generation, test case generation

blob_vault/   — content-addressed blob store (blake3-keyed flat files)
manifest.json — golden record: what is currently promoted
audit.log     — append-only JSONL promotion history
```

---

## Quick Start

**Requirements:** Python 3.10+, `blake3` package (`pip install blake3`)

```bash
git clone https://github.com/BrianLN-AI/synapse.git
cd synapse
git checkout council/f_20
pip install blake3

# Bootstrap the system — promotes core blobs, writes manifest.json v1.0.0
cd tests   # tests run from the tests/ directory
python bootstrap.py

# Inspect the manifest
cat manifest.json | python3 -m json.tool | head -40

# Store a blob
python -c "import seed; print(seed.put('logic/python', 'result = context.get(\"x\", 0) * 2'))"

# Invoke a blob
python -c "
import seed, bootstrap
bootstrap.run()
import json
m = json.load(open('manifest.json'))
disc_hash = m['blobs']['discovery']['logic/python']
print(seed.invoke(disc_hash, {'hash': disc_hash, 'vault_dir': 'blob_vault'}))
"
```

---

## ABI Contract

All `logic/python` blobs follow the Scope-Exchange Protocol:

- **Input:** `context` (dict) and `log(msg)` (telemetry sink) are injected
- **Output:** the blob **must** assign to `result` — this is enforced by the kernel
- **Isolation:** the scrubbed scope prevents blobs from accessing kernel internals, filesystem, or imports

```python
# Minimal valid blob
candidates = context.get("candidates", [])
result = sorted(candidates, key=lambda c: c["fitness"])[-1]
```

---

## Evolution Cycle

The system rewrites its own logic blobs through a governed loop:

```
evolve.run_all()
  for each label in manifest["blobs"]:
    ├── measure fitness (telemetry + feedback + OKR signals)
    ├── generate candidate (LLM via infer.py)
    ├── triple-pass review (6 gates: syntax, safety, ABI, feedback, reviewer, contract)
    ├── benchmark head-to-head (5 rounds)
    └── promote if candidate wins → manifest version bump + audit log entry
```

The engine blob itself has a separate governed upgrade path (`evolve.evolve_engine()`).

---

## Governance Chain

```
bootstrap reviewer (trust root)
  └── created at bootstrap, no prior approver
  └── promotes: evolve-engine reviewer + all f_0 core blobs

evolve-engine reviewer
  └── promoted by: bootstrap reviewer
  └── authorizes: all blob types
  └── used by: evolve_one() and run_all() for all subsequent promotions
```

Every promotion requires a `council/approval` artifact signed by a registered reviewer.
The approval blob is itself stored in the vault.

---

## Branch and Tag History

| Branch | Tag | Version | What it added |
|--------|-----|---------|---------------|
| `council/f_0` | `v1.0.0` | 1.0.0 | Self-hosting + closed feedback loop |
| `council/f_1` | `v1.1.0` | 1.1.0 | First self-modification cycle |
| `council/f_2` | `v1.2.0` | 1.2.0 | p95 + integrity signals end-to-end |
| `council/f_3` | `v1.3.0` | 1.3.0 | Persistent bytecode cache; dynamic tolerance |
| `council/f_4` | `v1.4.0` | 1.4.0 | Governed feedback loop |
| `council/f_5` | `v1.5.0` | 1.5.0 | Feedback blobs as governance artifacts |
| `council/f_6` | `v1.6.0` | 1.6.0 | Trust-weighted reviewer chain |
| `council/f_7` | `v1.7.0` | 1.7.0 | ContractCompliance gate; contract/definition blobs |
| `council/f_8` | `v1.8.0` | 1.8.0 | Inference-generated candidates (LLM bridge) |
| `council/f_9` | `v1.9.0` | 1.9.0 | Adversarial test authorship; goal/okr blobs |
| `council/f_10` | `v1.10.0` | 1.10.0 | OKR-driven mutation goals |
| `council/f_11` | `v1.11.0` | 1.11.0 | GOKR execution engine; structured fitness convergence |
| `council/f_12` | `v1.12.0` | 1.12.0 | blake3 as canonical hash; ABI freeze |
| `council/f_13` | `v1.13.0` | 1.13.0 | Engine as expression; governance-as-expression |
| `council/f_14` | `v1.14.0` | 1.14.0 | `logic/engine` blob type; two-level bytecode cache |
| `council/f_15` | `v1.15.0` | 1.15.0 | Engine governance; isolated ABI check + benchmark |
| `council/f_16` | `v1.16.0` | 1.16.0 | Multihash address format (ADR-015); `blake3:` prefix |
| `council/f_17` | `v1.17.0` | 1.17.0 | Remote vault tier; discovery L3 |
| `council/f_18` | `v1.18.0` | 1.18.0 | Hash-bridge expression; ZK/vault address linkage |
| `council/f_19` | `v1.19.0` | 1.19.0 | Federation; multi-peer blob resolution |
| `council/f_20` | `v1.20.0` | 1.20.0 | Capability registry; `list-capabilities` blob |

For the full narrative, see **[LOG.md](LOG.md)**.

---

## Repository Structure (council/f_20)

```
seed.py              — kernel
promote.py           — linker
evolve.py            — evolution engine
bootstrap.py         — system seeder
infer.py             — LLM bridge

blob_vault/          — content-addressed store (created at runtime)
blob_bytecode/       — compiled .pyc cache (created at runtime)
manifest.json        — golden record (created at bootstrap)
audit.log            — append-only JSONL history (created at bootstrap)

docs/
  adr/               — architecture decision records (ADR-001 through ADR-016, CAP-004/005)
  specs/             — original design specification documents
    f(undefined).md  — genesis specification
    f(7).md          — correctness layer spec
    f(8).md          — inference-generated candidates spec
    f(9).md          — adversarial test authorship + capability blobs spec

tests/
  test_f20.py        — f_20 capability registry test suite
  test_f19.py        — f_19 federation test suite
  test_f18.py        — f_18 hash-bridge test suite
  (test_f*.py ...)

ARCHITECTURE.md      — current-state reference (components, protocols, data flows)
LOG.md               — narrative history f_0 through f_20
AGENTS.md            — agent collaboration notes
ZK_PROTOCOL.md       — ZK circuit integration notes
```

---

## ADR Index

Architecture decisions are in `docs/adr/`. Key ones:

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | blake3 as canonical vault hash | Accepted (f_12) |
| ADR-002 | Scrubbed scope ABI | Accepted (f_0) |
| ADR-003 | Manifest self-sealing | Accepted (f_0) |
| ADR-004 | Content-addressed vault | Accepted (f_0) |
| ADR-013 | Governance as expression | Accepted (f_13) |
| ADR-015 | Multihash address format | Accepted (f_16) |
| ADR-016 | GOKR convergence protocol | Accepted (f_11) |
| CAP-004 | p95 latency signal | Accepted (f_2) |
| CAP-005 | Burstiness penalty | Accepted (f_3) |

---

## Safety

This system executes arbitrary, dynamically-loaded code blobs. The safety boundary is the
scrubbed scope: blobs receive only `context` and `log`. They cannot import os, sys, or
call `open()`, `eval()`, `exec()`, or `subprocess` — Pass 2 (SafetyVerification) blocks
all such patterns at promotion time.

For production use, additionally run in a network-isolated container with a non-root user.

---

*"Logic exists in the Intermezzo — the space between movement."*
