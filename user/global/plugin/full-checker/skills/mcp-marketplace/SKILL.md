---
name: "mcp-marketplace"
description: "MCP市场技能，集成68+原子MCP模块和400+MCP服务器。Invoke when user needs MCP tool integration, marketplace browsing, or MCP server management."
---

# MCP市场技能

## 概述

集成MCP(Model Context Protocol)生态，包括FocusMCP(68+原子模块)、Activepieces(400+ MCP服务器)等。

## MCP生态现状(2026)

| 项目 | Stars | 模块数 | 特点 |
|------|-------|--------|------|
| **FocusMCP** | 新 | 68+ bricks | 原子MCP模块，按需加载 |
| **Activepieces** | 21K | 400+ MCP | 开源Zapier替代，自动暴露MCP |
| **MCP 1.0** | 官方 | - | Linux Foundation托管，统一标准 |

## MCP 1.0 核心特性(2026年4月)
- 统一注册表
- 会话恢复
- 安全增强
- 跨AI工具兼容(Claude/ChatGPT/VS Code/Cursor)

## 与您系统的映射

| MCP能力 | 您的系统 |
|---------|---------|
| MCP Server | storage/mcp/ (JM/BC/Tools) |
| VCPToolBox | 87个插件, 端口6005 |
| agents-md | 项目上下文发现 |
| ollama-bridge | WS桥接 |

## 使用方法

### 安装MCP模块
```bash
# FocusMCP - 按需加载原子模块
mcp install shell    # 命令执行
mcp install search   # 搜索
mcp install files    # 文件操作
```

### Activepieces MCP
```bash
# 自动将pieces暴露为MCP服务器
# 可在Claude Desktop/Cursor/Windsurf中使用
```

## 适用场景

- AI工具扩展
- MCP服务器管理
- 跨平台工具集成
- 技能市场浏览