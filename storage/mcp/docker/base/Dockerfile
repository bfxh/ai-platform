# AI MCP 基础镜像
# 基于 Python 3.11 Slim 版本，提供轻量级运行环境

FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    git \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 升级 pip
RUN pip install --upgrade pip setuptools wheel

# 安装常用 Python 依赖
RUN pip install --no-cache-dir \
    requests>=2.31.0 \
    aiohttp>=3.9.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    uvicorn>=0.24.0 \
    fastapi>=0.104.0 \
    python-dotenv>=1.0.0 \
    loguru>=0.7.0 \
    httpx>=0.25.0 \
    websockets>=12.0 \
    psutil>=5.9.0 \
    pyyaml>=6.0.1 \
    click>=8.1.0

# 创建工作目录
WORKDIR /app

# 创建非 root 用户 (mcpuser)
RUN groupadd -r mcpuser && useradd -r -g mcpuser -d /app -s /bin/bash mcpuser \
    && chown -R mcpuser:mcpuser /app

# 创建日志目录
RUN mkdir -p /app/logs && chown -R mcpuser:mcpuser /app/logs

# 切换到非 root 用户
USER mcpuser

# 暴露常用端口范围
EXPOSE 8000-9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认命令
CMD ["python", "-c", "print('AI MCP Base Image Ready')"]
