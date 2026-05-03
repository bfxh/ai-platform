---
name: "ragflow-knowledge"
description: "RAGFlow知识库技能，基于RAG引擎构建专业文档问答系统。Invoke when user needs document Q&A, knowledge base, or RAG-powered search."
---

# RAGFlow知识库技能

## 概述

基于RAGFlow(77K Stars)和Dify(135K Stars)的RAG能力，构建专业文档问答和知识检索系统。

## 核心平台对比

| 平台 | Stars | 定位 | 特点 |
|------|-------|------|------|
| **RAGFlow** | 77K | RAG引擎 | 深度检索+Agent，文件解析强 |
| **Dify** | 135K | LLM应用平台 | 可视化配置，知识库成熟 |
| **LangChain-Chatchat** | 30K+ | 中文知识库 | 中文优化，本地问答 |
| **AnythingLLM** | 30K+ | 全能文档 | 一键安装，本地优先 |
| **PrivateGPT** | 55K+ | 隐私文档 | 完全离线，敏感文档 |

## 与您系统的映射

| RAG能力 | 您的系统 |
|---------|---------|
| 文档解析 | storage/mcp/Tools/ |
| 向量嵌入 | Ollama本地模型 |
| 知识检索 | core/knowledge_manager.py |
| 复利知识系统 | user/knowledge/ |

## 使用方法

### 构建知识库
```python
# 导入文档
knowledge.import_documents(
    path="D:\\docs",
    formats=["pdf", "docx", "txt", "md"]
)

# 语义搜索
results = knowledge.search("项目架构设计")
```

### 与复利知识系统集成
```python
# 四步工作流
knowledge.ingest(raw_data)     # 摄取
knowledge.digest(processed)    # 消化
knowledge.output(insights)     # 输出
knowledge.inspect(quality)     # 巡检
```

## 适用场景

- 项目文档问答
- 技术知识库
- 合同审查
- 行业报告分析