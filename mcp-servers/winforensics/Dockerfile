FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# System tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chainsaw (pre-compiled binary for fast Sigma-based EVTX hunting)
RUN CHAINSAW_VERSION=$(curl -s https://api.github.com/repos/WithSecureLabs/chainsaw/releases/latest | grep tag_name | cut -d'"' -f4) && \
    curl -L "https://github.com/WithSecureLabs/chainsaw/releases/download/${CHAINSAW_VERSION}/chainsaw_x86_64-unknown-linux-gnu.tar.gz" | tar xz -C /usr/local/bin || true

# Install uv (fast Python package manager — winforensics-mcp requires it)
RUN pip install --no-cache-dir uv

# Clone and install winforensics-mcp
RUN git clone https://github.com/x746b/winforensics-mcp /app/winforensics-mcp
WORKDIR /app/winforensics-mcp
RUN uv sync || (uv venv && uv pip install -e ".")
# Optional: WinRM support for remote collection
RUN uv pip install pywinrm 2>/dev/null || true

# Non-root user
RUN useradd -m -s /bin/bash investigator && \
    chown -R investigator:investigator /app
RUN mkdir -p /cases /evidence /reports && \
    chown -R investigator:investigator /cases /evidence /reports

USER investigator

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "print('ok')" || exit 1

CMD ["uv", "run", "python", "-m", "winforensics_mcp.server"]
