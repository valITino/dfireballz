FROM node:20-alpine

RUN npm install -g @modelcontextprotocol/server-filesystem

# Non-root user
RUN adduser -D -s /bin/sh investigator
RUN mkdir -p /cases /evidence /reports && \
    chown -R investigator:investigator /cases /evidence /reports

USER investigator

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD node -e "console.log('ok')" || exit 1

CMD ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/cases", "/evidence", "/reports"]
