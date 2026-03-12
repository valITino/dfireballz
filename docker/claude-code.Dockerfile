# Claude Code MCP Client — runs inside the dfireballz Docker network.
# Usage:
#   docker compose --profile claude-code run --rm claude-code
#
# Connects to each MCP server via stdio (docker exec -i) on the shared
# Docker socket.  No HTTP ports exposed.  No host-side Claude install needed.

FROM node:22-slim

# Suppress npm update notices and reduce noise
ENV NODE_ENV=production \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    npm_config_loglevel=error

# Install Claude Code CLI and clean npm cache
RUN npm install -g @anthropic-ai/claude-code@2.1.71 \
    && npm cache clean --force

# Runtime utilities: curl for health checks, jq for JSON, docker-cli
# for "docker exec -i" stdio transport to sibling MCP containers.
# tini for proper PID 1 signal handling (SIGTERM/SIGINT propagation).
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        jq \
        tini \
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

# Harden: strip SUID/SGID bits and remove recon tools (tintinweb pattern).
# Prevents privilege escalation via setuid binaries and limits recon
# capability if the container is compromised.
RUN find / -xdev -perm -4000 -type f -exec chmod u-s {} \; 2>/dev/null || true && \
    find / -xdev -perm -2000 -type f -exec chmod g-s {} \; 2>/dev/null || true && \
    rm -f /usr/bin/nc /usr/bin/netcat /bin/netstat /usr/bin/ss 2>/dev/null || true

# Non-root user for Claude Code process.
# Docker socket access is granted via group_add in docker-compose.yml.
RUN useradd -m -s /bin/bash -u 1001 claude && \
    mkdir -p /workspace && \
    chown -R claude:claude /workspace

WORKDIR /workspace

# Pre-configure MCP servers — stdio transport via docker exec -i.
# Claude Code auto-discovers .mcp.json in the working directory.
COPY --chown=claude:claude docker/mcp.json /workspace/.mcp.json

# Entrypoint: verify all MCP containers are healthy, then launch Claude.
COPY docker/claude-code-entrypoint.sh /usr/local/bin/claude-code-entrypoint.sh
RUN chmod +x /usr/local/bin/claude-code-entrypoint.sh

USER claude

# Use tini as PID 1 for proper signal forwarding to Claude Code process.
# Without this, SIGTERM from `docker stop` may not reach the claude CLI,
# causing a 10s timeout before SIGKILL on every container shutdown.
ENTRYPOINT ["tini", "--", "/usr/local/bin/claude-code-entrypoint.sh"]
