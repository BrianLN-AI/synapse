target = context.get('target')
request = context.get('request', {})
params = request.get('params', {})

priority = params.get('priority', 'normal')
runtime = params.get('runtime', 'python')

log(f'L3: Planning {runtime} execution for {target}...')

result = {
    'method': 'local_exec',
    'runtime': runtime,
    'sandbox': 'high_isolation' if priority == 'high' else 'standard',
    'cost_estimate': 0.0001
}
