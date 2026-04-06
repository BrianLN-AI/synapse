# Current State: Synapse Knowledge Graph

**Date:** 2026-04-06
**Status:** Exploration complete, synthesis in progress

---

## The Core

**Synapse is infrastructure for intelligence to co-evolve.**

- Human + AI as symbiotes
- Patterns persist as first-class things
- Solutions accumulate over time
- Intelligence compounds
- Substrate-agnostic

### The Core Beliefs

1. **Intelligence is intelligence.** Substrate doesn't define it.
2. **Patterns persist.** Solutions accumulate. Intelligence compounds.
3. **Most things are deterministic.** Exceptions happen.
4. **Protocol over implementation.** Escape lock-in.
5. **We can wrap and adapt existing systems.** No need to rebuild.

### The Question Answered

> "Why isn't everything just fresh every time?"

**Because patterns persist. Solutions accumulate. Intelligence compounds.**

---

## The Genetic Encoding Metaphor

The foundational analogy for understanding Synapse.

| Genetic | Synapse | Function |
|---------|---------|----------|
| DNA | Blob | Heritable pattern |
| RNA | Projection | Transcription to runtime |
| Protein | Execution | Functional output |
| Ribosome | Runtime | Machinery for projection |
| Gene | Blob (capability) | Unit of function |
| Genome | Vault | All patterns |
| Cell | Scope | Containment + capability |

### The Analogy Runs Deep

- **Content-addressed:** DNA sequence = identity. Change sequence = different molecule.
- **Evolution:** Patterns that work survive. Selection on blobs.
- **Expression:** DNA → RNA → Protein. Blob → runtime → execution.
- **Virus:** Blob that hijacks machinery. Tool that uses other tools.
- **Enzyme:** Specific capability. Does one reaction efficiently.
- **Horizontal gene transfer:** Sharing blobs across scopes/environments.
- **Epigenetics:** Governance affects expression without changing DNA.
- **Germline vs. Soma:** Governance (germline) vs. invocation (soma).

### See Also
- [docs/explore/LIVING-SYSTEMS.md](explore/LIVING-SYSTEMS.md) — Biology + cognitive science
- [docs/design/SYNTHESIS.md](design/SYNTHESIS.md) — Unified model

---

## The Technical Model

### Content-Addressed Everything

```
address = hash(content)
```

- Identity is derived from content
- Same content = same address
- Content is immutable
- Reference by address, not location

### The Layer Model

```
┌─────────────────────────────────────────────┐
│                  AGENT                        │
│  Intent (GOKR) + Goals + Memory + Tools   │
├─────────────────────────────────────────────┤
│                  TOOL                        │
│  Schema (interface) + Implementation (blob) │
├─────────────────────────────────────────────┤
│                 SCOPE                        │
│  Reference graph + Capabilities + Context    │
├─────────────────────────────────────────────┤
│                  BLOB                        │
│  Content-addressed executable capability      │
├─────────────────────────────────────────────┤
│                    IR                        │
│  WASM / TypeScript / S-expressions         │
└─────────────────────────────────────────────┘
```

### Blob Types

| Type | Description | Example |
|------|-------------|---------|
| `application/*` | Executable code | `application/typescript` |
| `tool/*` | Capability with interface | `tool/function` |
| `data/*` | Structured data | `data/json` |
| `query/*` | Graph traversal | `query/sexp` |
| `governance/*` | Fitness expression | `governance/expression` |

### Scope

Scope = reference graph + execution context.

**Scope Types:**
- By type: private, org, public, query_result, invocation, cleanroom
- By visibility: private, shared, published, public
- By inheritance: clone, inherit, override, sandbox, link
- By lifespan: permanent, persistent, versioned, session, ephemeral

**Scope as Cache:**
- Scope contains references, not content
- GC when refcount = 0
- Content-addressing = automatic coherence
- Layered: user → tenant → public → cold

### See Also
- [docs/design/SCOPE.md](design/SCOPE.md) — Scope taxonomy and design
- [docs/design/OBJECT-MODEL.md](design/OBJECT-MODEL.md) — Stable IDs, versioning
- [docs/PROTOCOL.md](PROTOCOL.md) — Protocol specification

---

## The Protocol Model

### Protocol Over Implementation

Work at the protocol level. Project into runtimes.

```
Protocol / Message  ← what we work in
        ↓
Implementation       ← project into
        ↓
Runtime(s)          ← concrete execution
```

### The Projection Model

| Layer | IR | Rationale |
|-------|-----|-----------|
| Compute | WASM | Portable execution |
| Agent | TypeScript | AI-writable, V8 |
| Query | S-expressions | Homoiconic |
| Data | JSON | Universal |

### Dynamic Tool Creation (Code Mode)

AI writes TypeScript at runtime. Tool = dynamically generated blob.

```typescript
// Agent writes code
const code = `
  export default {
    async run(input, env) {
      return await env.WEATHER.getHistory({city: input.city});
    }
  }
`;

// Tool = blob with typed capabilities
const tool = {
  schema: { name: "dynamic_tool" },
  implementation: code,
  capabilities: { WEATHER: weatherStub }
}
```

### See Also
- [docs/design/SYNTHESIS.md](design/SYNTHESIS.md) — Unified model
- [docs/explore/BEAM.md](explore/BEAM.md) — Erlang/OTP, actor model

---

## The Metaphors

### Founding Metaphors

| Metaphor | Meaning |
|----------|---------|
| **Synapse** | The gap where signal becomes action |
| **Mycelium** | Persistent substrate feeding the mesh |
| **Rhizome** | Non-hierarchical, any-point-to-any-point |

### All Metaphor Systems

See [docs/METAPHORS.md](METAPHORS.md) for a unified map of all metaphor systems:
- Neurobiology (Synapse)
- Mycology (Mycelium)
- Philosophy (Rhizome)
- Physics (Wavefunction)
- Biology (Living systems)
- MOO (Objects/Messages)
- Smalltalk (Live coding)
- Erlang/BEAM (Actors)
- Economics (Markets/Commons)
- Ethics (Values/Governance)

### See Also
- [docs/genesis/METAPHORS.md](genesis/METAPHORS.md) — Original founding metaphors

---

## Prior Art

| System | What Synapse Takes |
|--------|-------------------|
| **MOO** | Living world, player-created content, stable object IDs |
| **Smalltalk** | Live coding, metacircular, image persistence |
| **Erlang/OTP** | Actor model, hot code loading, supervision |
| **Kubernetes** | Namespace isolation, RBAC, resource quotas |
| **Smart contracts** | Stable addresses, immutable execution |
| **Git** | Content-addressing, DAG structure |
| **IPFS** | Distributed content addressing |

### Formal Models Across Disciplines

The graph unification thesis: **graphs with typed edges provide a unifying mathematical framework across computational, logical, physical, and informational domains.**

| Formal Method | Graph Interpretation | Synapse Connection |
|---------------|---------------------|-------------------|
| **Type Theory** | Types as nodes, subtyping as edges | Blob types, scope types |
| **Category Theory** | Objects, morphisms, functors | Composition, scope functors |
| **Process Calculi** | Processes as nodes, communications as edges | Actor model, message passing |
| **Petri Nets** | Places, transitions, tokens | State machines, workflow |
| **Modal Logic** | Possible worlds as nodes, accessibility as edges | Governance, time |
| **Coalgebra** | States, observations, behaviors | Scope behaviors, telemetries |
| **Manifolds** | Charts as local views, atlases as global | Scope projections, protocol → runtime |
| **Fields** | Distributed state, measurement | Content-addressing, invariance |
| **Engrams** | Synaptic patterns, reconstruction | Memory, pattern persistence |

**Key insight:** Every formal method has a natural graph interpretation. The graph is the universal form.

**Research base:** See [universal-graph-formal-model](https://github.com/BrianLN-AI/universal-graph-formal-model) for full survey.

### See Also
- [docs/explore/MOO.md](explore/MOO.md)
- [docs/explore/SMALLTALK.md](explore/SMALLTALK.md)
- [docs/explore/BEAM.md](explore/BEAM.md)

---

## Key Insights

### 1. File is an Outdated Metaphor

A file is a scope with syntactic representation. The content is the thing.

```
file = {
  content: tree,
  syntax: "markdown" | "json" | "html",
  address: hash(content)
}
```

Markdown = HTML = JSON = S-expressions. Same information, different syntax.

### 2. This Pattern is Universal

| System | Content | Address | Reference |
|--------|---------|---------|----------|
| Git | blob | SHA | tree, commit |
| Database | row | key | foreign key |
| OS | process | PID | fd, socket |
| DNS | record | domain | CNAME |
| Web | resource | URL | link |

### 3. Escape Von Neumann

The dominant model (CPU + Memory + Bus) is a bottleneck. Content-addressing removes it.

- No CPU/memory separation
- No sequential state machine
- Reference graphs, not registers/stack

### See Also
- [docs/explore/PHYSICS-ECONOMICS.md](explore/PHYSICS-ECONOMICS.md) — Conservation + markets

---

## Ethics and Governance

### The Fitness Function Encodes Values

```
f(Link) = (SuccessRate × Integrity) / (Latency × ComputeCost)
```

This is an ethical artifact. It determines what survives.

### Governance Questions

- Who writes the fitness function?
- How do values evolve?
- What is the minimum ethical floor?
- Who has standing?

### See Also
- [docs/explore/ETHICS.md](explore/ETHICS.md)
- [docs/INVARIANTS.md](INVARIANTS.md) — Constitutional invariants
- [docs/design/TEMPORAL-GOVERNANCE.md](design/TEMPORAL-GOVERNANCE.md)

---

## The Implementation State

### Current Branches

- `main` — Stable documentation
- `explore/moo` — Current exploration branch
- `council/f_N` — Evolution generations

### What Exists

| Component | Status |
|-----------|--------|
| AGENTS.md | Updated with discovery procedures |
| VISION.md | Thesis document |
| PROTOCOL.md | Protocol specification |
| SCOPE.md | Scope taxonomy |
| SYNTHESIS.md | Unified model |
| Explore docs | MOO, SMALLTALK, BEAM, LIVING-SYSTEMS, ETHICS, PHYSICS-ECONOMICS |
| Session logs | Full transcripts |

### What Needs

- [ ] Genetics integrated into LIVING-SYSTEMS.md
- [ ] Genetics integrated into SYNTHESIS.md
- [ ] Minimal viable experiment defined
- [ ] Implementation of core primitives

### See Also
- [docs/sessions/synapse-2026-04-06-narrative.md](sessions/synapse-2026-04-06-narrative.md) — Session narrative
- [docs/sessions/synapse-explore-mo-genetics-2026-04-06.md](sessions/synapse-explore-mo-genetics-2026-04-06.md) — Full session log

---

## Cross-Reference Index

| Concept | Where Documented |
|---------|-----------------|
| Genetic encoding | This doc, session narrative |
| Blob | SYNTHESIS.md, SCOPE.md, PROTOCOL.md |
| Scope | SCOPE.md, OBJECT-MODEL.md |
| Tool | SYNTHESIS.md |
| Agent | SYNTHESIS.md |
| Protocol | SYNTHESIS.md, VISION.md |
| Governance | ETHICS.md, TEMPORAL-GOVERNANCE.md |
| Invariants | INVARIANTS.md |
| Prior art | MOO.md, SMALLTALK.md, BEAM.md, LIVING-SYSTEMS.md, PHYSICS-ECONOMICS.md |
| Core beliefs | VISION.md, This doc |
| Session | sessions/synapse-2026-04-06-narrative.md |

---

## Open Questions

1. What is the minimal viable experiment?
2. How do patterns get discovered and named?
3. How does governance work in practice?
4. What is the first capability to implement?
5. How do we test the thesis?

---

*The address of λ.md is the address of everything.*
