# ADR-018: Namespace-Based Projections (The Clean Room)

**Status:** Accepted
**Vantage:** [ADVERSARY] / [BUILDER]

## Context
Initial implementations used a monolithic `system` object and ambient authority, allowing AI code to potentially collide with or leak into the Arbiter's scope (e.g., the `const result` collision).

## Decision
Transition to a Namespace-based Projection model. The Arbiter projects distinct, isolated proxies (`fabric`, `world`, `ai`) and explicitly nullifies host-level globals (`console`, `fetch`, `process`).

## Consequences
- Hardens the ABI contract by removing variable name collisions.
- Aligns with the Cloudflare "Code Mode" dispatcher pattern.
- Enables granular governance (e.g., a node can have `fabric` access but no `ai` access).
