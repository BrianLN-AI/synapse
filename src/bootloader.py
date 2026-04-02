import os, sys, json, hashlib
from pathlib import Path

# --- THE BOOTLOADER (f_7 Self-Hosting BIOS) ---
# This is the only physical file. It resolves the Linker Blob and executes it.

VAULT_DIR = Path("blob_vault")

def _boot_get(h: str) -> str:
    path = VAULT_DIR / h
    if not path.exists(): raise FileNotFoundError(f"Blob {h} not found during Boot.")
    return path.read_text()

def boot():
    try:
        # 1. Resolve System Root
        manifest_hash_file = Path("manifest.hash")
        if not manifest_hash_file.exists():
            print("Linker Error: No manifest.hash found. System cannot boot.")
            sys.exit(1)
        
        root_h = manifest_hash_file.read_text().strip()
        manifest = json.loads(_boot_get(root_h))
        
        # 2. Resolve Linker Capability
        linker_h = manifest.get("capabilities", {}).get("linker", {}).get("stable")
        if not linker_h:
            print("Linker Error: No 'linker' capability defined in Registry.")
            sys.exit(1)
            
        # 3. Load and Execute the Brain
        linker_payload = _boot_get(linker_h)
        
        # We execute the linker blob in the current process.
        # The linker blob must contain the main() logic and classes.
        exec(linker_payload, globals())
        
    except Exception as e:
        print(f"Bootloader Failure: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    boot()
