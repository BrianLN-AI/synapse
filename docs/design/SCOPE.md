# Scope Design: Questions, Ideas, and Open Problems

> **Status:** Brainstorm — gathering questions and concepts before synthesis

---

## Core Insight

> Scope contains references. If nothing in scope references a hash, that hash isn't your problem.

The vault is not a global flat store. It is the union of scoped reference graphs. Storage cost is a function of scope activity, not total system size.

---

## Key Principle: Reference Graph Ownership

| Old framing | New framing |
|-------------|-------------|
| Global append-only vault | Union of scoped vaults |
| "All blobs persist forever" | "Blobs persist as long as referenced" |
| Storage grows unbounded | Storage grows with scope needs |
| Storage = total blobs | Storage = referenced blobs |

**The invariant:**
> A scope must be able to resolve every hash it references. The vault is the set of hashes a scope can resolve.

**The consequence:**
> Garbage collection is tractable at scope level. GC per scope, not global.

---

## Modes of Scope Creation

| Mode | Trigger | Lifespan | Example |
|------|---------|----------|---------|
| **User** | First invoke | Persistent | My blobs, my telemetry |
| **Session** | Connection start | Ephemeral | Lambda cold start, REPL, MOO login |
| **Tenant** | Org signup | Persistent + billed | Company storage pool |
| **Project** | Repo init | Persistent | Project dependencies, Docker image |
| **Invocation** | Blob call | Atomic | Each blob execution scope |
| **Deployment** | Deploy event | Versioned | `deploy-2024-03-06` |
| **Role** | Permission grant | Scoped to grant | `admin`, `viewer`, `contributor` |

---

## How Other Systems Handle Scope/Tenancy

### Erlang/OTP

```
Process = scope (ephemeral, lightweight, millions per node)
Supervision tree = lifecycle hierarchy
ETS tables = shared scope (persists across process death)
Mnesia = distributed scope (shared state)
spawn = scope creation
```

- No persistent per-user scope
- State lives in ETS/Mnesia, keyed by user ID
- Process death = scope death (no persistence)
- Hot code loading updates scope in place

**Insight:** Erlang's "scope" is ephemeral process. Storage is explicit (ETS/Mnesia), not implicit (vault).

### MOO

```
Player = tenant (persistent identity)
Room = scope (what you can see)
Inventory = user's contained objects
Verb permissions = RBAC within scope
Creation room = first login spawns player object
```

- World is global; rooms partition visibility
- Every player object has stable ID (`#1234`)
- Properties are mutable in place (current state)
- History is not tracked (no version control)

**Insight:** MOO has stable object IDs but mutable state. Synapse could have stable IDs with immutable version history.

### Smalltalk

```
Image = global scope (one world)
Package/Namespace = visibility partition
Class = global singleton
```

- No built-in tenancy
- Image backup = point-in-time snapshot
- Live coding modifies running system
- Bootstrap problem: how does image boot itself?

**Insight:** Smalltalk's "scope" is the entire image. Namespace/package provides visibility control but not isolation.

### Kubernetes

```
Namespace = org (hard partition)
Pod = ephemeral scope (restartable)
Deployment = versioned scope
PVC = persistent claim
RBAC = roles within namespace
```

- Namespaces are hard isolation boundaries
- Resources scoped to namespace
- Quotas per namespace
- Network policies per namespace

**Insight:** Kubernetes treats scope as isolation unit with quotas. Synapse could use scope for storage/compute quotas.

### Smart Contracts (Ethereum)

```
Contract address = stable ID
Call scope = transaction (ephemeral)
Storage = persistent (within contract)
```

- Contract state is mutable (via calls)
- Transaction is ephemeral scope
- State changes are deterministic and auditable
- No GC — storage grows forever

**Insight:** Smart contracts have stable addresses with mutable state. "Gas" is the cost-per-computation model.

### Multi-Tenant SaaS Patterns

```
Database per tenant = strong isolation
Schema per tenant = shared infra + partitioning
Row-level security = shared table + policies
```

- Tradeoff: isolation vs. overhead
- Billing per tenant straightforward
- Compliance implications (GDPR)

**Insight:** These patterns are for data, not computation. Synapse's scope model could layer on top.

---

## Open Questions

### 1. Is Scope Hierarchical?

**Question:** Can scopes nest? (User → Project → Invocation?)

| Option | Pros | Cons |
|--------|------|------|
| Flat | Simple | No parent-child relationships |
| Hierarchical | Natural nesting, inheritance | Complexity in reference resolution |
| Graph | Flexible, can share | Harder to reason about |

### 2. What Does Scope Creation Mean?

**Question:** Is scope creation:
- Allocation (reserve storage quota)?
- Initialization (first blob PUT)?
- Registration (make scope discoverable)?

### 3. Can Scopes Share Blobs?

**Question:** If scope A references blob H, and scope B also references H:
- Do they share one copy? (Yes, content-addressed)
- Does each have own reference count?
- Can scope B "unshare" by copying?

### 4. What Persists When Scope Dies?

| Lifespan | What survives |
|----------|---------------|
| Ephemeral (session) | Nothing |
| Project | Blobs (if explicitly kept) |
| Tenant | Everything |

**Question:** Is there a "tenant death" protocol? (Data export, grace period, deletion?)

### 5. Governance Per Scope?

**Question:** Does each scope have its own governance expression?
- Yes: scope-specific fitness function
- No: global governance applies everywhere
- Hybrid: scope inherits parent, can override

### 6. Billing Model

**Question:** How do we charge for scope usage?
- Per-scope storage (total referenced blobs)
- Per-invocation compute
- Per-reference (cross-scope calls)
- Flat rate

### 7. Cross-Scope References

**Question:** What happens when scope A invokes a blob in scope B?
- Cross-scope call allowed?
- Reference counted in both?
- Governance required?

### 8. Scope Migration

**Question:** Can a scope move between tenants?
- User leaves org, takes their scope
- Project transfers ownership
- Tenant merges with another

### 9. Scope Archival

**Question:** Can scopes be "frozen" (read-only, no new invocations)?
- Useful for compliance (audit scope)
- Useful for deprecation (deprecated project)

### 10. Scope Visibility

**Question:** Who can see a scope?
- Private (owner only)
- Shared (explicit grant)
- Public (anyone can invoke)

---

## Emerging Concepts

### Reference Graph as Primary Structure

The vault is not a flat store. It is the union of reference graphs. Each scope has its own reference graph. Storage is the union across all scopes.

```
scope_1: { A, B, C }
scope_2: { A, D, E }
vault = { A, B, C, D, E }  // A appears once, shared
```

Reference counting per scope determines when blobs can be GC'd.

### Scope as Capability Container

Scopes hold capabilities. Capabilities are references to blobs. The scope's permission set determines what its references can do.

```
scope = {
  id: stable_scope_id,
  references: { hash1: count, hash2: count, ... },
  capabilities: ["invoke", "create", "delegate"],
  parent: optional_scope_id,
  governance: governance_expression_id
}
```

### Ephemeral Scopes for Isolation

Each blob invocation could create an ephemeral scope:
- Receive context as input
- Execute with limited references
- Return result, scope destroyed

This provides isolation without persistence overhead.

### Stable Object IDs

Building on MOO's `#1234` pattern:

```
object = {
  id: stable_id,        // User-facing reference
  current: hash,         // Current version
  history: [hashes],     // Version history
  owner: scope_id
}
```

- Stable ID for human use
- Hash for verification
- History for audit

### Scoped Governance

Governance expressions could be scoped:
- Scope inherits parent governance by default
- Can override with scope-specific expression
- Changes propagate down hierarchy

### "Cold Storage" for Unreferenced Blobs

When a blob loses all references:
1. Not deleted
2. Moved to cold storage (cheaper)
3. First reference triggers "restore" (slower)
4. Long no-reference period → deleted

---

## Questions from Discussion

### What actually requires keeping a hash indefinitely?

- Nothing, if nothing references it
- Reference graph determines storage needs
- "Append only" is pragmatic, not a law

### Is the vault scoped or global?

- Scoped in principle
- Union of scoped vaults = total content
- Shared blobs reduce storage cost

### What triggers scope creation?

- User first invoke
- Project initialization  
- Tenant signup
- Deployment event
- Login/session start

---

## References

- Erlang/OTP: `spawn`, `ets`, `mnesia`
- MOO: LambdaMOO object model, property/verb model
- Kubernetes: Namespace, RBAC, ResourceQuota
- Smart contracts: Solidity storage model
- Multi-tenant SaaS: Database isolation patterns

---

## Next Steps

1. Decide: hierarchical vs. flat vs. graph scope model
2. Design: scope creation protocol
3. Design: reference counting / GC strategy
4. Design: cross-scope invocation semantics
5. Design: billing model
6. Prototype: simplest scope model
