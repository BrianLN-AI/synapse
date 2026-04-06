# SYNTHESIS: The Unified Model

> Integrating: MOO, Smalltalk, BEAM, Scope, Object Model, Tools, Dynamic Execution, Agents

---

## The Core Unification

**Everything is a blob with a reference graph.**

| Concept | Blob type | Reference |
|---------|-----------|-----------|
| Code | `application/*` | hash |
| Tool | `tool/*` | schema hash + impl hash |
| Data | `data/*` | hash |
| Memory | `scope/agent` | reference set |
| Query | `query/*` | graph traversal |
| Governance | `governance/*` | expression hash |

**The IR is the blob content.** WASM, TypeScript, JSON, S-expressions — any content with a schema.

---

## The Layer Model

```
┌─────────────────────────────────────────────┐
│                  AGENT                        │
│  Intent (GOKR) + Goals + Memory + Tools   │
├─────────────────────────────────────────────┤
│                  TOOL                        │
│  Schema (interface) + Implementation (blob) │
├─────────────────────────────────────────────┤
│                 SCOPE                        │
│  Reference graph + Capabilities + Context   │
├─────────────────────────────────────────────┤
│                  BLOB                        │
│  Content-addressed executable capability     │
├─────────────────────────────────────────────┤
│                    IR                        │
│  WASM / TypeScript / S-expressions        │
└─────────────────────────────────────────────┘
```

---

## Blob Types

### Application Blob (`application/*`)

Executable code. The IR.

```json
{
  "type": "application/typescript",
  "payload": "async function(input, env) { ... }",
  "runtime": "wasm|v8|python"
}
```

### Tool Blob (`tool/*`)

Executable capability with interface.

```json
{
  "type": "tool/function",
  "schema": {
    "name": "get_weather",
    "parameters": { ... }
  },
  "implementation": "hash_of_ts_blob",
  "runtime": "v8"
}
```

### Query Blob (`query/*`)

Graph traversal definition.

```json
{
  "type": "query/sexp",
  "payload": "(traverse (hash x) GOVERNS (type? 'logic/') BFS)"
}
```

### Governance Blob (`governance/*`)

Fitness expression.

```json
{
  "type": "governance/expression",
  "payload": "(fitness > threshold)"
}
```

---

## Scope

Scope = reference graph + execution context.

```json
{
  "scope": {
    "id": "user-123",
    "type": "agent_memory",
    "references": {
      "tool_hash": { "count": 1, "origin": "created" },
      "data_hash": { "count": 3, "origin": "result" }
    },
    "capabilities": ["invoke", "create_tool", "delegate"],
    "parent": "tenant-scope-id"
  }
}
```

### Scope as Cache

- Scope contains references, not content
- GC when refcount = 0
- Content-addressing = automatic coherence
- Layered: user → tenant → public → cold

### Scope Types

| Type | Lifespan | Contains |
|------|----------|----------|
| `agent_memory` | Persistent | Tools, context, history |
| `invocation` | Ephemeral | Per-call references |
| `query_result` | Ephemeral | Traversal results |
| `deployment` | Versioned | Snapshot |

---

## Tool Model

### Static Tool

Pre-defined at deploy time.

```typescript
// Schema + implementation
const tool = {
  schema: { name: "get_weather", parameters: {...} },
  implementation: "ts_blob_hash"
}
```

### Dynamic Tool (Code Mode)

AI generates code at runtime.

```typescript
// Agent writes TypeScript
const code = `
  export default {
    async run(input, env) {
      let weather = await env.WEATHER.getHistory({city: input.city});
      return weather.temp > 70 ? "warm" : "cold";
    }
  }
`;

// Dynamic Worker = blob with typed capabilities
const tool = {
  schema: { name: "dynamic_tool", parameters: {...} },
  implementation: code,  // Generated blob
  runtime: "v8",
  capabilities: {
    WEATHER: ChatRoomRpcStub  // Typed interface
  }
}
```

### Tool Creation = Blob Creation

A blob can create a tool at runtime:

```javascript
// Tool-creating blob
async function createTool(input) {
  const code = await llm.generateCode(input.description)
  const tool_blob = {
    type: "tool/function",
    schema: input.schema,
    implementation: code,
    runtime: "v8"
  }
  const hash = await vault.put(tool_blob)
  return { tool_hash: hash }
}
```

---

## Agent Model

Agent = Blob with Intent + Memory + Tools.

```json
{
  "agent": {
    "id": "agent-xyz",
    "blob": "hash_of_agent_code",
    "intent": {
      "gokr": "hash_of_gokr_blob",
      "goals": ["goal1", "goal2"]
    },
    "memory": "scope_id",
    "tools": ["tool_hash_1", "tool_hash_2"],
    "context": {
      "user_id": "user-123",
      "tenant_id": "tenant-abc"
    }
  }
}
```

### Agent Memory = Scoped References

```json
{
  "scope": {
    "id": "agent-xyz-memory",
    "type": "agent_memory",
    "references": {
      "history_blob": { "count": 1 },
      "context_blob": { "count": 1 },
      "tool_def_1": { "count": 1 }
    }
  }
}
```

---

## Actor Model

Actor = Scope + Governance Expression.

| Actor (Erlang) | Synapse |
|-----------------|---------|
| Process | Blob invocation |
| Mailbox | Scope |
| Behavior | Blob code |
| Supervision | Governance |
| Link/Monitor | Capability delegation |

**Key difference:**
- Actors are reactive (message passing)
- Agents are proactive (have goals)
- Synapse supports both

---

## The IR Question

### IR Candidates

| IR | Hashable | Portable | Executable | AI-native |
|----|----------|----------|------------|-----------|
| WASM | ✓ | ✓ | ✓ | |
| TypeScript | ✓ | ✓ (V8) | ✓ | ✓ |
| S-expressions | ✓ | ✓ | ~ | ✓ |
| Tool schemas | ✓ | ✓ | | ✓ |

### Homoiconicity

A homoiconic language is one where program code and data have the same representation. The canonical example: S-expressions.

```
;; Code is data
(define foo (lambda (x) (+ x 1)))

;; Data is code
(eval '(+ 1 2))  ; → 3
```

**Why it matters for Synapse:**

| Property | Benefit |
|----------|---------|
| Code = data | Queries can examine code |
| Code = data | Governance can reason about programs |
| Code = data | Programs can generate programs |
| Code = data | Metadata IS the content |

**Synapse blobs are homoiconic by accident:**
```
blob.content = "async function..."  // Code
blob.content = "{...}"              // Data
blob.content = "(traverse...)"     // Query
```

The content is just bytes. The schema determines interpretation.

### Proposed: Layered IR

```
Compute layer:  WASM (portable execution)
Agent layer:    TypeScript (AI-writable)
Query layer:    S-expressions (homoiconic, queryable)
Data layer:    JSON/structured (typed)
```

**Homoiconicity at each layer:**

| Layer | Representation | Code=Data? |
|-------|---------------|------------|
| Compute | WASM | Binary, not homoiconic |
| Agent | TypeScript | Strings are data, eval exists |
| Query | S-expressions | Yes, canonical |
| Data | JSON | Data, not code |

**TypeScript as the AI-executable IR:**
- Hashable: the code string
- Executable: V8/WASM runtime
- Typed: TypeScript interfaces
- AI-native: LLMs trained on vast TS codebases
- Sandboxed: V8 isolates (Cloudflare model)
- Homoiconic-ish: `eval()` works, strings are data

---

## Reference Resolution

When invoking:

```
1. Resolve tool → blob hash
2. Check scope capabilities
3. Load blob → execution context
4. Bind capabilities as env
5. Execute in runtime
6. Return result blob
```

**Cross-scope:**
```
1. Scope A invokes blob in Scope B
2. Reference counted in A
3. B's governance applies
4. Result returned to A
```

---

## The Unified Abstraction

**Program = (blob, scope, capabilities, intent)**

| Component | Content-addressed | Purpose |
|-----------|-------------------|---------|
| blob | hash(content) | The executable |
| scope | hash(references) | The context |
| capabilities | hash(tool_refs) | What can be invoked |
| intent | hash(gokr) | The goal |

**Invocation = closure application**

```javascript
result = invoke(blob, { scope, capabilities, context })
```

**This is hashable end-to-end.**

---

## Comparison with Other Systems

| System | Program is | IR is |
|--------|-----------|-------|
| MOO | Object + verbs | Text |
| Smalltalk | Image | Bytecode + objects |
| Erlang | Process + behaviors | BEAM bytecode |
| Cloudflare | TypeScript + env | JS/TS |
| LangChain | Prompt + tools | Tool schemas |
| Synapse | (blob, scope, cap, intent) | WASM/TS/JSON |

---

### S-Expressions as Universal IR

S-expressions are the pure homoiconic form. They work for:

```lisp
;; Governance expression
(fitness (> success_rate 0.9) (< latency 100))

;; Query
(traverse (hash x) GOVERNS (type? 'logic/') BFS)

;; Blob content
(blob
  (type "tool/function")
  (schema (name "get_weather"))
  (impl "ts_hash"))
```

**S-expressions are:**
- Text, hashable
- Parseable everywhere
- Executable (LISP interpreters are tiny)
- Queryable (pattern matching)
- Human-readable

**The IR hierarchy:**

```
S-expressions  ← Query, Governance (pure homoiconic)
TypeScript     ← Tools, Agents (practical homoiconic)
WASM           ← Compute (efficient, not homoiconic)
JSON           ← Data (structured, not executable)
```

---

## The Genetic Encoding Metaphor

The foundational analogy for understanding Synapse.

| Genetic | Synapse | Function |
|---------|---------|----------|
| DNA | Blob | Heritable pattern |
| RNA | Projection | Transcription to runtime |
| Protein | Execution | Functional output |
| Ribosome | Runtime | Machinery for projection |
| Gene | Blob (capability) | Unit of function |
| Genome | Vault | All patterns |
| Cell | Scope | Containment + capability |

### The Analogy Runs Deep

- **Content-addressed:** DNA sequence = identity. Change sequence = different molecule.
- **Evolution:** Patterns that work survive. Selection on blobs.
- **Expression:** DNA → RNA → Protein. Blob → runtime → execution.
- **Virus:** Blob that hijacks machinery. Tool that uses other tools.
- **Enzyme:** Specific capability. Does one reaction efficiently.
- **Horizontal gene transfer:** Sharing blobs across scopes/environments.
- **Epigenetics:** Governance affects expression without changing DNA.
- **Germline vs. Soma:** Governance (germline) vs. invocation (soma).

See [docs/explore/LIVING-SYSTEMS.md](../explore/LIVING-SYSTEMS.md) for biology connections.

---

## Key Properties

1. **Content-addressing everywhere** — identity = hash
2. **Scope isolation** — references, not copies
3. **Tool = blob with schema** — any capability is addressable
4. **Agents = blobs with intent** — goals are content-addressed
5. **Dynamic tool creation** — blobs can create blobs
6. **TypeScript as AI-native IR** — matches Cloudflare Code Mode
7. **Layered IR** — WASM for compute, TS for AI-executable

---

## Open Questions

1. **Governance of tool creation?** When can blobs create tools? Who reviews?
2. **Capability delegation?** How do scopes pass capabilities to children?
3. **Cross-scope governance?** When A invokes B's blob, whose governance applies?
4. **IR negotiation?** Can agents choose between WASM and TS at runtime?
5. **Versioning tools?** Should tools be versioned or immutable like blobs?
