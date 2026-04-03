# Synapse: The D-JIT Logic Fabric

> **f(unknown) → f(0) → f(1) → f(n)**  
> *Each branch is a mutation. Each tag is a stable collapse of potential into form.*

---

## 🧠 What Is Synapse?

**Synapse** is a **Distributed Just-In-Time (D-JIT) Logic Fabric** — a content-addressed, protocol-oriented compute mesh that lets agentic AI systems build, share, and invoke trusted tools and code with other agents and systems.

### The "Why": A Marketplace for Trusted Logic

Imagine you need an algorithm. Someone else already wrote it, verified it, and proved it works. With Synapse, you don't rewrite it — you *reference its hash*, and the fabric resolves, plans, and executes it on your behalf, wherever it lives.

This is the core idea: **a marketplace for logic where any algorithm can be defined once, then implemented and verified by multiple actors in a trusted, content-addressed way.**

Synapse provides:

- **Guardrails and retaining walls** around generated and executed code — every blob runs in a scrubbed scope with explicit I/O contracts, not in the ambient environment.
- **A constrained fabric to weave solutions into** — agents don't call arbitrary code; they call hashes against a fabric that enforces the ABI, routes to the right runtime, and records every action in telemetry.
- **Infrastructure for building agents that build agents** — the system is self-referential: the layers that execute blobs are themselves blobs, resolved and improved through the same fabric.

### Core Philosophy

Traditional computing is obsessed with **nodes** (servers, functions, containers). Synapse shifts focus to the **gap** — the space where logic is *negotiated, brokered, and bound*.

Three metaphors guide the design:

- 🧬 **The Synapse** — transmission emerges from the weight of the connection, not the storage of data.
- 🍄 **The Mycelium** — the `blob_vault` is a persistent substrate feeding the entire mesh.
- 🌿 **The Rhizome** — a non-hierarchical system (Deleuze & Guattari) where any point connects to any other.

### The Evolutionary Arc

Two parallel experiment lineages evolve from the same shared base:

```text
[tag: unknown]  →  [tag: undefined]
                         │
              ┌──────────┴──────────────┐
              │                         │
   Non-council lineage           Council lineage
   (solo agent)                  (governed, multi-agent)
              │                         │
   Phase 1–6 build                f(0) genesis
              │                    COUNCIL.md
   [tag: f_0] af6b1e0              Phases 1–3
   [tag: f_1] 1e4dadbd             [tag: v1.0.0] c31f394  f_0
   [tag: f_2] 77df2c3e             [tag: v1.1.0] cf6ddd4  f_1 = f_0(f_0)
                                   [tag: v1.2.0] 9c7fb35  f_2 = f_1(f_1)
                                   [tag: v1.3.0] ec285e3  f_3 = f_2(f_2)
                                   [tag: v1.4.0] b39ea5f  f_4 = f_3(f_3)
                                   [tag: v1.5.0]          f_5 = f_4(f_4)
                                   [tag: v1.6.0]          f_6 = f_5(f_5)
                                   [tag: v1.7.0]          f_7 = f_6(f_6)
                                   [tag: v1.8.0]          f_8 = f_7(f_7)
                                   [tag: v1.9.0]          f_9 = f_8(f_8)
                                   [tag: v1.10.0]         f_10 = f_9(f_9)
                                   [tag: v1.11.0]         f_11 = f_10(f_10)
                                   [tag: v1.12.0]         f_12 = f_11(f_11)
                                   [tag: v1.13.0]         f_13 = f_12(f_12)
```

> **No experiment code lives on `main` yet.** `main` is stable docs and pointers only.
> See [docs/experiments.md](docs/experiments.md) and [docs/providence.md](docs/providence.md) for full details.

## 🧬 Two Experiment Lineages

Synapse is developed **agentically** — AI agents and human principals co-evolve the fabric, with the full derivation history preserved as a **providence tree** in git.

### Non-Council Track (`f_*` branches + `f_*` tags)

Started from `undefined` directly, without a governance layer. A solo agent built the system phase-by-phase, culminating in a "wavefunction collapse" commit that marks the first stable form.

- **Branches:** `f_0`, `f_1`, `f_2`
- **Tags (lightweight):** `unknown` → `undefined` → `f_0` → `f_1` → `f_2`
- **Origin commit:** `af6b1e0` — *"The Wavefunction Collapse: f(undefined) → f_0"*

### Council Track (`council/f_*` branches + `v1.*` tags)

Started from a distinct genesis commit (`f(0)`) and immediately introduced `COUNCIL.md` — a collective intelligence governance protocol. Every release milestone is an annotated tag with a tagger identity and a release summary.

- **Branches:** `council/f_0` through `council/f_13`
- **Tags (annotated):** `v1.0.0` through `v1.13.0`
- **Self-modification identity:** `f_n = f_{n-1}(f_{n-1})` — each cycle uses the previous version to produce the next

> Note: `council/f_0` is a **branch name** (git uses `/` in names); it is not a directory.

### Current Status

**No merges back to `main` yet** — the experiments are still evolving. `main` is intentionally kept as a stable entry point (docs + pointers only). Latest stable council release: **v1.13.0** (`council/f_13`). See [docs/experiments.md](docs/experiments.md) for lineage details and tag notes, and [docs/providence.md](docs/providence.md) for the provenance model and tagging conventions.

---

## 🛠 Architecture: The 4-Layer Stack

> **Implementation details live on the experiment branches**, not on `main`. The description below is an overview; see `council/f_*` or `f_*` branches for the actual implementation files.

Every invocation passes through four layers, each resolved as a blob at runtime:

| Layer | Name | Role |
| :---: | :--- | :--- |
| **L1** | **Interface** (The Proxy) | Normalizes intent, validates inputs, stamps `trace_id`. |
| **L2** | **Discovery** (The Librarian) | Resolves content-hashes across vault tiers (local → remote). |
| **L3** | **Planning** (The Broker) | Market arbitrage: picks execution node by Cost × Latency × Trust fitness function. |
| **L4** | **Binding** (The Engine) | Physically injects the blob into a scrubbed sandbox; handles retries and polyglot runtimes. |

### The ABI Contract

All blobs **must** follow the Scope-Exchange Protocol:

- **Input:** The linker injects `context` (data dict) and `log(msg)` (telemetry sink) into the execution scope.
- **Output:** The blob **must** assign its result to the variable `result`. Raw `return` statements are prohibited.
- **Isolation:** The scrubbed scope prevents blobs from accessing linker internals unless explicitly injected.

### The BIOS Fallback

To avoid infinite recursion (Discovery needs Discovery to find Discovery):

- `_raw_get(h, is_bios=True)` bypasses blob-based discovery entirely.
- It resolves directly from the filesystem using `manifest.hash` → `manifest.json` → layer hashes.

---

## 🚀 Quick Start

> **You are on `main`.** To run the fabric, check out an experiment branch first (e.g., `git checkout council/f_12` for the latest council release, or `git checkout f_2` for the non-council track).

### Prerequisites

- Python 3.10+
- (Optional) Docker for safe sandboxed execution
- (Optional) Node.js for polyglot blob execution (f_1+)

### 1. Clone and Explore

```bash
git clone https://github.com/BrianLN-AI/synapse.git
cd synapse
git checkout f_2   # or the branch you want to explore
```

### 2. Bootstrap the System

```bash
# Promote the manifest (registers layer blobs, writes manifest.hash)
python seed.py promote manifest.json
```

### 3. Store a Blob

```bash
# Store a Python blob that assigns result
echo 'result = context.get("x", 0) * 2' > double.py
HASH=$(python seed.py put double.py)
echo "Stored blob: $HASH"
```

### 4. Invoke a Blob

```bash
python seed.py invoke "$HASH" '{"x": 21}'
# → { "result": 42, "telemetry_hash": "...", "status": "success" }
```

### 5. Inspect Telemetry

```bash
# List telemetry artifacts
ls blob_vault/telemetry/

# Read a telemetry artifact
python seed.py invoke <telemetry_hash>
```

### 6. Run the MCP Server (f_2+)

```bash
# Start the Model Context Protocol stdio server
python seed.py mcp
# Send JSON-RPC on stdin, e.g.:
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python seed.py mcp
```

### Running Safely in Docker

```bash
docker run --rm -it \
  --network none \
  --cap-drop ALL \
  --user 1000:1000 \
  -v "$(pwd):/app" \
  -w /app \
  python:3.12-slim \
  python seed.py invoke <hash> '{"key":"value"}'
```

---

## 📁 Repository Structure

```text
synapse/
├── seed.py              # The Linker — CLI + MCP Server entry point
├── manifest.json        # Layer hash registry (l1–l4)
├── manifest.hash        # Pointer to current active manifest blob
├── l1_interface.py      # L1 Interface blob (source, stored via PUT on promote)
├── l2_discovery.py      # L2 Discovery blob
├── l3_planning.py       # L3 Planning / Broker blob
├── l4_binding.py        # L4 Binding / Engine blob
├── blob_vault/          # Content-addressed storage (SHA-256 keyed files)
│   └── telemetry/       # Telemetry artifacts from every invocation
├── scripts/
│   └── update_readme.py # Auto-updates the evolution snapshot section of this README
├── .github/
│   └── workflows/
│       └── update-readme.yml  # CI: updates README on every branch/tag push
├── f(undefined).md      # The initial concept: the undefined state
├── f_0.md               # Specification for the f_0 iteration
└── f_1.md               # Specification for the f_1 iteration
```

---

## 🌿 Branching / Evolution Model

Synapse tracks its evolutionary lineage using **git branches as iterations** and **tags as stable collapses**.

### Non-Council Lineage

| Branch / Tag | Description |
| :--- | :--- |
| `main` | Stable docs and pointers only. No experiment code. |
| tag: `unknown` | The Unknown — repo genesis commit, shared base of both lineages |
| tag: `undefined` | The Undefined — seed potential, shared base of both lineages |
| `f_0` (tag: `f_0`) | First stable collapse — "The Wavefunction Collapse: f(undefined) → f_0" |
| `f_1` (tag: `f_1`) | Second iteration |
| `f_2` (tag: `f_2`) | Third iteration |

### Council Lineage

| Branch / Tag | Identity | Description |
| :--- | :--- | :--- |
| `council/f_0` (tag: `v1.0.0`) | `f_0` | Self-hosting + closed feedback loop |
| `council/f_1` (tag: `v1.1.0`) | `f_1 = f_0(f_0)` | First self-modification cycle |
| `council/f_2` (tag: `v1.2.0`) | `f_2 = f_1(f_1)` | p95 + integrity signals end-to-end |
| `council/f_3` (tag: `v1.3.0`) | `f_3 = f_2(f_2)` | Persistent bytecode cache; dynamic tolerance |
| `council/f_4` (tag: `v1.4.0`) | `f_4 = f_3(f_3)` | Governed feedback loop |
| `council/f_5` (tag: `v1.5.0`) | `f_5 = f_4(f_4)` | Governance filter — council approval gate on promote |
| `council/f_6` (tag: `v1.6.0`) | `f_6 = f_5(f_5)` | Council as a governed blob (reviewer chain, trust weighting) |
| `council/f_7` (tag: `v1.7.0`) | `f_7 = f_6(f_6)` | Design-by-Contract correctness layer (contract/definition blob type, Pass 6 ContractCompliance) |
| `council/f_8` (tag: `v1.8.0`) | `f_8 = f_7(f_7)` | Inference-generated candidates via ai CLI / Cloudflare AI Gateway |
| `council/f_9` (tag: `v1.9.0`) | `f_9 = f_8(f_8)` | Adversarial test authorship (two-model pipeline: gemini-flash implementor, devstral tester; test/case blobs, test suite gate) |
| `council/f_10` (tag: `v1.10.0`) | `f_10 = f_9(f_9)` | Guided mutation goals from audit log trends + multi-candidate N=3 + dropped deterministic fallback |
| `council/f_11` (tag: `v1.11.0`) | `f_11 = f_10(f_10)` | Goal/OKR blob type + capability bootstrap + GOKR execution engine; run_all() discovers labels dynamically |
| `council/f_12` (tag: `v1.12.0`) | `f_12 = f_11(f_11)` | blake3 as canonical vault and manifest hash function; multihash address format foundation (ADR-015) |
| `council/f_13` (tag: `v1.13.0`) | `f_13 = f_12(f_12)` | Engine-as-expression: seed.py collapses to kernel; all execution policy (bytecode cache, telemetry, ABI) moves into a promotable engine expression stored in the vault |

See [docs/experiments.md](docs/experiments.md) for the full lineage histories and tag notes.

### The Collapse Ritual

When a branch reaches stable fitness:

1. All layer blobs (`l1`–`l4`) are finalized and stored in the vault.
2. `manifest.json` is updated with their hashes.
3. `python seed.py promote manifest.json` validates integrity and writes `manifest.hash`.
4. The branch is tagged (e.g., `v1.2.0` or `f_2`) to mark the stable collapse.
5. The next branch (`f_3`) diverges from this point.

---

## 🤖 Typical Workflows

### Build an Agent

```python
# 1. Write the agent blob (must assign result)
agent_code = '''
import requests  # injected via context or __builtins__
result = {"action": "search", "query": context["query"]}
'''

# 2. Store it
hash = seed.put(agent_code)

# 3. Invoke it
outcome = seed.invoke(hash, {"query": "current weather in London"})
```

### Chain Blobs

Blobs can invoke other blobs by embedding the hash in the context and calling `seed.invoke` (if the seed module is injected):

```python
# In a blob: chain to another blob
sub_result = seed.invoke(context["sub_hash"], {"data": context["input"]})
result = {"combined": sub_result["result"], "source": context["sub_hash"]}
```

### Promote a New System Manifest

```bash
# After updating l1_interface.py, l2_discovery.py, etc.:
python seed.py put l1_interface.py   # → <l1_hash>
python seed.py put l2_discovery.py   # → <l2_hash>
# ... update manifest.json with new hashes ...
python seed.py promote manifest.json
```

---

## ⚠️ Safety & Threat Model

**Synapse executes arbitrary, dynamically-loaded code blobs at runtime.** This is intentional by design — and it means the following risks are real:

| Risk | Description |
| :--- | :--- |
| **Arbitrary code execution** | Any blob stored in `blob_vault/` will be `exec()`'d directly. A malicious or malformed blob can do anything the process user can do. |
| **Credential exposure** | Blobs execute inside the same Python process. Any secrets in environment variables or mounted files are accessible. |
| **Network egress** | Blobs can open sockets, call external APIs, or exfiltrate data unless network is restricted. |
| **Privilege escalation** | If run as root or with elevated permissions, a blob can escape to the host OS. |
| **Supply-chain blobs** | Remote vault tiers could serve untrusted blobs if not properly authenticated. |

### Hardening Checklist

- **Do not run with `--yolo` or blindly invoke untrusted hashes.** Always verify blob provenance.
- **Run inside Docker** (or a locked-down VM). Example minimal invocation:

  ```bash
  docker run --rm -it \
    --network none \
    --read-only \
    --tmpfs /tmp \
    --cap-drop ALL \
    -v "$(pwd)/blob_vault:/app/blob_vault:ro" \
    python:3.12-slim python seed.py invoke <hash>
  ```

- **Use least privilege.** Run as a non-root user (`--user 1000:1000`).
- **Restrict network egress** using Docker `--network none` or firewall rules (`iptables`, `nftables`).
- **Mount blob_vault read-only** when not actively writing new blobs.
- **Never pass secrets** (API keys, tokens, passwords) in the `context` dict unless the blob is fully audited.
- **Enable audit logging.** Telemetry blobs are written to `blob_vault/telemetry/` — review them.
- **Validate blob hashes** before executing: the SHA-256 hash *is* the content address. A mismatch means tampering.
- **Isolate filesystem.** Use a `tmpfs` or ephemeral container so blobs cannot persist state between runs unless explicitly designed to.

> **TL;DR:** Treat every blob like a shell script you downloaded from the internet. Would you run it as root? No. Neither should Synapse.

---

<!-- AUTO-GENERATED:START -->
<!-- This section is automatically updated by scripts/update_readme.py on every push. Do not edit manually. -->

## 📊 Evolution Snapshots

**Last updated:** 2026-04-03 02:24 UTC

### Branches
- `copilot/update-documentation-experiment-lineages`
- `council/f_0`
- `council/f_1`
- `council/f_10`
- `council/f_11`
- `council/f_12`
- `council/f_13`
- `council/f_14`
- `council/f_2`
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

## 🤝 Contributing

1. Fork the repository and create a branch named `council/f_<n>_<feature>`.
2. Follow the **ABI Contract**: every blob must assign to `result` and use the `log()` sink.
3. Run `python seed.py promote manifest.json` before committing a new layer configuration.
4. Do not commit `blob_vault/` contents to version control (add to `.gitignore`).
5. Open a PR against the appropriate `f_<n>` branch (not `main`).

---

## 📄 License

No explicit license file has been found in this repository.  
All rights are assumed to be reserved by the author(s) until a license is added.  
**Do not use, distribute, or modify this code in production without explicit permission.**

---

"Logic exists in the Intermezzo — the space between movement."
