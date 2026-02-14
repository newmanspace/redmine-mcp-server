#!/bin/bash
set -e

# Patch MCP library DNS rebinding protection if configured
if [ "${DISABLE_DNS_REBINDING_PROTECTION}" = "true" ]; then
    MCP_SERVER_PY=$(python -c "import mcp.server.fastmcp.server as m; print(m.__file__)")
    if [ -f "$MCP_SERVER_PY" ]; then
        sed -i "s/enable_dns_rebinding_protection=True/enable_dns_rebinding_protection=False/g" "$MCP_SERVER_PY"
        echo "[entrypoint] Patched MCP library: DNS rebinding protection disabled"
    else
        echo "[entrypoint] WARNING: Could not find mcp server.py to patch"
    fi
fi

# Execute the original command
exec "$@"
