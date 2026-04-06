import { createArbiter } from './kernel';
import { createPersistentWorld } from './world_persistent';
import { readFileSync } from 'fs';

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

async function handleToolsList(): Promise<any> {
  const rootHash = await world.getLabel('root');
  if (!rootHash) return { tools: [] };
  const root = await world.resolve(rootHash);
  
  const tools = [
    {
      name: 'imagine',
      description: 'Add a new verb to the World. Args: { prompt: "description of verb to add" }',
      inputSchema: { type: 'object', properties: { prompt: { type: 'string' } }, required: ['prompt'] }
    },
    {
      name: 'execute',
      description: 'Execute arbitrary JavaScript code. Args: { code: "js code", context: {} }',
      inputSchema: { type: 'object', properties: { code: { type: 'string' }, context: { type: 'object' } }, required: ['code'] }
    }
  ];
  
  for (const [name, hash] of Object.entries(root.verbs || {})) {
    tools.push({ 
      name, 
      description: `Verb: ${name} (hash: ${hash})`,
      inputSchema: { type: 'object', properties: { prompt: { type: 'string' } } }
    });
  }
  return { tools };
}

async function handleToolsCall(name: string, args: any): Promise<any> {
  const rootHash = await world.getLabel('root');
  if (!rootHash) throw new Error('No root label');
  const root = await world.resolve(rootHash);
  
  // Special handling for 'imagine' - route through the arbiter
  if (name === 'imagine') {
    const verbHash = root.verbs['imagine'];
    if (!verbHash) throw new Error('Verb "imagine" not found');
    const scopeHash = await world.name({ props: { prompt: args.prompt || args }, verbs: {} });
    return await arbiter.message(verbHash, scopeHash);
  }
  
  // Special handling for 'execute' - run arbitrary JS code
  if (name === 'execute') {
    const code = args.code || args;
    const logicHash = await world.name({ type: 'logic/javascript', payload: code });
    const scopeHash = await world.name({ props: args.context || {}, verbs: {} });
    return await arbiter.message(logicHash, scopeHash);
  }
  
  // Standard verb lookup - create temp node like harness does
  const verbHash = root.verbs[name];
  if (!verbHash) throw new Error(`Verb '${name}' not found`);
  
  // Create temp node: merge root's props with args (like harness does)
  // Keep root's verbs, just update props
  const tempNode = { 
    props: { ...root.props, ...args }, 
    verbs: root.verbs 
  };
  const tempHash = await world.name(tempNode);
  
  const result = await arbiter.message(verbHash, tempHash);
  
  // Return the result directly (may be undefined, handle gracefully)
  return result ?? { result: 'completed' };
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
          result = await handleToolsList();
        } else if (method === 'tools/call') {
          const { name, arguments: args } = params;
          result = await handleToolsCall(name, args);
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