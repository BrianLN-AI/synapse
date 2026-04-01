# Synapse: Experiment Lineages

This document describes the two parallel experiment tracks that constitute Synapse's active development.
All experiments live on branches and tags; **no experiment code has been merged to `main` yet** — `main` is stable documentation and pointers only.

---

## Shared Base (Both Lineages)

Both experiment tracks share a common ancestry:

| Tag | Commit | Description |
| :--- | :--- | :--- |
| `unknown` | `2d22e7f` | **The Unknown** — repo genesis, concept before form |
| `undefined` | `f65f4a7` | **The Undefined** — seed potential, before implementation |

These two commits are the provenance root of the entire fabric.

---

## Non-Council Lineage (`f_*` track)

**Origin:** diverges from `undefined` directly — no council, no governance layer.  
**Character:** a single autonomous agent building the fabric phase by phase.  
**Branches:** `f_0`, `f_1`, `f_2`  
**Tags:** `f_0`, `f_1`, `f_2` (lightweight tags pointing directly at branch heads)

### Phase sequence on `f_0`

```
undefined  →  Phase 1 (BIOS & ABI)
           →  Phase 2 (Promote & Manifest)
           →  Phase 3 (Self-Referential Discovery)
           →  Phase 4 (Programmable Planning)
           →  Phase 5 (Normalization Proxy)
           →  Phase 6 (Delegated Injection)
           →  f_0  "The Wavefunction Collapse: f(undefined) → f_0"  [tag: f_0]
```

The collapse commit (`af6b1e0`) is the explicit marker: potential has collapsed into the first stable form.

### Tag map

| Tag | Commit | Notes |
| :--- | :--- | :--- |
| `f_0` | `af6b1e0` | Wavefunction collapse — first stable seed linker |
| `f_1` | `1e4dadbd` | Second iteration |
| `f_2` | `77df2c3e` | Third iteration |

---

## Council Lineage (`council/f_*` track + `v1.*` tags)

**Origin:** diverges from `undefined` at a distinct genesis commit — `f(0)` — before adding `COUNCIL.md` as the first act.  
**Character:** collective intelligence with a governance layer; every release milestone requires council approval.  
**Branches:** `council/f_0`, `council/f_1`, `council/f_2`, `council/f_3`, `council/f_4`  
**Tags:** annotated tags `v1.0.0`–`v1.4.0` (tag objects with tagger + message, pointing to `council/f_*` branch heads)

### Genesis sequence on `council/f_0`

```
undefined  →  f(0)  [genesis/init]
           →  Initialize worktree ignore
           →  Add COUNCIL.md  ← governance declared first
           →  Phase 1 BIOS Seed (seed.py)
           →  Phase 2 (promote routine + test fixtures)
           →  Phase 3 (Recursive Leap — self-hosted Discovery + Planning)
           →  feat: f_0 — close feedback loop, manifest v1.0.0
           →  chore: ignore runtime artifacts  [tag: v1.0.0]
```

### Release milestones (annotated tags)

| Tag | Commit | Identity | Summary |
| :--- | :--- | :--- | :--- |
| `v1.0.0` | `c31f394` | `f_0` | f_0 defined: self-hosting + closed feedback loop |
| `v1.1.0` | `cf6ddd4` | `f_1 = f_0(f_0)` | f_1: first self-modification cycle complete; co-authored with Claude Sonnet 4.6 |
| `v1.2.0` | `9c7fb35` | `f_2 = f_1(f_1)` | p95 + integrity signals wired end-to-end; co-authored with Claude Sonnet 4.6 |
| `v1.3.0` | `ec285e3` | `f_3 = f_2(f_2)` | Persistent bytecode cache; dynamic tolerance; highlights fitness-vs-correctness gap |
| `v1.4.0` | `b39ea5f` | `f_4 = f_3(f_3)` | Governed feedback loop; Council Approval for feedback/outcome blobs; co-authored with Claude Sonnet 4.6 |

#### v1.0.0 — `f_0 defined: self-hosting + closed feedback loop`
The council experiment reaches its first stable collapse: the seed linker is self-hosted, the feedback loop is closed, and the manifest is at v1.0.0. Tagger: Brian Lloyd-Newberry (BLN), 2026-04-01.

#### v1.1.0 — `f_1: first self-modification cycle complete`
Identity: `f_1 = f_0(f_0)`. The fabric rewrites its own core blobs for the first time. Compile cache, Bayesian cold-start smoothing, Welford p95 approximation. 3/3 blobs promoted. Co-authored with Claude Sonnet 4.6.

#### v1.2.0 — `p95 + integrity signals end-to-end`
Identity: `f_2 = f_1(f_1)`. p95 latency was flowing through telemetry but not the full signal path. f_2 wires it end-to-end and adds a Welford-based integrity signal. Planning v3 achieves ~2× fitness improvement. Co-authored with Claude Sonnet 4.6.

#### v1.3.0 — `persistent bytecode cache; dynamic tolerance`
Identity: `f_3 = f_2(f_2)`. Adds on-disk bytecode cache (L2 cold-start speedup), derives promotion tolerance dynamically from the audit log, and surfaces a key insight: the fitness formula rewards speed, not correctness. 1/3 blobs promoted; the gap is intentional — f_4 addresses it.

#### v1.4.0 — `governed feedback loop`
Identity: `f_4 = f_3(f_3)`. Introduces feedback/outcome blob type: callers record downstream pass/fail/partial outcomes after invocation. FeedbackScore feeds the planning fitness formula. Key insight: ungoverned feedback is just another unreviewed claim — Council Approval required for feedback blobs. Co-authored with Claude Sonnet 4.6.

---

## Full Branch + Tag Map

```
tags:    unknown   undefined
                  |
                  +──────────────────────────────────────────────────────────────+
                  │ Non-council lineage                                          │ Council lineage
                  │                                                              │
                  ↓                                                              ↓
            Phases 1–6                                                     f(0) genesis
                  ↓                                                        COUNCIL.md
            [tag: f_0]  af6b1e0  "The Wavefunction Collapse"             Phases 1–3
                  ↓                                                        close loop
            [tag: f_1]  1e4dadbd                                          [tag: v1.0.0]  c31f394
                  ↓                                                              ↓
            [tag: f_2]  77df2c3e                                          [tag: v1.1.0]  cf6ddd4  f_1=f_0(f_0)
                                                                                 ↓
                                                                          [tag: v1.2.0]  9c7fb35  f_2=f_1(f_1)
                                                                                 ↓
                                                                          [tag: v1.3.0]  ec285e3  f_3=f_2(f_2)
                                                                                 ↓
                                                                          [tag: v1.4.0]  b39ea5f  f_4=f_3(f_3)
```

> **Note:** `council/f_*` branch names use `/` as a namespace separator, not a directory.
> `council/f_0` is a branch named `council/f_0`, not a branch `council` with a subdirectory `f_0`.

---

## Key Differences Between Lineages

| Property | Non-council (`f_*`) | Council (`council/f_*`) |
| :--- | :--- | :--- |
| Genesis | From `undefined` directly | From `undefined` → `f(0)` genesis commit |
| Governance | None (solo agent) | `COUNCIL.md` protocol from the first commit |
| Milestone tags | Lightweight (`f_0`, `f_1`, `f_2`) | Annotated with tagger + message (`v1.0.0`–`v1.4.0`) |
| Identity formula | Phase-by-phase collapse | Self-modification cycles: `f_n = f_(n-1)(f_(n-1))` |
| Co-authorship | Solo | Includes Claude Sonnet 4.6 |

---

*See also: [providence.md](providence.md) for provenance model, tagging conventions, and term definitions.*
