# ADR-019: 4-Phase Mutation Lifecycle for Autonomous Growth

**Status:** Accepted
**Vantage:** [JURIST] / [PHYSICIST]

## Context
Autonomous code generation ("Imagine") poses a risk of "bricking" the World if bad logic is promoted to the Root label.

## Decision
Encode a mandatory 4-phase lifecycle into the `imagine` verb logic:
1. **Plan:** AI generates the mutation.
2. **Audit:** A second AI reviews for ABI safety.
3. **Trial:** A dry-run execution in a transient isolate.
4. **Promote:** Update the label only if all phases pass.

## Consequences
- Prevents invalid or unsafe code from reaching the stable Route (Root).
- Establishes a "Safe Feedback Loop" for self-modifying logic.
- Creates a permanent audit trail of failed and successful trials in the substrate.
