# PROJECTION.md — The Interface Shadow

**Status:** Soft Definition (f_0-f_11 baseline)
**Supersedes:** Shadow (The Isolation-centric model)

---

## The Soft Definition

A **Projection** is the **Interface** provided by the **Arbiter** (Kernel) to an execution. It is a silhouette of a familiar system (like `fs`, `os`, or `window`) that maps user-space "Intents" to **World**-space "Actions."

It is a **Proxy for Capability**.

---

## The Anatomy of the "Shadow" (Historical Context)

We initially used the term "Shadow" to describe this interface. Its anatomy reveals the core constraints of the fabric:

1.  **The Silhouette (Shape without Mass):** An LLM expects a system like `fs` or `os`. If we give it nothing, it fails. If we give it a Shadow, we provide the **silhouette** (the functions, the names, the patterns it is trained on) without the **mass** (the actual disk access, the root permissions). The code "touches" the shadow, but the shadow is just a 2D projection of the 3D **World**.
2.  **The Cave (Plato’s Vantage):** In the **[PHENOMENOLOGIST]** vantage, the code is like the inhabitant of the cave. It cannot see the **Ideal Forms** (the immutable hashes in the World). It only sees the **Shadows** cast on its local wall. The **Arbiter** is the one holding the torch, deciding which shadows to project.
3.  **Shadowing as Override (Systems Programming):** In traditional OS kernels, "Shadowing" (e.g., Shadow Page Tables or Shadowing a Registry) refers to intercepting an access and providing a local, virtual version of it. We "shadow" the host environment to prevent the code from leaking out.

---

## Why "Projection" instead of "Shadow"?

We have transitioned from "Shadow" to **"Projection"** (the ALGEBRAIST term) for three reasons:

1.  **Directionality:** A shadow is a passive byproduct; a **Projection** is an intentional mathematical mapping from the **World** (higher dimension) to the **Isolate** (lower dimension).
2.  **Algebraic Rigor:** A projection is a **Homomorphism**. It preserves the **Interface Shape** (the names and types) while changing the **Execution Substance** (the underlying content-addressed logic).
3.  **Multiplicity:** "Shadow" implies a single dark image. "Projection" allows for multiple simultaneous mappings of the same **World** (e.g., a "Linux-like" projection and a "Smalltalk-like" projection) to different actors.

---

## Implementation Pattern

In Synapse, the Projection is implemented as a **JS Proxy Object**. 

- **Input:** A property access (e.g., `system.storage.name`).
- **Mechanism:** The Proxy traps the access and sends a **Message** to the **Arbiter**.
- **Output:** The Arbiter resolves the intent to an **Expression** in the **World** and executes it.
