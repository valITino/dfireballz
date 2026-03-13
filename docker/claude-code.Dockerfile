# Claude Code MCP Client — runs inside the dfireballz Docker network.
# Usage:
#   docker compose --profile claude-code run --rm claude-code
#
# Connects to each MCP server via stdio (docker exec -i) on the shared
# Docker socket.  No HTTP ports exposed.  No host-side Claude install needed.

FROM node:22-slim

RUN npm install -g @anthropic-ai/claude-code

# Install curl for health checks, jq for JSON processing,
# docker-cli for "docker exec -i" stdio transport to sibling MCP containers,
# and dnsutils for DNS resolution debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    unzip \
    python3 \
    dnsutils \
    ca-certificates \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian bookworm stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Startup script: copy and make executable while still root.
COPY docker/claude-code-entrypoint.sh /usr/local/bin/claude-code-entrypoint.sh
RUN chmod +x /usr/local/bin/claude-code-entrypoint.sh

# Non-root user (matches node:22-slim's built-in 'node' user)
RUN mkdir -p /workspace /home/node/.claude \
    && chown -R node:node /workspace /home/node/.claude

USER node
WORKDIR /workspace

# Pre-configure MCP servers — stdio transport via docker exec -i.
# Claude Code auto-discovers .mcp.json in the working directory.
COPY --chown=node:node docker/mcp.json /workspace/.mcp.json

ENTRYPOINT ["/usr/local/bin/claude-code-entrypoint.sh"]
