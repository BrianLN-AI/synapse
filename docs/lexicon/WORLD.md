# WORLD.md — The Content-Addressable Substrate

**Status:** Soft Definition (f_0-f_11 baseline)
**Updated:** Added Node and Root (#0) concepts.

---

## The Soft Definition

**The World** is the **logical image of existence** in the Synapse fabric. It is an append-only, content-addressed graph of **Expressions** hosted on the **Substrate**. 

In the World, **Existence is Identity**. To exist is to be named.

---

## Relationship to Substrate

While the **Substrate** is the physical medium (the bits and the vault), the **World** is the **Meaningful Topology** built upon it. Multiple Worlds can exist on the same Substrate through different **Root Labels**.

---

## The Interface: Symmetry of Identity

The World provides a minimal, symmetric interface for managing identity:

1.  **name(expression) → Hash:** The act of **Naming**. It takes an atomic unit of content (an Expression) and derives its canonical identity. It is a deterministic injection: same content always produces the same name.
2.  **resolve(id) → Expression:** The act of **Resolution**. It takes a name (a Hash) and retrieves the corresponding content from the substrate.

---

## The "Anatomy" of the World

The World is composed of two primary types of expressions:

### 1. Expressions (Logic/Data)
Atomic units of content. A `logic/javascript` expression is a function; a `data/json` expression is a value. They have no state of their own—only their payload.

### 2. Nodes (The World Objects)
A **Node** is an expression that represents a "Point" in the World. It contains:
- **Properties (props):** The state of the node (e.g., `name`, `counter`).
- **Verbs (verbs):** A map of names to **Expression Hashes** (e.g., `greet -> 0xABC`). These are the capabilities of the node.

---

## Root Node (#0) — The Genesis

**Node #0** is the **Directory of Service Hashes**. It is a shared node in the World that acts as the entry point for all new sessions. 

- **Tenancy:** Global / Public Partition.
- **Scope:** Points to universal service verbs (`lookup`, `list`, `search`).
- **Access:** Every **Projection** is initialized with a reference to #0, allowing the code to discover capabilities by name instead of hardcoding hashes.

---

## The Rule of Identity

A thing that does not have a name in the World **does not exist** to the fabric. 
A thing whose name is known but cannot be resolved is a **Void**.
A thing that is resolved and matches its name is a **Truth**.
