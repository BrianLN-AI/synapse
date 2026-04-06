import { Hash, Expression } from './world';

/**
 * KERNEL.md - The Honest Foundation (Hardened f_0-f_11)
 * A protocol-driven, namespace-aware Arbiter.
 */

export interface World {
  name: (e: any) => Promise<Hash>;
  resolve: (h: Hash) => Promise<any>;
  getLabel?: (name: string) => Promise<Hash | undefined>;
  setLabel?: (name: string, hash: Hash) => Promise<void>;
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
  inference?: (prompt: string) => Promise<string>;
  rootLabel?: string;
  engines?: Record<string, LogicEngine>;
}

/**
 * defaultJSEngine: The standard JavaScript Lifecycle Runner.
 */
export const defaultJSEngine: LogicEngine = {
  async prepare(payload: string) {
    // For JS, preparation is just the function construction
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

        let result;
        try {
          ${payload}
        } catch (e) {
          fabric.log('JS Runtime Error:', e.message);
          throw e;
        }
        return typeof result !== 'undefined' ? result : null;
      })();
    `);
  },

  async run(artifact: any, dispatchers: Record<string, any>, context: any) {
    // Reduction + Resolution
    return await artifact(dispatchers, context);
  }
};

/**
 * createArbiter: The Lifecycle-Aware "Fair Arbiter".
 */
export function createArbiter(world: World, options: ArbiterOptions = {}) {
  const engineRegistry: Record<string, LogicEngine> = {
    'logic/javascript': defaultJSEngine,
    ...(options.engines || {})
  };

  // Internal cache for prepared artifacts (Invariant: Memory Optimization)
  const artifactCache = new Map<Hash, any>();

  async function message(logicHash: Hash, scopeHash: Hash) {
    const logicExpression = await world.resolve(logicHash);
    const scopeNode = await world.resolve(scopeHash);

    if (!logicExpression || !scopeNode) {
      throw new Error(`Expression not found in World: ${logicHash} or ${scopeHash}`);
    }

    const dispatchers = {
      fabric: createDispatcher(async (method, args) => {
        if (method === 'name') return await world.name(args[0]);
        if (method === 'resolve') return await world.resolve(args[0]);
        if (method === 'call') return await message(args[0], args[1]);
        if (method === 'log') {
          console.log(`[FABRIC-LOG]`, ...args);
          return;
        }
        if (method === 'wait') return new Promise(r => setTimeout(r, args[0] || 1000));
        if (method === 'list') return await (world as any).list?.();
        if (method === 'label') return await world.getLabel?.(args[0]);
        if (method === 'promote') return await world.setLabel?.(args[0], args[1]);
        throw new Error(`Method ${method} not found in 'fabric' namespace`);
      }),
      
      world: createDispatcher(async (method, args) => {
        const rootHash = await world.getLabel?.(options.rootLabel || 'root');
        const root = await world.resolve(rootHash!);
        return await message(root.verbs[method], scopeHash);
      }),

      ai: createDispatcher(async (method, args) => {
        if (method === 'inference') return await options.inference?.(args[0]?.prompt || args[0]);
        throw new Error(`Method ${method} not found in 'ai' namespace`);
      })
    };

    const engine = engineRegistry[logicExpression.type];
    if (!engine) throw new Error(`No engine for ${logicExpression.type}`);

    // Preparation Caching
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

/**
 * createDispatcher: A protocol bridge for a specific namespace.
 */
function createDispatcher(handler: (method: string, args: any[]) => Promise<any>) {
  return { call: handler };
}

/**
 * createArbiter: The Hardened "Fair Arbiter" Seed.
 */
export function createArbiter(world: World, options: ArbiterOptions = {}) {
  
  /**
   * message: The core dispatch function.
   */
  async function message(logicHash: Hash, scopeHash: Hash) {
    const logicExpression = await world.resolve(logicHash);
    const scopeNode = await world.resolve(scopeHash);

    if (!logicExpression || !scopeNode) {
      throw new Error(`Expression not found in World: ${logicHash} or ${scopeHash}`);
    }

    // 1. Define the Dispatchers
    const dispatchers = {
      fabric: createDispatcher(async (method, args) => {
        if (method === 'name') return await world.name(args[0]);
        if (method === 'resolve') return await world.resolve(args[0]);
        if (method === 'call') return await message(args[0], args[1]);
        if (method === 'log') {
          console.log(`[FABRIC-LOG]`, ...args);
          return;
        }
        if (method === 'wait') {
          return new Promise(r => setTimeout(r, args[0] || 1000));
        }
        if (method === 'list') {
          // List all expressions in the world (The "God View")
          // In a real system, this would be a scoped scan
          return await (world as any).list?.();
        }
        if (method === 'label' && world.getLabel) {
          return await world.getLabel(args[0]);
        }
        if (method === 'promote' && world.setLabel) {
          return await world.setLabel(args[0], args[1]);
        }
        throw new Error(`Method ${method} not found in 'fabric' namespace`);
      }),
      
      world: createDispatcher(async (method, args) => {
        const rootHash = await world.getLabel?.(options.rootLabel || 'root');
        if (!rootHash) throw new Error(`Root node not found`);
        const root = await world.resolve(rootHash);
        const verbHash = root.verbs[method];
        if (!verbHash) throw new Error(`Service '${method}' not found in World Root`);
        return await message(verbHash, scopeHash);
      }),

      ai: createDispatcher(async (method, args) => {
        if (method === 'inference') {
          return await options.inference?.(args[0]?.prompt || args[0]);
        }
        throw new Error(`Method ${method} not found in 'ai' namespace`);
      })
    };

    // 2. Polyglot Dispatch
    const context = { ...scopeNode.props, verbs: scopeNode.verbs };
    
    switch (logicExpression.type) {
      case 'logic/javascript':
        return await executeJS(logicExpression.payload, dispatchers, context);
      case 'logic/lisp':
        return await executeLisp(logicExpression.payload, dispatchers, context);
      default:
        throw new Error(`Unsupported expression type: ${logicExpression.type}`);
    }
  }

  /**
   * executeJS: The JavaScript Isolate Runner.
   */
  async function executeJS(code: string, dispatchers: Record<string, any>, context: any) {
    const fn = new Function('__dispatchers', 'context', `
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

        let result;
        try {
          ${code}
        } catch (e) {
          fabric.log('JS Runtime Error:', e.message);
          throw e;
        }
        return typeof result !== 'undefined' ? result : null;
      })();
    `);
    
    return await fn(dispatchers, context);
  }

  /**
   * executeLisp: A stub for the S-Expression Runner.
   */
  async function executeLisp(code: string, dispatchers: Record<string, any>, context: any) {
    console.log('[KERNEL] Lisp execution requested. Lisp: ', code);
    // This is where the Lisp interpreter would live.
    // For now, we return a "not yet implemented" signal to prove dispatch.
    return { error: 'Lisp runner not yet implemented', code };
  }

  return { message };
}
