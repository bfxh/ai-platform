# 项目文档自动生成系统

## 功能
分析项目目录结构，自动生成 `.PROJECT.md` 文档，包含：
- 基本信息（技术栈、语言、源码管理）
- 架构设计（模块、数据流、依赖）
- 功能清单（含 TODO 提取）
- 安装/构建指南
- 测试方法
- 维护记录

## 原则
**每个项目必须有对应的 .PROJECT.md 文档**，文档随项目走，记录所有重要信息。

## 使用
```bash
python /python/MCP_Core/skills/project_doc_generator/skill.py <项目路径>

# 示例
python /python/MCP_Core/skills/project_doc_generator/skill.py /python/MCP_Core
python /python/MCP_Core/skills/project_doc_generator/skill.py %SOFTWARE_DIR%/LLQ/browser-use-main
```
