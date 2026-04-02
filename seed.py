import os, sys, json, hashlib
from pathlib import Path

# --- THE BOOTLOADER (f_9 Resilient Rhizome) ---
# Decides the system root based on local state OR Gossip Consensus.

VAULT_DIR = Path("blob_vault")
GOSSIP_DIR = Path("gossip")

def _boot_get(h: str) -> str:
    path = VAULT_DIR / h
    if not path.exists(): raise FileNotFoundError(f"Blob {h} not found during Boot.")
    return path.read_text()

def resolve_root():
    """Resolves the current system root hash via local state or Gossip."""
    # 1. Check for Gossip Consensus (Shared Truth)
    if GOSSIP_DIR.exists():
        votes = {}
        for gossip_file in GOSSIP_DIR.glob("*.json"):
            try:
                data = json.loads(gossip_file.read_text())
                root_h = data.get("root_h")
                sigs = data.get("signatures", [])
                if root_h:
                    votes[root_h] = votes.get(root_h, 0) + len(sigs)
            except: continue
        
        if votes:
            winner = max(votes.items(), key=lambda x: x[1])[0]
            print(f"Bootloader: Gossip Consensus reached. winner: {winner[:8]}")
            return winner

    # 2. Fallback to Local Root (BIOS Fallback)
    manifest_hash_file = Path("manifest.hash")
    if manifest_hash_file.exists():
        return manifest_hash_file.read_text().strip()
    
    return None

def boot():
    try:
        root_h = resolve_root()
        if not root_h:
            print("Linker Error: No root found via Gossip or Local BIOS.")
            sys.exit(1)
        
        manifest = json.loads(_boot_get(root_h))
        linker_h = manifest.get("capabilities", {}).get("linker", {}).get("stable")
        if not linker_h:
            print("Linker Error: No 'linker' capability defined.")
            sys.exit(1)
            
        linker_payload = _boot_get(linker_h)
        exec(linker_payload, globals())
        
    except Exception as e:
        print(f"Bootloader Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    boot()
