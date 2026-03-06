FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastmcp \
    requests \
    aiohttp \
    pydantic

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
