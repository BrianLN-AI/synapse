# KERNEL.md — The Honest Foundation

**Status:** Soft Definition (f_0-f_11 baseline)
**Updated:** Added Recursive Kernel and Verb Types.

---

## The Soft Definition

A **Kernel** is the **minimal, irreducible part of the system** that must be correct for everything else to be possible. It is the part of the code that doesn't change until it is powerful enough to change itself (Invariant IV).

---

## The Recursive Kernel (Invariant IV)

Because of the recursion invariant, there is an infinite mirror of kernels. Every layer can act as a **Nanokernel** for the layer below it and a **Service** for the layer above it.

1.  **Nanokernel (The Arbiter):** The minimal functional code (e.g., `shadow_arbiter.ts`) that implements `resolve`, `name`, and `message`.
2.  **Microkernel (The Linker):** A layer of **Service Expressions** (stored in the World) that provides higher-level projections (Filesystems, Networks).
3.  **Exokernel (The World-Direct):** Raw access to the **World** substrate.

---

## Capability Distribution (Verbs)

The Arbiter manages different types of capabilities based on their **Tenancy** and **Scope**:

### 1. Primal Verbs (Nanokernel)
`name`, `resolve`, `message`. These are **Intrinsic Projections**—injected directly into every Shadow. They are the only way to interact with the World.

### 2. Bridge Verbs (Arbiter / Mass)
`inference`, `network`, `log`. These bridge the **Fabric** to the **Host Mass** (API keys, hardware). They are **Authorized Projections** that require a `govern` check.

### 3. Service Verbs (Microkernel)
`lookup`, `search`, `fs`. These live as **Expressions in the World**. They are accessed via **Message Passing** to their specific hashes.

### 4. User Verbs (Application)
Verbs defined by the user (e.g., `greet`, `mutate`). They live in the user's **Private Partition** and are only reachable within their specific **Scope Closure**.

---

## Summary

The kernel is the **Fair Arbiter**. it projects the **Interface Shadow** while protecting the **World** (the persistent truth) and managing the **Partition** (Authorization).
