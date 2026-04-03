# Synapse Build Log — D-JIT Logic Fabric

A lab notebook covering the construction of Synapse from its first concept through the f_20
generation. This is a record of what was built, what each generation enabled, and why the
sequence matters. Intended for contributors who want to understand the arc before reading code.

---

## What Synapse Is Trying to Become

Synapse is a content-addressed, self-evolving compute fabric: a system where logic (code)
is stored by its hash, governed through a reviewer chain, and evolved by measuring actual
performance against behavioral contracts. The end state is a fabric that accepts a behavioral
specification and an objective, then authors, verifies, benchmarks, and promotes its own
implementations toward those targets — autonomously, with a complete audit trail, without
human authorship of the implementation. Every generation from f_0 through f_20 is a step
toward that capability.

---

## Shared Base

**tag: `unknown` — commit `2d22e7f`**

Repo genesis. A concept before any form. No code, no structure — just the provenance root.

**tag: `undefined` — commit `f65f4a7`**

Seed potential. The undefined state the council lineage diverges from.

---

## f_0 — The Wavefunction Collapse

**Council tag:** `v1.0.0` at `c31f394`

### What was built

The first working linker: `seed.py` as the entry point and CLI, a four-layer stack
(L1 Interface, L2 Discovery, L3 Planning, L4 Binding), and the vault — a flat directory of
SHA-256-addressed blobs. The Scope-Exchange Protocol ABI: blobs receive a `context` dict and
a `log()` callable, and must assign their output to `result`. No `return` statements. The
manifest (`manifest.json`) records the hash of each layer blob; `manifest.hash` is the root
pointer that lets the system boot without infinite recursion.

Six sequential phases: Phase 1 (BIOS/ABI — scrubbed execution scope and bootstrap fallback),
Phase 2 (Promote — manifest sealing protocol), Phase 3 (Self-referential Discovery — the
Librarian is a blob found by the BIOS), Phase 4 (Programmable Planning — market arbitrage
blob), Phase 5 (Normalization Proxy), Phase 6 (Delegated Injection). `COUNCIL.md` was the
first commit — governance declared before code.

### Key insight

A manifest that seals itself creates an integrity anchor for the entire fabric. The BIOS
fallback (`_raw_get`) resolves the bootstrapping paradox: Discovery needs Discovery to find
Discovery, so the first resolution must bypass the blob system entirely. Every recursive
self-referential system needs this ground truth.

---

## f_1 — First Self-Modification Cycle

**Council tag:** `v1.1.0` — identity: `f_1 = f_0(f_0)`

### What was built

The first evolve cycle: `evolve.py` reads the current manifest, generates candidate blobs,
runs Triple-Pass Review (StaticAnalysis → SafetyVerification → ProtocolCompliance),
benchmarks old vs new over N rounds, and promotes the winner through Council Approval.
Telemetry blobs stored in the vault. Compile cache (bytecode cache keyed by content hash)
added to reduce cold-start cost. Bayesian cold-start smoothing for the fitness formula.

### Key insight

The identity formula `f_1 = f_0(f_0)` is the system description, not marketing. The fabric
used its own invoke and promote machinery to test and admit its own new layer blobs.
Self-modification requires that the evolve engine be a blob consumer and producer
simultaneously — the engineering tension this creates drove the design of the review gate.

---

## f_2 — Signal Integrity

**Council tag:** `v1.2.0` — identity: `f_2 = f_1(f_1)`

### What was built

p95 latency wired end-to-end using Welford's online algorithm for O(1) variance tracking.
Before f_2, p95 was computed in the telemetry blob but not surfaced through the full signal
path to planning. Planning v3 promoted with a fitness formula incorporating p95, achieving
~2x fitness improvement over v2.

### Key insight

Measuring the wrong thing is worse than measuring nothing. The fitness formula in f_1
rewarded average latency — which a blob could improve on the common case while silently
failing on edge cases. p95 catches tail behavior that averages mask.

---

## f_3 — Persistent Cache and Dynamic Tolerance

**Council tag:** `v1.3.0` — identity: `f_3 = f_2(f_2)`

### What was built

On-disk bytecode cache: L2 cold-start speedup by persisting compiled blobs across runs.
Dynamic PROMOTE_TOLERANCE: the evolve engine reads the audit log and sets the promotion
threshold at the 25th percentile of historically observed fitness improvements. One of
three blobs was held — intentionally. The fitness formula still had no downstream
correctness signal.

### Key insight

f_3 made explicit what had been implicit: the fitness formula rewards speed, not correctness.
A blob that computes the wrong answer faster than a correct blob wins the benchmark. The gap
was documented rather than papered over — the explicit precursor to f_4's feedback blobs.

---

## f_4 — Feedback Loop Closure

**Council tag:** `v1.4.0` — identity: `f_4 = f_3(f_3)`

### What was built

`feedback/outcome` blob type: callers record downstream outcomes after invoking a blob.
FeedbackScore added to the fitness formula in planning v5. Proven-execution anchor:
`record_feedback()` is anchored to `_LAST_TELEMETRY`, so feedback can only be recorded
after an actual invocation of the blob — preventing fabricated feedback.

### Key insight

Ungoverned feedback is just another unreviewed claim. After noticing any caller could record
arbitrary feedback, Council Approval was required for feedback blobs before they influence
FeedbackScore. The governance gate is now closed: feedback blobs are inert until promoted
through the same review chain as logic blobs.

---

## f_5 — Feedback Governance

**Council tag:** `v1.5.0`

### What was built

Pass 4 (FeedbackIntegrity): validates that the invoked hash exists, outcome is a valid enum,
and confidence is in range. `promote_feedback()` stores approved hashes in
`manifest["approved_feedback"]`. Two of three blobs promoted. Telemetry-reader v6 held —
the two-pass overhead was a legitimate cost in sparse-vault conditions.

### Key insight

"The council itself is a blob. Governance of the governing process is f_6's problem." When
you close one governance loop, the mechanism enforcing that closure becomes the next
ungoverned element. This is the recursive structure of the whole project.

---

## f_6 — Reviewer Chain

**Council tag:** `v1.6.0`

### What was built

`council/reviewer` blob type: the reviewer is content-addressed with `id`,
`authorized_types`, `trust_weight`, and `criteria` fields. Pass 5 (ReviewerIntegrity)
verifies that every reviewer blob is registered in the manifest before it can approve
anything. `bootstrap_reviewer()` creates the trust root — a reviewer with no prior approver,
self-grounding by design. Trust-weighted FeedbackScore in telemetry-reader v7. ADR
extraction added as a practice: every iteration now ends with a document step.

### Key insight

Every blob promotion is now traceable through an immutable content-addressed approval chain
back to the trust root. An adversary who wants to inject a malicious blob must forge the
approval chain — which requires compromising the vault itself, not just submitting a blob.

---

## f_7 — Design by Contract

**Council tag:** `v1.7.0`

### What was built

`contract/definition` blob type: declares behavioral contracts as executable Python —
`pre(context)`, `post(context, result)`, `invariant(context, result)`. Pass 6
(ContractCompliance): a hard gate that runs the contract against the candidate before
promotion. A blob that violates its contract cannot be promoted regardless of fitness.
Four-role reviewer model: designer (1.0), implementor (0.8), tester (1.0), critic (0.9).
Adversarial separation: tester reviewer must differ from implementor reviewer. Also in f_7:
blake3 as the canonical content-address hash function (replacing SHA-256).

### Key insight

Without a correctness gate, inference-generated candidates (f_8's target) cannot be trusted.
ContractCompliance is what makes machine-authored code safe to benchmark: the contract is
the specification that inference must satisfy before performance is measured.

---

## f_8 — Inference-Generated Candidates

**Council tag:** `v1.8.0`

### What was built

`infer.py` calls the `ai` CLI binary (subprocess, not direct API) with a structured prompt:
current blob payload, contract pre/post source verbatim, live fitness signals, mutation goal.
The LLM proposes an implementation. The proposal enters the vault through `seed.put()` and
faces the full governance chain before benchmarking. Credential safety: credentials live in
`os.environ` consumed by the subprocess — they never appear in vault blobs or audit log.

### Key insight

The LLM has no special status. Its output is just another blob. ContractCompliance is what
makes inference-generated candidates trustworthy — not the model, not the prompt, not the
author.

---

## f_9 — Adversarial Test Authorship

**Council tag:** `v1.9.0`

### What was built

Two-model pipeline: `gemini-flash` as implementor, `devstral` as tester. The tester model
receives the contract and candidate implementation and is explicitly prompted to find failure
modes. Generates N adversarial `test/case` blobs. The candidate must pass the full test
suite before benchmarking proceeds. Test suite accumulates across cycles — a growing
adversarial corpus covering every rejected implementation.

### Key insight

The adversarial separation is structural, not a naming convention. Implementor and tester
are different models by design — a physical fork in the inference pipeline. A model that
misunderstands the contract generates an implementation satisfying its own misunderstanding.
ContractCompliance and adversarial testing are orthogonal gates — both are needed.

---

## f_10 — Guided Mutation Goals

**Council tag:** `v1.10.0`

### What was built

`_derive_mutation_goal(label, signals)` replaces `_MUTATION_GOALS` (static string dict).
Reads recent benchmark events from the audit log and derives a goal responsive to actual
signal trends. Multi-candidate generation: `N_CANDIDATES = 3`. Benchmarks all passing
candidates, promotes the highest fitness winner. `_MUTATIONS` (deterministic fallback
strings) removed entirely — if inference is unavailable, the cycle returns
`inference-unavailable` and skips. No silent no-op promotions.

### Key insight

The system was evolving without knowing why. The audit log already contained the trend
data — `_derive_mutation_goal` just reads it. Making the mutation goal responsive to signal
trends closes the loop between observation and action. Removing the deterministic fallback
is a deliberate honesty constraint: the system should not produce promotions when the
preconditions for a meaningful promotion are not met.

---

## f_11 — GOKR Execution Engine

**Council tag:** `v1.11.0`

### What was built

The objective is now a governed artifact. `goal/okr` blob type: declares the objective in
human prose and key results as machine-checkable `{metric, target, direction}` tuples.
When a `goal/okr` is promoted for a label, `_mutation_goal_from_okr()` reads the key results
against current signal values and generates the mutation goal from actual gaps — the LLM
receives the objective verbatim. `run_all()` now discovers all capability labels from
`manifest["blobs"]` dynamically; no longer hardcoded to three infrastructure labels.

`bootstrap_capability(label, contract_hash, okr_hash, initial_blob_hash)` wires up a new
capability label in one atomic operation: validates all three blobs, promotes them as a
set under council approval, seeds the vault with an initial implementation. After this call,
the fabric evolves the new capability autonomously.

### Key insight

The division of labor after f_11: the human writes the contract (what it must do) and the
OKR (what success looks like). The fabric authors, validates, adversarially tests,
benchmarks, and promotes implementations toward those objectives. The audit log records
every decision. The reviewer chain traces every promotion to the trust root. This is the
GOKR execution engine: you write the spec and the success criteria. The fabric is the
engineering team.

---

## f_12 — Blake3 as Canonical Hash

**Council tag:** `v1.12.0`

### What was built

Blake3 replaces SHA-256 throughout the content-addressing layer. `seed.py` vault address is
now `blake3(envelope)` — blob identity is its blake3 hash. `promote.py` manifest hash is now
`blake3(content)` — the self-seal uses blake3. First commit of `bootstrap.py`, `infer.py`,
and `linker.py` as tracked files (previously untracked). All 259/259 tests passing across
eight generations. Closes ADR-001 for the Python layer.

### Key insight

Blake3 is 5–15x faster than SHA-256 in software and designed for parallel verification.
For a content-addressed system that hashes on every put and every manifest write, the
hashing cost is in the critical path. The migration was clean because vault files are named
by bare hex — changing the hash function changes what the names are, not how the filesystem
works.

---

## f_13 — Engine as Expression

**Council tag:** `v1.13.0`

### What was built

All execution policy — bytecode cache, telemetry recording, ABI enforcement — moved out of
`seed.py` into a promotable `logic/python` expression stored in the vault. The kernel
collapsed to ~30 lines: `put()`, `_raw_get()`, `_load_engine()` (one fixed exec dispatch),
and a kernel-fallback `invoke()` for pre-engine bootstrap. The engine blob is a governed,
content-addressed expression like any other. It can be inspected, benchmarked, and promoted
through the standard governance chain.

### Key insight

The kernel's only irreducible responsibility is bootstrapping: retrieving blobs from the
vault and loading the engine that handles everything else. Any policy that can live in the
engine blob should live there — not in the kernel, which cannot evolve itself without losing
the ground truth. f_13 is the system eating the last structural special case in its own
execution layer.

---

## f_14 — logic/engine Blob Type

**Council tag:** `v1.14.0`

### What was built

The f_13 engine blob used an `_exec()` injection workaround to pass the safety scanner's
exec-forbidden check. f_14 replaced the workaround with a proper `logic/engine` blob type.
Engine blobs are kernel-trusted infrastructure: the safety scanner (Pass 2) explicitly
exempts them from the exec-forbidden pattern check. Syntax checking (Pass 1) still applies —
the engine must be valid Python. The reviewer's `authorized_types` includes `logic/engine`,
so engine blobs must be approved by a reviewer with explicit engine authority.

### Key insight

The workaround in f_13 was honest — it was named `_exec` and commented — but it was still
a workaround. f_14 names the distinction that was already real: engine blobs are not
arbitrary user code; they are kernel-trusted infrastructure with a different threat model.
The honest representation is an explicit type exemption, not a pattern that confuses the
scanner.

---

## f_15 — Engine Governance

**Council tag:** `v1.15.0`

### What was built

`evolve_engine()`: a governed upgrade path for the `logic/engine` blob. The cycle: ABI
structural check (verifies `invoke`, `record_feedback`, `_load_code`, `_CODE_CACHE` appear
in scope after exec — the ENGINE_ABI_CONTRACT is an inline constant, not a vault blob),
Triple-Pass Review, independent benchmark (execs both current and candidate engine with
isolated kernel scopes — no shared telemetry, no cross-contamination), council approval,
manifest update, engine cache invalidation. `evolve_engine()` is not part of `run_all()`;
engine upgrades require deliberate invocation.

Fixed a sync bug from f_13/f_14: `EVOLVE_REVIEWER_PAYLOAD` had `authorized_types:
["logic/python"]` while bootstrap had `["logic/python", "logic/engine"]`. Hash mismatch
caused approval failures. Fixed by keeping both in sync.

### Key insight

The engine blob is the execution substrate for everything else. If it breaks, the entire
fabric breaks. The ABI contract check is the first gate because an engine that doesn't
expose the right scope keys will fail in ways that look like arbitrary runtime errors. The
isolation requirement for the benchmark — separate `_LAST_TELEMETRY` dicts, separate kernel
scopes — ensures the benchmark measures the engines, not their interference with each other.

---

## f_16 — Multihash Address Format

**Council tag:** `v1.16.0`

### What was built

Blake3 vault addresses were bare 64-hex-char strings with no self-description. f_16
implemented ADR-015: the canonical address format is now `blake3:<hex>`. `_to_bare_hex()`
strips the prefix for filesystem operations (vault files are still stored at bare hex
paths — colons are not safe on all filesystems). `_to_multihash()` adds the prefix for
public API returns. Backward compat: bare hex addresses accepted everywhere, treated as
implicit `blake3:<address>`. The vault can contain both forms; callers that understand
multihash handle both.

`_verify_council_approval()` normalizes both sides to bare hex before set comparison —
required because the approval artifact may have been stored in one format while the current
code uses another.

### Key insight

An address that carries its own decoding instructions does not require external context to
verify. This matters for federation: two systems that meet for the first time can verify
each other's blobs using only the address itself. The prefix is the shared language. f_17's
remote vault and f_19's federation peers both depend on this property.

---

## f_17 — Remote Vault Tier

**Council tag:** `v1.17.0`

### What was built

Discovery gained an HTTP fetch tier. If a blob is not in L1 (local vault) or L2 (local
alternate vault), Discovery checks `context["vault_url_remote"]` and fetches from
`<url>/<bare_hex>`. Content-hash verification is non-negotiable: `blake3(fetched_bytes)`
must equal `bare_hex` before the blob is accepted. On verification success, the blob is
written to L1 and returned. On mismatch, `ValueError` is raised — the remote is untrusted
until its content matches the address. Uses stdlib `urllib.request` only; no new
dependencies.

### Key insight

The content-addressed identity invariant (address = hash of content) is what makes the
remote tier safe without trust in the remote. The address is the specification. You don't
need to trust the server — you need to verify that what came back matches the address you
already knew. This is the same property that makes IPFS work and the same property
ADR-015's multihash format was designed to enable.

---

## f_18 — Hash-Bridge Expression

**Council tag:** `v1.18.0`

### What was built

`meta/hash-bridge` blob type: links a vault address (blake3) to a ZK address (poseidon or
other circuit-friendly hash). The bridge record stores `vault_address`, `zk_address`, and
a `proof` slot (reserved for a ZK proof that both hash the same content; null until ZK
infrastructure is wired). `put_bridge(vault_addr, zk_addr, proof=None)` normalizes bare
hex to canonical form before storage. `resolve_bridge(address)` scans the vault for bridges
matching either address field. `promote_bridge(bridge_hash, approval_hash)` writes the
bridge into `manifest["bridges"]` under the canonical vault address. `lookup_bridge(addr)`
returns the bridge record from the manifest.

Triple-Pass Review validates bridge structure: `vault_address` must be present and
`blake3:<hex>` format; proof must be null or a non-empty string (whitespace-only rejected).

### Key insight

ZK circuits use Poseidon (~10x fewer constraints than blake3 in-circuit). The vault uses
blake3 (fast, general-purpose). These hash functions serve different masters. The
hash-bridge makes the relationship between a vault blob and its ZK representation explicit,
auditable, and governed. The bridge is itself a vault blob with a blake3 address — governed
by the same review chain as everything else.

---

## f_19 — Federation

**Council tag:** `v1.19.0`

### What was built

Cross-vault blob resolution. `register_peer(url)` adds a federation peer URL to
`manifest["federation"]["peers"]` (idempotent). `list_peers()` and `remove_peer(url)` manage
the peer list. Both operations write to the audit log.

DISCOVERY_V9: extends V8 with a federation peers tier. After L1, L2, and the single
`vault_url_remote`, Discovery iterates over `context["vault_federation_peers"]` in order.
Each peer attempt: fetch `<peer_url>/<bare_hex>`, verify blake3 hash, cache to L1 on
success. On `URLError`, try the next peer. If all peers fail, `FileNotFoundError`. The
single `vault_url_remote` is preserved for backward compatibility with f_17.

### Key insight

Federation is not trust. Content-addressed verification applies to every peer response —
you accept a blob from a federation peer only after its hash matches the address you were
looking for. The peers are untrusted sources of content; the address is the trust anchor.
This is the same invariant as f_17's remote tier, extended to N peers.

---

## f_20 — Capability Registry

**Council tag:** `v1.20.0`

### What was built

The fabric becomes self-describing. `register_capability(label, description, tags)` stores
human-readable metadata in `manifest["capabilities"][label]`. `list_capabilities()` returns
all registered capabilities sorted by label, with `current_hash` resolved live from
`manifest["blobs"]`. `get_capability(label)` returns a single record or None. Both list and
get operations always reflect the current promoted blob — the registry is a view over the
manifest, not a separate store.

Bootstrap registers the three infrastructure labels (discovery, planning, telemetry-reader)
as capabilities with descriptions and tags during genesis. `LIST_CAPABILITIES_V1` is a
`logic/python` blob that takes `context["capabilities"]` and `context["blobs"]` and returns
a sorted list of capability records — the registry is queryable through the same invocation
machinery as everything else. `run_all()` bootstraps the `list-capabilities` label if
absent, registers it as a capability, then evolves it with the rest of the fabric. After
f_20, the first blob a new consumer should invoke is `list-capabilities`.

### Key insight

The fabric can now answer "what can I do?" through the same mechanism it uses to do anything.
`list-capabilities` is not a special API endpoint or a privileged introspection method —
it is a governed, content-addressed blob in the vault, promoted through Triple-Pass Review
and Council Approval, evolved by the same cycle that evolves discovery and planning. The
fabric's self-model is subject to the same governance as the rest of the fabric. This is
invariant V (governance) applied to the governance registry itself.

---

## Current State — f_20 Baseline

As of f_20, the fabric operates as follows per evolve cycle:

1. Bootstrap on first run: trust root reviewer → evolve reviewer → engine blob →
   discovery, planning, telemetry-reader blobs and contracts → capabilities registered
2. `run_all()` discovers all labels in `manifest["blobs"]`, bootstraps `list-capabilities`
   if absent, evolves all logic/python labels
3. Per label: derive mutation goal from audit log trends + OKR key results (if promoted) →
   generate 3 candidates (gemini-flash) → Triple-Pass Review + adversarial test suite
   (devstral) → benchmark N=25 rounds → promote best winner through Council Approval
4. Resolution path per blob lookup: L1 vault → L2 vault → remote URL → federation peers
   (each with content-hash verification before acceptance)
5. Hash-bridges link vault (blake3) addresses to ZK (poseidon) addresses for any blob
   with a ZK representation; bridges are vault blobs governed by the same chain
6. Every promotion, peer registration, capability registration, and bridge promotion is
   recorded in the append-only audit log and traceable through the reviewer chain to the
   trust root

What the human provides: behavioral contracts (what blobs must do), OKRs (what success
looks like), reviewer trust weights, and federation peer URLs. Everything else — candidate
generation, adversarial testing, benchmarking, promotion, evolution — is autonomous.

The fabric governs its own operation, evolves its own blobs, describes its own capabilities,
and resolves content across federated vaults. The trust root is a content-addressed blob
in the vault. The governance chain is an immutable content-addressed record. The audit log
is an append-only JSONL file. The manifest is a self-sealing hash of its own content.
Nothing is outside the accounting.
