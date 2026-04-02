# Red Team Review: D-JIT Blob ABI Circuit

**Reviewer role:** Adversarial / Red Team
**Date:** 2026-04-01
**Target:** `/Users/bln/play/synapse/zk-explore/blob_abi/src/main.nr`
**Verdict summary:** The proof is not meaningful for the stated purpose. All five constraints are satisfiable by a prover who never ran any blob at all.

---

## Attack Vectors (specific, concrete)

### AV-1: Phantom execution — prove a blob ran when nothing ran

The prover controls all private inputs: `result_inverse`, `latency_ms`, `memory_kb`. The public inputs `blob_hash`, `context_hash`, and `result` are supplied by the prover at proof-generation time — the verifier has no mechanism to check where they came from.

**Concrete attack:**
1. Choose any non-zero `blob_hash` (e.g., `0xdeadbeef`).
2. Choose any non-zero `context_hash`.
3. Choose `result = 1`, `result_inverse = 1`.
4. Choose `latency_ms = 1`, `memory_kb = 1`.
5. Generate the proof. All five constraints pass.

No blob ran. No execution occurred. The proof is valid.

### AV-2: Blob substitution — claim blob A ran when blob B (or nothing) ran

`blob_hash` is a public input — the prover sets it. The circuit contains zero constraints linking `blob_hash` to any actual blob content, bytecode, or Merkle root. The prover can put any non-zero value in `blob_hash` and the circuit accepts it.

**Concrete attack:**
- Prover wants to claim blob `X` (a trusted, audited blob) ran.
- Prover actually ran blob `Y` (untrusted, buggy, or never deployed).
- Prover sets `blob_hash = hash(X)` in the proof.
- Circuit accepts. The proof says "blob X ran" but blob Y ran — or nothing ran.

This is not a subtle attack. It is the default capability of any prover who understands the circuit.

### AV-3: Telemetry fabrication — fake latency and memory

`latency_ms` and `memory_kb` are private `u64` inputs. The circuit only checks `> 0`. There is no upper bound, no expected range, no relationship to wall-clock time, and no commitment that ties these values to any external measurement.

**Concrete attacks:**
- Set `latency_ms = 1`, `memory_kb = 1` regardless of what actually ran. Passes.
- Set `latency_ms = 999999999`, `memory_kb = 999999999` to fake a heavy workload. Passes.
- There is no way for a verifier to distinguish `latency_ms = 1` from `latency_ms = 500`. Both produce valid proofs.

Telemetry is meaningless. The constraints prove only that the prover typed a non-zero number.

### AV-4: Result fabrication — claim any output for any input

`result` is a public Field input set by the prover. The circuit only checks `result != 0` via the multiplicative inverse trick. There is no constraint binding `result` to the output of executing `blob_hash` on `context_hash`.

**Concrete attack:**
- A blob that returns `f(context) = 42` is meant to be attested.
- Prover sets `result = 7` (wrong answer), `result_inverse = field_inverse(7)`.
- Proof verifies. The system now accepts a false execution record claiming the blob produced 7.

### AV-5: context_hash is unconstrained relative to context content

`context_hash` is a non-zero public Field. Like `blob_hash`, nothing binds it to actual context data. A prover can:
- Reuse a valid `context_hash` from a legitimate prior proof.
- Pair it with a different `blob_hash`.
- Claim the combination executed, when it never did.

Cross-session replay: a valid proof for `(blob_hash=A, context_hash=C)` at time T1 is indistinguishable from a freshly generated proof for the same pair at T2. There is no timestamp, nonce, or sequence number in the proof.

### AV-6: Multiplicative inverse — field edge case on BN254

The circuit uses `result * result_inverse == 1` to prove `result != 0`. In a prime field this is sound for the standard case. However: if `result` is the field prime `p` itself, it is congruent to `0 mod p`. Any prover who sets `result = p` in the public input has `result == 0` inside the field, but the circuit is likely relying on the Noir type system to prevent this. This is a lower-priority concern but worth noting: the check `result != 0` is never stated as a direct assertion — it is implied by the inverse existing. Confirm that Noir's `Field` type prevents the prover from supplying `p` as `result` in the public input encoding. If not, the non-zero check is bypassed.

---

## What the Proof Does NOT Bind

| Property | Bound? | Notes |
|----------|--------|-------|
| Blob content / bytecode | No | `blob_hash` is an arbitrary non-zero field element; no Merkle proof, no commitment |
| Context content | No | `context_hash` is an arbitrary non-zero field element |
| Causal link: blob ran on context | No | No constraint connects these three values |
| Result correctness | No | `result` is prover-supplied; no execution trace |
| Actual elapsed time | No | `latency_ms` is private, unchecked against any external clock |
| Actual memory consumed | No | `memory_kb` is private, unchecked against any oracle |
| Execution timestamp | No | No nonce, block hash, or sequence number |
| Prover identity | No | No signature or authentication over the proof inputs |
| ABI version / interface | No | No constraint that the blob conforms to any typed interface |
| Uniqueness / replay protection | No | Same inputs produce valid proof indefinitely |

---

## Missing Constraints

Listed in order of severity.

### MC-1 (Critical): Commitment to blob content

`blob_hash` must be a commitment to the actual blob bytecode or content, and the circuit must verify this. Options:
- Require a Merkle inclusion proof: `merkle_path` and `merkle_root` (public) such that `hash(blob_content, merkle_path) == merkle_root`.
- Or: require the prover to know the preimage — commit to `blob_content` as a private input and constrain `poseidon(blob_content) == blob_hash`.

Without this, `blob_hash` is a label, not a commitment.

### MC-2 (Critical): Causal binding between (blob, context) and result

The triple `(blob_hash, context_hash, result)` must be causally linked. The circuit must prove "I know an execution trace T such that running blob B on input C produces result R." This requires either:
- An execution trace committed in the proof (expensive but correct), or
- A SNARK that encodes the blob's computation (a VM circuit), or
- At minimum: a cryptographic commitment scheme where the prover commits to the execution transcript and the circuit verifies the hash.

Without this, the result is disconnected from the blob.

### MC-3 (High): Replay protection / freshness

Add a public nonce or block hash to the circuit inputs. The verifier must check that this nonce has not been seen in a prior accepted proof. Without this, a single valid proof can be replayed indefinitely to inject false execution records.

### MC-4 (High): Telemetry oracle binding

`latency_ms` and `memory_kb` must be bound to an external measurement. Options:
- A trusted execution environment (TEE) attestation committed in the proof.
- A signed measurement report from a co-located monitor, with the signature verified inside the circuit.
- Or: drop these constraints entirely and be honest that they are not enforceable in a prover-controlled environment.

As written, these constraints prove nothing about actual resource consumption.

### MC-5 (Medium): Result range / type enforcement

The ABI presumably specifies a result type (a typed return value). The circuit should constrain `result` to the expected range or structure. `result != 0` is not an ABI check — it is a null check. A blob that always returns `1` regardless of input would satisfy this constraint for every execution.

### MC-6 (Medium): Prover authentication

If the D-JIT system tracks which prover attested which execution, add a public key commitment and require the prover to sign the public inputs. Otherwise any party can generate valid proofs for any blob, including blobs they have no access to.

### MC-7 (Low): Blob hash zero-check sufficiency

`blob_hash != 0` is a weak content-address check. It does not prevent collision attacks or distinguish a hash from a random non-zero field element. Pair this with MC-1 (Merkle proof) to make it meaningful.

---

## Verdict: Is This Proof Meaningful for the Stated Purpose?

**No.**

The stated purpose is: "prove that a blob execution respected the ABI contract." The proof as written does not establish any of the following:

1. A blob ran.
2. The blob identified by `blob_hash` ran.
3. The blob ran on the input identified by `context_hash`.
4. The result is the output of that execution.
5. The execution consumed the claimed resources.

Every public input (`blob_hash`, `context_hash`, `result`) is prover-chosen with no binding to external reality. Every private input (`result_inverse`, `latency_ms`, `memory_kb`) is trivially satisfiable with minimal values.

A prover who has never deployed a blob, never executed anything, and has no access to any runtime can generate an unlimited number of valid proofs for arbitrary `(blob_hash, context_hash, result)` triples in under one second.

**The five constraints prove only:**
- The prover can do field arithmetic (constraint 1).
- The prover typed three non-zero numbers (constraints 2, 3, 4, 5).

**This circuit is not a ZK attestation of blob execution. It is a proof of knowledge of field arithmetic.**

For the D-JIT promotion gate to have meaning, the circuit must bind at least MC-1 (content commitment) and MC-2 (causal execution link). Without those, council approval based on this proof is approval of a prover's ability to type non-zero integers, not evidence that any blob ran correctly.

---

*Red Team sign-off: all attack vectors above are trivially exploitable with off-the-shelf Noir tooling. No cryptographic weakness required — the attacks are structural.*
