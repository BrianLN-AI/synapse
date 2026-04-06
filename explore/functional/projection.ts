export type Hash = string;
export type Expression = 
  | { type: 'verb'; name?: string; payload: string }
  | { type: 'node'; verbs?: Record<string, Hash> }
  | { type: 'link'; target: Hash; verb?: string }
  | { type: 'text'; content: string }
  | { type: 'code'; language?: string; payload: string };

/**
 * PROJECTION.md - The Interface Shadow
 * A functional implementation of the projected interface.
 */

export type MessageHandler = (intent: string, args: any[]) => Promise<any>;

/**
 * project: The "Shadow" Mapping.
 * It projects a set of capabilities into a scope via a Proxy.
 */
export function project(handler: MessageHandler) {
  return new Proxy({}, {
    get: (target, intent: string) => {
      // Every property access is an asynchronous message to the handler.
      return async (...args: any[]) => {
        return await handler(intent, args);
      };
    }
  });
}
