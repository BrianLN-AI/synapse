target_payload = context.get('target_payload')
target_context = context.get('target_context')
target_plan = context.get('execution_plan')

log(f'L4: Binding execution via {target_plan.get("method")}...')

target_scope = {
    'context': target_context,
    'log': log,
    'result': None,
    'execution_plan': target_plan
}

try:
    exec(target_payload, {'__builtins__': __builtins__}, target_scope)
    result = target_scope.get('result')
except Exception as e:
    log(f'L4 Error: {str(e)}')
    raise e
