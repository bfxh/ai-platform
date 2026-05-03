FROM ai/mcp-base:latest

ENV SERVICE_NAME=blender_mcp \
    SERVICE_PORT=8001 \
    SERVICE_TYPE=JM \
    PYTHONPATH=/app

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libxi6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=mcpuser:mcpuser ./JM/blender_mcp /app/blender_mcp
COPY --chown=mcpuser:mcpuser ./JM/blender_mcp_server.py /app/blender_mcp_server.py
COPY --chown=mcpuser:mcpuser ./blender_scripts /app/blender_scripts

RUN pip install --no-cache-dir bpy>=4.0.0 2>/dev/null || true

USER mcpuser

EXPOSE 8001
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["python", "-m", "blender_mcp.server"]
