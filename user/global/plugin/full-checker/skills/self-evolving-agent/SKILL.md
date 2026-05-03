---
name: "self-evolving-agent"
description: "自进化Agent技能，自动将任务执行路径结晶为可复用技能。Invoke when user wants agent to learn from tasks and build personal skill tree automatically."
---

# 自进化Agent技能

## 概述

基于 [GenericAgent](https://github.com/lsdefine/GenericAgent) 的自进化理念，实现任务执行路径自动结晶为技能的能力。核心哲学：不预装技能，而是让技能在使用中自然生长。

## 核心机制

### 自进化循环
```
新任务 → 自主探索(安装依赖/写脚本/调试) → 结晶执行路径为skill → 写入记忆层 → 下次直接调用
```

### 与您系统的映射
| GenericAgent概念 | 您的系统对应 |
|------------------|-------------|
| 9个原子工具 | MCP服务 + Skill系统 |
| Agent Loop | core/dispatcher.py |
| 记忆层 | storage/Brain/ |
| 技能结晶 | user/global/plugin/ skills/ |

## 关键特性

- **技能结晶**：每次完成新任务自动生成skill文件
- **分层记忆**：L1工作记忆 / L2技能记忆 / L3长期记忆 / L4会话归档
- **Token高效**：<30K上下文窗口，远低于其他Agent的200K-1M
- **9个原子工具**：浏览器注入、终端执行、文件系统、键盘鼠标、屏幕视觉、ADB移动设备

## 使用方法

### 自动结晶模式
```python
# 用户首次执行任务
"帮我读取微信消息" → Agent自动: 安装依赖→逆向数据库→写脚本→保存skill

# 下次执行相同任务
"帮我读取微信消息" → 一行调用已有skill
```

### 手动结晶
```python
# 将复杂工作流封装为skill
skill = {
    "name": "stock-monitor",
    "trigger": "监控股票并提醒",
    "steps": ["安装mootdx", "构建选股流程", "配置cron", "保存skill"],
    "cron": "0 9 * * 1-5"
}
```

## 与现有系统集成

本技能与以下系统深度集成：
- **full-checker**：技能结晶后自动注册到总检查
- **obsidian-knowledge**：技能文档自动同步到知识库
- **mcp-second-brain**：技能记忆存储到第二大脑

## 适用场景

- 重复性任务自动化
- 个人技能树构建
- 工作流渐进式积累
- 团队知识传承

## 参考项目

- GenericAgent: `\python\GenericAgent` (已下载)
- 技术论文: arXiv - GenericAgent: A Token-Efficient Self-Evolving LLM Agent
