# IDENTITY.md — Addresses vs. Routes

**Status:** Soft Definition (f_0-f_11 baseline)

---

## The Logical Distinction

In the D-JIT Fabric, we distinguish between how a thing is **located** (Address) and how it is **reached** (Route).

### 1. Hash (The Address)
An **Address** is an **Immutable identity** derived from content (Invariant I).

- **Formalism:** [MATHEMATICIAN] — The Fixed Point.
- **Nature:** Permanent and Inviolable. It is the thing itself.
- **Metaphor:** GPS Coordinates. They describe a specific point in the World that never moves.
- **Role:** Provides the "Truth" for every message and resolution.

### 2. Label (The Route)
A **Route** is a **Mutable pointer** that points to an Address.

- **Formalism:** [ALGEBRAIST] — The Homomorphism.
- **Nature:** Temporal and Indirect. It is a "Sign" for a current state.
- **Metaphor:** A Street Name. "Main Street" can be moved to a different physical road, but the name persists as a way to navigate.
- **Role:** Provides the "Intent" for discovery. It allows the World to evolve while the code references a stable name.

---

## The Interaction

The **Arbiter** (Kernel) acts as the **Navigator** between these two spaces:

1.  **Resolution:** The Arbiter follows a **Route** (Label) to find its current **Address** (Hash).
2.  **Promotion:** The act of updating a **Route** to point to a new **Address**. This is the only "write" operation that allows for logical continuity in a content-addressed World.
3.  **Messaging:** Messages can be sent to either an Address (direct) or a Route (indirect). 

---

## Why the Distinction Matters

This separation allows for **Immutable History** combined with **Mutable Logic**:
- The **World** retains every Address that has ever existed (The Audit Trail).
- The **Arbiter** projects the latest Address via the Route (The Living System).
- The **AI** (and other logic) can reason about "The Root" or "The User" without needing to know the specific content-hash of the current second.
