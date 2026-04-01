# D-JIT Logic Fabric

A content-addressed compute mesh that treats code, data, and inference as immutable Blobs —
and applies itself to itself to discover and promote improvements through measured iteration.

---

## The Core Idea

Every unit of compute is a **Blob**: an immutable, content-addressed payload stored by its
SHA-256 hash. Blobs are invoked, not loaded. They execute in a scrubbed scope with only two
inputs — `context` (dict) and `log` (callable) — and must produce exactly one output:
the `result` variable. Nothing else crosses the boundary.

This is the ABI. It is not a convention; it is enforced at every invocation.

The fabric is self-hosting: the functions that discover, plan, and measure blobs are themselves
blobs. When the fabric improves, it does so by running its own evaluation cycle, promoting
better versions of its own core logic, and updating the manifest that future invocations
will read. It applies itself to itself.

---

## Layer Stack

```
Interface
    ↓
Discovery  (The Librarian)  — resolves a content hash to a blob envelope
    ↓
Planning   (The Broker)     — selects the best candidate by fitness
    ↓
Binding    (The Engine)     — executes the blob with ABI enforcement + telemetry
```

Every invocation generates a `telemetry/artifact` blob — latency, memory, outcome, log lines —
stored in the same vault. The telemetry reader aggregates this into fitness signals. The
planner reads those signals. The loop is closed: every past run informs every future selection.

---

## The Journey

### f(undefined) — The Spec

Before a line ran, there was a spec: `f(undefined).md`. It described a fabric where blobs
could discover, plan, and bind other blobs — and where the fitness function would govern
selection without a scheduler or orchestrator. The council spec (`COUNCIL.md`) defined a
peer-review layer: Triple-Pass Review (StaticAnalysis → SafetyVerification → ProtocolCompliance)
and Council Approval before any promotion.

The GOKR (Goal, Objective, Key Results) pointed at one thing: a closed feedback loop where
measured performance informs arbitration. That was the condition for calling f_0 done.

### f_0 — Close the Loop (v1.0.0)

Three layers built from scratch:

- `seed.py` — BIOS Seed: `put()` + `invoke()` + telemetry recording. The bootstrap root.
  Reads directly from the filesystem, never delegates to Discovery. Prevents infinite recursion.
- `promote.py` — Triple-Pass Review + Council Approval + manifest promotion.
- `linker.py` — Full layer stack: resolve → arbitrate → bind. Telemetry enrichment in `arbitrate()`.
- `bootstrap.py` — Promotes Discovery, Planning, and Telemetry-Reader v1 blobs to the manifest.

f_0 closed when: `linker.arbitrate()` read live telemetry to enrich candidates before scoring,
and the manifest recorded which blobs were canonical. The feedback loop existed.

**What f_0 did not know:** its own evolution engine had a hidden tax.

### f_1 — The Engine Finds Itself (v1.1.0)

f_1 was `f_0(f_0)` — the fabric running its own evaluation cycle against its own core blobs.

The evolution engine benchmarked v1 blobs against v2 candidates. v2 candidates were genuinely
better — EAFP discovery (one syscall on L1 hit instead of two), Bayesian cold-start smoothing
in the planner, Welford online variance for p95 approximation in the telemetry reader.

But the benchmark kept showing v2 losing to v1. The measured fitness was wrong.

Root cause: `exec()` recompiles source on every call. Longer v2 blobs paid a per-call
compilation tax that masked their true runtime performance. The benchmarking was measuring
compilation overhead, not blob logic.

f_1 fixed this by adding `_CODE_CACHE` to `seed.py`: `compile()` once per blob hash, reuse
the code object. After the fix, v2 blobs won clearly. **f_1 did not have a compile cache
before it ran. It found the need for one by measuring.**

Promoted: Discovery v2, Planning v2 (Bayesian), Telemetry-Reader v2 (Welford p95).
Manifest: v1.1.0.

### f_2 — Tail-Latency Awareness (v1.2.0)

f_2 was `f_1(f_1)`. The p95 signal existed in telemetry-reader v2 but was not flowing through
the full signal path: `linker.arbitrate()` did not forward it to Planning, and Planning did
not use it in the fitness function. A blob with a fast average but high variance would look
good even if it spiked unpredictably.

Three changes closed this gap:

- `linker.py`: forward `p95_latency_ms` and `integrity` from telemetry to every enriched candidate.
  Unknown blobs default to integrity=0.5 — uncertainty is not the same as trustworthiness.
- `PLANNING_V3`: use `p95_latency_ms` as the latency input when available. Bursty candidates
  are penalised even when their average looks acceptable.
- `TELEMETRY_READER_V3`: add an integrity signal — a Welford-based consecutive-success streak
  score, weighted 2× after position 4. A blob that was flaky but recently fixed earns less
  integrity than one with a steady clean record. O(1) memory, no stored invocation list.

f_2 also surfaced a subtle design issue in the integrity default: the first 4 invocations of
any blob can never be post-streak, so a blob with 10 clean runs achieves integrity ≈ 0.80,
not 1.0. The default for unknown blobs needed to be 0.5 (uncertain), not 1.0 (perfect) — or
the well-proven blob would lose to the unknown one.

Promoted: Discovery v3, Planning v3, Telemetry-Reader v3.
Manifest: v1.2.0. Planning v3 fitness: ~2× improvement over v2.

---

## What the f(n) Model Actually Means

f_0, f_1, f_2 are not version numbers with a changelog. They are fixed-point iterations.

Each f_n applies the current fabric to itself, observing what the measurement reveals, and
promoting the version of the fabric that performs better under those conditions. The fabric
does not improve because we wrote better code in f_2 than in f_0. It improves because it
ran, measured, found a gap, and promoted the blob that addressed it.

f_1 did not have a compile cache before it ran. f_2 did not use p95 in arbitration before
it ran. Both gaps were found by the fabric measuring itself, not by the authors reasoning
about the design.

The question the model asks at every iteration: *what does the telemetry reveal that the
current architecture is not seeing?*

---

## Files

| File | Role |
|------|------|
| `seed.py` | BIOS Seed — `put()`, `invoke()`, compile cache, telemetry recording |
| `promote.py` | Triple-Pass Review, Council Approval, manifest promotion |
| `linker.py` | Layer stack — resolve, arbitrate (with enrichment), bind |
| `bootstrap.py` | f_0 bootstrap — promotes v1 blobs, defines manifest v1.0.0 |
| `evolve.py` | Self-modification engine — evaluate → mutate → review → benchmark → promote |
| `tests/test_fabric.py` | Phase 1+2 tests (seed, promote) |
| `tests/test_phase3.py` | Phase 3 tests (linker, feedback loop, manifest v1.0.0) |
| `tests/test_f1.py` | f_1 tests (compile cache, Bayesian math, v2 correctness) |
| `tests/test_f2.py` | f_2 tests (p95 path, integrity signal, v3 correctness, manifest v1.2.0) |

Runtime artifacts (`blob_vault/`, `manifest.json`, `audit.log`) are git-ignored. They are
produced by running the fabric, not committed with it.

---

## Running

```bash
# Bootstrap f_0 (promotes v1 blobs, writes manifest v1.0.0)
python bootstrap.py

# Run the f_2 evolution cycle (evaluate → mutate → review → benchmark → promote)
python evolve.py

# Invoke a blob directly
python linker.py invoke <hash> --context '{"x": 1}'

# Dump telemetry fitness signals
python linker.py telemetry

# Run tests (requires clean state — test script wipes vault and manifest)
python tests/test_f2.py
```

---

## What Might Come Next

The fabric can now observe its own tail-latency and reward candidates that are consistently
fast, not just fast on average. Three directions the next iteration might surface:

**f_3 — ABI Evolution.** The current ABI is `context in, result out`. Blobs that run long
computations block; there is no streaming, no checkpoint, no partial result. f_3 could
benchmark whether any blob would benefit from a generator-style ABI (yield instead of
assign) and promote a new execution model if the telemetry supports it.

**f_3 — Distribution.** The vault is a local directory. Blobs are content-addressed, which
means a distributed vault is structurally natural — the hash is the address. The next
iteration could benchmark local vs. remote blob resolution and promote a Discovery blob
that knows how to span both tiers.

**f_3 — Self-Evaluation of Review.** The Triple-Pass Review is static: syntax check, safety
regex, ABI dry-run. It cannot evaluate whether a blob is *better* — only whether it is
*valid*. A fourth pass that runs the candidate against a held-out benchmark suite and
gates promotion on measured regression would close that gap. The fabric could then evaluate
its own review criteria, not just its own performance.

In each case, the model is the same: run, measure, find what the telemetry reveals, promote
what addresses it.

---

## Tags

| Tag | Manifest Version | What it Marks |
|-----|-----------------|---------------|
| `v1.0.0` | 1.0.0 | f_0 — feedback loop closed |
| `v1.1.0` | 1.1.0 | f_1 — compile cache found; v2 blobs promoted |
| `v1.2.0` | 1.2.0 | f_2 — p95 + integrity wired end-to-end; v3 blobs promoted |
