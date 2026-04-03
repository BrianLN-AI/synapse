# ADR-011: Council Identity as a Governed Blob — Content-Addressed and Promotable
**Date:** 2026-04-01
**Status:** Accepted — implemented in f_6 (council/f_6, v1.6.0)
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

Up to f_5, the council was an implicit actor: a bare string identifier (`"bootstrap"`, `"evolve"`) in council approval artifacts. The council had no formal identity, no content-addressed representation, no validation, and no chain of custody. Any string could impersonate any reviewer without detection.

f_5's feedback governance demonstrated the pattern: ungoverned claims (feedback blobs) are inert until promoted through the same Triple-Pass + Council Approval process as logic blobs. f_6 applied the same pattern to the council's own identity.

## Decision

The council's identity is a `council/reviewer` blob — content-addressed, validated, and promotable. The reviewer is no longer a name; it is a hash. The hash is both the identity and the integrity proof of the reviewer's specification.

This creates a closed governance loop:

- Blobs are promoted by reviewers
- Reviewers are promoted by reviewers
- The trust root is established once by `bootstrap_reviewer()` — self-grounding, minimally privileged, auditable by hash

The `council/reviewer` blob type is governed by the same Triple-Pass Review infrastructure as logic blobs, with an additional Pass 5 (ReviewerIntegrity) that enforces reviewer-specific structural invariants (`trust_weight` in (0.0, 1.0], non-empty `authorized_types`, non-empty `id`).

The evolution engine's own identity (`evolve-engine` reviewer) is defined in `EVOLVE_REVIEWER_PAYLOAD` — a JSON blob stored in the vault and promoted through the governed chain. The engine is not a special case. It is a promoted blob like any other.

## Why This Matters

Without governed reviewer identity:
- Any process could claim to be `"evolve"` or `"bootstrap"` and issue approvals
- Reviewer capabilities (authorized_types, trust_weight) are not enforceable
- There is no audit trail linking a reviewer's existence to a governed decision

With governed reviewer identity:
- A reviewer approval is only valid if `reviewer_hash` is in `manifest["reviewers"]`
- The reviewer blob's `authorized_types` can be checked against the blob being approved
- The trust_weight embedded in the reviewer blob propagates to FeedbackScore weighting
- Every approval is traceable: approval → reviewer_hash → reviewer blob → approving_reviewer_hash → ... → bootstrap trust root

## Consequences

- **Breaking API change at f_6:** `issue_council_approval(reviewer=str)` became `issue_council_approval(reviewer_hash=content_hash)`. All callers updated. Tests from f_5 required updating.
- The `manifest["reviewers"]` registry is the canonical list of approved governance authorities. A reviewer not in this registry cannot sign valid approvals.
- `bootstrap_reviewer()` is the only self-grounding entry point. After it runs, all subsequent governance requires a chain link.
- The evolve-engine reviewer (trust_weight=0.8) can only approve `logic/python` blobs. It cannot approve new reviewers or feedback blobs — that requires the bootstrap reviewer's `authorized_types: ["logic/python", "feedback/outcome", "council/reviewer"]`.
- [INFERRED] The `authorized_types` check is defined in the reviewer blob's spec but not currently enforced at promotion time. `_pass_reviewer_integrity` validates the field exists and is non-empty, but `promote()` does not check that the reviewer is authorised for the blob type being promoted. This is a gap.
- [HYPOTHESIS: enforcing `authorized_types` at `promote()` call time would close the gap. Currently, a reviewer with `authorized_types: ["logic/python"]` can technically sign an approval for a `feedback/outcome` blob — the manifest records it, and `_verify_council_approval` checks reviewer existence but not type authorisation.]

## Evidence Basis

- [MEASURED] `council/reviewer` blob type, `bootstrap_reviewer()`, `promote_reviewer()`, Pass 5 (`_pass_reviewer_integrity`) introduced in `promote.py` at commit 1f48718 (f_6).
- [MEASURED] `EVOLVE_REVIEWER_PAYLOAD` is identical in `bootstrap.py` and `evolve.py` at f_6. `seed.put()` idempotency means computing it twice produces the same hash — no double-promotion risk.
- [MEASURED] `_ensure_evolve_reviewer()` in `evolve.py` at f_6: "On the first run in a fresh environment (e.g., after bootstrap.run()), the evolve reviewer is already promoted by bootstrap.py. This function just verifies that and returns the hash."
- [MEASURED] f_6 commit message: "Governance invariant: every blob promotion is traceable through an immutable content-addressed approval chain back to the trust root."
- [INFERRED] The `authorized_types` enforcement gap was not called out in the f_6 commit message or tests. [HYPOTHESIS: this gap will surface in f_7 as the reviewer registry grows and type-unauthorised approvals become a real risk.]
