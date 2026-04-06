# Metaphor Systems: A Unified Map

> All models are wrong. Some are useful.
> — George Box

**See also:** [docs/VANTAGES.md](VANTAGES.md) for a formal framework for vantages — disciplinary traditions that offer different ways of seeing.

This document maps the metaphor systems that inform Synapse. Each illuminates different aspects. Together they form a coherent picture.

---

## The Core Analogy: Genetic Encoding

The foundational metaphor. All other systems connect to this.

| Genetic | Synapse | Function |
|---------|---------|----------|
| DNA | Blob | Heritable pattern |
| RNA | Projection | Transcription to runtime |
| Protein | Execution | Functional output |
| Ribosome | Runtime | Machinery for projection |
| Gene | Blob (capability) | Unit of function |
| Genome | Vault | All patterns |
| Cell | Scope | Containment + capability |

**The process:**
```
DNA → (transcription) → RNA → (translation) → Protein → (folding) → Function
Blob → (projection) → Runtime → (execution) → Result → (telemetry) → Fitness
```

See [design/SYNTHESIS.md](design/SYNTHESIS.md) for full model.

---

## Metaphor Systems

### 1. Neurobiology: The Synapse

**Source:** The founding metaphor. Synapse is named for this.

**What it illuminates:**
- The gap between potential and action
- Plasticity (fitness modulation)
- Signal transmission across boundaries
- Vesicles (envelopes protecting payloads)

**Key terms:**
- Synaptic cleft: the space between address and execution
- Vesicles: JSON envelopes
- Plasticity: evaluation function modulates strength
- Neurotransmitter: the blob content

**See:** [genesis/METAPHORS.md](genesis/METAPHORS.md)

---

### 2. Mycology: The Mycelium

**Source:** The founding metaphor.

**What it illuminates:**
- Persistent substrate vs. visible fruiting bodies
- Underground growth and spreading
- Nutrient transport across distance
- The invisible infrastructure

**Key terms:**
- Substrate: the vault (persistent)
- Hyphae: linker logic searching for hashes
- Fruiting body: the result (visible output)

**The connection to genetics:**
- Mycelium spreads through spores (horizontal gene transfer)
- Growth is distributed, not centralized

**See:** [genesis/METAPHORS.md](genesis/METAPHORS.md)

---

### 3. Philosophy: The Rhizome

**Source:** Deleuze & Guattari's A Thousand Plateaus.

**What it illuminates:**
- Non-hierarchical structure
- Any point connects to any other
- No center, no root
- Lines of flight (escape from structure)

**Key terms:**
- Rhizome: the reference graph
- Entry points: any hash
- Lines of flight: mutation proposals

**The connection to genetics:**
- Rhizome = horizontal gene transfer
- Spreading without hierarchy

**See:** [genesis/METAPHORS.md](genesis/METAPHORS.md)

---

### 4. Physics: The Wavefunction

**Source:** Quantum mechanics.

**What it illuminates:**
- Superposition (all blobs exist simultaneously)
- Collapse (invocation = measurement)
- Entanglement (correlated execution)
- Conservation laws (invariants)

**Key terms:**
- Superposition: all possible blobs exist until observed
- Collapse: invoke() collapses to a result
- Observation: the act of execution

**The connection to genetics:**
- Quantum superposition → all possible patterns exist in vault
- Collapse → selection of one pattern

**See:** [genesis/METAPHORS.md](genesis/METAPHORS.md)

---

### 5. Biology: Living Systems

**Source:** Autopoiesis, ecosystem theory, immune systems.

**What it illuminates:**
- Self-production (fabric produces fabric)
- Evolution (selection on patterns)
- Immune response (adversarial testing)
- Commons governance (shared resources)
- Keystone species (critical dependencies)

**Key concepts:**
- Autopoiesis: system produces itself
- Germline vs. soma: governance vs. execution
- Immune response: security/verification
- Ecosystem: vault as commons

**The connection to genetics:**
- Direct mapping: DNA → RNA → Protein
- Evolution: patterns that work survive
- Selection: fitness function

**See:** [explore/LIVING-SYSTEMS.md](explore/LIVING-SYSTEMS.md)

---

### 6. Object-Oriented Systems: MOO

**Source:** LambdaMOO and similar systems.

**What it illuminates:**
- Living world that players build together
- Everything is an object
- Objects have properties and verbs
- Message passing between objects
- Persistent world state

**Key concepts:**
- Object: blob
- Property: data blob
- Verb: application blob
- Room: scope
- Player: node
- Object ID: stable ID

**The connection to genetics:**
- MOO objects = genes (units of function)
- Player-created content = mutation

**See:** [explore/MOO.md](explore/MOO.md)

---

### 7. Runtime Systems: Smalltalk

**Source:** Squeak, Pharo, Self.

**What it illuminates:**
- Image-based persistence
- Live coding (modify running system)
- Everything is an object
- Metacircular (compiler in itself)
- The bootstrap problem

**Key concepts:**
- Image: vault
- Object: blob
- Method: blob invocation
- Workspace: telemetry
- Bootstrap: genesis blob

**The connection to genetics:**
- Image = genome (persists entire state)
- Live coding = real-time mutation

**See:** [explore/SMALLTALK.md](explore/SMALLTALK.md)

---

### 8. Actor Systems: Erlang/BEAM

**Source:** Erlang/OTP, Akka.

**What it illuminates:**
- Lightweight processes (ephemeral scopes)
- Message passing (invoke)
- Supervision trees (governance hierarchy)
- Hot code loading (blob promotion)
- "Let it crash" (failure recovery)

**Key concepts:**
- Process: invocation scope
- Mailbox: capability set
- Behavior: blob code
- Supervision: governance
- Hot loading: promotion

**The connection to genetics:**
- Process = ephemeral soma
- Supervision tree = epigenetic regulation

**See:** [explore/BEAM.md](explore/BEAM.md)

---

### 9. Economics: Markets and Commons

**Source:** Market mechanisms, Ostrom's commons.

**What it illuminates:**
- Execution routing as market arbitrage
- Governance as mechanism design
- Vault as commons
- Incentive alignment
- Tragedy of commons (degradation)

**Key concepts:**
- Market signal: fitness function
- Resource allocation: scope references
- Commons: the vault
- Governance: mechanism design

**The connection to genetics:**
- Market = evolutionary selection
- Commons = genome as shared resource

**See:** [explore/PHYSICS-ECONOMICS.md](explore/PHYSICS-ECONOMICS.md)

---

### 10. Ethics: Values and Governance

**Source:** Moral philosophy, care ethics, capabilities approach.

**What it illuminates:**
- The fitness function encodes values
- Who decides what survives
- What is owed to deprecated patterns
- Minimum ethical floor
- Accountability at scale

**Key concepts:**
- Fitness function = ethical judgment
- Governance = mechanism for values
- Deprecation = what happens to the "defeated"

**The connection to genetics:**
- Ethics = what gets selected
- Governance = epigenetic regulation

**See:** [explore/ETHICS.md](explore/ETHICS.md)

---

### 11. Formal Models: Graphs as Universal Form

**Source:** Type theory, category theory, process calculi, physics, neuroscience.

**What it illuminates:**
- Every formal system has a natural graph interpretation
- Graphs with typed edges unify across domains
- The graph is the universal substrate

**Key formal methods and their graph interpretations:**

| Formal Method | Nodes | Edges | Synapse |
|--------------|-------|-------|---------|
| Type Theory | Types | Subtyping relations | Blob types, scope types |
| Category Theory | Objects | Morphisms | Composition, functors |
| Process Calculi | Processes | Communications | Actor model, invoke |
| Petri Nets | Places | Transitions | State machines |
| Modal Logic | Worlds | Accessibility | Governance, time |
| Coalgebra | States | Observations | Scope behaviors |
| Manifolds | Charts | Transitions | Protocol → runtime |
| Engrams | Synapses | Patterns | Memory, persistence |

**Key insight:** Every formal method has a graph interpretation. The graph is the universal form. Synapse makes the graph explicit and content-addressed.

**Research base:** [universal-graph-formal-model](https://github.com/BrianLN-AI/universal-graph-formal-model)

**See:** [research/universal-graph-formal-model](https://github.com/BrianLN-AI/universal-graph-formal-model)

---

## The Unifying Framework

All metaphor systems map to a common structure:

```
POTENTIAL → SELECTION → EXPRESSION → PERSISTENCE
```

| Metaphor | Potential | Selection | Expression | Persistence |
|----------|-----------|-----------|------------|-------------|
| Genetics | DNA | Selection | RNA→Protein | Genome |
| Synapse | Blob | Governance | Runtime | Vault |
| Physics | Superposition | Observation | Collapse | Conservation |
| Economics | Market | Auction | Trade | Commons |
| MOO | Object | Verb | Message | World |
| Ecology | Species | Selection | Adaptation | Gene pool |

---

## Cross-References

| From | To | Connection |
|------|-----|------------|
| Synapse | Genetics | Signal transmission |
| Mycelium | Ecology | Growth, spreading |
| Rhizome | Horizontal gene transfer | No hierarchy |
| Wavefunction | Quantum | Potential → actual |
| Living systems | Genetics | Direct mapping |
| MOO | Genetics | Units of function |
| Smalltalk | Genetics | Image = genome |
| Erlang | Genetics | Ephemeral soma |
| Economics | Genetics | Selection mechanism |
| Ethics | Genetics | What gets selected |

---

## What Each Metaphor Is Good For

| Metaphor | Best Use |
|----------|----------|
| Genetics | Explaining the core model |
| Synapse | Understanding the gap |
| Mycelium | Understanding persistence |
| Rhizome | Understanding non-hierarchy |
| Wavefunction | Understanding invocation |
| Living systems | Understanding evolution |
| MOO | Understanding objects/messages |
| Smalltalk | Understanding persistence |
| Erlang | Understanding actors/isolation |
| Economics | Understanding governance |
| Ethics | Understanding values |

---

## Summary

Synapse is a **genetic encoding system for intelligence**:

- **Patterns** are **heritable** (content-addressed blobs)
- **Selection** is **fitness-based** (governance)
- **Expression** is **projected into runtimes** (projection)
- **Persistence** is **the vault** (genome)

The metaphor systems illuminate different aspects:
- Biology: how patterns work
- Physics: how patterns become real
- Computing: how patterns execute
- Economics: how patterns are valued
- Ethics: what patterns should survive
- Formal models: why graphs are the universal substrate

Together they form a coherent model of **intelligence that compounds**.

The graph is the universal form. Synapse makes graphs explicit, content-addressed, and governed.

---

## See Also

- [docs/VISION.md](VISION.md) — The thesis
- [docs/design/SYNTHESIS.md](design/SYNTHESIS.md) — Technical model
- [docs/VANTAGES.md](VANTAGES.md) — Formal vantage framework
- [docs/METAPHORS-VS-VANTAGES.md](METAPHORS-VS-VANTAGES.md) — Mapping and gaps
- [docs/INVARIANTS.md](../INVARIANTS.md) — Constitutional invariants
- [docs/KNOWLEDGE.md](KNOWLEDGE.md) — Current state map

---

*The address of λ.md is the address of everything.*
