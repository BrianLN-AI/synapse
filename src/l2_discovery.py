import os, json

target = context.get('target')
tiers = context.get('vault_tiers', ['blob_vault', 'remote_vault', 'collective_vault'])

log(f"L2: Symbiotic Resolution for {target}...")

# 1. Level 1: Hash-based Discovery (Identity)
result = {'status': 'not_found'}
for tier in tiers:
    path = f"{tier}/{target}"
    if os.path.exists(path) and os.path.isfile(path):
        log(f"L2: Identity Match found in {tier}")
        result = {'status': 'found', 'path': path, 'tier': tier}
        break

# 2. Level 2: Semantic Discovery (Intent)
# If target doesn't look like a hash (SHA-256 is 64 chars), or Level 1 failed
if result['status'] == 'not_found' or len(str(target)) != 64:
    log(f"L2: Level 1 failed or target is an Intent. Initiating Semantic Discovery for: {target}")
    
    try:
        # Load the Semantic Index from the vault
        index_path = 'blob_vault/semantic_index.json'
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                idx = json.load(f)
            
            candidates = list(idx.values())
            # Use Cognitive Primitives provided by Linker
            # Note: embed() and rerank() are in the global scope
            best_hash = rerank(str(target), candidates)
            
            if best_hash:
                log(f"L2: Semantic Match found: {best_hash}")
                # Now resolve that hash via Level 1 logic
                for tier in tiers:
                    path = f"{tier}/{best_hash}"
                    if os.path.exists(path):
                        result = {'status': 'found', 'path': path, 'tier': tier, 'method': 'semantic'}
                        break
    except Exception as e:
        log(f"L2: Semantic Discovery Error: {str(e)}")

if result['status'] == 'not_found':
    log(f"L2: Final resolution failure for {target}.")
