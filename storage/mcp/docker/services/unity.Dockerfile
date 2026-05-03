FROM ai/mcp-base:latest

ENV SERVICE_NAME=unity_mcp \
    SERVICE_PORT=8002 \
    SERVICE_TYPE=JM \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./JM/unity_mcp.py /app/unity_mcp.py

USER mcpuser

EXPOSE 8002
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" || exit 1

CMD ["python", "unity_mcp.py"]
