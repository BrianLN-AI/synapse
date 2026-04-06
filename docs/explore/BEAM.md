# BEAM: Erlang and Related Systems

## Premise

The BEAM (Bogdan/Björn's Erlang Abstract Machine) powers Erlang and related languages. It provides millions of lightweight processes, hot code loading, and distribution as first-class concepts.

---

## Core Concepts

### Lightweight Processes
- Millions of processes per node
- Isolated state, no shared memory
- Communicates via message passing
- ~300 bytes per process

### Supervision Trees
- Processes organized in trees
- "Let it crash" philosophy
- Supervisors restart failed children
- Fault isolation

### Hot Code Loading
- Update code without stopping
- Old and new code can coexist
- Process can switch versions
- "Zero downtime" deployments

### Distribution
- Transparent across nodes
- Location transparency
- Message passing works the same locally or remotely

---

## Related Systems

| Language | Notable |
|----------|---------|
| **Elixir** | Ruby-ish syntax, Phoenix framework |
| **Gleam** | Static typing, modern tooling |
| **LFE** | Lisp syntax on BEAM |
| **Prolog** | Influenced Erlang's pattern matching |
| **Lumen** | Erlang → WASM compiler |

---

## BEAM → Synapse Mapping

| BEAM | Synapse |
|------|---------|
| Process | Blob invocation |
| Supervision tree | Governance hierarchy |
| Hot code loading | Blob promotion |
| Message passing | Content-addressed invoke |
| Node | Mesh node |
| Mnesia | Vault |
| ETS tables | Telemetry cache |
| `spawn` | Scope creation |
| `init` boot | Genesis bootstrap |

---

## Key Insights

### "Let It Crash" vs. Immutable Blobs

Erlang embraces crashes as recoverable:
```
try ... catch
  throw:{crashed, Reason} -> restart()
end
```

Synapse's approach is different:
- Immutable blobs — can't crash, can only succeed or fail
- Promotion — new blobs replace old
- Fitness function — deprecate rather than recover

**Question:** Should Synapse support "try/recover" semantics, or is immutability + promotion sufficient?

### Reference Counting is Implicit

Erlang processes hold references (PIDs). When process dies, references go away. No explicit GC of references.

Synapse scopes hold references (hashes). When scope loses reference, blob can be GC'd.

**Similarity:** Both use reference counting implicitly.

### The Mnesia Question

Mnesia = distributed, reactive database on BEAM:
- Tables replicated across nodes
- Schema can change at runtime
- Reactive queries (select where changed)

**Synapse parallel:** Telemetry vault with scope-aware queries.

---

## Open Questions

1. **Supervision for scopes?** Should scopes have parent/child relationships with crash recovery?

2. **Hot code loading?** Can Synapse support "load new blob version without restarting invocations"?

3. **Distribution transparency?** Should invocation work the same locally and across nodes?

4. **ETS for telemetry?** Should telemetry cache use an ETS-like structure for fast reads?

---

## References

- [Erlang.org](https://www.erlang.org)
- [Learn You Some Erlang](https://learnyousomeerlang.com/)
- [Elixir School](https://elixirschool.com/)

---

## See Also

- [explore/MOO.md](MOO.md) — MOO object model
- [explore/SMALLTALK.md](SMALLTALK.md) — Live coding
- [design/SCOPE.md](../design/SCOPE.md) — Scope model
