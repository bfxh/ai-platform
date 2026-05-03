---
name: "local-llm-engine"
description: "本地LLM引擎技能，集成Ollama/LocalAI/Jan等本地推理能力。Invoke when user needs local LLM inference, model management, or wants to run AI models offline."
---

# 本地LLM引擎技能

## 概述

集成多种本地LLM推理引擎，实现完全离线的AI模型运行能力。

## 支持的引擎

| 引擎 | Stars | 特点 |
|------|-------|------|
| **Ollama** | 167K | 最快上手，一行命令运行模型 |
| **LocalAI** | 30K+ | OpenAI API兼容，35+后端，无需GPU |
| **Jan** | 40K+ | 桌面应用，完全离线ChatGPT体验 |
| **GPT4All** | 75K+ | 新手友好，本地RAG |
| **AnythingLLM** | 30K+ | 一键安装，本地默认，无需账号 |
| **PrivateGPT** | 55K+ | 完全离线，隐私优先 |

## 与您系统的映射

| 引擎能力 | 您的系统 |
|---------|---------|
| Ollama服务 | 已集成 (端口11434) |
| VCPToolBox API桥接 | 已集成 (端口6005) |
| WS Bridge | 已集成 (端口11436) |
| 模型管理 | qwen2.5-coder + deepseek-coder |

## 使用方法

### 模型管理
```bash
# Ollama - 拉取模型
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder:6.7b

# LocalAI - 兼容OpenAI API
curl http://localhost:8080/v1/chat/completions
```

### API桥接
```python
# 通过VCPToolBox桥接 (已部署)
# 端口6005: OpenAI兼容API
# 端口6006: 管理面板
```

## 适用场景

- 完全离线AI推理
- 数据隐私保护
- 无网络环境AI使用
- 本地模型微调