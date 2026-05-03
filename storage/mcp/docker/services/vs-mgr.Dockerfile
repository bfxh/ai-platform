FROM ai/mcp-base:latest

ENV SERVICE_NAME=vs_mgr \
    SERVICE_PORT=8007 \
    SERVICE_TYPE=BC \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./BC/vs_mgr.py /app/vs_mgr.py
COPY --chown=mcpuser:mcpuser ./BC/vscode_ai.py /app/vscode_ai.py

USER mcpuser

EXPOSE 8007
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8007/health')" || exit 1

CMD ["python", "vs_mgr.py"]
