#!/bin/bash
# Start the MCP server for Synapse D-JIT Fabric
# Usage: ./run_mcp.sh [command]
#
# Commands:
#   tools/list - List available verbs
#   tools/call - Call a verb with arguments
#   pipe      - Start stdio server mode

case "$1" in
  tools/list)
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | bun run explore/functional/mcp_server.ts
    ;;
  tools|call)
    NAME="${2:-ping}"
    ARGS="${3:-{}}"
    echo "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$NAME\",\"arguments\":$ARGS}}" | bun run explore/functional/mcp_server.ts
    ;;
  pipe|"")
    bun run explore/functional/mcp_server.ts
    ;;
  *)
    echo "Usage: $0 [tools/list|tools|call|pipe]"
    echo ""
    echo "Examples:"
    echo "  $0 tools/list                        # List available verbs"
    echo "  $0 tools call ping '{}'             # Call ping verb"
    echo "  $0 pipe                              # Start stdio server"
    ;;
esac