import { Hash } from './world';
import { readFileSync, appendFileSync, existsSync } from 'fs';
import { hashExpression } from './hashing';

export type Event = 
  | { type: 'put', hash: Hash, expression: any, ts: string, cause?: Hash }
  | { type: 'label', name: string, hash: Hash, ts: string, cause?: Hash };

/** 
 * createPersistentWorld: A World that persists as an append-only JSONL event log with provenance.
 */
export function createPersistentWorld(filePath: string) {
  const expressions = new Map<Hash, any>();
  const labels = new Map<string, Hash>();

  // 1. Replay History
  if (existsSync(filePath)) {
    const lines = readFileSync(filePath, 'utf-8').split('\n');
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event: Event = JSON.parse(line);
        if (event.type === 'put') {
          expressions.set(event.hash, event.expression);
        } else if (event.type === 'label') {
          labels.set(event.name, event.hash);
        }
      } catch (e) {
        console.error(`[SUBSTRATE] Corrupt event skipped: ${line}`);
      }
    }
  }

  const logEvent = (event: Omit<Event, 'ts'>) => {
    const timestampedEvent = { ...event, ts: new Date().toISOString() };
    appendFileSync(filePath, JSON.stringify(timestampedEvent) + '\n');
  };

  return {
    name: async (expression: any, cause?: Hash) => {
      const id = hashExpression(expression);
      if (!expressions.has(id)) {
        expressions.set(id, expression);
        logEvent({ type: 'put', hash: id, expression, cause });
      }
      return id;
    },

    resolve: async (id: Hash) => {
      return expressions.get(id);
    },

    setLabel: async (name: string, hash: Hash, cause?: Hash) => {
      labels.set(name, hash);
      logEvent({ type: 'label', name, hash, cause });
    },

    getLabel: async (name: string) => {
      return labels.get(name);
    },

    list: async () => {
      return Object.fromEntries(expressions);
    }
  };
}
