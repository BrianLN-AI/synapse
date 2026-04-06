# Scope Design

> **Status:** Design — scope taxonomy, principles, and open problems

---

## Core Insight

> Scope contains references. GC happens when nothing in scope references a hash.

The vault is not a global flat store. It is the union of scoped reference graphs. Storage cost is a function of scope activity, not total system size.

---

## Scope as Caching

Scopes are cache regions. References are cached items. Hashes are cache keys. GC is eviction.

| Caching | Synapse scope |
|---------|---------------|
| Cache region | Scope |
| Cached item | Reference (hash in scope) |
| Cache key | Hash (content-address) |
| Eviction | GC when refcount = 0 |
| Cache miss | Cold start (empty scope) |
| Cache warming | Pre-populate scope |
| TTL | (not modeled) |
| Write-through | Blob promotion propagates |

**The twist:** Content-addressing provides automatic coherence. Same hash → same content everywhere. No invalidation protocol needed.

**Layered caching:**

```
┌─────────────────────────────────────┐
│ User scope (L1)  → immediate refs  │
├─────────────────────────────────────┤
│ Tenant scope (L2) → org pool       │
├─────────────────────────────────────┤
│ Public scope (L3) → shared blobs   │
├─────────────────────────────────────┤
│ Cold storage       → unreferenced  │
├─────────────────────────────────────┤
│ Global vault        → source of    │
│                     truth          │
└─────────────────────────────────────┘
```

---

## Scope Taxonomy

Scopes are characterized along multiple dimensions simultaneously:

```
Scope Type         ← What it contains
Scope Visibility   ← Who can access
Scope Inheritance  ← What it inherits
Scope Lifespan     ← When it dies
Scope Persistence  ← What survives
```

### By Type

| Scope | Contains | Example |
|-------|----------|---------|
| `private` | User's own refs | My blobs, my telemetry |
| `org` | Team's refs | Shared project blobs |
| `public` | Published refs | Common library blobs |
| `query_result` | Ephemeral refs | Search results, graph traversals |
| `query_def` | Saved queries | Named queries, filters |
| `deployment` | Versioned refs | `deploy-2024-03-06` |
| `invocation` | Ephemeral refs | Per-call scope |
| `cleanroom` | Minimal refs | Fresh environment |
| `template` | Empty shell | Scope factory |

### By Visibility

| Visibility | Access | Governance |
|------------|--------|------------|
| `private` | Owner only | Owner-defined |
| `shared` | Explicit grants | Owner + grantee |
| `published` | Anyone can read | Publisher-defined |
| `public` | Anyone invoke | Global governance |

### By Inheritance

| Pattern | Behavior | Example |
|---------|----------|---------|
| `clone` | Copy all refs | Project fork |
| `inherit` | Parent refs + own | Tenant inherits org |
| `override` | Parent + local overrides | Org customizes global |
| `sandbox` | No inheritance | Cleanroom |
| `link` | Reference without copy | Shared module |

### By Lifespan

| Pattern | Creation | Death |
|---------|----------|-------|
| `permanent` | Signup | Deletion request |
| `persistent` | Project init | Project delete |
| `versioned` | Deploy | New deploy supersedes |
| `session` | Login | Logout |
| `ephemeral` | Invocation | Return |

---

## Scope Graph

Scopes can reference each other. A private scope can reference public blobs. An org scope can reference member's scopes. A query scope references the blobs it found.

```
user_scope:     { my_blob, my_blob, public/stdlib }
                      ↑          ↑         ↑
                      └──────────┴─────────┴─ references to other scopes
```

**This is a directed graph of scopes, not a tree.** Cyclic references are fine (content-addressed).

Scopes can also be:

| Relationship | Description |
|--------------|-------------|
| Parent/child | Scope A owns Scope B |
| Peer | Scopes share a parent |
| Reference | Scope A references Scope B's blobs |
| Fork | Clone of Scope A |

---

## Scope Structure

```json
{
  "scope": {
    "id": "stable_scope_id",
    "type": "private|org|public|query_result|...",
    "visibility": "private|shared|published|public",
    "inheritance": "clone|inherit|override|sandbox|link",
    "lifespan": "permanent|persistent|versioned|session|ephemeral",
    "parent": "optional_scope_id",
    "references": {
      "hash1": { "count": 3, "scope": "local" },
      "hash2": { "count": 1, "scope": "public" }
    },
    "capabilities": ["invoke", "create", "delegate", "publish"],
    "governance": "governance_expression_id",
    "owner": "user_or_org_id",
    "metadata": {}
  }
}
```

---

## Reference Resolution

When a scope references a hash:

1. Check local scope
2. Check parent scopes (if inheritance)
3. Check linked scopes (if reference)
4. Check public scopes (if visibility allows)
5. Return NotFound

**Reference counting:**

- Each scope tracks local reference counts
- Cross-scope references are tracked in originating scope
- GC when count = 0 in all referencing scopes

---

## Key Principles

### 1. Scope contains references, not content

Storage is content. Scopes hold references. Content lives in the vault.

### 2. GC is tractable at scope level

When nothing in a scope references a hash, that hash can be GC'd from that scope's working set.

### 3. Content-addressing provides coherence

Same hash = same content everywhere. No invalidation protocol needed.

### 4. Scopes are composable

Scopes can reference other scopes. Composition is declaration, not copying.

### 5. Visibility is orthogonal to type

A `private` scope can be `clone`d into a `shared` scope. A `public` scope can contain `private` blobs (owned by different users).

---

## Comparison with Other Systems

| System | Scope model |
|--------|------------|
| Erlang/OTP | Ephemeral processes + explicit ETS/Mnesia storage |
| MOO | Global world, rooms partition visibility, stable object IDs |
| Smalltalk | Global image, namespace/package for visibility |
| Kubernetes | Namespace = hard partition, RBAC within |
| Smart contracts | Stable address, mutable state, no GC |
| CDN | Edge caches + origin, TTL-based eviction |

---

## Graph Queries and Scopes

The vault is a Merkle DAG. Scopes provide cached access to subgraphs. Query scopes hold references to blobs found through graph traversal.

### Edge Types

The vault graph has derived edges:

| Edge | Meaning | Scope implication |
|------|---------|------------------|
| `GOVERNS` | Governance expression → promoted blob | Tracks what's approved |
| `OBSERVES` | Telemetry record → logic blob | Execution history |
| `PRECEDES` | Blob → prior version | Lineage/evolution |
| `DEPENDS` | Blob → referenced blobs | Dependency graph |
| `TAGGED` | Tag artifact → blob | Metadata |
| `SIMILAR` | Semantic similarity | Discovery |

### Query as Scope

Query results are scopes:

```
query_scope = {
  type: "query_result",
  lifespan: "ephemeral",
  references: { found_blob_1: 1, found_blob_2: 1 },
  query: "traverse from seed following GOVERNS..."
}
```

**This means:**
- Graph traversals create scopes
- Results are scoped references (cacheable)
- GC applies to query results
- Queries can be named and saved (`query_def` scope type)

### S-Expression Query DSL

Queries are S-expressions. Queries are blobs.

```lisp
; Current blobs for tenant T
(traverse (hash genesis) GOVERNS (type? "logic/") BFS)

; Semantic neighborhood of X
(traverse (query (embed x)) SIMILAR (score> 0.8) BFS)

; Chain projections (version history)
(chain (hash manifest-v1) PRECEDES)
```

**Homoiconicity:** Query language = execution language. Queries can be stored, versioned, governed.

### Scope as Graph Cache

```
User scope → { my blobs }
Tenant scope → { org blobs, shared modules }
Query scope → { results of traversal }
```

Scopes are cache regions for the reference graph. GC applies to all scope types uniformly.

### Semantic Similarity

```
(traverse (query "text embedding")) SIMILAR (score> 0.8)
```

Requires:
- Embedding model
- `meta/embedding` blob type
- Index (see GRAPH-QUERY-LAYER.md for details)

---

## Open Questions

1. **Hierarchical vs. graph?** Is scope a tree, a graph, or both?
2. **Scope creation protocol?** What does "create scope" mean operationally?
3. **Cross-scope invocation?** When scope A calls blob in scope B, what happens?
4. **Billing model?** Per-scope storage? Per-invocation? Per-reference?
5. **Scope death protocol?** Grace period, data export, deletion?
6. **Scope migration?** Can scopes move between tenants?
7. **Query scope TTL?** How long do query_result scopes live?

---

## References

- Erlang/OTP: `spawn`, `ets`, `mnesia`
- MOO: LambdaMOO object model, property/verb model
- Kubernetes: Namespace, RBAC, ResourceQuota
- Smart contracts: Solidity storage model
- CDN: Edge caching, TTL, write-through
- Content-addressed storage: IPFS, git

---

## Next Steps

1. Define scope creation protocol
2. Design reference counting strategy
3. Design cross-scope invocation semantics
4. Prototype layered scope model
5. Design billing model
