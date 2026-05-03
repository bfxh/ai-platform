---
title: 知识主题索引
date: 2026-04-29
updated: 2026-04-29
---

# 知识主题索引

本目录包含对 \python 平台及其相关组件的深度分析知识。

## 主题列表

| 文件 | 标题 | 关键词 |
|------|------|--------|
| [ai-platform-architecture.md](ai-platform-architecture.md) | \python 本地化 AI 能力集成平台架构分析 | architecture, dispatcher, pipeline, mcp, knowledge-system |
| [claude-code-clause.md](claude-code-clause.md) | Claude Code 土豆版 (CLAUSE) 架构与运行机制 | claude-code, agent, mcp, ink-tui, electron, bun |
| [vcp-toolbox-bridge.md](vcp-toolbox-bridge.md) | VCPToolBox 桥接方案 | vcp-toolbox, bridge, ollama, api-proxy, deployment |
| [startup-scripts-and-config.md](startup-scripts-and-config.md) | 启动脚本与配置参考 | scripts, startup, config, bun, environment |
| [bug-knowledge-base.md](bug-knowledge-base.md) | Bug 知识库 (第9-13轮安全审计) | security, command-injection, path-traversal, xxe, cors, pickle, ssl, async, race-condition |

## 关联关系

```
ai-platform-architecture (\python 平台)
    │
    ├── claude-code-clause (Claude Code 土豆版)
    │     └── 通过 .mcp-config.json 连接 \python 的 MCP 服务
    │
    └── vcp-toolbox-bridge (VCPToolBox 桥接)
          ├── 连接 Claude Code → VCPToolBox → Ollama
          └── startup-scripts-and-config (启动配置)
```

## 踩坑记录汇总

1. VCPToolBox 需要双进程（server.js + adminServer.js），管理面板在 PORT+1
2. Bun 安装后不在系统 PATH，需手动添加
3. VCPToolBox 有 IP 封禁机制，频繁无认证请求会触发 429
4. hnswlib-node 编译失败，用 --ignore-scripts 跳过
5. .env 写入受 TRAE 路径限制，通过启动脚本 copy 方式解决
6. Python 版本不一致（config.toml=312, scanner.py=310, AGENTS.md=310）
