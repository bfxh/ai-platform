FROM ai/mcp-base:latest

ENV SERVICE_NAME=network_optimizer \
    SERVICE_PORT=8010 \
    SERVICE_TYPE=Tools \
    PYTHONPATH=/app

USER root

COPY --chown=mcpuser:mcpuser ./Tools/network_optimizer.py /app/network_optimizer.py
COPY --chown=mcpuser:mcpuser ./Tools/net_pro.py /app/net_pro.py

USER mcpuser

EXPOSE 8010
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health')" || exit 1

CMD ["python", "network_optimizer.py"]
