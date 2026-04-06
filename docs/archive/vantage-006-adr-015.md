# Vantage Experiment 006: ADR-015 Multihash Address Format

**Date:** 2026-04-06
**Artifact:** ADR-015 (Multihash Address Format)
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

**ADR-015: Multihash Address Format**
- Address = `function_id | digest_length | digest_bytes` (prefixed)
- String form: `blake3:af1349...`
- Binary form: `[varint: function_id][varint: length][bytes: digest]`
- Solves: ZK layer divergence, cross-system federation, migration
- Hash-bridge expression: links vault address to ZK address
- Bootstrap property: address carries its own decoding instructions
- Backward compatible: old 64-char hex treated as implicit blake3

---

## Vantage Probes

### Protocol Designer (Interop) → `PRO-002` `[UNTRAINED]`

**Components seen:** Protocol negotiation, wire format, backward compatibility, extensibility

Multihash = protocol negotiation on wire. function_id = protocol version. Hash-bridge = protocol translator. Bootstrap property = self-describing protocol. Backward compat = graceful degradation.

**Rationalization:** → See §Rationalization

---

### Network Scientist (Addressing) → `NET-002` `[UNTRAINED]`

**Components seen:** Naming, routing, addressing vs location, namespace

Content-addressed = naming without location. Multihash = namespace with protocol. function_id = namespace identifier. Federation = cross-namespace resolution. Bootstrap = root namespace.

**Rationalization:** → See §Rationalization

---

### Semiotician (Sign) → `SEM-001` `[UNTRAINED]`

**Components seen:** Signifier, signified, index, symbol, interpretant

Address = signifier. Content = signified. Prefix (function_id) = index (points to decoding method). Hash-bridge = translation between sign systems. Self-describing address = symbol that contains its own interpretant.

**Rationalization:** → See §Rationalization

---

### Librarian (Cataloging) → `LIB-001` `[UNTRAINED]`

**Components seen:** Catalog, classification, shelf mark, provenance

Address = shelf mark. function_id = classification scheme. Hash-bridge = cross-reference. Self-describing = catalog record that describes itself. Federation = inter-library loan.

**Rationalization:** → See §Rationalization

---

## Vantage Conflicts

| # | Conflict | Vantage A | Vantage B | Status |
|---|----------|-----------|-----------|--------|
| 1 | Address: label vs location | Network | Librarian | Network: naming; Librarian: cataloging |
| 2 | function_id: namespace vs classification | Network | Librarian | Same concept, different framing |
| 3 | Self-describing: feature vs complexity | Protocol | Network | Protocol: necessary for interop; Network: adds overhead |
| 4 | Binary vs string: machine vs human | Protocol | Librarian | Protocol: binary for circuits; Librarian: string for humans |

---

## Transformation Rules (Hypotheses) → `TR-006` `[UNTRAINED]`

```
pro.wire_format = net.naming × sem.signifier
lib.classification = net.namespace × sem.index
sem.interpretant = lib.provenance × pro.bootstrap
net.routing = pro.negotiation × lib.inter_library_loan
```

---

## Invariant Candidates → `INV-006` `[UNTRAINED]`

1. **Address must be self-describing** — no external context needed to verify
2. **function_id is the shared language** — two systems agree on prefixes, not on everything
3. **Hash-bridge is explicit** — relationships between address spaces are stored, not assumed

---

## Rationalization

### PRO-002: Protocol Designer probe of multihash

**Projection:** Multihash as protocol negotiation, prefix as version, hash-bridge as translator.

**Why:**
- Protocol negotiation: parties agree on encoding before exchanging messages
- function_id = which protocol/encoding to use
- Hash-bridge = explicit translation between protocols
- Self-describing = protocol doesn't require out-of-band context

**Weaknesses:**
- Protocol negotiation usually happens at handshake — multihash embeds it in every address
- This is more like "self-describing protocol" than negotiation

---

### NET-002: Network Scientist probe of multihash

**Projection:** Content addressing = naming without location, function_id = namespace.

**Why:**
- Content-addressed storage (IPFS) uses exactly this model
- Multihash extends it with explicit namespace (function_id)
- Federation = cross-namespace resolution
- Hash-bridge = explicit pointer between namespaces

**Weaknesses:**
- This is almost verbatim what the ADR says
- I'm narrating, not probing

---

### SEM-001: Semiotician probe of multihash

**Projection:** Address as signifier, content as signified, prefix as Peirce's index.

**Why:**
- Peirce: index = sign that physically connects to what it signifies
- function_id physically points to the decoding algorithm
- Self-describing address = sign that tells you how to interpret it = rare in natural language
- Hash-bridge = translation between sign systems

**Weaknesses:**
- Semiotics is a interpretive discipline — projections are inherently subjective
- "Index" in semiotics is not the same as "pointer" in CS
- This might be too metaphorical to be useful

---

### LIB-001: Librarian probe of multihash

**Projection:** Address as shelf mark, function_id as classification scheme.

**Why:**
- Libraries have classification systems (Dewey, Library of Congress)
- Shelf mark = address on shelf = content address
- function_id = which classification system
- Hash-bridge = cross-reference in catalog

**Weaknesses:**
- Library classification is hierarchical; multihash is flat
- "Federation = inter-library loan" is a loose analogy

---

## Notes

- ADR-015 is about interoperability — the vantages agree strongly
- The "bootstrap property" (self-describing address) is the key invariant
- No strong conflicts — vantages mostly converge
- Semiotician and Librarian are new vantage types I hadn't mapped before

---

## Cross-Reference

- Compare to ADR-001: both about addressing and naming
- ADR-001: hash function choice; ADR-015: address format
- Together: how to name things (ADR-001) and how to express addresses (ADR-015)
