# GitHub 开源管理系统 (github_opensource)

## 描述

GitHub开源管理系统，支持项目初始化、配置优化、自动发布和CI/CD配置。

## 功能

### 1. 项目初始化
- 生成标准Python项目结构
- 创建pyproject.toml和setup.py
- 生成README.md和LICENSE
- 配置.gitignore

### 2. CI/CD 配置
- GitHub Actions工作流
- 自动测试 (pytest)
- 代码质量检查 (black, ruff)
- PyPI自动发布

### 3. 项目模板
- **ai_toolkit**: AI工具集合
- **mcp_framework**: MCP开发框架
- **automation_tools**: 自动化工具

## 用法

### 命令行

```bash
# 初始化新项目
python /python/MCP_Core/skills/github_opensource/skill.py init my_project

# 生成仓库配置
python /python/MCP_Core/skills/github_opensource/skill.py config ai_toolkit

# 创建项目结构
python /python/MCP_Core/skills/github_opensource/skill.py structure my_project

# 生成完整项目
python /python/MCP_Core/skills/github_opensource/skill.py full my_project ai_toolkit

# 同步到GitHub
python /python/MCP_Core/skills/github_opensource/skill.py sync /python/GitHub/my_project

# 查看可用模板
python /python/MCP_Core/skills/github_opensource/skill.py templates
```

### MCP 调用

```json
{
  "skill": "github_opensource",
  "action": "generate_full_project",
  "params": {
    "project_name": "my_project",
    "project_type": "ai_toolkit"
  }
}
```

## 生成的文件

### pyproject.toml
- 构建系统配置
- 项目元数据
- 依赖管理
- 开发工具配置

### setup.py
- 传统安装配置
- 入口点定义
- 分类器配置

### GitHub Actions (ci.yml)
- 多版本Python测试
- 代码格式检查
- 自动构建和发布

### README.md
- 项目徽章
- 安装说明
- 使用示例
- 开发指南

## 项目模板

### ai_toolkit
```python
{
  "name": "AI Toolkit",
  "description": "AI工具集合，包含MCP技能、工作流和自动化工具",
  "topics": ["python", "ai", "mcp", "automation", "toolkit"],
  "features": ["MCP Skills", "Workflows", "AI Integration", "CLI Tools"]
}
```

### mcp_framework
```python
{
  "name": "MCP Framework",
  "description": "MCP (Model Control Protocol) 开发框架",
  "topics": ["mcp", "python", "framework", "protocol"],
  "features": ["MCP Server", "Skills System", "Workflow Engine"]
}
```

### automation_tools
```python
{
  "name": "Automation Tools",
  "description": "自动化工具集合",
  "topics": ["automation", "python", "scripts", "productivity"],
  "features": ["Task Automation", "Script Templates", "Scheduling"]
}
```

## 输出

- 完整项目结构
- 配置文件
- CI/CD工作流
- 项目文档

## 依赖

- Python 3.10+
- Git
- 标准库 (os, json, subprocess, pathlib)
