# CAP-BARE-016: Federated Arbitrage — Cross-Fabric Execution Routing
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit 8c9f54a (f_3 Phase 2) extended the broker marketplace with "federated" nodes — Synapse instances on other machines. The broker can now route execution to remote fabric peers, not just local nodes. L4 handles federated invocations via a "Cross-Fabric Handshake" bridge.

## What Was Built / Decided

Node marketplace extended with `type` attribute:

```python
nodes = {
    'local':      {'latency': 100, 'cost': 1,  'trust': 1.0, 'type': 'internal',  ...},
    'node-gamma': {'latency': 20,  'cost': 10, 'trust': 0.95,'type': 'federated', ...},
    'node-delta': {'latency': 5,   'cost': 50, 'trust': 0.9, 'type': 'federated', ...}
}
```

L3 now selects `method: "federated_invoke"` for federated nodes instead of `"local_exec"`.

L4 branches on `method`:
- `federated_invoke`: logs "Cross-Fabric Handshake", simulates remote execution result
- `local_exec`: existing Python/JavaScript execution paths

Plasticity penalty increased from 5x to 10x for failing federated nodes — the broker is more aggressive about routing away from unreliable peers.

Commit narrative: "Federated bridging allows the fabric to scale horizontally. No single node needs to be the bottleneck; logic moves to where the latency is lowest."

## What It Enables

- Horizontal scale: high-priority requests automatically route to the lowest-latency federated peer
- Topology abstraction: callers do not know whether execution happened locally or on a peer node
- Federated plasticity: failures on peer nodes are penalized in the same feedback loop as local node failures

## Why Not In council/f_N

The council tree is single-node and has no federated execution concept. [MEASURED — no federated nodes, no cross-fabric invocation in any council branch]

**Critical weakness in this implementation**: the `federated_invoke` path is entirely simulated — L4 returns a hardcoded string `"Collective success: Executed on federated node {node}."` with no actual network call. This is a scaffolding placeholder, not a working implementation. [MEASURED — confirmed in l4_binding.py diff]

This is a key reason the bare tree did not advance past f_3: the federated capability was sketched but not implemented. No actual transport mechanism (HTTP, gRPC, another Synapse instance) exists. The plasticity loop penalizes simulated failures on nodes that never actually run code.

## Evidence Basis

- Commit 8c9f54a diff, l3_planning.py and l4_binding.py diffs read directly [MEASURED]
- Federated node types and arbitrage logic confirmed [MEASURED]
- `federated_invoke` implementation as simulation confirmed [MEASURED]
- 10x penalty increase confirmed [MEASURED]
- Council absence of federated nodes confirmed [MEASURED]
