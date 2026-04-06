# ADR-020: AST-Only Deterministic Verification

**Date:** 2026-04-06
**Status:** ACTIVE
**Author:** D-JIT Fabric
**Branch:** `explore/codemode-proxy`

---

## Summary

Replace AI-based semantic auditing with deterministic AST (Abstract Syntax Tree) analysis in the kernel's preparation phase. The AST auditor enforces structural invariants (forbidden globals, output assignment) at parse time, eliminating probabilistic verification failures.

---

## Context

The `imagine` verb's convergence loop was failing due to:
1. **AI Auditor hallucinations** — rejecting valid code for fictional safety issues
2. **JSON parse failures** — AI returning markdown-wrapped JSON
3. **Format mismatches** — AI generating `return { }` vs required `result = { }`
4. **Slow convergence** — 3-5 attempts per mutation due to audit failures

The system's verification wall was too high relative to the planner's capability.

---

## Decision

Implement **AST-only deterministic verification**:

1. **AST Auditor** (`ast_auditor.ts`):
   - Parse code with Acorn
   - Walk AST to detect forbidden globals (`console`, `fetch`, `globalThis`, `process`, `eval`)
   - Verify output assignment (`result = x` or `return x`)
   - Throw on structural violation before execution

2. **Kernel Integration** (`kernel.ts`):
   - AST audit runs in `engine.prepare()` before function construction
   - Fast-fail on parse/syntax errors
   - Supports both `return x` and `result = x` patterns

3. **Simplified `imagine` verb**:
   - Remove AI semantic audit phase
   - Trust deterministic AST checks
   - Convergence loop: Plan → AST Trial → Promote

---

## Consequences

### Positive
- **Deterministic:** Same code always passes or fails
- **Fast:** No AI round-trip for audit
- **Clear errors:** AST errors directly indicate the problem
- **Invariant enforcement:** Structural rules are mathematically verifiable

### Negative
- **No semantic safety:** AST cannot detect logic errors, only structural violations
- **Limited expressiveness:** Some valid patterns might be rejected (e.g., complex control flow)

---

## Implementation

```typescript
// ast_auditor.ts
export function auditAST(code: string): AuditResult {
  const ast = parse(wrappedCode, { sourceType: 'script' });
  // Walk tree: check forbidden globals, result assignment, return statement
  // Return { safe: true } or { safe: false, reason: "..." }
}

// kernel.ts:prepare()
async prepare(payload: string) {
  const audit = auditAST(payload);
  if (!audit.safe) throw new Error(`[AST-AUDIT] ${audit.reason}`);
  // ... continue with function construction
}
```

---

## Flag

[CHERRY-PICK CANDIDATE]

The AST auditor is a standalone module that can be cherry-picked into any future engine variant. It provides the **structural** half of verification; future work can add **semantic** verification as a separate layer if needed.

---

## References

- `explore/functional/ast_auditor.ts`
- `explore/functional/kernel.ts` (prepare phase)
- `docs/INVARIANTS.md` (Constitutional Invariants)