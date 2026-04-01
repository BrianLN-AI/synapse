# CAP-BARE-009: Market Arbitrage — Broker Marketplace
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** BRANCH-ONLY
**Branch:** bare/f_N

## Context

Commit 7967b74 (f_1 Phase 3) evolved the L3 broker from a simple priority policy into a marketplace with multiple named nodes. The broker selects an execution node based on cost/latency tradeoffs — "market arbitrage" in the commit narrative.

## What Was Built / Decided

L3 now maintains a `nodes` dict with per-node attributes:

```python
nodes = {
    'local':     {'latency': 100, 'cost': 1,  'trust': 1.0, 'runtime': 'python'},
    'gpu-local': {'latency': 50,  'cost': 10, 'trust': 0.9, 'runtime': 'python'},
    'beta-edge': {'latency': 10,  'cost': 50, 'trust': 0.8, 'runtime': 'python'}
}
```

Node selection:
- `priority == "high"`: select node with minimum latency (latency-optimized)
- otherwise: select node with minimum cost (cost-optimized)

The selected node is included in the `execution_plan`, and L4 uses it for routing. `seed.py` was also fixed to use `exec(l3_payload, l3_scope, l3_scope)` (same dict for globals and locals) to prevent variable scoping errors in the broker blob.

L4 gained a `remote_dispatch` method for simulated remote routing to non-local nodes.

## What It Enables

- Multi-dimensional execution selection: latency vs. cost vs. trust, extensible to any attribute
- The marketplace model makes policy transparent and auditable (node choice is in telemetry)
- Foundation for real node registries: replace the hardcoded `nodes` dict with a vault-resolved registry blob

## Why Not In council/f_N

The council tree implements its version of execution selection differently: the fitness function at promote-time scores blob versions (v1 vs. v2 blobs), not execution nodes. The council tree's selection operates over blob implementations, not over where/how to execute a given blob. These are orthogonal problems; both trees solve "what is optimal?" but answer different questions. [INFERRED — council/f_3 fitness function targets blob version selection, not node routing]

The bare tree's node marketplace is the stronger model for multi-node deployments. The council tree's fitness function is the stronger model for blob evolution. A complete fabric needs both.

## Evidence Basis

- Commit 7967b74 diff and l3_planning.py diff read directly [MEASURED]
- Node dict structure and selection logic confirmed [MEASURED]
- Council fitness function focus: inferred from council/f_3 structure and commit messages [INFERRED]
