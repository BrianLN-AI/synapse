import { Hash } from './world';
import { auditAST } from './ast_auditor';

/**
 * KERNEL.md - The Honest Foundation (Hardened f_0-f_11)
 * A protocol-driven, namespace-aware Arbiter.
 */

export interface World {
  name: (e: any) => Promise<Hash>;
  resolve: (h: Hash) => Promise<any>;
  getLabel?: (name: string) => Promise<Hash | undefined>;
  setLabel?: (name: string, hash: Hash) => Promise<void>;
  list?: () => Promise<Record<Hash, any>>;
}

export interface LogicEngine {
  /**
   * Preparation Phase: Translate payload (e.g., Transpile, Parse).
   * Returns an 'Artifact' that can be cached.
   */
  prepare: (payload: string) => Promise<any>;
  
  /**
   * Execution Phases (Projection, Reduction, Resolution).
   */
  run: (artifact: any, dispatchers: Record<string, any>, context: any) => Promise<any>;
}

export interface ArbiterOptions {
  inference?: (prompt: string | { prompt: string }) => Promise<string>;
  rootLabel?: string;
  engines?: Record<string, LogicEngine>;
}

/**
 * defaultJSEngine: The standard JavaScript Lifecycle Runner.
 */
export const defaultJSEngine: LogicEngine = {
  async prepare(payload: string) {
    // PHASE 0: DETERMINISTIC AST AUDIT
    const audit = auditAST(payload);
    if (!audit.safe) {
      throw new Error(`[AST-AUDIT] ${audit.reason}`);
    }

    // For JS, preparation is the function construction
    // We wrap the payload to provide the Synapse ABI
    // Supports both 'return x' and 'result = x' patterns (assignment expr returns its value)
    return new Function('__dispatchers', 'context', `
      return (async () => {
        const fabric = new Proxy({}, { 
          get: (_, m) => (...a) => __dispatchers.fabric.call(m, a[0] === undefined ? [] : a) 
        });
        const world = new Proxy({}, { 
          get: (_, m) => (...a) => __dispatchers.world.call(m, a[0] === undefined ? [] : a) 
        });
        const ai = new Proxy({}, { 
          get: (_, m) => (...a) => __dispatchers.ai.call(m, a[0] === undefined ? [] : a) 
        });

        const console = { log: fabric.log };
        const globalThis = undefined;
        const fetch = undefined;
        const process = undefined;

        try {
          // Wrap payload to capture 'result' variable
          return await (async () => { 
            var result;
            ${payload}
            return result;
          })();
        } catch (e) {
          fabric.log('JS Runtime Error:', e.message);
          throw e;
        }
      })();
    `);
  },

  async run(artifact: any, dispatchers: Record<string, any>, context: any) {
    return await artifact(dispatchers, context);
  }
};

/**
 * lispEngine: A stub for the S-Expression Runner.
 */
export const lispEngine: LogicEngine = {
  async prepare(payload: string) {
    return payload;
  },
  async run(payload: any, dispatchers: Record<string, any>, context: any) {
    dispatchers.fabric.call('log', [`[KERNEL] Lisp execution requested. Lisp: ${payload}`]);
    return { error: 'Lisp runner not yet implemented', code: payload };
  }
};

/**
 * createArbiter: The Lifecycle-Aware "Fair Arbiter".
 */
export function createArbiter(world: World, options: ArbiterOptions = {}) {
  const engineRegistry: Record<string, LogicEngine> = {
    'logic/javascript': defaultJSEngine,
    'logic/lisp': lispEngine,
    ...(options.engines || {})
  };

  const artifactCache = new Map<Hash, any>();

  async function message(logicHash: Hash, scopeHash: Hash): Promise<any> {
    const logicExpression = await world.resolve(logicHash);
    const scopeNode = await world.resolve(scopeHash);

    if (!logicExpression || !scopeNode) {
      throw new Error(`Expression not found in World: ${logicHash} or ${scopeHash}`);
    }

    const dispatchers = {
      fabric: {
        call: async (method: string, args: any[]) => {
          if (method === 'name') return await world.name(args[0]);
          if (method === 'resolve') return await world.resolve(args[0]);
          if (method === 'call') return await message(args[0], args[1]);
          if (method === 'log') {
            console.log(`[FABRIC-LOG]`, ...args);
            return;
          }
          if (method === 'wait') return new Promise(r => setTimeout(r, args[0] || 1000));
          if (method === 'list') return await world.list?.();
          if (method === 'label') return await world.getLabel?.(args[0]);
          if (method === 'promote') return await world.setLabel?.(args[0], args[1]);
          throw new Error(`Method ${method} not found in 'fabric' namespace`);
        }
      },
      
      world: {
        call: async (method: string, args: any[]) => {
          const rootHash = await world.getLabel?.(options.rootLabel || 'root');
          if (!rootHash) throw new Error(`Root label '${options.rootLabel || 'root'}' not found`);
          const root = await world.resolve(rootHash);
          const verbHash = root.verbs[method];
          if (!verbHash) throw new Error(`Service '${method}' not found in World Root`);
          return await message(verbHash, scopeHash);
        }
      },

      ai: {
        call: async (method: string, args: any[]) => {
          if (method === 'inference') {
            const prompt = args[0]?.prompt || args[0];
            return await options.inference?.(prompt);
          }
          throw new Error(`Method ${method} not found in 'ai' namespace`);
        }
      }
    };

    const engine = engineRegistry[logicExpression.type];
    if (!engine) throw new Error(`No engine for ${logicExpression.type}`);

    let artifact = artifactCache.get(logicHash);
    if (!artifact) {
      artifact = await engine.prepare(logicExpression.payload);
      artifactCache.set(logicHash, artifact);
    }

    const context = { ...scopeNode.props, verbs: scopeNode.verbs };
    return await engine.run(artifact, dispatchers, context);
  }

  return { message };
}
