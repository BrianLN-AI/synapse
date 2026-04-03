import os, sys, json, hashlib
from pathlib import Path

# --- THE BOOTLOADER (f_11 Resilience Hardening) ---

def _boot_get(h: str) -> str:
    path = Path("blob_vault") / h
    if not path.exists(): raise FileNotFoundError(f"Blob {h} not found during Boot.")
    return path.read_text()

def crypto_verify_sim(data: str, sig: str) -> bool:
    """Mock verification for the bootloader."""
    return sig is not None and len(sig) == 64

def resolve_root(tenant_id: str = "global"):
    """Resolves the current system root hash with Identity-Aware Consensus."""
    
    # 1. Load Local Root first (The known-good BIOS state)
    local_root = None
    manifest_hash_file = Path(f"manifest_{tenant_id}.hash")
    if not manifest_hash_file.exists(): manifest_hash_file = Path("manifest.hash")
    if manifest_hash_file.exists():
        local_root = manifest_hash_file.read_text().strip()

    # 2. Check for Gossip Consensus (Shared Truth)
    gossip_dir = Path("gossip")
    if gossip_dir.exists():
        votes = {}
        for gossip_file in gossip_dir.glob("*.json"):
            try:
                data = json.loads(gossip_file.read_text())
                if data.get("tenant_id", "global") != tenant_id: continue
                
                root_h = data.get("root_h")
                sigs = data.get("signatures", [])
                
                # SECURITY: Verify each signature before tallying
                valid_sigs = [s for s in sigs if crypto_verify_sim(root_h, s)]
                
                if root_h and valid_sigs:
                    votes[root_h] = votes.get(root_h, 0) + len(valid_sigs)
            except: continue
        
        if votes:
            winner = max(votes.items(), key=lambda x: x[1])[0]
            winner_tally = votes[winner]
            
            # CONSENSUS LOGIC: 
            # If local root exists, only switch to winner if it has high consensus (> 1 peer)
            if local_root and winner != local_root:
                if winner_tally > 1:
                    print(f"Bootloader: Switch authorized. Local root overridden by collective consensus ({winner_tally} votes).", file=sys.stderr)
                    return winner
                else:
                    # print(f"Bootloader: Collective root '{winner[:8]}' ignored. Insufficient consensus to override local state.", file=sys.stderr)
                    return local_root
            
            print(f"Bootloader: Consensus reached for tenant '{tenant_id}'. Winner: {winner[:8]}", file=sys.stderr)
            return winner

    return local_root

def boot():
    tenant_id = "global"
    if "--tenant" in sys.argv:
        idx = sys.argv.index("--tenant")
        if idx + 1 < len(sys.argv):
            tenant_id = sys.argv[idx + 1]
            sys.argv.pop(idx); sys.argv.pop(idx)

    try:
        root_h = resolve_root(tenant_id)
        if not root_h:
            print(f"Linker Error: No root found for tenant '{tenant_id}'.")
            sys.exit(1)
        
        manifest = json.loads(_boot_get(root_h))
        linker_h = manifest.get("capabilities", {}).get("linker", {}).get("stable")
        if not linker_h:
            print("Linker Error: No 'linker' capability defined.")
            sys.exit(1)
            
        linker_payload = _boot_get(linker_h)
        exec_scope = {
            "__builtins__": __builtins__,
            "CURRENT_TENANT": tenant_id,
            "os": os, "sys": sys, "json": json, "hashlib": hashlib, "time": time, "glob": glob, "subprocess": subprocess, "Path": Path
        }
        exec(linker_payload, exec_scope, exec_scope)
        if "main" in exec_scope: exec_scope["main"]()
        
    except Exception as e:
        print(f"Bootloader Failure: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import time, glob, subprocess
    boot()
