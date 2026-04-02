# Synapse Build Log — D-JIT Logic Fabric

A lab notebook covering the construction of Synapse from its first concept through the f_10
generation. This is a record of what was built, what each generation enabled, and why the
sequence matters. Intended for contributors who want to understand the arc before reading code.

---

## What Synapse Is Trying to Become

Synapse is a content-addressed, self-evolving compute fabric: a system where logic (code)
is stored by its hash, governed through a reviewers chain, and evolved by measuring actual
performance against behavioral contracts. The end state is a fabric that accepts a behavioral
specification and an objective, then authors, verifies, benchmarks, and promotes its own
implementations toward those targets — autonomously, with a complete audit trail, without
human authorship of the implementation. Every generation from f_0 through f_10 is a step
toward that capability. The non-council lineage (bare f_0 through f_5) and the council
lineage (council/f_0 through council/f_10, tagged v1.0.0 through v1.10.0) are parallel
experiments from the same base — the council track adds formal governance from its first
commit.

---

## Shared Base

**tag: `unknown` — commit `2d22e7f`**

Repo genesis. A concept before any form. No code, no structure — just the provenance root
that both experiment tracks share.

**tag: `undefined` — commit `f65f4a7`**

Seed potential. The undefined state that both lineages diverge from. The non-council track
branches directly here; the council track adds a genesis commit (`f(0)`) before its first
real commit.

---

## f_0 — The Wavefunction Collapse

**Non-council tag:** `f_0` at `af6b1e0`
**Council tag:** `v1.0.0` at `c31f394`

### What was built

The first working linker: `seed.py` as the entry point and CLI, a four-layer stack
(L1 Interface, L2 Discovery, L3 Planning, L4 Binding), and the vault — a flat directory of
SHA-256-addressed blobs. The Scope-Exchange Protocol ABI: blobs receive a `context` dict and
a `log()` callable, and must assign their output to `result`. No `return` statements. The
manifest (`manifest.json`) records the hash of each layer blob; `manifest.hash` is the root
pointer that lets the system boot without infinite recursion.

The non-council track built this in six sequential phases:
- Phase 1: BIOS/ABI — the scrubbed execution scope and the bootstrap fallback (`_raw_get`)
- Phase 2: Promote — the manifest sealing protocol
- Phase 3: Self-referential Discovery — the Librarian is a blob, found by the BIOS
- Phase 4: Programmable Planning — market arbitrage blob (Cost × Latency × Trust)
- Phase 5: Normalization Proxy — L1 Interface normalizes and stamps trace IDs
- Phase 6: Delegated Injection — L4 decouples the linker from execution

The council track added `COUNCIL.md` as its first commit after genesis — governance declared
before any code — then followed the same phase sequence.

### Key insight

A manifest that seals itself (its hash is content-addressed into `manifest.hash`) creates
an integrity anchor for the entire fabric. The BIOS fallback (`is_bios=True`) resolves the
bootstrapping paradox: Discovery needs Discovery to find Discovery, so the first resolution
must bypass the blob system entirely and read from the filesystem. Every recursive
self-referential system needs this kind of ground truth.

### What it enabled

A working, self-hosted fabric. The layers run as blobs resolved through themselves. f_1
could now attempt the first self-modification cycle: the fabric rewriting its own blobs.

---

## f_1 — First Self-Modification Cycle

**Non-council tag:** `f_1` at `1e4dadbd`
**Council tag:** `v1.1.0` at `cf6ddd4` — identity: `f_1 = f_0(f_0)`

### What was built

The first evolve cycle: `evolve.py` reads the current manifest, generates candidate blobs
(hand-authored v2 implementations), runs Triple-Pass Review (StaticAnalysis →
SafetyVerification → ProtocolCompliance), benchmarks old vs new over N rounds, and promotes
the winner through Council Approval. Telemetry blobs are stored in the vault. A compile
cache (bytecode cache keyed by content hash) was added to reduce cold-start cost. Bayesian
cold-start smoothing for the fitness formula: early invocations don't dominate the signal.
The non-council track added multi-vault discovery (tiered resolution: local → remote) and
polyglot blob execution (Python and Node.js runtimes).

### Key insight

The identity formula `f_1 = f_0(f_0)` is the system description, not marketing. The fabric
used its own invoke and promote machinery to test and admit its own new layer blobs. All
three core blobs (discovery, planning, telemetry-reader) were promoted. Self-modification
requires that the evolve engine be a blob consumer and a blob producer simultaneously — the
engineering tension this creates (what happens if evolve.py promotes a broken blob?) drove
the design of the review gate.

### What it enabled

Proof that the self-modification loop closes. f_2 could now instrument the telemetry path
more carefully and surface p95 latency as a first-class signal.

---

## f_2 — Signal Integrity

**Non-council tag:** `f_2` at `77df2c3e`
**Council tag:** `v1.2.0` at `9c7fb35` — identity: `f_2 = f_1(f_1)`

### What was built

p95 latency wired end-to-end: Welford's online algorithm for O(1) variance tracking. Before
f_2, p95 was computed in the telemetry blob but not surfaced through the full signal path to
planning. f_2 fixed the gap. A Welford-based integrity signal was added. Planning v3 was
promoted with a fitness formula that incorporates p95, achieving approximately 2x fitness
improvement over v2.

### Key insight

Measuring the wrong thing is worse than measuring nothing. The fitness formula in f_1
rewarded average latency — which a blob could improve by getting faster on the common case
while silently failing on edge cases. p95 catches tail behavior that averages mask. The
Welford algorithm made this tractable: O(1) memory, no stored sample list, numerically
stable variance.

### What it enabled

A fitness signal that distinguishes consistent implementations from ones that are fast on
average but erratic under load. f_3 could now address the next gap: the fitness formula
still rewarded speed unconditionally, even when the blob was computing the wrong answer.

---

## f_3 — Persistent Cache and Dynamic Tolerance

**Council tag:** `v1.3.0` at `ec285e3` — identity: `f_3 = f_2(f_2)`

### What was built

On-disk bytecode cache: L2 cold-start speedup by persisting compiled blobs across runs.
Dynamic PROMOTE_TOLERANCE: instead of a hardcoded 0.30 threshold, the evolve engine reads
the audit log and sets the promotion threshold at the 25th percentile of historically
observed fitness improvements. When improvements have been large, the threshold rises;
when improvements have been small, it falls. The formula tracks the actual distribution.

One of three blobs was held — intentionally. The fitness formula still had no downstream
correctness signal.

### Key insight

f_3 made explicit what had been implicit: the fitness formula rewards speed, not
correctness. A blob that computes the wrong answer faster than a correct blob wins the
benchmark. The gap was documented rather than papered over — this is the explicit precursor
to f_4's feedback blobs.

### What it enabled

A diagnostic record of the correctness gap. f_4 could introduce feedback blobs as the
mechanism for carrying downstream correctness signal back into the fitness formula.

---

## f_4 — Feedback Loop Closure

**Council tag:** `v1.4.0` at `b39ea5f` — identity: `f_4 = f_3(f_3)`

### What was built

`feedback/outcome` blob type: callers record downstream outcomes (pass/fail/partial) after
invoking a blob. FeedbackScore added to the fitness formula in planning v5:
`fitness = (success_rate / (latency * burstiness)) * FeedbackScore`. The
telemetry-reader aggregates feedback blobs per logic hash and computes a confidence-weighted
pass rate. Default FeedbackScore is 1.0 (neutral) — blobs with no feedback are not
penalized. Proven-execution anchor: `record_feedback()` is anchored to `_LAST_TELEMETRY`,
so feedback can only be recorded after an actual invocation of the blob, preventing
fabricated feedback.

### Key insight

Ungoverned feedback is just another unreviewed claim. After noticing that any caller could
record arbitrary feedback, Council Approval was required for feedback blobs before they
influence FeedbackScore. The governance gate is now closed: feedback blobs in the vault are
inert until promoted through the same review chain as logic blobs.

### What it enabled

A fitness formula that distinguishes correct blobs from fast-but-wrong ones. f_5 could now
address the next problem: the feedback governance was real, but the governance mechanism
itself (the council) was an informal string, not a governed artifact.

---

## f_5 — Feedback Governance

**Council tag:** `v1.5.0`

### What was built

Governance protocol for feedback/outcome blobs applied to the feedback path itself: the
same Triple-Pass Review + Council Approval required before any feedback influences
FeedbackScore. Changes to `promote.py` added Pass 4 (FeedbackIntegrity): validates that
the invoked hash exists, outcome is a valid enum, and confidence is in range.
`promote_feedback()` stores approved hashes in `manifest["approved_feedback"]`. The linker
passes only approved feedback to the telemetry-reader blob. Blob improvements: v6
telemetry-reader filters by approved set; v6 planning adds Bayesian smoothing for
FeedbackScore when feedback count is below a minimum threshold (cold-start).

Two of three blobs promoted. Telemetry-reader v6 held — the two-pass overhead was a
legitimate cost in sparse-vault conditions.

### Key insight

The insight from f_5's commit message: "The next question: the council itself is a blob.
Governance of the governing process is f_6's problem." When you close one governance loop,
the mechanism enforcing that closure becomes the next ungoverned element. This is the
recursive structure of the whole project.

### What it enabled

A feedback path with integrity guarantees end-to-end. f_6 could address governance of the
governance mechanism itself — the council reviewer as a content-addressed blob.

---

## f_6 — Reviewer Chain

**Council tag:** `v1.6.0`

### What was built

`council/reviewer` blob type: the reviewer is no longer a bare string but a
content-addressed governed blob with `id`, `authorized_types`, `trust_weight`, and
`criteria` fields. Pass 5 (ReviewerIntegrity) verifies that every reviewer blob is
registered in the manifest before it can approve anything. `bootstrap_reviewer()` creates
the trust root — a reviewer with no prior approver, self-grounding by design.
`issue_council_approval()` now requires a `reviewer_hash` (content hash, not free-form
string). The evolve engine has its own governed reviewer identity (trust_weight=0.8,
bootstrap trust_weight=1.0). Trust-weighted FeedbackScore in telemetry-reader v7: a
feedback blob approved by a high-trust reviewer carries more weight than one approved by
a lower-trust reviewer.

Bootstrap sequence: `bootstrap.py` promotes the bootstrap reviewer (trust root), then
promotes the evolve-engine reviewer through that trust root. After bootstrap, all further
reviewer promotions require a registered reviewer's approval.

ADR extraction was added in f_6 as a practice: every iteration now ends with a document
step recording architectural decisions as governed blobs.

### Key insight

Every blob promotion is now traceable through an immutable content-addressed approval chain
back to the trust root. This is the governance invariant. An adversary who wants to inject
a malicious blob must forge the approval chain — which requires compromising the vault
itself, not just submitting a blob.

### What it enabled

A complete reviewer chain with content-addressed trust anchoring. f_7 could now introduce
a correctness gate that was architecturally independent of fitness — because fitness is
speed, and correctness is not.

---

## f_7 — Design by Contract

**Council tag:** `v1.7.0` at `75863a0`

### What was built

The correctness layer. `contract/definition` blob type: declares behavioral contracts in
executable Python — `pre(context) -> bool`, `post(context, result) -> bool`,
`invariant(context, result) -> bool`. Pass 6 (ContractCompliance): a hard gate that runs
the contract against the candidate blob before promotion. A blob that violates its contract
cannot be promoted regardless of fitness. Fitness measures performance; ContractCompliance
measures correctness — these are orthogonal concerns on different axes.

Three additional blob types: `test/case` (structured input/output expectations authored by
a tester role), `adr/decision` (immutable, supersedes-chained architecture decision
records), and `critique/finding` (critic reviewer output — blocking or advisory severity).

Four-role reviewer model: designer (trust_weight=1.0), implementor (0.8), tester (1.0),
critic (0.9). Adversarial separation requirement: the tester reviewer must differ from the
implementor reviewer. Shared authorship creates shared blind spots.

Also introduced in this cycle: blake3 as the canonical content-address hash function
(replacing SHA-256), and ZK_PROTOCOL.md defining a zero-knowledge verification layer for
fitness integrity.

Manifest structure extended per label: `logic/python` + `contract/definition` +
`test/case[]` + `adr/decision`. Version promoted: `1.7.0`.

### Key insight

Without a correctness gate, inference-generated candidates (f_8's target) cannot be trusted.
A fast blob that silently computes the wrong answer is indistinguishable from a correct one
in the fitness formula. ContractCompliance is what makes machine-authored code safe to
benchmark: the contract, written by a human in executable form, is the specification that
inference must satisfy before performance is even measured.

### What it enabled

Safe inference-generated candidates. f_8 could now route an LLM into the evolve cycle as
the implementation author, because the contract gate would catch behavioral violations
regardless of where the code came from.

---

## f_8 — Inference-Generated Candidates

**Council tag:** `v1.8.0` at `cfec991`

### What was built

The LLM inference pipeline: `infer.py` calls the `ai` CLI binary (subprocess, not direct
API) with a structured prompt containing the current blob payload, the behavioral contract
pre/post source verbatim, live fitness signals, and a mutation goal. The LLM proposes an
implementation. The proposal enters the vault through `seed.put()` and faces the full
governance chain — Triple-Pass including Pass 6 ContractCompliance — before benchmarking.

Credential safety: `CF_ACCOUNT_ID`, `CF_GATEWAY_NAME`, `CF_AIG_TOKEN` live in
`os.environ` and are consumed by the `ai` subprocess. They never appear in subprocess
arguments, vault blobs, or audit log entries. The test suite scans for literal credential
strings in the vault and audit log.

Fallback: if the `ai` binary is unavailable or returns a non-zero exit code, `evolve_one()`
falls back to a deterministic hand-authored mutation string for that label. The system is
never blocked on inference availability.

Audit log gains two fields: `generated_via_inference: true|false` and
`inference_model: "haiku"|"sonnet"|null`.

### Key insight

The LLM has no special status. Its output is just another blob. ContractCompliance is what
makes inference-generated candidates trustworthy — not the model, not the prompt, not the
author. This is Design-by-Contract applied to machine authorship: the spec is expressed in
code (the contract blob), and that code is the gate through which all proposals must pass.
The governance chain is unchanged; only the source of candidates changes.

### What it enabled

Candidates generated faster than hand-authoring, exploring implementation space the human
author did not consider. f_9 could now address the next gap: a single model that generates
the implementation also determines whether it "looks correct." Shared understanding creates
shared blind spots.

---

## f_9 — Adversarial Test Authorship

**Council tag:** `v1.9.0` at `b94dde8`

### What was built

A two-model pipeline: `gemini-flash` as implementor, `devstral` as tester. The evolve
cycle gains a tester pass after ContractCompliance: the tester model receives the contract
and the candidate implementation and is explicitly prompted to find failure modes — boundary
conditions, edge cases, inputs the implementor may not have considered. The tester generates
N adversarial `test/case` blobs. These are promoted to the manifest. The candidate must
pass the full test suite before benchmarking proceeds. If any test fails, the candidate is
rejected and the test cases that caused failure are logged to the audit trail.

Test suite accumulation: each f_9+ evolution cycle adds N new `test/case` blobs to the
label's suite. Over time, the test suite becomes a comprehensive adversarial corpus covering
every implementation the evolve engine has ever generated and rejected.

`tolerance` field in test cases: `exact` (result == expected), `structural` (same top-level
keys), `behavioral` (post-condition holds — the default, most flexible). Version: `1.9.0`.

### Key insight

The adversarial separation is structural, not a naming convention. Implementor and tester
are different models by design — a physical fork in the inference pipeline. A model that
misunderstands the contract will generate an implementation that satisfies its own
misunderstanding. ContractCompliance catches behavioral violations against the spec, but
probes with synthetic contexts. The tester probes with adversarial ones. Both gates are
needed.

### What it enabled

A growing adversarial corpus that strengthens with every cycle. f_10 could now address
the static mutation goal problem: the mutation strings in evolve.py were hardcoded and did
not respond to what the audit log was actually telling the system about where fitness was
degrading.

---

## f_10 — Guided Mutation Goals

**Council tag:** `v1.10.0` at `bd498aa`

### What was built

`_derive_mutation_goal(label, signals)` replaces `_MUTATION_GOALS` (the static string
dict). The function reads recent benchmark events from the audit log for the label, inspects
current fitness signals, and derives a goal: if `success_rate < 0.8`, push reliability;
if `volatility > 0.5`, push consistency; if `avg_latency_ms > 10`, push latency; else
improve overall fitness. The hardcoded strings become fallbacks for when the audit log has
insufficient history.

Multi-candidate generation: `N_CANDIDATES = 3`. Each evolve cycle generates three
candidates from the derived mutation goal, filters by Triple-Pass + ContractCompliance +
test suite, then benchmarks all passing candidates against the current blob and promotes
the one with the highest fitness. The cost is three inference calls per cycle.

`_MUTATIONS` (deterministic fallback mutation strings) and `_MUTATION_GOALS` (static
per-label goals) are removed entirely. If inference is unavailable, the cycle returns
`inference-unavailable` and skips — no silent no-op promotions that look like progress.

Audit log: benchmark events now record `candidate_index` and `n_candidates` for future
trend analysis across the pool. Version: `1.10.0`.

### Key insight

The system was evolving without knowing why. A blob's latency could be trending upward
across successive promotions while the evolve engine still used the same "reduce latency"
string it had since the first evolve cycle. The audit log already contained the trend
data — `_derive_mutation_goal` just reads it. Making the mutation goal responsive to
signal trends closes the loop between observation and action.

Removing the deterministic fallback is a deliberate honesty constraint: the system should
not produce promotions when the preconditions for a meaningful promotion (inference
availability, real candidates, real testing) are not met.

### What it enabled

The baseline state for f_11. The fabric can now: generate candidates targeted at actual
performance gaps, test them adversarially with a structurally separate model, verify them
against executable contracts, benchmark the N best candidates, and promote the winner with
a complete audit trail. What it cannot yet do is encode the objective itself as a governed
artifact.

---

## Current State — f_10 Baseline

As of f_10, the fabric can do the following autonomously per evolve cycle:

1. Read the current manifest: logic hash, contract hash, test suite hashes
2. Derive a mutation goal from recent audit log trends and current fitness signals
3. Generate three candidate implementations (gemini-flash, via `ai` CLI binary)
4. For each candidate:
   - Triple-Pass Review (StaticAnalysis, SafetyVerification, ProtocolCompliance,
     SemanticIntegrity, ReviewerIntegrity, ContractCompliance)
   - Adversarial test suite execution (devstral-generated test cases)
5. Benchmark all passing candidates against the current blob (25 rounds, 5 warmup)
6. Promote the winner through Council Approval, update the manifest
7. Record the full decision — candidate index, model used, fitness delta, test outcomes —
   in the audit log, traceable to the trust root

What the human provides: nothing at runtime. The contract and test suite are already
governed artifacts in the vault. The evolve engine reads them, generates against them, and
verifies against them.

What the human still controls: the behavioral contracts (what the blob must do), the
reviewer trust weights (who can approve what), and the objective — which is still a Python
string in `evolve.py`, not a governed artifact.

The three infrastructure labels (discovery, planning, telemetry-reader) are evolved
autonomously. The fabric governs and improves its own operation through the same machinery
it uses for everything else.

---

## What Is Next — f_11 and the GOKR Execution Engine

f_11 addresses the last gap: the objective is not a governed artifact.

The evolve cycle already has the structure of a GOKR loop — Objective (mutation goal),
Key Results (fitness signal thresholds), Initiatives (candidate blobs), Iteration
(benchmark cycles), Retrospective (audit log). But none of these are declared as governed
blobs. The objective lives in a Python string. Key results are inferred from hardcoded
thresholds. The GOKR structure is real but ungoverned.

Three additions are planned for f_11:

**`goal/okr` blob type.** A governed blob that declares the objective in human prose and
the key results as machine-checkable targets:
- `objective`: what we want the capability to do (human-authored prose)
- `key_results`: list of `{metric, target, direction}` tuples, each mapping to a fitness
  signal with a target value and direction (above/below)

When a `goal/okr` is promoted for a label, `_derive_mutation_goal()` reads the key results
against current signal values and generates the mutation goal from the actual gaps. The LLM
receives the objective verbatim in the generation prompt — it generates toward declared
intent, not a hardcoded string.

**Capability blobs.** Domain-specific `logic/python` blobs governed under user-defined
labels — not infrastructure labels (discovery, planning, telemetry-reader), but arbitrary
capability labels: `summarizer`, `classifier`, `extractor`. The governance chain is
identical. The fabric does not distinguish infrastructure from capability at the protocol
level; the difference is only in who defines the label and contract.

**Bootstrap function.** `bootstrap_capability(label, contract_hash, okr_hash,
initial_blob_hash)` wires up a new capability — registers the contract, promotes the OKR,
seeds the vault with an initial implementation — and the fabric begins evolving it
autonomously from that point.

The division of labor after f_11: the human writes the contract (what it must do) and the
OKR (what success looks like). The fabric authors, validates, adversarially tests,
benchmarks, and promotes implementations toward the declared objectives. The audit log
records every decision. The reviewer chain traces every promotion to the trust root.

This is the GOKR execution engine: you write the spec and the success criteria. The fabric
is the engineering team.
