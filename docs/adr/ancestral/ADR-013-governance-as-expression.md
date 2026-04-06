# ADR-013: Governance as a Typed Expression

**Date:** 2026-04-02
**Status:** Proposed
**Supersedes:** ADR-011 (council-identity-as-governed-blob — subsumed and generalized)
**Superseded by:** —

---

## Context

Prior to this ADR, governance was represented as a "council" — a social structure (a group
of agents who deliberate and approve). The word "council" conflates two distinct things:

1. **The authority**: who or what has standing to approve a promotion
2. **The mechanism**: how that authority reaches a decision (N-of-M signatures, fitness
   threshold, ZK proof, etc.)

ADR-011 established that council identity should be a governed blob. This ADR generalizes
that: governance itself is a typed expression in the vault, subject to the same evolution
gate as any other expression. The mechanism is encoded in the expression type.

The rename from "council" to "governance" throughout the system reflects this generalization:
governance is an abstraction, not a social structure.

---

## Decision

**Governance is a typed expression. The manifest references a governance expression hash.**

**Taxonomy of governance types:**

```
governance/single-key   — one key, one signature (bootstrap / genesis)
governance/quorum       — N of M threshold signatures
governance/threshold    — automated fitness floor, no signers required
governance/proof        — ZK proof of fitness satisfies governance
```

**`governance/single-key`** — the bootstrap case:
```json
{
  "type": "governance/single-key",
  "payload": {
    "key": "<public-key-hex>"
  }
}
```

**`governance/quorum`** — N of M signers:
```json
{
  "type": "governance/quorum",
  "payload": {
    "members":  ["<key-hash-1>", "<key-hash-2>", "<key-hash-3>"],
    "required": 2
  }
}
```

`required` is N. `members.length` is M. "Council" is the social term for a quorum
governance structure — the type name reflects the mechanism, not the social arrangement.

**`governance/threshold`** — automated fitness gate:
```json
{
  "type": "governance/threshold",
  "payload": {
    "fitness_floor":  0.75,
    "min_invocations": 100,
    "window":         "7d"
  }
}
```

No human signatures required. The telemetry record is the approval artifact. A promotion
is valid if the candidate's fitness score over the specified window exceeds the floor.

**`governance/proof`** — ZK proof satisfies governance:
```json
{
  "type": "governance/proof",
  "payload": {
    "circuit":        "<circuit-expression-hash>",
    "fitness_floor":  0.75
  }
}
```

A valid ZK proof that `fitness_score >= floor` computed honestly from vault telemetry
constitutes approval. No signers, no human review. The circuit expression defines what
counts as a valid proof. This is the fully automated governance endpoint.

**Hybrid layering:**

The manifest supports governance at two levels:
- `manifest.governance` — tenant default (applies to all labels)
- `manifest.blobs[label].governance` — per-label override

Engine checks label governance first, falls back to tenant governance. This allows
security-critical expressions to require stricter governance (e.g., `governance/quorum`
with a higher required count) while routine expressions use automated threshold governance.

**Changing governance:**

Changing governance = promoting a new governance expression to the manifest. The old
governance expression remains in the vault — full audit history of who governed at every
point in time.

**Bootstrap governance:**

The genesis blob (ADR-012) references the initial governance expression. The very first
governance expression is `governance/single-key` with the tenant's founding key. This is
the founding exception — the one governance artifact that is not itself governed by a
prior governance expression. Every subsequent governance change goes through the current
governance gate.

---

## Alternatives Considered

### Keep "council" as the governance abstraction
- **Pro:** Consistent with prior ADRs; no rename required
- **Con:** "Council" implies a social structure; obscures that governance is a mechanism
- **Con:** Makes it hard to express automated governance (governance/threshold, governance/proof)
  without the concept feeling like a category error
- **Verdict:** Rejected. The rename is load-bearing: it opens the abstraction correctly.

### Governance as a field, not a blob
- **Pro:** Simpler; no extra vault entry
- **Con:** Governance rules are not auditable, not content-addressed, not evolvable via the gate
- **Con:** Changing governance rules cannot be governed by existing governance
- **Verdict:** Rejected. Governance-as-expression is required for the system to be self-consistent.

### Single governance type (quorum only)
- **Pro:** Simpler taxonomy; less to implement
- **Con:** Cannot express automated governance; requires humans in all promotion paths
- **Con:** Prevents evolution toward fully automated governance (ZK proof endpoint)
- **Verdict:** Rejected. The taxonomy reflects genuinely different mechanisms.

---

## Consequences

**Immediate:**
- Blob type namespace `governance/` now has four defined subtypes
- `manifest.council` field renamed to `manifest.governance`
- ADR-011 is subsumed — its content is generalized here
- All references to "council" in code and documentation should migrate to "governance"
  (backward compat: `council` field accepted but deprecated)

**Ongoing:**
- Governance expressions are evolved through the standard gate like any expression
- The evolution path: single-key → quorum → threshold → proof (each step removes a human
  from the promotion loop and replaces them with a verifiable claim)
- New governance types may be added by defining a new `governance/<type>` expression
  and promoting it as the tenant's governance expression

**Known gaps:**
- Key rotation protocol for `governance/single-key` and `governance/quorum` members
- Revocation: what happens when a governance expression is invalidated (see TEMPORAL-GOVERNANCE.md)
- Governance of governance: the first governance change after genesis requires the genesis
  key to sign — recursive bootstrapping is handled by the single-key genesis case

---

## Evidence Basis

- **[MEASURED]** ADR-011 established governance as a governed blob; this ADR generalizes
- **[INFERRED]** governance/threshold and governance/proof follow naturally from the telemetry
  and ZK infrastructure already in place (ADR-006, ADR-009, zk-explore/blob_abi_v2)
- **[CITED]** Threshold signature schemes (N-of-M) are standard in cryptographic literature;
  the quorum naming is consistent with distributed systems usage (Paxos, Raft)
