FROM python:3.12-slim AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    binutils \
    file \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME so Ghidra headless finds the JDK without TTY prompt
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Install radare2 from GitHub (not available in Debian Trixie repos)
# Use explicit versioned URL as fallback if latest redirect fails
RUN wget -q "https://github.com/radareorg/radare2/releases/latest/download/radare2_amd64.deb" -O /tmp/radare2.deb && \
    (dpkg -i /tmp/radare2.deb || apt-get install -f -y) && \
    rm -f /tmp/radare2.deb && \
    r2 -v || echo "WARN: radare2 install may have failed — r2pipe will report errors at runtime"

# Install Ghidra headless
RUN wget -q "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_build/ghidra_11.1.2_PUBLIC_20240709.zip" -O /tmp/ghidra.zip && \
    unzip -q /tmp/ghidra.zip -d /opt && \
    mv /opt/ghidra_* /opt/ghidra && \
    rm /tmp/ghidra.zip

ENV GHIDRA_INSTALL_DIR=/opt/ghidra
ENV PATH="${PATH}:/opt/ghidra/support"

# Install Capa (download and make executable — no || true to surface errors)
RUN wget -q "https://github.com/mandiant/capa/releases/latest/download/capa-linux" -O /usr/local/bin/capa && \
    chmod +x /usr/local/bin/capa

# Python packages
RUN pip install --no-cache-dir \
    "fastmcp<3" \
    yara-python \
    pefile \
    python-magic \
    lief \
    capstone \
    r2pipe

# Create YARA rules directory with a minimal index
RUN mkdir -p /app/yara-rules && \
    echo '// DFIReballz YARA Rules Index' > /app/yara-rules/index.yar && \
    echo '// Add your custom rules to /app/yara-rules/custom.yar' > /app/yara-rules/custom.yar && \
    echo 'rule placeholder { condition: false }' >> /app/yara-rules/index.yar && \
    echo 'rule placeholder_custom { condition: false }' >> /app/yara-rules/custom.yar

# Non-root user
RUN useradd -m -s /bin/bash investigator
RUN mkdir -p /cases /evidence /reports /tmp/ghidra-projects && \
    chown -R investigator:investigator /cases /evidence /reports /tmp/ghidra-projects /app/yara-rules

COPY server.py /app/server.py
RUN chown -R investigator:investigator /app

USER investigator
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import fastmcp; print('ok')" || exit 1

ENTRYPOINT []
CMD ["python3", "-m", "server"]
