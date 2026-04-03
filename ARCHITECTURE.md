# D-JIT Logic Fabric — Architecture Reference

**Version:** f_20 (v1.20.0)
**Status:** Current-state reference. No history. For the journey, see LOG.md.

---

## What It Is

The D-JIT Logic Fabric is a content-addressed, self-evolving compute runtime. Every piece of
executable logic — and every artifact that governs, tests, contracts, or measures that logic —
is stored in a content-addressed vault identified by a blake3 hash. Nothing executes unless it
is in the vault. Nothing is promoted to the manifest unless it clears a six-pass review and
carries a council approval artifact.

The system rewrites its own logic blobs through a governed evolution loop: measure, generate
candidate, review, benchmark, promote. The same governance chain that guards external logic
guards the evolution engine itself.

---

## System Map

```
┌──────────────────────────────────────────────────────────────────────┐
│  seed.py (kernel)                                                    │
│  ├── VAULT_DIR/           content-addressed blob store               │
│  ├── BYTECODE_DIR/        compiled .pyc cache (L2)                   │
│  ├── manifest.json        golden record — what is currently promoted │
│  └── audit.log            append-only JSONL promotion history        │
│                                                                      │
│  promote.py (linker)                                                 │
│  ├── triple_pass_review() — 6-pass gate before any promotion         │
│  ├── promote()            — manifest update + audit entry            │
│  ├── register_capability() / list_capabilities()                     │
│  ├── register_peer() / list_peers()                                  │
│  └── promote_bridge() / lookup_bridge()                              │
│                                                                      │
│  evolve.py (evolution engine)                                        │
│  ├── run_all()            — evolve all governed labels               │
│  ├── evolve_one()         — evolve a single label                    │
│  └── evolve_engine()      — governed path for logic/engine blob      │
│                                                                      │
│  bootstrap.py             — seeds the system to v1.0.0               │
│  infer.py                 — LLM bridge (candidate generation, test cases) │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The Blob

The fundamental unit. Every blob is a JSON envelope:

```json
{ "type": "<blob-type>", "payload": "<string>" }
```

The blob's address is the blake3 hash of this envelope, serialized with sorted keys:

```
address = blake3(json.dumps({"payload": ..., "type": ...}, sort_keys=True))
```

Blobs are immutable and idempotent. Same content always produces the same address. The vault
never rewrites a blob — `put()` is a no-op if the address already exists.

### Address Format (ADR-015)

Addresses use the multihash prefix convention:

```
blake3:af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
sha256:e3b0c44298fc1c149afbf4c8996fb924...
poseidon:7f3c21...
```

The vault filesystem uses bare hex names (colons are not safe on all filesystems). The prefix
lives in the public API and the manifest. `_to_bare_hex()` / `_to_multihash()` normalize at
every boundary. Bare hex addresses (legacy) are treated as implicit `blake3`.

---

## Blob Types

| Type | Payload | Governed? | Purpose |
|------|---------|-----------|---------|
| `logic/python` | Python source | Yes | Executable logic — discovery, planning, etc. |
| `logic/engine` | Python source | Yes (separate path) | Kernel execution policy — invoked by `_load_engine()` |
| `council/reviewer` | JSON | Yes | Trust anchor — authorizes promotions |
| `council/approval` | JSON | No (generated) | Point-in-time approval artifact |
| `contract/definition` | JSON (pre/post/invariant fn source) | Yes | Behavioral contract for a label |
| `test/case` | JSON | Yes | Probe input + expected output for a label |
| `goal/okr` | JSON | Yes | OKR with key results; drives mutation goals |
| `feedback/outcome` | JSON | Yes | Caller-observed outcome for a logic blob |
| `telemetry/artifact` | JSON | No (generated) | Invocation record — latency, memory, log lines |
| `meta/hash-bridge` | JSON | Yes | Links a blake3 vault address to a ZK address |

---

## The Vault

`seed.VAULT_DIR` (`./blob_vault/`) — a flat directory. Each file is named by the bare blake3
hex digest of its contents. No directories, no namespacing — the hash is the address.

**Core operations:**

```python
seed.put(blob_type, payload)     → "blake3:<hex>"   # write (idempotent)
seed._raw_get(address)           → dict             # read (BIOS-level, no engine delegation)
seed.invoke(address, context)    → Any              # execute a logic blob
seed.record_feedback(...)        → "blake3:<hex>"   # write feedback/outcome
seed.put_bridge(vault_addr, zk_addr, proof=None) → "blake3:<hex>"  # write hash-bridge
seed.resolve_bridge(address)     → dict | None      # find bridge by either address
```

`_raw_get` is the BIOS read path — it reads directly from the filesystem without delegating
to any blob. This prevents infinite recursion during bootstrap and engine loading.

---

## The Manifest

`./manifest.json` — the golden record. Authoritative statement of what is currently promoted.

```json
{
  "version": "1.20.0",
  "hash": "<blake3 of the manifest content itself>",
  "promoted_at": "2026-04-03T...",
  "blobs": {
    "discovery":         { "logic/python": "blake3:<hex>", "contract/definition": "blake3:<hex>", ... },
    "planning":          { "logic/python": "blake3:<hex>", ... },
    "telemetry-reader":  { "logic/python": "blake3:<hex>", ... },
    "list-capabilities": { "logic/python": "blake3:<hex>" },
    "engine":            { "logic/engine": "blake3:<hex>" }
  },
  "reviewers": {
    "<reviewer-id>": "blake3:<hex>"
  },
  "capabilities": {
    "discovery":          { "description": "...", "tags": [...], "registered_at": "..." },
    "planning":           { "description": "...", "tags": [...], "registered_at": "..." },
    "telemetry-reader":   { "description": "...", "tags": [...], "registered_at": "..." },
    "list-capabilities":  { "description": "...", "tags": [...], "registered_at": "..." }
  },
  "federation": {
    "peers": ["https://vault.example.com"]
  }
}
```

The manifest's own hash is computed over all fields except `"hash"` itself and stored in
`manifest["hash"]`. This makes it a self-sealing record — tampering changes the hash.

---

## The Kernel (seed.py)

The kernel is the minimal BIOS. It has one fixed dispatch: `_load_engine()`. It cannot be
changed by any blob — it is not in the vault, it is not governed. Its invariants are:

1. **Content-addressing** — every blob is identified by hash of its content
2. **One fixed dispatch** — `_load_engine()` reads `manifest["blobs"]["engine"]` and exec's it
3. **ABI contract** — all executed logic blobs must set a `result` variable; everything else in scope is scrubbed
4. **Telemetry** — every invocation writes a `telemetry/artifact` blob

The kernel has two execution paths:

- **Engine path** (normal): delegates to the promoted `logic/engine` blob
- **Kernel path** (bootstrap / pre-engine): `_invoke_kernel()` handles invocation directly

Both paths enforce the ABI contract and write telemetry. The engine path adds L2 bytecode
cache (disk-persisted `.pyc` via `marshal`). The kernel path uses L1 only.

### Execution Model

When `invoke(address, context)` is called:

```
invoke(address, context)
  → _load_engine()           # check manifest for promoted engine blob
  │   hit → engine.invoke()  # engine handles everything including bytecode cache
  └   miss → _invoke_kernel()
              ├── _raw_get(address)         # load blob from vault
              ├── compile(payload, ...)     # compile to code object (L1 cache)
              ├── exec(code, scrubbed_scope) # {context, log} only — no kernel internals
              ├── check scope["result"]     # ABI: must be set
              └── _record_telemetry(...)    # write telemetry/artifact to vault
```

The scrubbed scope is the security boundary. A blob cannot see `VAULT_DIR`, kernel functions,
or any other blob. It receives `context` (a dict) and `log` (a callable) only.

---

## The Promotion Pipeline (promote.py)

Before any blob can be referenced in the manifest, it passes a six-pass review gate and
carries a council approval artifact.

### Triple-Pass Review (6 passes)

```python
triple_pass_review(blob_hash, label=None) → {"passes": [...], "approved": bool}
```

| Pass | Name | What it checks |
|------|------|----------------|
| 1 | StaticAnalysis | Required fields, syntax validity (all `logic/*`), JSON structure (`contract/definition`, `test/case`, `goal/okr`, `meta/hash-bridge`) |
| 2 | SafetyVerification | Forbidden patterns in `logic/python` blobs: `import os`, `import sys`, `__import__`, `open()`, `eval()`, `exec()`, `subprocess`, `shutil`, `VAULT_DIR` |
| 3 | ProtocolCompliance | Dry-run ABI check — invoke with probe context, fail only if `result` not set |
| 4 | FeedbackIntegrity | `feedback/outcome` blobs: valid outcome enum, confidence in range, referenced logic blob exists in vault |
| 5 | ReviewerIntegrity | `council/reviewer` blobs: required fields, `trust_weight` in (0.0, 1.0] |
| 6 | ContractCompliance | `logic/python` vs promoted `contract/definition` for the label — pre/post/invariant must hold |

Pass 2 (SafetyVerification) is skipped for `logic/engine` blobs — exec is their purpose.

### Council Approval

```python
issue_council_approval(blob_hashes, reviewer_hash) → "blake3:<hex>"
```

A `council/approval` blob records: reviewer hash, approved blob hashes, timestamp. It is
itself stored in the vault and its address is passed to `promote()`. The promotion path verifies
the approval blob exists and was issued by a registered reviewer.

### Promotion

```python
promote(label, blob_hashes, council_approval_hash, version=None)
```

1. Verify all blobs clear triple-pass review
2. Verify council approval artifact
3. Update `manifest["blobs"][label]` with new hashes
4. Increment version (`"1.19.0"` → `"1.20.0"`)
5. `_write_manifest()` — recompute manifest hash
6. `_write_audit()` — append JSONL entry to `audit.log`

The audit log entry includes: event type, label, blob hashes, reviewer, version, timestamp.

---

## The Evolution Loop (evolve.py)

The evolution loop drives the self-modification cycle. It measures existing blobs, generates
candidates via LLM, reviews and benchmarks them, and promotes winners.

### evolve_one(label)

```
evolve_one(label)
  ├── evaluate(label, current_hash)         # current fitness signals
  │     ├── telemetry stats (latency_ms, memory_kb, p95)
  │     ├── feedback score (pass/fail/partial outcomes, confidence-weighted)
  │     └── OKR signals (from promoted goal/okr blob for label)
  ├── _derive_mutation_goal(label, signals) # what to improve
  ├── infer.generate_candidate(...)         # LLM generates new payload
  ├── triple_pass_review(candidate)         # gate
  ├── benchmark(label, old_hash, new_hash)  # head-to-head: 5 rounds each
  │     └── invoke(hash, context) × N, measure latency + memory
  ├── compare fitness: new > old?
  │   yes → issue_council_approval + promote() → outcome: "promoted"
  │   no  → outcome: "stable"
  └── infer.generate_test_cases()           # generate new test/case blobs for next cycle
```

### evolve_engine()

The engine blob (`logic/engine`) has its own governed upgrade path:

```
evolve_engine()
  ├── infer.generate_candidate() with engine-specific contract
  ├── _verify_engine_abi(candidate)   # must define invoke() and record_feedback()
  ├── _benchmark_engine(...)          # isolated sandbox — never touches live manifest
  └── promote via evolve-engine reviewer → manifest["blobs"]["engine"]
```

The engine is explicitly excluded from `run_all()` — it is too critical to evolve in a bulk
pass. It must be invoked separately.

### run_all()

Discovers all labels with a `logic/python` blob in `manifest["blobs"]`. Bootstraps
`list-capabilities` if absent. Runs `evolve_one()` on each label, with `telemetry-reader`
first so its signals are fresh for subsequent benchmarks.

### Fitness Formula

Planning blob (v8) scoring:

```
fitness = success_rate × feedback_score
        × (1 / normalized_effective_latency)
        × (1 / normalized_memory)
        × integrity_factor
```

`effective_latency = p95_latency_ms × burstiness_penalty`
where `burstiness_penalty = max(1, p95/avg / BURST_THRESHOLD)`.

---

## Governance Chain

```
bootstrap reviewer (trust root)
  └── self-grounding — no prior approver; created at bootstrap
  └── promotes: evolve-engine reviewer, all f_0 core blobs

evolve-engine reviewer
  └── promoted by: bootstrap reviewer
  └── authorized_types: logic/python, logic/engine, council/reviewer,
                        contract/definition, test/case, goal/okr,
                        feedback/outcome, meta/hash-bridge
  └── promotes: all blobs via evolve_one() and run_all()
```

Every `council/reviewer` blob carries `trust_weight` (0.0, 1.0] and an `authorized_types`
list. A reviewer can only approve blobs whose type appears in its list. The first reviewer
has no upstream approver — it is the self-grounding trust anchor.

---

## Core Logic Blobs

### discovery (v9, federation-aware)

Finds the best available version of a given logic blob.

**Input context:** `{"hash": "<blake3>", "vault_dir": "<path>"}`

**Protocol:**
1. L1 in-process cache → L2 vault → L3 remote (vault URL in context)
2. L4 federation peers from `manifest["federation"]["peers"]` with blake3 content verification

**Output:** `result = {"hash": "<best-hash>", "source": "l1|l2|l3|l4"}`

### planning (v8, burstiness-aware)

Selects the best candidate blob from a set of evaluated candidates.

**Input context:** `{"candidates": [{"hash", "success_rate", "latency_ms", "p95_latency_ms", "integrity", "cost", "invocation_count", "feedback_score", "feedback_count"}]}`

**Output:** `result = {"selected_hash": "<hash>", "fitness": <float>}`

### telemetry-reader (v8)

Aggregates telemetry artifacts from the vault for a set of logic blobs.

**Input context:** `{"vault_dir": "<path>"}`

**Output:** `result = {<hash>: {"count", "avg_latency_ms", "p95_latency_ms", "avg_memory_kb", "errors"}}`

### list-capabilities (v1)

Returns a structured list of all registered capabilities.

**Input context:** `{"capabilities": manifest["capabilities"], "blobs": manifest["blobs"]}`

**Output:** `result = [{label, description, tags, registered_at, current_hash}, ...]` (sorted by label)

---

## Capability Registry

`manifest["capabilities"]` records every named capability in the fabric. A capability is
a logic blob with a human-readable description and tags.

```python
promote.register_capability(label, description, tags=[...])
promote.list_capabilities()    → [{"label", "description", "tags", "registered_at", "current_hash"}, ...]
promote.get_capability(label)  → dict | None
```

Bootstrap registers `discovery`, `planning`, `telemetry-reader`. `run_all()` registers
`list-capabilities` on first run. All registrations write to `audit.log`.

The `list-capabilities` blob is itself a governed, promotable `logic/python` blob — the
registry is queryable through the same invocation mechanism as any other blob.

---

## Hash-Bridge Expression (f_18 / ADR-015)

When vault addressing (blake3) and ZK circuit addressing (poseidon) diverge, a
`meta/hash-bridge` blob makes the relationship explicit and auditable:

```json
{
  "type": "meta/hash-bridge",
  "payload": {
    "vault_address": "blake3:af1349b9...",
    "zk_address":    "poseidon:7f3c21...",
    "proof":         null
  }
}
```

The bridge blob is itself stored in the vault at its own blake3 address. The `proof` field is
reserved for a ZK proof that both addresses hash the same content; it may be null until ZK
infrastructure is wired in.

```python
seed.put_bridge(vault_address, zk_address, proof=None) → "blake3:<hex>"
seed.resolve_bridge(address)   → dict | None   # lookup by either address
promote.promote_bridge(hash, council_approval_hash)
promote.lookup_bridge(vault_address) → dict | None
```

---

## Federation (f_19)

Federation allows one vault to resolve blobs from peer vaults. The peer list lives in
`manifest["federation"]["peers"]`. Trust is content-based, not network-based: a peer
response is only accepted if its blake3 hash matches the address requested.

```python
promote.register_peer(url)         # add peer to manifest
promote.list_peers()               # list registered peers
promote.remove_peer(url) → bool    # remove peer
```

`discovery` (v9) implements the federation lookup as L4 (after L1 in-process, L2 vault, L3
single remote URL). All peer fetches verify content hash before returning. A peer that returns
wrong content is silently bypassed.

---

## Telemetry and Feedback Loop

**Every invocation** writes a `telemetry/artifact` blob:

```json
{
  "invoked":       "blake3:<hex>",
  "timestamp_utc": "2026-04-03T...",
  "latency_ms":    12.345,
  "memory_kb":     4.2,
  "log":           ["..."],
  "error":         null
}
```

`_LAST_TELEMETRY[logic_hash]` tracks the most recent telemetry address for each logic blob.
This is a shared dict between kernel and engine — feedback recorded via either path links to
the same telemetry records.

**Caller-observed feedback** is recorded as `feedback/outcome`:

```json
{
  "invoked":          "blake3:<hex>",
  "invocation_telem": "blake3:<hex>",
  "outcome":          "pass|fail|partial",
  "confidence":       0.9,
  "reviewer":         "caller",
  "reviewer_hash":    "blake3:<hex>",
  "timestamp_utc":    "..."
}
```

The feedback score fed into the fitness formula is confidence-weighted: high-confidence
failures penalize more than low-confidence ones. A blob with fewer than `MIN_FEEDBACK` (3)
outcomes uses a neutral score.

---

## Bootstrap Sequence

```
bootstrap.run()
  ├── seed.put() all core blobs (discovery, planning, telemetry-reader, engine)
  ├── promote.bootstrap_reviewer() — trust root, no prior approver
  ├── promote.promote_reviewer(evolve-engine) — second reviewer, authorized for all types
  ├── promote.issue_council_approval() for each core blob
  ├── promote.promote(discovery / planning / telemetry-reader / engine) → v1.0.0
  └── promote.register_capability(discovery / planning / telemetry-reader)
```

After `bootstrap.run()`, the manifest is at v1.0.0 and the system is self-hosting: all
subsequent operations (invocation, feedback, evolution) route through the vault.

---

## Audit Log

`./audit.log` — append-only JSONL. Every state-modifying operation writes an entry:

| `event` | Written by | Fields |
|---------|-----------|--------|
| `promote` | `promote()` | label, blob_hashes, reviewer, version, timestamp |
| `promote_reviewer` | `promote_reviewer()` | reviewer_id, reviewer_hash, timestamp |
| `promote_bridge` | `promote_bridge()` | bridge_hash, vault_address, zk_address, timestamp |
| `register_peer` | `register_peer()` | url, timestamp |
| `remove_peer` | `remove_peer()` | url, timestamp |
| `register_capability` | `register_capability()` | label, description, tags, timestamp |

---

## File Inventory

```
seed.py          — kernel (vault, BIOS read, engine dispatch, hash-bridge)
promote.py       — linker (triple-pass review, promotion, registry, federation)
evolve.py        — evolution engine (run_all, evolve_one, evolve_engine, blob versions)
bootstrap.py     — system seeder (runs once to establish v1.0.0)
infer.py         — LLM bridge (generate_candidate, generate_test_cases)

blob_vault/      — content-addressed blob store (bare hex filenames)
blob_bytecode/   — compiled .pyc cache (L2 bytecode persistence)
manifest.json    — golden record
audit.log        — append-only JSONL history

docs/adr/        — architecture decision records (ADR-001 through ADR-016, CAP-004/005)
LOG.md           — narrative history f_0 through f_20
ARCHITECTURE.md  — this document
```
