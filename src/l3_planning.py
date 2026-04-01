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

# --- THE DISTILLATION ROUTINE (f_5 Self-Optimization) ---
try:
    log("L3: Initiating Distillation Review...")
    cog_files = glob.glob('blob_vault/cognitive/*')
    patterns = {}
    
    # Analyze recent cognitive artifacts for patterns
    for f in cog_files[-10:]:
        try:
            with open(f, 'r') as fh:
                # Resolve the actual artifact hash from the reference file
                artifact_h = fh.read().strip()
                with open(f'blob_vault/{artifact_h}', 'r') as afh:
                    artifact = json.load(afh)
                    prompt = artifact.get('prompt', '')
                    patterns[prompt] = patterns.get(prompt, 0) + 1
        except: continue
    
    # Identify recurring patterns (threshold: 3)
    for prompt, count in patterns.items():
        if count >= 3:
            log(f"L3: [DISTILLATION OPPORTUNITY] Found pattern: '{prompt}' (Count: {count})")
            # Generate a Distilled Blob
            distilled_code = f"""
log('Executing Distilled Logic for prompt: {prompt}')
result = 'Distilled result for: {prompt}'
"""
            new_h = put(distilled_code, 'distilled_logic')
            log(f"L3: Distilled logic created: {new_h}")
            
            # Propose to Registry
            with open('manifest.hash', 'r') as f: root_h = f.read().strip()
            with open(f'blob_vault/{root_h}', 'r') as f: manifest = json.load(f)
            
            cap_name = "distilled_" + hashlib.md5(prompt.encode()).hexdigest()[:8]
            if cap_name not in manifest['capabilities']:
                manifest['capabilities'][cap_name] = {'stable': new_h}
                prop_id = propose(manifest)
                log(f"L3: [PROPOSED] Distilled capability: {cap_name}. Proposal ID: {prop_id}")
except Exception as e:
    log(f"L3: Distillation Error: {str(e)}")


# --- THE SPAWNER ROUTINE (Autonomous Evolution) ---
if intent == 'SPAWN':
    log(f"L3: Spawner activated. Generating new logic...")
    generated_code = f"log('Auto-generated blob executing...')\nresult = 'SPAWNED BLOB SUCCESS: ' + str(context.get('params', {{}}))"
    new_blob_hash = put(generated_code, 'generated_logic')
    with open('manifest.hash', 'r') as f: root_h = f.read().strip()
    with open(f'blob_vault/{root_h}', 'r') as f: current_manifest = json.load(f)
    new_capability_name = params.get('name', 'generated_tool')
    current_manifest['capabilities'][new_capability_name] = {'stable': new_blob_hash}
    proposal_id = propose(current_manifest)
    result = {'method': 'local_exec', 'node': 'local', 'runtime': 'python', 'sandbox': 'standard', 'spawned_hash': new_blob_hash, 'proposal_id': proposal_id}
else:
    # --- PLASTICITY ROUTINE (Feedback) ---
    try:
        telemetry_files = glob.glob('blob_vault/*')
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
        'method': 'local_exec', 
        'node': node_name,
        'runtime': stats['runtime'],
        'sandbox': 'high_isolation' if priority == 'high' else 'standard',
        'cost_estimate': stats['cost'] * 0.0001,
        'retry_policy': {'max_attempts': 3 if priority == 'high' else 1, 'backoff': 0.1}
    }
