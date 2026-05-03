FROM ai/mcp-base:latest

ENV SERVICE_NAME=github_dl \
    SERVICE_PORT=8006 \
    SERVICE_TYPE=BC \
    PYTHONPATH=/app

USER root

RUN pip install --no-cache-dir PyGithub>=2.1.0 gitpython>=3.1.0

COPY --chown=mcpuser:mcpuser ./BC/github_dl.py /app/github_dl.py
COPY --chown=mcpuser:mcpuser ./BC/github_auto_dl.py /app/github_auto_dl.py

USER mcpuser

EXPOSE 8006
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8006/health')" || exit 1

CMD ["python", "github_dl.py"]
