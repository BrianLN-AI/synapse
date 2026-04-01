# Synapse: The D-JIT Logic Fabric

**Status:** `f_2` (Agentic Mesh - Phase 2)  
**Version:** 1.2.0-Beta  
**Foundation:** Content-Addressed, Protocol-Oriented Compute Mesh

## 🧠 The Vision
Synapse is a multidisciplinary compute fabric that treats code, data, and inference as immutable **Blobs**. Inspired by neurobiology (Synapses), mycology (Mycelial Substrates), and philosophy (Rhizomatic Intermezzos), the fabric's intelligence resides not in its nodes, but in the **Gaps** (The Linker) between them.

## 🚀 The Journey So Far

### `f_0`: The Wavefunction Collapse (The Foundation)
The system began as `f(undefined)`, a field of potentiality. We collapsed it into a stable **Seed Linker** capable of a "Cold Boot" via a BIOS fallback.
- **Strict ABI:** Every blob must assign its return value to a `result` variable.
- **The 4-Layer Stack:** Interface (L1), Discovery (L2), Planning (L3), and Binding (L4).
- **Recursive Leap:** The Linker uses the fabric to find and execute the fabric itself.

### `f_1`: The Distributed Leap (The Substrate)
We evolved the local seed into a distributed system.
- **Multi-Vault Discovery:** Hashes now resolve across local and remote tiers.
- **Polyglot Engine:** Support for both Python (`exec`) and JavaScript (`node -e`) runtimes.
- **Market Arbitrage:** The L3 Broker performs cost vs. latency trade-offs to select the optimal execution node.

### `f_2`: The Agentic Mesh (The Living Fabric) - *Current*
The fabric is becoming "alive" through self-reflection.
- **Self-Correction:** Autonomous retry loops with exponential backoff in L4.
- **Dynamic Plasticity:** The L3 Broker now "learns" from telemetry. It autonomously penalizes slow or failing nodes by increasing their latency weight in real-time.

## 🛠 How It Works

1. **PUT**: Store logic in the content-addressed `blob_vault`.
   ```bash
   python3 seed.py put logic.py # Returns SHA-256 Hash
   ```
2. **INVOKE**: The Linker negotiates the execution of a hash.
   ```bash
   python3 seed.py invoke <hash> '{"params": {"priority": "high"}}'
   ```
3. **TELEMETRY**: Every invocation generates a content-addressed artifact documenting the request envelope, execution plan, logs, and performance metrics.

## 🛤 What's Next?

- **`f_2` Phase 3: Formal Protocol**: Implementing an **MCP (Model Context Protocol)** server to expose the fabric's blobs as tools for external LLMs.
- **`f_2` Phase 4: Memory**: Enabling persistent state blobs that allow logic to "remember" between invocations.
- **`f_3`: Collective Intelligence**: Bridging multiple Synapse fabrics into a global, peer-to-peer compute substrate.

---
*The fabric moves in the Intermezzo—the space between.*
