# Object Model: Identity, Versioning, and Mutation

## Premise

Blobs are immutable and identified by content hash. But real systems need stable references — names that persist across versions. This doc explores the object model that bridges immutable blobs with mutable-sounding use cases.

---

## The Core Question

**MOO objects had stable IDs (`#1234`) but mutable state.**
**Git commits are immutable but referenced by branch names.**

**Synapse: what model serves both immutability and usability?**

---

## Models

### Model 1: Pure Content-Address (Current)

```
blob = { address: hash(content), content: bytes }
```

- Hash IS identity
- Immutable by definition
- Every change = new address
- Simple, verifiable

**Pros:** Tamper-evident, simple GC
**Cons:** No stable human-readable names, hard to track "the same thing" across versions

### Model 2: Stable ID + Version History

```
object = {
  id: stable_id,           // Human-facing reference
  current: hash,            // Current version
  history: [hash1, ...],   // Version history
  owner: scope_id
}
```

- Stable ID for human use
- Hash for verification
- History for audit
- Mutable in sense of "has versions"

**Pros:** Stable references, versionable
**Cons:** More complex, history can grow

### Model 3: Mutable Reference (Like MOO)

```
object = {
  id: stable_id,
  properties: { ... },    // Mutable
  verbs: [...],           // Mutable
  owner: scope_id
}
```

- Objects can be modified in place
- No version history
- MOO model

**Pros:** Simple, familiar
**Cons:** No audit trail, harder to verify

---

## Proposed: Hybrid Model

Synapse supports both:

| Type | Immutable | Stable ID | Versioned |
|------|-----------|-----------|-----------|
| Blob | Yes | Hash = ID | No |
| Object | Content immutable | Stable ID | Yes |

```
object = {
  id: "my-service",                    // Stable human name
  current: "abc123...",                // Current blob hash
  history: ["def456...", "ghi789..."], // Version chain
  type: "application/python",
  metadata: {
    author: "agent_xyz",
    created: 1234567890,
    description: "...",
    tags: ["api", "http"]
  }
}
```

**Invariants:**
- `current` is always a valid blob hash
- `history` contains all past `current` values
- Changing `current` creates a new object version

---

## Stable ID Use Cases

### Human-Readable References

```python
# Instead of:
invoke("abc123def456...")

# User writes:
invoke("my-service")
# System resolves: my-service → current blob hash
```

### Soft Deprecation

When object updates:
1. New blob created
2. Object's `current` updates
3. Old `current` stays in `history`
4. Old blob not deleted (still referenced in history)

### Audit Trail

```python
# What was this object on 2024-03-01?
history_snapshot = get_object_at_version("my-service", timestamp)
# Returns: { id, blob_hash, timestamp }
```

### Fork

```python
# Fork object to new ID
fork = {
  id: "my-service-fork",
  current: original.current,
  history: original.history,
  metadata: { fork_of: original.id }
}
```

---

## Version Resolution

| Syntax | Resolution |
|--------|------------|
| `my-service` | Current version |
| `my-service@v1.2.3` | Semantic version |
| `my-service@abc123` | Specific hash |
| `my-service@latest` | Current |
| `my-service@2024-03-01` | Timestamp |

---

## Comparison with Other Systems

| System | Identity | Versioning | Mutation |
|--------|----------|------------|----------|
| Git blob | SHA | No | No |
| Git ref | name | Yes | Yes (force push aside) |
| MOO | #1234 | No | Yes |
| Smalltalk | Object ref | No | Yes |
| Datomic | Entity ID | Yes (history DB) | No (append-only) |
| DNS | domain | Yes (TTL) | Yes |
| Smart contract | address | No | Yes (state) |

---

## Open Questions

1. **ID namespace?** Who controls ID allocation? Is there a global namespace?

2. **Version policy?** How many versions are kept? Forever? Rolling window?

3. **Semantic versioning?** Should objects have semver? Who increments?

4. **Migration?** When object changes, can old code still access old version?

5. **Cross-object references?** If object A references object B, and B updates, what happens?

---

## Implementation Notes

### Object Registry

```json
{
  "registry": {
    "my-service": {
      "current": "abc123",
      "history": ["def456", "ghi789"],
      "type": "application/python"
    }
  }
}
```

Registry itself is a blob. Referenced by scope.

### Resolution

```python
def resolve(reference):
  if is_hash(reference):
    return reference
  if is_object_ref(reference):
    obj = get_object(reference)
    return obj.current
  raise NotFound
```

### Stable ID as Capability

`my-service` is a capability. Possessing the reference means you can invoke the current version.

Revoking access = removing reference from scope.

---

## See Also

- [explore/MOO.md](../explore/MOO.md) — MOO object model
- [explore/SMALLTALK.md](../explore/SMALLTALK.md) — Live coding, image persistence
- [design/SCOPE.md](SCOPE.md) — Scopes hold object references
