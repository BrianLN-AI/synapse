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

def _raw_get(h: str, is_bios: bool = False) -> str:
    """The Linker Resolver: Checks L2 Discovery, falls back to BIOS."""
    
    # 1. BIOS Fallback: Direct filesystem lookup for system/bootstrap
    # or if we are already in the process of resolving L2 itself.
    if is_bios or not os.path.exists("manifest.hash"):
        path = VAULT_DIR / h
        if not path.exists():
            raise FileNotFoundError(f"Blob {h} not found in BIOS.")
        with open(path, 'r') as f:
            return f.read()

    # 2. Recursive Discovery (The Leap)
    # Load current system root
    with open("manifest.hash", "r") as f:
        root_h = f.read().strip()
    
    manifest = json.loads(_raw_get(root_h, is_bios=True))
    l2_h = manifest.get("layers", {}).get("l2")

    if not l2_h:
        # No Discovery Layer? Fail back to BIOS
        return _raw_get(h, is_bios=True)
    
    # Avoid infinite recursion: If we're looking for L2 itself, use BIOS
    if h == l2_h:
        return _raw_get(h, is_bios=True)

    # Use the L2 Blob to resolve the target hash
    # Note: invoke() will call _raw_get(), so we need to prevent infinite loops
    # here by carefully managing is_bios.
    # To keep it simple for the Seed, we'll use a direct internal invoke.
    try:
        # We use a simplified internal invocation to avoid seed.invoke's overhead here
        l2_payload = _raw_get(l2_h, is_bios=True)
        l2_scope = {"context": {"target": h}, "log": lambda m: None, "result": None}
        exec(l2_payload, {"__builtins__": __builtins__}, l2_scope)
        
        resolved_path = l2_scope.get("result", {}).get("path")
        if resolved_path and os.path.exists(resolved_path):
            with open(resolved_path, "r") as f:
                return f.read()
    except Exception as e:
        # If Discovery fails, the Mycelium falls back to BIOS
        pass

    return _raw_get(h, is_bios=True)

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
    
    # 1. Broker Consultation (The Broker Leap)
    # Check if a manifest and L3 exist to provide an execution plan
    execution_plan = {"method": "local_exec", "sandbox": "standard"}
    if os.path.exists("manifest.hash"):
        try:
            with open("manifest.hash", "r") as f:
                root_h = f.read().strip()
            manifest = json.loads(_raw_get(root_h, is_bios=True))
            l3_h = manifest.get("layers", {}).get("l3")
            if l3_h:
                # Avoid infinite recursion: don't broker the broker
                if h != l3_h:
                    l3_payload = _raw_get(l3_h, is_bios=True)
                    l3_scope = {"context": {"target": h, "priority": context.get("priority", "normal")}, "log": lambda m: None, "result": None}
                    exec(l3_payload, {"__builtins__": __builtins__}, l3_scope)
                    execution_plan = l3_scope.get("result", execution_plan)
        except Exception:
            # Fallback to standard if brokering fails
            pass

    # 2. Binding (The Engine)
    payload = _raw_get(h)
    
    # Telemetry Sink
    logs = []
    def log(msg):
        logs.append(f"[{time.time()}] {msg}")

    # The Scrubbed Scope (The ABI)
    local_scope = {
        "context": context or {},
        "log": log,
        "result": None,
        "execution_plan": execution_plan # Inject the plan for context
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
        "execution_plan": execution_plan,
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
        
    elif cmd == "promote":
        manifest_path = sys.argv[2]
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # 1. Integrity Check (Verify all hashes in manifest exist)
        print("Starting Integrity Check...")
        for layer, h in manifest.get("layers", {}).items():
            print(f"Verifying {layer}: {h}...")
            try:
                _raw_get(h)
            except FileNotFoundError:
                print(f"FAILED: Hash {h} for {layer} not found in vault!")
                sys.exit(1)
        
        # 2. Store the manifest as a blob
        manifest_h = put(json.dumps(manifest), "system/manifest")
        
        # 3. Update the global manifest pointer
        with open("manifest.hash", "w") as f:
            f.write(manifest_h)
        
        print(f"Successfully promoted manifest: {manifest_h}")

if __name__ == "__main__":
    main()
