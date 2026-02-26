---
name: redmine
description: Interact with Redmine via MCP server. Query issues, projects, wiki pages, and manage tasks. Use when users ask about Redmine tickets, projects, or want to create/update issues.
---

# Redmine Skill

Connect to Redmine through the local MCP server at `/docker/redmine-mcp-server`.

## Configuration

Redmine MCP server is already running at `http://localhost:8000/mcp`.

**Connection Details:**
- MCP Endpoint: `http://localhost:8000/mcp`
- Health Check: `http://localhost:8000/health`
- Redmine URL: `http://redmine.fa-software.com`
- API Key: Stored in `/docker/redmine-mcp-server/.env.docker`

## Available Tools

The MCP server provides 14 tools. Call them via HTTP POST to `/mcp` endpoint.

### 1. list_redmine_projects
List all accessible projects.

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_redmine_projects","arguments":{}}}'
```

### 2. get_redmine_issue
Get a specific issue by ID.

**Parameters:**
- `issue_id` (required): Issue ID
- `include_journals` (optional): Include comments, default true
- `include_attachments` (optional): Include attachments, default true

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_redmine_issue","arguments":{"issue_id":123}}}'
```

### 3. list_my_redmine_issues
List issues assigned to current user.

**Parameters:**
- `filters.limit`: Max results (default 25)
- `filters.offset`: Pagination offset
- `filters.status_id`: Filter by status
- `filters.project_id`: Filter by project

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_my_redmine_issues","arguments":{"filters":{"limit":10}}}}'
```

### 4. search_redmine_issues
Search issues by query string.

**Parameters:**
- `query` (required): Search query
- `options.limit`: Max results
- `options.fields`: Fields to return
- `options.scope`: Search scope (all/my_project/subprojects)

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_redmine_issues","arguments":{"query":"bug","options":{"limit":10}}}}'
```

### 5. create_redmine_issue
Create a new issue.

**Parameters:**
- `project_id` (required): Project ID
- `subject` (required): Issue subject
- `description` (optional): Description
- `fields` (required): Additional fields (tracker_id, priority_id, etc.)

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"create_redmine_issue","arguments":{"project_id":1,"subject":"Bug report","fields":{}}}}'
```

### 6. update_redmine_issue
Update an existing issue.

**Parameters:**
- `issue_id` (required): Issue ID
- `fields` (required): Fields to update (subject, description, status_id, etc.)

**Usage:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"update_redmine_issue","arguments":{"issue_id":123,"fields":{"status_id":2}}}}'
```

### 7. get_redmine_wiki_page
Get wiki page content.

**Parameters:**
- `project_id` (required): Project ID or identifier
- `wiki_page_title` (required): Page title
- `version` (optional): Specific version
- `include_attachments` (optional): Include attachments

### 8. create_redmine_wiki_page
Create a new wiki page.

**Parameters:**
- `project_id` (required): Project ID
- `wiki_page_title` (required): Page title
- `text` (required): Page content
- `comments` (optional): Change comment

### 9. update_redmine_wiki_page
Update wiki page.

### 10. delete_redmine_wiki_page
Delete wiki page.

### 11. search_entire_redmine
Search across issues and wiki pages.

**Parameters:**
- `query` (required): Search query
- `resources`: Filter (issues/wiki_pages)
- `limit`: Max results
- `offset`: Pagination offset

### 12. summarize_project_status
Get project status summary.

**Parameters:**
- `project_id` (required): Project ID
- `days`: Lookback period (default 30)

### 13. get_redmine_attachment_download_url
Get download URL for attachment.

**Parameters:**
- `attachment_id` (required): Attachment ID

### 14. cleanup_attachment_files
Clean up expired attachments.

---

## Helper Script

Create a helper script for easier calls:

```bash
#!/bin/bash
# File: /docker/redmine-mcp-server/scripts/redmine-tool.sh

MCP_URL="http://localhost:8000/mcp"

call_tool() {
    local tool_name="$1"
    local args="$2"
    
    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"$tool_name\",\"arguments\":$args}}" | \
        grep "^data:" | sed 's/^data: //' | jq -r '.result.content[].text' | jq -r '.result // .error'
}

# Example usage:
# call_tool "list_redmine_projects" "{}"
# call_tool "get_redmine_issue" "{\"issue_id\":123}"
```

---

## Common Workflows

### Check my open issues
```bash
call_tool "list_my_redmine_issues" '{"filters":{"status_id":"open","limit":10}}'
```

### Search for bugs in a project
```bash
call_tool "search_redmine_issues" '{"query":"bug","options":{"limit":20}}'
```

### Create a new bug report
```bash
call_tool "create_redmine_issue" '{"project_id":1,"subject":"Login fails","description":"Cannot login with valid credentials","fields":{"tracker_id":1,"priority_id":2}}'
```

### Get project status
```bash
call_tool "summarize_project_status" '{"project_id":1,"days":7}'
```

---

## Error Handling

MCP server returns standard JSON-RPC responses:

**Success:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{"type": "text", "text": "..."}]
  }
}
```

**Error:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

---

## Notes

- MCP server must be running before calling tools
- Check health endpoint first: `curl http://localhost:8000/health`
- All responses are SSE (Server-Sent Events) format
- Parse `data:` prefix from response lines
- Results are JSON strings, may need double-parsing
