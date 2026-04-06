import { Hash, Expression } from './world';

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
