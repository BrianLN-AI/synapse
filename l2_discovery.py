import os
target = context.get('target')
tiers = context.get('vault_tiers', ['blob_vault'])
log(f'L2: Multi-Vault Resolution for {target}...')
result = {'status': 'not_found'}
for tier in tiers:
    log(f'L2: Searching tier: {tier}...')
    path = f'{tier}/{target}'
    if os.path.exists(path):
        result = {'status': 'found', 'path': path, 'tier': tier}
        break
