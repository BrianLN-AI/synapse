target = context.get('target')
vault_path = 'blob_vault'
if target:
    log(f'L2: Resolving hash {target}...')
    result = {'status': 'found', 'path': f'{vault_path}/{target}'}
else:
    result = {'status': 'error', 'message': 'No target hash provided'}
