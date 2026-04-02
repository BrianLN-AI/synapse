import os
import sys
import json
import hashlib
import time
import glob
import subprocess
from pathlib import Path

# --- Storage Adapter (The Substrate Abstraction) ---

class VaultAdapter:
    """Consolidates all filesystem I/O for the Linker."""
    def __init__(self, vault_dir: str = "blob_vault", collective_dir: str = "collective_vault"):
        self.vault_dir = Path(vault_dir)
        self.collective_dir = Path(collective_dir)
        self.telemetry_dir = self.vault_dir / "telemetry"
        self.cognitive_dir = self.vault_dir / "cognitive"
        self.state_dir = self.vault_dir / "state"
        self.proposals_dir = self.vault_dir / "proposals"
        self.signatures_dir = self.vault_dir / "signatures"
        self.index_file = self.vault_dir / "semantic_index.json"
        
        for d in [self.vault_dir, self.telemetry_dir, self.cognitive_dir, self.state_dir, self.proposals_dir, self.signatures_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def read(self, h: str, is_bios: bool = False) -> str:
        """Reads a blob by hash with a BIOS fallback."""
        path = self.vault_dir / h
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Blob {h} not found.")
        with open(path, 'r') as f: return f.read()

    def write(self, data: str, type_hint: str = "generic") -> str:
        """Writes an immutable blob and returns its hash."""
        h = hashlib.sha256(data.encode()).hexdigest()
        path = self.vault_dir / h
        with open(path, 'w') as f: f.write(data)
        return h

    def get_manifest_hash(self) -> str:
        if not os.path.exists("manifest.hash"): return None
        with open("manifest.hash", "r") as f: return f.read().strip()

    def update_manifest_hash(self, h: str):
        with open("manifest.hash", "w") as f: f.write(h)

    def get_state(self, state_id: str) -> dict:
        """Syncs state from collective, then local."""
        coll_path = self.collective_dir / "state" / str(state_id)
        local_path = self.state_dir / str(state_id)
        
        # Try collective sync first
        if coll_path.exists():
            with open(coll_path, 'r') as f: h = f.read().strip()
            try:
                state_data = json.loads(self.read(h))
                # Update local cache
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
        # Push to both local and collective
        for d in [self.state_dir, self.collective_dir / "state"]:
            d.mkdir(parents=True, exist_ok=True)
            with open(d / str(state_id), 'w') as f: f.write(h)

    def list_artifacts(self, category: str = "cognitive", count: int = 10) -> list:
        d = self.cognitive_dir if category == "cognitive" else self.telemetry_dir
        files = sorted(list(d.glob("*")), key=os.path.getmtime)
        results = []
        for f in files[-count:]:
            try:
                h = f.read_text().strip() if f.is_file() else None
                if h: results.append(json.loads(self.read(h)))
            except: continue
        return results

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
        # Log to cognitive vault
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

    def resolve_capability(self, name: str, version: str = "stable") -> str:
        root_h = self.adapter.get_manifest_hash()
        if not root_h: return None
        try:
            manifest = json.loads(self.adapter.read(root_h))
            return manifest.get("capabilities", {}).get(name, {}).get(version)
        except: return None

    def invoke(self, h: str, context: dict = None) -> dict:
        if not h or not isinstance(h, str):
            return {"result": None, "status": "failure", "error": "Invalid or empty Blob Hash provided."}
        start_time = time.perf_counter()
        context = context or {}
        logs = []
        def log(msg): logs.append(f"[{time.time()}] {msg}")

        # 1. Proxy
        proxy_h = self.resolve_capability("proxy")
        request_envelope = context
        if proxy_h and h != proxy_h:
            try:
                scope = {"context": {"request": context, "timestamp": time.time(), "trace_id": "syn-" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8]}, "log": log, "result": None, "__builtins__": __builtins__, "inference": self.inference, "embed": self.embed}
                exec(self.adapter.read(proxy_h), scope, scope)
                request_envelope = scope.get("result", request_envelope)
            except: pass

        # 2. Broker
        execution_plan = {"method": "local_exec", "sandbox": "standard"}
        broker_h = self.resolve_capability("broker")
        if broker_h and h != broker_h:
            try:
                scope = {"context": {"target": h, "request": request_envelope}, "log": log, "result": None, "os": os, "glob": glob, "json": json, "hashlib": hashlib, "__builtins__": __builtins__, "inference": self.inference, "embed": self.embed, "rerank": self.rerank, "put": self.adapter.write, "propose": self.propose}
                exec(self.adapter.read(broker_h), scope, scope)
                if scope.get("result"): execution_plan = scope["result"]
            except: pass

        # 3. State
        state_id = request_envelope.get("params", {}).get("state_id")
        state = self.adapter.get_state(state_id) if state_id else {}

        # 4. Engine
        try:
            payload = self.adapter.read(h)
            engine_h = self.resolve_capability("engine")
            if engine_h and h != engine_h:
                scope = {"context": {"target_payload": payload, "target_context": request_envelope, "execution_plan": execution_plan, "state": state}, "log": log, "result": None, "subprocess": subprocess, "json": json, "__builtins__": __builtins__, "inference": self.inference, "embed": self.embed}
                exec(self.adapter.read(engine_h), scope, scope)
                result = scope.get("result")
                state = scope.get("context", {}).get("state", state)
            else:
                scope = {"context": request_envelope, "log": log, "result": None, "execution_plan": execution_plan, "state": state, "__builtins__": __builtins__, "inference": self.inference, "embed": self.embed}
                exec(payload, scope, scope)
                result = scope.get("result")
                state = scope.get("state", state)
            
            if result is None: raise ValueError("ABI Violation: No result assigned.")
            if state_id: self.adapter.put_state(state_id, state)
            status = "success"
            error = None
        except Exception as e:
            status = "failure"
            error = str(e)
            result = None

        # Telemetry
        telemetry = {"blob_hash": h, "request_envelope": request_envelope, "execution_plan": execution_plan, "status": status, "latency": time.perf_counter() - start_time, "logs": logs, "error": error, "timestamp": time.time()}
        self.adapter.write(json.dumps(telemetry))
        return {"result": result, "status": status}

def main():
    adapter = VaultAdapter()
    linker = Linker(adapter)
    
    if len(sys.argv) < 2:
        print("Usage: seed.py <command> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "put":
        payload = Path(sys.argv[2]).read_text() if os.path.exists(sys.argv[2]) else sys.argv[2]
        print(adapter.write(payload))
    elif cmd == "index":
        idx = adapter.index_get()
        idx[sys.argv[2]] = {"hash": sys.argv[2], "description": sys.argv[3], "vector": linker.embed(sys.argv[3])}
        adapter.index_put(idx)
        print(f"Indexed: {sys.argv[2]}")
    elif cmd == "sign":
        print(f"Signed {sys.argv[2]}: {linker.sign(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'local-node')}")
    elif cmd == "governance":
        jury_h = linker.resolve_capability("jury")
        if not jury_h: print("Error: No Jury capability"); sys.exit(1)
        # Simplified internal jury call for CLI
        scope = {"context": {"proposal_id": sys.argv[2]}, "log": lambda m: None, "result": None, "inference": linker.inference, "sign": linker.sign, "tally": linker.tally, "_raw_get": adapter.read, "json": json, "os": os, "__builtins__": __builtins__}
        exec(adapter.read(jury_h), scope, scope)
        print(json.dumps(scope.get("result"), indent=2))
    elif cmd == "tally":
        print(f"Signatures for {sys.argv[2]}: {linker.tally(sys.argv[2])}")
    elif cmd == "invoke":
        print(json.dumps(linker.invoke(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}), indent=2))
    elif cmd == "mcp":
        for line in sys.stdin:
            try:
                req = json.loads(line)
                m, p, rid = req.get("method"), req.get("params", {}), req.get("id")
                if m == "tools/list":
                    manifest = json.loads(adapter.read(adapter.get_manifest_hash()))
                    res = {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{"name": k, "versions": list(v.keys())} for k, v in manifest.get("capabilities", {}).items()]}}
                elif m == "tools/call":
                    res = {"jsonrpc": "2.0", "id": rid, "result": linker.invoke(p.get("name"), {"params": p.get("arguments", {}), "intent": "mcp_call"})}
                else: res = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}
                print(json.dumps(res), flush=True)
            except Exception as e: print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)
    elif cmd == "promote":
        prop_id = sys.argv[2]
        min_sigs = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        prop_path = adapter.proposals_dir / prop_id
        if not prop_path.exists():
            manifest = json.loads(Path(sys.argv[2]).read_text())
        else:
            if linker.tally(prop_id) < min_sigs:
                print(f"FAILED: Consensus not reached for {prop_id}"); sys.exit(1)
            manifest = json.loads(prop_path.read_text())
        for name, versions in manifest.get("capabilities", {}).items():
            for ver, h in versions.items(): adapter.read(h)
        h = adapter.write(json.dumps(manifest))
        adapter.update_manifest_hash(h)
        print(f"Successfully promoted: {h}")

if __name__ == "__main__": main()
