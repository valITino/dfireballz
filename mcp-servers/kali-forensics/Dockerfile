FROM kalilinux/kali-rolling AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install forensics tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    kali-tools-forensics \
    bulk-extractor \
    foremost \
    binwalk \
    exiftool \
    tshark \
    wireshark-common \
    yara \
    file \
    binutils \
    sleuthkit \
    dc3dd \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip3 install --break-system-packages --no-cache-dir \
    fastmcp \
    volatility3 \
    pyshark \
    yara-python \
    python-magic \
    pefile

# Pre-download Volatility3 symbol tables
RUN mkdir -p /usr/lib/python3/dist-packages/volatility3/symbols && \
    python3 -c "import volatility3.framework; volatility3.framework.require_interface_version(2,0,0)" 2>/dev/null || true

# Non-root user
RUN useradd -m -s /bin/bash investigator
RUN mkdir -p /cases /evidence /reports && \
    chown -R investigator:investigator /cases /evidence /reports

COPY server.py /app/server.py
RUN chown -R investigator:investigator /app

USER investigator
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import fastmcp; print('ok')" || exit 1

CMD ["python3", "-m", "server"]
