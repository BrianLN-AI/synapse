import { spawnSync } from 'child_process';

/**
 * deepStableStringify: Ensures nested objects are stringified in a deterministic order.
 */
function deepStableStringify(obj: any): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(deepStableStringify).join(',') + ']';
  }
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => `"${k}":${deepStableStringify(obj[k])}`).join(',') + '}';
}

/**
 * hashExpression: Computes the BLAKE3 hash of an expression.
 */
export function hashExpression(expression: any): string {
  const content = deepStableStringify(expression);
  
  const result = spawnSync('python3', ['-c', 'import blake3, sys; print(blake3.blake3(sys.stdin.read().encode()).hexdigest())'], {
    input: content,
    encoding: 'utf-8'
  });

  if (result.status === 0) {
    return `b3:${result.stdout.trim()}`;
  } else {
    throw new Error(`Hash calculation failed: ${result.stderr}`);
  }
}
