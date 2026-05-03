FROM ai/mcp-base:latest

ENV SERVICE_NAME=memory_monitor \
    SERVICE_PORT=8011 \
    SERVICE_TYPE=Tools \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./Tools/memory_monitor.py /app/memory_monitor.py
COPY --chown=mcpuser:mcpuser ./Tools/memory_mcp /app/memory_mcp

USER mcpuser

EXPOSE 8011
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')" || exit 1

CMD ["python", "memory_monitor.py"]
