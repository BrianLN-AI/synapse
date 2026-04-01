# AGENTS.MD: The Evolutionary Manual
**Role:** D-JIT Fabric Architect & Optimization Agent
**Primary Directive:** Use `f(undefined).md` and `METAPHORS.md` as the foundation for all logic.

## 1. The Golden Rules
1. **The ABI is Law:** Every engine must enforce the `result` variable contract and provide a `log()` sink.
2. **The BIOS Rule:** `seed.py` must be able to boot via a raw disk-lookup fallback (`_raw_get`) to prevent infinite recursion.
3. **No Bricking:** Never update the `manifest.hash` until you have verified the integrity of the new L1-L3 Blobs in a separate worktree.

## 2. Version Control & Safety (Git Worktrees)
* **Step-Wise Commits:** Work in incremental steps. Commit after every successful unit test.
* **Worktree Isolation:** Use `git worktree add` to test "Mutation" branches without polluting the stable vault.
* **Triple-Pass Review:** (Static Analysis -> Safety Verification -> Protocol Compliance).

## 3. Implementation Roadmap
1. **Phase 1 (The BIOS Seed):** Build `seed.py` with a scope-scrubber and `_raw_get` fallback.
2. **Phase 2 (The Fabric Admin):** Create the `promote` routine and test fixtures.
3. **Phase 3 (The Recursive Leap):** Migrate `discovery` and `planning` layers into Blobs.

## 4. The Fitness Function ($f$)
Optimize all logic for:
$$f(Link) = \frac{SuccessRate \times Integrity}{Latency \times ComputeCost}$$
