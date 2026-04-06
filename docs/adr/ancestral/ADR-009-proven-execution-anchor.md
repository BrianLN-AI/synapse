# ADR-009: Proven-Execution Anchor — `record_feedback()` Requires a Prior Invocation
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** council/f_6

## Context

When feedback blobs were introduced (f_4), a structural problem appeared: a caller could record feedback about a blob without having invoked it. Phantom feedback — a `feedback/outcome` blob claiming a blob "failed" when no invocation occurred — would corrupt the FeedbackScore for that blob with no real execution basis.

## Decision

`record_feedback()` is anchored to `_LAST_TELEMETRY[logic_hash]`: the most recent telemetry blob hash produced by invoking this blob in the current process.

```python
_LAST_TELEMETRY: dict[str, str] = {}  # logic_hash → most recent telemetry/artifact hash

# In _record_telemetry():
telem_hash = put("telemetry/artifact", json.dumps(record))
_LAST_TELEMETRY[content_hash] = telem_hash
return telem_hash

# In record_feedback():
invocation_telem = _LAST_TELEMETRY.get(logic_hash)  # None if no invocation in this process
record = {
    "invoked": logic_hash,
    "invocation_telem": invocation_telem,  # proven-execution anchor
    ...
}
```

The `invocation_telem` field links the feedback blob to a specific telemetry artifact — a content-addressed record of an actual invocation. If `_LAST_TELEMETRY` has no entry for `logic_hash`, `invocation_telem` is `None`, which is a signal to the governance review (Pass 4 at f_5) that this feedback has no proven execution basis.

Note: the anchor is process-scoped. `_LAST_TELEMETRY` resets on process restart. This means feedback recorded in a different process from the invocation has `invocation_telem = None`. The governance gate (Pass 4 / FeedbackIntegrity) can reject feedback without a telemetry anchor — the policy is configurable.

## Alternatives Considered

- **No anchor — trust the caller:** Any process can claim any outcome for any blob. Feedback becomes gameable.
- **Require invocation_telem to be non-None (strict anchor):** Would reject all cross-process feedback. Legitimate use cases (a test suite that runs blobs and records outcomes in a second process) would fail.
- **Cryptographic signature by the invoking process:** More robust but requires key management and violates the "secrets never enter context" constraint.
- **Blockchain-style chain of custody:** Far more complex than the use case requires.

## Consequences

- Within a single process, `record_feedback()` always has a telemetry anchor for any blob that was `invoke()`d in that process.
- Cross-process feedback has `invocation_telem = None`. The governance gate (Pass 4, FeedbackIntegrity) does not currently reject `None` anchors — it validates structure, outcome enum, and confidence range, and checks the `invoked` hash exists in the vault.
- [HYPOTHESIS: Pass 4 could be extended to require a non-None anchor as a stronger guarantee. This is a policy choice, not a structural limitation.]
- The `invocation_telem` hash, if present, can be verified: `_raw_get(invocation_telem)` should return a `telemetry/artifact` blob with `invoked == logic_hash`. This check is not currently enforced in Pass 4.

## Evidence Basis

- [MEASURED] `_LAST_TELEMETRY` and `invocation_telem` field in `seed.py` at commit b39ea5f (f_4). The process-scope limitation is explicit in the code comment.
- [MEASURED] `record_feedback()` docstring at commit b39ea5f: "Proven-execution anchor: feedback is tied to _LAST_TELEMETRY[logic_hash]... This means feedback can only be recorded after an actual invocation — it cannot be fabricated without running the blob first."
- [INFERRED] The process-scope limitation is a genuine constraint — cross-process feedback anchoring is not solved. The `invocation_telem = None` case is a gap, not a design decision.
- [MEASURED] Pass 4 (FeedbackIntegrity) in `promote.py` at commit 09a69dd (f_5) validates structure and referential integrity but does not require a non-None anchor.
