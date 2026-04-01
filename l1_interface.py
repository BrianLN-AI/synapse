raw_request = context.get('request', {})
log(f'L1: Normalizing intent: {raw_request.get("intent", "unknown")}')
result = {
    'protocol': 'D-JIT/1.1-Alpha',
    'intent': raw_request.get('intent', 'unknown'),
    'params': {k.lower(): v for k, v in raw_request.get('params', {}).items()},
    'metadata': {'origin': 'seed_cli', 'trace_id': context.get('trace_id')}
}
