# Architectural Decision Records

This directory contains the records for the D-JIT Fabric's evolution.

## Active Foundation
These records apply directly to the current **Codemode** lineage (`explore/codemode-proxy`):

- **ADR-001/015**: [Identity] BLAKE3 and Multihash addressing.
- **ADR-002**: [ABI] Scrubbed-scope `context`/`result` contract.
- **ADR-004**: [Substrate] Content-addressed persistent storage.
- **ADR-005**: [Recursion] `f(n) = f(n-1)(f(n-1))` protocol.
- **ADR-017**: [Identity] Deep-stable hashing for nested structures.
- **ADR-018**: [Projection] Namespace-based isolated proxies.
- **ADR-019**: [Verification] 4-phase autonomous mutation lifecycle.

## Ancestral Records
Decisions from previous generations (f_0-f_20) that are currently out of scope for the functional re-bootstrap but may be re-integrated later are stored in [`ancestral/`](./ancestral/).
