# ADR-015: Multihash Address Format

**Date:** 2026-04-02
**Status:** Accepted — implemented in f_16 (council/f_16, v1.16.0)
**Supersedes:** ADR-001 (partially — address encoding; blake3 as canonical vault hash retained)
**Superseded by:** —

---

## Context

Vault addresses are currently 64-character blake3 hex strings with no self-description.
An address like `af1349b9...` carries no information about which hash function produced
it. The function is assumed globally: everything in the vault is blake3.

This assumption breaks in three scenarios:

**1. ZK layer divergence.** The optimal hash for in-circuit ZK computation (Poseidon,
~10x fewer constraints than blake3) is different from the optimal hash for general-purpose
vault addressing (blake3, fast, widely available). When vault hash ≠ ZK hash, there is
no way to encode both addresses without an out-of-band convention.

**2. Cross-system federation.** Two systems that federated independently may have chosen
different hash functions. Their addresses are opaque to each other — you cannot even
determine if an address from System A is verifiable without knowing A's hash function
through external means.

**3. Migration.** Moving from one hash function to another requires re-keying every
expression in the vault. Without self-describing addresses, you cannot have a mixed vault
during migration — the transition is flag-day, not gradual.

IPFS solved this problem in 2014 with multihash: encode the function identifier and digest
length as a prefix of every address. The address is self-describing — no external context
required to verify it. [CITED — Protocol Labs, multihash specification, 2014]

---

## Decision

**Adopt multihash as the canonical address format.**

An address encodes three fields:

```text
address = function_id | digest_length | digest_bytes
```

**String representation** (canonical, human-readable):

```text
<function-prefix>:<hex-digest>

blake3:af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262
sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
poseidon:7f3c21...
```

**Binary representation** (for compact storage and ZK circuits):

```text
[varint: function_id][varint: digest_length_bytes][bytes: digest]
```

**Canonical function codes** (aligned with IPFS multicodec table):

| Function | String prefix | Code | Digest length |
|---|---|---|---|
| blake3 | `blake3` | 0x1e | 32 bytes |
| sha2-256 | `sha256` | 0x12 | 32 bytes |
| poseidon-bls12_381 | `poseidon` | 0xb401 | 32 bytes |

The string prefix form is canonical for human use and storage. The binary form is used
in ZK circuits and compact encodings.

**Vault hash vs ZK hash — explicit separation:**

The vault uses one hash function (canonical: blake3). ZK circuits may use a different
hash function (canonical for Ethereum ZK ecosystem: Poseidon). Both are valid multihash
addresses. When they diverge, a hash-bridge expression in the vault makes the relationship
explicit:

```json
{
  "type": "meta/hash-bridge",
  "payload": {
    "vault_address": "blake3:af1349b9...",
    "zk_address":    "poseidon:7f3c21...",
    "proof":         "<zk-proof-that-both-hash-same-content>"
  }
}
```

The hash-bridge expression is itself a vault expression with a blake3 address.

**The KEY invariant updated:**

```text
address = multihash(envelope)
        = function_id | digest_length | digest_bytes

vault canonical:   blake3 (0x1e)
zk canonical:      blake3 (Noir) | poseidon (Halo2/Circom)
federation:        agree on function_id, or store hash-bridge expressions
```

**Backward compatibility:**

Existing addresses (`af1349b9...`, 64 hex chars) are treated as implicit
`blake3:<address>`. The prefix is assumed when absent. New addresses use the explicit
prefix form. The vault can contain both; callers that understand multihash handle both.

---

## Alternatives Considered

### Keep 64-char blake3 hex (current)

- **Pro:** Simple, no change required, no parsing overhead
- **Con:** Cannot distinguish blake3 from sha256 addresses at read time
- **Con:** Blocks federation with systems using different hash functions
- **Con:** Requires flag-day migration if hash function ever changes
- **Verdict:** Rejected. The limitations compound as the system scales.

### Separate address spaces per hash function

- **Pro:** No encoding change; just use different vault directories
- **Con:** Requires external routing logic to know which space an address belongs to
- **Con:** Cross-hash-function references require out-of-band convention
- **Verdict:** Rejected. Self-describing addresses are strictly cleaner.

### Use IPFS CIDs directly

- **Pro:** Standard, tooling exists, interoperable with IPFS ecosystem
- **Con:** CIDs include content type and version fields beyond hash function — more than we need
- **Con:** Introduces IPFS as a dependency or reference implementation
- **Verdict:** Rejected as the direct format; adopted as the design reference. Our multihash
  encoding is a subset of the CID concept, not a full adoption.

---

## Consequences

**Immediate:**

- `vault.put(type, payload)` returns `blake3:<hex>` (prefix added)
- `vault.get("blake3:<hex>")` works; `vault.get("<hex>")` still works (backward compat)
- Hash-bridge expression type `meta/hash-bridge` is defined
- Address comparison must strip or normalize the prefix before comparing

**Ongoing:**

- ZK circuits that need Poseidon addressing can store expressions at both addresses with
  a hash-bridge linking them
- Federation between systems: the function_id is the shared language — two systems agree
  to recognize addresses from the same function_id without needing to agree on everything else
- Migration between hash functions is gradual: add new addresses, maintain both, deprecate old

**The bootstrap property:**
An address is self-describing. A new party joining the network reads any address, extracts
the function ID, looks up the algorithm, verifies the content. No external context required.
This is the golden record property: the address carries its own decoding instructions.

---

## Evidence Basis

- **[CITED]** IPFS multihash specification, Protocol Labs (2014): `<hash-func-type><digest-length><hash-digest>`
- **[CITED]** IPFS multicodec table: blake3 = 0x1e, sha2-256 = 0x12
- **[MEASURED]** Current addresses: 64-char blake3 hex, no function prefix
- **[INFERRED]** Multihash enables gradual migration, federation, and ZK/vault hash divergence
- **[MEASURED]** blake3 test vectors (Python blake3 package, verified 2026-04-02):
  - `blake3:af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262` ← blake3(b"")
  - `blake3:6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85` ← blake3(b"abc")
  - `blake3:2a43e6bf5d7dfe202bf9653c94aacb221a20cd5e449602684d9ffbd38d9a8920` ← blake3(bytes(range(251)))
