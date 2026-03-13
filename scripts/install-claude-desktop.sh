#!/usr/bin/env bash
set -euo pipefail

# Auto-merge DFIReballz MCP config into Claude Desktop's config file.
# Creates a backup before modifying.

echo "DFIReballz — Claude Desktop MCP Installer"
echo ""

# Detect OS and set config path
if [[ "${OSTYPE:-linux}" == "darwin"* ]]; then
    CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "${OSTYPE:-linux}" == "msys" || "${OSTYPE:-linux}" == "cygwin" ]]; then
    CONFIG_PATH="${APPDATA}/Claude/claude_desktop_config.json"
else
    CONFIG_PATH="$HOME/.config/Claude/claude_desktop_config.json"
fi

echo "  Config file: ${CONFIG_PATH}"

# Ensure .mcp.json exists
if [ ! -f .mcp.json ]; then
    echo "  ERROR: .mcp.json not found. Run 'make configure-mcp MCP_HOST=claude-desktop' first."
    exit 1
fi

# Create config directory if it doesn't exist
CONFIG_DIR=$(dirname "$CONFIG_PATH")
mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_PATH" ]; then
    # Backup existing config
    cp "$CONFIG_PATH" "${CONFIG_PATH}.backup.$(date +%s)"
    echo "  Backup created: ${CONFIG_PATH}.backup.*"

    # Merge: add DFIReballz servers to existing config
    if command -v jq &>/dev/null; then
        jq -s '.[0] * {mcpServers: (.[0].mcpServers // {} | . * .[1].mcpServers)}' \
            "$CONFIG_PATH" .mcp.json > "${CONFIG_PATH}.tmp" && \
            mv "${CONFIG_PATH}.tmp" "$CONFIG_PATH"
        echo "  Merged DFIReballz MCP servers into existing config."
    else
        echo "  WARNING: jq not installed — cannot auto-merge."
        echo "  Manually copy the contents of .mcp.json into:"
        echo "    ${CONFIG_PATH}"
        exit 1
    fi
else
    # No existing config — copy directly
    cp .mcp.json "$CONFIG_PATH"
    echo "  Created new config with DFIReballz MCP servers."
fi

echo ""
echo "  Done! Restart Claude Desktop to load the MCP tools."
echo ""
