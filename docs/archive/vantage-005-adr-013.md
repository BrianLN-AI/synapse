# Vantage Experiment 005: ADR-013 Governance as Expression

**Date:** 2026-04-06
**Artifact:** ADR-013 (Governance as a Typed Expression)
**Method:** Back-of-envelope probe
**Status:** Draft — hypotheses only

---

## Provenance Tags

| Tag | Meaning |
|-----|---------|
| `[UNTRAINED]` | LLM projection, no domain expertise |
| `[TRAINED]` | Grounded in training data / literature |
| `[EXPERT-VALIDATED]` | Verified by domain expert |
| `[DISAGREES]` | Expert contradicts projection |

---

## The Artifact

**ADR-013: Governance as a Typed Expression**
- Renames "council" → "governance" (mechanism, not social structure)
- Governance types: single-key, quorum, threshold, proof
- Governance is a content-addressed blob in the vault
- Evolution path: single-key → quorum → threshold → proof
- Changing governance = promoting new governance expression
- Bootstrap case: genesis governance is self-grounding
- Hybrid layering: per-label override + tenant default

---

## Vantage Probes

### Logician (Type Theory) → `LOG-001` `[UNTRAINED]`

**Components seen:** Typed terms, type checking, subtyping, Church encoding

Governance types = type system. Each governance type = a type constructor. Expression = term. Manifest = typing context. Evolution path = type refinement. Bootstrap = ground type.

**Rationalization:** → See §Rationalization

---

### Linguist (Grammar) → `LIN-001` `[UNTRAINED]`

**Components seen:** Grammar, syntax, semantics, productive language

Governance types = syntactic categories. Expression = well-formed string. Type checking = grammaticality. Evolution path = grammar expansion. Bootstrap = protolanguage (one expression type).

**Rationalization:** → See §Rationalization

---

### Architect (Structure) → `ARC-001` `[UNTRAINED]`

**Components seen:** Foundation, load-bearing, structural integrity, facade

Single-key = foundation. Quorum = load-bearing wall. Threshold = automated system. Proof = pure structural integrity (no humans needed). Changing governance = structural renovation without collapse.

**Rationalization:** → See §Rationalization

---

### Protocol Designer (Layering) → `PRO-001` `[UNTRAINED]`

**Components seen:** Protocol stack, abstraction layer, interface, implementation

Governance types = layers in a protocol stack. Expression = message format. Evolution path = protocol versioning. Bootstrap = bootstrap protocol (handshake). Per-label override = protocol negotiation.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Governance change: version vs mutation | Logician | Architect | Logician: new term; Architect: structural change |
| 2 | Single-key bootstrap: feature vs weakness | Protocol | Architect | Protocol: necessary; Architect: single point of failure |
| 3 | Evolution path is teleological | Linguist | Logician | Linguist: grammar grows; Logician: types are discovered |
| 4 | Proof governance: verified vs trusted | Logician | Protocol | Logician: proof is syntactic; Protocol: proof is protocol |

---

## Transformation Rules (Hypotheses) → `TR-005` `[UNTRAINED]`

```
logician.type_system = arc.foundation × pro.protocol_stack
lin.grammar = logician.type_checking × arc.structural_integrity
pro.protocol_version = logician.type_refinement × lin.grammar_expansion
arc.load_bearing = pro.layer × logician.subtype
```

---

## Invariant Candidates → `INV-005` `[UNTRAINED]`

1. **Governance must be expressible as an expression** — can't govern what you can't encode
2. **Every governance change is itself governed** — recursive bootstrapping handled by bootstrap case
3. **The evolution path removes humans** — single-key → quorum → threshold → proof

---

## Rationalization

### LOG-001: Logician probe of governance as expression

**Projection:** Governance types as type constructors, expression as term, manifest as typing context.

**Why:**
- Typed systems have type constructors (Product, Sum, Function)
- Governance types are named variants = sum type
- Manifest binding governance hash = typing context
- Evolution path = type refinement (more expressive, same foundation)

**Weaknesses:**
- "Type refinement" is my injection — not in the ADR
- Types are usually discovered, not evolved — the analogy may break down
- The ADR says governance is "typed" but doesn't use type theory language

---

### LIN-001: Linguist probe of governance as expression

**Projection:** Governance types as syntactic categories, expression as well-formed string.

**Why:**
- Grammar defines well-formed expressions
- Governance types define valid governance structures
- "Council" → "governance" rename = syntax change (same semantics)
- Evolution path = productive language (can generate new forms)

**Weaknesses:**
- "Grammar" suggests generative rules — governance is more constrained
- Linguistic grammars are descriptive, not prescriptive — governance expressions are prescriptive
- The mapping is loose

---

### ARC-001: Architect probe of governance as expression

**Projection:** Governance types as structural elements, change as renovation.

**Why:**
- Single-key = foundation (everything built on it)
- Quorum = load-bearing wall (distributes weight)
- Threshold = automated system (doesn't need human operator)
- Proof = pure structure (no human in the loop at all)

**Weaknesses:**
- "Foundation" suggests immutability — governance changes, but foundations are supposed to stay
- The metaphor works but doesn't add precision

---

### PRO-001: Protocol Designer probe of governance as expression

**Projection:** Governance types as protocol layers, expression as message format.

**Why:**
- Protocols have bootstrap handshake
- Evolution path = protocol versioning
- Per-label override = protocol negotiation
- Proof governance = protocol with cryptographic verification

**Weaknesses:**
- Protocol layering usually means different abstraction levels — governance types are different mechanisms, not different layers
- "Negotiation" suggests parties agree — per-label override is unilateral

---

## Notes

- ADR-013 is about abstraction — renaming council to governance
- The "evolution path" (single-key → quorum → threshold → proof) is the most interesting structure
- The bootstrap case is the key invariant: every governed system has an ungoverned root
- Conflicts are shallow — vantages mostly agree on the structure
