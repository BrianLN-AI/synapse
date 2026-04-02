# Design Memo: Temporal Governance

**Date:** 2026-04-02
**Status:** Design — pre-ADR
**Depends on:** ADR-013 (governance-as-expression)

---

## The problem: ossification

Current governance approvals are:
- **Point-in-time**: records that approval happened at time T under governance G
- **Vault-permanent**: append-only storage; approvals cannot be deleted
- **No expiry**: an approval granted in f_0 is still valid in f_12
- **No revocation mechanism**: there is no artifact that invalidates a prior approval

This creates ossification: an expression stays current because nothing challenges it, not
because it is still the best available option. The governance game is **one-shot** — pass
the gate once, remain current indefinitely.

In game theory terms: under one-shot governance, blob authors optimize for the promotion
moment only. Quality after promotion has no governance consequence. The council (now:
governance authority) has no feedback loop on whether its approvals aged well. The
Nash equilibrium is stable but non-improving. [CITED — Fudenberg & Maskin, Folk Theorem, 1986:
repeated games sustain cooperative equilibria; one-shot games do not]

---

## The target state: continuous validity

Governance should be a **live condition**, not a historical fact.

Three mechanisms, in increasing automation:

### 1. Revocation artifacts

An explicit revocation expression in the vault that references a prior approval hash:

```json
{
  "type": "governance/revocation",
  "payload": {
    "revokes":    "<approval-expression-hash>",
    "reason":     "fitness degraded below floor",
    "signed-by":  "<governance-expression-hash>",
    "timestamp":  "2026-04-02T19:00:00Z"
  }
}
```

**Manifest rule**: an expression is current only if no valid revocation artifact references
its approval hash. Validity check at promotion time and optionally at invocation time.

The revocation artifact must itself be signed by the current governance authority — you
cannot revoke your own approval without current governance standing.

### 2. Fitness floor in manifest (semi-automated)

The governance expression declares a fitness floor. If telemetry shows the promoted
expression's fitness has dropped below the floor, it enters an "under review" state:

```json
{
  "type": "governance/threshold",
  "payload": {
    "fitness_floor":   0.75,
    "min_invocations": 100,
    "review_on_drop":  true,
    "demote_on_drop":  false
  }
}
```

With `demote_on_drop: true`, the manifest automatically removes the expression from
"current" status — no human intervention required. The telemetry record is the demotion
artifact.

### 3. ZK-provable continuous validity (fully automated)

The `governance/proof` type (ADR-013) enables fully automated continuous validity:

```json
{
  "type": "governance/proof",
  "payload": {
    "circuit":           "<circuit-expression-hash>",
    "fitness_floor":     0.75,
    "window_invocations": 1000
  }
}
```

A ZK proof that `fitness_score(last_1000_invocations) >= 0.75` computed honestly from
vault telemetry constitutes ongoing validity. The proof is re-generated periodically
(or on demand). If the proof fails, the expression is automatically under review.

This closes the loop: the ZK infrastructure (ADR-001, zk-explore/blob_abi_v2) that was
built to prove content binding can be extended to prove ongoing fitness. The technical
components exist; the connection to the approval lifecycle is the missing piece.

---

## The game theory improvement

Under continuous validity:

- **Blob authors** must optimize for ongoing performance, not just the promotion moment
- **Governance authorities** have a feedback loop — their past approvals are continuously
  re-evaluated; poor approval criteria are exposed over time
- **The game becomes iterated** — in repeated games, cooperative equilibria (maintain quality)
  are sustainable because defection (quality decay) is detected and punished (demotion)

This directly addresses the ossification problem. The governance gate is no longer a
one-time hurdle; it is a continuously enforced standard.

---

## Temporal validity in federation

When two tenants federate (ADR-012 alliance), temporal validity rules must be agreed:

- Does Tenant A's point-in-time approval satisfy Tenant B's continuous validity requirement?
- How long after approval do expressions need recertification for cross-tenant recognition?
- Who can issue valid revocations for cross-tenant recognized expressions?

These are treaty-level questions. The alliance expression (ADR-012) should encode them:

```json
{
  "type": "governance/alliance",
  "payload": {
    "recognizes":      ["<governance-hash-A>", "<governance-hash-B>"],
    "validity":        "continuous",
    "fitness_floor":   0.6,
    "recert_window":   "30d"
  }
}
```

---

## What changes in the manifest

The manifest gains an optional validity window per promoted expression:

```json
{
  "blobs": {
    "discovery": {
      "logic/python": "<hash>",
      "approved-at":  "2026-04-02T19:00:00Z",
      "valid-until":  null,
      "fitness-floor": 0.75
    }
  }
}
```

`valid-until: null` = no expiry (current behavior, backward compatible).
`valid-until: <timestamp>` = hard expiry; expression must be re-promoted before then.
`fitness-floor: <float>` = continuous validity; checked against live telemetry.

---

## Open questions before ADR

1. **Who checks validity?** At invocation time (expensive, inline), at promotion time
   (checks prior expression), or by a background governance daemon?

2. **Graceful demotion**: when an expression is demoted, what runs instead? The prior
   promoted version? Nothing? A fallback expression hash in the manifest?

3. **Proof freshness**: for `governance/proof`, how often must the proof be regenerated?
   Who pays the proving cost? This is a significant compute expense.

4. **Revocation storm**: if a governance key is compromised and an attacker revokes many
   expressions, what is the recovery path? Requires a "re-promotion under new governance"
   emergency protocol.
