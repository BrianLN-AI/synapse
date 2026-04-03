import json
import subprocess
import os
import hashlib
from pathlib import Path

def run_cmd(args):
    return subprocess.run(["python3"] + args, capture_output=True, text=True)

print("--- Synapse Resilience & Validation Suite ---")

# 1. Gossip Recovery Test
print("\nTest 1: Gossip Recovery (Missing local root)...")
root_h = Path("manifest.hash").read_text().strip()
Path("gossip").mkdir(exist_ok=True)
sig = "a" * 64
gossip_data = {"tenant_id": "global", "root_h": root_h, "signatures": [sig, sig]}
Path("gossip/peer_recovery.json").write_text(json.dumps(gossip_data))

os.rename("manifest.hash", "manifest.hash.bak")
res = run_cmd(["seed.py", "invoke", "41aa0d45bcc596e2b08f8405cf4427dd9b7e4465c0d12e53b853c23298cf853a"])
# Refined check for tenant-scoped log
if "Consensus reached for tenant 'global'" in res.stderr and res.returncode == 0:
    print("PASS: System recovered via Gossip.")
else:
    print(f"FAIL: Recovery failed. Status: {res.returncode}")
    print(f"Stderr: {res.stderr}")

os.rename("manifest.hash.bak", "manifest.hash")

# 2. Bad Promotion Block Test
print("\nTest 2: Bad Promotion Block (Missing blob)...")
bad_manifest = {
    "version": "broken",
    "capabilities": {"proxy": {"stable": "non-existent-hash-0000000000000000000000000000000000000000000"}}
}
Path("bad_manifest.json").write_text(json.dumps(bad_manifest))
res = run_cmd(["seed.py", "promote", "bad_manifest.json"])
if "Pre-promotion verification failed" in res.stderr:
    print("PASS: System blocked broken manifest promotion.")
else:
    print(f"FAIL: Broken manifest was promoted! Stderr: {res.stderr}")

# 3. Unauthorized Mutation Block
print("\nTest 3: Unauthorized Mutation (Insufficient signatures)...")
mutation = {"version": "unauthorized", "capabilities": {"proxy": {"stable": root_h}}}
proposal_id = hashlib.sha256(json.dumps(mutation).encode()).hexdigest()
Path(f"blob_vault/proposals/{proposal_id}").parent.mkdir(parents=True, exist_ok=True)
Path(f"blob_vault/proposals/{proposal_id}").write_text(json.dumps(mutation))

res = run_cmd(["seed.py", "promote", proposal_id, "2"])
if "Consensus not reached" in res.stdout or "Consensus not reached" in res.stderr:
    print("PASS: Unauthorized mutation blocked.")
else:
    print(f"FAIL: Unauthorized mutation allowed! Result: {res.stdout} {res.stderr}")

print("\n--- Resilience Testing Complete ---")
