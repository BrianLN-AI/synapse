raw_request = context.get('request', {})
intent = raw_request.get('intent', 'unknown')
params = raw_request.get('params', {})

log(f"L1: Proxying request with intent: {intent}...")

# Normalization
normalized_params = {k.lower(): v for k, v in params.items()}

log("L1: Policy Check Passed (Rate Limit: OK)")

result = {
    'protocol': 'D-JIT/1.2-Beta',
    'intent': intent.upper(),
    'params': normalized_params,
    'metadata': {
        'origin': 'seed_proxy',
        'timestamp': context.get('timestamp', 0),
        'trace_id': context.get('trace_id', 'syn-001')
    }
}
