target_payload = context.get('target_payload')
target_context = context.get('target_context')
target_plan = context.get('execution_plan', {})
state = context.get('state', {}) # Receive state

runtime = target_plan.get('runtime', 'python')
method = target_plan.get('method', 'local_exec')
node = target_plan.get('node', 'unknown')
retry_policy = target_plan.get('retry_policy', {'max_attempts': 1, 'backoff': 0})

max_attempts = retry_policy.get('max_attempts', 1)
backoff = retry_policy.get('backoff', 0)

log(f"L4: Binding execution via {method} on node {node} (Max Attempts: {max_attempts})...")

last_error = None
for attempt in range(1, max_attempts + 1):
    try:
        if attempt > 1:
            log(f"L4: [RETRY] Attempt {attempt} for target payload...")
            if backoff > 0:
                import time
                time.sleep(backoff * (2**(attempt-2)))

        if method == 'remote_dispatch':
            log(f"L4: [SIMULATION] Dispatching payload to remote node: {node}")
            result = f"Remote execution on {node} simulated."
        else:
            if runtime == 'python':
                # Inject state into target scope
                target_scope = {
                    'context': target_context, 
                    'log': log, 
                    'result': None, 
                    'execution_plan': target_plan,
                    'state': state
                }
                exec(target_payload, target_scope, target_scope)
                result = target_scope.get('result')
                # Capture updated state
                state = target_scope.get('state', state)

            elif runtime == 'javascript':
                import json, subprocess
                # Pass state to JS too
                js_wrapper = f"""
                const context = {json.dumps(target_context)};
                let state = {json.dumps(state)};
                let result = null;
                const log = (msg) => console.error(`[LOG] ${msg}`);
                {target_payload}
                process.stdout.write(JSON.stringify({{result: result, state: state}}));
                """
                proc = subprocess.run(['node', '-e', js_wrapper], capture_output=True, text=True)
                if proc.returncode == 0:
                    output = json.loads(proc.stdout)
                    result = output.get('result')
                    state = output.get('state', state)
                else:
                    raise Exception(proc.stderr)
        
        if result is not None:
            break
    except Exception as e:
        last_error = str(e)
        log(f"L4 Error: Attempt {attempt} failed: {last_error}")

# Pass updated state back to Linker via context object
context['state'] = state
result = result
