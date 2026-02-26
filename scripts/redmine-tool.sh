#!/bin/bash
# Redmine MCP Tool Caller
# Usage: ./redmine-tool.sh <tool_name> [json_args]

set -e

MCP_URL="http://localhost:8000/mcp"
HEALTH_URL="http://localhost:8000/health"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if MCP server is running
check_health() {
    if ! curl -s "$HEALTH_URL" | grep -q '"status":"ok"'; then
        echo -e "${RED}Error: MCP server is not running or not healthy${NC}"
        echo "Check: $HEALTH_URL"
        exit 1
    fi
    echo -e "${GREEN}✓ MCP server is healthy${NC}"
}

# Call MCP tool
call_tool() {
    local tool_name="$1"
    local args="${2:-{}}"
    
    local response
    response=$(curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool_name\",\"arguments\":$args}}")
    
    # Parse SSE response
    local result
    result=$(echo "$response" | grep "^data:" | sed 's/^data: //' | jq -r '.result.content[].text // .error.message' 2>/dev/null)
    
    if [ -z "$result" ]; then
        # Try to extract error
        result=$(echo "$response" | grep "^data:" | sed 's/^data: //' | jq -r '.error.message // "Unknown error"' 2>/dev/null)
        echo -e "${RED}Error: $result${NC}"
        return 1
    fi
    
    echo "$result"
}

# List available tools
list_tools() {
    echo -e "${YELLOW}Available Redmine MCP Tools:${NC}"
    echo ""
    echo "  list_redmine_projects          - List all projects"
    echo "  get_redmine_issue              - Get issue by ID"
    echo "  list_my_redmine_issues         - List my assigned issues"
    echo "  search_redmine_issues          - Search issues"
    echo "  create_redmine_issue           - Create new issue"
    echo "  update_redmine_issue           - Update issue"
    echo "  get_redmine_wiki_page          - Get wiki page"
    echo "  create_redmine_wiki_page       - Create wiki page"
    echo "  update_redmine_wiki_page       - Update wiki page"
    echo "  delete_redmine_wiki_page       - Delete wiki page"
    echo "  search_entire_redmine          - Global search"
    echo "  summarize_project_status       - Project status summary"
    echo "  get_redmine_attachment_download_url - Get attachment URL"
    echo "  cleanup_attachment_files       - Cleanup expired attachments"
}

# Show usage
usage() {
    echo "Redmine MCP Tool Caller"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  health              - Check MCP server health"
    echo "  list                - List available tools"
    echo "  call <tool> [args]  - Call a tool with JSON args"
    echo ""
    echo "Examples:"
    echo "  $0 health"
    echo "  $0 list"
    echo "  $0 call list_redmine_projects"
    echo "  $0 call get_redmine_issue '{\"issue_id\":123}'"
    echo "  $0 call search_redmine_issues '{\"query\":\"bug\",\"options\":{\"limit\":10}}'"
    echo ""
}

# Main
case "${1:-}" in
    health)
        check_health
        ;;
    list)
        list_tools
        ;;
    call)
        if [ -z "${2:-}" ]; then
            echo -e "${RED}Error: Tool name required${NC}"
            usage
            exit 1
        fi
        check_health > /dev/null 2>&1
        call_tool "$2" "${3:-{}}"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        if [ -n "${1:-}" ]; then
            # Try to call tool directly
            check_health > /dev/null 2>&1
            call_tool "$1" "${2:-{}}"
        else
            usage
        fi
        ;;
esac
