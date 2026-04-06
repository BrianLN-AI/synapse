# ADR-021: Multi-Runtime Logic Dispatch Pattern

## Status
[PROPOSED]

## Context
The current Synapse Fabric kernel uses `new Function()` for `logic/javascript` execution. While sufficient for simple scripting, this approach:
1. Is tied to JavaScript runtimes (Node.js/Bun).
2. Lacks strong security/isolation (uses soft sandboxing).
3. Limits performance for compute-intensive tasks (e.g., data science, ML).

To evolve into a truly modular D-JIT Fabric, we require a **multi-runtime dispatch system** capable of executing arbitrary compute (WASM, Python via Pyodide, Native Libs) securely.

## Decision
We will evolve the kernel to implement a **Runtime Dispatcher pattern** based on the WIT (WebAssembly Interface Types) standard:
1. Define a platform-agnostic `synapse.wit` ABI contract.
2. Abstract the kernel execution engine to dispatch logic based on the `type` field in `LogicBlob`:
   - `logic/javascript`: Standard `new Function` or `vm` module.
   - `logic/wasm`: `wasmtime` / `wazero` / native WebAssembly runtime.
   - `logic/python`: `pyodide` / CPython runtime host.
3. Use a **Message-Passing ABI** (instead of direct JS object injection) to facilitate communication between host and guest.

## Consequences
- **Pros**:
  - Language-agnostic verb development (Rust, Python, C++, JS).
  - Stronger security boundaries (WASM/Worker threads).
  - Platform portability (CLI, Browser, Server).
- **Cons**:
  - Increased complexity in kernel dispatching logic.
  - Startup overhead for Wasm/Pyodide runtimes (requiring warm-pool strategies).
  - Necessity of a cross-runtime serialization layer (WIT-based).

## Trigger for Adoption
This pattern will be adopted when we require either:
1. Complex data analysis (e.g., Pandas/NumPy integration).
2. High-performance, memory-safe execution (e.g., C/Rust primitives).
3. Client-side execution in a browser environment (Web Workers/WASM).

[CHERRY-PICK CANDIDATE]
