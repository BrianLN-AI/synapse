import { createArbiter } from './kernel';
import { createPersistentWorld } from './world_persistent';

const TYPE_DEFINITIONS = `
type Hash = string;

type Expression = 
  | { type: 'verb'; name?: string; payload: string }
  | { type: 'node'; verbs?: Record<string, Hash>; props?: Record<string, any> }
  | { type: 'link'; target: Hash; verb?: string }
  | { type: 'text'; content: string }
  | { type: 'code'; language?: string; payload: string };

interface World {
  name: (expression: Expression, cause?: Hash) => Promise<Hash>;
  resolve: (hash: Hash) => Promise<Expression | undefined>;
  list: () => Promise<Record<Hash, Expression>>;
  getLabel: (name: string) => Promise<Hash | undefined>;
  setLabel: (name: string, hash: Hash, cause?: Hash) => Promise<void>;
}

interface Fabric {
  name: (expression: Expression) => Promise<Hash>;
  resolve: (hash: Hash) => Promise<Expression | undefined>;
  list: () => Promise<Record<Hash, Expression>>;
  getLabel: (name: string) => Promise<Hash | undefined>;
  setLabel: (name: string, hash: Hash) => Promise<void>;
  call: (verbHash: Hash, nodeHash: Hash) => Promise<any>;
  log: (...args: any[]) => void;
}

interface AI {
  inference: (prompt: string) => Promise<string>;
}
`;

const TOOL_DESCRIPTIONS = {
  search: `Search the World for verbs or expressions. Write JavaScript to filter the World state.

Available: world.getLabel(name), world.resolve(hash), world.list(), world.name(expression)

Must return a value (use 'return' or assign to 'result').

${TYPE_DEFINITIONS}`,
  
  execute: `Execute JavaScript code against the Synapse World. Use fabric.* to call verbs, world.* for state, ai.* for inference.

Available:
- fabric.name(expression), fabric.resolve(hash), fabric.list(), fabric.getLabel(name), fabric.setLabel(name, hash)
- fabric.call(verbHash, nodeHash) - calls a verb on a node
- fabric.log(...args) - logging
- world.getLabel(name), world.resolve(hash), world.list(), world.name(expression), world.setLabel(name, hash)
- ai.inference(prompt) - call AI model

Must return a value (use 'return' or assign to 'result').

${TYPE_DEFINITIONS}`
};

const WORLD_FILE = '/Users/bln/play/synapse/explore/functional/world_state.jsonl';

const world = createPersistentWorld(WORLD_FILE);

const arbiter = createArbiter(world, {
  rootLabel: 'root',
  inference: async (prompt: string) => {
    const { execSync } = await import('child_process');
    const escapedPrompt = prompt.replace(/"/g, '\\"').replace(/\n/g, ' ');
    const output = execSync(`ai groq/llama-3.3-70b-versatile --no-daemon "${escapedPrompt}"`, { encoding: 'utf-8' });
    return output.replace(/\u001b\[[0-9;]*m/g, '').replace(/^\[AI - Model:.*\]/i, '').trim();
  }
});

interface ExecuteResult {
  result: unknown;
  error?: string;
  logs?: string[];
}

async function handleSearch(code: string): Promise<ExecuteResult> {
  try {
    const searchCode = `
      return (async () => {
        ${code}
      })();
    `;
    const searchFn = new Function('world', searchCode);
    const result = await searchFn(world);
    return { result, logs: [] };
  } catch (e: any) {
    return { result: undefined, error: e.message, logs: [] };
  }
}

async function handleExecute(code: string): Promise<ExecuteResult> {
  try {
    const fabric = {
      name: async (expr: any) => await world.name(expr),
      resolve: async (h: string) => await world.resolve(h),
      list: async () => await world.list(),
      getLabel: async (n: string) => await world.getLabel(n),
      setLabel: async (n: string, h: string) => await world.setLabel(n, h),
      call: async (verbHash: string, nodeHash: string) => await arbiter.message(verbHash, nodeHash),
      log: (...args: any[]) => console.log('[FABRIC]', ...args),
    };
    const ai = {
      inference: async (prompt: string) => {
        const { execSync } = await import('child_process');
        const escapedPrompt = prompt.replace(/"/g, '\\"').replace(/\n/g, ' ');
        const output = execSync(`ai groq/llama-3.3-70b-versatile --no-daemon "${escapedPrompt}"`, { encoding: 'utf-8' });
        return output.replace(/\u001b\[[0-9;]*m/g, '').replace(/^\[AI - Model:.*\]/i, '').trim();
      }
    };
    
    const executeCode = `
      return (async () => {
        ${code}
      })();
    `;
    const executeFn = new Function('fabric', 'world', 'ai', executeCode);
    const result = await executeFn(fabric, world, ai);
    return { result, logs: [] };
  } catch (e: any) {
    return { result: undefined, error: e.message, logs: [] };
  }
}

async function main() {
  const stdin = process.stdin;
  const stdout = process.stdout;
  
  stdin.setEncoding('utf-8');
  
  let buffer = '';
  
  stdin.on('data', async (chunk) => {
    buffer += chunk;
    
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      if (!line.trim()) continue;
      
      try {
        const request = JSON.parse(line);
        const { jsonrpc, id, method, params } = request;
        
        let result: any;
        
        if (method === 'tools/list') {
          result = {
            tools: [
              {
                name: 'search',
                description: TOOL_DESCRIPTIONS.search,
                inputSchema: { type: 'object', properties: { code: { type: 'string' } }, required: ['code'] }
              },
              {
                name: 'execute',
                description: TOOL_DESCRIPTIONS.execute,
                inputSchema: { type: 'object', properties: { code: { type: 'string' } }, required: ['code'] }
              }
            ]
          };
        } else if (method === 'tools/call') {
          const { name, arguments: args } = params;
          const code = args?.code || args;
          
          if (name === 'search') {
            result = await handleSearch(code);
          } else if (name === 'execute') {
            result = await handleExecute(code);
          } else {
            const response = {
              jsonrpc: '2.0',
              id,
              error: { code: -32601, message: 'Method not found' }
            };
            stdout.write(JSON.stringify(response) + '\n');
            continue;
          }
        } else {
          const response = {
            jsonrpc: '2.0',
            id,
            error: { code: -32601, message: 'Method not found' }
          };
          stdout.write(JSON.stringify(response) + '\n');
          continue;
        }
        
        const response = { jsonrpc: '2.0', id, result };
        stdout.write(JSON.stringify(response) + '\n');
        
      } catch (e: any) {
        const errorResponse = {
          jsonrpc: '2.0',
          id: null,
          error: { code: -32603, message: e.message }
        };
        stdout.write(JSON.stringify(errorResponse) + '\n');
      }
    }
  });
  
  stdin.on('end', () => {
    process.exit(0);
  });
}

main();