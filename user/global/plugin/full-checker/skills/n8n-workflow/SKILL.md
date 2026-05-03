---
name: "n8n-workflow"
description: "n8n工作流自动化技能，181K Stars开源自动化平台。Invoke when user needs workflow automation, API integration, or task scheduling."
---

# n8n工作流自动化技能

## 概述

基于n8n(181K Stars)和Activepieces(21K Stars, 400+ MCP服务器)的工作流自动化能力。

## 核心平台对比

| 平台 | Stars | 定位 | 特点 |
|------|-------|------|------|
| **n8n** | 181K | 通用自动化 | Fair-Code, 自托管, 400+集成 |
| **Activepieces** | 21K | AI+MCP自动化 | 400+ MCP服务器, 开源Zapier替代 |
| **Dify** | 135K | LLM应用开发 | 可视化Agent工作流 |
| **Flowise** | 35K+ | 低代码AI工作流 | 拖拽式, LangChain生态 |

## 与您系统的映射

| 自动化能力 | 您的系统 |
|-----------|---------|
| 工作流引擎 | core/workflow_engine.py |
| 任务调度 | gstack-core/ |
| MCP服务 | storage/mcp/ |
| 技能系统 | user/global/plugin/ |

## 使用方法

### Docker部署n8n
```bash
docker run -p 5678:5678 n8nio/n8n
```

### 工作流示例
```json
{
  "name": "AI日报生成",
  "trigger": "schedule:0 8 * * *",
  "steps": [
    "搜索AI行业新闻",
    "筛选3条重要资讯",
    "生成摘要",
    "发送到微信"
  ]
}
```

## 适用场景

- 业务流程自动化
- API集成
- 定时任务调度
- 多系统数据同步