import { createArbiter } from './kernel';
import { createPersistentWorld } from './world_persistent';
import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';

type Hash = string;

/**
 * Hardened Codemode Harness
 */

const WORLD_FILE = '/Users/bln/play/synapse/explore/functional/world_state.jsonl';
const world = createPersistentWorld(WORLD_FILE);

const inferenceProvider = async (prompt: string): Promise<string> => {
  console.log(`[HARNESS] Calling AI...`);
  try {
    const escapedPrompt = prompt.replace(/"/g, '\\"').replace(/\n/g, ' ');
    const output = execSync(`ai groq/llama-3.3-70b-versatile --no-daemon "${escapedPrompt}"`, { encoding: 'utf-8' });
    // Strip ANSI codes and metadata
    const cleanOutput = output.replace(/\u001b\[[0-9;]*m/g, '').replace(/^\[AI - Model:.*\]/i, '').trim();
    return cleanOutput;
  } catch (e) {
    console.error(`[HARNESS] AI Inference Failed:`, e);
    return "Error: AI Inference unavailable.";
  }
};

const arbiter = createArbiter(world, { 
  inference: inferenceProvider,
  rootLabel: 'root' 
});

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (command === 'init') {
    const rootHash = await world.name({
      props: { name: 'The Root', description: 'Genesis of the hardened fabric.' },
      verbs: {}
    });
    await world.setLabel('root', rootHash);
    console.log(`World initialized. Root Node: ${rootHash}`);
  }

  if (command === 'add-verb') {
    const nodeHash = args[1];
    const verbName = args[2];
    const code = args[3];
    const type = args[4] || 'logic/javascript';

    const verbHash = await world.name({ type, payload: code });
    const node = await world.resolve(nodeHash);
    if (!node) throw new Error("Node not found");
    
    const newNode = { ...node, verbs: { ...node.verbs, [verbName]: verbHash } };
    const newNodeHash = await world.name(newNode);

    if (node.props?.name === 'The Root') {
      await world.setLabel('root', newNodeHash);
    }

    console.log(`Verb '${verbName}' (type: ${type}) added to ${nodeHash}. New Node: ${newNodeHash}`);
  }

  if (command === 'message') {
    const nodeHash = args[1];
    const verbName = args[2];
    const messageArgs = args[3] ? JSON.parse(args[3]) : {};
    
    const node = await world.resolve(nodeHash);
    const verbHash = node.verbs[verbName];
    
    const tempNode = { ...node, props: { ...node.props, ...messageArgs } };
    const tempHash = await world.name(tempNode);
    
    console.log(`[ARBITER] Messaging '${verbName}'...`);
    const finalResult = await arbiter.message(verbHash, tempHash);
    console.log("Result:", JSON.stringify(finalResult, null, 2));
  }

  if (command === 'status') {
    const data = JSON.parse(readFileSync(WORLD_FILE, 'utf-8'));
    console.log("--- World Status (Hardened) ---");
    console.log(`Root Label: ${data.labels?.root}`);
    console.log(`Expressions: ${Object.keys(data.expressions || {}).length}`);
    for (const [h, e] of Object.entries(data.expressions || {})) {
      if ((e as any).props) {
        console.log(`Node ${h}: ${(e as any).props.name} (Verbs: ${Object.keys((e as any).verbs || {}).join(', ')})`);
      }
    }
  }
}

main().catch(console.error);
