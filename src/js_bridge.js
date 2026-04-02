/**
 * Synapse: Native JS Bridge (f_6.2)
 * Handles structured execution and Runtime Discovery in Node.js.
 */

const fs = require('fs');

function run() {
    try {
        const inputData = fs.readFileSync(0, 'utf8');
        const envelope = JSON.parse(inputData);

        const { target_payload, target_context, state, execution_plan, manifest } = envelope;

        // --- Discovery Primitives (JS Implementation) ---
        const list_capabilities = () => {
            return Object.keys(manifest?.capabilities || {});
        };

        const get_capability = (name, version = 'stable') => {
            return manifest?.capabilities?.[name]?.[version] || null;
        };

        // Note: invoke_capability in JS would require a bidirectional pipe
        // for this Alpha, we provide resolution logic.
        
        // --- Sandbox Scope ---
        const context = target_context;
        let internalState = state || {};
        const log = (msg) => console.error(`[LOG] ${msg}`);
        let result = null;

        const blobFunc = new Function(
            'context', 'state', 'log', 'result', 
            'get_capability', 'list_capabilities', `
            ${target_payload}
            return { result, state };
        `);

        const output = blobFunc(
            context, internalState, log, result, 
            get_capability, list_capabilities
        );

        process.stdout.write(JSON.stringify({
            status: 'success',
            result: output.result,
            state: output.state
        }));

    } catch (err) {
        process.stdout.write(JSON.stringify({
            status: 'failure',
            error: err.message
        }));
        process.exit(1);
    }
}

run();
