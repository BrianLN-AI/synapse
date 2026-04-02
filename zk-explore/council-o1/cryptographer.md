# Cryptographer's Adversarial Review: D-JIT Blob ABI Circuit

**Reviewer role:** The Cryptographer (Council review)
**Date:** 2026-04-01
**Artifact:** `/Users/bln/play/synapse/zk-explore/blob_abi/src/main.nr`
**Claims under review:** KR1.1 (circuit encodes ABI constraints and proof verifies), KR1.2 (proof generation < 30s)

---

## What Holds Cryptographically

### The non-zero result check is sound (with one caveat addressed below)

`assert(result * result_inverse == 1)` is the standard multiplicative inverse technique for
non-zero proof in a prime field. In a prime field F_p, every non-zero element has a unique
multiplicative inverse. Zero has no multiplicative inverse because `0 * x = 0` for all x,
and `0 != 1`. The constraint is satisfied if and only if `result != 0` in F_p. This is a
well-established pattern — it holds.

### The hash non-zero checks are syntactically sound

`assert(blob_hash != 0)` and `assert(context_hash != 0)` compile to a valid field inequality
constraint. Given that `blob_hash` and `context_hash` are public inputs, the verifier can
also check these directly. The circuit constraint correctly rejects the zero case.

### The latency and memory checks are syntactically sound

`assert(latency_ms > 0)` and `assert(memory_kb > 0)` on `u64` types produce valid range
constraints. u64 is a non-field type with bounded range; Noir compiles this to bit-decomposition
or comparison constraints. The arithmetic is correct.

### KR1.2 is uncontested

87ms proof generation is plausible for a circuit this small — five constraints, no loops, no
recursion. The circuit is trivially small. This number is almost certainly accurate.

---

## What Does NOT Hold (Gaps)

### 1. The multiplicative inverse trick has one critical edge case in F_p

In BN254 (the field Noir uses by default), `p` is a specific 254-bit prime. The field
element representing `result = p` reduces to `0` in F_p. A prover supplying the raw integer
value of `p` as the result would have it reduce to zero at the field level — but this is
handled: Noir's field type already reduces inputs mod p at witness assignment time. There is
no bypass here for a compliant Noir prover.

However: if `result` encodes a semantic value (e.g., "the blob's return value"), then
`result = p - 1` is a valid non-zero field element that satisfies the constraint. The circuit
does not check that `result` falls within any semantic range. Any non-zero field element
passes. This is not a soundness gap for the stated claim ("result != 0") but is a semantic
gap — see below.

### 2. Proving `blob_hash != 0` proves nothing about the blob's actual content

This is the largest gap in the circuit.

`blob_hash` is a **public input**. The verifier supplies it (or the prover presents it and
the verifier checks it against an expected value). The circuit asserts it is non-zero. That
is all. The circuit contains:

- No hash computation. There is no `pedersen_hash`, no `keccak256`, no `poseidon` call.
- No binding between `blob_hash` and any actual blob bytes.
- No commitment scheme. No Merkle path. No preimage constraint.

What the circuit actually proves: "I know a non-zero field element that I am calling
`blob_hash`." The prover can supply any non-zero value — `0xdeadbeef`, `1`, `0xFFFF...` —
and the constraint passes. There is no cryptographic link between `blob_hash` and any blob
that actually ran.

The claim that this proves "blob_hash matches content" (KR1.1) is **false**. The circuit
does not constrain the relationship between `blob_hash` and any content.

### 3. Proving `latency_ms > 0` and `memory_kb > 0` does not prove execution ran

`latency_ms` and `memory_kb` are **private witnesses**. The prover chooses them freely.
A cheating prover does this:

1. Pick any blob_hash != 0 (e.g., `1`).
2. Pick any context_hash != 0 (e.g., `1`).
3. Pick any result != 0 (e.g., `1`), compute result_inverse = 1.
4. Set latency_ms = 1, memory_kb = 1.
5. Generate proof. It verifies.

The blob never ran. No execution occurred. The proof is completely synthetic. The private
witnesses are unconstrained by any execution trace. There is no commitment to measured values,
no attestation from a trusted execution environment, no oracle binding latency_ms to wall
clock time.

The claim that latency > 0 and memory > 0 proves "execution consumed real time and memory"
is **false**. These are self-reported private values with no external anchor.

### 4. The `context_hash` constraint is identical in weakness to `blob_hash`

The circuit checks `context_hash != 0` but places no constraint relating `context_hash` to
any actual context. Same gap as `blob_hash`.

### 5. `result` is public but unconstrained relative to execution

The verifier sees `result`. But the circuit contains no constraint tying `result` to a
computation over `blob_hash` or `context_hash`. A prover can present result = 42 for any
blob_hash and any context_hash. The circuit does not prove "this blob, given this context,
produced this result." It proves only "these three non-zero values coexist in a proof."

---

## Soundness Concerns

### SC1: Complete fabrication attack

A cheating prover who has never run any blob can generate a valid proof for any statement of
the form "blob X produced result Y in context Z." Steps: choose any three non-zero values for
the public inputs, compute result_inverse, set latency_ms = memory_kb = 1. Proof generates
and verifies. This is not a theoretical concern — it is the default behavior of this circuit
for any non-zero inputs.

The circuit has **zero binding** between public claims and any execution reality.

### SC2: The circuit proves its own satisfiability, not execution semantics

When the verifier checks this proof, they learn:
- Some witness exists such that the five constraints are satisfied.
- Specifically: result != 0, blob_hash != 0, context_hash != 0, some private latency > 0,
  some private memory > 0.

They do not learn:
- That the blob identified by `blob_hash` ran.
- That it ran in the context identified by `context_hash`.
- That it produced `result`.
- That any execution occurred at all.

The proof is a proof of satisfiability of a trivially satisfiable constraint system.

### SC3: Zero-knowledge property is technically present but irrelevant

Is the circuit ZK? Yes — `result_inverse`, `latency_ms`, and `memory_kb` are private
witnesses; the verifier learns nothing about them beyond that they satisfy the constraints.

But this observation cuts both ways: **the ZK property hides the private witnesses from the
verifier, which means the verifier cannot check whether those witnesses correspond to anything
real.** The privacy guarantees reinforce the fabrication attack (SC1) rather than protecting
anything meaningful.

The verifier does learn something they might not need to know: that a valid `result_inverse`
exists — but since `result` is public, anyone can verify result != 0 directly without the
proof. The ZK property here protects nothing of value and obscures the fact that the prover
fabricated the private witnesses.

### SC4: No trusted execution environment binding

A meaningful ZK proof of execution would require one of:
- A commitment to the blob's bytecode inside the circuit (hash the bytecode, constrain it).
- An execution trace commitment (prove the VM steps were followed).
- A TEE (Trusted Execution Environment) attestation incorporated as a public input with a
  signature verification constraint.
- An oracle signature over (blob_hash, context_hash, result, latency_ms, memory_kb) verified
  inside the circuit.

None of these are present. The circuit has no execution model. It is five inequality checks.

### SC5: The test suite validates syntax, not security

`test_valid_execution` uses `result=1, result_inverse=1` — the simplest possible case.
`test_zero_result_fails` confirms the constraint rejects zero. These tests confirm the circuit
compiles and the Noir runtime applies the constraints. They do not test any security property
or confirm the circuit is binding against a cheating prover.

The test suite is a correctness smoke-test, not a security test.

---

## Verdict on KR1.1 and KR1.2

### KR1.2: Proof generation < 30s — CONFIRMED

87ms is credible for a five-constraint circuit with no recursive proof composition. This
claim holds.

### KR1.1: Circuit encodes ABI constraints and proof is "meaningful" — PARTIALLY FALSE

The precise claim in KR1.1 is: "Noir circuit encoding D-JIT ABI constraints (result exists,
blob_hash matches content, result != 0) generates a valid proof and verifies."

Breaking it down:

| Sub-claim | Verdict | Reason |
|-----------|---------|--------|
| Circuit generates a valid proof | TRUE | Trivially — five satisfiable constraints |
| Proof verifies | TRUE | Trivially — circuit is correct Noir |
| result != 0 is enforced | TRUE | Multiplicative inverse technique is sound |
| blob_hash matches content | FALSE | No hash computation, no preimage constraint, no binding |
| result exists (ABI-semantically) | MISLEADING | result != 0 is proved; that result came from blob execution is not |
| Proof attests blob execution respected ABI | FALSE | No execution model in circuit; prover can fabricate all witnesses |

The circuit is **sound as a Noir program** — it does what the code says. The circuit is
**unsound as an attestation of execution** — it cannot distinguish real execution from
fabricated witnesses.

The word "meaningful" in the claim context requires that the proof tells the verifier
something they could not fabricate themselves. This proof does not satisfy that requirement.
Any party with three non-zero field elements can generate a valid proof without running
anything.

### Summary judgment

KR1.1 is half-true and half-false. The proof is technically valid. The semantic claim — that
it attests blob execution respected the ABI contract — does not hold. The circuit is a
proof-of-concept that demonstrates Noir tooling works, not a proof that any blob ran.

To make this meaningful, the circuit needs at minimum:
1. A hash of the blob bytecode computed inside the circuit (binding blob_hash to actual content).
2. A signature or commitment over execution measurements (binding latency_ms and memory_kb to
   a trusted source, not the prover's own choice).
3. Either a simplified execution trace or a TEE attestation verified as a circuit constraint.

Without these, the proof demonstrates that the prover can satisfy five arithmetic inequalities.
It does not demonstrate that any blob executed.
