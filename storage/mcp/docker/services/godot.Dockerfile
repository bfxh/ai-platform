FROM ai/mcp-base:latest

ENV SERVICE_NAME=godot_mcp \
    SERVICE_PORT=8004 \
    SERVICE_TYPE=JM \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./JM/godot_mcp.py /app/godot_mcp.py
COPY --chown=mcpuser:mcpuser ./JM/godot_mcp_server.py /app/godot_mcp_server.py

USER mcpuser

EXPOSE 8004
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8004/health')" || exit 1

CMD ["python", "godot_mcp_server.py"]
