FROM kalilinux/kali-rolling AS base

ENV DEBIAN_FRONTEND=noninteractive

# Install system OSINT tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    subfinder \
    amass \
    whatweb \
    theharvester \
    whois \
    dnsutils \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python OSINT packages
# --ignore-installed avoids "Cannot uninstall multidict" from Debian-managed packages
RUN pip3 install --break-system-packages --no-cache-dir --ignore-installed \
    "fastmcp<3" \
    maigret \
    sherlock-project \
    holehe \
    h8mail \
    dnstwist \
    requests \
    aiohttp

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

ENTRYPOINT []
CMD ["python3", "-m", "server"]
