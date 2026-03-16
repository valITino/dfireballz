FROM node:20-alpine

RUN npm install -g @modelcontextprotocol/server-filesystem

# Create mount-point directories (ownership set via bind mounts at runtime)
RUN mkdir -p /cases /evidence /reports /output

# Run as 'node' user (UID 1000 — matches most host users for bind mounts)
# The MCP server itself enforces directory scoping; no additional OS-level restriction needed
USER node

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD node -e "console.log('ok')" || exit 1

ENTRYPOINT []
CMD ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/cases", "/evidence", "/reports", "/output"]
