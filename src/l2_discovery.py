import os
target = context.get('target')
# In f_3, we add 'collective_vault' to the resolution path
tiers = context.get('vault_tiers', ['blob_vault', 'remote_vault', 'collective_vault'])

log(f"L2: Collective Resolution for {target}...")

result = {'status': 'not_found'}
for tier in tiers:
    log(f"L2: Searching tier: {tier}...")
    path = f"{tier}/{target}"
    if os.path.exists(path):
        log(f"L2: SUCCESS! Hash found in {tier}")
        result = {'status': 'found', 'path': path, 'tier': tier}
        break

if result['status'] == 'not_found':
    log(f"L2: Hash {target} not found in Collective.")
