# Vantage Experiment 001: ADR-008 Feedback Blobs

**Date:** 2026-04-06
**Artifact:** ADR-008 (Feedback Blobs as Governance)
**Method:** Back-of-envelope probe
**Provenance:** `[UNTRAINED]` — LLM pattern-matching only, no expert validation
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

### Physicist (Control Theory) `[UNTRAINED]`
**Components seen:** Error signal, damping, stability, equilibrium

Feedback score is a negative feedback term. Default 1.0 = equilibrium. Bayesian smoothing = damping to prevent oscillation.

### Biologist (Evolutionary) `[UNTRAINED]`
**Components seen:** Selection pressure, phenotype, gene expression, drift

Feedback blob = phenotypic expression of logic blob genotype. Governance gate = epigenetic regulation. `feedback_score < 1.0` = negative selection. Default 1.0 = neutral drift.

### Economist (Market Signals) `[UNTRAINED]`
**Components seen:** Price signal, incentive, market equilibrium, regulation

Feedback blob = price signal for quality. Fitness = market cap. Governance gate = regulatory oversight. Bayesian smoothing = sticky prices.

### Epidemiologist (Signal Propagation) `[UNTRAINED]`
**Components seen:** Signal, threshold, propagation, case fatality

Feedback blob = case report. Telemetry reader = surveillance system. `MIN_FEEDBACK (3)` = epidemic detection threshold.

### Jurist (Due Process) `[UNTRAINED]`
**Components seen:** Evidence, process, precedent, burden of proof

Feedback blob = evidence (not verdict). Governance gate = adjudication. Default 1.0 = presumption of innocence.

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Feedback is evidence vs signal | Jurist | Economist | Bridged by governance gate |
| 2 | Regulation: filter vs amplifier | Epidemiologist | Economist | Open |
| 3 | Neutral default: stability vs drift | Physicist | Biologist | Context-dependent |
| 4 | Bayesian smoothing: damping vs latency | Physicist | Economist | Tradeoff unstated |

---

## Transformation Rules (Hypotheses) `[UNTRAINED]`

These are guesses — need empirical testing:

```
economist.signal ← physicist.equilibrium_adjust
biologist.selection_pressure ← economist.incentive_gradient × governance.filter_efficacy
jurist.burden_of_proof ← biologist.feedback_count ≥ MIN_FEEDBACK
epidemiologist.threshold ← jurist.precedent_weight × telemetry.sensitivity
```

---

## Invariant Candidates `[UNTRAINED]`

What appears constant across all vantages (untested):

1. **Causality:** Feedback must be recorded before it can influence fitness
2. **Governance gate required:** Feedback is inert without Triple-Pass + Council (f_4 insight)
3. **Safety property:** Default 1.0 enables exploration without penalty

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
