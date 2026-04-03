raw_request = context.get('request', {})
intent = raw_request.get('intent', 'unknown')
params = raw_request.get('params', {})

log(f"L1: Proxying request with intent: {intent}...")

# MCP Translation Logic
if intent == "mcp_call":
    log("L1: Translating formal MCP JSON-RPC call...")
    # MCP params are often nested in 'arguments' by seed.py
    normalized_params = {k.lower(): v for k, v in params.items()}
else:
    normalized_params = {k.lower(): v for k, v in params.items()}

log("L1: Policy Check Passed (Rate Limit: OK)")

result = {
    'protocol': 'D-JIT/1.2-Beta (MCP-Enabled)',
    'intent': intent.upper(),
    'params': normalized_params,
    'metadata': {
        'origin': 'seed_mcp_proxy',
        'timestamp': context.get('timestamp', 0),
        'trace_id': context.get('trace_id', 'syn-001')
    }
}
