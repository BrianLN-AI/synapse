import os, sys, json, hashlib
from pathlib import Path

# --- THE BOOTLOADER (f_10 Sovereign Intelligence) ---
# Decides the system root based on Tenant-Scoped Gossip Consensus.

VAULT_DIR = Path("blob_vault")
GOSSIP_DIR = Path("gossip")

def _boot_get(h: str) -> str:
    path = VAULT_DIR / h
    if not path.exists(): raise FileNotFoundError(f"Blob {h} not found during Boot.")
    return path.read_text()

def resolve_root(tenant_id: str = "global"):
    """Resolves the system root hash for a specific tenant via Gossip."""
    if GOSSIP_DIR.exists():
        votes = {}
        for gossip_file in GOSSIP_DIR.glob("*.json"):
            try:
                data = json.loads(gossip_file.read_text())
                # Filter by Tenant ID
                if data.get("tenant_id", "global") != tenant_id:
                    continue
                    
                root_h = data.get("root_h")
                sigs = data.get("signatures", [])
                if root_h:
                    votes[root_h] = votes.get(root_h, 0) + len(sigs)
            except: continue
        
        if votes:
            winner = max(votes.items(), key=lambda x: x[1])[0]
            print(f"Bootloader: Consensus reached for tenant '{tenant_id}'. Winner: {winner[:8]}")
            return winner

    # Fallback to local root (BIOS)
    # We now support tenant-specific local roots
    manifest_hash_file = Path(f"manifest_{tenant_id}.hash")
    if not manifest_hash_file.exists():
        manifest_hash_file = Path("manifest.hash")
        
    if manifest_hash_file.exists():
        return manifest_hash_file.read_text().strip()
    
    return None

def boot():
    # Parse Tenant from CLI args if provided
    tenant_id = "global"
    if "--tenant" in sys.argv:
        idx = sys.argv.index("--tenant")
        if idx + 1 < len(sys.argv):
            tenant_id = sys.argv[idx + 1]
            # Remove from argv to not confuse the Linker main()
            sys.argv.pop(idx)
            sys.argv.pop(idx)

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
        # Inject tenant_id into the globals so the Linker knows who it is
        exec_globals = globals().copy()
        exec_globals["CURRENT_TENANT"] = tenant_id
        exec(linker_payload, exec_globals)
        
    except Exception as e:
        print(f"Bootloader Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    boot()
