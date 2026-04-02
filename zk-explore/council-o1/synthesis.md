# Council Synthesis: ZK O1 Blob ABI Circuit Review

**Date:** 2026-04-02
**Reviewers:** Cryptographer, Pragmatist, Red Team
**Artifact:** `zk-explore/blob_abi/src/main.nr`
**Claims under review:** KR1.1 (circuit encodes ABI constraints, proof is meaningful), KR1.2 (proof generation < 30s, verification < 100ms)

---

## IAC Findings (3/3 convergence — highest confidence)

### [IAC-1] The proof is fully fabricable without running any blob

Every reviewer independently identified this as the central verdict.

**Concrete attack:** Choose any three non-zero values for public inputs. Set `result_inverse = field_inverse(result)`. Set `latency_ms = 1`, `memory_kb = 1`. Generate proof. It verifies. No blob ran.

This is not a subtle gap. It is the default behavior of the circuit for any non-zero inputs. A prover who has never deployed a blob and has no access to any runtime can generate unlimited valid proofs for arbitrary `(blob_hash, context_hash, result)` triples.

### [IAC-2] `blob_hash != 0` is not content-addressing

The circuit comment says "blob was content-addressed (hash is non-zero)." This comment is false.

Content-addressing requires the hash to be cryptographically derived from the content. The circuit contains no hash computation — no `blake3`, no `poseidon`, no Merkle proof. It accepts any non-zero field element as `blob_hash`. The prover can supply `1`, `0xdeadbeef`, or a hash of a completely different blob and the constraint passes. `blob_hash` is a label, not a commitment.

### [IAC-3] `latency_ms` and `memory_kb` are self-reported with no external anchor

These are private witnesses the prover supplies freely. The circuit checks `> 0`. There is no commitment to a measurement source, no oracle binding, no TEE attestation. A prover sets `latency_ms = 1, memory_kb = 1` regardless of what actually ran. Equally, they can set `latency_ms = 999999999` to fake a heavy workload. Both pass. The constraints prove only that the prover typed a non-zero number.

### [IAC-4] KR decisions

| KR | Claim | Decision | Basis |
|----|-------|----------|-------|
| KR1.2 | Proof generation < 30s, verification < 100ms | **YES** | 87ms prove / 22ms verify is credible for 5 constraints. Uncontested. |
| KR1.1 | Circuit encodes ABI constraints, proof is "meaningful" | **NO** (misleading) | Proof is technically valid Noir; semantic claim does not hold. |

KR1.1 sub-claim breakdown:

| Sub-claim | Verdict |
|-----------|---------|
| Circuit is valid Noir that compiles | YES |
| Proof generates and verifies | YES |
| `result != 0` is enforced | YES — multiplicative inverse technique is sound |
| `blob_hash` matches content | NO — zero binding to actual content |
| Proof attests blob execution | NO — fabrication trivially available |
| Proof is "meaningful" | NO — any three non-zero integers produce a valid proof |

### [IAC-5] The test suite validates syntax, not security

`test_valid_execution` uses `result=1, result_inverse=1` — the degenerate case. `1×1=1` happens to be correct but exercises no real BN254 field arithmetic. The three `should_fail` tests confirm the constraints reject zero inputs. No test exercises a cheating prover. No test checks that a fabricated proof cannot be generated.

---

## 2/3 Convergence

**Replay attacks unaddressed** (Pragmatist, Red Team): No nonce, epoch, or timestamp in the proof. A valid proof for `(blob X, context Y)` is valid indefinitely and indistinguishable from a fresh proof. Follows from IAC-1 but worth naming separately.

**`context_hash` has identical weakness to `blob_hash`** (Cryptographer, Red Team): Checks non-zero, binds to nothing.

**ZK privacy reinforces the fabrication attack** (Cryptographer, implied by Pragmatist): The private witnesses hide the prover's fabricated values from the verifier, making phantom execution undetectable. The ZK property here protects nothing of value.

---

## Single-agent findings worth preserving

**Pragmatist — highest-leverage prescription:** Write the circuit spec before writing more Noir. The current circuit was written without a protocol spec. The question "what should the proof bind?" was not answered first. The subsequent work is substantial and must happen at the protocol level.

**Pragmatist — trust model gap:** Who is the prover? (A) Executing node — adversarially positioned. (B) Council member re-runs independently — soft trust, not cryptographic. (C) TEE attestation — strong but absent. This is undefined, and the answer determines what constraints the circuit needs.

**Red Team — repair roadmap:**

| Priority | Missing constraint | What it fixes |
|----------|-------------------|---------------|
| MC-1 (Critical) | Commitment to blob content | Bind `blob_hash` to actual bytecode via Merkle proof or preimage constraint |
| MC-2 (Critical) | Causal binding: (blob, context) → result | Prove the execution trace, not just three coexisting values |
| MC-3 (High) | Replay protection / freshness nonce | Prevent recycling of stale proofs |
| MC-4 (High) | Telemetry oracle binding | Bind `latency_ms`/`memory_kb` to a trusted measurement source |
| MC-5 (Medium) | Result range / type enforcement | Constrain `result` to a semantically defined range |
| MC-6 (Medium) | Prover authentication | Bind proof to a council member's identity |
| MC-7 (Low) | Stronger hash zero-check | `blob_hash != 0` does not prevent collision substitution |

**Cryptographer — ZK_PROTOCOL implication:** `ZK_PROTOCOL.md` states "ZK proves computation correctness at promotion time." The O1 circuit does not prove computation correctness. It proves the prover can satisfy five trivially-satisfiable arithmetic constraints. The spec is aspirational; O1 does not fulfill it yet.

---

## What O1 Actually Demonstrated

O1 demonstrates **the toolchain is operational**: Noir compiles on this stack, UltraHonk proves and verifies at these sizes, the basic non-zero check pattern is understood, `std::hash::blake3` is available. That is a real finding — the ZK path is technically open.

O1 does not demonstrate that any blob executed, that `blob_hash` matches content, or that execution measurements are real.

---

## Recommended Next Step (IAC-confirmed, 3/3)

**Before writing O2 or any new Noir:**

1. **Update ZK_PROTOCOL.md circuit spec.** Define: what is `blob_hash` a commitment to and how is it verified, who the prover is, how execution measurements are bound to reality, how replay is prevented. The circuit follows from the spec.

2. **Address MC-1 and MC-2 first.** Content commitment and causal execution link are blocking. Without them, the proof has no governance semantics — it is a proof that the prover can do field arithmetic.

3. **Revise KR1.1** to match what was demonstrated: "Noir circuit demonstrates ZK toolchain is operational on this stack" — that is YES with evidence.

The protocol design work required to get from O1 to a meaningful proof is substantial and independent of Noir syntax. Define the protocol first; write the circuit second.

---

*IAC threshold: 3/3 = highest-confidence finding. Act on IAC findings first.*
*Reviewers operated independently. Synthesis produced 2026-04-02.*
