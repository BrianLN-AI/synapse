/**
 * Synapse: Native JS Bridge (f_6)
 * Handles structured execution of Synapse Blobs in Node.js.
 */

const fs = require('fs');

function run() {
    try {
        // 1. Read the execution context from stdin (or a temporary file if needed)
        // For f_6, we use a simple synchronous stdin read for this seed.
        const inputData = fs.readFileSync(0, 'utf8');
        const envelope = JSON.parse(inputData);

        const { target_payload, target_context, state, execution_plan } = envelope;

        // 2. Prepare the sandbox scope
        const context = target_context;
        let result = null;
        let internalState = state || {};
        const log = (msg) => console.error(`[LOG] ${msg}`);

        // 3. Execute the payload
        // We use a Function constructor to create a clean execution scope
        const blobFunc = new Function('context', 'state', 'log', 'result', `
            ${target_payload}
            return { result, state };
        `);

        const output = blobFunc(context, internalState, log, result);

        // 4. Return the result and updated state
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
