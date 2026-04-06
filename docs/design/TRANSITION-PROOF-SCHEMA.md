# Proposed Transition Proof Schema (for ADR-013)

### Transition Proof (Governance Handoff)

The transition between governance epochs ($N \to N+1$) MUST be cryptographically verified. This payload is required for `governance/proof` and `governance/quorum` handoffs.

```json
{
  "type": "governance/transition-proof",
  "payload": {
    "epoch": {
      "from": "<governance-hash-N>",
      "to":   "<governance-hash-N+1>"
    },
    "lockout_period": {
      "start": "<iso-timestamp>",
      "duration_blocks": 100
    },
    "authentication": {
      "signature": "<signature-from-N-authority>",
      "proof":     "<zk-proof-of-fitness-N+1>"
    }
  }
}
```

### Atomic Handoff Protocol (Sequence)

1. **PROPOSE**: Candidate $N+1$ submits the transition proof to governance $N$.
2. **LOCK**: Upon verification, the registry enters `Epoch-Lockout` state.
3. **RECONCILE**: For `duration_blocks`, both $N$ and $N+1$ MUST approve any blob promotion for it to succeed. (Any disagreement results in a rejection).
4. **COMMIT**: After `duration_blocks`, governance $N+1$ asserts exclusive authority.
