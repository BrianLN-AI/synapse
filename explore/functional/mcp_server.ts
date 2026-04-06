import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { createArbiter } from "./kernel";
import { createPersistentWorld } from "./world_persistent";

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

const server = new McpServer({
  name: "synapse-codemode",
  version: "1.0.0",
});

server.tool(
  "search",
  "Search the World for verbs or expressions. Write JavaScript to filter the World state.",
  { code: z.string().describe("JavaScript code to filter state") },
  async ({ code }) => {
    try {
      const searchFn = new Function('world', `return (async () => { ${code} })();`);
      const result = await searchFn(world);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (e: any) {
      return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
    }
  }
);

server.tool(
  "execute",
  "Execute JavaScript code against the Synapse World. Use fabric.* to call verbs, world.* for state, ai.* for inference.",
  { code: z.string().describe("JavaScript code to execute") },
  async ({ code }) => {
    try {
      const fabric = {
        name: async (expr: any) => await world.name(expr),
        resolve: async (h: string) => await world.resolve(h),
        list: async () => await world.list(),
        getLabel: async (n: string) => await world.getLabel(n),
        setLabel: async (n: string, h: string) => await world.setLabel(n, h),
        call: async (verbHash: string, nodeHash: string) => await arbiter.message(verbHash, nodeHash),
        log: (...args: any[]) => console.error('[FABRIC]', ...args),
      };
      const ai = {
        inference: async (prompt: string) => {
          const { execSync } = await import('child_process');
          const output = execSync(`ai groq/llama-3.3-70b-versatile --no-daemon "${prompt.replace(/"/g, '\\"')}"`, { encoding: 'utf-8' });
          return output.trim();
        }
      };

      const executeFn = new Function('fabric', 'world', 'ai', `return (async () => { ${code} })();`);
      const result = await executeFn(fabric, world, ai);
      return { content: [{ type: "text", text: typeof result === 'string' ? result : JSON.stringify(result, null, 2) }] };
    } catch (e: any) {
      return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
    }
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Synapse MCP Server running on stdio");
}

main().catch((err) => {
  console.error("Server error:", err);
  process.exit(1);
});
