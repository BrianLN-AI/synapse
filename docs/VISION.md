# VISION.md

> *Code is a commons. Knowledge should persist. Intelligence should be composable.*

---

## The Problem

Every software system faces the same three crises:

**1. The knowledge crisis.** What you knew when you wrote code is lost when you stop maintaining it. Teams forget why decisions were made. Critical context lives in people's heads, not in the system. The code survives; the reasoning dies.

**2. The trust crisis.** You run code you didn't write. You trust authors you don't know. You update dependencies you can't audit. The supply chain is opaque, and the attack surface is invisible.

**3. The evolution crisis.** Systems are hard to change. Every modification risks breaking something. The system that runs cannot be the system you are improving. You need shadows, flags, migrations — two systems to maintain.

---

## The Thesis

**Synapse is a persistent, governed, self-improving computational ecosystem.**

It treats code as a commons — immutable, addressable, evolvable through collective intelligence. Not a registry. Not a market. Not an AI agent. A *fabric* — woven by many, governed by expression, persistent across time.

The core insight is this:

> **When code is content-addressed, code becomes data. When code becomes data, code becomes a subject for itself.**

You can reason about code the same way you reason about facts. You can trace its provenance. You can measure its fitness. You can evolve it through governed selection. You can persist its history. You can compose it without copying it.

This is not a new idea. It's a synthesis of ideas that have existed separately for decades.

---

## What Synapse Is Synthesizing

### From MOO: The Living World

MOO (Multiple User Dungeon, Object-Oriented) created persistent virtual worlds where players built the world together. Everything was an object. Players created objects, verbs, properties. The world grew organically. State survived disconnection.

**What Synapse takes:** The vault is the world. Blobs are objects. Players are agents. The world persists and grows through contribution.

### From Smalltalk: The Living Image

Smalltalk created systems where code could be modified while running. The "image" was the world — a single file containing the entire running state. The compiler was written in the language itself. The bootstrap was the language.

**What Synapse takes:** The engine is a blob. The fabric is self-referential. The bootstrap is the genesis.

### From Erlang: The Distributed Fabric

Erlang created systems that could be updated without downtime. Supervision trees meant failures were recovered, not prevented. Hot code loading meant the system could improve itself in production.

**What Synapse takes:** Promotion without downtime. Governance as supervision. Distribution across nodes.

### From Biology: The Evolving Commons

Biology shows how complex systems can evolve without central planning. Selection pressure improves fitness. The germline persists; the soma executes. Ecosystems are commons — shared, growing, governed by dynamics rather than authority.

**What Synapse takes:** The vault is a commons. Fitness is selection pressure. The f(Link) function is the fitness function. Governance is the selection mechanism.

### From Physics: The Conservation Laws

Physics teaches that the deepest properties of a system are its conserved quantities. Phase transitions mark qualitative changes. Quantum mechanics shows that measurement creates state.

**What Synapse takes:** The invariants are conservation laws. Promotion is a phase transition. Governance collapses the superposition of candidates into one actualized state.

### From Economics: The Market for Logic

Economics shows how markets coordinate distributed actors without central planning. Mechanism design produces desired outcomes from selfish participants. Commons (Ostrom) shows how shared resources can be governed sustainably.

**What Synapse takes:** Execution routing is market arbitrage. Governance is mechanism design. The vault is a commons with governed access.

### From Ethics: The Encoding of Values

Ethics asks: who decides? What is preserved? What is owed? The fitness function is an encoding of values — it determines what survives. When ZK proofs remove humans from the loop, whose values are encoded in the circuit?

**What Synapse must face:** The fitness function is a moral artifact. Governance is the ethics checkpoint. Accountability persists even when humans don't.

### From Cognitive Science: The Extended Mind

Cognitive science shows that mind extends beyond skull. Tools are cognitive artifacts. Memory is externalized. Intelligence is distributed across agents and systems.

**What Synapse takes:** The mesh is cognitive infrastructure. Telemetry is introspection. The vault is long-term memory. The fitness function is Bayesian belief update.

---

## The Three Properties

### 1. Persistence

Code persists not just across sessions but across *interpretations*. The vault is append-only — every version of every idea is preserved. You can trace the history of a capability from genesis to current form. Context is not lost.

### 2. Governability

Code cannot be added to the fabric without passing through governance. The governance expression is a program that decides what can evolve. This is mechanism design — the rules determine the outcomes without requiring a central authority to enforce them.

### 3. Composability

Code is referenced by content address, not by location. You can compose capabilities without copying them. You can invoke logic you have never seen, because you have its address. Composition is declaration, not copying.

---

## What Synapse Is Not

**Synapse is not a package manager.** Package managers distribute copies. Synapse references originals. Updates are new addresses, not mutations.

**Synapse is not an AI agent.** Agents act. Synapse executes. Agents use Synapse; Synapse doesn't use agents.

**Synapse is not a blockchain.** Synapse is not about consensus. Governance can be centralized (single key) or decentralized (quorum, proof). Synapse doesn't require a chain.

**Synapse is not a database.** Databases store state. Synapse stores capability. The distinction matters: state mutates; capability persists.

**Synapse is not a programming language.** Synapse runs on top of languages. Blobs can be Python, JavaScript, WASM, anything. The fabric doesn't care about syntax; it cares about addresses and fitness.

---

### Scope and Multi-Tenancy

The vault is not a global flat store. It is the union of scoped reference graphs. Each scope (user, tenant, project, session) holds references to the blobs it uses. Storage grows with scope activity, not unbounded.

Scopes are cache regions. References are cached items. Garbage collection is eviction. Content-addressing provides automatic coherence — the same hash is the same content everywhere, with no invalidation protocol needed.

See [docs/design/SCOPE.md](docs/design/SCOPE.md) for full design.

---

## The Core Abstraction

The core abstraction is simple:

```
blob = { address: hash(content), content: bytes }
vault = { get(hash) → blob, put(blob) → hash }
fabric = vault + linker + governance + evolution
```

Everything else derives from this.

**Content address** gives you identity and persistence. **Vault** gives you storage and retrieval. **Linker** gives you execution. **Governance** gives you selection. **Evolution** gives you improvement over time.

The fitness function `f(Link)` is what connects governance to evolution. It's simultaneously:

- A biological selection pressure
- A Bayesian belief update
- An economic market signal
- A phase transition criterion
- An ethical judgment

This is not metaphorical. The same mathematical form appears in all these domains because they are all solving the same problem: *how to choose among alternatives when you can't evaluate them exhaustively.*

---

## The GOKR

The Goal/Objective/Key Result (GOKR) protocol is how Synapse steers itself:

1. The GOKR is a blob — an expression of intent
2. Agents propose blobs that serve the GOKR
3. Governance evaluates proposals against fitness criteria
4. Council converges on synthesis — multiple independent agents agreeing on direction
5. The synthesis is promoted — the fabric has moved

This is not automation replacing judgment. It's judgment made explicit, persistent, and composable.

---

## The Metaphor

The fabric is a **synapse**: the gap between neurons where signal becomes action.

The potential exists in the vault. The action occurs at invocation. Between them: the governance gate, where possibility collapses into execution.

The fabric is a **mycelium**: a persistent substrate feeding the mesh.

The nodes are fruiting bodies — temporary expressions of the underlying network. The substrate persists; the bodies come and go.

The fabric is a **rhizome**: non-hierarchical, any-point-to-any-point, no center.

You can enter anywhere. You can trace any path. There is no root object; every address is equally valid as an entry point.

---

## The Question Synapse Asks

> *What if we could build systems that remembered what they knew?*

Not just stored data. Remembered reasoning. Persisted context. Evolved intelligently. Composed without copying.

Code is knowledge. Synapse asks: what would it mean for knowledge to behave like code — immutable, addressable, composable, governable, evolvable?

This is the question. The rest is engineering.

---

## Status

**Current:** Implementation exists in experiment branches (f_0 through f_20). Governance protocol defined. Core primitives working.

**Next:** The gap between "working prototype" and "persistent computational ecosystem" is governance, interoperability, and the ability for new agents to orient and contribute with minimal friction.

---

*The address of λ.md is the address of everything.*
