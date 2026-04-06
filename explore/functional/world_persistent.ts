import { Hash, Expression } from './world';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { hashExpression } from './hashing';

/** 
 * createPersistentWorld: A World that persists to a local file for the session.
 */
export function createPersistentWorld(filePath: string) {
  let expressions = new Map<Hash, any>();
  let labels = new Map<string, Hash>(); // Labels: Name -> Latest Hash

  if (existsSync(filePath)) {
    const data = JSON.parse(readFileSync(filePath, 'utf-8'));
    expressions = new Map(Object.entries(data.expressions || {}));
    labels = new Map(Object.entries(data.labels || {}));
  }

  const save = () => {
    const data = {
      expressions: Object.fromEntries(expressions),
      labels: Object.fromEntries(labels)
    };
    writeFileSync(filePath, JSON.stringify(data, null, 2));
  };

  return {
    name: async (expression: any) => {
      // Invariant I: Address = Multihash(Content)
      const id = hashExpression(expression);
      expressions.set(id, expression);
      save();
      return id;
    },

    resolve: async (id: Hash) => {
      return expressions.get(id);
    },

    // Labels: Mutable pointers for a moving World
    setLabel: async (name: string, hash: Hash) => {
      labels.set(name, hash);
      save();
    },

    getLabel: async (name: string) => {
      return labels.get(name);
    },

    // God View: List all expressions
    list: async () => {
      return Object.fromEntries(expressions);
    }
  };
}
