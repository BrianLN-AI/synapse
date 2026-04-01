import glob, json, os

# Federated Marketplace
nodes = {
    'local': {'latency': 100, 'cost': 1, 'trust': 1.0, 'runtime': 'python', 'type': 'internal'},
    'node-gamma': {'latency': 20, 'cost': 10, 'trust': 0.95, 'runtime': 'python', 'type': 'federated'},
    'node-delta': {'latency': 5, 'cost': 50, 'trust': 0.9, 'runtime': 'javascript', 'type': 'federated'}
}

target = context.get('target')
request = context.get('request', {})
params = request.get('params', {})
priority = params.get('priority', 'normal')
intent = request.get('intent', 'UNKNOWN')

# --- THE SPAWNER ROUTINE (Autonomous Evolution) ---
if intent == 'SPAWN':
    log(f"L3: Spawner activated. Generating new logic for intent: {params.get('description', 'unknown')}")
    # 1. Use Inference to generate the blob payload
    # In a real f_4 system, the LLM would output valid Python code adhering to the ABI.
    # Here, we simulate the code generation.
    generated_code = f"""
log('Auto-generated blob executing...')
result = 'SPAWNED BLOB SUCCESS: ' + str(context.get('params', {{}}))
"""
    # 2. Store the generated blob
    new_blob_hash = put(generated_code, 'generated_logic')
    log(f"L3: Generated new blob with hash: {new_blob_hash}")
    
    # 3. Create a Mutation Proposal
    # Read current manifest to propose an addition
    with open('manifest.hash', 'r') as f: root_h = f.read().strip()
    with open(f'blob_vault/{root_h}', 'r') as f: current_manifest = json.load(f)
    
    new_capability_name = params.get('name', 'generated_tool')
    current_manifest['capabilities'][new_capability_name] = {'stable': new_blob_hash}
    
    proposal_id = propose(current_manifest)
    log(f"L3: Proposed mutation to Registry. Proposal ID: {proposal_id}")
    
    # Force local execution for the spawner acknowledgment
    result = {
        'method': 'local_exec',
        'node': 'local',
        'runtime': 'python',
        'sandbox': 'standard',
        'cost_estimate': 0.0,
        'retry_policy': {'max_attempts': 1, 'backoff': 0},
        'spawned_hash': new_blob_hash,
        'proposal_id': proposal_id
    }
else:
    # --- PLASTICITY ROUTINE (Feedback) ---
    try:
        telemetry_files = glob.glob('blob_vault/telemetry/*') + glob.glob('blob_vault/*')
        telemetry_files.sort(key=os.path.getmtime)
        for f in telemetry_files[-20:]:
            try:
                with open(f, 'r') as fh:
                    data = json.load(fh)
                    if isinstance(data, dict) and 'execution_plan' in data:
                        node = data['execution_plan'].get('node')
                        status = data.get('status')
                        if node and node in nodes and status == 'failure':
                            nodes[node]['latency'] *= 5
            except: continue
    except Exception as e:
        log(f"L3: Plasticity Error: {str(e)}")

    # --- FEDERATED ARBITRAGE ---
    if priority == 'high':
        node_name = min(nodes, key=lambda n: nodes[n]['latency'])
    else:
        node_name = min(nodes, key=lambda n: nodes[n]['cost'])

    stats = nodes[node_name]
    log(f"L3: Selected Node: {node_name} (Type: {stats['type']}, optimized for {priority} priority)")

    result = {
        'method': 'local_exec' if stats['type'] == 'internal' else 'federated_invoke',
        'node': node_name,
        'runtime': stats['runtime'],
        'sandbox': 'high_isolation' if priority == 'high' else 'standard',
        'cost_estimate': stats['cost'] * 0.0001,
        'retry_policy': {
            'max_attempts': 3 if priority == 'high' else 1,
            'backoff': 0.1
        }
    }
