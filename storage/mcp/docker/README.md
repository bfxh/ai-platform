# AI MCP Docker 容器化系统

AI MCP Docker 容器化系统为所有 MCP 服务提供完整的容器化部署和管理方案，支持 Windows Docker Desktop 环境。

## 系统架构

```
AI MCP Docker System
├── docker/
│   ├── base/
│   │   └── Dockerfile              # 基础镜像
│   ├── services/
│   │   ├── blender.Dockerfile      # Blender MCP
│   │   ├── unity.Dockerfile        # Unity MCP
│   │   ├── ue.Dockerfile           # Unreal Engine MCP
│   │   ├── godot.Dockerfile        # Godot MCP
│   │   ├── code-quality.Dockerfile # Code Quality
│   │   ├── github-dl.Dockerfile    # GitHub Download
│   │   ├── vs-mgr.Dockerfile       # VS Manager
│   │   ├── dev-mgr.Dockerfile      # Dev Manager
│   │   ├── download-manager.Dockerfile
│   │   ├── network-optimizer.Dockerfile
│   │   └── memory-monitor.Dockerfile
│   ├── templates/
│   │   └── mcp-service.Dockerfile  # 服务模板
│   ├── docker-compose.yml          # 主配置
│   ├── .env.example                # 环境配置模板
│   ├── build-all.ps1               # 构建脚本
│   ├── manage-services.ps1         # 管理脚本
│   ├── health-check.ps1            # 健康检查
│   └── README.md                   # 本文档
```

## 服务分类

| 类别 | 服务 | 端口 | 说明 |
|------|------|------|------|
| **JM** | blender-mcp | 8001 | Blender 3D 建模 MCP |
| **JM** | unity-mcp | 8002 | Unity 引擎 MCP |
| **JM** | ue-mcp | 8003 | Unreal Engine MCP |
| **JM** | godot-mcp | 8004 | Godot 引擎 MCP |
| **BC** | code-quality | 8005 | 代码质量检查 |
| **BC** | github-dl | 8006 | GitHub 下载管理 |
| **BC** | vs-mgr | 8007 | VS Code 管理 |
| **BC** | dev-mgr | 8008 | 开发管理 |
| **Tools** | download-manager | 8009 | 下载管理 |
| **Tools** | network-optimizer | 8010 | 网络优化 |
| **Tools** | memory-monitor | 8011 | 内存监控 |
| **Shared** | n8n | 5678 | 工作流引擎 |

## 快速开始

### 1. 前置要求

- Windows 10/11 专业版或企业版
- Docker Desktop for Windows (已启用 WSL2 后端)
- PowerShell 5.1 或更高版本

### 2. 初始化配置

```powershell
# 复制环境配置模板
cd \python\MCP\docker
copy .env.example .env

# 编辑 .env 文件，根据需要修改配置
notepad .env
```

### 3. 构建镜像

```powershell
# 构建所有镜像 (基础镜像 + 所有服务)
.\build-all.ps1

# 构建指定版本标签
.\build-all.ps1 -Tag v1.0.0

# 只构建特定服务
.\build-all.ps1 -Services blender-mcp,code-quality

# 跳过基础镜像构建
.\build-all.ps1 -SkipBase
```

### 4. 启动服务

```powershell
# 启动所有服务
.\manage-services.ps1 start

# 启动特定服务
.\manage-services.ps1 start -Services blender-mcp,download-manager
```

### 5. 查看状态

```powershell
# 查看所有服务状态
.\manage-services.ps1 status

# 查看容器列表
.\manage-services.ps1 ps
```

## 服务管理

### 启动/停止/重启

```powershell
# 启动
.\manage-services.ps1 start
.\manage-services.ps1 start -Services blender-mcp

# 停止
.\manage-services.ps1 stop
.\manage-services.ps1 stop -Services blender-mcp

# 重启
.\manage-services.ps1 restart
.\manage-services.ps1 restart -Services blender-mcp
```

### 查看日志

```powershell
# 查看所有服务日志 (最新 100 行)
.\manage-services.ps1 logs

# 跟踪日志输出
.\manage-services.ps1 logs -Follow

# 查看特定服务日志
.\manage-services.ps1 logs -Services blender-mcp -Lines 50

# 持续跟踪
.\manage-services.ps1 logs -Services blender-mcp -Follow -Lines 50
```

### 更新服务

```powershell
# 更新所有服务 (拉取最新镜像并重新部署)
.\manage-services.ps1 update

# 更新特定服务
.\manage-services.ps1 update -Services blender-mcp
```

### 容器操作

```powershell
# 在容器中执行命令
.\manage-services.ps1 exec -Services blender-mcp -Command "python -c 'print(1+1)'"

# 清理未使用的资源
.\manage-services.ps1 cleanup

# 强制清理 (无需确认)
.\manage-services.ps1 cleanup -Force
```

## 健康检查

### 单次检查

```powershell
# 执行一次健康检查
.\health-check.ps1

# 自动重启不健康服务
.\health-check.ps1 -AutoRestart

# 生成 HTML 报告
.\health-check.ps1 -Report
```

### 持续监控

```powershell
# 持续监控 (每 60 秒检查一次)
.\health-check.ps1 -Continuous

# 自定义间隔
.\health-check.ps1 -Continuous -Interval 30

# 持续监控 + 自动重启
.\health-check.ps1 -Continuous -Interval 30 -AutoRestart

# 发送告警通知
.\health-check.ps1 -Continuous -AutoRestart -AlertWebhook "https://hooks.slack.com/..."
```

## 版本回滚

Docker 镜像支持多标签管理，便于版本回滚:

```powershell
# 查看所有镜像标签
docker images ai/mcp-*

# 回滚到特定版本 (修改 docker-compose.yml 中的 IMAGE_TAG)
# 编辑 .env 文件
notepad .env
# 修改 IMAGE_TAG=v1.0.0

# 重新部署
.\manage-services.ps1 update
```

## 配置说明

### 环境变量 (.env)

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | info | 日志级别 |
| `DOCKER_NETWORK` | ai-mcp-network | Docker 网络名称 |
| `IMAGE_TAG` | latest | 镜像标签 |
| `BLENDER_PORT` | 8001 | Blender 服务端口 |
| `GITHUB_TOKEN` | - | GitHub 访问令牌 |
| `AUTO_RESTART_UNHEALTHY` | true | 自动重启不健康服务 |
| `ALERT_WEBHOOK_URL` | - | 告警 Webhook |

### 资源限制

每个服务都可以配置资源限制:

```env
BLENDER_MEMORY_LIMIT=4G
BLENDER_MEMORY_RES=1G
BLENDER_CPU_LIMIT=2.0
BLENDER_CPU_RES=0.5
```

## 网络架构

所有服务共享 `ai-mcp-network` 桥接网络:

```
172.20.0.0/16
├── 172.20.0.1    (网关)
├── 172.20.0.2    (blender-mcp)
├── 172.20.0.3    (unity-mcp)
├── 172.20.0.4    (ue-mcp)
└── ...
```

服务间可以通过容器名互相访问:
```python
# 在 blender-mcp 中访问 code-quality
requests.get("http://mcp-code-quality:8005/health")
```

## 数据持久化

每个服务都有独立的数据卷:

| 卷名 | 用途 |
|------|------|
| blender-data | Blender 模型数据 |
| blender-logs | Blender 日志 |
| github-data | GitHub 下载缓存 |
| dlmgr-downloads | 下载文件存储 |
| n8n-data | N8N 工作流数据 |

## 故障排除

### Docker Desktop 未运行

```powershell
# 检查 Docker 状态
docker version

# 启动 Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### 端口冲突

```powershell
# 检查端口占用
netstat -ano | findstr :8001

# 修改 .env 中的端口配置
notepad .env
```

### 容器无法启动

```powershell
# 查看容器日志
.\manage-services.ps1 logs -Services blender-mcp

# 检查容器详情
docker inspect mcp-blender

# 手动运行容器调试
docker run -it --rm ai/mcp-jm-blender:latest bash
```

### 镜像构建失败

```powershell
# 查看构建日志
cat .\build-logs\build-*.log

# 清理缓存重新构建
docker builder prune -f
.\build-all.ps1
```

## 安全建议

1. **非 root 用户**: 所有容器使用 `mcpuser` 非 root 用户运行
2. **端口暴露**: 只暴露必要端口，避免暴露敏感服务
3. **镜像扫描**: 定期扫描镜像漏洞
   ```powershell
   docker scan ai/mcp-jm-blender:latest
   ```
4. **令牌管理**: 将敏感令牌存储在 `.env` 文件中，不要提交到版本控制

## 性能优化

### 资源分配建议

| 服务 | 内存限制 | CPU 限制 | 说明 |
|------|----------|----------|------|
| blender-mcp | 4G | 2.0 | 3D 渲染需要较多资源 |
| ue-mcp | 4G | 2.0 | 引擎服务资源密集 |
| unity-mcp | 2G | 1.5 | 中等资源需求 |
| code-quality | 2G | 1.0 | 代码分析需要内存 |
| 其他 | 1G | 0.5 | 轻量级服务 |

### 日志管理

日志文件自动存储在容器中，可通过以下方式管理:

```powershell
# 查看日志大小
docker system df -v

# 清理旧日志
docker logs --tail 100 mcp-blender

# 设置日志驱动限制 (在 docker-compose.yml 中)
# logging:
#   driver: "json-file"
#   options:
#     max-size: "10m"
#     max-file: "3"
```

## 扩展开发

### 添加新服务

1. 在 `services/` 目录创建新的 Dockerfile
2. 在 `docker-compose.yml` 添加服务定义
3. 在 `build-all.ps1` 和 `manage-services.ps1` 添加服务信息
4. 在 `.env.example` 添加配置项

### 自定义基础镜像

修改 `base/Dockerfile`，添加全局依赖:

```dockerfile
RUN pip install --no-cache-dir your-package
```

然后重新构建:
```powershell
.\build-all.ps1
```

## 更新日志

### v1.0.0 (2026-04-22)
- 初始版本
- 支持 11 个 MCP 服务
- 完整的构建、管理、健康检查功能
- Windows Docker Desktop 兼容

## 许可证

MIT License
