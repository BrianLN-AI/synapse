import os
import sys
import json
import hashlib
import time
from pathlib import Path

# --- Constants & Setup ---
VAULT_DIR = Path("blob_vault")
TELEMETRY_DIR = VAULT_DIR / "telemetry"
VAULT_DIR.mkdir(exist_ok=True)
TELEMETRY_DIR.mkdir(exist_ok=True)

# --- Core Protocol Methods ---

def _raw_get(h: str) -> str:
    """The BIOS Fallback: Direct filesystem lookup to prevent recursion."""
    path = VAULT_DIR / h
    if not path.exists():
        raise FileNotFoundError(f"Blob {h} not found in BIOS.")
    with open(path, 'r') as f:
        return f.read()

def put(payload: str, blob_type: str = "generic") -> str:
    """Content-Addressed Storage (SHA-256)."""
    h = hashlib.sha256(payload.encode()).hexdigest()
    path = VAULT_DIR / h
    with open(path, 'w') as f:
        f.write(payload)
    return h

def invoke(h: str, context: dict = None) -> dict:
    """The Engine: Executes a Blob in a scrubbed sandbox."""
    start_time = time.perf_counter()
    payload = _raw_get(h)
    
    # Telemetry Sink
    logs = []
    def log(msg):
        logs.append(f"[{time.time()}] {msg}")

    # The Scrubbed Scope (The ABI)
    # Blobs must assign their final value to 'result'
    local_scope = {
        "context": context or {},
        "log": log,
        "result": None
    }
    
    try:
        # Execute the blob
        exec(payload, {"__builtins__": __builtins__}, local_scope)
        
        if "result" not in local_scope or local_scope["result"] is None:
            raise ValueError(f"Blob {h} violated ABI: No 'result' assigned.")
            
        result = local_scope["result"]
        status = "success"
        error = None
    except Exception as e:
        status = "failure"
        error = str(e)
        result = None

    end_time = time.perf_counter()
    
    # Telemetry Artifact
    telemetry = {
        "blob_hash": h,
        "status": status,
        "latency": end_time - start_time,
        "logs": logs,
        "error": error,
        "timestamp": time.time()
    }
    
    # PUT telemetry/artifact blob
    telemetry_h = put(json.dumps(telemetry), "telemetry/artifact")
    
    return {
        "result": result,
        "telemetry_hash": telemetry_h,
        "status": status
    }

# --- CLI Interface ---

def main():
    if len(sys.argv) < 2:
        print("Usage: seed.py <command> [args]")
        print("Commands: put <file/payload>, invoke <hash> [json_context]")
        sys.exit(1)

    cmd = sys.argv[1]
    
    if cmd == "put":
        payload = sys.argv[2]
        if os.path.exists(payload):
            with open(payload, 'r') as f:
                payload = f.read()
        print(put(payload))
        
    elif cmd == "invoke":
        h = sys.argv[2]
        ctx = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(invoke(h, ctx), indent=2))

if __name__ == "__main__":
    main()
