# Design Memo: Graph Query Layer

**Date:** 2026-04-02
**Status:** Design — pre-ADR
**Target implementation:** f_15+

---

## What the vault actually is

The vault is a **Merkle DAG** — a directed acyclic graph where every node is
content-addressed. Two independently derived expressions with identical content are the
same node. The graph is append-only (nodes are never removed). Any expression can
reference any other by hash.

This is the same structure as git (objects) and IPFS (content identifiers). The vault's
core reference graph — expressions that embed other expressions' hashes in their payload
— is a DAG by construction: if A's hash depends on B's hash, B cannot transitively
depend on A without creating a hash cycle, which is cryptographically infeasible.

Currently the vault is used as a flat key-value store: `put(type, payload) → hash`,
`get(hash) → envelope`. This is correct but incomplete. The rich graph structure is
present but not navigable beyond direct hash lookup.

---

## Multiple edge types

Beyond direct hash references (embedded in payload), the graph has derived edges that
must be stored explicitly as expression artifacts:

```
GOVERNS   — governance expression → promoted expression
OBSERVES  — telemetry record → logic expression
PRECEDES  — expression → prior version of itself (lineage)
DEPENDS   — expression → expression it references by hash
TAGGED    — tag artifact → expression
SIMILAR   — semantic similarity (embedding-derived)
```

**Edges are content-addressed expressions.** An edge artifact:
```json
{
  "type": "meta/edge",
  "payload": {
    "source":    "<expression-hash>",
    "edge-type": "TAGGED",
    "target":    "<expression-hash>",
    "metadata":  {}
  }
}
```

The edge has a hash. The edge can itself be tagged, governed, or linked. The graph
describes its own structure.

**Tags are edges:**
```json
{
  "type":    "meta/tag",
  "payload": {
    "target":    "<expression-hash>",
    "tag":       "security-sensitive",
    "tagged-by": "<tenant-id>"
  }
}
```

Tags are tenant-specific, auditable, and revocable (via a revocation expression). Different
tenants can tag the same expression differently.

---

## The traversal state machine

All graph queries are parameter variations of one state machine:

```lisp
(traverse seed follow predicate strategy
  :depth    nil        ; max edge hops (nil = unbounded)
  :breadth  nil        ; max nodes per depth level
  :budget   nil        ; total node visits before forced stop
  :timeout  nil        ; wall-clock ms limit
  :on-cycle on-cycle   ; cycle handler (see below)
  :lazy     false)     ; true = stream, false = collect
```

**Parameters:**
- `seed` — entry point: `(hash h)`, `(type t)`, `(tag t)`, `(query embedding)`
- `follow` — which edge types to traverse: `#{GOVERNS SIMILAR}`, `(all-edges)`
- `predicate` — filter: `(type? "logic/")`, `(and (type? "logic/") (tag? "security-sensitive"))`
- `strategy` — `BFS`, `DFS`, `CHAIN` (asserts at most one successor per node)

**The state machine:**

```
START    → resolve seed to initial hashes → FRONTIER
FRONTIER → pick next hash (by strategy) → VISIT
VISIT    → check visited set → EXPAND (if new) | FRONTIER (if seen)
EXPAND   → load expression, find neighbors by edge type and depth → FILTER
FILTER   → apply predicate → COLLECT (if true) | advance frontier
COLLECT  → append to results → FRONTIER
DONE     → return results (when frontier empty)
```

---

## S-expression query DSL

Traversal parameters form a composable DSL. Queries are S-expressions. S-expressions
are expressions. **Queries can be stored as expressions in the vault and invoked like
any other expression.** This is homoiconicity: the query language and the execution
language are the same.

```lisp
; Common traversals

; Current expressions for tenant T
(traverse (hash genesis) GOVERNS (type? "logic/") BFS)

; Governance chain for expression X  
(chain (traverse (hash x) #{GOVERNS PRECEDES} any) PRECEDES)

; All security-sensitive logic and their governance artifacts
(then
  (traverse (tag "security-sensitive") TAGGED (type? "logic/") BFS)
  (traverse _ GOVERNS (type? "governance/") CHAIN))

; Semantic neighborhood of X (1 hop, score > 0.8)
(traverse (query (embed x)) SIMILAR (score> 0.8) BFS 1)

; Chain projections over governance history
(chain (hash manifest-v1) PRECEDES)    ; manifest version history

; Composition operators
(then t1 t2)          ; result of t1 becomes seed of t2
(chain t edge)        ; constrain traversal to one predecessor per node
(intersect t1 t2)     ; intersection of result sets
(union t1 t2)         ; union of result sets
```

**A stored query:**
```python
query_hash = vault.put("query/sexp",
    "(traverse (tag 'security-sensitive') TAGGED (type? 'logic/') BFS)")

# Later: invoke with a graph as context
result = invoke(query_hash, {"graph": current_graph})
```

---

## Chains over the graph

A chain is a traversal constrained to one predecessor per node, totally ordered. Any
dimension of the graph can be projected into a chain:

- **Lineage chain**: `(chain (hash x) PRECEDES)` — evolution history of expression X
- **Governance chain**: `(chain (hash approval) PRECEDES)` — approval history for a label
- **Telemetry chain**: `(chain (hash x) OBSERVES)` — time-ordered observations for X

The chain doesn't exist in the vault as a structure — it emerges from applying the CHAIN
strategy to any edge type. Blockchain is a chain projected over a consensus subgraph;
this system can construct equivalent chains without requiring an external chain, because
the vault is already a tamper-evident append-only Merkle DAG.

---

## Cycle handling

**Content-addressed edges** (hash embedded in payload): acyclic by construction.
A's hash depends on B's hash → B cannot transitively depend on A.

**Derived edges** (stored as edge artifacts): can cycle. A is similar to B, B is similar to A.
The visited set prevents infinite traversal. Per-edge-type policy handles semantics:

```lisp
(with-policy
  PRECEDES :on-cycle 'error    ; temporal contradiction
  DEPENDS  :on-cycle 'error    ; circular dependency
  GOVERNS  :on-cycle 'warn     ; mutual governance — surface it
  SIMILAR  :on-cycle 'skip     ; symmetric by nature
  TAGGED   :on-cycle 'skip)
```

**Cycles as knowledge.** When a cycle is detected (and policy is not 'error), store it:
```json
{
  "type": "meta/cycle",
  "payload": {
    "path":      ["<hash-1>", "<hash-2>", "<hash-1>"],
    "edge-type": "GOVERNS",
    "severity":  "warn"
  }
}
```

The cycle artifact is itself navigable: `(traverse (type "meta/cycle") TAGGED any BFS)`.

---

## Stack depth and performance

**Trampoline** — avoids stack overflow for deep graphs:
```lisp
; Return thunks instead of recursing; trampoline unwinds iteratively
(trampoline (traverse-step graph frontier #{} [] follow pred strategy depth))
```
Stack depth is constant regardless of graph depth. [CITED — Ganz, Friedman, Wand, 1999]

**Lazy streams** — caller controls termination:
```lisp
(take 10 (stream-traverse graph seed SIMILAR any BFS))
(take-while condition (stream-traverse graph seed GOVERNS any CHAIN))
```

**Budgets** — safety valves for production:
```lisp
(traverse seed follow pred BFS :depth 10 :budget 1000 :timeout 5000)
```

---

## Open questions before ADR

1. **Index storage**: type, tag, and semantic indexes must live somewhere. Options:
   a. External database (fast, mutable, not content-addressed)
   b. Index expressions in the vault (content-addressed, but rebuilding is expensive)
   c. Hybrid (external for speed, vault for audit)

2. **Semantic similarity**: embedding generation is not yet defined. Which model? Who
   computes it? When is it stored? This requires a new expression type: `meta/embedding`.

3. **Edge governance**: should edge artifacts require governance? A tag like
   "security-sensitive" applied by an untrusted tenant should carry less weight than one
   applied by a governed tenant. Edge attestation tier?

4. **Query expression invocation**: `invoke(query_hash, {graph: g})` — what is the type
   of `g`? A handle to the local vault, or a serialized subgraph? This affects whether
   queries can cross vault boundaries.
