# D-JIT Logic Fabric

**D-JIT** (Distributed Just-In-Time) Logic Fabric is a content-addressed compute mesh. It
treats code, data, and inference as immutable Blobs — and applies itself to itself to discover
and promote improvements through measured iteration.

*Why "D-JIT"?* Traditional [JIT compilation](https://en.wikipedia.org/wiki/Just-in-time_compilation)
compiles code at runtime rather than ahead of time. This fabric is distributed (blobs live in
a content-addressed vault, not in memory) and just-in-time (a blob is compiled and executed
on first invocation, then cached). The "D" matters: any node with vault access can invoke any
blob by hash — the hash is both the address and the integrity proof.

Branch: [`council/f_2`](https://github.com/BrianLN-AI/synapse/tree/council/f_2) —
latest tag: [`v1.2.0`](https://github.com/BrianLN-AI/synapse/tree/v1.2.0)
([`9c7fb35`](https://github.com/BrianLN-AI/synapse/commit/9c7fb359a81231e3d091a5ece55a7662cdd42052))

---

## The Core Idea

Every unit of compute is a **Blob**: an immutable, content-addressed payload stored by its
[SHA-256](https://en.wikipedia.org/wiki/SHA-2) hash (a 64-character hex fingerprint that
uniquely identifies the content). Blobs are invoked, not loaded. They execute in a scrubbed
scope with only two inputs — `context` (a dict of caller-provided values) and `log` (a
callable for structured output) — and must produce exactly one output: the `result` variable.
Nothing else crosses the boundary.

*Why content-addressed?* If the hash matches, the content is identical — deduplication is
free, caching is trivially correct, and no blob can be silently modified. The hash is the
contract. Storing blobs by hash also means a distributed vault is structurally natural: the
address works the same whether the vault is local or remote.

*Why scrubbed scope?* Blobs cannot see or manipulate linker internals. This prevents
privilege escalation (a blob cannot reach up into the engine that runs it) and makes
behaviour fully deterministic from inputs. The only way a blob can affect the outside world
is through its `result`. Side effects are structurally impossible.

*Why a `result` variable?* Explicit output makes ABI (**Application Binary Interface** — the
contract between a blob and the runtime) violations detectable at the engine level. If a blob
runs without setting `result`, the engine raises an error before the caller ever sees a
response. There is no silent failure.

This ABI contract is not a convention. It is enforced at every invocation.

The fabric is self-hosting: the functions that discover, plan, and measure blobs are themselves
blobs. When the fabric improves, it does so by running its own evaluation cycle, promoting
better versions of its own core logic, and updating the manifest that future invocations will
read. It applies itself to itself.

---

## Layer Stack

```
Interface
    ↓
Discovery  (The Librarian)  — resolves a content hash to a blob envelope
    ↓
Planning   (The Broker)     — selects the best candidate by fitness score
    ↓
Binding    (The Engine)     — executes the blob with ABI enforcement + telemetry
```

The four layers are not hardcoded. Each layer (except the BIOS bootstrap root) is itself a
blob in the vault and is looked up by hash at runtime. When a better version of Discovery is
promoted, the next invocation uses it automatically — no redeploy, no restart.

*Why separate Discovery from Binding?* Discovery validates that a hash exists and returns
the envelope before Binding executes it. This separation means the engine never executes an
unverified blob, and Discovery can be swapped for a distributed or cached version without
touching the execution engine.

Every invocation generates a `telemetry/artifact` blob — latency, memory, outcome, log
lines — stored in the same vault. The telemetry reader aggregates this into fitness signals.
The planner reads those signals. The loop is closed: every past run informs every future
selection.

---

## Fitness Function

The planner scores candidates using:

```
f(Link) = SuccessRate × Integrity / (Latency × ComputeCost)
```

- **SuccessRate**: fraction of past invocations that completed without error
- **Integrity**: recency-weighted success streak — recent consecutive clean runs count more
  than an old perfect record (see [f_2](#f_2--tail-latency-awareness-v120) below)
- **Latency**: the p95 latency when available, falling back to average
  ([p95](https://en.wikipedia.org/wiki/Percentile) = the latency that 95% of invocations fall
  under; captures tail behaviour that averages hide)
- **ComputeCost**: proxy for memory usage (peak KB from
  [tracemalloc](https://docs.python.org/3/library/tracemalloc.html))

*Why p95 instead of average?* A blob might average 2 ms but spike to 200 ms on 5% of calls.
The average looks fine; the tail behaviour is catastrophic for callers that need reliability.
p95 catches spikes that averages hide.

*Why Bayesian smoothing?* New blobs have no history. Without smoothing, a blob with one
perfect run (100% success rate) would score identically to one with 1,000 clean runs — the
fabric could not distinguish genuine reliability from luck. [Bayesian smoothing](https://en.wikipedia.org/wiki/Additive_smoothing)
blends observed values toward a prior (neutral default) until enough data accumulates.
Blobs with fewer than 5 invocations (`MIN_SAMPLES`) are smoothed toward a success rate of
0.95 and a latency of 1.0 ms.

---

## The Journey

### f(undefined) — The Spec

Before a line ran, there was a spec: [`f(undefined).md`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/f%28undefined%29.md).
It described a fabric where blobs could discover, plan, and bind other blobs — and where the
fitness function would govern selection without a scheduler or orchestrator. The council spec
([`COUNCIL.md`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/COUNCIL.md)) defined
a peer-review layer: Triple-Pass Review (StaticAnalysis → SafetyVerification →
ProtocolCompliance) and Council Approval before any promotion could happen.

**GOKR** (Goal, Objective, Key Results — a planning framework for stating *what* we want
and *how we know we got there*) pointed at one thing: a closed feedback loop where measured
performance informs arbitration. That was the condition for calling f_0 done.

*Why Triple-Pass Review?* Blobs are executed code, not configuration. An unchecked promotion
could introduce syntax errors, dangerous patterns (`exec`, `import os`, `open` for writing),
or ABI violations that break the fabric. Three passes catch three distinct failure classes:
syntax, safety, and protocol. They run before any blob reaches the manifest.

*Why Council Approval?* Promotion is recorded in an auditable manifest. Requiring a
`council/approval` blob — a content-addressed artifact recording who approved what and when —
creates a chain of custody. Every manifest entry traces back to an approval.

### f_0 — Close the Loop (v1.0.0)

Tag [`v1.0.0`](https://github.com/BrianLN-AI/synapse/tree/v1.0.0) —
commit [`c31f394`](https://github.com/BrianLN-AI/synapse/commit/c31f394c00a8438cf8a60af0fab91f08763b411c)
— branch [`council/f_0`](https://github.com/BrianLN-AI/synapse/tree/council/f_0)

Four files built from scratch:

- **`seed.py`** — **BIOS** (Basic Input/Output System) Seed: the lowest-level bootstrap root.
  `put()` stores blobs by hash; `invoke()` executes them with ABI enforcement and telemetry.
  `seed.py` reads directly from the filesystem via `_raw_get()` and never delegates to
  Discovery. *Why?* If Discovery is not yet in the manifest, invoking it through the normal
  path would call Discovery → call Discovery → infinite recursion. `_raw_get()` cuts the loop
  at the root.

- **`promote.py`** — Triple-Pass Review, Council Approval issuance, and manifest promotion.
  The manifest (`manifest.json`) records which blob hash is canonical for each named role
  (discovery, planning, telemetry-reader). `audit.log` records every promotion as an
  append-only JSONL line.

- **`linker.py`** — Full layer stack: resolve → arbitrate (with telemetry enrichment) → bind.
  `arbitrate()` reads live telemetry before scoring, so every past invocation informs future
  candidate selection.

- **`bootstrap.py`** — Seeds the fabric by promoting Discovery, Planning, and Telemetry-Reader
  v1 blobs through Triple-Pass Review and writing the initial manifest at v1.0.0.

f_0 closed when `linker.arbitrate()` read live telemetry to enrich candidates before scoring
and the manifest recorded which blobs were canonical. The feedback loop existed.

**What f_0 did not know:** its own evolution engine had a hidden performance tax.

### f_1 — The Engine Finds Itself (v1.1.0)

Tag [`v1.1.0`](https://github.com/BrianLN-AI/synapse/tree/v1.1.0) —
commit [`cf6ddd4`](https://github.com/BrianLN-AI/synapse/commit/cf6ddd41587a22e0a03d3892e73bd3bf3fd9f98b)
— branch [`council/f_1`](https://github.com/BrianLN-AI/synapse/tree/council/f_1)

f_1 was `f_0(f_0)` — the fabric running its own evaluation cycle (`evolve.py`) against its
own core blobs.

The v2 candidate blobs were genuinely better:
- **EAFP** ([Easier to Ask Forgiveness than Permission](https://docs.python.org/3/glossary.html#term-EAFP))
  Discovery: try reading the blob directly; catch `FileNotFoundError` on miss. v1 called
  `Path.exists()` before reading — two filesystem calls on every hit. v2 calls `read_text()`
  directly — one call on hit, two only on miss. *Why does this matter?* Discovery is on the
  hot path for every invocation. Halving the filesystem calls on L1 hits (the common case)
  compounds across the lifetime of the vault.
- **Bayesian cold-start smoothing** in the planner (see [Fitness Function](#fitness-function)
  above).
- **[Welford online algorithm](https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford's_online_algorithm)**
  in the telemetry reader for p95 approximation. *Why Welford?* Storing all latency values
  to compute p95 exactly would grow the stats structure with every invocation — unbounded
  memory. Welford computes running mean and variance in O(1) space with a single pass, so
  p95 (approximated as mean + 1.645σ, the [standard normal](https://en.wikipedia.org/wiki/Standard_normal_table)
  quantile for 95%) can be computed from any number of invocations without ever storing them.

But the benchmark kept showing v2 **losing** to v1. The measured fitness was wrong.

Root cause: Python's `exec()` recompiles source text on every call. Longer v2 blobs paid a
per-call compilation tax that masked their true runtime performance. The benchmarking was
measuring compilation overhead, not blob logic.

f_1 fixed this by adding `_CODE_CACHE` to `seed.py`: [`compile()`](https://docs.python.org/3/library/functions.html#compile)
once per blob hash, reuse the code object. After the fix, v2 blobs won clearly.
**f_1 did not have a compile cache before it ran. It found the need for one by measuring.**

Promoted: Discovery v2, Planning v2, Telemetry-Reader v2. Manifest: v1.1.0.

### f_2 — Tail-Latency Awareness (v1.2.0)

Tag [`v1.2.0`](https://github.com/BrianLN-AI/synapse/tree/v1.2.0) —
commit [`9c7fb35`](https://github.com/BrianLN-AI/synapse/commit/9c7fb359a81231e3d091a5ece55a7662cdd42052)
— branch [`council/f_2`](https://github.com/BrianLN-AI/synapse/tree/council/f_2)

f_2 was `f_1(f_1)`. The p95 signal existed in telemetry-reader v2 but was not flowing
through the full signal path: `linker.arbitrate()` did not forward it to Planning, and
Planning did not use it in the fitness function. A blob with a fast average but high variance
would look good even if it spiked unpredictably.

Three changes closed this gap:

- **`linker.py`**: forward `p95_latency_ms` and `integrity` from telemetry to every enriched
  candidate. Unknown blobs (no telemetry history) default to `integrity = 0.5`. *Why 0.5?*
  The streak-weighting math means even a blob with 10 consecutive clean runs achieves
  integrity ≈ 0.80 (the first 4 invocations pre-date the 2× weighting). If unknown blobs
  defaulted to 1.0 (perfect), every proven blob would lose to any unknown challenger.
  `0.5` expresses genuine uncertainty — "we don't know yet."

- **`PLANNING_V3`**: use `p95_latency_ms` as the latency input when available, falling back
  to average. Bursty candidates are penalised even when their average looks acceptable.

- **`TELEMETRY_READER_V3`**: add an integrity signal — consecutive-success streak weighted
  2× after position 4. *Why position 4?* A streak of 1–4 is a short run; 5+ is a sustained
  pattern. The 2× multiplier rewards blobs that have been reliably clean for an extended
  period, not just blobs that happened to pass once. Still O(1) memory via Welford; no stored
  invocation list.

**f_2 also surfaced a subtle design issue:** the integrity default needed to reflect
uncertainty, not optimism. This was found by writing the test: a candidate with 10 clean runs
was losing to an unknown challenger because the unknown's default (1.0) beat the measured
value (0.80). The fix was a design correction, not a bug patch.

Promoted: Discovery v3, Planning v3, Telemetry-Reader v3. Manifest: v1.2.0.
Planning v3 fitness: ~2× improvement over v2.

---

## What the f(n) Model Actually Means

f_0, f_1, f_2 are not version numbers with a changelog. They are **fixed-point iterations**.

Each f_n applies the current fabric to itself, observing what measurement reveals, and
promoting the version that performs better under those conditions. The fabric does not improve
because the authors wrote better code. It improves because it ran, measured, found a gap,
and promoted the blob that addressed it.

f_1 did not have a compile cache before it ran. f_2 did not use p95 in arbitration before
it ran. Both gaps were found by the fabric measuring itself.

The question every iteration asks: *what does the telemetry reveal that the current
architecture is not seeing?*

---

## Files

| File | Role |
|------|------|
| [`seed.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/seed.py) | BIOS Seed — `put()`, `invoke()`, compile cache, telemetry recording |
| [`promote.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/promote.py) | Triple-Pass Review, Council Approval, manifest promotion |
| [`linker.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/linker.py) | Layer stack — resolve, arbitrate (with telemetry enrichment), bind |
| [`bootstrap.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/bootstrap.py) | f_0 bootstrap — promotes v1 blobs, writes manifest v1.0.0 |
| [`evolve.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/evolve.py) | Self-modification engine — evaluate → mutate → review → benchmark → promote |
| [`tests/test_fabric.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/tests/test_fabric.py) | Phase 1+2 tests (seed, promote) |
| [`tests/test_phase3.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/tests/test_phase3.py) | Phase 3 tests (linker, feedback loop, manifest v1.0.0) |
| [`tests/test_f1.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/tests/test_f1.py) | f_1 tests (compile cache, Bayesian math, v2 correctness) |
| [`tests/test_f2.py`](https://github.com/BrianLN-AI/synapse/blob/council/f_2/tests/test_f2.py) | f_2 tests (p95 path, integrity signal, v3 correctness, manifest v1.2.0) |

Runtime artifacts (`blob_vault/`, `manifest.json`, `audit.log`) are git-ignored. They are
produced by running the fabric, not committed with it. Each run starts fresh.

---

## Running

```bash
# Bootstrap f_0 (promotes v1 blobs, writes manifest v1.0.0)
python bootstrap.py

# Run the self-modification cycle (evaluate → mutate → review → benchmark → promote v3 blobs)
python evolve.py

# Invoke a blob directly through the full layer stack
python linker.py invoke <hash> --context '{"x": 1}'

# Dump aggregated telemetry fitness signals for all blobs in the vault
python linker.py telemetry

# Run tests (wipes vault and manifest first for clean state)
python tests/test_f2.py
```

---

## What Might Come Next

The fabric can now observe its own tail-latency and reward candidates that are consistently
fast, not just fast on average. Three directions the next iteration might surface:

**f_3 — ABI Evolution.** The current ABI is `context in, result out`. Blobs that run long
computations block the caller; there is no streaming, no checkpoint, no partial result. f_3
could benchmark whether any blob would benefit from a generator-style ABI (`yield` instead of
`result =`) and promote a new execution model if the telemetry supports it. The key question:
does measured throughput improve enough to justify the ABI complexity increase?

**f_3 — Distribution.** The vault is a local directory. Blobs are content-addressed, which
means a distributed vault is structurally natural — the hash works as an address anywhere.
The next iteration could benchmark local vs. remote blob resolution via an L1/L2 cache
split (L1 = local fast tier, L2 = remote or slower tier) and promote a Discovery blob that
knows how to span both tiers transparently.

**f_3 — Self-Evaluation of Review.** The Triple-Pass Review is static: syntax check, safety
regex, ABI dry-run. It can determine whether a blob is *valid*, but not whether it is *better*.
A fourth pass that runs the candidate against a held-out benchmark suite and gates promotion
on measured regression would close that gap. The fabric could then evaluate its own review
criteria, not just its own runtime performance.

In each case, the model is the same: run, measure, find what the telemetry reveals, promote
what addresses it.

---

## Tag History

| Tag | Manifest | Commit | What it Marks |
|-----|----------|--------|---------------|
| [`v1.0.0`](https://github.com/BrianLN-AI/synapse/tree/v1.0.0) | 1.0.0 | [`c31f394`](https://github.com/BrianLN-AI/synapse/commit/c31f394c00a8438cf8a60af0fab91f08763b411c) | f_0 — feedback loop closed; v1 blobs in manifest |
| [`v1.1.0`](https://github.com/BrianLN-AI/synapse/tree/v1.1.0) | 1.1.0 | [`cf6ddd4`](https://github.com/BrianLN-AI/synapse/commit/cf6ddd41587a22e0a03d3892e73bd3bf3fd9f98b) | f_1 — compile cache found; v2 blobs promoted |
| [`v1.2.0`](https://github.com/BrianLN-AI/synapse/tree/v1.2.0) | 1.2.0 | [`9c7fb35`](https://github.com/BrianLN-AI/synapse/commit/9c7fb359a81231e3d091a5ece55a7662cdd42052) | f_2 — p95 + integrity wired end-to-end; v3 blobs promoted |
