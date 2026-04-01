# CAP-BARE-013: MCP Integration — The Fabric as a Model Context Protocol Server
**Date:** 2026-04-01
**Status:** Proposed
**Flag:** CHERRY-PICK CANDIDATE
**Branch:** bare/f_N

## Context

Commit 8eeb76c (f_2 Phase 3) is the most architecturally significant commit in the bare tree that has no equivalent in the council tree. It transformed the D-JIT fabric into a JSON-RPC Model Context Protocol (MCP) server. An LLM (or any MCP client) can now invoke fabric blobs as tools, without knowing that the fabric exists.

MCP is the standard protocol by which AI assistants (Claude, etc.) interact with external tools. Making the fabric an MCP server means every blob in the vault is automatically discoverable and invocable by any MCP-capable AI agent.

## What Was Built / Decided

`seed.py` gained a new `mcp` command that runs a JSON-RPC stdio loop:

```python
for line in sys.stdin:
    request = json.loads(line)
    method = request.get("method")
    ...
```

Two MCP methods implemented:

**`tools/list`**: reads `manifest.hash`, resolves the manifest, returns all registered capability layers as tools:

```json
{
  "tools": [
    {"name": "proxy", "hash": "7f8768f..."},
    {"name": "librarian", "hash": "c14bdf..."},
    {"name": "broker", "hash": "5d42b2..."},
    {"name": "engine", "hash": "a534a3..."}
  ]
}
```

**`tools/call`**: takes `{"name": "<hash_or_layer_name>", "arguments": {...}}`, calls `invoke()`, returns result:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"result": ..., "telemetry_hash": "...", "status": "success"}
}
```

L1 (interface) was updated to detect `intent == "mcp_call"` and apply MCP-specific normalization, tagging the envelope with `origin: "seed_mcp_proxy"`.

The README added at this commit documents the complete fabric philosophy and the MCP integration as a first-class capability.

This commit also transitioned the manifest from `layers` (named l1/l2/l3/l4) to `capabilities` (named proxy/librarian/broker/engine) — a semantic rename that makes the manifest self-describing for external consumers.

## What It Enables

- **LLM-native blob invocation**: any Claude session with MCP configured can call fabric blobs as tools, with full telemetry and the four-layer execution stack
- **Zero integration cost**: blobs do not need to be modified to become MCP tools — promotion to the manifest makes them discoverable
- **Bidirectional AI integration**: the fabric can call AI models (via blobs), and AI models can call the fabric (via MCP) — completing a loop
- **Protocol neutrality**: the MCP server is just one entry point; `invoke()` and `promote` still work directly. The fabric is not MCP-dependent
- **Tool registry from manifest**: `tools/list` returns the live manifest — the tool registry is self-maintaining as capabilities are promoted

## Why Not In council/f_N

The council tree has no MCP server. The council tree is focused on blob fitness evaluation and self-modification — it operates as a standalone computation substrate, not as an externally-accessible service. [MEASURED — no `mcp` command, no JSON-RPC loop in council/f_7 or any council commit message]

This is the strongest cherry-pick candidate in the entire bare tree. The council tree will eventually need an external interface for AI agent integration. MCP is the canonical standard for this as of April 2026. The bare tree's implementation is minimal but architecturally sound:

- `tools/list` driven by the manifest means the tool registry is automatic
- `tools/call` routes through the full four-layer stack — MCP callers get telemetry, retry, and planning for free
- The stdio transport is correct for Claude Code MCP integration

**Known limitations to fix before cherry-pick:**
1. `tools/call` accepts hash OR layer name as `name` — the ambiguity needs resolution (hash-only is safer for content-addressed systems)
2. No schema/description per tool — MCP `tools/list` should return tool descriptions for LLM planning
3. Error responses do not conform to full MCP spec (missing `isError` field in `tools/call` results)
4. No authentication or rate limiting on the stdio interface

## Evidence Basis

- Commit 8eeb76c diff read in full [MEASURED]
- MCP stdio loop implementation confirmed [MEASURED]
- `tools/list` and `tools/call` methods confirmed [MEASURED]
- Manifest `capabilities` rename confirmed [MEASURED]
- Council tree absence of MCP: confirmed across all council commit messages and branch list [MEASURED]
- MCP as canonical standard: this is a VOLATILE claim; MCP was introduced by Anthropic in late 2024 [CITED — based on training knowledge; verify current spec at modelcontextprotocol.io]
