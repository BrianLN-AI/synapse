# ABI.md — The Executable Contract

**Status:** Soft Definition (f_0-f_11 baseline)

---

## The Contract

Every **Expression** of type `logic/javascript` must adhere to the Synapse ABI to be valid.

### 1. Injected Namespaces (The Projection)
The Arbiter projects three namespaces into the logic's scope:
- **`fabric`**: Primal motions (`name`, `resolve`, `call`, `log`, `wait`, `list`, `promote`).
- **`world`**: Dynamic service discovery via Node #0.
- **`ai`**: The intelligence bridge (`inference`).

### 2. Contextual State
- **`context`**: A JSON object containing the properties and verbs of the Node currently executing the message.

### 3. Output Requirement
- The logic **MUST** assign its final value to the variable **`result`**. 
- If the intent is to update state, the logic must return a **new state object** that the caller can `fabric.name`.

### 4. Sanitization
- Logic runs in a "Clean Room."
- `console`, `fetch`, `process`, and `globalThis` are **undefined**.
- Use `fabric.log` for telemetry.

---

## Example Pattern

```javascript
// A valid Synapse verb
fabric.log('Processing input:', context.input);
const summary = await ai.inference('Summarize: ' + context.input);
result = { ...context, summary }; 
```
