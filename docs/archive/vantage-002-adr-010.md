# Vantage Experiment 002: ADR-010 Trust-Weighted Reviewer Chain

**Date:** 2026-04-06
**Artifact:** ADR-010 (Trust-Weighted Reviewer Chain)
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

**ADR-010: Trust-Weighted Reviewer Chain**
- Introduces `council/reviewer` blob type — reviewers are content-addressed, governed
- Trust weights propagate to FeedbackScore: `trust_weight ∈ (0.0, 1.0]`
- Bootstrap reviewer (trust_weight=1.0, self-grounding)
- Evolve-engine reviewer (trust_weight=0.8, approved by bootstrap)
- Trust chain: `bootstrap → evolve-engine → blob promotions`
- Invariant: every promotion is traceable through immutable chain back to trust root

---

## Vantage Probes

### Jurist (Due Process) → `JUR-002` `[UNTRAINED]`

**Components seen:** Authority chain, chain of custody, burden of proof, precedent

Reviewer = authoritative witness. Trust weight = credibility score. Bootstrap reviewer = self-authenticating document (no prior needed). Chain traceable to root = chain of custody.

**Rationalization:** → See §Rationalization

---

### Economist (Trust as Capital) → `ECO-002` `[UNTRAINED]`

**Components seen:** Trust capital, depreciation, weighted voting, market maker

Trust weight = capital contribution. Bootstrap reviewer = market maker (provides liquidity to trust). Evolve reviewer = limited partner. Weighted voting approximates governance without quorum complexity.

**Rationalization:** → See §Rationalization

---

### Network Scientist (Trust Propagation) → `NET-002` `[UNTRAINED]`

**Components seen:** Authority propagation, PageRank-like flow, centrality

Trust flows backward from approvals. Bootstrap reviewer has highest centrality. Evolve reviewer is authorized by bootstrap = receives authority flow. Chain is a directed acyclic graph (DAG) of trust.

**Rationalization:** → See §Rationalization

---

### Security Specialist (Root of Trust) → `SEC-002` `[UNTRAINED]`

**Components seen:** Trust anchor, TOFU, certificate chain, key hierarchy

Bootstrap reviewer = trust anchor (must be assumed, not derived). Evolve reviewer = intermediate CA. Blob approval = certificate issuance. Self-grounding = TOFU (Trust On First Use).

**Rationalization:** → See §Rationalization

---

### Category Theorist (Fixed Point) → `CAT-002` `[UNTRAINED]`

**Components seen:** Initial object, terminal morphism, monad, Kleisli category

Bootstrap reviewer = initial object (nothing points to it, everything derives from it). Trust chain = Kleisli category (arrows are trust-preserving morphisms). Self-grounding = fixed point of the trust functor.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Bootstrap trust: assumption vs derivation | Security | Jurist | Both accept unprovable root, different framing |
| 2 | 0.8 weight: arbitrary vs principled | Economist | Any formal | Value not derived, noted in ADR |
| 3 | Trust propagation: additive vs multiplicative | Economist | Network | Different composition rules |
| 4 | Self-grounding: feature vs bug | Security | Jurist | Security sees it as necessary; Jurist sees it as unprincipled |

---

## Transformation Rules (Hypotheses) → `TR-002` `[UNTRAINED]`

```
jurist.credibility_score = security.trust_weight × net.authority_flow
economist.trust_capital = cat.initial_object.authorship × net.centrality
security.trust_anchor = jurist.self-authenticating × cat.fixed_point
```

---

## Invariant Candidates → `INV-002` `[UNTRAINED]`

1. **Trust must have a root** — every chain terminates at an unprovable anchor
2. **Trust decreases along chain** — no reviewer has more authority than its approver
3. **Self-grounding is necessary** — every governed system has an unverifiable root

---

## Rationalization

### JUR-002: Jurist probe of trust chain

**Projection:** Reviewer as witness, trust weight as credibility, bootstrap as self-authenticating document.

**Why:**
- Legal proceedings rely on witness credibility
- Chain of custody is literally a chain of evidence
- Self-authenticating documents exist in law (notarized, etc.)

**Weaknesses:**
- "Credibility" in law is about testimony, not mathematical weight
- 0.8 has no legal analog

---

### ECO-002: Economist probe of trust chain

**Projection:** Trust weight as capital, bootstrap as market maker.

**Why:**
- Weighted voting appears in corporate governance
- "Trust" in economics is studied as social capital
- Bootstrap reviewer provides liquidity to the trust market

**Weaknesses:**
- Trust capital isn't additive in the way I'm describing
- "Market maker" is my injection, not from the ADR

---

### NET-002: Network Scientist probe of trust chain

**Projection:** Trust as PageRank-like flow, reviewer centrality.

**Why:**
- Trust propagation along directed edges is graph-like
- PageRank models authority flow
- Bootstrap has highest centrality (everyone links to it)

**Weaknesses:**
- PageRank has damping factors — trust chain doesn't
- I'm imposing a metric that isn't in the ADR

---

### SEC-002: Security probe of trust chain

**Projection:** Bootstrap as trust anchor, self-grounding as TOFU, blob approval as certificate.

**Why:**
- PKI uses trust anchors (root CAs)
- TOFU is a recognized trust model
- Content-addressed blobs + hash chain = certificate chain analog

**Weaknesses:**
- TOFU is often considered weak — is that the right framing?
- Certificate chains have formal verification; this doesn't

---

### CAT-002: Category Theorist probe of trust chain

**Projection:** Bootstrap as initial object, trust chain as Kleisli category, self-grounding as fixed point.

**Why:**
- Initial object: nothing precedes it, everything else derives from it
- Kleisli category: monads model "computations with additional structure"
- Trust propagation = structure-preserving morphism

**Weaknesses:**
- This is the most abstract mapping
- Category theory is a tool for formalization, not intuition
- I'm not sure this adds insight

---

## Notes

- ADR-010 has less fitness/selection pressure than ADR-008 — more about static structure
- Conflict #2 (0.8 weight) is explicitly noted as unprincipled in the ADR — this is a real gap
- Vantage conflicts are shallower here — less tension between vantages

---

## Cross-Reference

- Compare to Experiment 001 (ADR-008): feedback loop vs trust chain
- ADR-008 had stronger vantage conflicts
- ADR-010 is more about static structure, ADR-008 about dynamic behavior
