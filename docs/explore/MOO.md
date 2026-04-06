# MOO Exploration: Object-Oriented MUDs and the D-JIT Fabric

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

## Canonical MOO Systems

| System | Created | Notable |
|--------|---------|---------|
| **LambdaMOO** | 1990, Xerox PARC | Canonical; first widely-deployed MOO |
| **MOO-Central** | 1990s | Major public MOO |
| **MOO Japan** | 1990s | Japanese MOO culture |
| **FrobMOO** | Various | Gaming-oriented MOOs |
| **MOO.se** | Various | Swedish academic MOOs |

### LambdaMOO Reference
- [MOO Programming Guide](https://www.cs.clemson.edu/~mark/moo.html)
- [Official MOO Documentation](http://www.moo-obsessed.com/papers/LambdaMooRef.html)
- [MOO as Social Infrastructure (Wetware)](https://wetware.cool/blog/moo-as-social-infrastructure)

---

## What MOO Has That D-JIT Could Use

### 1. Object Model
MOO's object model is surprisingly modern:
- Objects are first-class
- Properties are dynamic (can be added at runtime)
- Verbs are methods attached to objects
- Inheritance with multiple parents

**Synapse parallel:** Blobs are immutable objects. The ABI contract defines the interface. The 4-layer stack handles what MOO verbs do.

### 2. Capability-Based Security
MOO objects have permissions:
```
player.can_do_something -> bool
```

**Synapse parallel:** The ABI contract + scrubbed scope + governance expression.

### 3. Persistent World State
MOO world state survives disconnection. Every property write is immediately persisted.

**Synapse parallel:** The append-only vault. Telemetry is persisted. Manifest is the "world state."

### 4. Player-Created Content
MOO players create objects, verbs, properties. The MOO grows organically.

**Synapse parallel:** Blob creation is the equivalent. The vault grows organically.

### 5. Message Passing
Objects communicate via:
```
object:verb(arg1, arg2)
```

**Synapse parallel:** Blob invocation. Content-addressed calls.

### 6. The "Recursion Problem"
MOO had a bootstrap problem: the initial MOO database had to be created, but the database was stored in the MOO itself.

**Synapse parallel:** The `_raw_get` bootstrap. The genesis blob problem.

---

## What Synapse Has That MOO Didn't

| MOO | Synapse |
|-----|---------|
| Mutable objects | Immutable blobs (append-only) |
| Text-based world | Content-addressed computation |
| Single-server | Distributed mesh |
| Object-level security | Hash-based identity + governance |
| Linear world (rooms) | Address-space (content addressing) |
| No verification | ZK proof layer |
| No fitness function | f(Link) optimization |
| Single-threaded interpreter | Multi-runtime (Python, JS, WASM) |
| Human players | AI agents |

---

## Key MOO Concepts Mapped to Synapse

### Room → Vault Region
In MOO, rooms contain objects. In Synapse, vaults contain blobs. Both are persistent storage with content-based addressing.

### Player → Node
Players are agents in MOO. Nodes are runtimes in Synapse.

### Exit → Link
Exits connect rooms. Links connect blobs (invocation chains).

### Verb → Blob (application/*)
Verbs are callable code. Blobs are executable code.

### Property → Data Blob (data/*)
Properties are named values. Data blobs are named content.

### Inheritance → Composition via References
MOO objects inherit. Synapse blobs reference other blobs.

### Object Permissions → Governance Expression
MOO: `player can call verb`
Synapse: `governance expression approves blob`

### MOO Programmer → AI Agent
MOO allowed players to extend the world. Synapse allows AI agents to propose blob mutations.

---

## Interesting MOO Properties for Synapse Design

### 1. The "Soft" Nature of MOO
MOO had no compile step. Code was entered as text and executed immediately. This made it very "soft" — easy to change, hard to version.

**Question for Synapse:** Should blobs be versioned? Current design is not — blobs are immutable and referenced by hash.

### 2. The "Living" World
MOO worlds were alive because players contributed. The world evolved through player action.

**Synapse parallel:** The GOKR + council convergence. The fabric evolves through governed contribution.

### 3. The "First Login" Problem
When you first logged into a MOO, you appeared in a special "creation room" where you could build yourself.

**Synapse parallel:** Genesis blob + cold boot. The bootstrap process creates the initial environment.

### 4. Social Governance
MOO had social enforcement. Admins could modify anything, but they did so sparingly because it would anger players.

**Synapse parallel:** Governance expression + quorum. Social pressure encoded as cryptographic constraints.

### 5. The "Unwind" Problem
MOO code could corrupt the database. Recovery required admin intervention.

**Synapse parallel:** Append-only vault. No corruption possible — only new blobs.

---

## MOO-Inspired Ideas for Synapse

### 1. Object-Capability Model for Blobs
MOO had fine-grained permissions. Synapse could add capability tokens to blobs:
```
{
  "capabilities": ["network", "filesystem", "spawn"],
  "parent_capabilities": ["parent_blob_hash"]
}
```

### 2. Blob Inheritance (Composition)
MOO objects could inherit from parents. Synapse could allow blobs to declare dependencies:
```
{
  "inherits_from": ["hash1", "hash2"],
  "overrides": ["method1"]
}
```

### 3. Verb Namespaces
MOO verbs had namespaces (e.g., `$room:open_door()`). Synapse could add typed invocation:
```
blob_type:verb_name(hash, context)
```

### 4. Player-Created Blobs
MOO let players create verbs. Synapse could let AI agents create blobs via governance.

### 5. The "Living Vault"
MOO worlds were described textually. Synapse could add descriptive metadata to blobs:
```
{
  "description": "Doubles a number",
  "author": "agent_xyz",
  "created_at": 1234567890,
  "usage_examples": ["..."]
}
```

---

## Questions

1. **Object identity:** MOO objects had persistent IDs (`#1234`). Synapse blobs have hashes. Is this sufficient or do we need named objects?

2. **State mutation:** MOO objects could be mutated. Synapse blobs are immutable. Is append-only sufficient for all use cases?

3. **Access control:** MOO had fine-grained permissions. Synapse has governance expressions. Is this the right abstraction level?

4. **Player/agent creation:** In MOO, players created themselves. In Synapse, what creates new nodes/blobs?

5. **The genesis problem:** How does the first blob get created without a prior blob?

---

## References

- [LambdaMOO Programmer's Manual](http://www.moo-obsessed.com/papers/LambdaMooRef.html)
- [MOO Programming Guide](https://www.cs.clemson.edu/~mark/moo.html)
- [Wetware: MOO as Social Infrastructure](https://wetware.cool/blog/moo-as-social-infrastructure)
- [Wikipedia: MOO](https://en.wikipedia.org/wiki/MOO)
- [Eric Mack's MOO Papers](http://www.moo-obsessed.com/papers/)

---

## Next Steps

1. Research LambdaMOO architecture in depth
2. Map MOO security model to capability-based security
3. Design "blob inheritance" as composition
4. Explore "living vault" metadata
5. Define "player/agent" creation in Synapse context
