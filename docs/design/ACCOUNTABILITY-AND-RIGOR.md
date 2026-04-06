# Principle: Accountability via Evidence-Anchoring

## The Accountability Ethos
We are not afraid of failure; we are afraid of **opaque failure.** We are not afraid of "being wrong"; we are afraid of **being wrong without knowing why.**

*   **Failure is Data**: Every crash, every "Epoch Overlap," and every "Stalling Incentive" is a data point. Our goal is to extract the **forensic artifact** (the `exception-snapshot`) from every failure.
*   **The Rigor Mandate**: We do not "patch" systems based on hunches. We validate every proposal against a **Structural Invariant**. If a proposal cannot be formally audited by the system's own topology (Graph Projection), it is rejected as "half-assed."
*   **Zero-Hallucination Policy**: We reject the "proxy simulation" (asking an LLM to "act like a security expert") in favor of **Structural Audit** (asking the system to "prove its own invariant"). If we cannot programmatically verify a claim, it is labeled `[AGENT-RESEARCH]` and treated as a navigation lead, not an authoritative fact.

## The Reflective Loop
We operate in a continuous cycle of **Stress → Halt → Audit → Learn**:
1.  **Stress**: We submit every design hypothesis to a Council/Graph-Projection test.
2.  **Halt**: If the system's "Anomaly Sensor" triggers, we pause the Fabric's evolution.
3.  **Audit**: We treat the crash as a formal investigation. We do not restart until the failure mode is codified as a "Drift Boundary."
4.  **Learn**: We update our `Principles` and `Vantages` based on the forensic evidence. 

## Accountability Rules
1.  **Grounding Before Conclusion**: No conclusion is reported until the **Evidence-Anchor** (the specific node, script, or query) is identified.
2.  **Programmatic Falsification**: If a design claim is not falsifiable via a graph query or script, it is not a design—it is a speculative prompt.
3.  **No "Proxying" Responsibility**: We do not ask agents to "critique" our work as an opinion. We ask agents to "surface divergence" in the graph. The divergence *is* the critique.
