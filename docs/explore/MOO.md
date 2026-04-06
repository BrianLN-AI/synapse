# MOO: Object-Oriented MUDs

## Premise

MOO (Multiple User Dungeon, Object-Oriented) systems were text-based virtual worlds built on object-oriented principles. The canonical implementation was **LambdaMOO**, created by Pavel Curtis at Xerox PARC in 1990.

**Core MOO properties:**
1. **Everything is an object** — rooms, players, exits, verbs, even the programming environment
2. **Objects have properties** — named data slots
3. **Objects have verbs** — callable methods
4. **Inheritance** — objects inherit from parent objects
5. **Message passing** — objects communicate by passing messages
6. **Player-created content** — players can create new objects, verbs, and properties
7. **Persistent world** — state survives across connections
8. **Capability-based security** — objects have permissions on what can be done to them

---

## Canonical Systems

| System | Created | Notable |
|--------|---------|---------|
| **LambdaMOO** | 1990, Xerox PARC | Canonical; first widely-deployed MOO |
| **MOO-Central** | 1990s | Major public MOO |
| **MOO Japan** | 1990s | Japanese MOO culture |
| **FrobMOO** | Various | Gaming-oriented MOOs |
| **MOO.se** | Various | Swedish academic MOOs |

### References
- [LambdaMOO Programmer's Manual](http://www.moo-obsessed.com/papers/LambdaMooRef.html)
- [MOO Programming Guide](https://www.cs.clemson.edu/~mark/moo.html)
- [Wetware: MOO as Social Infrastructure](https://wetware.cool/blog/moo-as-social-infrastructure)

---

## What MOO Has That D-JIT Could Use

### 1. Object Model
MOO's object model is surprisingly modern:
- Objects are first-class
- Properties are dynamic (can be added at runtime)
- Verbs are methods attached to objects
- Inheritance with multiple parents

### 2. Capability-Based Security
```moo
player.can_do_something -> bool
```

### 3. Persistent World State
Every property write is immediately persisted. State survives disconnection.

### 4. Player-Created Content
Players create objects, verbs, properties. The MOO grows organically.

### 5. Message Passing
```moo
object:verb(arg1, arg2)
```

### 6. The "Recursion Problem"
The initial MOO database had to be created, but the database was stored in the MOO itself.

---

## MOO → Synapse Mapping

| MOO | Synapse |
|-----|---------|
| Object | Blob |
| Property | Data blob (data/*) |
| Verb | Blob (application/*) |
| Room | Scope / vault region |
| Player | Node |
| Exit | Link (invocation chain) |
| Object ID `#1234` | Stable ID (see design/OBJECT-MODEL.md) |
| Inheritance | Composition via references |
| Object permissions | Governance expression |
| Creation room | Genesis blob |
| Player programmer | AI agent |

---

## Interesting MOO Properties

### The "Soft" Nature
MOO had no compile step. Code was entered as text and executed immediately. Easy to change, hard to version.

**Question:** Should blobs be versioned? Current design: immutable, referenced by hash.

### The "Living" World
MOO worlds were alive because players contributed. The world evolved through player action.

**Synapse:** GOKR + council convergence. The fabric evolves through governed contribution.

### The "First Login" Problem
First login → creation room → build yourself.

**Synapse:** Genesis blob + cold boot.

### Social Governance
Admins could modify anything, but did so sparingly. Social enforcement.

**Synapse:** Governance expression + quorum. Social pressure encoded as cryptographic constraints.

### The "Unwind" Problem
MOO code could corrupt the database. Recovery required admin intervention.

**Synapse:** Immutable blobs. No corruption possible — only new blobs.

---

## MOO-Inspired Ideas

### Object-Capability Model
```json
{
  "capabilities": ["network", "filesystem", "spawn"],
  "parent_capabilities": ["parent_blob_hash"]
}
```

### Verb Namespaces
```moo
$room:open_door()
```

### Living Vault Metadata
```json
{
  "description": "Doubles a number",
  "author": "agent_xyz",
  "created_at": 1234567890,
  "usage_examples": ["..."]
}
```

---

## Questions for Synapse

1. **Object identity:** MOO objects had persistent IDs (`#1234`). Synapse blobs have hashes. Is this sufficient or do we need named objects?

2. **State mutation:** MOO objects could be mutated. Synapse blobs are immutable. Is append-only sufficient for all use cases?

3. **Access control:** MOO had fine-grained permissions. Synapse has governance expressions. Is this the right abstraction level?

4. **Player/agent creation:** In MOO, players created themselves. In Synapse, what creates new nodes/blobs?

5. **The genesis problem:** How does the first blob get created without a prior blob?

---

## See Also

- [design/OBJECT-MODEL.md](../design/OBJECT-MODEL.md) — Stable IDs, versioning
- [explore/SMALLTALK.md](SMALLTALK.md) — Live coding, metacircular systems
- [explore/BEAM.md](BEAM.md) — Actor model, hot code loading
