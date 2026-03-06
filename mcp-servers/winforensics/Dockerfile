FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# System tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Chainsaw (pre-compiled binary for fast Sigma-based EVTX hunting)
RUN CHAINSAW_VERSION=$(curl -s https://api.github.com/repos/WithSecureLabs/chainsaw/releases/latest | grep tag_name | cut -d'"' -f4) && \
    curl -L "https://github.com/WithSecureLabs/chainsaw/releases/download/${CHAINSAW_VERSION}/chainsaw_x86_64-unknown-linux-gnu.tar.gz" | tar xz -C /usr/local/bin || true

# Install uv (fast Python package manager — winforensics-mcp requires it)
RUN pip install --no-cache-dir uv

# Clone and install winforensics-mcp
RUN git clone https://github.com/x746b/winforensics-mcp /app/winforensics-mcp
WORKDIR /app/winforensics-mcp
# uv sync fails on libscca-python/libesedb-python (C extensions needing autotools).
# These are runtime-optional (try/except ImportError in parsers), so install without them.
RUN uv venv && \
    uv pip install -e "." --no-deps && \
    uv pip install mcp python-evtx python-registry python-dateutil pefile mft pylnk3 && \
    uv pip install libscca-python libesedb-python --only-binary=:all: 2>/dev/null || true
# Optional: WinRM support for remote collection
RUN uv pip install pywinrm 2>/dev/null || true

# Non-root user
RUN useradd -m -s /bin/bash investigator && \
    chown -R investigator:investigator /app
RUN mkdir -p /cases /evidence /reports && \
    chown -R investigator:investigator /cases /evidence /reports

USER investigator

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /app/winforensics-mcp/.venv/bin/python -c "import winforensics_mcp; print('ok')" || exit 1

# Ensure no inherited ENTRYPOINT interferes with CMD
ENTRYPOINT []

# Use venv python directly — uv run would re-sync against pyproject.toml
# and fail on libscca-python/libesedb-python C extensions
CMD ["/app/winforensics-mcp/.venv/bin/python", "-m", "winforensics_mcp.server"]
