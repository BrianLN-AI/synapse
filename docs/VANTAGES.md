# VANTAGES: A Formal Framework for Perspective Systems

> Beyond metaphor — a taxonomy of lenses for understanding complex systems

---

## Premise

Different disciplines, traditions, and practices offer different ways of seeing the world. Each provides:
- An ontology (what exists)
- An epistemology (how we know)
- A methodology (how we investigate)
- Key questions to ask
- Invariants to preserve

We need a better word than "metaphor." Metaphor suggests comparison. These are vantage points — ways of looking at the same thing from different traditions.

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
- [docs/VISION.md](VISION.md) — The thesis
- [docs/design/SYNTHESIS.md](design/SYNTHESIS.md) — Technical synthesis
- [docs/INVARIANTS.md](INVARIANTS.md) — Constitutional invariants
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
