# D-JIT Protocol Specification v1.0
**Status:** Draft — Protocol Definition
**Supersedes:** f(nil).md (implementation-anchored)
**Scope:** Runtime-agnostic contracts for D-JIT Logic Fabric

---

## 1. Core Concepts

### 1.1 Blob

An immutable, content-addressed unit of data or code.

**Identity:** `hash = H(payload_bytes)` where `H` is the hash function specified in the envelope header. Default: SHA-256.

**Invariants:**
- A blob's identity is derived from its payload. If payload changes, identity changes.
- Two blobs with identical payloads have identical hashes, regardless of origin.
- Blobs are never mutated. Updates create new blobs with new hashes.

### 1.2 Vault

A content-addressed key-value store. Implements:

```
get(hash) → blob | NotFound
put(blob) → hash
scan(filter) → [blob]
```

The vault is scoped, not global. Each scope (user, tenant, project, session) holds references to the blobs it uses. Storage grows with scope activity.

See [docs/design/SCOPE.md](docs/design/SCOPE.md) for the scope model.

Storage backend is implementation-defined: filesystem, SQLite, memory, S3, IPFS.

### 1.3 Scope

A scope is a reference container. It holds references (hashes) to blobs, not the blobs themselves.

```json
{
  "id": "scope_id",
  "type": "private|org|public|...",
  "references": { "hash": count, ... }
}
```

Scopes can reference each other. The vault is the union of all scoped reference graphs.

### 1.4 Node

A runtime instance with a vault and a linker. Identified by a public key pair.

### 1.5 Mesh

A set of nodes that can exchange blobs by hash.

---

## 2. The Typed Envelope

All blobs are serialized as UTF-8 JSON conforming to this schema:

```json
{
  "v": 1,
  "hash": "<hex-encoded hash of payload bytes>",
  "hash_fn": "sha256",
  "type": "<MIME-like type string>",
  "payload": "<raw string>",
  "metadata": {
    "ctime": <unix epoch seconds, integer>,
    "author": "<optional node public key>",
    "predecessor": "<optional previous blob hash>",
    "references": ["<optional array of blob hashes this blob depends on>"],
    "interface": ["<optional array of function names this blob exports>"],
    "signature": "<optional cryptographic signature over hash+type+payload>"
  }
}
```

### 2.1 Field Definitions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `v` | Yes | Integer | Envelope version. Current: 1. |
| `hash` | Yes | String | Hex-encoded hash of `payload` bytes. |
| `hash_fn` | Yes | String | Hash algorithm. Values: `sha256`, `sha512`, `blake3`. |
| `type` | Yes | String | MIME-like type. Format: `namespace/subtype`. |
| `payload` | Yes | String | Raw content. Interpreted according to `type`. |
| `metadata.ctime` | Yes | Integer | Unix epoch seconds at creation. |
| `metadata.author` | No | String | Public key of the creating node. |
| `metadata.predecessor` | No | String | Hash of the blob this is a version of. |
| `metadata.references` | No | Array[String] | Hashes of blobs this blob depends on. |
| `metadata.interface` | No | Array[String] | Names of functions this blob exports. |
| `metadata.signature` | No | String | Signature over `hash + type + payload`. |

### 2.2 Hash Computation

```
hash = hex_encode(H(utf8_encode(payload)))
```

The hash is computed over the `payload` string only, not the envelope. This means the same payload in two different envelopes (different metadata) produces the same hash.

### 2.3 Type Namespace

Types follow `namespace/subtype` convention:

| Namespace | Meaning | Examples |
|-----------|---------|----------|
| `application/` | Executable code | `application/python`, `application/javascript`, `application/wasm` |
| `data/` | Structured data | `data/row`, `data/table`, `data/schema` |
| `text/` | Human-readable text | `text/markdown`, `text/plain` |
| `telemetry/` | Runtime metrics | `telemetry/artifact`, `telemetry/edge` |
| `trust/` | Trust records | `trust/score`, `trust/endorsement` |
| `query/` | Query definitions | `query/select`, `query/traverse` |
| `system/` | System control | `system/manifest`, `system/config` |

Implementations MUST handle unknown types gracefully: store them, return them on `get()`, but refuse to `bind()` them.

---

## 3. Seed Protocol

The minimal interface every D-JIT implementation must provide.

### 3.1 Operations

#### PUT

```
Input:  { type: string, payload: string, predecessor?: string, references?: string[], author?: string }
Output: { hash: string }
Errors: InvalidType, PayloadTooLarge, StorageFull
```

**Behavior:**
1. Compute `hash = H(payload)`
2. Construct envelope with `v=1`, `hash_fn`, `type`, `payload`, `metadata`
3. If `hash` already exists in vault, return existing hash (idempotent)
4. Store envelope in vault
5. Return `{ hash }`

#### INVOKE

```
Input:  { hash: string, args?: any }
Output: { result: any, telemetry_hash: string }
Errors: BlobNotFound, UnsupportedType, BindError, Timeout, SandboxViolation
```

**Behavior:**
1. Load blob by `hash` from vault
2. Dispatch to binding engine based on `type`
3. Execute payload with `args`
4. Capture result, latency, resource usage
5. Emit telemetry blob (see §5)
6. Return `{ result, telemetry_hash }`

#### GET

```
Input:  { hash: string }
Output: { blob: Envelope }
Errors: BlobNotFound
```

**Behavior:** Return the full envelope. Read-only.

### 3.2 Binding Engine Contract

A binding engine handles one or more blob types. Interface:

```
can_handle(type) → bool
bind(blob, args) → result
```

**Requirements:**
- MUST execute in a sandbox appropriate to the type
- MUST return within a configurable timeout
- MUST report resource usage (time, memory)
- MUST NOT expose host environment to untrusted payloads

**Sandbox Levels:**

| Level | Description | Use Case |
|-------|-------------|----------|
| `none` | No isolation. Full host access. | Trusted environments only. |
| `lexical` | No access to caller's scope. Global scope only. | Semi-trusted blobs. |
| `context` | Restricted global scope. Only explicitly provided bindings. | Untrusted blobs. |
| `process` | Separate process. OS-level isolation. | Untrusted code, network access. |
| `vm` | Virtual machine. Hardware-level isolation. | Maximum security. |

Implementations MUST declare their default sandbox level. `none` is NOT acceptable for production mesh nodes.

---

## 4. Judge Protocol

Trust verification interface.

### 4.1 Operations

#### VERIFY

```
Input:  { hash: string }
Output: { integrity: float, details: { computed_hash: string, stored_hash: string, match: bool } }
Errors: BlobNotFound
```

**Behavior:** Recompute hash from payload, compare to stored hash. Return `1.0` if match, `0.0` if not.

#### SCORE

```
Input:  { hash: string }
Output: {
  target_hash: string,
  integrity: float,
  invocation_count: int,
  success_rate: float,
  avg_latency_ms: float,
  avg_memory_kb: float,
  trust_score: float,
  ts: int
}
Errors: BlobNotFound
```

**Behavior:**
1. Verify integrity
2. Find all telemetry blobs where `metadata.predecessor == hash`
3. Compute metrics from telemetry
4. Compute trust_score per §6
5. Store trust record as a `trust/score` blob
6. Return score record

#### SCAN

```
Input:  {}
Output: [{ score record }, ...]
Errors: None
```

**Behavior:** Score all non-telemetry, non-trust blobs in vault.

### 4.2 Trust Record Blob

Trust scores are stored as blobs:

```json
{
  "type": "trust/score",
  "payload": "<JSON-serialized score record>",
  "metadata": {
    "predecessor": "<hash of the scored blob>"
  }
}
```

---

## 5. Telemetry Protocol

Every INVOKE MUST emit a telemetry blob.

### 5.1 Telemetry Artifact

```json
{
  "type": "telemetry/artifact",
  "payload": "{\"invoked_hash\":\"...\",\"latency_ms\":N,\"memory_kb\":N,\"success\":bool,\"error\":\"optional\",\"ts\":N}",
  "metadata": {
    "predecessor": "<hash of the invoked blob>"
  }
}
```

### 5.2 Telemetry Edge (Phase 4+)

For graph-aware execution, telemetry records the path taken:

```json
{
  "type": "telemetry/edge",
  "payload": "{\"source_hash\":\"...\",\"target_hash\":\"...\",\"latency_ms\":N,\"success\":bool,\"ts\":N}",
  "metadata": {
    "predecessor": null
  }
}
```

### 5.3 Requirements

- Telemetry blobs MUST be emitted for every INVOKE, including failures
- `success` MUST be `false` if an error occurred during binding
- `ts` MUST have sub-second precision to ensure unique hashes per emission
- Telemetry blobs MUST NOT be scored by the Judge (skip in SCAN)

---

## 6. Fitness Function

All planning decisions optimize:

```
f(Link) = (SuccessRate × Integrity) / (max(Latency, ε) × max(Cost, ε))
```

Where:
- `SuccessRate` ∈ [0, 1]: fraction of successful invocations
- `Integrity` ∈ {0, 1}: 1.0 if hash matches, 0.0 if not
- `Latency` > 0: average execution time in milliseconds
- `Cost` > 0: resource cost (memory in KB, or implementation-defined)
- `ε` = 1e-6: floor to prevent division by zero

**Interpretation:** Higher is better. A blob with perfect trust, low latency, and low cost scores highest. A tampered blob scores 0.0 regardless of other metrics.

**Path Scoring (Phase 4+):** For a path of N blobs, the path fitness is:

```
f(Path) = min(f(blob_i) for i in 1..N)
```

The weakest link determines the path score. Alternative aggregation strategies (mean, weighted mean) are implementation-defined but MUST be documented.

---

## 7. Linker Protocol

The self-hosting orchestrator.

### 7.1 Manifest

A manifest blob defines the active configuration:

```json
{
  "type": "system/manifest",
  "payload": "{\"version\":\"1.0.0\",\"discovery_hash\":\"...\",\"planning_hash\":\"...\",\"binding_hash\":\"...\",\"ts\":N}",
  "metadata": {}
}
```

| Field | Description |
|-------|-------------|
| `discovery_hash` | Hash of the discovery logic blob |
| `planning_hash` | Hash of the planning logic blob |
| `binding_hash` | Optional. Hash of the binding engine blob. If absent, use built-in. |

### 7.2 Operations

#### BOOTSTRAP

```
Input:  { discovery_blob, planning_blob, binding_blob? }
Output: { manifest_hash: string, discovery_hash: string, planning_hash: string }
```

**Behavior:**
1. Store discovery and planning blobs
2. Create manifest blob referencing them
3. Write manifest reference to local config (implementation-defined location)
4. Back up previous manifest reference

#### EXECUTE

```
Input:  { hash: string, args?: any }
Output: { result: any, mode: string, tier: string, path: string[] }
Errors: ManifestNotFound, BlobNotFound, LinkerError, PermissionError
```

**Behavior:**
1. Load manifest
2. Load and execute discovery blob → resolve target
3. Load and execute planning blob → decide execution mode
4. If `reject`: raise PermissionError
5. If `shadow`: execute, annotate result with shadow flag
6. If `embed`: execute normally
7. Return result with metadata

#### EXECUTE_BY_INTENT (Phase 4+)

```
Input:  { intent: string, constraints?: { max_latency_ms?: int, min_trust?: float } }
Output: { result: any, path: string[], mode: string }
Errors: NoPathFound, IntentAmbiguous, ConstraintsUnmet
```

**Behavior:**
1. Query vault for blobs matching intent
2. Find all paths from manifest to candidates
3. Score each path
4. Select best path within constraints
5. Execute leaf blob
6. Return result with full path

---

## 8. Discovery Protocol

### 8.1 Discovery Function Contract

A discovery blob MUST export a function with this signature:

```
discover(hash: string, vault: Vault) → Resolution | null
```

Where `Resolution` is:

```json
{
  "tier": "L1" | "L2" | "L3",
  "path": "<implementation-defined location string>",
  "blob": "<full envelope>"
}
```

### 8.2 Tier Definitions

| Tier | Scope | Latency Target | Trust Requirement |
|------|-------|----------------|-------------------|
| L1 | Local vault | < 10ms | None (local data) |
| L2 | Known peers | < 100ms | Peer must be in trust list |
| L3 | Global registry | < 1000ms | Blob must have valid signature |

### 8.3 Resolution Protocol

1. Check L1 (local vault). If found, return.
2. Query L2 peers for hash. If found, fetch and store locally, return.
3. Query L3 registry. If found, verify signature, fetch and store locally, return.
4. Return `null` if not found at any tier.

---

## 9. Planning Protocol

### 9.1 Planning Function Contract

A planning blob MUST export a function with this signature:

```
plan(blob: Envelope, trust: TrustRecord | null, context: ExecutionContext) → Decision
```

Where `Decision` is:

```json
{
  "path": "embed" | "shadow" | "reject",
  "reason": "<human-readable explanation>",
  "sandbox": "<optional sandbox level override>"
}
```

### 9.2 Execution Context

```json
{
  "available_runtimes": ["python", "javascript", "wasm"],
  "current_load": float,
  "memory_available_kb": int,
  "network_latency_ms": int
}
```

### 9.3 Default Planning Logic

If no planning blob is configured, implementations MUST use:

```
if trust is null:
    return { path: "embed", reason: "no trust data" }
if trust.integrity < 1.0:
    return { path: "reject", reason: "integrity failed" }
if trust.trust_score > 0:
    return { path: "embed", reason: "trust_score > 0" }
return { path: "shadow", reason: "no invocation history" }
```

---

## 10. Mesh Protocol (L2/L3)

### 10.1 Peer Discovery

Nodes announce themselves via:
- mDNS (local network)
- DHT (overlay network)
- Static configuration

### 10.2 Blob Exchange

```
Request:  { type: "get_blob", hash: string }
Response: { type: "blob", envelope: Envelope } | { type: "not_found", hash: string }
```

### 10.3 Gossip

Nodes periodically exchange hash lists:

```
Request:  { type: "have", hashes: [string], since: int }
Response: { type: "have", hashes: [string], since: int }
```

Each node computes the set difference and requests missing blobs.

### 10.4 Trust Propagation

Trust records can be endorsed by other nodes:

```json
{
  "type": "trust/endorsement",
  "payload": "{\"target_hash\":\"...\",\"trust_score\":N,\"endorser\":\"<public key>\"}",
  "metadata": {
    "predecessor": "<hash of the endorsed trust/score blob>"
  }
}
```

---

## 11. Version Negotiation

### 11.1 Envelope Version

The `v` field in the envelope determines the schema version. Implementations:

- MUST accept envelopes with `v` equal to or less than their maximum supported version
- MUST reject envelopes with `v` greater than their maximum supported version
- MUST produce envelopes with their maximum supported version

### 11.2 Protocol Version

Nodes exchange protocol version during handshake:

```
{ "djit_version": "1.0", "supported_hash_fns": ["sha256"], "supported_types": ["application/*", "data/*", ...] }
```

### 11.3 Backward Compatibility

New versions of this spec MUST:
- Add fields, never remove or rename them
- Define default values for new required fields
- Specify the minimum version that can read the new fields

---

## 12. Error Semantics

All errors follow this envelope:

```json
{
  "error": {
    "code": "<machine-readable error code>",
    "message": "<human-readable description>",
    "detail": "<optional implementation-specific context>"
  }
}
```

### 12.1 Standard Error Codes

| Code | Meaning |
|------|---------|
| `BlobNotFound` | Hash does not exist in vault |
| `InvalidType` | Type string does not match `namespace/subtype` format |
| `PayloadTooLarge` | Payload exceeds implementation-defined limit |
| `UnsupportedType` | No binding engine handles this type |
| `BindError` | Execution failed (runtime error in payload) |
| `Timeout` | Execution exceeded time limit |
| `SandboxViolation` | Payload attempted prohibited operation |
| `IntegrityFailed` | Hash mismatch detected |
| `PermissionError` | Planner rejected execution |
| `ManifestNotFound` | No active manifest |
| `NoPathFound` | Intent could not be resolved to any blob |
| `IntentAmbiguous` | Multiple blobs match intent with equal scores |
| `StorageFull` | Vault has no remaining capacity |

---

## 13. Implementation Requirements

### 13.1 Minimum Viable Implementation

A conforming D-JIT implementation MUST provide:
1. Vault with `get()`, `put()`, `scan()` operations
2. Seed with `PUT`, `INVOKE`, `GET` operations
3. Judge with `VERIFY`, `SCORE` operations
4. At least one binding engine for at least one `application/*` type
5. Telemetry emission on every INVOKE
6. Manifest-based linker with `BOOTSTRAP` and `EXECUTE`

### 13.2 Optional Extensions

- L2/L3 discovery (§8, §10)
- Graph traversal (§7 EXECUTE_BY_INTENT)
- Edge-weighted trust (§5.2)
- Query blobs (§2.3 `query/` namespace)
- Branching and merging (Dolt-style version control)
- CRDT-based trust aggregation
- Streaming telemetry views

### 13.3 Interoperability

Two implementations interoperate if:
1. They use the same envelope version and hash function
2. They can exchange blobs via the mesh protocol (§10)
3. They produce identical hashes for identical payloads
4. They handle unknown types gracefully

---

## 14. Security Model

### 14.1 Threat Assumptions

| Assumption | Level | Notes |
|------------|-------|-------|
| Local vault integrity | Trusted | Filesystem access = game over |
| Peer communication | Untrusted | All messages authenticated |
| Blob payloads | Untrusted | Execute in sandbox |
| Telemetry data | Semi-trusted | Can be spoofed, mitigated by cross-referencing |
| Trust records | Semi-trusted | Verified by integrity check |

### 14.2 Required Security Properties

1. **Integrity:** Every blob's hash MUST be verified before binding
2. **Isolation:** Binding engines MUST execute in a sandbox appropriate to the trust level
3. **Provenance:** Blob signatures SHOULD be verified when available
4. **Rate limiting:** Implementations SHOULD limit PUT rate to prevent DoS
5. **Size limits:** Implementations SHOULD enforce maximum blob size

### 14.3 Audit Trail

Every security-relevant operation MUST be logged:
- Blob PUT (with hash and type)
- Blob INVOKE (with hash and result)
- Trust score changes
- Manifest changes
- Peer connections and disconnections
