# Vantage Probe: ADR-013 (Governance as Expression)
**Method:** Registry-Based Probe (v0.1)
**Vantages:** Economist, Security

---

## 1. Economist Probe (Price Signals & Incentives)

**Core Axioms Applied:** Price discovery, regulatory oversight

**Diagnostic Questions & Findings:**
1. **Incentive:** "Who has the incentive to behave correctly?"
   * **Finding:** Reviewers (in `council/reviewer` blob) have "Trust Weight". If they approve a "Proof Governance" blob (which reduces manual labor), they increase their own efficiency. [Incentive: Efficiency gain]
2. **Price Signal:** "What is the price signal for quality?"
   * **Finding:** The `trust_weight` (which decays) acts as a price signal. High-trust reviewers = "expensive" high-quality signal.
3. **Manipulation:** "Is there manipulation potential?"
   * **Finding:** Yes. If a reviewer holds all keys, they can pass "Proof Governance" blobs that relax constraints. [Regulation: Thresholds needed]

**Conflict Signature:** Risk of "regulatory capture" where a high-trust reviewer lowers the threshold for their own benefit.

---

## 2. Security Probe (Attack Surface & Auditability)

**Core Axioms Applied:** Trust anchors, Auditability

**Diagnostic Questions & Findings:**
1. **Trust Anchor:** "Where is the trust anchor? Is it self-grounding?"
   * **Finding:** The "Bootstrap Case" (genesis governance) is the anchor. It is self-grounding. [Risk: Single point of failure]
2. **Impact:** "What is the impact of a compromised reviewer?"
   * **Finding:** A compromised reviewer can change the governance type to something less restrictive, effectively "poisoning" the evolution path.
3. **Auditability:** "Is the chain of custody verifiable?"
   * **Finding:** Yes. Because governance expressions are content-addressed blobs, we can audit the evolution of the governance type over time.

**Conflict Signature:** Vulnerable to a "Trust Anchor Hijack" at the genesis stage.

---

## 3. Translation Table (v0.1: Economist ↔ Security)

| Economist Concern | Security Mapping | Resolution/Conflict |
|-------------------|------------------|--------------------|
| Incentive Alignment | Auditability | Economists want incentives; Security wants proof. |
| Manipulation Potential | Trust Anchor Vulnerability | Security sees "Hijack"; Economist sees "Arbitrage." |

---

## Learnings (Synthesized)

*   **Convergence:** Both vantages identify the "Genesis Anchor" as the critical point of failure.
*   **Conflict:** The Economist sees "Regulatory Capture" (Reviewer sets the threshold to benefit themselves), while the Security Specialist sees "Root of Trust Hijack" (Reviewer changes the rules to subvert the system).
*   **Transformation:** We can map Economist "Incentive Alignment" → Security "Auditability" — if you have perfect auditability, you can force incentives through penalization.

---

**Does this look like the right level of "modeled expertise" vs. "simulation"?** If yes, we can start using this template for every ADR.
