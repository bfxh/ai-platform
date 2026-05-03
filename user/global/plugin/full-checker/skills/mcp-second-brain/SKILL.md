---
name: "mcp-second-brain"
description: "MCP第二大脑技能，基于SurrealDB图数据库实现AI持久化记忆。Invoke when user needs persistent AI memory or wants to build graph-based knowledge system."
---

# MCP第二大脑技能

## 概述

基于 [mcp-second-brain](https://github.com/malekjakub69/mcp-second-brain) 和 [second-brain](https://github.com/thekitchencoder/second-brain)，构建AI持久化图数据库记忆系统，让AI拥有跨会话的长期记忆。

## 核心功能

- **实体提取**：自动识别人物、地点、项目、概念
- **去重检测**：检测近似想法并跳过重复
- **自动关联**：通过向量相似度自动关联相关想法
- **语音消息**：通过Whisper转录音频后作为文本处理
- **图连接**：想法链接到实体和彼此（SurrealDB关系）
- **MCP集成**：将大脑暴露给Claude Code等AI助手

## 架构

```
用户输入 → 实体提取 → 去重检测 → 向量嵌入 → 自动关联 → SurrealDB存储
                                                                    ↓
AI助手 ← MCP接口 ← 图查询 ← 关系检索 ← 语义搜索 ← 记忆召回
```

## 与您系统的映射

| 第二大脑概念 | 您的系统对应 |
|-------------|-------------|
| SurrealDB图数据库 | storage/Brain/ |
| MCP Server | storage/mcp/ |
| 实体提取 | core/knowledge_manager.py |
| 向量嵌入 | Ollama本地模型 |
| 语义搜索 | 复利知识系统 |

## 使用方法

### 存储想法
```python
# 自然语言输入
brain.store("今天和团队讨论了新项目的架构方案，决定用微服务")
# 自动提取实体: [团队, 新项目, 微服务]
# 自动关联: 微服务 → architecture → projects
```

### 查询记忆
```python
# 语义搜索
results = brain.search("之前讨论的架构方案")
# 返回相关想法、实体、关联
```

### MCP集成
```python
# 通过MCP协议暴露给AI助手
mcp_config = {
    "server": "mcp-second-brain",
    "tools": ["store_thought", "search_thoughts", "get_entities", "get_connections"]
}
```

## Telegram Bot集成

支持通过Telegram Bot自然对话，Bot自动将对话内容存储到第二大脑。

## 适用场景

- AI长期记忆管理
- 项目经验积累
- 个人知识图谱
- 团队知识共享
- 跨会话上下文保持

## 参考项目

- mcp-second-brain: `\python\mcp-second-brain` (已下载)
- second-brain: `\python\second-brain` (已下载)
