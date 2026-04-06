# ENGINE.md — The Execution Host

**Status:** Soft Definition (f_0-f_11 baseline)

---

## The Soft Definition

An **Engine** is a pluggable component of the **Arbiter** (Kernel) responsible for executing a specific type of **Expression**.

While the Arbiter manages **Identity** and **Messaging**, the Engine manages **Execution** and **Isolation**.

---

## The Engine Contract

Every engine must implement a single primitive motion:

### execute(payload, dispatchers, context) → result

1.  **payload**: The raw content of the Expression (e.g., JS code, Lisp S-expressions).
2.  **dispatchers**: The set of **Projected Namespaces** (`fabric`, `world`, `ai`) provided by the Arbiter.
3.  **context**: The **Node State** for the current message.
4.  **result**: The value returned to the Arbiter, fulfilling the ABI.

---

## Pluggability

Engines are registered with the Arbiter by **Expression Type**. This allows the fabric to be polyglot:

- `logic/javascript` → **JSIsolateEngine** (Uses `new Function` or `workerd`).
- `logic/lisp` → **SExprEngine** (Uses an internal interpreter).
- `logic/python` → **PyodideEngine** (Uses WASM).

---

## Vantages

### [PHYSICIST] — The Isolate
The Engine is the physical containment field. It ensures that the "Energy" of the logic does not leak into the "Mass" of the host.

### [ALGEBRAIST] — The Interpreter
The Engine is the function that maps the **Syntax** of an Expression to the **Semantics** of the Fabric Protocol.

### [BUILDER] — The Runtime
The Engine is the part of the system that is most sensitive to the **Host Environment**. A Cloudflare Engine looks different from a Browser Engine, but they both satisfy the same Arbiter contract.
