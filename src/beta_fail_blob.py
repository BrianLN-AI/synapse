node = execution_plan.get('node')
if node == 'beta-edge':
    log('Simulated Beta-Edge Failure')
    raise Exception('Beta-Edge Node Unavailable')
else:
    result = f'Success on {node}'

