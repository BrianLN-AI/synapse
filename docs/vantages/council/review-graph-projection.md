# Vantage: Graph-Projection Audit

This vantage governs how we analyze proposed protocols (e.g., `ADR-013-V3`). 

## 1. The Audit Protocol
When evaluating a proposal, follow these steps:
1. **Identify High-Entropy Signal (Human Input)**: Start with the human "feeling" of risk.
2. **Topological Mapping**: Create a graph projection (`ugs query` or `traversal`) that visualizes the risk.
3. **Formal Invariant Check**: Assert the invariant (e.g., `assert(governance_epoch_N.next == governance_epoch_N_plus_1)`) against the proposed design.
4. **Collision Detection**: If the projection shows a violation of the invariant, the audit *fails*. 

## 2. Evaluation Standards
*   **Is it deterministic?** Does the protocol rely on a time-window (`duration_blocks`)? If yes, it *fails* (Non-deterministic authority).
*   **Is it Self-Validating?** Does the `transition-proof` explicitly link the new governance epoch to the revoked state of the old? If no, it *fails* (Root of Trust hijack).
*   **Is the "Kill Switch" Programmable?** Can we programmatically detect the failure condition? If no, the experiment is not falsifiable.
