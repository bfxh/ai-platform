FROM ai/mcp-base:latest

ENV SERVICE_NAME=download_manager \
    SERVICE_PORT=8009 \
    SERVICE_TYPE=Tools \
    PYTHONPATH=/app

USER root

RUN apt-get update && apt-get install -y --no-install-recommends aria2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir aria2p>=0.11.0

COPY --chown=mcpuser:mcpuser ./Tools/download_manager.py /app/download_manager.py
COPY --chown=mcpuser:mcpuser ./Tools/aria2_mcp.py /app/aria2_mcp.py

RUN mkdir -p /app/downloads && chown -R mcpuser:mcpuser /app/downloads

USER mcpuser

EXPOSE 8009
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8009/health')" || exit 1

CMD ["python", "download_manager.py"]
