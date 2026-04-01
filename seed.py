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
SEMANTIC_INDEX = VAULT_DIR / "semantic_index.json"
VAULT_DIR.mkdir(exist_ok=True)
TELEMETRY_DIR.mkdir(exist_ok=True)

# --- Cognitive Primitives (f_4 Symbiotic Leap) ---

def inference(prompt: str) -> str:
    """Mocked Inference with Telemetry (f_5)."""
    start_t = time.perf_counter()
    # In f_4 actual, this calls a local or remote model
    res = f"Simulated reasoning for: {prompt[:50]}..."
    end_t = time.perf_counter()
    
    # Generate Cognitive Artifact
    artifact = {
        "type": "cognitive_artifact",
        "prompt": prompt,
        "response": res,
        "latency": end_t - start_t,
        "timestamp": time.time()
    }
    h = put(json.dumps(artifact), "cognitive/artifact")
    
    # Store reference in cognitive vault for easy scanning
    path = VAULT_DIR / "cognitive" / h
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f: f.write(h)
    
    return res

def embed(text: str) -> list:
    """Mocked Embedding: Simulates vector generation."""
    # Returns a deterministic mock vector based on the string
    h = hashlib.md5(text.encode()).hexdigest()
    return [int(h[i:i+2], 16) / 255.0 for i in range(0, 8, 2)]

def rerank(query: str, candidates: list) -> str:
    """Mocked Reranking: Picks the best hash based on semantic intent."""
    # Simplistic 'keyword' match for simulation
    query = query.lower()
    for cand in candidates:
        if query in cand.get('description', '').lower():
            return cand.get('hash')
    return candidates[0].get('hash') if candidates else None

def index_blob(h: str, description: str):
    """Adds a blob to the semantic index."""
    idx = {}
    if SEMANTIC_INDEX.exists():
        with open(SEMANTIC_INDEX, 'r') as f: idx = json.load(f)
    idx[h] = {"hash": h, "description": description, "vector": embed(description)}
    with open(SEMANTIC_INDEX, 'w') as f: json.dump(idx, f)

# --- Security & Governance (f_4 Symbiotic Leap) ---

def propose(mutation: dict) -> str:
    """Saves a draft manifest as a Proposal."""
    proposal_h = hashlib.sha256(json.dumps(mutation).encode()).hexdigest()
    path = VAULT_DIR / "proposals" / proposal_h
    with open(path, 'w') as f: json.dump(mutation, f)
    return proposal_h

def sign(proposal_id: str, node_id: str = "local-node") -> str:
    """Simulates a cryptographic signature on a proposal."""
    sig_data = {"proposal_id": proposal_id, "node_id": node_id, "timestamp": time.time()}
    sig_h = hashlib.sha256(json.dumps(sig_data).encode()).hexdigest()
    path = VAULT_DIR / "signatures" / proposal_id / f"{node_id}.sig"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f: json.dump(sig_data, f)
    return sig_h

def tally(proposal_id: str) -> int:
    """Counts valid signatures for a proposal."""
    path = VAULT_DIR / "signatures" / proposal_id
    if not path.exists(): return 0
    return len(list(path.glob("*.sig")))

# --- Core Protocol Methods ---

def _raw_get(h: str, is_bios: bool = False) -> str:
    """The Linker Resolver: Checks L2 Discovery, falls back to BIOS."""
    if is_bios or not os.path.exists("manifest.hash"):
        path = VAULT_DIR / h
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Blob {h} not found in BIOS.")
        with open(path, 'r') as f:
            return f.read()

    # Recursive Discovery
    with open("manifest.hash", "r") as f:
        root_h = f.read().strip()
    manifest = json.loads(_raw_get(root_h, is_bios=True))
    l2_h = manifest.get("capabilities", {}).get("librarian", {}).get("stable")

    if not l2_h or h == l2_h:
        return _raw_get(h, is_bios=True)

    try:
        vault_tiers = ["blob_vault", "remote_vault", "collective_vault"]
        l2_payload = _raw_get(l2_h, is_bios=True)
        # Pass Cognitive primitives to Librarian
        l2_scope = {
            "context": {"target": h, "vault_tiers": vault_tiers}, 
            "log": lambda m: None, "result": None,
            "embed": embed, "rerank": rerank, "inference": inference,
            "json": json, "os": os, "glob": glob
        }
        exec(l2_payload, l2_scope, l2_scope)
        resolved_path = l2_scope.get("result", {}).get("path")
        if resolved_path and os.path.exists(resolved_path):
            with open(resolved_path, "r") as f:
                return f.read()
    except Exception: pass
    return _raw_get(h, is_bios=True)

def put(payload: str, blob_type: str = "generic") -> str:
    """Content-Addressed Storage (SHA-256)."""
    h = hashlib.sha256(payload.encode()).hexdigest()
    path = VAULT_DIR / h
    with open(path, 'w') as f: f.write(payload)
    return h

def _resolve_capability(name: str, version: str = "stable") -> str:
    """Translates a semantic capability name into a Content-Hash via the Registry."""
    if not os.path.exists("manifest.hash"): return None
    try:
        with open("manifest.hash", "r") as f: root_h = f.read().strip()
        manifest = json.loads(_raw_get(root_h, is_bios=True))
        return manifest.get("capabilities", {}).get(name, {}).get(version)
    except Exception: return None

def _invoke_jury(proposal_id: str) -> dict:
    """Internal: Invokes the Jury capability to evaluate a proposal."""
    jury_h = _resolve_capability("jury")
    if not jury_h: return {"status": "error", "message": "No Jury capability found"}
    
    try:
        jury_payload = _raw_get(jury_h, is_bios=True)
        # Jury needs access to raw_get to read the proposal and new blobs
        jury_scope = {
            "context": {"proposal_id": proposal_id},
            "log": lambda m: None, "result": None,
            "inference": inference, "sign": sign, "tally": tally,
            "_raw_get": _raw_get, "json": json, "os": os, "__builtins__": __builtins__
        }
        exec(jury_payload, jury_scope, jury_scope)
        return {"status": "success", "result": jury_scope.get("result")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def invoke(h: str, context: dict = None) -> dict:
    """The Engine: Executes a Blob in a scrubbed sandbox."""
    start_time = time.perf_counter()
    context = context or {}
    
    # 1. Proxy Normalization
    request_envelope = context
    proxy_h = _resolve_capability("proxy")
    if proxy_h and h != proxy_h:
        try:
            l1_payload = _raw_get(proxy_h, is_bios=True)
            l1_scope = {
                "context": {"request": context, "timestamp": time.time(), "trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}, 
                "log": lambda m: None, "result": None, "__builtins__": __builtins__,
                "inference": inference, "embed": embed # Inject cognitive
            }
            exec(l1_payload, l1_scope, l1_scope)
            request_envelope = l1_scope.get("result", request_envelope)
        except Exception: pass

    # 2. Broker Planning
    execution_plan = {"method": "local_exec", "sandbox": "standard"}
    broker_h = _resolve_capability("broker")
    if broker_h and h != broker_h:
        try:
            l3_payload = _raw_get(broker_h, is_bios=True)
            l3_scope = {
                "context": {"target": h, "request": request_envelope}, 
                "log": lambda m: None, "result": None, 
                "os": os, "glob": glob, "json": json, "__builtins__": __builtins__,
                "inference": inference, "embed": embed, "rerank": rerank,
                "put": put, "propose": propose # Inject Mutation Primitives
            }
            exec(l3_payload, l3_scope, l3_scope)
            if l3_scope.get("result"): execution_plan = l3_scope["result"]
        except Exception: pass

    # 3. State Resolution
    state = {}
    state_id = request_envelope.get("params", {}).get("state_id")
    state_file = VAULT_DIR / "state" / str(state_id) if state_id else None
    collective_state_file = Path("collective_vault") / "state" / str(state_id) if state_id else None
    
    if state_id and collective_state_file and collective_state_file.exists():
        try:
            with open(collective_state_file, "r") as f: state_h = f.read().strip()
            state = json.loads(_raw_get(state_h, is_bios=True))
            if state_file:
                state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(state_file, "w") as f: f.write(state_h)
        except Exception: pass
    elif state_id and state_file and state_file.exists():
        try:
            with open(state_file, "r") as f:
                state_h = f.read().strip()
                state = json.loads(_raw_get(state_h, is_bios=True))
        except Exception: pass

    # 4. Binding & Execution
    payload = _raw_get(h)
    logs = []
    def log(msg): logs.append(f"[{time.time()}] {msg}")

    try:
        engine_h = _resolve_capability("engine")
        if engine_h and h != engine_h:
            l4_payload = _raw_get(engine_h, is_bios=True)
            l4_scope = {
                "context": {"target_payload": payload, "target_context": request_envelope, "execution_plan": execution_plan, "state": state},
                "log": log, "result": None, "subprocess": subprocess, "json": json, "__builtins__": __builtins__,
                "inference": inference, "embed": embed # Inject cognitive
            }
            exec(l4_payload, l4_scope, l4_scope)
            result = l4_scope.get("result")
            state = l4_scope.get("context", {}).get("state", state)
        else:
            local_scope = {"context": request_envelope, "log": log, "result": None, "execution_plan": execution_plan, "state": state, "__builtins__": __builtins__, "inference": inference, "embed": embed}
            exec(payload, local_scope, local_scope)
            result = local_scope.get("result")
            state = local_scope.get("state", state)
            
        if result is None: raise ValueError(f"Blob {h} violated ABI: No 'result' assigned.")

        # 5. State Persistence
        if state_id:
            state_h = put(json.dumps(state), "system/state")
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f: f.write(state_h)
            if collective_state_file:
                collective_state_file.parent.mkdir(parents=True, exist_ok=True)
                with open(collective_state_file, "w") as f: f.write(state_h)

        status = "success"
        error = None
    except Exception as e:
        status = "failure"
        error = str(e)
        result = None

    end_time = time.perf_counter()
    telemetry = {"blob_hash": h, "request_envelope": request_envelope, "execution_plan": execution_plan, "status": status, "latency": end_time - start_time, "logs": logs, "error": error, "timestamp": time.time()}
    put(json.dumps(telemetry), "telemetry/artifact")
    return {"result": result, "status": status}

# --- CLI Interface ---

def main():
    if len(sys.argv) < 2:
        print("Usage: seed.py <command> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "put":
        payload = sys.argv[2]
        if os.path.exists(payload):
            with open(payload, 'r') as f: payload = f.read()
        print(put(payload))
    elif cmd == "index":
        # seed.py index <hash> <description>
        index_blob(sys.argv[2], sys.argv[3])
        print(f"Indexed: {sys.argv[2]}")
    elif cmd == "sign":
        # seed.py sign <proposal_id> <node_id>
        node = sys.argv[3] if len(sys.argv) > 3 else "local-node"
        sig = sign(sys.argv[2], node)
        print(f"Signed {sys.argv[2]} as {node}: {sig}")
    elif cmd == "governance":
        # seed.py governance <proposal_id>
        print(json.dumps(_invoke_jury(sys.argv[2]), indent=2))
    elif cmd == "tally":
        # seed.py tally <proposal_id>
        print(f"Signatures for {sys.argv[2]}: {tally(sys.argv[2])}")
    elif cmd == "invoke":
        h = sys.argv[2]
        ctx = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(invoke(h, ctx), indent=2))
    elif cmd == "mcp":
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method, params, req_id = request.get("method"), request.get("params", {}), request.get("id")
                if method == "tools/list":
                    with open("manifest.hash", "r") as f: root_h = f.read().strip()
                    manifest = json.loads(_raw_get(root_h, is_bios=True))
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [{"name": k, "versions": list(v.keys())} for k, v in manifest.get("capabilities", {}).items()]}}
                elif method == "tools/call":
                    res = invoke(params.get("name"), {"params": params.get("arguments", {}), "intent": "mcp_call"})
                    response = {"jsonrpc": "2.0", "id": req_id, "result": res}
                else: response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
                print(json.dumps(response), flush=True)
            except Exception as e: print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)
    elif cmd == "promote":
        # Usage: seed.py promote <proposal_id> <min_signatures>
        proposal_id = sys.argv[2]
        min_sigs = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        
        proposal_path = VAULT_DIR / "proposals" / proposal_id
        if not proposal_path.exists():
            # Fallback for manual legacy promotion
            with open(sys.argv[2], 'r') as f: manifest = json.load(f)
        else:
            # Formal Governance Promotion
            current_sigs = tally(proposal_id)
            if current_sigs < min_sigs:
                print(f"FAILED: Proposal {proposal_id} has only {current_sigs}/{min_sigs} signatures. Consensus not reached.")
                sys.exit(1)
            with open(proposal_path, 'r') as f: manifest = json.load(f)

        for name, versions in manifest.get("capabilities", {}).items():
            for ver, h in versions.items(): _raw_get(h)
        
        h = put(json.dumps(manifest), "system/manifest")
        with open("manifest.hash", "w") as f: f.write(h)
        print(f"Successfully promoted: {h}")

if __name__ == "__main__": main()
