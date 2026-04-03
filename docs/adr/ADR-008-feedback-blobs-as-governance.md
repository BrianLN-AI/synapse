# ADR-008: Feedback Blobs as Governance — Downstream Outcomes as Vault Artifacts
**Date:** 2026-04-01
**Status:** Accepted — implemented in f_5 (council/f_5, v1.5.0)
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

f_3 surfaced a fundamental limitation: the fitness formula rewards speed, not correctness. A type guard that prevents silent failures pays a latency penalty with no fitness gain — because the benefit only appears in downstream systems that used the blob's output. Discovery v4's type guard and Telemetry-Reader v4's recency decay were both rejected by the benchmark despite being correctness improvements.

The insight from f_3: "the fitness formula cannot reward correctness improvements. A blob that does more correct work will lose to a simpler faster blob every time. The next question the telemetry reveals: how does the system credit quality without compromising the performance signal?"

## Decision

Introduce a `feedback/outcome` blob type in `seed.py`. Callers record downstream outcomes (pass/fail/partial) after invoking a logic blob. Feedback blobs are stored in the vault via `put("feedback/outcome", ...)`.

A `FeedbackScore` signal (confidence-weighted pass rate, default 1.0 neutral) is added to the fitness formula numerator in Planning v5:

```
f = (sr × integrity × feedback_score) / (latency × burstiness × cost)
```

Feedback blobs are content-addressed and immutable — recording one does not promote it. Whether it influences fitness depends on the governing process (same Triple-Pass + Council Approval as logic blobs, introduced at f_5).

Default FeedbackScore = 1.0 (neutral). Blobs with no feedback are not penalised. Blobs with net-negative governed feedback are penalised proportionally.

## Alternatives Considered

- **Database record for outcomes:** Not content-addressed. Mutable. Not auditable via hash chain.
- **Flag at the blob level (metadata):** Would require mutating the blob, which violates immutability. A new version of the blob with a quality annotation would have a different hash — defeating the purpose.
- **External monitoring/alerting only:** Keeps correctness signals outside the fitness system. The fitness formula never sees them. The type guard problem remains unsolved.
- **Human-curated quality scores:** Not automated. Does not close the feedback loop.

## Consequences

- The vault now contains four blob types: `logic/python`, `telemetry/artifact`, `council/approval`, and `feedback/outcome`. All share the same storage format and are read via `_raw_get()`.
- The fitness formula now has a downstream signal path: invoke → outcome observed → feedback blob written → telemetry-reader aggregates → fitness updated.
- Ungoverned feedback (not promoted via Triple-Pass + Council Approval) is inert. This was the key design insight from f_4: "feedback is only as good as the process that generates it. Ungoverned feedback is just another unreviewed claim." The governance gate was added at f_5.
- The `feedback_score` default of 1.0 means unknown blobs are treated neutrally, not optimistically. A blob with approved-negative feedback falls below 1.0; one with no feedback stays at 1.0.
- The `FeedbackScore` Bayesian smoothing (Planning v6, f_5) blends toward 1.0 when `feedback_count < MIN_FEEDBACK (3)` — prevents one approved-negative feedback from collapsing a blob's score.

## Evidence Basis

- [MEASURED] `record_feedback()` and `feedback/outcome` blob type introduced in `seed.py` at commit b39ea5f (f_4). The design rationale is in the docstring verbatim.
- [MEASURED] f_3 commit message: "f_3 insight: the fitness formula cannot reward correctness improvements." This is the stated motivation for f_4's design.
- [MEASURED] f_4 commit message: "f_4 insight: feedback is only as good as the process that generates it. Ungoverned feedback is just another unreviewed claim."
- [INFERRED] The choice to make feedback governance-gated (rather than trusted by default) was made in response to the f_4 insight, implemented at f_5.
