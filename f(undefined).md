# f(undefined): D-JIT Logic Fabric Genesis Specification
**Version:** 1.3.0
**Status:** Logical Architecture & Execution Protocol

## 1. Executive Summary
The **D-JIT (Distributed Just-In-Time) Logic Fabric** is a content-addressed, protocol-oriented compute mesh. It treats code, data, and inference as immutable **Blobs**. The system's intelligence resides in the **Linker**, which negotiates execution (Embed vs. Remote) at the moment of invocation.

## 2. Goals & Objectives (GOKR)
* **Goal:** A self-correcting, location-transparent logic fabric with a strict ABI.
* **Objective:** Eliminate "Silent Failures" through mandatory scope-based I/O and telemetry.
* **Key Result:** A "Seed" implementation capable of a "Cold Boot" using a BIOS Fallback to prevent infinite recursion.

## 3. Logical Architecture: The 4-Layer Stack
1. **Interface (The Proxy):** Captures intent and translates it into a Protocol Contract.
2. **Discovery (The Librarian):** Resolves Content-Hashes (**blake3**, 32 bytes) across vault tiers.
3. **Planning (The Broker):** Performs "Market Arbitrage" (Latency vs. Cost vs. Trust).
4. **Binding (The Engine):** Physically injects the Blob into a scrubbed sandbox.

## 4. The Execution Contract (The ABI)
To ensure deterministic execution, all Blobs must adhere to the **Scope-Exchange Protocol**:
* **Inputs:** The Linker injects a `context` object (data) and a `log(msg)` function (telemetry sink).
* **Outputs:** Blobs **must** assign their final return value to a `result` variable in the local scope. Raw `return` statements are prohibited.
* **Isolation:** Blobs are executed in a "Scrubbed Scope." They cannot see Linker internal variables (e.g., `VAULT_DIR`) unless explicitly passed.

## 5. The Bootstrap Protocol (The BIOS)
To prevent infinite recursion (where Discovery needs Discovery to find Discovery):
* **The BIOS Fallback:** The Seed Linker MUST implement a private `_raw_get(h)` method.
* **The Root Pointer:** This method bypasses Blob-based Discovery to resolve the initial System Manifest directly from the filesystem.

## 6. Seed Functional Requirements
Implement a **Seed CLI/MCP Server** in Python (`seed.py`):
1. **PUT**: Accept Type/Payload -> blake3 hash -> Store in `./blob_vault/`.
2. **INVOKE**: Load Hash -> Bind (exec/eval) -> **Verify `result` exists** -> Return.
3. **TELEMETRY**: Measure latency/memory and `PUT` a 'telemetry/artifact' blob for every run, including any `log()` data.

## 7. The ZK Verification Layer (The Witnessing)
Blobs may carry zero-knowledge proofs that certify computation without revealing private inputs.
See `ZK_PROTOCOL.md` for the full threat model, circuit inventory, and trust assumptions.

Core principle: **a blob can prove it was executed honestly, not merely that it ran.**

* **Content Binding:** The prover must possess the actual blob bytes. `blake3(blob_content) == blob_hash` is provable in-circuit. A prover cannot claim blob X ran when blob Y ran.
* **Fitness Integrity:** The fitness formula `f = (SuccessRate * Integrity) / (Latency * Cost)` is provable as a ZK circuit. A promoter cannot inflate a candidate's score.
* **Proof artifacts** are first-class: they are hashed and stored in the vault alongside the blobs they certify.
* **Promotion gate (future):** A promoted blob may require a valid proof artifact before the manifest is updated.

The canonical hash function for all content-addressing, ZK circuits, and proof artifacts is **blake3**. No other hash function is permitted in new code.
