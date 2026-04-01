target_payload = context.get('target_payload')
target_context = context.get('target_context')
target_plan = context.get('execution_plan', {})
runtime = target_plan.get('runtime', 'python')

log(f'L4: Binding execution via {runtime}...')

if runtime == 'python':
    target_scope = {
        'context': target_context,
        'log': log,
        'result': None,
        'execution_plan': target_plan
    }
    exec(target_payload, {'__builtins__': __builtins__}, target_scope)
    result = target_scope.get('result')

elif runtime == 'javascript':
    # Simple JS execution via Node.js
    # Pass the context as JSON and capture the result back as JSON
    js_wrapper = f"""
    const context = {json.dumps(target_context)};
    let result = null;
    const log = (msg) => console.error(`[LOG] ${{msg}}`);
    
    {target_payload}
    
    if (result === null) {{
        process.stderr.write("ABI Violation: result not assigned");
        process.exit(1);
    }}
    process.stdout.write(JSON.stringify({{result: result}}));
    """
    try:
        proc = subprocess.run(['node', '-e', js_wrapper], capture_output=True, text=True)
        if proc.returncode == 0:
            output = json.loads(proc.stdout)
            result = output.get('result')
        else:
            log(f'L4 JS Error: {proc.stderr}')
            raise Exception(f'JS execution failed: {proc.stderr}')
    except Exception as e:
        log(f'L4 JS Exception: {str(e)}')
        raise e
