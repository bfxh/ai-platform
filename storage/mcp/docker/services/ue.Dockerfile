FROM ai/mcp-base:latest

ENV SERVICE_NAME=ue_mcp \
    SERVICE_PORT=8003 \
    SERVICE_TYPE=JM \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./JM/ue_mcp.py /app/ue_mcp.py
COPY --chown=mcpuser:mcpuser ./JM/ue5_manager.py /app/ue5_manager.py

USER mcpuser

EXPOSE 8003
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["python", "ue_mcp.py"]
