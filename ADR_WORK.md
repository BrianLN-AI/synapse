# ADR_WORK.md — bare f_N Walking Instructions

**Branch:** bare f_N lineage (f_0, f_1, f_2, f_3 local branches)
**Purpose:** Walk each phase/tag, extract capabilities and lessons not carried into council/f_N.
**Output:** `docs/adr/` in this worktree. Cherry-pick candidates flagged for main.

---

## Instructions for Extracting Agent

For each phase/tag below, in order:

1. Read the files introduced or changed at that phase (git diff previous tag)
2. Read the README or docs committed at that point for intent
3. Identify: what capability was built? what design decision was made?
4. Write a stub to `docs/adr/<ID>-<slug>.md` using the format below
5. Flag: `[CHERRY-PICK CANDIDATE]`, `[BRANCH-ONLY]`, or `[LESSON]`
6. Advance to next phase

---

## ADR/CAP/LESSON Format

```markdown
# <ID>: <Title>
**Date:** <from git commit>
**Status:** Proposed
**Flag:** [CHERRY-PICK CANDIDATE | BRANCH-ONLY | LESSON — do not adopt]
**Branch:** bare/f_N

## Context
What was being built? What problem was being solved?

## What Was Built / Decided
Concrete description.

## What It Enables
What does this capability make possible?

## Why Not In council/f_N
Was it abandoned? Superseded? Too complex? Not yet needed?

## Evidence Basis
Tag all claims: [MEASURED] [INFERRED] [CITED] [HYPOTHESIS]
```

---

## Phase Points to Walk

### PHASE: genesis — Phase 1 (commit: 739a228)
`Phase 1: Seed Implementation (BIOS & ABI)`

Extract: **CAP-BARE-001** — Original BIOS/ABI design. Compare to council/f_N version. What was different in the genesis intent vs. what the council tree implemented?

---

### PHASE: genesis — Phase 2 (commit: f26c048)
`Phase 2: Fabric Admin Implementation (Promote & Manifest)`

Extract: **CAP-BARE-002** — Original promote/manifest design. Were there capabilities here not carried into council/f_N?

---

### PHASE: genesis — Phases 3–6 (commits: 0358dee → 7725c7f)
`Phase 3: Recursive Leap → Phase 6: Binding Leap`

Each "leap" is a named capability. Extract one CAP stub per leap:
- **CAP-BARE-003**: Recursive Leap (self-referential discovery)
- **CAP-BARE-004**: Broker Leap (programmable planning / market arbitrage)
- **CAP-BARE-005**: Interface Leap (normalization proxy)
- **CAP-BARE-006**: Binding Leap (delegated injection)

For each: what did it add? Is any of it in council/f_N? Should any be `[CHERRY-PICK CANDIDATE]`?

---

### PHASE: f_1 Phase 1 (commit: 9e4a10c)
`f_1 Phase 1: Multi-Vault Discovery (Distributed Tiers)`

Extract: **CAP-BARE-007** — Multi-vault federation. Blob lookup across distributed vault tiers. Not present in council/f_N. Flag: `[CHERRY-PICK CANDIDATE]` if this belongs in the roadmap.

---

### PHASE: f_1 Phase 2 (commit: 7daff80)
`f_1 Phase 2: Execution Engine Expansion (Polyglot Runtimes)`

Extract: **CAP-BARE-008** — Polyglot runtimes. Blob execution beyond Python. What languages? What was the design? Why did council/f_N stay Python-only?

---

### PHASE: f_1 Phase 3 (commit: 7967b74)
`f_1 Phase 3: The Market Arbitrage (Broker Marketplace)`

Extract: **CAP-BARE-009** — Multi-provider cost/latency arbitrage. Broker selects execution target based on market signals. Relationship to council/f_N fitness formula?

---

### PHASE: f_1 Phase 4 (commit: 02b14dd)
`f_1 Phase 4: The Interface Evolution (Standardized Proxy)`

Extract: **CAP-BARE-010** — Standardized proxy / interface normalization. Relationship to PROTOCOL.md schema-blob-as-interface design in council/f_N?

---

### PHASE: f_2 Phase 1 (commit: 8f44395)
`f_2 Phase 1: Self-Correction (Autonomous Retries)`

Extract: **CAP-BARE-011** — Autonomous retry logic. How did the system recover from failures? Did council/f_N absorb this differently?

---

### PHASE: f_2 Phase 2 (commit: b261120)
`f_2 Phase 2: Performance Feedback (Dynamic Plasticity)`

Extract: **CAP-BARE-012** — Dynamic plasticity / performance feedback. Compare to council/f_N's telemetry-as-blobs approach.

---

### PHASE: f_2 Phase 3 (commit: 8eeb76c)
`f_2 Phase 3: Formal Protocol (MCP Integration)`

Extract: **CAP-BARE-013** — MCP integration. The fabric speaks Model Context Protocol — LLMs can invoke blobs directly. Significant capability not in council/f_N. Likely `[CHERRY-PICK CANDIDATE]`.

---

### PHASE: f_2 Phase 4 (commit: 2cd3f15)
`f_2 Phase 4: Persistent Memory (The Persistent Substrate)`

Extract: **CAP-BARE-014** — Persistent memory / stateful substrate. What state survived across invocations? How does this relate to the vault design?

---

### PHASE: f_3 Phase 1–3 (commits: e3059ec → 1b2db18)
`f_3: Collective Intelligence (P2P Discovery, Federated Arbitrage, Location-Transparent State)`

Extract three stubs:
- **CAP-BARE-015**: P2P discovery — blobs found across peers, not just local vault
- **CAP-BARE-016**: Federated arbitrage — cross-fabric cost optimization
- **CAP-BARE-017**: Location-transparent state — blob execution location hidden from caller

These are the frontier where the bare tree stopped. Extract: what was working? what was the design? why did it stop here?

---

### LESSON: Why the bare tree stopped at f_3

After walking all phases, write:
- **LESSON-001**: Expansion without a selection mechanism — the bare tree built capabilities without a fitness gate. Each "leap" added scope but there was no mechanism to measure whether the leap improved the system. Contrast with council/f_N where f_N must beat f_(N-1) to be promoted.

---

## After Walking All Phases

1. Review all stubs
2. Produce summary: which are flagged `[CHERRY-PICK CANDIDATE]`?
3. Write to `docs/adr/BARE-WALK-SUMMARY.md`
4. Do not cherry-pick yet — flag only. Brian reviews the flags.
