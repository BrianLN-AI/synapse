# VERIFICATION.md — The Mutation Protocol

**Status:** Soft Definition (f_0-f_11 baseline)

---

## The Mutation Lifecycle

To ensure the World remains stable, every mutation planned by an **`imagine`** verb must pass through a verification loop:

### 1. Planning (Imagine)
The Master Architect (`imagine`) uses AI inference to generate:
- **Logic:** The new verb code.
- **State:** The new property values.
- **Test:** A sample input and expected outcome.

### 2. Syntax Validation
The Arbiter attempts to parse the code. If it contains syntax errors (e.g., `SyntaxError: Cannot declare const result twice`), the mutation is rejected before being named in the World.

### 3. Trial Execution (The Dry Run)
The `imagine` verb performs a **Trial Message**:
1. Create a transient Node with the new logic.
2. Message the logic with a "Safe Context."
3. Verify that it assigns to `result` and does not throw a runtime error.

### 4. Promotion
Only if the Trial Execution succeeds does the `imagine` verb call `fabric.promote('root', newNodeHash)`.

---

## Continuous Verification

Because the World is **Content-Addressed**, we can always "Roll Back" by moving the Route (Label) to a previous Hash. Promotion is a **Proposed Truth** that can be challenged by any agent with the **[ADVERSARY]** vantage.
