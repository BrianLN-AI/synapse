# LOGICAL_ARCHITECTURE.md — The D-JIT Codemode Topology

**Status:** Current Implementation (f_0-f_11 baseline)
**Branch:** `explore/codemode-proxy`

---

## 1. The Topology

The system is organized into four layers of increasing abstraction and decreasing privilege:

### Layer 0: The Substrate (`world_persistent.ts`, `hashing.ts`)
- **Nature:** A BLAKE3 content-addressed persistent image.
- **Implementation:** Append-only JSONL event log (`world_state.jsonl`).
- **Rule:** Existence = Identity. Every event is immutable and auditable.
- **Features:** Providence tracking (ts, cause), Labels (mutable pointers to content-addressed state).

### Layer 1: The Arbiter (`kernel.ts`)
- **Nature:** The "Fair Arbiter" (Nanokernel).
- **Role:** 
  - Handles context-switching between Nodes.
  - Manages the Engine registry (logic/javascript, logic/lisp).
  - **AST Auditor:** Deterministic structural verification before execution.
  - Facilitates messaging via Namespace Projections.

### Layer 2: The Projections (`projection.ts`)
- **Nature:** Interface Shadows (`fabric`, `world`, `ai`).
- **Role:** Maps user-space intents to World-space actions. Strips host mass (console, fetch, globalThis) to maintain isolation.

### Layer 3: The Expressions (World)
- **Nature:** Units of Logic (Verbs) and State (Nodes).
- **Implementation:** Content-addressed blobs stored in Substrate.
- **Formats:** `logic/javascript`, `logic/lisp`, `doc/plan`.

---

## 2. The Execution Lifecycle

Every message to the World follows a strict 4-phase physical lifecycle:

```
1. Preparation:   Engine translates payload → cached Artifact
                  └─ AST Auditor runs deterministic checks here
2. Projection:    Arbiter injects namespace proxies (fabric, world, ai)
3. Reduction:     Logic executes, interacting via projections only
4. Resolution:    Logic assigns to `result` (or returns), isolate dissolves
```

---

## 3. The Mutation Protocol (`imagine` verb)

Autonomous growth via the **`imagine`** verb:

```
Planning (AI) → AST Trial → Promotion
     │              │           │
     │              │           └─ Root label updated to new Node hash
     │              └─ Deterministic verification in kernel.ts:prepare
     └─ AI generates: { newVerbs, newProps, testCase }
```

**Features:**
- **Convergence Loop:** Retries on AST failure (up to 3 attempts).
- **Providence:** Captures `planHash` — the "cause" of every mutation.
- **Deterministic Verification:** AST-only (no AI semantic audit) — faster, deterministic.

---

## 4. Primal Service Verbs

- **`fabric.name`**: Content-address a new expression → returns hash.
- **`fabric.resolve`**: Retrieve expression by hash.
- **`fabric.call`**: Recursive messaging (invoke verb on node).
- **`fabric.promote`**: Update label to new hash (evolutionary commitment).
- **`fabric.log`**: Debugging output via proxy.
- **`world.search`**: Query the World for matching verbs.
- **`ai.inference`**: The Intelligence Bridge (Groq/Llama).

---

## 5. ABI Contract

Every verb must conform to the Synapse ABI:

```javascript
// Valid: return statement
return { pong: true };

// Valid: result assignment  
result = { pong: true };

// Forbidden: console, fetch, globalThis, process, eval
```

The **AST Auditor** enforces this deterministically:
- Parse → Walk AST → Check for forbidden globals, ensure output assignment.