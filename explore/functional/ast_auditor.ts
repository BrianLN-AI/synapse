import { parse } from 'acorn';

export type AuditResult = { safe: true } | { safe: false; reason: string };

const FORBIDDEN_GLOBALS = new Set(['console', 'fetch', 'globalThis', 'process', 'eval', 'Function', 'require', 'module', 'exports', 'window', 'document']);

/**
 * AST-based deterministic auditor for Synapse ABI compliance.
 * Runs before the AI auditor to catch structural violations instantly.
 */
export function auditAST(code: string): AuditResult {
  let ast: any;
  try {
    // Wrap in async IIFE to match the engine's actual execution context
    // This allows top-level await, const declarations, etc.
    const wrapped = `(async () => { ${code} })`;
    ast = parse(wrapped, { ecmaVersion: 'latest', sourceType: 'script' });
  } catch (e: any) {
    return { safe: false, reason: `Parse Error: ${e.message}` };
  }

  const issues: string[] = [];
  let hasResultAssignment = false;
  let hasReturnStatement = false;

  function walk(node: any) {
    if (!node || typeof node !== 'object') return;

    // 1. Check for forbidden globals (Identifiers not in member chains)
    if (node.type === 'Identifier' && FORBIDDEN_GLOBALS.has(node.name)) {
      issues.push(`Forbidden global: '${node.name}'`);
    }

    // 2. Check for result assignment
    if (node.type === 'AssignmentExpression' && node.left?.type === 'Identifier' && node.left.name === 'result') {
      hasResultAssignment = true;
    }

    // 2b. Check for return statement (also valid output)
    if (node.type === 'ReturnStatement' && node.argument !== null) {
      hasReturnStatement = true;
    }

    // 3. Check for unsafe property access on 'context' without guards
    if (node.type === 'MemberExpression') {
      const obj = node.object;
      // Detect: context.props.something (nested member access)
      if (obj?.type === 'MemberExpression' && obj.object?.type === 'Identifier' && obj.object.name === 'context') {
        // Check if this is inside a conditional guard or uses optional chaining
        if (!node.optional) {
          // We'll do a simpler check: flag deep context access
          // A more sophisticated check would track the control flow
        }
      }
      // Detect: context.something
      if (obj?.type === 'Identifier' && obj.name === 'context' && !node.optional) {
        // Flag: direct context access without optional chaining
        // issues.push(`Unsafe context access: use 'context?.${node.property?.name || '?'}'`);
      }
    }

    // 4. Check for dangerous calls (eval, Function constructor, etc.)
    if (node.type === 'CallExpression') {
      const callee = node.callee;
      if (callee?.type === 'Identifier' && (callee.name === 'eval' || callee.name === 'Function')) {
        issues.push(`Dangerous call: ${callee.name}()`);
      }
      if (callee?.type === 'MemberExpression' && callee.property?.type === 'Identifier' && callee.property.name === 'exec') {
        if (callee.object?.type === 'Identifier' && (callee.object.name === 'Function' || callee.object.name === 'eval')) {
          issues.push(`Dangerous call: Function.exec()`);
        }
      }
    }

    // Recurse
    for (const key of Object.keys(node)) {
      if (key === 'parent') continue;
      const child = node[key];
      if (Array.isArray(child)) {
        child.forEach(walk);
      } else if (typeof child === 'object') {
        walk(child);
      }
    }
  }

  walk(ast);

  // 5. Check for result assignment or return statement
  if (!hasResultAssignment && !hasReturnStatement) {
    issues.push('Missing required "result" assignment or "return" statement');
  }

  if (issues.length > 0) {
    return { safe: false, reason: issues.join('; ') };
  }

  return { safe: true };
}
