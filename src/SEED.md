# Seed Linker: Formal Capability Model

**Version:** 1.0.0
**Role:** The BIOS (Basic Input/Output System) of the D-JIT Fabric.

## 1. Execution Contract (The ABI)
The Linker ensures a "Scrubbed Scope" for all Blobs.

### Inputs
- `context`: The request envelope (intent, params, metadata).
- `log(msg)`: The telemetry sink.
- `state`: Persistent memory object.
- `execution_plan`: The brokered plan.

### Cognitive Primitives
- `inference(prompt) -> str`: Reasoning engine.
- `embed(text) -> vector`: Semantic mapping.
- `rerank(query, candidates) -> hash`: Semantic selection.

### Administrative Primitives
- `put(payload) -> hash`: Content-addressed storage.
- `propose(manifest) -> proposal_id`: Mutation proposal.
- `sign(id, node) -> sig_h`: Consensus signature.
- `tally(id) -> int`: Consensus verification.

### Outputs
- `result`: **MANDATORY**. The final return value must be assigned to this variable.

---

## 2. Storage Protocol (The Adapter)
The Linker abstracts I/O through a standardized Adapter.

### Required Methods
- `read(h: str, tiers: list) -> str`: Retrieve a blob by hash.
- `write(h: str, data: str)`: Store an immutable blob.
- `exists(h: str) -> bool`: Check for blob existence.
- `get_state(id: str) -> dict`: Retrieve persistent memory.
- `put_state(id: str, state: dict)`: Commit persistent memory.
- `list(path: str) -> list`: Scan for artifacts/telemetry.

---

## 3. The 4-Layer Recursive Stack
The Linker coordinates the following semantic capabilities:
1. **Proxy (L1):** Normalization & MCP.
2. **Librarian (L2):** Semantic & Identity Resolution.
3. **Broker (L3):** Federated Arbitrage & Distillation.
4. **Engine (L4):** Binding & Retry Logic.
