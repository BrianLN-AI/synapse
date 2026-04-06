# ADR-013-V2: Atomic Governance Handoff

**Date:** 2026-04-06
**Status:** Experiment / Proposed
**Objective:** Replace race-prone governance promotion with atomic, epoch-based handoffs.

---

## 1. Experiment Design
### Assumptions
- The vault is strictly append-only; an approval blob once written cannot be altered.
- All participants (quorums, automated fitness checkers) have a synchronized view of the global block-height.

### Knowns
- Governance promotion race conditions exist in `ADR-013`.
- The current governance-as-expression doesn't define a handoff state.

### Unknowns
- Is `duration_blocks` a global constant, or does it need to scale with fitness-score variance?
- Does the `governance/transition-proof` payload size impact block propagation latency beyond acceptable limits?

---

## 2. The Hypothesis
A governance evolution $N \to N+1$ is secure IF AND ONLY IF it is enforced by an immutable transition-proof blob that binds the revocation of $N$ to the activation of $N+1$ across a versioned lockout period ($T_{lock}$).

## 3. The Kill Switch
This experiment is a **FAILURE** if:
1. **Epoch Overlap:** An execution trace is produced where both Governance $N$ and $N+1$ return `True` for `authorize(promotion_req)` at any shared block height $H \in [T_{start}, T_{end}]$.
2. **Registry Spoof:** A registry update for $N+1$ is promoted without a valid `transition-proof` blob linking to the `approval-hash` of $N$.
3. **Incentive Stalling:** The design requires human manual intervention to resolve a promotion deadlock during the $T_{lock}$ period.

## 4. Atomic Handoff Protocol
1. **Transition Proof Schema**: Any governance blob promoting a new governance expression MUST include a `transition-proof` payload.
2. **Registry Lockout**: The registry enters a `Locked` state upon transition-proof submission.
3. **Epoch Reconcile**: For `duration_blocks`, the engine REQUIRES multisig confirmation (or dual-proof validation) from both $N$ and $N+1$.
4. **Finality**: Upon expiry of `duration_blocks`, $N$ is cryptographically demoted; $N+1$ becomes the sole authority.

## 5. Consequences
- **Positive**: Atomic, versioned, and auditable governance evolution.
- **Negative**: Governance evolution becomes more latency-intensive (due to $T_{lock}$).
- **Verification**: All transition-proofs are vault-stored and linked in the global manifest audit trail.

---

## 6. Next Audit Step (Council Review)
Submit this ADR to the Council (Lens: *Verifiable Experimenter*) to determine if the $T_{lock}$ duration is sufficient to prevent the "Root of Trust" hijack identified in Audit Round 1.
