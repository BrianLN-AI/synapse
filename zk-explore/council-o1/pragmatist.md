# Council Review: ZK Blob ABI Circuit — Pragmatist Perspective

**Reviewer:** The Pragmatist
**Date:** 2026-04-01
**Circuit:** `/Users/bln/play/synapse/zk-explore/blob_abi/src/main.nr`
**Stated purpose:** Cryptographically verifiable council approval of D-JIT blob promotion

---

## What Works in the Toy, Breaks in Production

### 1. The field arithmetic for result non-zero is correct but trivial to satisfy

The `result * result_inverse == 1` pattern is a valid ZK technique for proving non-zero. It works. But the test uses `result=1, result_inverse=1` — the degenerate case where no real multiplicative inverse is computed. A more meaningful test would use `result=42` and the actual BN254 field inverse of 42. That inverse is a large number, not 1. The test does not exercise the constraint the comment claims it exercises.

This is not a soundness bug. The circuit constraint is correct. But the test gives false confidence — it passes for the wrong reason.

### 2. `blob_hash != 0` is not blob integrity

In the real D-JIT system, `blob_hash` must be the SHA256 hash of the blob's actual bytecode. The circuit only checks it is nonzero. Any 32-byte nonzero value satisfies the constraint.

What this means concretely: a prover can submit the proof with `blob_hash = 1` and a blob that has nothing to do with the manifest entry. The verifier cannot distinguish a proof over the real blob from a proof over an arbitrary hash. The content-addressing property — the whole point of a vault indexed by SHA256 — is not enforced by this circuit.

The circuit comment says "blob was content-addressed (hash is non-zero)." That claim is false. Non-zero is necessary but nowhere near sufficient for content-addressing.

### 3. `latency_ms` and `memory_kb` are private witnesses — the prover supplies them

This is the deepest practical problem. `latency_ms` and `memory_kb` are private inputs. The circuit proves that the prover knows *some* nonzero values for these fields. It does not prove the values correspond to an actual execution. A prover can supply `latency_ms=1, memory_kb=1` and the proof is valid.

To generate *honest* values, whoever runs the blob must instrument the execution, capture wall-clock time and RSS (resident set size), and feed those numbers as witnesses when generating the proof. There is currently no mechanism in the system to enforce this. The prover is trusted to be honest about their own measurement. That is not a ZK proof of execution; it is a signed attestation with extra steps.

### 4. `context_hash != 0` tells us nothing about the context

Same issue as `blob_hash`. The context could be a garbage value. There is no binding between the `context_hash` witness and the actual execution context the council is approving.

### 5. Result being a `Field` is underspecified

Python's `exec()` returns `None`. Whatever "result" means in the D-JIT execution model needs to be defined concretely before it can be committed to a ZK witness. Does result mean the value of a specific variable after execution? The return code? A hash of stdout? The circuit does not say, and neither does the test. `result=1` is meaningless without a spec.

---

## Trust Model Gaps

### Who is the prover?

The circuit does not answer this, and the answer matters enormously.

**Option A: The node running the blob is the prover.** This is the natural reading — the executor generates the proof after running the blob. Problem: the executing node is adversarially positioned. It has every incentive to claim good latency and valid results. The proof proves only that the node *knows a valid assignment*, not that the assignment came from real execution.

**Option B: A council member is the prover.** Then the council member must have run the blob themselves before voting. That is a plausible trust model — each approver runs and measures independently. But the circuit does not enforce that council members are the ones generating proofs, and there is no binding between a proof and a council member's identity.

**Option C: A trusted execution environment generates the proof.** This is the only model where `latency_ms` and `memory_kb` carry real meaning, because the measurement source is outside the prover's control. But there is no TEE here.

Without a defined prover identity, the trust assumption is: "whoever generates this proof is honest about their execution measurements." That is a soft trust assumption, not a cryptographic one.

### The proof does not bind to any council vote

A ZK proof is a mathematical object. Right now, nothing in the circuit ties the proof to a specific council approval event, a timestamp, a quorum of approvers, or a manifest version. The proof says "some execution with these public inputs satisfied the ABI." It does not say "the council voted to promote blob X at time T."

For blob promotion governance, you need the proof to be a commitment inside a larger protocol — a vote record, a merkle accumulator of approvals, something. Standalone, this proof has no governance semantics.

### Replay attacks are unaddressed

The proof is replayable. A valid proof for blob X in context Y at time T1 is also a valid proof at time T2. There is no nonce, no timestamp, no epoch in the public inputs. A stale or recycled proof cannot be distinguished from a fresh one.

---

## Path from Toy to Real

Ordered by what blocks production use vs. what is nice to have.

### Must fix before this means anything

**1. Bind `blob_hash` to actual blob content.**
The verifier must be able to confirm that `blob_hash` is the SHA256 of the blob bytes being promoted. Either: (a) compute the hash inside the circuit from private blob bytes — expensive but airtight; or (b) make `blob_hash` a public input that the verifier independently computes from the vault and checks matches. Option (b) is practical: verifier fetches the blob from the vault, computes SHA256, checks it equals the `blob_hash` in the proof. The circuit does not change, but the verification protocol does.

**2. Define what `result` means.**
Specify the ABI: after `exec(blob_code, context)`, what variable or return channel carries the canonical result? That spec must exist before the circuit has meaning. The result should probably be a hash of the execution output, not a raw Python value, since raw Python objects are not field elements.

**3. Add a replay-prevention nonce.**
Include a per-vote epoch or nonce as a public input. The council approval flow generates the nonce; the proof must be generated fresh for each promotion event.

### Must fix to get real execution measurements

**4. Define the measurement harness.**
Specify exactly what process runs the blob, how it measures wall-clock time and peak RSS, and what guarantees that the prover cannot substitute different numbers. Candidates:
- Independent re-execution by each council member (option B above) — verifiable but slow
- A lightweight sandboxed runner that signs its own measurements — shifts trust to the sandbox
- TEE-based attestation — strong but heavy

Until this is defined, `latency_ms` and `memory_kb` are self-reported and the proof of ABI compliance is nominal.

**5. Bind the proof to a prover identity.**
Add the prover's public key or council member ID as a public input. The corresponding private key is used in witness generation. This lets the manifest record which council member ran each verification.

### Nice to have

**6. Range-check latency and memory.**
`latency_ms > 0` accepts 1ms. A blob that executes in 1ms is suspiciously fast. Minimum thresholds (e.g., `latency_ms >= 10`) would make phantom execution claims slightly harder to fake plausibly.

**7. Test realistic field arithmetic.**
Add a test with `result=42` and the correct BN254 field inverse of 42. The current tests do not exercise the non-zero check for any value other than 1.

---

## Verdict on Whether O1 Is a Meaningful Step Toward the Stated Goal

O1 is a proof of concept for ZK tooling in this stack, not a meaningful step toward cryptographically verifiable blob promotion governance.

What O1 demonstrates: Noir can be used in this project, the toolchain compiles and runs, and the basic ZK pattern for proving non-zero via multiplicative inverse is understood.

What O1 does not demonstrate: that execution actually happened, that the blob hash corresponds to anything in the vault, that the proof is tied to a council decision, or that the trust model has been thought through.

The stated goal is to "make council approval cryptographically verifiable." The current circuit makes it cryptographically verifiable that *someone* generated a proof satisfying five trivially-satisfiable constraints. That is not the same thing. A council member who wants to rubber-stamp a blob without running it can generate a valid proof in seconds by supplying `latency_ms=1, memory_kb=1` and any nonzero hash.

The gap is not a Noir gap or a ZK math gap. The gap is a protocol design gap: there is no mechanism binding the proof to real execution, real blob content, or a real council vote. Those bindings must be designed before the circuit has governance semantics.

O1 is a useful foundation in the sense that the toolchain works and the team understands the ZK primitive. It is not a foundation in the sense that the subsequent work is incremental — the protocol design work required is substantial and independent of the circuit syntax.

**Recommended next step:** Before writing more Noir, write the protocol spec. Define: who proves, what they prove over, how the manifest records proofs, and how replay is prevented. The circuit follows from the spec; the current circuit was written without one.
