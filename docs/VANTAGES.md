# VANTAGES: A Formal Framework for Perspective Systems

> Beyond metaphor — a taxonomy of lenses for understanding complex systems

---

## Definitions

### Vantage

**A vantage is a disciplinary tradition, practice, or framework that offers a distinct way of understanding a system.**

A vantage provides:
- **Ontology** — what exists in this view
- **Epistemology** — how we know what we claim
- **Methodology** — how we investigate
- **Key questions** — what to ask
- **Invariants** — what must be preserved

Vantages are not metaphors. A metaphor says "X is like Y." A vantage says "from X you see Z."

### Metaphor

**A metaphor is a named system that works, through which we understand something else.**

Metaphors are named after systems (MOO, BEAM, Biology) that work. We study them to understand Synapse.

See [docs/METAPHORS.md](METAPHORS.md) for the metaphor map.

### The Relationship

```
System (works) → Metaphor (naming) → Vantage (discipline)
```

Studying a working system (MOO) gives you a metaphor. The metaphor points to a vantage (Actor Theorist). The vantage gives you a framework for reasoning.

---

## Premise

Different disciplines, traditions, and practices offer different ways of seeing the world. Each provides:
- An ontology (what exists)
- An epistemology (how we know)
- A methodology (how we investigate)
- Key questions to ask
- Invariants to preserve

---

## The Pattern

Every vantage has:

```json
{
  "name": "physicist",
  "ontology": {
    "what_exists": ["particles", "fields", "spacetime"],
    "what_matters": ["conservation laws", "symmetry"]
  },
  "epistemology": {
    "how_we_know": "measurement",
    "evidence": "reproducible experiment",
    "validation": "independent replication"
  },
  "methodology": {
    "investigation": ["observe", "measure", "model", "test"],
    "tools": ["mathematics", "experiment", "simulation"]
  },
  "key_questions": [
    "What is conserved?",
    "What symmetry underlies this?",
    "What happens at the limit?"
  ],
  "key_invariants": ["conservation", "unitarity", "causality"],
  "signature": {
    "form": "conservation_law = symmetry",
    "example": "E = mc²"
  }
}
```

---

## Taxonomy of Vantages

### Structural Vantages

**The Algebraist**
- **Ontology:** Sets, operations, relations
- **Methodology:** Transform, preserve structure
- **Questions:** What is invariant under transformation?
- **Signature:** `f(x) = y` preserves structure

**The Mathematician**
- **Ontology:** Abstract objects, proofs
- **Methodology:** Derive, prove, generalize
- **Questions:** Can this be simplified? Proved?
- **Signature:** Elegance, proof

**The Categorist**
- **Ontology:** Objects, morphisms, functors
- **Methodology:** Universal properties, composition
- **Questions:** What is the universal construction?
- **Signature:** `A → B → C` = `A → C`

---

### Empirical Vantages

**The Physicist**
- **Ontology:** Particles, fields, spacetime
- **Methodology:** Measure, experiment
- **Questions:** What is conserved? What symmetry?
- **Invariants:** Energy, momentum, charge
- **Signature:** Conservation laws = Noether's theorem

**The Biologist**
- **Ontology:** Organisms, populations, ecosystems
- **Methodology:** Observe, compare, experiment
- **Questions:** What survives? What reproduces?
- **Invariants:** Genetic information
- **Signature:** Fitness = survival × reproduction

**The Statistician**
- **Ontology:** Distributions, samples, populations
- **Methodology:** Sample, estimate, test
- **Questions:** What varies? How? Why?
- **Invariants:** Asymptotic behavior
- **Signature:** P(data | hypothesis)

**The Climatologist**
- **Ontology:** Systems, feedback, equilibria
- **Methodology:** Model, simulate, project
- **Questions:** What stabilizes? What amplifies?
- **Invariants:** Conservation of mass/energy
- **Signature:** Feedback loops, tipping points

---

### Information Vantages

**The Information Theorist**
- **Ontology:** Signals, entropy, channels, codes
- **Methodology:** Encode, transmit, decode, compress
- **Questions:** How much information? What is redundant? What can be recovered?
- **Invariants:** Information cannot be created or destroyed (only transformed)
- **Signature:** H(X) = -Σ p(x) log p(x)
- **Synapse:** Blob entropy, compression, channel capacity

**The Data Scientist**
- **Ontology:** Datasets, features, models, predictions
- **Methodology:** Collect, transform, model, validate
- **Questions:** What predicts what? How confident? What is the bias?
- **Invariants:** No free lunch, bias-variance tradeoff
- **Signature:** Training error, generalization gap
- **Synapse:** Telemetry as data, fitness as prediction

**The Statistician**
- **Ontology:** Populations, samples, parameters, distributions
- **Methodology:** Sample, estimate, test, infer
- **Questions:** What varies? How? Is it significant?
- **Invariants:** Law of large numbers, Central Limit Theorem
- **Signature:** P(data | hypothesis)
- **Synapse:** Fitness estimation, confidence intervals

**The Bayesian**
- **Ontology:** Priors, likelihoods, posteriors, beliefs
- **Methodology:** Update beliefs given evidence
- **Questions:** What do we believe now? How should we update?
- **Invariants:** Bayes' theorem, coherence
- **Signature:** P(θ | D) ∝ P(D | θ) × P(θ)
- **Synapse:** Fitness as Bayesian update

---

### Complexity Vantages

**The Complexity Theorist**
- **Ontology:** Problems, reductions, complexity classes
- **Methodology:** Classify, reduce, prove bounds
- **Questions:** What is the complexity? P = NP?
- **Invariants:** Complexity classes (P, NP, PSPACE)
- **Signature:** Polynomial vs. exponential
- **Synapse:** Blob complexity, governance cost

**The Emergentist**
- **Ontology:** Levels, emergence, downward causation
- **Methodology:** Identify levels, trace emergence, find mechanisms
- **Questions:** What emerges? How? What causes what?
- **Invariants:** Conservation across levels
- **Signature:** Macro from micro, feedback loops
- **Synapse:** Blobs emerge from primitives, governance emerges from rules

**The Fractalist**
- **Ontology:** Self-similarity, scale invariance, fractals
- **Methodology:** Measure dimension, find recursion, identify patterns
- **Questions:** Is it self-similar? At what scales?
- **Invariants:** Fractal dimension
- **Signature:** D = lim log(N) / log(1/ε)
- **Synapse:** Scope nesting, blob composition

**The Network Scientist**
- **Ontology:** Nodes, edges, networks, topologies
- **Methodology:** Measure centrality, find communities, trace diffusion
- **Questions:** Who is connected to whom? What flows? How resilient?
- **Invariants:** Degree distribution, clustering coefficient
- **Signature:** Small world, scale-free
- **Synapse:** Reference graph, blob dependencies

---

### Biological Vantages

**The Epidemiologist**
- **Ontology:** Hosts, pathogens, transmissions, immunity
- **Methodology:** Track, model, predict, intervene
- **Questions:** What spreads? How fast? What stops it?
- **Invariants:** R₀ (basic reproduction number)
- **Signature:** SIR model, herd immunity
- **Synapse:** Blob propagation, viral capabilities, quarantine

**The Ecologist**
- **Ontology:** Species, niches, ecosystems, succession
- **Methodology:** Observe, model, manage
- **Questions:** What occupies this niche? What is the carrying capacity?
- **Invariants:** Conservation of matter and energy
- **Signature:** Food webs, trophic levels
- **Synapse:** Blob ecosystems, keystone patterns

**The Geneticist**
- **Ontology:** Genes, alleles, genotypes, phenotypes
- **Methodology:** Sequence, compare, associate, edit
- **Questions:** What is the sequence? What does it do?
- **Invariants:** Central dogma (DNA → RNA → protein)
- **Signature:** Genetic code, inheritance
- **Synapse:** Blob inheritance, composition

---

### Neural/Cognitive Vantages

**The Connectionist**
- **Ontology:** Neurons, weights, activations, layers
- **Methodology:** Train, optimize, infer, fine-tune
- **Questions:** What does the network learn? How?
- **Invariants:** Gradient descent, loss landscape
- **Signature:** Weights → activations → output
- **Synapse:** Neural-inspired routing, embedding spaces

**The Neuroscientist**
- **Ontology:** Neurons, synapses, regions, networks
- **Methodology:** Measure, stimulate, model
- **Questions:** How does the brain implement this?
- **Invariants:** Neural coding principles
- **Signature:** Spike timing, connectivity
- **Synapse:** Synaptic weight = blob fitness

**The Cognitive Psychologist**
- **Ontology:** Representations, processes, capacities
- **Methodology:** Test, measure, compare
- **Questions:** What can be processed? How fast?
- **Invariants:** Working memory limits
- **Signature:** Reaction time, accuracy
- **Synapse:** Cognitive load, attention

---

### Social Vantages

**The Economist**
- **Ontology:** Agents, goods, markets
- **Methodology:** Incentives, equilibrium, game theory
- **Questions:** What are the incentives? What is the equilibrium?
- **Invariants:** Scarcity, opportunity cost
- **Signature:** Supply × demand = price

**The Jurist**
- **Ontology:** Persons, property, obligations
- **Methodology:** Precedent, interpretation, argument
- **Questions:** Who has standing? What is the chain of custody?
- **Invariants:** Due process, burden of proof
- **Signature:** Precedent binds future cases

**The Ethicist**
- **Ontology:** Persons, goods, harms, duties
- **Methodology:** Principle, consequence, virtue
- **Questions:** What should survive? What is owed?
- **Invariants:** Dignity, autonomy
- **Signature:** What ought to be vs. what is

**The Anthropologist**
- **Ontology:** Cultures, practices, meanings
- **Methodology:** Ethnography, interpretation
- **Questions:** What does this mean? How is it practiced?
- **Invariants:** Symbolic systems
- **Signature:** Thick description

---

### Computational Vantages

**The Computer Scientist**
- **Ontology:** Algorithms, data structures, complexity
- **Methodology:** Analyze, optimize, prove
- **Questions:** What is the complexity? Does it terminate?
- **Invariants:** Correctness, termination
- **Signature:** O(n log n)

**The Actor Theorist**
- **Ontology:** Actors, messages, mailboxes, behaviors
- **Methodology:** Send, receive, spawn, supervise
- **Questions:** What sends to what? Who supervises? What fails?
- **Invariants:** Isolation, no shared state
- **Signature:** send(pid, msg), become(behavior)
- **Synapse:** Blob invocation, scope isolation, supervision

**The Event/Stream Processor**
- **Ontology:** Events, streams, windows, aggregations
- **Methodology:** Filter, map, reduce, join
- **Questions:** What happened? When? In what order?
- **Invariants:** Event ordering, exactly-once
- **Signature:** Event time, processing time, watermarks
- **Synapse:** Telemetry as event stream, audit as event log

**The Protocol Designer**
- **Ontology:** Messages, state machines, handshakes
- **Methodology:** Specify, model, verify
- **Questions:** What messages? In what order? What if?
- **Invariants:** Safety (nothing bad) + liveness (something good)
- **Signature:** State machine, sequence diagrams
- **Synapse:** Protocol as blob, invocation as handshake

**The Security Specialist**
- **Ontology:** Threats, attacks, defenses, trust
- **Methodology:** Threat model, attack surface, defense in depth
- **Questions:** What can go wrong? Who do we trust?
- **Invariants:** Principle of least privilege
- **Signature:** CIA triad (confidentiality, integrity, availability)
- **Synapse:** Capability model, scope isolation

**The Engineer**
- **Ontology:** Systems, components, interfaces
- **Methodology:** Design, build, test
- **Questions:** What carries the load? What fails?
- **Invariants:** Margins, tolerances
- **Signature:** MTBF, failure modes

**The Operator**
- **Ontology:** Processes, logs, metrics
- **Methodology:** Monitor, alert, respond
- **Questions:** Is it running? What is the latency?
- **Invariants:** Availability, consistency
- **Signature:** SLOs, error budgets

---

### Cognitive Vantages

**The Cognitive Scientist**
- **Ontology:** Representations, processes, states
- **Methodology:** Behavioral experiment, modeling
- **Questions:** How is it represented? What processes?
- **Invariants:** Working memory limits
- **Signature:** Dual process theory

**The Phenomenologist**
- **Ontology:** Lived experience, qualia
- **Methodology:** First-person description
- **Questions:** What is the experience?
- **Invariants:** Subjective certainty
- **Signature:** Intentionality

**The Systems Thinker**
- **Ontology:** Feedback loops, stocks, flows
- **Methodology:** Diagram, simulate, intervene
- **Questions:** What is the feedback? Where are the delays?
- **Invariants:** Conservation, feedback
- **Signature:** Causal loop diagrams

---

### Design Vantages

**The Architect**
- **Ontology:** Patterns, forces, trade-offs
- **Methodology:** Pattern language, precedent
- **Questions:** What are the forces? What pattern fits?
- **Invariants:** Structural integrity
- **Signature:** Pattern → Context → Solution

**The UX Designer**
- **Ontology:** Users, tasks, contexts
- **Methodology:** Research, prototype, test
- **Questions:** What do users need? What do they actually do?
- **Invariants:** Usability, accessibility
- **Signature:** User mental model = interface model

**The Strategist**
- **Ontology:** Positions, moves, payoffs
- **Methodology:** Scenario planning, game theory
- **Questions:** What is the position? What move is optimal?
- **Invariants:** Competitive advantage
- **Signature:** SWOT, Porter's forces

---

## How Vantages Relate

### Orthogonal Vantages

Different vantages answer different questions. No conflict.

```
Physicist asks: "What is conserved?"
Economist asks: "What is the equilibrium?"
Both can be true simultaneously.
```

### Contradictory Vantages

Same evidence, different conclusions.

```
Optimist: "Half full"
Pessimist: "Half empty"
Both looking at the same glass.
```

### Complementary Vantages

Together explain more than alone.

```
Physicist + Biologist: "What physical constraints shape evolution?"
Economist + Jurist: "What incentives shape law?"
```

### Hierarchical Vantages

One vantage grounds another.

```
Physicist grounds Chemistry grounds Biology grounds Psychology
```

---

## Vantages in Synapse

### Scope Has Vantages

```json
{
  "scope": {
    "id": "project-alpha",
    "vantages": ["builder", "operator", "ethicist"],
    "default": "builder"
  }
}
```

### Governance Uses Vantages

When council disagrees, which vantage wins?

```json
{
  "governance": {
    "expression": "(fitness > threshold)",
    "vantage": "ethicist",
    "fallback": "economist"
  }
}
```

### The Fitness Function Has Vantages

| Vantage | Fitness = |
|---------|-----------|
| Biologist | Survival × reproduction |
| Economist | Efficiency × equity |
| Ethicist | Dignity preserved |
| Engineer | MTBF × performance |
| Operator | SLOs × cost |

### The Genetic Model Uses Multiple Vantages

- **Biologist:** DNA → blob (heritable pattern)
- **Economist:** Selection → governance (mechanism design)
- **Physicist:** Conservation → invariants (Noether)
- **Engineer:** Projection → runtime (build vs. run)
- **Operator:** Feedback → telemetry (observe, adjust)

---

## Formalizing a Vantage

```json
{
  "vantage": {
    "id": "biologist",
    "name": "The Biologist",
    "description": "Asks what survives and reproduces",
    
    "ontology": {
      "what_exists": ["organism", "population", "environment", "gene"],
      "what_matters": ["fitness", "adaptation", "reproduction"]
    },
    
    "epistemology": {
      "how_we_know": ["observation", "experiment", "evolution"],
      "evidence": ["survival rates", "reproductive success", "fitness metrics"],
      "validation": "independent measurement of fitness"
    },
    
    "methodology": {
      "investigation": ["observe", "measure_fitness", "select", "breed"],
      "tools": ["statistics", "genomics", "ecology"]
    },
    
    "questions": {
      "primary": "What survives?",
      "secondary": [
        "What reproduces?",
        "What adapts?",
        "What is the carrying capacity?"
      ]
    },
    
    "invariants": {
      "conserved": ["genetic information"],
      "bounded": ["resources", "population size"]
    },
    
    "signature": {
      "form": "fitness = survival × reproduction",
      "units": "individuals over time",
      "measurement": "selection coefficient"
    },
    
    "synapse_mapping": {
      "organism": "blob",
      "population": "vault",
      "environment": "scope",
      "gene": "capability",
      "fitness": "f(link)"
    }
  }
}
```

---

## Composing Vantages

### Vantage Composition

```json
{
  "composition": {
    "type": "complementary",
    "vantages": ["physicist", "economist"],
    "joint_question": "What physical constraints shape market behavior?",
    "integration": "Statistical mechanics of markets"
  }
}
```

### Vantage Hierarchy

```json
{
  "hierarchy": {
    "grounds": "physicist",
    "grounded": "economist",
    "reason": "Markets are physical systems constrained by thermodynamics"
  }
}
```

### Vantage Conflict Resolution

```json
{
  "conflict": {
    "vantage_a": "ethicist",
    "vantage_b": "economist",
    "question": "Should this pattern survive?",
    "resolution": "governance decides based on expressed values"
  }
}
```

---

## Open Questions

1. **Can vantages be fully formalized?** Or is some intuition irreducible?
2. **How do we resolve vantage conflicts?** Is there a meta-vantage?
3. **Can vantages be learned?** Can an AI acquire a vantage?
4. **What is the minimum set of vantages?** Is there a basis?
5. **How do vantages evolve?** Can new vantages emerge?
6. **What is the relationship between vantages and languages?** Does language constrain vantages?

---

## See Also

- [docs/METAPHORS.md](METAPHORS.md) — The unified metaphor map
- [docs/METAPHORS-VS-VANTAGES.md](METAPHORS-VS-VANTAGES.md) — Mapping and gaps between metaphors and vantages
- [docs/VISION.md](VISION.md) — The thesis
- [docs/design/SYNTHESIS.md](design/SYNTHESIS.md) — Technical synthesis
- [docs/INVARIANTS.md](../INVARIANTS.md) — Constitutional invariants
- [universal-graph-formal-model](https://github.com/BrianLN-AI/universal-graph-formal-model) — Formal methods research

---

## Appendix: Vantage Survey

| Vantage | Ontology | Key Question | Signature |
|---------|----------|---------------|-----------|
| Algebraist | Sets, ops | What is preserved? | f(x) |
| Mathematician | Abstract | Can it be proved? | Elegance |
| Categorist | Objects, morphisms | Universal construction? | A → C |
| Physicist | Particles, fields | What is conserved? | E = mc² |
| Biologist | Organisms, genes | What survives? | fitness |
| Statistician | Distributions | What varies? | P(X) |
| Economist | Agents, goods | Equilibrium? | S × D = P |
| Jurist | Persons, duties | Chain of custody? | precedent |
| Ethicist | Persons, harms | What should be? | ought |
| Engineer | Systems, loads | What fails? | MTBF |
| Operator | Processes, logs | Is it running? | SLOs |
| Cognitive Scientist | Representations | How represented? | dual process |
| Architect | Patterns, forces | What pattern fits? | pattern language |
| Systems Thinker | Feedback, stocks | What is the loop? | causal diagram |

---

*The address of λ.md is the address of everything.*
