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
                        nodes[node]['latency'] *= 10
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
