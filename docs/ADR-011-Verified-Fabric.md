# ADR 011: The Verified Fabric (ZK-Proofs for Compute)

**Status:** Proposed  
**Context:** Current fabric operations rely on 'Blind Trust' of remote nodes. f_11 requires cryptographic proof that a requested piece of code was executed correctly and produced the claimed result.

## 1. Decision
We will integrate a **Prover/Verifier** pattern into the D-JIT 4-layer stack. 

## 2. Technical Specification

### New Primitive: `verify_proof(proof, hash, result) -> bool`
The Linker will provide a primitive to validate ZK-Proof artifacts.

### The Proof Artifact
A specialized JSON blob stored in the vault:
```json
{
  "type": "zk_proof",
  "blob_hash": "...",
  "result_hash": "...",
  "proof_data": "...",
  "prover_pubkey": "..."
}
```

### Protocol Flow
1.  **Arbitrage (L3)**: Identifies a 'High-Integrity' requirement.
2.  **Dispatch (L4)**: Routes the task to a node with the `prover` capability.
3.  **Synthesis (Prover)**: Runs the blob inside a zkVM and generates the proof.
4.  **Verification (Linker)**: Local Linker verifies the proof before committing state.

## 3. Implementation Phases
- **Phase 1 (Simulation):** Implement the Linker primitives with a mock prover that uses digital signatures as a 'Commitment' to correctness.
- **Phase 2 (Integration):** Integrate a real SNARK/STARK library (e.g., Risc0 or SP1) to generate physical proofs.
