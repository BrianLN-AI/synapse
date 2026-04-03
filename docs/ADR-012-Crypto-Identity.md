# ADR 012: Cryptographic Identity Substrate

**Status:** Proposed  
**Context:** We move from simulated node IDs ('node-A') to verifiable Ed25519 public/private key pairs.

## 1. Decision
Every Synapse Node will generate and manage a persistent cryptographic identity.

## 2. Technical Specification

### Key Storage
Keys are stored in a restricted `keys/` directory within the node's root.
- `identity.pub`: The public identity shared with the collective.
- `identity.key`: The private key used for signing.

### New Primitives
- `crypto_sign(data) -> signature`
- `crypto_verify(data, signature, pubkey) -> bool`

### Identity Artifact
When a node joins the collective, it `PUTs` an **Identity Blob** containing its public key and current `capabilities`.

## 3. Benefits
- **Unforgeable Providence**: Every blob lineage is signed by the author's private key.
- **Secure Governance**: Tallying signatures now requires cryptographic verification of the voter's identity.
- **Encrypted State**: Foundation for future Phase 4 (Privacy) where state can be encrypted for specific public keys.
