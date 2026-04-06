# Synapse: The D-JIT Logic Fabric

> **f(unknown) → f(0) → f(1) → f(n)**
> *Each branch is a mutation. Each tag is a stable collapse of potential into form.*

---

## Start Here

**[λ.md](λ.md)** — The bootstrap record. The minimal self-describing document that
defines what this system is. A new participant who reads only this file can orient
completely and begin contributing. It is the key on the record.

---

## The Why: A Marketplace for Trusted Logic

Imagine you need an algorithm. Someone else already wrote it, verified it, and proved it
works. With Synapse, you don't rewrite it — you *reference its hash*, and the fabric
resolves, plans, and executes it on your behalf, wherever it lives.

**A marketplace for logic where any algorithm can be defined once, then implemented and
verified by multiple actors in a trusted, content-addressed way.**

Synapse provides:

- **Guardrails around generated and executed code** — every blob runs in a scrubbed scope
  with explicit I/O contracts, not in the ambient environment
- **A constrained fabric to weave solutions into** — agents call hashes against a fabric
  that enforces the ABI, routes to the right runtime, and records every action in telemetry
- **Infrastructure for agents that build agents** — the system is self-referential; the
  layers that execute blobs are themselves blobs, resolved and improved through the same fabric
- **A governed convergence protocol** — multiple AI systems contribute proposals to shared
  objectives; synthesis across independent sessions produces stronger signal than any single agent

---

## Three Metaphors, Six Vantages

The system is the same structure observed from different distances.

**Three founding metaphors** (why it exists):

| Metaphor | Meaning |
|----------|---------|
| 🧬 **The Synapse** | Transmission emerges from the weight of the connection, not the storage of data |
| 🍄 **The Mycelium** | The `blob_vault` is a persistent substrate feeding the entire mesh |
| 🌿 **The Rhizome** | A non-hierarchical system where any point connects to any other |

**Six vantages** (how to read the formal structure):

| Vantage | Core question |
|---------|--------------|
| `[ALGEBRAIST]` | What transformations preserve identity? |
| `[JURIST]` | What is the chain of custody? |
| `[BIOLOGIST]` | What survives? What is inside vs. outside? |
| `[PHYSICIST]` | What is conserved? |
| `[BUILDER]` | What carries the weight? |
| `[MATHEMATICIAN]` | What cannot be simplified further? |

Full six-vantage treatment of all five constitutional invariants: **[docs/INVARIANTS.md](docs/INVARIANTS.md)**

---

## The Five Constitutional Invariants

The minimal set from which everything else derives. These are not rules — they are the
conditions under which this system *is* this system.

```scheme
(invariant I:identity        (= (address x) (multihash (content x))))
(invariant II:inviolability  (forall (t) (append-only (vault t))))
(invariant III:self-description (= address (encode algorithm digest-length digest)))
(invariant IV:recursion      (= f_n (apply f_{n-1} f_{n-1})))
(invariant V:governance      (forall (g) (if (governs? g x) (expression? g vault))))
```

**Leave the invariants in roots.** Simplifying any one of them destroys the property
it protects — as √2 ≈ 1.414 loses the algebraic property that made it useful.

---

## Architecture: The 4-Layer Stack

Every invocation passes through four layers, each resolved as a blob at runtime:

| Layer | Name | Role |
|:---:|:---|:---|
| **L1** | **Interface** (The Proxy) | Normalizes intent, validates inputs, stamps `trace_id` |
| **L2** | **Discovery** (The Librarian) | Resolves content-hashes across vault tiers |
| **L3** | **Planning** (The Broker) | Market arbitrage: picks execution node by Cost × Latency × Trust |
| **L4** | **Binding** (The Engine) | Injects blob into scrubbed sandbox; handles retries and polyglot runtimes |

### The ABI Contract

All blobs follow the Scope-Exchange Protocol:

- **Input:** `context` (data dict) + `log(msg)` (telemetry sink) injected into scope
- **Output:** blob **must** assign its result to the variable `result`
- **Isolation:** scrubbed scope — blobs cannot access linker internals unless explicitly injected

---

## The Evolutionary Arc

```
f(unknown) → f(undefined)
                  │
     ┌────────────┴────────────┐
     │                         │
Non-council lineage      Council lineage
(solo agent)             (governed, multi-agent)
     │                         │
  f_0–f_8+               f_0–f_14 (current: v1.14.0)
  (untagged past f_2)
                         f_n = f_{n-1}(f_{n-1})
```

> **Implementation lives on experiment branches, not `main`.**
> `main` is stable docs, pointers, and the bootstrap record.

### Council Lineage — Milestone Summary

| Tag | Identity | Key capability added |
|:----|:---------|:--------------------|
| `v1.0.0` | `f_0` | Self-hosting + closed feedback loop |
| `v1.1.0` | `f_1 = f_0(f_0)` | First self-modification cycle |
| `v1.4.0` | `f_4 = f_3(f_3)` | Governed feedback loop |
| `v1.6.0` | `f_6 = f_5(f_5)` | Council as governed blob — reviewer chain, trust weighting |
| `v1.7.0` | `f_7 = f_6(f_6)` | Design-by-Contract layer — executable specs |
| `v1.9.0` | `f_9 = f_8(f_8)` | Adversarial test authorship — two-model pipeline |
| `v1.10.0` | `f_10 = f_9(f_9)` | Guided mutation goals from audit log trends |
| `v1.11.0` | `f_11 = f_10(f_10)` | Goal/OKR blob type + GOKR execution engine |
| `v1.12.0` | `f_12 = f_11(f_11)` | blake3 canonical hash; multihash address format foundation |
| `v1.13.0` | `f_13 = f_12(f_12)` | Engine-as-expression: execution policy moves into a promotable vault expression |
| `v1.14.0` | `f_14 = f_13(f_13)` | logic/engine type: honest kernel trust boundary; exec() allowed by type, not naming trick (current) |

Full lineage: [docs/experiments.md](docs/experiments.md) · Full decision record: [docs/adr/](docs/adr/)

---

## The GOKR — Current Objective

*What we are building toward. The formal blob form lives in [λ.md §VIII](λ.md).*

**Objective:** Build a self-modifying content-addressed logic fabric where any capable
agent — given only λ.md's address — can orient, contribute a valid proposal, and
participate in the governed evolution of capabilities toward declared objectives.

| Phase | Milestone | Key result |
|:------|:----------|:-----------|
| I — f_11 | Govern the objective | GOKR as vault blob, not Python string |
| II — f_12 | Session protocol | Cold-start → proposal-ready in ≤ 5 tool calls |
| III — f_13 | First convergence run | 3 models, 1 shared GOKR, IAC synthesis |
| IV — f_14 | λ.md as blob zero | Genesis address fixed in vault |
| V — f_15+ | Graph query layer | Semantic similarity across expression space |

---

## Quick Start

> You are on `main`. To run the fabric, check out an experiment branch first.

```bash
git clone https://github.com/BrianLN-AI/synapse.git
cd synapse

# Read the bootstrap record first
cat λ.md

# Check out the latest council release to run the fabric
git checkout council/f_20

# Bootstrap the system
python seed.py promote manifest.json

# Store a blob
echo 'result = context.get("x", 0) * 2' > double.py
HASH=$(python seed.py put double.py)

# Invoke a blob
python seed.py invoke "$HASH" '{"x": 21}'
# → { "result": 42, "telemetry_hash": "...", "status": "success" }
```

**Requirements:** Python 3.10+ · Node.js optional (polyglot blobs, f_1+) · Docker recommended

---

## Safety & Threat Model

Synapse executes arbitrary, dynamically-loaded code blobs. This is intentional — and real risks follow:

| Risk | Description |
|:-----|:------------|
| **Arbitrary code execution** | Blobs are `exec()`'d. A malicious blob can do anything the process user can do |
| **Credential exposure** | Secrets in environment variables are accessible to blobs |
| **Network egress** | Blobs can open sockets unless network is restricted |
| **Supply-chain blobs** | Remote vault tiers could serve untrusted blobs if not authenticated |

**Hardening:**

```bash
docker run --rm -it \
  --network none \
  --read-only \
  --tmpfs /tmp \
  --cap-drop ALL \
  --user 1000:1000 \
  -v "$(pwd)/blob_vault:/app/blob_vault:ro" \
  -v "$(pwd):/app:ro" \
  -w /app \
  python:3.12-slim python seed.py invoke <hash>
```

> Treat every blob like a shell script downloaded from the internet.
> The ABI contract is not a security boundary — it is a capability boundary.
> For security, use Docker isolation and network restriction.

---

## Contributing

Contributing to the fabric means contributing to the GOKR:

1. Read [λ.md](λ.md) — understand the five invariants and the current objective
2. Check out the experiment branch you want to extend (`council/f_14` or later)
3. Contribute a proposal: write a `proposal/roadmap` blob referencing the current GOKR hash
4. Follow the ABI Contract — every blob assigns to `result` and uses `log()`
5. Open a PR against the appropriate `f_<n>` branch (not `main`)

See [docs/adr/ADR-016-gokr-convergence-protocol.md](docs/adr/ADR-016-gokr-convergence-protocol.md)
for the full multi-agent convergence protocol.

---

## Key Documents

| Document | Purpose |
|:---------|:--------|
| [λ.md](λ.md) | Bootstrap record — start here |
| [docs/VISION.md](docs/VISION.md) | The thesis — what Synapse is and why |
| [docs/KNOWLEDGE.md](docs/KNOWLEDGE.md) | Current state map — everything we know |
| [docs/METAPHORS.md](docs/METAPHORS.md) | Unified metaphor map — all systems of metaphor |
| [docs/genesis/f(undefined).md](docs/genesis/f(undefined).md) | Genesis specification |
| [docs/genesis/METAPHORS.md](docs/genesis/METAPHORS.md) | Founding metaphors |
| [docs/design/SYNTHESIS.md](docs/design/SYNTHESIS.md) | Technical synthesis — unified model |
| [docs/INVARIANTS.md](docs/INVARIANTS.md) | Constitutional invariants |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Protocol specification |
| [docs/SECURITY.md](docs/SECURITY.md) | Security audit findings |
| [docs/PROCESS.md](docs/PROCESS.md) | Iteration cycle, worktree protocol |
| [docs/adr/](docs/adr/) | Architectural decisions |
| [docs/explore/](docs/explore/) | Prior art — MOO, Smalltalk, BEAM, biology, ethics, physics |
| [docs/sessions/](docs/sessions/) | Session transcripts |

---

<!-- AUTO-GENERATED:START -->
<!-- This section is automatically updated by scripts/update_readme.py on every push. Do not edit manually. -->

## 📊 Evolution Snapshots

**Last updated:** 2026-04-03 15:27 UTC

### Branches
- `copilot/update-documentation-experiment-lineages`
- `council/f_0`
- `council/f_1`
- `council/f_10`
- `council/f_11`
- `council/f_12`
- `council/f_13`
- `council/f_14`
- `council/f_15`
- `council/f_16`
- `council/f_17`
- `council/f_18`
- `council/f_19`
- `council/f_2`
- `council/f_20`
- `council/f_3`
- `council/f_4`
- `council/f_5`
- `council/f_6`
- `council/f_7`
- `council/f_8`
- `council/f_9`
- `docs/adr-bare-decisions`
- `docs/adr-council-decisions`
- `docs/genesis-worldview`
- `f_0`
- `f_1`
- `f_10`
- `f_12`
- `f_2`
- `f_3`
- `f_4`
- `f_5`
- `f_6`
- `f_7`
- `f_8`
- `f_9`
- `main`

### Tags
- `v1.20.0`
- `v1.19.0`
- `v1.18.0`
- `v1.17.0`
- `v1.16.0`
- `v1.15.0`
- `v1.14.0`
- `v1.13.0`
- `v1.12.0`
- `v1.11.0`
- `v1.10.0`
- `v1.9.0`
- `v1.8.0`
- `v1.7.0`
- `v1.6.0`
- `v1.5.0`
- `v1.4.0`
- `v1.3.0`
- `v1.2.0`
- `v1.1.0`
- `v1.0.0`
- `unknown`
- `undefined`
- `f_11`
- `f_10`
- `f_9`
- `f_8`
- `f_7`
- `f_6`
- `f_4`
- `f_3`
- `f_2`
- `f_1`
- `f_0`

<!-- AUTO-GENERATED:END -->

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*"Logic exists in the Intermezzo — the space between movement."*

*The address of λ.md is the address of everything.*
