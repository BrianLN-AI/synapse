# Council Review: Extend vs. Restart — ZK Pragmatist Perspective

**Reviewer:** The ZK Pragmatist
**Date:** 2026-04-01
**Scope:** O1 (v1 circuit) + O2 (v2 circuit, `blob_abi_v2/src/main.nr`) vs. current D-JIT system at f_6
**Question:** Does ZK work actually change anything real in this system, or is it theoretical theater? Extend from f_6 or fresh collapse?

---

## Practical Feasibility Assessment

### The 29-second problem is real, but the framing is wrong

29 seconds to generate a proof is not disqualifying by itself. The question is: what is it gating?

In the current f_6 cycle, blob promotion is a deliberate, infrequent governance event — `evolve.py` runs, benchmarks candidates over 25 rounds with 5 warmup discards, then Triple-Pass Review runs, then Council Approval issues, then manifest updates. That entire cycle takes minutes. A 29-second proof generation step is a rounding error in the governance latency, not a throughput bottleneck.

The real problem is **where in the cycle the proof lives**. If proof generation happens once per promotion (after the benchmark confirms a winner), 29 seconds is fine. If it happens per-invocation as part of blob execution, it is a 29-second tax on every call through the linker — catastrophically wrong.

The current toolchain (Noir beta.19, Barretenberg 4.0.0-nightly, UltraHonk) is pre-production. [MEASURED from circuit metadata] 21ms verification is already acceptable. Proof generation times will improve as the toolchain matures; 29 seconds is a 2026 number for blake2s in-circuit over 512 bytes, not a fundamental limit.

**Verdict on feasibility:** Proof generation at promotion time is viable. Proof generation at invocation time is not. The architecture must place the prover outside the hot path.

### The hash function mismatch is an immediate blocker

The prompt says O2 uses blake3 in-circuit. The actual `blob_abi_v2/src/main.nr` uses `std::hash::blake2s`. [MEASURED from source] The vault currently uses SHA256 for content-addressing. These three hash functions are all different.

This is not a minor discrepancy. If the circuit proves `blake2s(blob_content) == blob_hash` but the vault stores blobs under their SHA256 address, the blob_hash in the proof will never match any manifest entry. The content binding is mathematically sound but operationally useless — it proves possession of content that hashes correctly under one function, while the system authenticates by another.

Before any production integration, one of these must happen:
- Migrate the vault from SHA256 to blake2s (touches every blob address in the system)
- Replace the in-circuit hash with SHA256 (SHA256 in-circuit is more expensive than blake2s; `Sha256Compression` is available in Noir but not as a full-message hash in beta.19 [INFERRED from circuit comment])
- Treat blob_hash as a commitment separate from the vault key, requiring a mapping layer

The O1 pragmatist review identified the content-binding gap. O2 closes the cryptographic gap (fabrication attack) but introduces an operational gap (hash function mismatch). Neither circuit is deployable against the current vault without changes to the storage layer.

### The fitness circuit is more immediately useful than the content-binding circuit

The `compute_fitness` function in O2 proves the fitness score was computed honestly from public telemetry aggregates. This is different in character from the blob content circuit: the inputs are all public, anyone can verify the arithmetic independently, and the circuit adds a checkable commitment that the council member did not manipulate the formula.

This is a narrow but real guarantee. The fitness formula in f_6 is deterministic from public telemetry; what the fitness circuit adds is a proof that the promoter used the canonical formula and not a modified version that favored their candidate. That is a meaningful governance property — it closes the "honest arithmetic" gap without requiring TEE-level trust in the measurement source.

---

## What ZK Adds (vs. What Already Exists)

The existing system at f_6 provides:
- **Content integrity:** SHA256 content-addressing. If the hash matches, the bytes are identical. Deduplication is free. Tampering is detectable.
- **Governance chain:** Triple-Pass Review (StaticAnalysis → SafetyVerification → ProtocolCompliance), Council Approval artifact (hashed and stored), append-only audit.log.
- **Promotion integrity:** manifest.hash is SHA256 of the manifest content. Any modification to the manifest is detectable.
- **Execution telemetry:** every invocation writes a telemetry artifact. Fitness signals are aggregated from real measured runs.
- **Trust weighting:** council reviewers have explicit trust_weight values; the evolve-engine reviewer runs at 0.8.

**What does ZK add on top of this?**

| Property | f_6 provides | ZK adds |
|----------|-------------|---------|
| Blob bytes are what the hash says | Yes — SHA256 | Nothing new (already solved) |
| Fitness was computed from the canonical formula | No — take the promoter's word for it | Yes — fitness circuit proves honest arithmetic |
| Council member actually possessed and ran the blob | No — audit.log records approval, not execution | Yes — content-binding circuit proves possession (not execution) |
| Execution measurements are honest | No — telemetry is self-reported by the executor | No — O2 circuit does not cover this |
| Proof is tied to a specific governance event | No circuit covers this | No — not implemented in either version |
| Replay prevention | None in current system | None in either circuit |

**The honest answer:** ZK adds one thing the existing system genuinely lacks — a proof that the promoter possessed the actual blob bytes at time of approval (the content-binding circuit), and that the fitness formula was applied correctly (the fitness circuit). Everything else the current governance chain already handles.

What ZK does *not* add — and cannot add without additional protocol design: proof that the blob was actually executed, that telemetry measurements are honest, or that the proof is bound to a specific council vote at a specific time.

### The fabrication attack O2 closes is real but low-stakes here

O2 closes the fabrication attack identified in O1: without content binding, a prover can claim blob X ran when blob Y ran. This is a real vulnerability. But in the f_6 trust model, the council is a small group of authorized reviewers running the evolve cycle collaboratively. The fabrication attack is primarily a threat from external or adversarial provers.

In a distributed deployment where untrusted nodes submit proofs of blob execution for remote verification, content binding is critical. In a trusted-council single-operator setup, the threat model is different. The urgency of closing this gap depends on the deployment model the system is moving toward.

---

## Minimum Viable ZK Integration

If the goal is to add meaningful ZK guarantees without redesigning the system, the minimum integration that changes something real is:

**Step 1: Fitness proof at promotion time (immediate, no hash migration)**

The fitness circuit already works. The inputs are public (from vault telemetry). Add a step to `evolve.py`: after benchmarking, before issuing Council Approval, generate a fitness proof over the telemetry aggregates that produced the winning score. Store the proof artifact in the vault. Record the proof hash in the Council Approval artifact alongside the existing data.

This adds a checkable commitment that fitness was computed honestly. It requires no hash migration, no changes to the vault, no change to the verification trust model (anyone can re-derive the telemetry aggregates and verify the proof). The 29-second proof generation is acceptable here because it happens once per promotion, not per invocation.

Cost: integrate Nargo proof generation into `evolve.py` as a subprocess call. Verification is 21ms and can run as part of any audit.

**Step 2: Resolve the hash function conflict before content-binding**

Before the blob content circuit is useful, pick one hash function: blake2s throughout (migrate vault addressing), or SHA256 in-circuit (wait for Noir beta to support it fully). This is a prerequisite for Step 3, not a ZK question — it is a vault architecture question.

**Step 3: Content-binding proof at promotion time (after Step 2)**

Once the hash function is unified, the content-binding circuit proves the promoter possessed the actual blob bytes. Store the content proof in the vault alongside the Council Approval artifact. This closes the fabrication attack for remote or semi-trusted governance.

**What to skip for now:**

- Proof of execution with honest telemetry: this requires either a TEE or independent re-execution by each council member. The protocol design is substantial. The circuit does not cover this and cannot without hardware support or a multi-party measurement protocol.
- Per-invocation proofs: 29 seconds per invocation is not viable. Batch proofs (one proof for N invocations) would require a different circuit design.
- Replay prevention and identity binding: real but requires additional public inputs (nonce, council member key). Design the protocol spec first.

---

## Recommendation

**Extend from f_6, not a fresh collapse. ZK is additive here, not foundational.**

Here is why "ZK-first design" does not mean "start over":

The D-JIT system's core value — content-addressed blobs, measured fitness selection, self-modifying evolution — has nothing to do with ZK. ZK is a governance audit mechanism layered on top. The vault, the linker, the telemetry loop, the Triple-Pass Review: these are all correct and do not need replacement.

A "ZK-first fresh collapse" would mean redesigning the system with ZK primitives as the trust root. What would that actually require?

- The vault would need to use a ZK-friendly hash function (blake2s, Poseidon, or MiMC) throughout, not SHA256
- The fitness formula would need to be in-circuit from the start
- Council governance would need to be a multi-party proving protocol, not a sequential approval chain
- Proof generation would need to be integrated into the execution path, not bolted on at promotion time

That is a significant amount of protocol and circuit design that does not yet exist. Building it before the protocol spec is written is the mistake the O1 pragmatist review warned against: "Before writing more Noir, write the protocol spec." The same warning applies to a fresh collapse.

**What "ZK-first" means in practice vs. in theory:**

In theory: the system's trust model is cryptographically grounded from the ground up. No governance action is accepted without a proof. Fitness is a ZK commitment. Blob execution is attested.

In practice, right now: integrate the fitness proof into `evolve.py` (Step 1 above), resolve the hash function conflict, then add content-binding proofs. This is three concrete tasks, all additive to f_6, none requiring a rebuild. The system evolves — which is what the f_n model is designed to do.

**The one thing that cannot be retrofitted easily:**

The vault's hash function. SHA256 content-addressing is baked into every blob address in the vault, the manifest, and the audit log. If the system ever needs ZK-native content addressing (Poseidon, MiMC) for recursive proof composition or L2 compatibility, migrating the vault is a significant operation. This is the only architectural decision that costs more to defer than to make now.

If ZK-native content addressing is a hard future requirement — for example, if the goal is to publish blob inclusion proofs to a ZK rollup or to compose proofs recursively — then the vault hash function migration is worth doing in a dedicated f_7 cycle. If it is not a hard requirement, SHA256 is fine and the current architecture supports Step 1 and Step 3 with a local blake2s mapping.

**Bottom line:** The existing council governance already provides most of what matters. ZK adds honest-arithmetic proofs for fitness and possession proofs for content binding. Neither requires starting over. The minimum viable integration is the fitness proof at promotion time — it adds a real guarantee, it works with the current toolchain, and it does not require resolving the hash migration question first. Start there. Let the next f_n tell you what the telemetry reveals.
