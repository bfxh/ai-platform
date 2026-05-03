FROM ai/mcp-base:latest

ENV SERVICE_NAME=dev_mgr \
    SERVICE_PORT=8008 \
    SERVICE_TYPE=BC \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./BC/dev_mgr.py /app/dev_mgr.py
COPY --chown=mcpuser:mcpuser ./BC/mcp_workflow.py /app/mcp_workflow.py

USER mcpuser

EXPOSE 8008
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8008/health')" || exit 1

CMD ["python", "dev_mgr.py"]
