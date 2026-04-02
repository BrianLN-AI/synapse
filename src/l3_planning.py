import glob, json, os, hashlib

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

# --- SYNTHETIC FEEDBACK LOOPS (f_5 Cognitive Replay) ---
try:
    log("L3: Initiating Synthetic Replay Review...")
    telemetry_files = glob.glob('blob_vault/*')
    telemetry_files.sort(key=os.path.getmtime)
    
    for f in telemetry_files[-10:]:
        try:
            with open(f, 'r') as fh:
                data = json.load(fh)
                if isinstance(data, dict) and data.get('status') == 'failure':
                    failed_hash = data.get('blob_hash')
                    error = data.get('error')
                    log(f"L3: [REPLAY OPPORTUNITY] Found failure in blob: {failed_hash}")
                    lesson_prompt = f"Analyze this failure and generate a fix: Blob {failed_hash} failed with error: {error}. Context: {data.get('request_envelope')}"
                    lesson_fix = inference(lesson_prompt)
                    lesson_code = f"log('Executing Synthetic Lesson for failed blob: {failed_hash}')\nlog('Lesson learned: {lesson_fix}')\nresult = 'Lesson applied successfully'"
                    lesson_h = put(lesson_code, 'synthetic_lesson')
                    with open('manifest.hash', 'r') as f: root_h = f.read().strip()
                    with open(f'blob_vault/{root_h}', 'r') as f: manifest = json.load(f)
                    lesson_name = "lesson_" + hashlib.md5(failed_hash.encode()).hexdigest()[:8]
                    if lesson_name not in manifest['capabilities']:
                        manifest['capabilities'][lesson_name] = {'stable': lesson_h}
                        propose(manifest)
                    break 
        except: continue
except Exception as e:
    log(f"L3: Replay Error: {str(e)}")

# --- THE DISTILLATION ROUTINE (f_5 Pattern Recognition) ---
try:
    log("L3: Initiating Distillation Review...")
    cog_files = glob.glob('blob_vault/cognitive/*')
    patterns = {}
    for f in cog_files[-10:]:
        try:
            with open(f, 'r') as fh:
                artifact_h = fh.read().strip()
                with open(f'blob_vault/{artifact_h}', 'r') as afh:
                    artifact = json.load(afh)
                    prompt = artifact.get('prompt', '')
                    patterns[prompt] = patterns.get(prompt, 0) + 1
        except: continue
    for prompt, count in patterns.items():
        if count >= 3:
            distilled_code = f"log('Executing Distilled Logic for prompt: {prompt}')\nresult = 'Distilled result for: {prompt}'"
            new_h = put(distilled_code, 'distilled_logic')
            with open('manifest.hash', 'r') as f: root_h = f.read().strip()
            with open(f'blob_vault/{root_h}', 'r') as f: manifest = json.load(f)
            cap_name = "distilled_" + hashlib.md5(prompt.encode()).hexdigest()[:8]
            if cap_name not in manifest['capabilities']:
                manifest['capabilities'][cap_name] = {'stable': new_h}
                propose(manifest)
except Exception: pass

# --- ARBITRAGE ---
if intent == 'SPAWN':
    log(f"L3: Spawner activated...")
    generated_code = f"log('Auto-generated blob executing...')\nresult = 'SPAWNED BLOB SUCCESS: ' + str(context.get('params', {{}}))"
    new_blob_hash = put(generated_code, 'generated_logic')
    with open('manifest.hash', 'r') as f: root_h = f.read().strip()
    with open(f'blob_vault/{root_h}', 'r') as f: current_manifest = json.load(f)
    current_manifest['capabilities'][params.get('name', 'gen_tool')] = {'stable': new_blob_hash}
    prop_id = propose(current_manifest)
    result = {'method': 'local_exec', 'node': 'local', 'runtime': 'python', 'sandbox': 'standard', 'spawned_hash': new_blob_hash, 'proposal_id': proposal_id}
else:
    if priority == 'high': node_name = min(nodes, key=lambda n: nodes[n]['latency'])
    else: node_name = min(nodes, key=lambda n: nodes[n]['cost'])
    stats = nodes[node_name]
    
    # FIXED: Prioritize 'runtime' from params if present
    runtime = params.get('runtime', stats['runtime'])
    
    log(f"L3: Selected Node: {node_name} (Type: {stats['type']}, Runtime: {runtime})")
    result = {
        'method': 'local_exec' if stats['type'] == 'internal' else 'federated_invoke',
        'node': node_name,
        'runtime': runtime,
        'sandbox': 'high_isolation' if priority == 'high' else 'standard',
        'cost_estimate': stats['cost'] * 0.0001,
        'retry_policy': {'max_attempts': 3 if priority == 'high' else 1, 'backoff': 0.1}
    }
