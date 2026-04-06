# Vantage Experiment 001: ADR-008 Feedback Blobs

**Date:** 2026-04-06
**Artifact:** ADR-008 (Feedback Blobs as Governance)
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

**ADR-008: Feedback Blobs as Governance**
- Adds `feedback/outcome` blob type to vault
- Adds `feedback_score` to fitness formula: `f = (sr × integrity × feedback_score) / (latency × burstiness × cost)`
- Governance gate: feedback only affects fitness after Triple-Pass + Council Approval
- Default `feedback_score = 1.0` (neutral)
- Bayesian smoothing when `feedback_count < MIN_FEEDBACK (3)`

---

## Vantage Probes

### Physicist (Control Theory) → `PHY-001` `[UNTRAINED]`

**Components seen:** Error signal, damping, stability, equilibrium

Feedback score is a negative feedback term. Default 1.0 = equilibrium. Bayesian smoothing = damping to prevent oscillation.

**Rationalization:** → See §Rationalization

---

### Biologist (Evolutionary) → `BIO-001` `[UNTRAINED]`

**Components seen:** Selection pressure, phenotype, gene expression, drift

Feedback blob = phenotypic expression of logic blob genotype. Governance gate = epigenetic regulation. `feedback_score < 1.0` = negative selection. Default 1.0 = neutral drift.

**Rationalization:** → See §Rationalization

---

### Economist (Market Signals) → `ECO-001` `[UNTRAINED]`

**Components seen:** Price signal, incentive, market equilibrium, regulation

Feedback blob = price signal for quality. Fitness = market cap. Governance gate = regulatory oversight. Bayesian smoothing = sticky prices.

**Rationalization:** → See §Rationalization

---

### Epidemiologist (Signal Propagation) → `EPI-001` `[UNTRAINED]`

**Components seen:** Signal, threshold, propagation, case fatality

Feedback blob = case report. Telemetry reader = surveillance system. `MIN_FEEDBACK (3)` = epidemic detection threshold.

**Rationalization:** → See §Rationalization

---

### Jurist (Due Process) → `JUR-001` `[UNTRAINED]`

**Components seen:** Evidence, process, precedent, burden of proof

Feedback blob = evidence (not verdict). Governance gate = adjudication. Default 1.0 = presumption of innocence.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Feedback is evidence vs signal | Jurist | Economist | Bridged by governance gate |
| 2 | Regulation: filter vs amplifier | Epidemiologist | Economist | Open |
| 3 | Neutral default: stability vs drift | Physicist | Biologist | Context-dependent |
| 4 | Bayesian smoothing: damping vs latency | Physicist | Economist | Tradeoff unstated |

---

## Transformation Rules (Hypotheses) → `TR-001` `[UNTRAINED]`

These are guesses — need empirical testing:

```
economist.signal ← physicist.equilibrium_adjust
biologist.selection_pressure ← economist.incentive_gradient × governance.filter_efficacy
jurist.burden_of_proof ← biologist.feedback_count ≥ MIN_FEEDBACK
epidemiologist.threshold ← jurist.precedent_weight × telemetry.sensitivity
```

**Rationalization:** → See §Rationalization

---

## Invariant Candidates → `INV-001` `[UNTRAINED]`

What appears constant across all vantages (untested):

1. **Causality:** Feedback must be recorded before it can influence fitness
2. **Governance gate required:** Feedback is inert without Triple-Pass + Council (f_4 insight)
3. **Safety property:** Default 1.0 enables exploration without penalty

**Rationalization:** → See §Rationalization

---

## Rationalization

### PHY-001: Physicist probe of feedback fitness

**Projection:** Feedback score as negative feedback term, default 1.0 as equilibrium, Bayesian smoothing as damping.

**Why:**
- Fitness formula is ratio-based → reminiscent of control systems (error/signal)
- Default 1.0 doesn't perturb numerator → equilibrium state
- Bayesian smoothing blends toward default → damping behavior

**Weaknesses:**
- I'm conflating "1.0 = neutral" with "equilibrium" — these aren't the same
- "Damping" is my intuition, not a formal mapping

---

### BIO-001: Biologist probe of feedback fitness

**Projection:** Logic blob as genotype, feedback blob as phenotype, governance as epigenetics.

**Why:**
- DNA → blob (heritable pattern) is an established Synapse metaphor
- Feedback reflects downstream consequences → phenotype emerges from genotype
- Governance gate modulates expression → epigenetic regulation

**Weaknesses:**
- Genotype/phenotype analogy is loose
- "Epigenetic regulation" is a specific mechanism — does governance work that way?

---

### ECO-001: Economist probe of feedback fitness

**Projection:** Feedback as price signal, fitness as market cap, governance as regulation.

**Why:**
- Quality → price is standard economic mapping
- Aggregate signal → market cap (fitness = weighted sum)
- Governance gate prevents manipulation → regulatory oversight

**Weaknesses:**
- This is textbook economics — I may be applying stereotypes
- "Sticky prices" analogy for Bayesian smoothing — is this actually how economists think?

---

### EPI-001: Epidemiologist probe of feedback fitness

**Projection:** Feedback blob as case report, MIN_FEEDBACK as epidemic threshold.

**Why:**
- `MIN_FEEDBACK (3)` is a detection threshold
- Epidemiological surveillance uses thresholds to detect outbreaks
- The language of "spread" and "threshold" maps naturally

**Weaknesses:**
- I don't actually know how epidemiologists reason about thresholds
- The mapping is surface-level (both use the word "threshold")

---

### JUR-001: Jurist probe of feedback fitness

**Projection:** Feedback as evidence, governance as adjudication, default 1.0 as presumption of innocence.

**Why:**
- Feedback is observed outcome, not verdict → evidence
- Council approval is a process → adjudication
- Default neutral → innocent until proven guilty

**Weaknesses:**
- "Presumption of innocence" applies to persons, not artifacts
- This may be anthropomorphizing the system

---

### TR-001: Transformation rules

**Projection:** Vantages map to each other via these functions.

**Why:**
- If vantages are bases in a tensor, there must be transformation rules
- The rules are my guesses at what maps to what

**Weaknesses:**
- These are completely made up
- No reason to believe these specific functions

---

### INV-001: Invariant candidates

**Projection:** These properties are constant across vantages.

**Why:**
- Causality is logical necessity
- Governance gate appears in multiple vantages → convergent design
- Default 1.0 is explicitly documented as enabling exploration

**Weaknesses:**
- "Safety property" is my framing, not from the ADR
- Invariants should be verified, not assumed

---

## Next Steps

- [ ] Test transformation rules against other ADRs
- [ ] Find ADR with stronger vantage conflicts
- [ ] Consult domain experts (economist, epidemiologist) to validate projections
- [ ] Build simple tool to record vantage probes

---

## Notes

- Vantage pairs that map well: Physicist ↔ Economist (equilibrium)
- Governance gate is a convergence point across all vantages
- The tensor analogy holds: the "thing" (feedback loop) is invariant, components vary by vantage
