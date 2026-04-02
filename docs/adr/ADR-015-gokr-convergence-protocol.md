# ADR-015: GOKR Convergence Protocol

**Date:** 2026-04-02
**Status:** Proposed
**Supersedes:** —
**Superseded by:** —

---

## Context

The f_10 evolve cycle has the structural shape of a GOKR loop: mutation goal (Objective),
fitness signal thresholds (Key Results), candidate blobs (Initiatives), benchmark cycles
(Iteration), audit log (Retrospective). But none of these are declared as governed artifacts
in the vault — the objective is a Python string in `evolve.py`, the key results are
hardcoded thresholds, and there is no protocol for multiple AI systems to contribute to
or evolve the GOKR itself.

Two gaps follow from this:

1. **The GOKR is ungoverned.** Changing the objective requires editing source code. There is
   no audit trail for why the objective changed, no proposal mechanism, no synthesis step.

2. **Multi-session collaboration is ad-hoc.** If multiple AI systems (Claude, Gemini, Devstral,
   etc.) are to contribute to a shared capability, there is no protocol for: how a session
   declares its contribution, how cold-start sessions recover context, or how proposals from
   different sessions converge to a canonical next state.

This ADR establishes the GOKR as a first-class artifact in the vault and defines the
protocol for multi-session, multi-model collaborative evolution.

---

## Decision

### Blob Types

**`goal/gokr`** — the canonical shared objective:

```json
{
  "type": "goal/gokr",
  "payload": {
    "objective": "<human-authored prose — what we want the system to do>",
    "key_results": [
      { "metric": "fitness_score", "target": 0.85, "direction": "gte" },
      { "metric": "p95_latency_ms", "target": 10, "direction": "lte" }
    ],
    "current_f_n": "f_11",
    "open_questions": [
      "Should OKR evolution require quorum approval or threshold governance?"
    ],
    "predecessor": "<prior gokr blob hash or null>"
  }
}
```

`predecessor` chains GOKR versions into an immutable history. The manifest references
the canonical GOKR hash. Changing the GOKR requires a governed promotion through the
same evolution gate as any other expression.

---

**`proposal/roadmap`** — one session's answer to the current GOKR:

```json
{
  "type": "proposal/roadmap",
  "payload": {
    "gokr_hash": "<hash of the goal/gokr blob this responds to>",
    "model": "gemini-2.5-flash",
    "session_context": "synapse-cli-2026-04-02",
    "proposals": [
      {
        "title": "<short label>",
        "description": "<what to build and why>",
        "key_result_impact": { "fitness_score": "+0.10", "p95_latency_ms": "-2" },
        "effort": "medium",
        "open_questions": []
      }
    ],
    "rationale": "<why this model prioritized these proposals over alternatives>",
    "divergences": "<where this model's view differs from prior proposals, if known>"
  }
}
```

`model` is stamped by the session that writes the blob, not derived from the vault.
This enables trust-weighted synthesis — a `proposal/roadmap` from a high-trust model
carries more weight in convergence.

`divergences` is optional but encouraged: explicit disagreement is signal, not noise.

---

**`synthesis/gokr`** — convergence output from N proposals:

```json
{
  "type": "synthesis/gokr",
  "payload": {
    "gokr_hash": "<hash of the goal/gokr blob being synthesized>",
    "proposal_hashes": ["<hash1>", "<hash2>", "<hash3>"],
    "synthesizer_model": "claude-sonnet-4-6",
    "convergence_points": [
      "<claim that 2+ proposals independently reached>"
    ],
    "divergence_points": [
      {
        "topic": "<what they disagreed on>",
        "positions": { "gemini-2.5-flash": "...", "claude-sonnet-4-6": "..." },
        "resolution": "<chosen direction and why, or 'unresolved'>"
      }
    ],
    "overrules": [
      {
        "prior_synthesis_hash": "<hash of synthesis/gokr being overruled>",
        "overruled_convergence_point": "<exact text of the prior convergence point>",
        "reason": "<why the prior consensus no longer holds>"
      }
    ],
    "next_gokr": {
      "objective": "<refined objective for next cycle>",
      "key_results": [],
      "open_questions": []
    }
  }
}
```

`overrules` is optional and normally empty. When a synthesis explicitly contradicts a
`convergence_point` from a prior synthesis, it must name the prior synthesis hash and
the overruled point. A non-empty `overrules` field triggers heavier governance
requirements for the resulting `goal/gokr` promotion (quorum required, not threshold).
This is the system's equivalent of overruling precedent — permitted, but it must leave
a traceable record and requires broader consensus than ordinary evolution.

A `synthesis/gokr` blob is the input to the next `goal/gokr`. The synthesizer produces
a `next_gokr` payload; a governed promotion mints the next `goal/gokr` blob from it.

---

**`context/session-handoff`** — cold-start protocol for any session:

```json
{
  "type": "context/session-handoff",
  "payload": {
    "gokr_hash": "<current canonical goal/gokr hash>",
    "current_f_n": "f_11",
    "recent_proposal_hashes": ["<hash1>", "<hash2>"],
    "latest_synthesis_hash": "<hash or null>",
    "open_questions": [
      "<questions from the GOKR or synthesis that need answering>"
    ],
    "session_summary": "<1-3 sentence prose summary of where things stand>",
    "timestamp": "2026-04-02T19:00:00Z"
  }
}
```

Any session can load the latest `context/session-handoff` blob and immediately understand:
what the current objective is, what proposals exist, what's unresolved. The vault is the
shared memory; this blob is the index into it.

---

### Protocol

**Session init:**

```bash
synapse-session-init [--gokr <hash>]
```

1. Look up the latest `context/session-handoff` blob in the vault (by mtime or manifest pointer).
2. If found: load it. Print the GOKR objective, key results, recent proposals, open questions.
3. If not found: bootstrap. Accept a human-authored `goal/gokr` as the first blob, write it
   to the vault, create an initial handoff blob.
4. Print a structured system prompt that any AI can use to orient and begin contributing.

**Session contribute:**

Any session that has a proposal writes it as a `proposal/roadmap` blob directly to the vault.
No coordination required — the vault is the shared substrate.

**Synthesis run:**

```bash
synapse-synthesize [--gokr <hash>] [--proposals <hash1,hash2,...>]
```

1. Load all `proposal/roadmap` blobs that reference the current `gokr_hash`.
2. Dispatch to a synthesis model (configurable; default: `ai sonnet`).
3. Write the resulting `synthesis/gokr` blob to the vault.
4. If synthesis includes a `next_gokr`, mint the next `goal/gokr` blob (requires governance approval).
5. Update the `context/session-handoff` blob.

**Session close:**

```bash
synapse-session-close --summary "<1-3 sentence summary>"
```

Writes a new `context/session-handoff` blob with the current state. Any subsequent session
will load this as its starting context.

---

## Rationale

**Why blobs for GOKR?** The blob vault is already the system's source of truth for governed
artifacts. Making the GOKR a blob gives it the same immutability, content-addressing, and
audit trail as any other expression. Changing the objective leaves a traceable record.

**Why stamp `model` in the proposal blob?** Different models have different strengths and
blind spots. Explicit model attribution enables trust-weighted synthesis (a proposal from
a model with a strong track record on a given label type carries more weight) and makes
divergence analysis meaningful (where Gemini and Claude disagree is often where the
interesting design tension lives).

**Why `divergences` as an explicit field?** Convergence on the same point across independent
sessions is the strongest architectural signal (IAC — Independent Agent Convergence).
Divergence is equally useful: it identifies open design questions. Both are lost if proposals
are naively summarized.

**Why keep the `ai` subprocess boundary?** Credentials never enter vault artifacts. The
`proposal/roadmap` blob contains the model name but not the API key used to call it. The
subprocess boundary enforces this structurally.

**Why `session-handoff` as a blob?** Session state must survive across context resets,
model switches, and days-long gaps. A blob in the vault is the only artifact type that
persists reliably across all of these. The alternative — a markdown file or a CLAUDE.md
annotation — is not governed and not content-addressed.

---

## Consequences

- Four new blob types: `goal/gokr`, `proposal/roadmap`, `synthesis/gokr`, `context/session-handoff`
- Three new scripts: `synapse-session-init`, `synapse-synthesize`, `synapse-session-close`
- The manifest gains a `gokr` pointer (the canonical current `goal/gokr` hash) alongside
  the existing `governance` and `blobs` fields
- The evolve cycle's `mutation_goal` string in `evolve.py` is eventually replaced by a
  reference to the active `goal/gokr` blob (this migration is f_12 work, not a blocker)
- Multi-session, multi-model contribution becomes the default workflow, not an exception

## Open Questions

- Should `goal/gokr` promotion require `governance/quorum` (human approval) or can it be
  `governance/threshold` (automated fitness)? Objectives feel like they need human intent —
  but a fitness-driven objective shift is exactly what f_10's `_derive_mutation_goal` does.
- Should `synthesis/gokr` require governance approval before a new `goal/gokr` is minted,
  or is the synthesizer model's output sufficient?
- Is `synapse-session-init` a Python script, a shell script, or a blob that invokes itself
  (homoiconic bootstrap)?
