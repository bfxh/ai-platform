# AI MCP 服务 Dockerfile 模板
# 使用方法: 复制此文件并重命名为 {service-name}.Dockerfile，然后修改以下变量
#
# 构建命令示例:
# docker build -f mcp-service.Dockerfile \
#   --build-arg SERVICE_NAME=blender_mcp \
#   --build-arg SERVICE_PORT=8001 \
#   --build-arg SERVICE_TYPE=JM \
#   -t ai/mcp-jm-blender:latest .

FROM ai/mcp-base:latest

# 构建参数 (需要在构建时传入)
ARG SERVICE_NAME
ARG SERVICE_PORT
ARG SERVICE_TYPE
ARG SERVICE_MODULE

# 环境变量
ENV SERVICE_NAME=${SERVICE_NAME} \
    SERVICE_PORT=${SERVICE_PORT} \
    SERVICE_TYPE=${SERVICE_TYPE} \
    SERVICE_MODULE=${SERVICE_MODULE} \
    PYTHONPATH=/app

# 切换到 root 用户以安装依赖
USER root

# 复制服务特定依赖文件 (如果存在)
COPY --chown=mcpuser:mcpuser requirements.txt* ./

# 安装服务特定依赖
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# 复制服务代码
# 注意: 源路径需要根据实际项目结构调整
COPY --chown=mcpuser:mcpuser ./${SERVICE_MODULE} /app/${SERVICE_MODULE}
COPY --chown=mcpuser:mcpuser ./shared /app/shared 2>/dev/null || true

# 创建服务启动脚本
RUN echo '#!/bin/bash\n\
echo "Starting ${SERVICE_NAME} on port ${SERVICE_PORT}"\n\
cd /app\n\
exec python -m ${SERVICE_MODULE}' > /app/start.sh \
    && chmod +x /app/start.sh

# 切换回非 root 用户
USER mcpuser

# 暴露服务端口
EXPOSE ${SERVICE_PORT}

# 工作目录
WORKDIR /app

# 健康检查
# 服务需要实现 /health 端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT}/health || exit 1

# 启动命令
CMD ["/app/start.sh"]


# =============================================================================
# 以下为具体服务示例配置 (复制后取消注释并修改):
# =============================================================================

# ----- JM 类服务示例: Blender MCP -----
# FROM ai/mcp-base:latest
# ENV SERVICE_NAME=blender_mcp SERVICE_PORT=8001 SERVICE_TYPE=JM
# USER root
# COPY --chown=mcpuser:mcpuser ./JM/blender_mcp /app/blender_mcp
# RUN pip install --no-cache-dir bpy>=4.0.0
# USER mcpuser
# EXPOSE 8001
# WORKDIR /app
# HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
#     CMD curl -f http://localhost:8001/health || exit 1
# CMD ["python", "-m", "blender_mcp.server"]

# ----- BC 类服务示例: Code Quality -----
# FROM ai/mcp-base:latest
# ENV SERVICE_NAME=code_quality SERVICE_PORT=8005 SERVICE_TYPE=BC
# USER root
# COPY --chown=mcpuser:mcpuser ./BC/code_quality.py /app/
# RUN pip install --no-cache-dir pylint>=3.0.0 black>=23.0.0 flake8>=6.0.0
# USER mcpuser
# EXPOSE 8005
# WORKDIR /app
# HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
#     CMD curl -f http://localhost:8005/health || exit 1
# CMD ["python", "code_quality.py"]

# ----- Tools 类服务示例: Download Manager -----
# FROM ai/mcp-base:latest
# ENV SERVICE_NAME=download_manager SERVICE_PORT=8009 SERVICE_TYPE=Tools
# USER root
# COPY --chown=mcpuser:mcpuser ./Tools/download_manager.py /app/
# RUN pip install --no-cache-dir aria2p>=0.11.0
# USER mcpuser
# EXPOSE 8009
# WORKDIR /app
# HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
#     CMD curl -f http://localhost:8009/health || exit 1
# CMD ["python", "download_manager.py"]
