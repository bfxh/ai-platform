# AI工具包管理器 (ai_toolkit_manager)

## 描述

多AI工具兼容管理器，支持8+主流AI平台的兼容性检测、配置管理和统一适配器生成。

## 功能

### 1. 兼容性检测
- 自动检测已安装的AI工具包
- 检查版本兼容性
- 验证API密钥配置

### 2. 配置管理
- 为每个工具生成配置文件
- 统一管理多个AI工具配置
- 支持环境变量覆盖

### 3. 适配器生成
- 生成统一适配器代码
- 提供一致的API接口
- 支持动态工具切换

## 支持的AI工具

| 工具 | 提供商 | 功能 | 环境变量 |
|------|--------|------|----------|
| openai | OpenAI | GPT-4/3.5 | OPENAI_API_KEY |
| anthropic | Anthropic | Claude 3 | ANTHROPIC_API_KEY |
| google | Google | Gemini | GOOGLE_API_KEY |
| ollama | Local | 本地模型 | - |
| azure | Microsoft | Azure OpenAI | AZURE_OPENAI_API_KEY |
| huggingface | Hugging Face | 开源模型 | HUGGINGFACE_API_KEY |
| cohere | Cohere | Command系列 | COHERE_API_KEY |
| mistral | Mistral AI | Mistral系列 | MISTRAL_API_KEY |

## 用法

### 命令行

```bash
# 检查兼容性
python /python/MCP_Core/skills/ai_toolkit_manager/skill.py check_compat

# 列出所有工具
python /python/MCP_Core/skills/ai_toolkit_manager/skill.py list_tools

# 配置工具
python /python/MCP_Core/skills/ai_toolkit_manager/skill.py configure openai

# 生成适配器
python /python/MCP_Core/skills/ai_toolkit_manager/skill.py generate_adapter
```

### MCP 调用

```json
{
  "skill": "ai_toolkit_manager",
  "action": "check_compatibility",
  "params": {}
}
```

## 输出

- 兼容性检测报告
- 配置文件 (Config/<tool>_config.json)
- 统一适配器 (MCP_Core/adapters/unified_adapter.py)

## 依赖

- Python 3.8+
- 标准库 (os, json, subprocess, pathlib)

## 配置示例

```json
{
  "tool_id": "openai",
  "tool_name": "OpenAI",
  "configured_at": "2026-04-04T09:30:00",
  "config": {
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "default_model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```
