---
title: Claude Code 土豆版 (CLAUSE) 架构与运行机制
date: 2026-04-29
source: 代码分析
tags: [claude-code, clause, agent, mcp, ink-tui, electron, bun]
---

# Claude Code 土豆版 (CLAUSE) — 完整运行机制

## 一、项目概述

基于 2026-03-31 泄露的 Claude Code 源码修复的本地增强版，名为 claude-code-tudou（土豆版）。
TypeScript + Bun 编写，双端体验：终端 TUI（React + Ink）+ 桌面端（Electron + Vue 3）。

位置：

## 二、启动流程

```
bin/claude-code-tudou
    │ 检查 CLAUDE_CODE_FORCE_RECOVERY_CLI
    ├── 恢复模式 → src/localRecoveryCli.ts
    └── 正常模式 → spawn("bun", ["--env-file=.env", entrypoint])
        │
        ▼
src/entrypoints/cli.tsx (智能路由器)
    │ 所有分支用动态 import()，快速路径零模块加载
    ├── --version → 输出版本号退出
    ├── --dump-system-prompt → 输出系统提示词
    ├── --claude-in-chrome-mcp → Chrome MCP
    ├── --computer-use-mcp → 计算机使用 MCP
    ├── --daemon-worker → 守护进程
    ├── remote-control/rc/bridge → 远程控制
    └── 默认 → 加载 main.tsx → 完整 TUI
```

## 三、12步初始化 (init.ts)

1. enableConfigs()
2. applySafeConfigEnvironmentVariables()
3. applyExtraCACertsFromConfig()
4. setupGracefulShutdown()
5. initialize1PEventLogging()
6. populateOAuthAccountInfoIfNeeded()
7. initJetBrainsDetection()
8. detectCurrentRepository()
9. initializeRemoteManagedSettingsLoadingPromise()
10. configureGlobalMTLS()
11. configureGlobalAgents()
12. preconnectAnthropicApi()

## 四、核心架构

```
┌─────────────────────────────────────────────┐
│  用户界面层                                  │
│  TUI (Ink+React) / Desktop (Electron+Vue3)  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  QueryEngine (query.ts) — Agent Loop        │
│  query() → API → 解析工具调用 → 执行 → 循环  │
├──────────────────┬──────────────────────────┤
│  Tool 系统       │  API 通信层               │
│  20+ 内置工具    │  services/api/claude.ts   │
│  BashTool       │  Anthropic SDK            │
│  FileEditTool   │  Bedrock/Vertex           │
│  AgentTool      │                           │
│  MCPTool        │                           │
├──────────────────┼──────────────────────────┤
│  MCP 客户端      │  记忆系统                 │
│  services/mcp/   │  memdir/memdir.ts        │
│  Stdio/SSE/HTTP  │  MEMORY.md (≤200行/25KB) │
└──────────────────┴──────────────────────────┘
```

## 五、Agent Loop（核心运行机制）

```
1. 构建 System Prompt (CLAUDE.md + MEMORY.md + 工具描述 + 消息历史)
2. 调用 Anthropic API (流式)
3. 解析响应:
   - text_delta → 实时显示
   - tool_use → 工具调用
4. 执行工具 (BashTool/FileEditTool/MCPTool/AgentTool 等)
5. 工具结果追加到消息历史
6. 回到步骤2，循环直到 end_turn / 用户中断 / 最大迭代次数
```

## 六、20+ 内置工具

| 工具 | 功能 | 关键特性 |
|------|------|----------|
| BashTool | 执行终端命令 | 沙盒隔离、超时控制、后台运行 |
| FileEditTool | 精准编辑文件 | 查找替换、多位置编辑 |
| FileReadTool | 读取文件 | 行范围读取、缓存 |
| FileWriteTool | 写入文件 | 创建/覆盖 |
| GrepTool | 代码搜索 | ripgrep 引擎 |
| GlobTool | 文件匹配 | glob 模式 |
| AgentTool | 子代理 | 独立上下文、可嵌套 |
| MCPTool | MCP 服务调用 | Stdio/SSE/HTTP 传输 |
| WebFetchTool | 网页抓取 | URL 内容获取 |
| WebSearchTool | 网页搜索 | 搜索引擎查询 |
| LSPTool | 语言服务 | 代码诊断/跳转定义 |
| SkillTool | 技能执行 | 可复用技能模块 |
| TodoWriteTool | 任务管理 | 待办事项 |
| TaskCreateTool | 创建后台任务 | 异步执行 |
| ConfigTool | 配置管理 | 运行时配置 |
| BriefTool | 上下文摘要 | 压缩对话历史 |
| EnterPlanModeTool | 进入规划模式 | 分步规划 |
| TeamCreateTool | 创建团队 | 多 Agent 协作 |
| SendMessageTool | 团队消息 | Agent 间通信 |
| ToolSearchTool | 工具搜索 | 发现可用工具 |

## 七、MCP 集成机制

```
MCP 客户端启动流程:
1. 读取配置 (.mcp-config.json + ~/.claude/mcp.json + Claude.ai 远程)
2. 为每个 MCP 服务创建 Transport:
   - StdioClientTransport → 子进程通信
   - SSEClientTransport → HTTP SSE
   - StreamableHTTPClientTransport → HTTP 流
3. 连接并发现能力 (listTools/listResources/listPrompts)
4. 为每个 MCP 工具创建 MCPTool 实例
5. 调用时 MCPTool.execute() → client.callTool()
```

本项目 .mcp-config.json 配置了 18 个 MCP 服务，全部指向 /python/MCP/ 下的 Python 脚本。

## 八、Agent/子代理系统

AgentTool 实现子代理：
- agentType: 代理类型标识
- whenToUse: 何时使用
- tools: 允许使用的工具列表
- 独立上下文窗口、独立 API 调用
- 支持自定义代理（从 .claude/agents/ 加载）

## 九、桌面端架构

Electron 主进程 (desktop/main.cjs):
- BrowserWindow (1260×860) 加载 Vue 3 前端
- IPC: chat:send/stop/newSession/getState, settings:get/save
- 核心通信: sendViaClaudeCli() → spawn CLI 子进程 → stdin 传 prompt → stdout 解析 stream-json
- 关键设计：桌面端启动 CLI 子进程，共享完全相同的核心逻辑

## 十、模型管理

选择优先级：会话内 /model > --model 参数 > ANTHROPIC_MODEL 环境变量 > 用户设置 > 默认 claude-sonnet-4

支持提供商：anthropic / bedrock / vertex / ollama / openrouter

## 十一、认证系统

- API Key (ANTHROPIC_API_KEY): 环境变量/配置文件/macOS Keychain
- OAuth Token: Claude.ai OAuth + 自动刷新
- AWS STS (Bedrock): 自动检测
- GCP (Vertex AI): Google ADC

## 十二、技术栈

| 层次 | 技术 |
|------|------|
| 运行时 | Bun 1.1+ |
| TUI | React 19 + Ink 6 |
| 桌面 | Electron 41 + Vue 3 |
| AI SDK | @anthropic-ai/sdk 0.80+ |
| MCP SDK | @modelcontextprotocol/sdk 1.29+ |
| 搜索 | ripgrep (内置) |
| 类型校验 | Zod 4 |
| 遥测 | OpenTelemetry |
| 特性开关 | GrowthBook |
| 沙盒 | @anthropic-ai/sandbox-runtime |

## 十三、土豆版修复

| 修复 | 说明 |
|------|------|
| 启动链路 | 修复入口脚本错误的路由逻辑 |
| 交互性能 | 解决 modifiers-napi 缺失导致 Enter 键失效 |
| 依赖补全 | 为缺失 .md/.txt 模板添加桩文件 |
| 桌面集成 | 重新开发 Electron 与 CLI 通信桥接 |
| API 兼容 | 通过 .env 支持 MiniMax/OpenRouter/Ollama |
