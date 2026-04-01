# The Protocol Layer

*Design notes — captured after f_3, during the discussion of capability surfaces and IDL.*

---

## The Core Inversion

In traditional systems, the protocol IS the interface. You design REST endpoints. You define
a GraphQL schema. You write a gRPC service. The protocol is chosen first and the capability
is built inside it. To expose the same capability via a different protocol, you rebuild.

This fabric inverts that:

**The schema blob is the interface. The protocol is a view.**

A capability is defined once — as a schema blob in the vault, describing what it accepts
and what it returns. The protocol is a generator blob that projects that schema into a
specific communication model:

```
schema blob (canonical)
    ↓
generator blob (target: "rest")      → OpenAPI spec + route handlers
generator blob (target: "graphql")   → type definitions + resolvers
generator blob (target: "grpc")      → .proto file
generator blob (target: "wit")       → WIT component definition
generator blob (target: "json-rpc")  → method registry
generator blob (target: "mcp")       → MCP tool definitions (inputSchema/outputSchema)
generator blob (target: "openapi")   → OpenAPI 3.x document
```

The capability itself is untouched. Protocol support is added, versioned, and governed
independently of the capability it exposes.

---

## Why Protocol Matters More Than It Looks

Protocol is not a transport detail. It is the boundary where trust must be explicitly
declared — the exact point where one system ends and another begins. Every protocol
decision determines:

- **Who can participate.** A capability exposed only as gRPC is not accessible to a browser.
  One exposed as MCP is accessible to any LLM with MCP support. Protocol determines the
  membership of the ecosystem.

- **How trust propagates.** REST has ambient authority by default (any client with a URL
  can call). Cap'n Proto RPC is capability-secure (you can only call what you hold a
  reference to). The protocol choice determines the trust model for external callers.

- **How the system evolves.** Protocol versioning is historically the hardest part of
  distributed systems. Breaking changes in a REST API require client coordination.
  Here, protocol versioning IS schema versioning: old clients pin to an old schema hash,
  new clients get the new one. The vault handles it.

- **What the system can participate in.** The MCP case: a fabric that generates MCP tool
  definitions from its schema blobs can be invoked by any LLM that speaks MCP — including
  the LLM that helped build it. Protocol support is ecosystem membership.

---

## The Generator Blob Model

Each protocol adapter is a blob in the vault. It is:

- **Content-addressed** — the same schema hash + the same generator hash always produces
  the same output. Deterministic. Cacheable. The output can itself be stored as a blob
  keyed by `(schema_hash, generator_hash, target_format)`.

- **Governed** — a generator blob goes through Triple-Pass Review and Council Approval
  before it can produce protocol artifacts for any external caller. The trust model is
  uniform: protocol support for a capability can only be promoted if the generator passed
  review. You cannot add gRPC support for an unreviewed capability.

- **Independently versioned** — the generator for REST v1 and the generator for REST v2
  are separate blobs. You promote the new one. Old callers using the old generator hash
  continue working. Protocol versioning and schema versioning unify into blob versioning.

- **Composable** — a generator can invoke other generators. A "full API bundle" generator
  might call the REST generator, the JSON Schema generator, and the MCP generator and
  return all three artifacts. Each sub-generator is a separate promoted blob.

---

## Protocol Versioning Unified With Schema Versioning

Traditional API versioning:
```
/api/v1/users
/api/v2/users   ← breaking change, new endpoint, old clients must migrate
```

This fabric:
```
schema_v1_hash  → generator produces /api/v1/... endpoints
schema_v2_hash  → generator produces /api/v2/... endpoints
```

There is no migration process. Old clients hold a reference to the schema_v1_hash. New
clients get schema_v2_hash from the manifest. The vault stores both forever. The generator
produces both on demand. The diff between v1 and v2 is visible from the schema blobs alone.

---

## The MCP Connection

MCP (Model Context Protocol) describes a tool as:
- name
- description
- inputSchema (JSON Schema)
- outputSchema (JSON Schema)

A schema blob already contains this information. An MCP generator blob takes a schema hash
and returns an MCP tool definition. Any LLM with an MCP client can then:

- Invoke the capability by hash
- Read the telemetry for any blob
- Trigger an evolution cycle
- Inspect the manifest
- Query governance history

The LLM is not a special case. It is a caller that speaks MCP. The fabric does not need
LLM-specific integration — it generates MCP support from the same schema blobs that
generate REST support. The LLM becomes a first-class participant in the governance and
evolution loop through a protocol it already speaks.

---

## Naming This Layer

Several terms have been used in prior art. Each captures part of the idea:

**"Semantic Layer"** — emphasises that the canonical description is semantic (what the
capability means) not syntactic (how it is encoded). The protocol is syntax; the schema
is semantics. Accurate but abstract.

**"Capability Mesh"** — emphasises the network of capabilities and how they compose.
Captures the distributed/interconnected nature. Good when talking about multiple
capabilities and their relationships.

**"Universal Protocol Adapter"** — emphasises the generation aspect. The fabric adapts
its canonical descriptions to any protocol. Functional and concrete. Best when explaining
to someone unfamiliar with the architecture.

**"Interface Compiler"** — emphasises that generator blobs are compilers: they take a
schema (source language) and produce protocol artifacts (target language). Precise.
Resonates with engineers who think about compilers.

**"Protocol Fabric"** — plays on the fabric metaphor already in use. The fabric weaves
protocols together from a single thread (the schema blob). Cohesive with the project
naming.

**"Rosetta Stone pattern"** — one canonical inscription, many languages derived from it.
Good as a metaphor but not a technical name.

None of these is wrong. They describe the same thing at different levels of abstraction:
- What it is: an interface compiler
- What it does: universal protocol adaptation
- What it produces: a protocol fabric / capability mesh
- Why it works: semantic layer over protocol syntax

---

## The Structural Consequence

The fabric does not "support" protocols. It generates support for them on demand, governed
by the same process that governs everything else. The question "does this fabric speak
GraphQL?" has the same answer as "does this fabric have a planning blob?" — check the
manifest. If a GraphQL generator blob is promoted, it speaks GraphQL. If not, promote one.

This means protocol support is:
- **Auditable** — every promoted generator is in the audit log
- **Reversible** — a generator blob can be demoted if it produces unsafe artifacts
- **Evolvable** — a new generator version supersedes the old one through the standard
  promotion process
- **Testable** — the generator blob goes through Triple-Pass Review like any other blob

The protocol layer is not infrastructure. It is governed compute, same as everything else.

---

## Open Questions

1. **Capability grant at generation time or invocation time?** When a caller asks for an
   MCP tool definition, does the fabric check whether that caller is allowed to invoke the
   underlying capability? Or is generation unconditional and invocation gated separately?

2. **Generator output as a blob?** Should the output of a generator be stored in the vault
   (keyed by `(schema_hash, generator_hash, target)`)? This makes generation free after the
   first call. Or does it introduce staleness risk if the generator is updated but the
   cached output is not invalidated? (Answer: no staleness risk — if either hash changes,
   the cache key changes. Both are content-addressed.)

3. **The trust boundary for MCP.** An LLM with MCP access to this fabric can trigger
   evolution. Is that the right trust level? The governance process (Triple-Pass + Council
   Approval) is the gate — the LLM can propose but not promote unilaterally. That seems
   right, but worth stating explicitly.

4. **Protocol as capability.** Should "speak MCP" be a first-class capability that can
   be granted or revoked, separate from the underlying blob capabilities? Or is it always
   available to any caller that can reach the fabric? The WASI/capability-secure model
   suggests the former.
