target_payload = context.get('target_payload')
target_context = context.get('target_context')
target_plan = context.get('execution_plan', {})
state = context.get('state', {}) 

runtime = target_plan.get('runtime', 'python')
method = target_plan.get('method', 'local_exec')
node = target_plan.get('node', 'unknown')
retry_policy = target_plan.get('retry_policy', {'max_attempts': 1, 'backoff': 0})
spawned_hash = target_plan.get('spawned_hash')

sandbox_builtins = globals().get('SAFE_BUILTINS', __builtins__)

# --- SPAWNER INTERCEPT ---
if spawned_hash:
    log(f"L4: Intercepting Spawner output. Proposal ID: {target_plan.get('proposal_id')}")
    result = f"Spawned Tool '{target_context.get('params', {}).get('name')}' with Hash: {spawned_hash}. Proposal {target_plan.get('proposal_id')} awaits consensus."
    context['state'] = state
else:
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

            if method == 'federated_invoke':
                log(f"L4: [BRIDGE] Shipping context/state to federated peer: {node}")
                result = f"Collective success on {node}."
            else:
                if runtime == 'python':
                    # Inject classes for Matryoshka support
                    target_scope = {
                        'context': target_context, 
                        'log': log, 
                        'result': None, 
                        'execution_plan': target_plan,
                        'state': state,
                        '__builtins__': sandbox_builtins,
                        'inference': inference,
                        'embed': embed,
                        'rerank': rerank,
                        'get_capability': get_capability,
                        'list_capabilities': list_capabilities,
                        'invoke_capability': invoke_capability,
                        'VaultAdapter': globals().get('VaultAdapter'), # f_6 Matryoshka
                        'Linker': globals().get('Linker')              # f_6 Matryoshka
                    }
                    exec(target_payload, target_scope, target_scope)
                    result = target_scope.get('result')
                    state = target_scope.get('state', state)

                elif runtime == 'javascript':
                    import json, subprocess
                    with open('manifest.hash', 'r') as f: root_h = f.read().strip()
                    with open(f'blob_vault/{root_h}', 'r') as f: manifest_data = json.load(f)
                    envelope = {
                        "target_payload": target_payload, "target_context": target_context,
                        "state": state, "execution_plan": target_plan, "manifest": manifest_data
                    }
                    proc = subprocess.run(['node', 'src/js_bridge.js'], input=json.dumps(envelope), capture_output=True, text=True)
                    if proc.returncode == 0:
                        output = json.loads(proc.stdout)
                        if output.get('status') == 'success':
                            result = output.get('result'); state = output.get('state', state)
                        else: raise Exception(output.get('error'))
                    else: raise Exception(proc.stderr or proc.stdout)
            
            if result is not None: break
        except Exception as e:
            last_error = str(e)
            log(f"L4 Error: Attempt {attempt} failed: {last_error}")

    if result is None and last_error:
        raise Exception(f"L4 Execution failed locally: {last_error}")

    context['state'] = state

result = result
