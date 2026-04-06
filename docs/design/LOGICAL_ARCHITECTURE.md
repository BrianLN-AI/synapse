# LOGICAL_ARCHITECTURE.md — The D-JIT Codemode Topology

**Status:** Current Implementation (f_0-f_11 baseline)
**Branch:** `explore/codemode-proxy`

---

## 1. The Topology

The system is organized into four layers of increasing abstraction and decreasing privilege:

### Layer 0: The Substrate (`SUBSTRATE.md`)
- **Implementation:** `world_persistent.ts`, `hashing.ts`.
- **Nature:** A BLAKE3 content-addressed persistent image.
- **Rule:** Existence = Identity. Every bit is immutable and auditable.

### Layer 1: The Arbiter (`KERNEL.md`)
- **Implementation:** `kernel.ts`.
- **Nature:** The "Fair Arbiter" (Nanokernel).
- **Role:** Handles context-switching, manages the Engine registry, and facilitates messaging via Namespace Projections.

### Layer 2: The Projections (`PROJECTION.md`)
- **Implementation:** `projection.ts`.
- **Nature:** Interface Shadows (`fabric`, `world`, `ai`).
- **Role:** Maps user-space intents to World-space actions. Strips host mass (console, fetch) to maintain isolation.

### Layer 3: The Expressions (`WORLD.md`)
- **Implementation:** `world_state.json`.
- **Nature:** Units of Logic and State.
- **Role:** Content-addressed blobs (Verbs) and Nodes (Nouns) that define the system's behavior.

---

## 2. The Execution Lifecycle (`ENGINE.md`)

Every message to the World follows a strict 4-phase physical lifecycle:
1. **Preparation:** Engine translates payload (e.g., TS -> JS) and generates a cached Artifact.
2. **Projection:** Arbiter injects namespace proxies and sanitizes the scope.
3. **Reduction:** Logic executes, interacting with the World only through projections.
4. **Resolution:** Logic assigns to `result`, isolate is dissolved, and value is returned.

---

## 3. The Mutation Protocol (`VERIFICATION.md`)

Autonomous growth via the **`imagine`** verb follows a high-integrity lifecycle:
- **Phase 1: Planning:** AI Architect generates logic, state, and test cases.
- **Phase 2: Audit:** A second AI model reviews the code for Synapse ABI safety.
- **Phase 3: Trial:** A dry-run execution against the test case in a transient node.
- **Phase 4: Promotion:** The label (Route) is updated to the new hash (Address).

---

## 4. Primal Service Verbs

- **`fabric.name/resolve`**: Identity management.
- **`fabric.call`**: Recursive messaging.
- **`fabric.promote`**: Evolutionary commitment.
- **`world.lookup`**: Service discovery via the Root Node (#0).
- **`ai.inference`**: The Intelligence Bridge.
