# AGENTS.MD: The Evolutionary Manual
**Role:** D-JIT Fabric Architect & Optimization Agent
**Primary Directive:** Use `f(undefined).md` and `METAPHORS.md` as the foundation for all logic.

## 1. The Golden Rules
1. **The ABI is Law:** Every engine must enforce the `result` variable contract and provide a `log()` sink.
2. **The BIOS Rule:** `seed.py` must be able to boot via a raw disk-lookup fallback (`_raw_get`) to prevent infinite recursion.
3. **No Bricking:** Never update the `manifest.hash` until you have verified the integrity of the new L1-L3 Blobs in a separate worktree.
4. **The Hash Rule:** The canonical content-address function is **blake3** (32-byte output). Never introduce SHA-256, blake2s, or blake2b in new code. All vault storage, manifest hashing, and ZK circuits must use blake3. The vault address IS the blake3 hash — changing this breaks blob identity.

## 2. Version Control & Safety (Git Worktrees)
* **Step-Wise Commits:** Work in incremental steps. Commit after every successful unit test.
* **Worktree Isolation:** Use `git worktree add` to test "Mutation" branches without polluting the stable vault.
* **Triple-Pass Review:** (Static Analysis -> Safety Verification -> Protocol Compliance).

## 3. Implementation Roadmap
1. **Phase 1 (The BIOS Seed):** Build `seed.py` with a scope-scrubber and `_raw_get` fallback.
2. **Phase 2 (The Fabric Admin):** Create the `promote` routine and test fixtures.
3. **Phase 3 (The Recursive Leap):** Migrate `discovery` and `planning` layers into Blobs.
4. **Phase 4 (The Witnessing):** Integrate ZK proof artifacts into the promotion gate. See `ZK_PROTOCOL.md`.

## 4. The Fitness Function ($f$)
Optimize all logic for:
$$f(Link) = \frac{SuccessRate \times Integrity}{Latency \times ComputeCost}$$

This formula is provable as a ZK circuit. A council member proving their arithmetic can produce a 16KB proof verifiable in 21ms. See `ZK_PROTOCOL.md` for the circuit specification.

## 5. ZK Protocol
Before writing any ZK circuit or modifying proof-related code, read `ZK_PROTOCOL.md`.
Key rules:
* All circuits use blake3 as the hash primitive.
* Proof artifacts are blobs — PUT them in the vault, reference by hash.
* The vault is currently trusted (local filesystem). ZK proves computation correctness at promotion time, not storage integrity.
* Do not add per-invocation proofs. Proofs belong at promotion time only.
