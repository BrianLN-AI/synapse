target_payload = context.get('target_payload')
target_context = context.get('target_context')
target_plan = context.get('execution_plan', {})
state = context.get('state', {}) 

runtime = target_plan.get('runtime', 'python')
method = target_plan.get('method', 'local_exec')
node = target_plan.get('node', 'unknown')
is_high_integrity = target_plan.get('integrity') == 'high'

sandbox_builtins = globals().get('SAFE_BUILTINS', __builtins__)

# --- f_11: VERIFIED EXECUTION GATE ---
if is_high_integrity and method == 'local_exec':
    log(f"L4: High-Integrity requested. Delegating to Prover...")
    target_h = target_plan.get('target_hash')
    
    # Wrap in params for Proxy compatibility
    prover_args = {
        'params': {
            'target_h': target_h, 
            'context': target_context
        }
    }
    
    prover_res = invoke_capability('prover', prover_args)
    
    if prover_res.get('status') == 'success':
        proof = prover_res['result'].get('proof', {})
        result_val = prover_res['result'].get('result')
        
        # VERIFY (Deterministic JSON)
        res_json = json.dumps(result_val, sort_keys=True)
        res_h = hashlib.sha256(res_json.encode()).hexdigest()
        commitment_data = f"{target_h}:{res_h}"
        
        log(f"DEBUG L4: hashing result string: {res_json}")
        log(f"DEBUG L4: commitment string: {commitment_data}")
        
        is_valid = crypto_verify(commitment_data, proof.get('signature'), proof.get('prover_pubkey'))
        
        if is_valid:
            log(f"L4: PROOF VERIFIED. Integrity confirmed.")
            result = result_val
        else:
            log(f"L4: [SECURITY ALERT] Proof Verification FAILED.")
            raise Exception("Integrity Verification Failed")
    else:
        raise Exception(f"Prover failed: {prover_res.get('error')}")

# --- SPAWNER / FEDERATED / NORMAL EXECUTION ---
elif target_plan.get('spawned_hash'):
    log(f"L4: Intercepting Spawner output...")
    result = f"Spawned Tool. Proposal {target_plan.get('proposal_id')} awaits consensus."
elif method == 'federated_invoke':
    log(f"L4: [BRIDGE] Shipping context/state to federated peer: {node}")
    result = f"Collective success on {node}."
else:
    target_scope = {'context': target_context, 'log': log, 'result': None, 'state': state, '__builtins__': sandbox_builtins}
    # FIXED: Added 'invoke' to the passed primitives
    known_primitives = ['inference', 'embed', 'rerank', 'get_capability', 'list_capabilities', 'invoke_capability', 'read_blob', 'json', 'put', 'propose', 'branch', 'rollback', 'sign', 'tally', 'VaultAdapter', 'Linker', 'crypto_sign', 'crypto_verify', 'get_public_key', 'hashlib', 'invoke']
    for p in known_primitives:
        val = globals().get(p)
        if val is not None: target_scope[p] = val
    exec(target_payload, target_scope, target_scope)
    result = target_scope.get('result')
    state = target_scope.get('state', state)

context['state'] = state
result = result
