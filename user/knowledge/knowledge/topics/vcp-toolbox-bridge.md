---
title: VCPToolBox 桥接方案 — Claude Code 通过 VCPToolBox 连接本地模型
date: 2026-04-29
source: 实践部署
tags: [vcp-toolbox, bridge, ollama, claude-code, api-proxy, deployment]
---

# VCPToolBox 桥接方案

## 一、方案目标

让 Claude Code 土豆版在没有外部 API Key 的情况下，通过 VCPToolBox 中间层连接本地 Ollama 模型。

## 二、架构

```
Claude Code (CLAUSE)
    │  ANTHROPIC_BASE_URL=http://127.0.0.1:6005/v1
    │  ANTHROPIC_AUTH_TOKEN=vcp-bridge-key
    ▼
VCPToolBox API (端口 6005)
    │  API_URL=http://127.0.0.1:11434
    │  API_Key=ollama-local
    │  87 个插件 + RAG + Agent
    ▼
Ollama (端口 11434)
    │  qwen2.5-coder:7b
    ▼
VCPToolBox 管理面板 (端口 6006)
    │  http://127.0.0.1:6006/AdminPanel/
    │  admin / vcp2026
```

## 三、VCPToolBox 关键发现

### 3.1 双进程架构（重要！）

VCPToolBox 需要启动**两个** Node.js 进程：

| 进程 | 命令 | 端口 | 作用 |
|------|------|------|------|
| API 服务 | `node server.js` | 6005 | API 桥接 + 插件系统 |
| 管理面板 | `node adminServer.js` | **6006** (=PORT+1) | 管理面板 Web UI |

**踩坑记录**：只启动 server.js 时，访问 /AdminPanel/ 会被 302 重定向到 PORT+1（6006），但 6006 没有服务，面板打不开。必须同时启动 adminServer.js。

源码位置：
- server.js 第534行：`const ADMIN_PORT = parseInt(port) + 1`
- server.js 第540行：`res.redirect(302, ...:${ADMIN_PORT}...)`

### 3.2 IP 封禁机制

VCPToolBox 有安全防护：
- 异常检测时间窗口: 30 分钟
- 最大不同 IP 数: 5
- 锁定持续时间: 60 分钟
- 登录失败次数过多会触发 IP 封禁（429 Too Many Requests）

**踩坑记录**：测试 API 时未带 Authorization 头，多次 401 触发了 IP 封禁。解决方案：重启 VCPToolBox 进程。

### 3.3 依赖安装问题

- `hnswlib-node` 编译失败（向量搜索库，需要 C++ 编译环境）
- 解决：`npm install --ignore-scripts` 跳过原生模块编译
- `better-sqlite3` 需要单独编译：`npm rebuild better-sqlite3`

## 四、VCPToolBox 配置文件 (config.env)

```env
API_Key=ollama-local          # 后端 API Key（Ollama 不需要真实 Key）
API_URL=http://127.0.0.1:11434  # 后端 API 地址（Ollama）
PORT=6005                      # 主服务端口
Key=vcp-bridge-key             # API 认证 Key
Image_Key=vcp-image-key        # 图片服务 Key
File_Key=vcp-file-key          # 文件服务 Key
VCP_Key=vcp-ws-key             # WebSocket Key
AdminUsername=admin             # 管理面板用户名
AdminPassword=vcp2026           # 管理面板密码
DebugMode=true                 # 调试模式
ShowVCP=false                  # 隐藏 VCP 工具描述
ChinaModel1=GLM,qwen,deepseek,hunyuan  # 中国模型列表
ChinaModel1Cot=true            # 中国模型启用 CoT
```

## 五、Claude Code .env 配置

```env
MODEL_PROVIDER=anthropic
ANTHROPIC_AUTH_TOKEN=vcp-bridge-key
ANTHROPIC_BASE_URL=http://127.0.0.1:6005/v1
ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen2.5-coder:7b
ANTHROPIC_DEFAULT_OPUS_MODEL=qwen2.5-coder:7b
ANTHROPIC_DEFAULT_SONNET_MODEL=qwen2.5-coder:7b
ANTHROPIC_MODEL=qwen2.5-coder:7b
API_TIMEOUT_MS=3000000
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
DISABLE_TELEMETRY=1
```

关键点：
- MODEL_PROVIDER 设为 anthropic（因为 VCPToolBox 暴露 OpenAI 兼容接口，Claude Code 用 anthropic 模式可以兼容）
- ANTHROPIC_BASE_URL 指向 VCPToolBox（6005），不是 Ollama（11434）
- 三个模型槽位都设为同一个 Ollama 模型名

## 六、VCPToolBox 87 个插件分类

| 类别 | 代表插件 | 功能 |
|------|----------|------|
| AI 生成 | VCPDoubaoGen, VCPFluxGen, VCPQwenImageGen | 图片/视频/音乐生成 |
| 搜索 | VCPGoogleSearch, VCPTavilySearch, VCPDeepWikiVCP | 网页搜索/知识查询 |
| 文件 | VCPServerFileOperator, VCPServerCodeSearcher | 文件操作/代码搜索 |
| 系统 | VCPServerPowerShellExecutor, VCPLinuxShellExecutor | 命令执行 |
| 知识 | VCPLightMemo, VCPProjectAnalyst, VCPRAGDiaryPlugin | 记忆/RAG/项目分析 |
| Agent | VCPAgentAssistant, VCPMagiAgent, VCPSnowBridge | 多 Agent 协作 |
| 服务 | ChromeBridge, FileServer, ImageServer, VCPLog | 桥接/文件/图片/日志 |

## 七、验证方法

```bash
# 检查三个服务状态
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:11434/api/tags
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:6005/v1/models -H "Authorization: Bearer vcp-bridge-key"
curl.exe -s -o NUL -w "%{http_code}" http://127.0.0.1:6006/AdminPanel/login.html

# 测试 API 调用
curl.exe -X POST http://127.0.0.1:6005/v1/chat/completions \
  -H "Authorization: Bearer vcp-bridge-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"hello"}]}'
```

## 八、位置信息

| 组件 | 路径 |
|------|------|
| VCPToolBox | \python\downloads\VCPToolBox\VCPToolBox-main |
| Claude Code |  |
| 启动脚本 | \python\scripts\launch\start_clause.bat |
| 桥接脚本 | \python\scripts\launch\start_vcp_bridge.bat |
| .env 模板 | \python\scripts\launch\clause_env |
