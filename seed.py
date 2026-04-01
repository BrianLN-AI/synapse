import os
import sys
import json
import hashlib
import time
import glob
import subprocess
from pathlib import Path

# --- Constants & Setup ---
VAULT_DIR = Path("blob_vault")
TELEMETRY_DIR = VAULT_DIR / "telemetry"
VAULT_DIR.mkdir(exist_ok=True)
TELEMETRY_DIR.mkdir(exist_ok=True)

# --- Core Protocol Methods ---

def _raw_get(h: str, is_bios: bool = False) -> str:
    """The Linker Resolver: Checks L2 Discovery, falls back to BIOS."""
    
    # 1. BIOS Fallback: Direct filesystem lookup
    if is_bios or not os.path.exists("manifest.hash"):
        path = VAULT_DIR / h
        if not path.exists() or not path.is_file():
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
    try:
        # Pass vault_tiers to L2 (Simulated Tiered Discovery)
        vault_tiers = ["blob_vault", "remote_vault"]
        l2_payload = _raw_get(l2_h, is_bios=True)
        l2_scope = {"context": {"target": h, "vault_tiers": vault_tiers}, "log": lambda m: None, "result": None}
        exec(l2_payload, {"import os": os, "__builtins__": __builtins__}, l2_scope)
        
        resolved_path = l2_scope.get("result", {}).get("path")
        if resolved_path and os.path.exists(resolved_path):
            with open(resolved_path, "r") as f:
                return f.read()
    except Exception as e:
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
    context = context or {}
    
    # 1. Interface Normalization (The Interface Leap)
    # Check for manifest and L1 to normalize the incoming context
    request_envelope = context
    if os.path.exists("manifest.hash"):
        try:
            with open("manifest.hash", "r") as f:
                root_h = f.read().strip()
            manifest = json.loads(_raw_get(root_h, is_bios=True))
            l1_h = manifest.get("layers", {}).get("l1")
            if l1_h and h != l1_h:
                l1_payload = _raw_get(l1_h, is_bios=True)
                l1_scope = {"context": {"request": context, "timestamp": time.time(), "trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}, "log": lambda m: None, "result": None}
                exec(l1_payload, {"__builtins__": __builtins__}, l1_scope)
                request_envelope = l1_scope.get("result", request_envelope)
        except Exception:
            pass

    # 2. Broker Consultation (The Broker Leap)
    execution_plan = {"method": "local_exec", "sandbox": "standard"}
    if os.path.exists("manifest.hash"):
        try:
            with open("manifest.hash", "r") as f:
                root_h = f.read().strip()
            manifest = json.loads(_raw_get(root_h, is_bios=True))
            l3_h = manifest.get("layers", {}).get("l3")
            if l3_h and h != l3_h:
                l3_payload = _raw_get(l3_h, is_bios=True)
                # Pass full request_envelope to L3 for smarter planning
                l3_scope = {
                    "context": {"target": h, "request": request_envelope}, 
                    "log": lambda m: None, 
                    "result": None,
                    "os": os,
                    "glob": glob,
                    "json": json
                }
                # Use l3_scope for both globals and locals to be safe
                exec(l3_payload, l3_scope, l3_scope)
                # UPDATE the plan with the results from the Broker
                if l3_scope.get("result"):
                    execution_plan = l3_scope["result"]
        except Exception:
            pass

    # 3. Binding (The Engine)
    payload = _raw_get(h)
    
    # Telemetry Sink
    logs = []
    def log(msg):
        logs.append(f"[{time.time()}] {msg}")

    # Use Layer 4 (L4) Binding if available (The Binding Leap)
    try:
        if os.path.exists("manifest.hash"):
            with open("manifest.hash", "r") as f:
                root_h = f.read().strip()
            manifest = json.loads(_raw_get(root_h, is_bios=True))
            l4_h = manifest.get("layers", {}).get("l4")
            if l4_h and h != l4_h:
                l4_payload = _raw_get(l4_h, is_bios=True)
                # Pass payload and plan to L4 for binding
                import subprocess
                l4_scope = {
                    "context": {
                        "target_payload": payload,
                        "target_context": request_envelope,
                        "execution_plan": execution_plan
                    },
                    "log": log, # Share log sink for L4 trace
                    "result": None,
                    "subprocess": subprocess, # Inject for external runtimes
                    "json": json # Inject for serialization
                }
                exec(l4_payload, {"__builtins__": __builtins__}, l4_scope)
                result = l4_scope.get("result")
                status = "success"
                error = None
            else:
                # Fallback to direct execution if L4 not found or we're invoking L4 itself
                local_scope = {"context": request_envelope, "log": log, "result": None, "execution_plan": execution_plan}
                exec(payload, {"__builtins__": __builtins__}, local_scope)
                result = local_scope.get("result")
                status = "success"
                error = None
        else:
            # Fallback for no manifest (BIOS)
            local_scope = {"context": request_envelope, "log": log, "result": None, "execution_plan": execution_plan}
            exec(payload, {"__builtins__": __builtins__}, local_scope)
            result = local_scope.get("result")
            status = "success"
            error = None
            
        if result is None:
            raise ValueError(f"Blob {h} violated ABI: No 'result' assigned.")

    except Exception as e:
        status = "failure"
        error = str(e)
        result = None

    end_time = time.perf_counter()
    
    # Telemetry Artifact
    telemetry = {
        "blob_hash": h,
        "request_envelope": request_envelope,
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
        
    elif cmd == "mcp":
        # Model Context Protocol (MCP) Stdio Loop
        # Listens for JSON-RPC on stdin
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                req_id = request.get("id")

                if method == "tools/list":
                    # Resolve manifest to show available layers as tools
                    with open("manifest.hash", "r") as f:
                        root_h = f.read().strip()
                    manifest = json.loads(_raw_get(root_h, is_bios=True))
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": [{"name": k, "hash": v} for k, v in manifest.get("layers", {}).items()]
                        }
                    }
                elif method == "tools/call":
                    # Call a specific hash or layer name
                    tool_hash = params.get("name") # In Synapse, tool name can be the hash
                    tool_params = params.get("arguments", {})
                    res = invoke(tool_hash, {"params": tool_params, "intent": "mcp_call"})
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": res
                    }
                else:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
                
                print(json.dumps(response), flush=True)
            except Exception as e:
                print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)

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
