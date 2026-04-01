# Bare f_N Walk — Summary
**Date:** 2026-04-01
**Extracted by:** ADR agent (bare walk pass)
**Branch walked:** bare f_N lineage (commits 739a228 → 1b2db18)
**Stubs produced:** 17 CAPs + 1 LESSON

---

## What Was Walked

19 commits across genesis, f_0 stabilization, f_1, f_2, and f_3 phases. The bare tree is an expansionist lineage: each phase adds capabilities without a fitness gate. It diverged from the council tree at genesis (same BIOS/ABI seed) and grew in a different direction — runtime brokering, MCP integration, polyglot execution, persistent memory, and P2P collective state.

---

## Cherry-Pick Candidates

These are flagged for Brian's review. Do not adopt without reviewing the "Known limitations" in each stub.

| ID | Title | Why |
|----|-------|-----|
| **CAP-BARE-007** | Multi-Vault Discovery | Clean tiered resolution interface; council tree needs this as it scales. Design is sound and council-compatible. |
| **CAP-BARE-010** | Interface Evolution (trace_id) | Low-cost improvement: `trace_id` generation and protocol versioning at entry. Adds distributed tracing to council telemetry. No architectural disruption. |
| **CAP-BARE-013** | MCP Integration | The strongest candidate. Fabric speaks MCP: LLMs can invoke blobs as tools via JSON-RPC stdio. Council tree will need an external interface. Four known limitations to fix (tool descriptions, hash/name ambiguity, MCP error spec conformance, no auth). |
| **CAP-BARE-014** | Persistent Memory | Opt-in stateful blobs via content-addressed state pointers. Compatible with council's pure-function design (state is only injected if `state_id` provided). Enables blob agents. |

---

## Branch-Only (Do Not Adopt)

These represent genuine design forks or incomplete implementations. Understand them; do not cherry-pick.

| ID | Title | Reason |
|----|-------|--------|
| CAP-BARE-001 | BIOS/ABI Seed | Council absorbed this at genesis. No delta. |
| CAP-BARE-002 | Promote/Manifest | Conceptually absorbed; council tree evolved promote into a fitness-gated cycle. |
| CAP-BARE-003 | Recursive Leap | Council absorbed this at genesis (d5b06b5). Council added bytecode cache; bare tree did not. |
| CAP-BARE-004 | Broker Leap | Design fork: bare tree brokers at invocation time; council tree gates at promote time. Both are valid. Do not conflate. |
| CAP-BARE-005 | Interface Leap (L1 proxy) | No equivalent in council. Relevant if council needs heterogeneous caller support (MCP, REST, gRPC). Not needed today. |
| CAP-BARE-006 | Binding Leap (delegated exec) | Council chose direct exec with bytecode cache. Bare tree chose delegated exec for extensibility. Council's choice is correct for its use case. |
| CAP-BARE-008 | Polyglot Runtimes | Unsandboxed subprocess execution. Security risk. Council stayed Python-only correctly. |
| CAP-BARE-009 | Market Arbitrage | Per-invocation node routing. Valid for multi-node deployments; not needed for council's single-node design. |
| CAP-BARE-011 | Self-Correction (retries) | Council answers this differently: select a better blob at promote-time. Bare tree retries the same blob. Both valid; different problems. |
| CAP-BARE-012 | Performance Feedback | Council does this better (p95, burstiness, dynamic tolerance in council/f_3). Bare tree's 5x/10x penalty multiplier is cruder. |
| CAP-BARE-015 | P2P Discovery | Capability registry refactor (`_resolve_capability()`) is good; the P2P collective vault is a simulation. |
| CAP-BARE-016 | Federated Arbitrage | `federated_invoke` returns a hardcoded string. Not a real implementation. |
| CAP-BARE-017 | Location-Transparent State | `collective_vault` is a local directory. No network layer. Design is correct; implementation is simulation-only. |

---

## The Central Lesson

**LESSON-001** documents the structural reason the bare tree stopped at f_3: expansion without selection. The tree added 17 capabilities in one day with no fitness gate between capability addition and manifest promotion. By f_3, two of the four "collective" capabilities were simulations that looked like implementations. There was no mechanism to detect this.

The council tree reached f_7 because every generation must beat the previous on a measurable fitness criterion. The bare tree never implemented this discipline.

**Before adopting any bare tree capability into the council tree:** define the fitness criterion first. Build second. Gate promotion on the criterion.

---

## Relationship Between the Trees

```
genesis (739a228)
    ↓ shared BIOS/ABI/recursive-leap/promote
    ↓
council/f_0 ── fitness gate added ──→ council/f_7 (current, Design-by-Contract)
    |
bare/f_0 ── no fitness gate ──→ f_1 → f_2 (MCP, state, plasticity) → f_3 (P2P sim) → STOPPED
```

The bare tree is not a failed experiment. It explored design space that the council tree has not entered: MCP integration, polyglot runtimes, per-invocation brokering, distributed state. These are valuable designs. They lack selection pressure. Adding selection pressure is the work needed to bring them forward.

---

## Files Produced

| File | ID |
|------|----|
| `CAP-BARE-001-bios-abi-seed.md` | CAP-BARE-001 |
| `CAP-BARE-002-promote-manifest.md` | CAP-BARE-002 |
| `CAP-BARE-003-recursive-leap.md` | CAP-BARE-003 |
| `CAP-BARE-004-broker-leap.md` | CAP-BARE-004 |
| `CAP-BARE-005-interface-leap.md` | CAP-BARE-005 |
| `CAP-BARE-006-binding-leap.md` | CAP-BARE-006 |
| `CAP-BARE-007-multi-vault-discovery.md` | CAP-BARE-007 |
| `CAP-BARE-008-polyglot-runtimes.md` | CAP-BARE-008 |
| `CAP-BARE-009-market-arbitrage.md` | CAP-BARE-009 |
| `CAP-BARE-010-interface-evolution.md` | CAP-BARE-010 |
| `CAP-BARE-011-self-correction.md` | CAP-BARE-011 |
| `CAP-BARE-012-performance-feedback.md` | CAP-BARE-012 |
| `CAP-BARE-013-mcp-integration.md` | CAP-BARE-013 |
| `CAP-BARE-014-persistent-memory.md` | CAP-BARE-014 |
| `CAP-BARE-015-p2p-discovery.md` | CAP-BARE-015 |
| `CAP-BARE-016-federated-arbitrage.md` | CAP-BARE-016 |
| `CAP-BARE-017-location-transparent-state.md` | CAP-BARE-017 |
| `LESSON-001-expansion-without-selection.md` | LESSON-001 |
