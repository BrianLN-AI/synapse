# Synapse: The D-JIT Logic Fabric

**Status:** `f_2` (Agentic Mesh)  
**Latest Baseline:** [f_1 (1.1.0-Stable)](https://github.com/BrianLN-AI/synapse/tree/f_1)  
**Foundation:** Content-Addressed, Protocol-Oriented Compute Mesh

---

## 🧠 The "Why": Philosophy of the Cleft

Traditional computing is obsessed with **Nodes** (servers, functions, containers). **Synapse** shift the focus to the **Gaps**—the space between nodes where logic is negotiated, brokered, and bound. 

We call this the **Synaptic Cleft**. In this fabric, code is not a static file; it is a [Wavefunction](https://en.wikipedia.org/wiki/Wave_function) of potentiality that only "collapses" into a result at the moment of invocation.

### Core Metaphors
*   **The Synapse (Neurobiology):** The site of transmission. Intelligence emerges from the weight and plasticity of the connection, not the storage of the data.
*   **The Mycelium (Mycology):** A persistent, underground [Substrate](https://en.wikipedia.org/wiki/Substrate_(mycology)) (`blob_vault`) that feeds the entire system.
*   **The Rhizome (Philosophy):** A non-hierarchical system (from [Deleuze & Guattari](https://en.wikipedia.org/wiki/Rhizome_(philosophy))) where any point can connect to any other point.

---

## 📖 Lexicon & Definitions

*   **D-JIT (Distributed Just-In-Time):** A runtime that resolves, plans, and executes logic across a distributed mesh exactly when needed.
*   **Blob:** An immutable, content-addressed unit of logic or data. Identified by its [SHA-256](https://en.wikipedia.org/wiki/SHA-2) hash.
*   **ABI (Application Binary Interface):** The strict contract for Blobs. In Synapse, every blob *must* assign its output to a `result` variable and use the provided `log()` sink.
*   **GOKR (Goals, Objectives, and Key Results):** Our framework for architectural success.
*   **BIOS (Basic Input/Output System):** The hardcoded fallback mechanism that allows the Linker to "Cold Boot" (start from scratch) without infinite recursion.
*   **The Linker:** The brain of the system. It coordinates the 4-layer stack to transform a Hash into a Result.

---

## 🚀 The Evolutionary Journey

### [f_0: The Wavefunction Collapse](https://github.com/BrianLN-AI/synapse/tree/af6b1e02)
**Goal:** Establish the baseline "Seed" and the 4-Layer Stack.
*   **The Leap:** Transitioned from "Unknown" potential to a functional Python Linker.
*   **Key Achievement:** Implemented the **Recursive Leap**, where the Linker uses the fabric to find the layers (Interface, Discovery, Planning, Binding) it needs to execute the fabric.
*   **Tag:** `f_0` ([af6b1e02](https://github.com/BrianLN-AI/synapse/commit/af6b1e02))

### [f_1: The Distributed Leap](https://github.com/BrianLN-AI/synapse/tree/1e4dadbd)
**Goal:** Expand the fabric beyond a single local vault.
*   **Distributed Discovery:** L2 can now resolve hashes across multiple "Vault Tiers" (Local vs. Remote).
*   **Polyglot Runtime:** L4 evolved to support both **Python** (`exec`) and **JavaScript** ([Node.js](https://nodejs.org/)).
*   **Market Arbitrage:** L3 began acting as a **Broker**, choosing nodes based on Cost vs. Latency.
*   **Tag:** `f_1` ([1e4dadbd](https://github.com/BrianLN-AI/synapse/commit/1e4dadbd))

### [f_2: The Agentic Mesh](https://github.com/BrianLN-AI/synapse/tree/f_2) (Current)
**Goal:** Enable self-reflection and autonomous optimization.
*   **Self-Correction:** L4 now implements **Autonomous Retries** with exponential backoff.
*   **Dynamic Plasticity:** L3 now "learns." It scans telemetry artifacts to autonomously penalize failing nodes and reinforce successful links.
*   **Current Hash:** [ec8a2898](https://github.com/BrianLN-AI/synapse/commit/ec8a2898)

---

## 🛠 Architectural Blueprint: The 4-Layer Stack

| Layer | Name | Responsibility |
| :--- | :--- | :--- |
| **L1** | **Interface** | The Proxy. Normalizes intent, validates requests, and tags with `trace_id`. |
| **L2** | **Discovery** | The Librarian. Resolves Content-Hashes across the Mycelial Substrate (Vault Tiers). |
| **L3** | **Planning** | The Broker. Performs Market Arbitrage. Selects the Node/Runtime based on the Fitness Function. |
| **L4** | **Binding** | The Engine. Physically injects the Blob into a scrubbed sandbox and handles retries. |

---

## 🛤 The Road to f_3 (Collective Intelligence)

1.  **Formal Protocol (MCP):** Integrating the [Model Context Protocol](https://modelcontextprotocol.io/) to let external LLMs call Synapse tools.
2.  **Persistent Memory:** Enabling Blobs to store state between invocations.
3.  **Global Fabric:** Bridging independent Synapse instances into a P2P compute mesh.

---
*Logic exists in the Intermezzo—the space-between movement.*
