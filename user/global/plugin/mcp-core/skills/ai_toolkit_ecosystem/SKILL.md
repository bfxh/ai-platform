# AI工具生态系统 (ai_toolkit_ecosystem)

## 描述

多AI工具生态系统，提供工具市场、插件系统和智能推荐功能。

## 功能

### 1. 工具市场
- 浏览可用AI工具
- 查看工具详情和评分
- 一键安装工具

### 2. 插件系统
- 创建插件模板
- 管理插件生命周期
- 扩展系统功能

### 3. 智能推荐
- 根据任务推荐工具
- 关键词匹配
- 热度排序

## 工具分类

### Core (核心)
- OpenAI (GPT-4/3.5)
- Anthropic Claude
- Google Gemini

### Local (本地)
- Ollama
- llama.cpp
- Hugging Face Transformers

### Specialized (专业)
- LangChain (应用框架)
- LlamaIndex (数据索引)
- AutoGen (多智能体)

## 用法

### 命令行

```bash
# 列出工具市场
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py list
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py list core

# 安装工具
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py install openai

# 查看统计
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py stats

# 推荐工具
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py recommend "代码辅助"

# 搜索工具
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py search "local"

# 创建插件
python /python/MCP_Core/skills/ai_toolkit_ecosystem/skill.py create_plugin my_plugin
```

### MCP 调用

```json
{
  "skill": "ai_toolkit_ecosystem",
  "action": "recommend_tools",
  "params": {
    "task_description": "文本生成"
  }
}
```

## 任务推荐映射

| 任务类型 | 推荐工具 |
|----------|----------|
| 文本生成 | openai, anthropic, google |
| 代码辅助 | openai, anthropic, ollama |
| 数据分析 | anthropic, openai, llamaindex |
| 文档处理 | llamaindex, langchain, anthropic |
| 本地部署 | ollama, llamacpp, transformers |
| 多智能体 | autogen, langchain, openai |
| 知识库 | llamaindex, langchain, anthropic |
| 图像理解 | openai, google, anthropic |

## 输出

- 工具市场列表
- 安装报告
- 生态统计
- 插件模板
