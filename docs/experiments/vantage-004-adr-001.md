# Vantage Experiment 004: ADR-001 blake3 Canonical Hash

**Date:** 2026-04-06
**Artifact:** ADR-001 (blake3 as Canonical Content-Address Hash)
**Method:** Back-of-envelope probe
**Status:** Draft — hypotheses only

---

## Provenance Tags

| Tag | Meaning |
|-----|---------|
| `[UNTRAINED]` | LLM projection, no domain expertise |
| `[TRAINED]` | Grounded in training data / literature |
| `[EXPERT-VALIDATED]` | Verified by domain expert |
| `[DISAGREES]` | Expert contradicts projection |

---

## The Artifact

**ADR-001: blake3 as Canonical Hash**
- Chose blake3 over SHA-256, blake2s, blake2b, Poseidon
- Reason: ZK circuit compatibility (Noir beta.19 stdlib)
- SHA-256 not available as complete hash in Noir stdlib (only compression primitive)
- blake3 is the intersection of: Python stdlib, Noir stdlib, cross-platform availability
- Key invariant: vault address IS the blake3 hash
- Known gaps: O2 circuit still uses blake2s, JSON envelope not ZK-friendly

---

## Vantage Probes

### Information Theorist (Entropy) → `INF-001` `[UNTRAINED]`

**Components seen:** Collision resistance, entropy, compression, channel capacity

Hash = maximally compressing identifier. blake3 chosen for ZK = choosing function that minimizes circuit complexity = minimizes channel bandwidth for proof verification. Collision resistance = Shannon entropy bound on predictability.

**Rationalization:** → See §Rationalization

---

### Cryptographer (Commitment Scheme) → `CRY-001` `[UNTRAINED]`

**Components seen:** Binding, hiding, commitment, random oracle

Content-addressed hash = perfect commitment scheme. Binding: cannot find two contents with same hash (collision resistance). Hiding: hash reveals nothing about content (pre-image resistance). Self-sealing manifest = hash-and-commit.

**Rationalization:** → See §Rationalization

---

### Physicist (Irreversibility) → `PHY-002` `[UNTRAINED]`

**Components seen:** Entropy increase, arrow of time, irreversibility, thermodynamic cost

Hash = information destruction (entropy increase). blake3 chosen over reversible operation = arrow of time. Manifest self-sealing = entropy of system increases. ZK circuit compatibility = minimizing thermodynamic cost of proof verification.

**Rationalization:** → See §Rationalization

---

### Network Scientist (Naming) → `NET-001` `[UNTRAINED]`

**Components seen:** Naming, address, location independence, routing

Content-addressed = location-independent naming. Hash = stable identifier that doesn't depend on where content lives. This is the key insight of IPFS/Content-Addressed储物.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Hash as compression vs commitment | Information Theorist | Cryptographer | Same function, different framing |
| 2 | blake3 for ZK: efficiency vs purity | Physicist | Cryptographer | Efficiency wins in practice |
| 3 | Collision resistance: how much is enough? | Information Theorist | Cryptographer | Different security bounds |
| 4 | Self-sealing: feature vs overhead | Network | Physicist | Network sees it as naming; Physicist as entropy cost |

---

## Transformation Rules (Hypotheses) → `TR-004` `[UNTRAINED]`

```
cry.commitment_scheme = inf.maximum_compression × net.naming_stability
phy.entropy_cost = cry.collision_resistance × inf.channel_bandwidth
net.address = cry.binding × phy.irreversibility
```

---

## Invariant Candidates → `INV-004` `[UNTRAINED]`

1. **Hash function is a protocol commitment** — changing it requires migration
2. **Content address = name is stable** — address doesn't change if content moves
3. **ZK compatibility constrains the hash** — not all hash functions are equal for circuits

---

## Rationalization

### INF-001: Information Theorist probe of blake3

**Projection:** Hash as compression, ZK compatibility as channel bandwidth minimization.

**Why:**
- Hash = maximally compressing identifier (32 bytes = any-size content)
- ZK circuits are about proof transmission = channel capacity
- Choosing blake3 for circuit efficiency = minimizing proof size = maximizing channel capacity

**Weaknesses:**
- "Compression" is misleading — hash loses information intentionally
- ZK circuit cost is about constraint count, not bandwidth
- I may be conflating information theory with compression theory

---

### CRY-001: Cryptographer probe of blake3

**Projection:** Hash as commitment scheme, manifest self-sealing as hash-and-commit.

**Why:**
- Commitment scheme: binding + hiding = hash properties
- Content-addressed blobs are literally perfect commitment schemes
- Self-sealing manifest = commit to current state, prove you haven't changed it

**Weaknesses:**
- Commitment schemes involve a reveal phase — content-addressed hashes don't have that
- I'm stretching the analogy
- The ZK context adds a third property (proof) that standard commitment doesn't have

---

### PHY-002: Physicist probe of blake3

**Projection:** Hash as entropy increase, blake3 choice as minimizing thermodynamic cost.

**Why:**
- Hashing is irreversible = entropy increase = thermodynamic arrow of time
- ZK proof verification is computation = thermodynamic cost
- Choosing blake3 = choosing function with lowest energy cost for verification

**Weaknesses:**
- Modern hash functions aren't thermodynamically expensive
- This framing is too metaphorical
- "Thermodynamic cost of computation" is a real concept (Landauer limit) but blake3 vs SHA-256 doesn't approach that limit

---

### NET-001: Network Scientist probe of blake3

**Projection:** Content address as location-independent naming.

**Why:**
- IPFS uses content addressing for exactly this reason
- Hash = stable identifier that doesn't depend on storage location
- Federation requires this stability

**Weaknesses:**
- This is the most straightforward mapping — almost tautological
- Not much insight added

---

## Notes

- ADR-001 is about infrastructure choice, not behavior — fewer vantage conflicts
- The ZK constraint is the key differentiator — vantages mostly agree that blake3 is the right choice
- "Hash function is a protocol commitment" is the most robust invariant — it's true across all vantages
