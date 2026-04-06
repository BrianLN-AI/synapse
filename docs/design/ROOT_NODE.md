# ROOT_NODE.md — The Directory of Service

**Status:** Soft Definition (f_0-f_11 baseline)

---

## The Role of #0

**Node #0** is the **Genesis Node** of any World instance. It serves as the **Directory of Service Hashes**, allowing new expressions and projections to orient themselves and discover capabilities by name.

---

## Topology

- **Residency:** Global Partition (Publicly readable).
- **Structure:** A standard **Node** whose `verbs` map contains references to the most useful **Service Expressions** in the fabric.
- **Precedence:** #0 is the root of the **Stare Decisis** chain for objectives (GOKR) and service contracts.

---

## The "lookup" Primal Capability

The Arbiter provides a `system.lookup(name)` capability. 

- **Mechanism:** When called, the Arbiter searches the `#0` node's `verbs` map for the name.
- **Output:** It returns a **Projected Interface** (Shadow) for the resolved Expression hash.
- **Benefit:** Code no longer needs to hardcode hashes. It only needs the "Name" (The Sign) and the Arbiter handles the "Resolution" (The Truth).

---

## Example Usage

```javascript
// Orienting from the Root
const logger = await system.lookup("global_logger");
await logger.log("System initialized from Node #0.");
```

---

## Bootstrapping #0

In a new World, the first act is the **Genesis Promotion**:
1. Name the primal service expressions (`lookup`, `log`, `inference`).
2. Name a Node whose `verbs` point to these expressions.
3. Designate this Node's hash as `#0` in the Arbiter's local configuration.
