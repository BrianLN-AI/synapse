# ADR-017: Deep-Stable Hashing for Content Identity

**Status:** Accepted
**Vantage:** [MATHEMATICIAN]

## Context
During f_0 iteration, a collision vulnerability was found where shallow key-sorting in the hashing function allowed structural changes to nested objects (like `verbs`) to go undetected, resulting in the same BLAKE3 hash for different system states.

## Decision
Implement a deep-stable stringification algorithm that recursively sorts all keys in a JSON object before hashing.

## Consequences
- Guaranteed unique identities for any structural change in the World graph.
- Hardens Invariant I: Address = Multihash(Content).
- Increases hashing latency slightly but ensures substrate integrity.
