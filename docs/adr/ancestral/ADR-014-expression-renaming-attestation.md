# ADR-014: Expression Renaming and Attestation Tiers

**Date:** 2026-04-02
**Status:** Proposed
**Supersedes:** —
**Superseded by:** —

---

## Context

**Naming:** The system's content-addressed units are currently called "blobs" — Binary Large
OBjects. This name describes the storage format, not the semantic content. In practice,
these units are programs, knowledge, skills, agents, contracts, observations, and goals.
In lambda calculus, programs and data are unified: both are expressions. Every unit in
the vault follows the ABI `f(context) → result` — it is a function, an expression that
evaluates. The word "blob" obscures this.

**Attestation:** In a multi-tenant system with multiple governance authorities, callers need
to know the governance status of an expression they're about to use. The current ABI
returns only `result` — it provides no information about whether the expression was
governed, by whom, or under what criteria. Without this, cross-tenant usage has no
trust signal.

---

## Decision

**Rename blob → expression throughout.**

An "expression" in the lambda calculus sense: a term that evaluates. A value is an
expression. A function is an expression. A program is an expression. Telemetry is an
expression. All units in the vault are expressions, distinguished by type, not by whether
they "run."

The type namespace is unchanged:
- `logic/python` — an expression whose evaluation is Python execution
- `telemetry/json` — an expression encoding an observation
- `governance/quorum` — an expression encoding governance rules
- `schema/json` — an expression encoding structural constraints

**Extend the ABI with an attestation envelope.**

Current ABI:
```
expression(context) → result
```

New ABI:
```
expression(context) → { result, attestation }
```

Where attestation is:

```json
{
  "tier":         1 | 2 | 3,
  "governance":   "<governance-expression-hash> | null",
  "tenant":       "<tenant-id> | null",
  "proof":        "<zk-proof-bytes> | null"
}
```

**Three attestation tiers:**

| Tier | Meaning | Governance hash | Proof |
|------|---------|----------------|-------|
| 1 | Direct by hash — no governance claim | null | null |
| 2 | Alliance-recognized — another tenant's governance is recognized by yours | present | null |
| 3 | Fully governed — your governance promoted this expression | present | present (if governance/proof) |

**Attestation is witness, not enforcement.**

The engine does not refuse to execute Tier 1 expressions. It executes any expression by
hash and attaches the attestation tier to the result. Callers decide whether to require
a minimum tier. This keeps the vault as a commons (no gatekeeping) and decouples
governance checking from execution.

This is consistent with the vault's own model: `vault.get(hash)` returns any expression
regardless of governance status. The engine extends this: `invoke(hash, context)` executes
any expression and reports its governance status.

**Tier determination at invocation:**

```
tier 3: hash is in manifest.blobs[label] for caller's tenant
tier 2: hash is in an alliance-recognized manifest
tier 1: hash exists in vault but is not in any recognized manifest
```

---

## Alternatives Considered

### Keep "blob" as the unit name
- **Pro:** No rename; backward compatible; no confusion for existing users
- **Con:** Obscures that every unit is a function; makes the lambda calculus foundation
  invisible; "blob" suggests raw bytes, not executable knowledge
- **Verdict:** Rejected. The rename is conceptually load-bearing.

### Enforcement at the engine layer (engine refuses Tier 1)
- **Pro:** Hard governance guarantee; no ungoverned expression can run
- **Con:** Couples governance to execution; changing governance rules requires new engine expression
- **Con:** Breaks the commons model (vault returns anything; engine should too)
- **Con:** Cannot run ungoverned expressions during bootstrap or development
- **Verdict:** Rejected. Attestation is the right pattern: witness without gatekeeping.

### No attestation (governance checked externally)
- **Pro:** Simpler engine; no attestation overhead
- **Con:** Every caller must independently compute governance status; no shared signal
- **Con:** In multi-tenant systems, callers cannot easily check another tenant's manifest
- **Verdict:** Rejected. Attestation standardizes the trust signal across all callers.

---

## Consequences

**Immediate:**
- All documentation and code references: "blob" → "expression"
- Variable names, type strings, comments: systematic rename
- `invoke()` return value gains `attestation` field (backward compat: callers who ignore
  the extra field are unaffected)
- Existing type strings (`logic/python`, `telemetry/json`, etc.) are unchanged — they
  are expression type names, not affected by the unit rename

**Ongoing:**
- New code uses "expression" consistently
- The ABI is: `expression(context) → {result, attestation}` — this is the canonical form
- Alliance expressions (ADR-012) feed into Tier 2 attestation computation
- ZK proofs (from `governance/proof` governance type, ADR-013) populate the `proof` field
  in Tier 3 attestation

**Known gaps:**
- Alliance expression schema (which expressions does a tenant recognize from another?)
- Performance: attestation tier computation at invocation time — requires manifest lookup;
  caching strategy needed for hot paths
- The `result` field is unchanged — existing callers work without modification

---

## Evidence Basis

- **[CITED]** Church, "A Formulation of the Simple Theory of Types," 1940; McCarthy,
  "Recursive Functions of Symbolic Expressions," 1960 — programs and data are expressions
- **[INFERRED]** Attestation-as-witness follows from the commons model of the vault (ADR-004)
- **[MEASURED]** Current ABI returns only `result` — attestation field is additive, not breaking
- **[INFERRED]** Three tiers cover the meaningful cases: ungoverned, alliance, fully governed
