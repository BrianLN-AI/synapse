# Architect's Review: Extend f_6 vs. Fresh ZK-First Collapse

**Reviewer role:** The Architect — reads for load-bearing vs. accidental structure  
**Corpus read:** seed.py, promote.py, evolve.py (f_6 worktree)  
**Question:** SHA256 → blake3 migration: retrofit or deeper? Extend or restart?

---

## Foundational Elements (load-bearing)

These are the things you cannot change without changing what the system *is*.

**1. Content-addressed identity**

The vault is a content-addressed store. A blob's hash IS its identity. This is not a storage detail — it is the entire basis on which the governance chain (promote.py) can make tamper-evident claims. If you change what is hashed, or how, you change the identity of every existing blob. This principle is non-negotiable regardless of which hash function you use.

**2. The envelope structure as the unit of identity**

`seed.put()` hashes the full JSON envelope (`{"type": ..., "payload": ...}`, sorted keys), not the raw payload. This means blob type is part of the content address. A `logic/python` blob with payload X and a `telemetry/artifact` blob with the same payload X have different hashes. That is load-bearing: the governance passes rely on type being unforgeable via the hash. Changing the envelope format would orphan all existing vault entries.

**3. The scrubbed-scope ABI**

`invoke()` executes blobs in a scope containing only `context` and `log`. This is not a safety nicety — it is what makes blobs auditable units. The Triple-Pass Review's safety scan (Pass 2) and the ABI enforcement (Pass 3) only make sense in a world where the scope boundary is real. The ABI contract (`result` variable must be set) is the interface between the engine and any blob. Everything downstream — benchmarking, fitness signals, the evolution loop — depends on this contract holding.

**4. The governance chain as a trust lattice**

The promote.py architecture establishes a proper lattice: bootstrap reviewer → promoted reviewers → council/approval artifacts → blob promotions. The manifest hash seals each state transition. Critically, `_write_manifest()` strips the old hash before hashing — the manifest's hash is always over its content, not over a prior hash. This means you can verify any manifest state in isolation. Tampering with any link in the chain produces a detectable inconsistency. This structure is foundational: it is what separates this from a mutable config file.

**5. Telemetry as blobs**

Every invocation produces a `telemetry/artifact` blob stored in the same vault. This means the fitness signal and the logic blobs live in the same address space, are subject to the same governance, and are equally retrievable by hash. The telemetry reader is itself a promotable blob reading other blobs. If telemetry were stored externally (a database, a log file), this recursive structure would break — the evolve engine would need privileged access to a second system.

**6. The self-modification loop structure**

evolve.py's cycle (evaluate → mutate → triple-pass → benchmark → promote) is not an accident of implementation. It is the operational expression of what f_n means: the system applies its own governance machinery to its own candidates. The evolve-engine reviewer is itself a promoted council/reviewer blob. The system eating its own tail is foundational — it is what makes the evolution governed rather than arbitrary.

---

## Accidental Elements (retrofit-able)

These can change without touching system identity.

**1. Python as the implementation language**

seed.py, promote.py, evolve.py are Python. The blob payloads are also Python (executed via `exec`). The language of the engine is accidental — the architecture could be implemented in any language that provides an exec-equivalent with scope isolation. The blob execution language is slightly more sticky (blobs in the vault are Python bytecode-cacheable), but the vault itself is language-agnostic JSON envelopes.

**2. SHA256 as the hash function**

Despite appearing in two places, SHA256 is a choice, not a structural commitment (see next section for the caveat). The vault is a flat directory of files named by hash. Switching to blake3 would require: (a) recomputing hashes for any existing blobs you want to carry forward, (b) updating seed.put() and promote._write_manifest(), (c) updating the hash-length guard in discovery blobs (still 64 hex chars for both sha256 and blake3-256). The manifest's hash-of-state would also need migration. These are real migration costs, but none of them change what the system does.

**3. The filesystem as the vault backend**

`VAULT_DIR` is a directory on disk. `_raw_get()` reads files by filename. This is an implementation detail. The vault interface — get(hash) → envelope, put(type, payload) → hash — could be backed by S3, a content-addressed object store, or a local database. The 64-char hex filename convention is the only coupling point.

**4. The benchmark parameters (BENCHMARK_ROUNDS, tolerance derivation)**

`_derive_tolerance()` reads the audit log to set promotion thresholds dynamically. The specific formula (25th percentile of observed improvements, 0.30 fallback) is a tunable heuristic. The mechanism — data-derived tolerance rather than hand-tuned constants — is worth keeping, but the specific formula is not load-bearing.

**5. The blob payload evolution history (v2–v7 payloads)**

The versioned payloads in evolve.py (DISCOVERY_V2 through V7, PLANNING_V2 through V7, TELEMETRY_READER_V2 through V7) are candidates for the current iteration. They are the current mutation set. In a fresh start, you would define different initial candidates. The existence of six prior versions is historical record, not architecture.

**6. The in-process bytecode cache (BYTECODE_DIR)**

`_load_code()` caches compiled Python code objects to disk. This is a performance optimization layered on top of the content-addressed store. It is correct (immutable blobs can never produce stale bytecode), useful, and entirely removable without breaking any guarantee.

---

## The Hash Migration: Retrofit or Deeper?

The surface answer is: retrofit. SHA256 appears in exactly two sites. Changing both is mechanical. But the ZK constraint reveals a deeper issue.

**The binding problem**

The ZK circuit proves `blake3(blob_content) == blob_hash`. "blob_content" here is ambiguous. What the circuit is binding to is the raw content of the blob — presumably the payload bytes, or the envelope bytes, or something the circuit can witness. But in f_6, what gets hashed is the JSON-serialized envelope with sorted keys:

```python
envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
content_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
```

The circuit must witness exactly this byte string: the UTF-8 encoding of a specific JSON serialization. JSON serialization is non-canonical. Python's `json.dumps(sort_keys=True)` is deterministic within CPython, but "sorted keys" is not a ZK-friendly input format. The circuit would need to prove correctness of JSON serialization rules, not just hash preimage knowledge.

**What this actually requires**

A ZK-first system would not hash a JSON envelope. It would hash a canonical binary encoding — probably a fixed-width struct or a length-prefixed schema (protobuf, CBOR, or a custom schema). The "type" field would be an integer or a fixed-length field, not an arbitrary string. The payload would be length-prefixed. The circuit witnesses the preimage directly.

If you retrofit ZK proofs onto the current f_6 envelope format, you are asking circuits to prove properties of JSON serialization. That is not impossible, but it is expensive (JSON whitespace and quote handling in a circuit is overhead that serves nothing), and it couples your proof system to Python's json.dumps behavior.

**The deeper assumption exposed**

f_6 assumes the vault is a trusted local filesystem. `_raw_get()` reads files and returns their content. There is no verification that the file on disk matches what was originally stored. A ZK proof of content binding is only meaningful if there is an untrusted party who might tamper — if the vault can be remote, distributed, or adversarial. f_6 has no model of an untrusted vault. Adding ZK without adding that threat model produces proofs that prove nothing useful.

**Verdict on the retrofit**

Swapping SHA256 for blake3 at the two call sites: retrofit, minor, mechanical.

Swapping the envelope format from JSON to a canonical binary encoding to make ZK circuits tractable: structural change. Every existing vault entry is orphaned. The hash-length guard in the discovery blobs (hardcoded 64-char check) happens to be the same for both sha256 and blake3-256, but the validation logic would need to match the new canonical encoding's output format.

Introducing a threat model where the vault is untrusted and proofs are verified by an external verifier: not retrofit. That changes what `_raw_get()` means — it can no longer be the BIOS-level bootstrap root that unconditionally trusts the filesystem.

---

## What ZK-First Would Change

Concrete things that would be designed differently if ZK proofs were first-class from the start, not bolted on.

**1. Canonical binary envelope format, not JSON**

The blob envelope would be a fixed-schema binary format (CBOR or a custom schema). Type would be an enum integer. Payload would be length-prefixed bytes. The hash would be `blake3(canonical_bytes)`. Circuits witness the canonical bytes directly. No JSON serialization rules in the proof path.

**2. The vault would have an explicit trust model**

`_raw_get()` would not be "read from disk, trust the result." The vault interface would include a proof alongside each blob: `get(hash) → (envelope, proof)`. The proof is verified before the envelope is used. The BIOS bootstrap root would be a trusted root hash, not a trusted filesystem path. Untrusted parties can serve blobs; the proof verifies binding.

**3. The manifest hash would be a Merkle root**

`_write_manifest()` currently hashes the entire manifest JSON as a single blob. A ZK-first manifest would be a Merkle tree over the blob registry entries. This enables efficient proofs of inclusion (prove that blob X is in the manifest without revealing all other entries) without re-hashing the full manifest on each promotion. The audit log entries would include Merkle proofs, not just manifest hashes.

**4. The council/approval artifact would be a ZK statement, not a blob pointer**

Currently `issue_council_approval()` creates a blob containing a list of approved hashes and a reviewer hash. The approval is "verified" by checking the manifest's reviewer registry. In a ZK-first design, an approval would be a ZK proof that: (a) the reviewer holds a private key whose public key is committed in the manifest, and (b) the approved blobs pass the review criteria. The approval itself would be verifiable without loading the manifest or trusting any mutable state.

**5. Feedback blobs would commit to a witnessed execution trace, not just a telemetry hash**

`record_feedback()` anchors feedback to `_LAST_TELEMETRY[logic_hash]` — a hash of a telemetry blob recorded in the same process. In a ZK-first design, the proven-execution anchor would be a ZK proof of execution: a proof that the logic blob was executed with a specific input and produced a specific output (or error). The proof is verifiable by the governance chain without trusting the process that ran the blob. This is the difference between "the process claims it ran the blob" and "we have a proof it ran."

**6. The scrubbed-scope boundary would be enforced by the circuit, not by Python's exec**

f_6 enforces the scope boundary by controlling what Python dict is passed to `exec()`. That is a convention, not a cryptographic guarantee. A ZK-first design would execute blobs in a zkVM (zero-knowledge virtual machine) where the execution trace is proven. The scrubbed scope is enforced by the zkVM's memory model, not by the engine's trust in its own scope setup. This makes the safety passes (Pass 2, Pass 3) unnecessary for security — they become documentation aids, not gates.

**7. The evolve cycle would benchmark on proven execution traces**

The current benchmark loop calls `seed.invoke()` N times and reads telemetry back from the vault. A ZK-first benchmarker would collect proven execution traces and compute fitness over the verified traces. A candidate blob cannot game the benchmark by behaving differently when benchmarked vs. when deployed, because the proof commits to the execution.

---

## Recommendation

**Extend, but with a bounded scope.**

Here is the precise argument:

f_6 has accumulated real architectural capital that does not exist in a fresh wavefunction: a working governance chain (bootstrap → reviewer chain → approval → promotion), a self-modifying evolution loop that uses its own machinery, a proven-execution anchor for feedback, and six iterations of fitness signal refinement. These are not trivially reproduced. The design decisions embedded in them (envelope type-binding, scrubbed scope, governance as blobs, feedback as governed blobs) are correct and would survive a ZK-first redesign largely intact.

What cannot be retrofitted from f_6 without structural change:

1. The JSON envelope format — it must become canonical binary for ZK circuits to be tractable.
2. The vault trust model — `_raw_get()` must become `_raw_get_and_verify()` with a proof parameter, or the ZK proofs prove nothing.
3. The manifest structure — must become a Merkle tree for efficient inclusion proofs.

These three changes are deep enough that every existing vault entry is orphaned and the manifest schema is replaced. That is effectively a new vault with new blob identity rules.

**The practical path: extend with a protocol break**

Do not try to migrate existing vault entries. Define blake3 + canonical binary as the v2 protocol. The vault becomes bi-protocol during transition: a flag or directory split distinguishes SHA256-JSON blobs (legacy, read-only) from blake3-binary blobs (v2, ZK-capable). The governance chain, the evolution loop, and the scrubbed-scope ABI carry forward entirely. The blob identity scheme and the vault trust model are replaced.

**What is specifically lost by extending vs. restarting:**

Extending: you carry the JSON envelope convention as a design scar in the codebase even after migration. The bootstrap reviewer and existing promoted blobs cannot cross the protocol boundary without reprocessing. The audit log contains entries keyed by SHA256 hashes that are no longer the primary identity scheme. These are manageable costs.

Restarting: you lose the six-iteration fitness formula refinement history, the governance chain bootstrapping code (which is non-trivial to get right), the proven-execution anchor design (which is subtle — getting it wrong produces feedback that can be fabricated), and the dynamic tolerance derivation from audit history. You would rebuild these over multiple iterations before reaching f_6-equivalent capability.

**Recommendation in one sentence:** Extend council/f_6 with a declared protocol break at the vault and envelope layer; everything above the content-addressing scheme (governance, evolution loop, fitness formula, scrubbed scope) carries forward without change.

---

*Written: 2026-04-01*  
*Source corpus: /Users/bln/play/synapse/worktrees/f_6/{seed.py, promote.py, evolve.py}*
