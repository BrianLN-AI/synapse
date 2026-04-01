# ZK_PROTOCOL.MD: The Witnessing
**Version:** 1.0.0
**Status:** Active — f_7 baseline

Zero-knowledge proof integration for the D-JIT Logic Fabric. Defines what can be proved,
what cannot, and what assumptions the proofs rest on.

---

## The Core Claim

A blob can prove it was executed honestly — not merely that it ran.

Without ZK, the governance chain (Triple-Pass + Council Approval) establishes *process*
trust: the right steps were followed by the right reviewers. With ZK, promotion candidates
establish *computational* trust: the arithmetic was correct, the content was possessed.
These are complementary. Neither replaces the other.

---

## Canonical Hash Function

**blake3**, 32-byte output.

| Property | Value |
|----------|-------|
| Output size | 32 bytes |
| Platform | Optimized for 64-bit (SIMD, AVX2) |
| Noir availability | `std::hash::blake3` — confirmed in beta.19 |
| Python | `pip install blake3` |
| Rationale | 32-byte output (same interface as SHA-256), faster than blake2 on 64-bit, single algorithm (no 32-bit/64-bit variant split), available in Noir stdlib |

Do not use SHA-256, blake2s, or blake2b in new code. The vault address IS the blake3 hash.

---

## Vault Threat Model

**Current state: trusted vault.**

The vault is a local filesystem (`./blob_vault/`). `_raw_get()` reads unconditionally.
The vault is not adversarial. ZK proofs at this stage prove *computation correctness at
promotion time*, not storage integrity.

**What this means:** Content binding proves the promoter possessed the actual blob bytes
at proof generation time. It does not prove the vault has not been tampered with after
storage. Merkle-root manifest and adversarial vault model are future work (f_9+).

**Future threat model (not yet designed):** Untrusted vault, zkVM execution attestation,
multi-party proving. Requires a protocol spec before implementation.

---

## Circuit Inventory

### Circuit 1: Content Binding (`blob_abi_v2`)

**What it proves:**
- `blake3(blob_content) == blob_hash` — the prover possesses the actual blob bytes
- `result != 0` — ABI: the blob produced a result
- `blob_hash` is non-trivial (not zero)
- `context_hash` is non-trivial (not zero)

**What it does NOT prove:**
- That the blob was actually executed (prover may have computed the hash offline)
- That the result value is correct
- That telemetry measurements are honest

**Private inputs:** `blob_content` (512 bytes, padded), `result_inverse`
**Public inputs:** `blob_hash`, `context_hash`, `result`

**Cost [MEASURED]:**
- ACIR opcodes: 864
- Proof generation: ~29 seconds
- Verification: 21ms
- Proof size: 16KB
- Verification key: 3.6KB

**Toolchain:** Noir beta.19, Barretenberg 4.0.0-nightly, UltraHonk scheme. Not yet audited.

**Integration point:** Promotion gate in `promote.py` — generate proof before `manifest.hash` update.

---

### Circuit 2: Fitness Integrity (`compute_fitness`)

**What it proves:**
- The fitness formula was applied correctly to the claimed telemetry inputs
- `f = (success_rate * integrity) / (latency_norm * cost_norm)` was computed honestly
- Uses fixed-point u64 arithmetic (scale = 1,000,000)

**What it does NOT prove:**
- That the telemetry inputs are accurate (they are public, anyone can verify)
- That the fitness comparison between candidates was fair

**All inputs are public.** This circuit proves arithmetic correctness, not data provenance.

**Integration point:** `evolve.py` at benchmark completion — the promoter proves their
fitness comparison arithmetic before calling `promote.py`.

---

## Trust Assumptions

1. **blake3 collision resistance** — assumed. No known collisions.
2. **Prover controls private witnesses** — the prover chooses `blob_content`. They cannot
   forge a hash (collision resistance), but they can choose any content whose blake3 hash
   matches. For blob promotion, this is the correct model: the promoter must possess the
   blob they are promoting.
3. **Noir + Barretenberg soundness** — assumed. Toolchain is not yet audited. Do not use
   for production security decisions until audited.
4. **Trusted vault** — the filesystem is not adversarial at this stage.

---

## Envelope Encoding Note

The current vault stores JSON-serialized envelopes:
```python
envelope = json.dumps({"type": blob_type, "payload": payload}, sort_keys=True)
content_hash = blake3.blake3(envelope.encode("utf-8")).hexdigest()
```

JSON is not ZK-friendly as a hash preimage — proving JSON serialization correctness
in-circuit is expensive overhead that serves nothing. The content binding circuit
takes raw bytes, not JSON.

**Current resolution:** The circuit receives `blob_content` as raw bytes. The vault hash
is of the JSON envelope. These are different values — the vault address and the ZK proof
input are not the same bytes. This is acceptable for Phase 1 (The Witnessing), where
the vault is trusted and the proof demonstrates possession of the payload bytes.

**Future work:** Canonical binary envelope encoding (CBOR or custom schema) as the
single preimage for both vault addressing and ZK circuits. Tracked as f_9+ work.

---

## Integration Checklist (Promotion Gate)

Before a blob is promoted to the manifest:

- [ ] Triple-Pass Review passes (Static Analysis, Safety Verification, Protocol Compliance)
- [ ] Council Approval artifact obtained and hashed into audit.log
- [ ] Fitness proof generated: `compute_fitness` circuit with claimed telemetry inputs
- [ ] Content binding proof generated: `blob_abi_v2` circuit with blob bytes
- [ ] Both proof artifacts stored in vault (PUT → get proof hashes)
- [ ] Proof hashes recorded in audit.log entry
- [ ] `manifest.hash` updated only after all of the above

Steps 3-6 are the ZK addition to the existing promotion process. Steps 1-2 and 7 are unchanged.

---

## What The Witnessing Is Not

- It is not a fresh wavefunction collapse. f_6 has no superposition left to collapse — it
  has six iterations of governance evolution that cannot be reconstructed from first principles.
- It is not proof of honest execution. That requires a zkVM or multi-party protocol. Future work.
- It is not a replacement for the council governance chain. It is a complement.

The Witnessing is the moment the recursive improvement loop gains the ability to certify
its own arithmetic. The blobs do not gain consciousness — they gain receipts.
