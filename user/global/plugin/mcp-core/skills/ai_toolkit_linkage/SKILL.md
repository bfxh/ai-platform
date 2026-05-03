# AI工具联动系统 (ai_toolkit_linkage)

## 描述

多AI工具联动系统，支持链式执行、并行执行和智能路由，实现多模型协作。

## 功能

### 1. 链式执行 (Chain)
一个工具的输出作为下一个工具的输入，形成处理流水线。

### 2. 并行执行 (Parallel)
多个工具同时处理同一任务，结果合并输出。

### 3. 智能路由 (Route)
根据任务描述自动选择最佳工具。

## 工作流模板

### 内容创作
```json
{
  "type": "chain",
  "steps": [
    {"tool": "openai", "action": "generate_outline"},
    {"tool": "anthropic", "action": "expand_content"},
    {"tool": "openai", "action": "polish"}
  ]
}
```

### 代码审查
```json
{
  "type": "parallel",
  "tools": ["openai", "anthropic"],
  "merge_strategy": "concat"
}
```

### 研究分析
```json
{
  "type": "chain",
  "steps": [
    {"tool": "google", "action": "search_summarize"},
    {"tool": "anthropic", "action": "deep_analysis"},
    {"tool": "openai", "action": "generate_report"}
  ]
}
```

## 用法

### 命令行

```bash
# 链式执行
python /python/MCP_Core/skills/ai_toolkit_linkage/skill.py chain config.json

# 并行执行
python /python/MCP_Core/skills/ai_toolkit_linkage/skill.py parallel config.json

# 智能路由
python /python/MCP_Core/skills/ai_toolkit_linkage/skill.py route "分析代码" openai,anthropic

# 创建模板
python /python/MCP_Core/skills/ai_toolkit_linkage/skill.py template content_creation
```

### MCP 调用

```json
{
  "skill": "ai_toolkit_linkage",
  "action": "chain_execute",
  "params": {
    "task_config": {
      "steps": [
        {"tool": "openai", "action": "summarize"},
        {"tool": "anthropic", "action": "analyze"}
      ]
    }
  }
}
```

## 合并策略

- **concat**: 连接所有结果
- **best**: 选择最佳结果（最长）
- **vote**: 投票选择

## 输出

- 执行结果报告
- 执行时间统计
- 错误日志
