FROM ai/mcp-base:latest

ENV SERVICE_NAME=code_quality \
    SERVICE_PORT=8005 \
    SERVICE_TYPE=BC \
    PYTHONPATH=/app

USER root

RUN pip install --no-cache-dir \
    pylint>=3.0.0 \
    black>=23.0.0 \
    flake8>=6.0.0 \
    mypy>=1.7.0 \
    bandit>=1.7.0

COPY --chown=mcpuser:mcpuser ./BC/code_quality.py /app/code_quality.py

USER mcpuser

EXPOSE 8005
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')" || exit 1

CMD ["python", "code_quality.py"]
