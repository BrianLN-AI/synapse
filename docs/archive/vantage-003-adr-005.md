# Vantage Experiment 003: ADR-005 Self-Modification Protocol

**Date:** 2026-04-06
**Artifact:** ADR-005 (f(N)(f(N)) Self-Modification Protocol)
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

**ADR-005: Self-Modification Protocol**
- Five-step cycle: Evaluate → Mutate → Review → Benchmark → Promote
- Fixed set of core blobs (discovery, planning, telemetry-reader)
- PROMOTE_TOLERANCE = 0.30 (allows capability improvements with speed tradeoffs)
- Fixed-point iteration: `f_n = f_{n-1}(f_{n-1})`
- Termination: when no further improvements pass the gate
- Warmup (5 invocations) added to account for compilation overhead

---

## Vantage Probes

### Biologist (Evolutionary) → `BIO-002` `[UNTRAINED]`

**Components seen:** Fitness landscape, selection pressure, canalization, punctuated equilibrium

Five-step cycle = selective breeding program. Core blobs = conserved genes. PROMOTE_TOLERANCE = canalization (allows deviation from optimum for capability). Fixed-point = local optimum. Warmup = phenotypic plasticity before selection.

**Rationalization:** → See §Rationalization

---

### Complexity Theorist (Fitness Landscape) → `CMP-002` `[UNTRAINED]`

**Components seen:** Fitness landscape, local optima, ruggedness, search algorithm

Five-step cycle = hill climbing with mutation. PROMOTE_TOLERANCE = allows crossing fitness valleys. Fixed-point = local optimum (terminates search). Core blobs = basin of attraction. Benchmark = fitness measurement.

**Rationalization:** → See §Rationalization

---

### Neuroscientist (Metacognition) → `NEU-002` `[UNTRAINED]`

**Components seen:** Self-model, recursion depth, executive function, homeostasis

Self-modification = metacognition (thinking about thinking). Five-step cycle = executive function. Fixed-point = stable self-model. PROMOTE_TOLERANCE = allows self-model drift. Warmup = recalibration before evaluation.

**Rationalization:** → See §Rationalization

---

### Category Theorist (Fixed Point) → `CAT-003` `[UNTRAINED]`

**Components seen:** Fixed point, self-application, endomorphism, Y-combinator

`f_n = f_{n-1}(f_{n-1})` = Y-combinator structure. Self-modification = endomorphism. Fixed-point = least fixed point of the evaluation functional. Promotion = convergence to attractor.

**Rationalization:** → See §Rationalization

---

### Engineer (Control System) → `ENG-002` `[UNTRAINED]`

**Components seen:** Control loop, stability, tolerance band, settling time

Five-step cycle = control loop. PROMOTE_TOLERANCE = deadband (prevents oscillation). Warmup = plant settling time. Fixed-point = steady state. Benchmark = feedback measurement.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Fixed-point: optimum vs pathology | Complexity | Neuroscientist | Both see it differently — optimum vs stuck |
| 2 | PROMOTE_TOLERANCE: feature vs kludge | Biologist | Engineer | Biologist sees canalization; Engineer sees deadband |
| 3 | Self-modification: adaptation vs instability | Complexity | Neuroscientist | Adaptation vs homeostatic threat |
| 4 | Warmup: plasticity vs cost | Biologist | Engineer | Plasticity enables search; cost delays evaluation |

---

## Transformation Rules (Hypotheses) → `TR-003` `[UNTRAINED]`

```
biologist.local_optimum = complexity.fixed_point
neuroscientist.stable_self_model = complexity.attractor_basin
engineer.settling_time = biologist.phenotypic_plasticity × complexity.ruggedness
cat.least_fixed_point = complexity.global_optimum_search
```

---

## Invariant Candidates → `INV-003` `[UNTRAINED]`

1. **Termination requires a gate** — without PROMOTE_TOLERANCE, self-modification doesn't converge
2. **Hardcoded mutations are the constraint** — human commits limit search space
3. **Self-modification must measure itself** — benchmark must account for its own overhead (warmup)

---

## Rationalization

### BIO-002: Biologist probe of self-modification

**Projection:** Core blobs as conserved genes, PROMOTE_TOLERANCE as canalization, fixed-point as local optimum.

**Why:**
- Evolution uses fixed-point iteration (population → fitness → selection → population)
- Canalization = buffered development that allows genetic assimilation of new traits
- Conserved genes = core functions that don't change

**Weaknesses:**
- Biological evolution doesn't have a "promotion gate"
- Fixed-point in biology is extinction, not convergence

---

### CMP-002: Complexity Theorist probe of self-modification

**Projection:** Five-step as hill climbing, PROMOTE_TOLERANCE as crossing valleys.

**Why:**
- Fitness landscape is standard complexity/optimization framing
- Local optima = where hill climbing terminates
- Tolerance allows "valley crossing" (accept temporary decrease for better long-term)

**Weaknesses:**
- Fitness landscapes are metaphors, not formal
- The system doesn't explore a landscape — it has fixed mutation candidates

---

### NEU-002: Neuroscientist probe of self-modification

**Projection:** Self-modification as metacognition, fixed-point as stable self-model.

**Why:**
- Metacognition = cognition about cognition
- Stable self-model is necessary for coherent agency
- Executive function runs the five-step cycle

**Weaknesses:**
- Neurological self-modification is slower and messier
- "Stable self-model" could mean pathological rigidity

---

### CAT-003: Category Theorist probe of self-modification

**Projection:** `f_n = f_{n-1}(f_{n-1})` as Y-combinator, fixed-point as least fixed point.

**Why:**
- Y-combinator implements recursion via self-application
- `Y F = F (Y F)` — the classic fixed-point equation
- The ADR literally uses this notation

**Weaknesses:**
- Category theory is about structure, not computation
- The analogy is almost too perfect — the ADR is written in CS terms

---

### ENG-002: Engineer probe of self-modification

**Projection:** Five-step as control loop, PROMOTE_TOLERANCE as deadband.

**Why:**
- Control theory is about stable self-regulation
- Deadband prevents oscillation (too-fast switching)
- Settling time = how long until system stabilizes

**Weaknesses:**
- Control systems are typically continuous, this is discrete
- "Deadband" is more about actuator hysteresis than promotion criteria

---

## Notes

- ADR-005 has recursion/self-reference as core theme — many vantages converge on "fixed point"
- PROMOTE_TOLERANCE is a key tension point across vantages
- Compare to ADR-008: this is about the *engine*, ADR-008 is about *quality signal*

---

## Cross-Reference

- Compare to Experiment 001 (ADR-008): self-modification engine vs quality signal
- Compare to Experiment 002 (ADR-010): dynamic behavior vs static structure
- Invariant #2: hardcoded mutations — this is a fundamental limitation noted in ADR-005
