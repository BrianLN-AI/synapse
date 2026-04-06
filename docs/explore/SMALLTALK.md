# SMALLTALK: Live Coding and the Living Image

## Premise

Smalltalk created systems where code could be modified while running. The "image" was the world — a single file containing the entire running state. The bootstrap was the language itself.

---

## Core Concepts

### Image-Based Persistence
- Entire running state in one file
- Objects, classes, contexts all persisted
- "Resume where you left off"
- No separate "source code" and "running system"

### Everything is an Object
- Numbers are objects
- Classes are objects
- Methods are objects
- The world is objects all the way down

### Message Passing
```smalltalk
receiver message: arg
```
Not "calling a method" — sending a message. Receiver decides how to respond.

### Live Coding
- Modify code while running
- Change class, changes apply immediately
- No compile step
- REPL is the world

### Metacircular
- Compiler written in Smalltalk
- IDE written in Smalltalk
- Everything self-hosted

### Bootstrap Problem
How does the image boot itself?
- Seed image with minimal objects
- Compiler builds more objects
- Full image emerges from minimal seed

---

## Related Systems

| System | Notable |
|--------|---------|
| **Squeak** | Croquet OS, Etoys, JIT innovations |
| **Pharo** | Clean fork, modern tooling |
| **Self** | Prototype-based, generational GC |
| **VisualWorks** | Commercial Smalltalk |
| **Amber** | Smalltalk → JavaScript |
| **GNU Smalltalk** | Minimal, scripting |
| **LISP images** | MacLISP, Emacs — similar image model |

---

## Smalltalk → Synapse Mapping

| Smalltalk | Synapse |
|-----------|---------|
| Image | Vault + Scope |
| Object | Blob |
| Method lookup | Content address resolution |
| Message send | Blob invocation |
| Metaclass | Engine-as-expression |
| Workspace | Telemetry |
| Image bootstrap | Genesis blob |
| Class hierarchy | Blob composition / inheritance |
| Live coding | Blob promotion (with hot loading?) |

---

## Key Insights

### Live Coding vs. Immutable Blobs

Smalltalk: modify running code directly. Changes apply immediately.

Synapse: immutable blobs. To change behavior, promote new blob.

**Question:** Does Synapse need hot code loading? Can blobs be updated without full promotion cycle?

### The Bootstrap Chain

Smalltalk:
```
Minimal seed → compiler → more objects → full image
```

Synapse:
```
Genesis blob → initial fabric → blob creation → full vault
```

**Question:** How does genesis blob get created? What is the minimal seed?

### Metacircular Architecture

Smalltalk compiler is written in Smalltalk. The language bootstraps itself.

Synapse:
- Engine is a blob (f_13+)
- Fabric can modify fabric
- Self-referential

### "Workspace" as Telemetry

Smalltalk workspace = live REPL with history.

Synapse telemetry = execution record with history.

---

## Open Questions

1. **Hot code loading?** Can Synapse update blob behavior without full promotion?

2. **Live REPL?** Should there be a "workspace" mode for interactive exploration?

3. **Image backup?** Can scopes be snapshotted like Smalltalk images?

4. **Bootstrap chain?** What is the minimal genesis, and how does it build the full fabric?

---

## References

- [Pharo by Example](http://pharobyexample.org/)
- [Squeak: A Quick Tour](https://handwiki.org/wiki/Squeak)
- [Self Language](http://www.selflanguage.org/)

---

## See Also

- [explore/MOO.md](MOO.md) — MOO object model
- [explore/BEAM.md](BEAM.md) — Actor model
- [design/BOOTSTRAP.md](../design/BOOTSTRAP.md) — Genesis and cold boot (TODO)
