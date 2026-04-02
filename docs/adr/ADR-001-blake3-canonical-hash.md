# ADR-001: blake3 as Canonical Content-Address Hash Function

**Date:** 2026-04-01
**Status:** Accepted — decision made; code migration pending (tracked separately)
**Supersedes:** SHA-256 usage in ADR-003 (manifest hash) and ADR-004 (vault address)
**Superseded by:** —

---

## Context

The D-JIT Logic Fabric is content-addressed: a blob's identity IS its hash. The vault
stores blobs at `./blob_vault/<hash>`, the manifest seals itself with its own hash, and
telemetry artifacts are referenced by hash throughout the governance chain.

The original genesis spec (`f(undefined).md` v1.0–1.2) specified SHA-256 for content
addressing. This was the default choice — widely supported, well-understood, no special
justification recorded.

When ZK proof integration was explored (zk-explore/, O1 and O2 circuits), a constraint
emerged: the ZK circuit must recompute `hash(blob_content)` inside the circuit to prove
content binding. This requires a hash function available as a native primitive in the
chosen ZK toolchain (Noir beta.19 / Barretenberg UltraHonk).

SHA-256 is not available as a complete hash function in Noir beta.19's stdlib — only
`Sha256Compression` (a block compression primitive) is exposed. Using it would require
manually implementing SHA-256's padding and finalization in-circuit: significant complexity
with no benefit over switching hash functions.

This forced a deliberate choice of hash function across the entire stack.

---

## Decision

**Use blake3 as the single canonical hash function for all content addressing, manifest
hashing, and ZK circuits.**

The vault address IS the blake3 hash. All new code uses blake3. SHA-256 is not permitted
in new code.

---

## Alternatives Considered

### SHA-256
- **Pro:** Universal — every ZK toolchain supports it; existing vault data uses it
- **Con:** Not available as a complete hash in Noir beta.19 stdlib (only block primitive)
- **Con:** Slower than blake3 on modern 64-bit hardware
- **Verdict:** Rejected for new code. Would require manual in-circuit implementation.
  Migration path: supersede this ADR when SHA-256 becomes available in Noir stdlib.

### blake2s
- **Pro:** Available in Noir beta.19 as `std::hash::blake2s`; in Python stdlib as `hashlib.blake2s`
- **Pro:** 32-byte output (same interface as SHA-256)
- **Con:** Optimized for 32-bit and constrained environments — suboptimal on 64-bit platforms
- **Con:** blake3 supersedes it in every dimension on modern hardware
- **Note:** O2 circuit (`blob_abi_v2`) was built with blake2s. This is a known gap — the
  circuit must be updated to blake3 to align with the vault hash function.
- **Verdict:** Rejected as canonical. Used in O2 circuit temporarily; migration to blake3 pending.

### blake2b
- **Pro:** In Python stdlib as `hashlib.blake2b`; optimized for 64-bit platforms
- **Pro:** Configurable output size (`digest_size=32` gives 32-byte output)
- **Con:** Not confirmed available in Noir beta.19 stdlib (only blake2s and blake3 confirmed)
- **Con:** 64-bit optimization advantage does not transfer to ZK circuit complexity
- **Verdict:** Rejected. No ZK toolchain alignment confirmed.

### Poseidon / MiMC (ZK-native hash functions)
- **Pro:** Designed for ZK circuits — dramatically fewer constraints than any general-purpose hash
- **Pro:** Standard in Ethereum ZK ecosystem (zkSync, Aztec, StarkWare)
- **Con:** Not in Python stdlib or blake3 pip package — would require custom implementation
- **Con:** Not a general-purpose hash — unsuitable as a vault content-address function
- **Con:** Splits the hash function: ZK layer uses Poseidon, vault uses something else
- **Verdict:** Future consideration for deep ZK-native recursion (f_9+). Not a drop-in replacement.
  If Poseidon becomes necessary, the right answer is dual-hash (vault = blake3, ZK = Poseidon)
  with a cross-reference, not a vault migration.

---

## Consequences

**Planned (not yet implemented — code still uses SHA-256 as of v1.11.0):**
- `seed.py:104` — replace `hashlib.sha256` with `blake3.blake3` (pip install blake3)
- `promote.py:57` — replace `hashlib.sha256` with `blake3.blake3`
- Vault migration: re-key existing blobs from SHA-256 to blake3 addresses (migration script needed)
- O2 circuit (`zk-explore/blob_abi_v2`): replace `std::hash::blake2s` with `std::hash::blake3`
- `f(undefined).md` updated to v1.3.0 to reflect blake3 in the Discovery layer

**Ongoing:**
- All agents bootstrapped from `f(undefined).md` or `AGENTS.md` will use blake3 by default
- blake3 pip package is a new runtime dependency (not in Python stdlib)
- New ZK circuits must use `std::hash::blake3` as the hash primitive

**Known gaps at time of this decision:**
- O2 circuit still uses blake2s — not yet migrated (tracked in f_7 work)
- JSON envelope as hash preimage is not ZK-friendly — future work to define canonical binary
  encoding (see ZK_PROTOCOL.md, Envelope Encoding Note)
- Vault migration script not yet written

**Future supersession triggers:**
- SHA-256 becomes available as a complete hash in Noir stdlib
- Poseidon becomes necessary for recursive ZK circuits
- blake3 collision or weakness discovered

---

## Evidence Basis

- **[MEASURED]** Noir beta.19 stdlib: `std::hash::blake3` available, `std::hash::blake2s` available,
  `std::hash::sha256` not available (only `Sha256Compression`)
- **[MEASURED]** O2 circuit with blake2s: 864 ACIR opcodes, 29s proving, 21ms verification
- **[MEASURED]** blake3 available cross-platform: Python (pip), Node (npm), Rust (crates.io),
  browser (WASM), Cloudflare Workers, AWS Lambda
- **[MEASURED]** Erlang: no blake3 support (OpenSSL algorithms only)
- **[AGENT-RESEARCH]** blake3 circuit implementations exist for Halo2/PSE and Circom communities
- **[INFERRED]** blake3 circuit complexity likely lower than blake2s (simpler compression function)
  — not yet measured; O3 work will produce the opcode count
