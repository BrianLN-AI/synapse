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
        self.keys_dir = self.root_dir / "keys"
        self.telemetry_dir = self.vault_dir / "telemetry"
        self.cognitive_dir = self.vault_dir / "cognitive"
        self.state_dir = self.vault_dir / "state"
        self.proposals_dir = self.vault_dir / "proposals"
        self.signatures_dir = self.vault_dir / "signatures"
        self.index_file = self.vault_dir / "semantic_index.json"
        self.manifest_hash_file = self.root_dir / "manifest.hash"
        
        for d in [self.vault_dir, self.telemetry_dir, self.cognitive_dir, self.state_dir, self.proposals_dir, self.signatures_dir, self.keys_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Initialize Node Identity if missing
        self._ensure_identity()

    def _ensure_identity(self):
        """Generates a node identity if one doesn't exist."""
        pub_file = self.keys_dir / "identity.pub"
        priv_file = self.keys_dir / "identity.key"
        if not pub_file.exists():
            # Simulated Ed25519 generation
            seed = hashlib.sha256(str(time.time()).encode()).hexdigest()
            priv_file.write_text(f"priv-{seed}")
            pub_file.write_text(f"pub-{seed[:16]}")

    def get_public_key(self) -> str:
        return (self.keys_dir / "identity.pub").read_text()

    def crypto_sign(self, data: str) -> str:
        """Simulated Cryptographic Sign."""
        priv = (self.keys_dir / "identity.key").read_text()
        return hashlib.sha256((priv + data).encode()).hexdigest()

    def crypto_verify(self, data: str, sig: str, pubkey: str) -> bool:
        """Simulated Cryptographic Verify."""
        return sig is not None and len(sig) == 64

    def read(self, h: str, is_bios: bool = False) -> str:
        path = self.vault_dir / h
        if not path.exists() or not path.is_file(): raise FileNotFoundError(f"Blob {h} not found.")
        return path.read_text()

    def write(self, data: str, type_hint: str = "generic", lineage: dict = None) -> str:
        h = hashlib.sha256(data.encode()).hexdigest()
        path = self.vault_dir / h
        path.write_text(data)
        if lineage:
            prov_data = {"blob_hash": h, "type_hint": type_hint, "lineage": lineage, "timestamp": time.time()}
            prov_path = self.vault_dir / "providence" / h
            prov_path.parent.mkdir(parents=True, exist_ok=True)
            prov_path.write_text(json.dumps(prov_data))
        return h

    def get_manifest_hash(self) -> str:
        if not self.manifest_hash_file.exists(): return None
        return self.manifest_hash_file.read_text().strip()

    def update_manifest_hash(self, h: str):
        self.manifest_hash_file.write_text(h)

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

    def sign(self, prop_id: str, node_id: str = "local-node", conditions: dict = None) -> str:
        data = {"target_id": prop_id, "node_id": node_id, "timestamp": time.time(), "conditions": conditions or {}}
        h = hashlib.sha256(json.dumps(data).encode()).hexdigest()
        d = self.adapter.signatures_dir / prop_id
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{node_id}.sig", 'w') as f: json.dump(data, f)
        return h

    def is_authorized(self, h: str, context: dict) -> bool:
        d = self.adapter.signatures_dir / h
        if not d.exists(): return False
        current_trace = context.get('metadata', {}).get('trace_id')
        valid_sigs = 0
        for sig_file in d.glob("*.sig"):
            try:
                sig = json.loads(sig_file.read_text())
                cond = sig.get('conditions', {})
                if 'trace_id' in cond and cond['trace_id'] != current_trace: continue
                if 'expires_at' in cond and time.time() > cond['expires_at']: continue
                valid_sigs += 1
            except: continue
        return valid_sigs > 0

    def tally(self, prop_id: str) -> int:
        d = self.adapter.signatures_dir / prop_id
        return len(list(d.glob("*.sig"))) if d.exists() else 0

    def branch(self, name: str) -> str:
        branch_root = self.adapter.root_dir / "branches" / name
        branch_root.mkdir(parents=True, exist_ok=True)
        root_h = self.adapter.get_manifest_hash()
        if root_h: (branch_root / "manifest.hash").write_text(root_h)
        return str(branch_root)

    def rollback(self, h: str):
        try:
            self.adapter.read(h)
            self.adapter.update_manifest_hash(h)
            return f"Rollback success: Root is now {h}"
        except Exception as e: return f"Rollback failed: {str(e)}"

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
        # Cognitive & Discovery Primitives
        primitives = {
            "inference": self.inference, "embed": self.embed, "rerank": self.rerank,
            "get_capability": self.resolve_capability, "list_capabilities": self.list_capabilities,
            "invoke_capability": self.invoke_capability, "read_blob": self.adapter.read, "json": json,
            "invoke": self.invoke, # f_11 Recursive Execution
            "crypto_sign": self.adapter.crypto_sign,
            "crypto_verify": self.adapter.crypto_verify,
            "get_public_key": self.adapter.get_public_key
        }

        if self.is_authorized(h, context):
            primitives.update({"put": self.adapter.write, "propose": self.propose, "branch": self.branch, "rollback": self.rollback, "sign": self.sign, "tally": self.tally})
        
        proxy_h = self.resolve_capability("proxy")
        request_envelope = context
        if proxy_h and h != proxy_h:
            try:
                scope = {"context": {"request": context, "timestamp": time.time(), "trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}, "log": log, "result": None, "__builtins__": __builtins__, "SAFE_BUILTINS": SAFE_BUILTINS}
                scope.update(primitives)
                exec(self.adapter.read(proxy_h), scope, scope)
                request_envelope = scope.get("result", request_envelope)
            except Exception as e: log(f"Proxy Error: {str(e)}")
        execution_plan = {"method": "local_exec", "sandbox": "standard"}
        broker_h = self.resolve_capability("broker")
        if broker_h and h != broker_h:
            try:
                scope = {"context": {"target": h, "request": request_envelope}, "log": log, "result": None, "os": os, "glob": glob, "json": json, "hashlib": hashlib, "__builtins__": __builtins__, "SAFE_BUILTINS": SAFE_BUILTINS, "put": self.adapter.write, "propose": self.propose}
                scope.update(primitives)
                exec(self.adapter.read(broker_h), scope, scope)
                if scope.get("result"): execution_plan = scope["result"]
            except Exception as e: log(f"Broker Error: {str(e)}")
        state_id = request_envelope.get("params", {}).get("state_id")
        state = self.adapter.get_state(state_id) if state_id else {}
        try:
            payload = self.adapter.read(h)
            engine_h = self.resolve_capability("engine")
            if engine_h and h != engine_h:
                scope = {"context": {"target_payload": payload, "target_context": request_envelope, "execution_plan": execution_plan, "state": state}, "log": log, "result": None, "subprocess": subprocess, "json": json, "hashlib": hashlib, "__builtins__": __builtins__, "inference": self.inference, "embed": self.embed, "invoke": self.invoke, "SAFE_BUILTINS": SAFE_BUILTINS, "VaultAdapter": VaultAdapter, "Linker": Linker}
                scope.update(primitives)
                exec(self.adapter.read(engine_h), scope, scope)
                result = scope.get("result"); state = scope.get("context", {}).get("state", state)
            else:
                scope = {"context": request_envelope, "log": log, "result": None, "execution_plan": execution_plan, "state": state, "hashlib": hashlib, "__builtins__": SAFE_BUILTINS, "inference": self.inference, "embed": self.embed, "invoke": self.invoke, "VaultAdapter": VaultAdapter, "Linker": Linker}
                scope.update(primitives)
                exec(payload, scope, scope)
                result = scope.get("result"); state = scope.get("state", state)
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
    if cmd == "put":
        payload = Path(sys.argv[2]).read_text() if os.path.exists(sys.argv[2]) else sys.argv[2]
        type_hint = sys.argv[3] if len(sys.argv) > 3 else "generic"
        lineage = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        print(adapter.write(payload, type_hint, lineage))
    elif cmd == "index":
        idx = adapter.index_get()
        idx[sys.argv[2]] = {"hash": sys.argv[2], "description": sys.argv[3], "vector": linker.embed(sys.argv[3])}
        adapter.index_put(idx); print(f"Indexed: {sys.argv[2]}")
    elif cmd == "crypto_sign":
        print(f"Signature: {adapter.crypto_sign(sys.argv[2])}")
    elif cmd == "crypto_verify":
        # seed.py crypto_verify <data> <sig> <pubkey>
        print(f"Valid: {adapter.crypto_verify(sys.argv[2], sys.argv[3], sys.argv[4])}")
    elif cmd == "pubkey":
        print(f"Identity: {adapter.get_public_key()}")
    elif cmd == "sign":
        node = sys.argv[3] if len(sys.argv) > 3 else "local-node"
        cond = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        print(f"Signed {sys.argv[2]}: {linker.sign(sys.argv[2], node, cond)}")
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
