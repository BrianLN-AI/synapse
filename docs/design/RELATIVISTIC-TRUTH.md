# Principle: Relativistic Truth (The Observer-Dependency Principle)

## Definition
Truth is not a global invariant; it is a **Vantage-Dependent Projection**. The state of the system is only verifiable from a specific perspective (the vantage) and at a specific state (the epoch).

## The Principle
*   **Truth is an Observer-Dependency**: There is no "God-View" of the Fabric. A claim like "ADR-013-V3 is safe" is meaningless unless qualified by the vantage ("as seen from the Graph-Projection Audit") and the state ("as of block $H$").
*   **Truth as Structural Invariant**: We do not seek "The Truth." We seek **Structural Invariants** that hold across a specified range of system states. If an invariant holds from $H_0$ to $H_n$, it is "true" for that epoch.
*   **The Anti-Dogma**: We reject universalizing claims. We explicitly document the **vantage** (the lens, the agent, the query) used to verify any finding. If two agents (e.g., Categorist vs. Protocol) report divergent findings, that divergence is **not a conflict to be resolved**; it is the **truth of the system** at that specific vantage.

## How this changes our work:
1.  **Vantage-Explicit Rationalization**: No finding is presented as "The System is X." It is presented as: "From the perspective of [Vantage], and under the invariants of [State], the system projects as X."
2.  **Divergence as Signal**: When our Council (or Audit) produces conflicting results, we do not force synthesis. We map the divergence as a "System Property"—it tells us the system is behaving differently depending on the vantage (e.g., the security agent sees a hijack, the protocol agent sees a deadlock).
3.  **The End of "Universals"**: We stop using words like "safe," "correct," or "perfect." We use "verifiable within [Vantage]," "resilient against [Failure Mode]," or "consistent with [State Invariant]."

## Implementation Rule
*   Every Audit report must begin with: **Vantage:** [Lens Name], **State:** [Epoch/Block/Hash].
*   If we find two conflicting "truths," we create a `vantage-map` in the graph to document *why* they diverge, rather than choosing one.
*   The system is an ensemble of perspectives; its "truth" is the interaction of those perspectives.
