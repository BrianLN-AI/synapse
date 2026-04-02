import os
import sys
import json
import hashlib
import time
import glob
import subprocess
from pathlib import Path

# --- Safety & Security (f_5 Hardening) ---

_b = vars(__builtins__) if hasattr(__builtins__, "__dict__") else __builtins__
SAFE_BUILTINS = {
    k: _b[k] for k in [
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'chr',
        'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter', 'float',
        'format', 'frozenset', 'getattr', 'hasattr', 'hash', 'hex', 'id', 'int',
        'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
        'min', 'next', 'object', 'oct', 'ord', 'pow', 'print', 'range', 'repr',
        'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'str', 'sum',
        'tuple', 'type', 'vars', 'zip', 'Exception', 'ValueError', 'TypeError', 
        'KeyError', 'IndexError', 'StopIteration'
    ] if k in _b
}

def is_valid_hash(h: str) -> bool:
    """Strict SHA-256 Hex Validation."""
    if not isinstance(h, str) or len(h) != 64: return False
    try:
        int(h, 16)
        return True
    except ValueError: return False

# --- Storage Adapter (The Substrate Abstraction) ---

class VaultAdapter:
    def __init__(self, vault_dir: str = "blob_vault", collective_dir: str = "collective_vault", root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.vault_dir = self.root_dir / vault_dir
        self.collective_dir = self.root_dir / collective_dir
        self.telemetry_dir = self.vault_dir / "telemetry"
        self.cognitive_dir = self.vault_dir / "cognitive"
        self.state_dir = self.vault_dir / "state"
        self.proposals_dir = self.vault_dir / "proposals"
        self.signatures_dir = self.vault_dir / "signatures"
        self.index_file = self.vault_dir / "semantic_index.json"
        self.manifest_hash_file = self.root_dir / "manifest.hash"

        for d in [self.vault_dir, self.telemetry_dir, self.cognitive_dir, self.state_dir, self.proposals_dir, self.signatures_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_manifest_hash(self) -> str:
        if not self.manifest_hash_file.exists(): return None
        return self.manifest_hash_file.read_text().strip()

    def update_manifest_hash(self, h: str):
        self.manifest_hash_file.write_text(h)

    def read(self, h: str, is_bios: bool = False) -> str:
        path = self.vault_dir / h
        if not path.exists() or not path.is_file(): raise FileNotFoundError(f"Blob {h} not found.")
        return path.read_text()

    def write(self, data: str, type_hint: str = "generic") -> str:
        h = hashlib.sha256(data.encode()).hexdigest()
        path = self.vault_dir / h
        path.write_text(data)
        return h


    def get_state(self, state_id: str) -> dict:
        coll_path = self.collective_dir / "state" / str(state_id)
        local_path = self.state_dir / str(state_id)
        if coll_path.exists():
            with open(coll_path, 'r') as f: h = f.read().strip()
            try:
                state_data = json.loads(self.read(h))
                with open(local_path, 'w') as f: f.write(h)
                return state_data
            except: pass
        if local_path.exists():
            with open(local_path, 'r') as f: h = f.read().strip()
            try: return json.loads(self.read(h))
            except: pass
        return {}

    def put_state(self, state_id: str, state: dict):
        h = self.write(json.dumps(state))
        for d in [self.state_dir, self.collective_dir / "state"]:
            d.mkdir(parents=True, exist_ok=True)
            with open(d / str(state_id), 'w') as f: f.write(h)

    def index_get(self) -> dict:
        if not self.index_file.exists(): return {}
        with open(self.index_file, 'r') as f: return json.load(f)

    def index_put(self, index: dict):
        with open(self.index_file, 'w') as f: json.dump(index, f)

# --- The Linker (Cognitive & Admin Facade) ---

class Linker:
    def __init__(self, adapter: VaultAdapter):
        self.adapter = adapter

    def inference(self, prompt: str) -> str:
        start_t = time.perf_counter()
        res = f"Simulated reasoning for: {prompt[:50]}..."
        artifact = {"type": "cognitive_artifact", "prompt": prompt, "response": res, "latency": time.perf_counter() - start_t, "timestamp": time.time()}
        h = self.adapter.write(json.dumps(artifact))
        with open(self.adapter.cognitive_dir / h, 'w') as f: f.write(h)
        return res

    def embed(self, text: str) -> list:
        h = hashlib.md5(text.encode()).hexdigest()
        return [int(h[i:i+2], 16) / 255.0 for i in range(0, 8, 2)]

    def rerank(self, query: str, candidates: list) -> str:
        query = query.lower()
        for cand in candidates:
            if query in cand.get('description', '').lower(): return cand.get('hash')
        return candidates[0].get('hash') if candidates else None

    def propose(self, mutation: dict) -> str:
        h = hashlib.sha256(json.dumps(mutation).encode()).hexdigest()
        with open(self.adapter.proposals_dir / h, 'w') as f: json.dump(mutation, f)
        return h

    def sign(self, prop_id: str, node_id: str = "local-node") -> str:
        data = {"proposal_id": prop_id, "node_id": node_id, "timestamp": time.time()}
        h = hashlib.sha256(json.dumps(data).encode()).hexdigest()
        d = self.adapter.signatures_dir / prop_id
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{node_id}.sig", 'w') as f: json.dump(data, f)
        return h

    def tally(self, prop_id: str) -> int:
        d = self.adapter.signatures_dir / prop_id
        return len(list(d.glob("*.sig"))) if d.exists() else 0

    def branch(self, name: str) -> str:
        """Forks the current fabric into a separate temporal branch (Sub-Fabric)."""
        branch_root = self.adapter.root_dir / "branches" / name
        branch_root.mkdir(parents=True, exist_ok=True)
        
        # 1. Clone Registry
        root_h = self.adapter.get_manifest_hash()
        if root_h:
            (branch_root / "manifest.hash").write_text(root_h)
            
        # 2. Symlink/Link the Substrate (Vault)
        # In a real f_7, we'd use symlinks to share blobs without copying
        # For the seed, we'll point the sub-adapter to the parent vault
        return str(branch_root)

    def resolve_capability(self, name: str, version: str = "stable") -> str:
        root_h = self.adapter.get_manifest_hash()
        if not root_h: return None
        try:
            manifest = json.loads(self.adapter.read(root_h))
            return manifest.get("capabilities", {}).get(name, {}).get(version)
        except: return None

    def list_capabilities(self) -> list:
        root_h = self.adapter.get_manifest_hash()
        if not root_h: return []
        try:
            manifest = json.loads(self.adapter.read(root_h))
            return list(manifest.get("capabilities", {}).keys())
        except: return []

    def invoke_capability(self, name: str, context: dict = None, version: str = "stable") -> dict:
        h = self.resolve_capability(name, version)
        if not h: return {"result": None, "status": "failure", "error": f"Capability not found: {name}"}
        return self.invoke(h, context)

    def invoke(self, h: str, context: dict = None) -> dict:
        if not is_valid_hash(h): return {"result": None, "status": "failure", "error": f"Invalid SHA-256 Hash provided: {h}"}
        start_time = time.perf_counter()
        context = context or {}
        logs = []
        def log(msg): logs.append(f"[{time.time()}] {msg}")

        primitives = {
            "inference": self.inference, "embed": self.embed, "rerank": self.rerank,
            "get_capability": self.resolve_capability, "list_capabilities": self.list_capabilities,
            "invoke_capability": self.invoke_capability, "put": self.adapter.write, "propose": self.propose,
            "branch": self.branch
        }

        # 1. Proxy
        proxy_h = self.resolve_capability("proxy")
        request_envelope = context
        if proxy_h and h != proxy_h:
            try:
                scope = {"context": {"request": context, "timestamp": time.time(), "trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}, "log": log, "result": None, "__builtins__": __builtins__, "SAFE_BUILTINS": SAFE_BUILTINS}
                scope.update(primitives)
                exec(self.adapter.read(proxy_h), scope, scope)
                request_envelope = scope.get("result", request_envelope)
            except Exception as e: log(f"Proxy Error: {str(e)}")

        # 2. Broker
        execution_plan = {"method": "local_exec", "sandbox": "standard"}
        broker_h = self.resolve_capability("broker")
        if broker_h and h != broker_h:
            try:
                scope = {"context": {"target": h, "request": request_envelope}, "log": log, "result": None, "os": os, "glob": glob, "json": json, "hashlib": hashlib, "__builtins__": __builtins__, "SAFE_BUILTINS": SAFE_BUILTINS}
                scope.update(primitives)
                exec(self.adapter.read(broker_h), scope, scope)
                if scope.get("result"): execution_plan = scope["result"]
            except Exception as e: log(f"Broker Error: {str(e)}")

        # 3. State
        state_id = request_envelope.get("params", {}).get("state_id")
        state = self.adapter.get_state(state_id) if state_id else {}

        # 4. Engine
        try:
            payload = self.adapter.read(h)
            engine_h = self.resolve_capability("engine")
            if engine_h and h != engine_h:
                # Structural layers get full builtins and classes
                scope = {
                    "context": {"target_payload": payload, "target_context": request_envelope, "execution_plan": execution_plan, "state": state}, 
                    "log": log, "result": None, "subprocess": subprocess, "json": json, "__builtins__": __builtins__, 
                    "inference": self.inference, "embed": self.embed, "SAFE_BUILTINS": SAFE_BUILTINS,
                    "VaultAdapter": VaultAdapter, "Linker": Linker # Inject Classes
                }
                scope.update(primitives)
                exec(self.adapter.read(engine_h), scope, scope)
                result = scope.get("result")
                state = scope.get("context", {}).get("state", state)
            else:
                # Direct execution uses sandbox but can still get classes if needed for system tasks
                scope = {
                    "context": request_envelope, "log": log, "result": None, 
                    "execution_plan": execution_plan, "state": state, "__builtins__": SAFE_BUILTINS,
                    "VaultAdapter": VaultAdapter, "Linker": Linker # Inject Classes
                }
                scope.update(primitives)
                exec(payload, scope, scope)
                result = scope.get("result")
                state = scope.get("state", state)
            
            if result is None: raise ValueError("ABI Violation: No result assigned.")
            if state_id: self.adapter.put_state(state_id, state)
            status = "success"; error = None
        except Exception as e: status = "failure"; error = str(e); result = None

        telemetry = {"blob_hash": h, "request_envelope": request_envelope, "execution_plan": execution_plan, "status": status, "latency": time.perf_counter() - start_time, "logs": logs, "error": error, "timestamp": time.time()}
        self.adapter.write(json.dumps(telemetry))
        return {"result": result, "status": status, "error": error}

def main():
    adapter = VaultAdapter(); linker = Linker(adapter)
    if len(sys.argv) < 2: print("Usage: seed.py <command> [args]"); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "put": print(adapter.write(Path(sys.argv[2]).read_text() if os.path.exists(sys.argv[2]) else sys.argv[2]))
    elif cmd == "index":
        idx = adapter.index_get()
        idx[sys.argv[2]] = {"hash": sys.argv[2], "description": sys.argv[3], "vector": linker.embed(sys.argv[3])}
        adapter.index_put(idx); print(f"Indexed: {sys.argv[2]}")
    elif cmd == "sign": print(f"Signed {sys.argv[2]}: {linker.sign(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'local-node')}")
    elif cmd == "governance":
        jury_h = linker.resolve_capability("jury")
        if not jury_h: print("Error: No Jury capability"); sys.exit(1)
        scope = {"context": {"proposal_id": sys.argv[2]}, "log": lambda m: None, "result": None, "inference": linker.inference, "sign": linker.sign, "tally": linker.tally, "_raw_get": adapter.read, "json": json, "os": os, "__builtins__": __builtins__}
        exec(adapter.read(jury_h), scope, scope); print(json.dumps(scope.get("result"), indent=2))
    elif cmd == "tally": print(f"Signatures for {sys.argv[2]}: {linker.tally(sys.argv[2])}")
    elif cmd == "invoke": print(json.dumps(linker.invoke(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}), indent=2))
    elif cmd == "mcp":
        for line in sys.stdin:
            try:
                req = json.loads(line); m, p, rid = req.get("method"), req.get("params", {}), req.get("id")
                if m == "tools/list":
                    manifest = json.loads(adapter.read(adapter.get_manifest_hash()))
                    res = {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{"name": k, "versions": list(v.keys())} for k, v in manifest.get("capabilities", {}).items()]}}
                elif m == "tools/call": res = {"jsonrpc": "2.0", "id": rid, "result": linker.invoke(p.get("name"), {"params": p.get("arguments", {}), "intent": "mcp_call"})}
                else: res = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}
                print(json.dumps(res), flush=True)
            except Exception as e: print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)
    elif cmd == "promote":
        prop_id = sys.argv[2]; min_sigs = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        prop_path = adapter.proposals_dir / prop_id
        if not prop_path.exists(): manifest = json.loads(Path(sys.argv[2]).read_text())
        else:
            if linker.tally(prop_id) < min_sigs: print(f"FAILED: Consensus not reached for {prop_id}"); sys.exit(1)
            manifest = json.loads(prop_path.read_text())
        for name, versions in manifest.get("capabilities", {}).items():
            for ver, h in versions.items(): adapter.read(h)
        h = adapter.write(json.dumps(manifest)); adapter.update_manifest_hash(h); print(f"Successfully promoted: {h}")

if __name__ == "__main__": main()
