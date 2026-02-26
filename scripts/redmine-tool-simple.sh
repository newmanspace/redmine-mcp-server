#!/bin/bash
# Redmine MCP Tool Caller - Simple Version
# Usage: ./redmine-tool.sh <tool_name> [json_args]

MCP_URL="http://localhost:8000/mcp"

call_tool() {
    local tool_name="$1"
    local args="${2:-{}}"
    
    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool_name\",\"arguments\":$args}}" | \
        grep "^data:" | sed 's/^data: //'
}

# Main
if [ -z "${1:-}" ]; then
    echo "Usage: $0 <tool_name> [json_args]"
    echo "Example: $0 list_redmine_projects"
    exit 1
fi

call_tool "$1" "${2:-{}}"
