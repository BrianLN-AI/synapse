# ADR-010: Trust-Weighted Reviewer Chain — Non-Uniform Trust Across Reviewers
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

Up to f_4, the reviewer field in `council/approval` artifacts was a free-form string (e.g., `"bootstrap"`, `"evolve"`). Any string could be passed as a reviewer identifier. There was no check that the reviewer was registered, authorised for the blob type, or trustworthy. A malicious or incorrect reviewer string had no effect on the governance outcome.

f_4's insight: "feedback is only as good as the process that generates it." The same insight applies to reviewers. f_5 implemented feedback governance (governance gate for feedback blobs). f_6 extended the principle to reviewers themselves.

## Decision (f_5: Feedback Governance)

Add Pass 4 (FeedbackIntegrity) to `triple_pass_review()`. Feedback blobs must pass structural validation before they are counted in FeedbackScore. Introduce `promote_feedback()` and `approved_feedback` registry in the manifest. Only promoted feedback blobs influence fitness.

## Decision (f_6: Reviewer Governance — `council/reviewer` Blob Type)

Introduce a `council/reviewer` blob type. A reviewer is no longer a string but a content-addressed governed blob with:

- `id`: human-readable identifier
- `authorized_types`: list of blob types this reviewer may approve
- `trust_weight`: float in (0.0, 1.0] — authority level applied to feedback confidence
- `criteria`: human-readable description of what this reviewer checks

Every reviewer must pass Pass 5 (ReviewerIntegrity) before it can be used in approvals. `issue_council_approval()` now takes `reviewer_hash` (a content hash) rather than a free-form string.

Trust weights propagate to FeedbackScore: a feedback blob approved by a reviewer with `trust_weight=0.8` counts at 80% confidence. Telemetry-Reader v7 implements this weighting.

## Trust Chain Architecture

```
bootstrap reviewer (trust_weight=1.0, self-grounding, no prior approver)
    ↓ approves
evolve-engine reviewer (trust_weight=0.8, approved by bootstrap)
    ↓ approves
blob promotions (logic/python, feedback/outcome)
```

The bootstrap reviewer is established by `bootstrap_reviewer()` — the only function that does not require a pre-existing approved reviewer. It is self-grounding by design: every governed system has an unverifiable root, and making it small and auditable is the best available option.

## Alternatives Considered

- **Uniform trust (all reviewers equal):** Simpler, but cannot express that an automated evolution engine reviewing its own output is less authoritative than a human-verified trust root.
- **Role-based access control (RBAC):** More expressive but requires a separate identity system. Trust weights embedded in content-addressed blobs are auditable via hash chain without an external registry.
- **Multi-signature requirement (N-of-M):** Stronger governance but more complex. A trust_weight system approximates multi-signature via weighted confidence rather than hard quorum.

## Consequences

- Every existing call to `issue_council_approval(reviewer=str)` was a breaking change at f_6. The API changed to `reviewer_hash=content_hash`. Tests from f_5 required updating (`tests/test_f5.py` updated at f_6 commit 1f48718).
- The governance invariant: every blob promotion is traceable through an immutable content-addressed approval chain back to the trust root.
- `manifest["reviewers"]` registry maps reviewer hashes to metadata (bootstrapped/approved_by, registered_at).
- `linker.read_telemetry()` now builds `reviewer_trust` dict from manifest reviewers and passes it as context to the telemetry-reader blob — wiring trust weights into the signal path.
- The bootstrap reviewer's trust is implicit (weight=1.0, self-grounding). Its `bootstrapped: True` flag in the manifest registry distinguishes it from governed-chain reviewers.
- [INFERRED] The trust weight system creates a partial ordering of reviewer authority. Future iterations could define a quorum policy (promote only if sum(trust_weights of approvers) ≥ threshold).

## Evidence Basis

- [MEASURED] `council/reviewer` blob type, `_pass_reviewer_integrity` (Pass 5), `bootstrap_reviewer()`, `promote_reviewer()` introduced in `promote.py` at commit 1f48718 (f_6).
- [MEASURED] f_6 commit message: "Governance invariant: every blob promotion is traceable through an immutable content-addressed approval chain back to the trust root."
- [MEASURED] `BOOTSTRAP_REVIEWER_PAYLOAD` and `EVOLVE_REVIEWER_PAYLOAD` in `bootstrap.py` at f_6: trust_weight=1.0 and trust_weight=0.8 respectively.
- [MEASURED] `linker.py` at f_6 adds `reviewer_trust` dict construction and passes it to telemetry-reader context.
- [INFERRED] The 0.8 trust_weight for the evolve-engine reviewer (vs 1.0 for bootstrap) reflects that automated feedback from the evolution engine carries less authority than the explicit trust root. The 0.8 value was chosen by the author without a stated derivation.
