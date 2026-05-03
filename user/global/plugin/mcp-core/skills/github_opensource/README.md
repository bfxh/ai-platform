# GitHub 开源管理技能

## 功能说明

GitHub 开源管理技能是一个用于管理 GitHub 仓库、生成项目结构、配置文件和 CI/CD 流程的自动化工具。它提供了以下核心功能：

- **仓库管理**：生成 GitHub 仓库配置，包括名称、描述、许可证等
- **项目结构生成**：自动创建标准化的项目目录结构
- **配置文件生成**：生成 pyproject.toml、setup.py、.gitignore 等配置文件
- **文档生成**：生成 README.md、LICENSE 等文档文件
- **CI/CD 配置**：生成 GitHub Actions 工作流配置
- **项目同步**：初始化 Git 仓库并提供同步到 GitHub 的指南

## 参数定义

| 参数名 | 类型 | 必需 | 描述 | 枚举值 |
|-------|------|------|------|-------|
| action | string | 是 | 要执行的操作 | init, config, structure, sync, full, templates |
| project_name | string | 否 | 项目名称 | - |
| project_type | string | 否 | 项目类型 | ai_toolkit, mcp_framework, automation_tools |
| repo_path | string | 否 | 仓库路径 | - |

## 项目模板

技能提供了以下预定义的项目模板：

| 模板名称 | 描述 | 主题 |
|---------|------|------|
| ai_toolkit | AI 工具集合，包含 MCP 技能、工作流和自动化工具 | python, ai, mcp, automation, toolkit |
| mcp_framework | MCP (Model Control Protocol) 开发框架 | mcp, python, framework, protocol |
| automation_tools | 自动化工具集合 | automation, python, scripts, productivity |

## 推荐配置

技能使用以下推荐的开源配置：

- **许可证**：MIT
- **可见性**：public
- **包管理器**：pip
- **Python 版本**：3.10+
- **CI/CD**：GitHub Actions
- **文档**：Markdown
- **测试**：pytest

## 使用示例

### 1. 生成项目模板信息

```python
from skills.github_opensource.skill import GitHubOpenSourceManager

skill = GitHubOpenSourceManager()
result = skill.execute({"action": "templates"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "templates": {
    "ai_toolkit": {
      "name": "AI Toolkit",
      "description": "AI工具集合，包含MCP技能、工作流和自动化工具",
      "topics": ["python", "ai", "mcp", "automation", "toolkit"],
      "features": ["MCP Skills", "Workflows", "AI Integration", "CLI Tools"]
    },
    "mcp_framework": {
      "name": "MCP Framework",
      "description": "MCP (Model Control Protocol) 开发框架",
      "topics": ["mcp", "python", "framework", "protocol"],
      "features": ["MCP Server", "Skills System", "Workflow Engine"]
    },
    "automation_tools": {
      "name": "Automation Tools",
      "description": "自动化工具集合",
      "topics": ["automation", "python", "scripts", "productivity"],
      "features": ["Task Automation", "Script Templates", "Scheduling"]
    }
  }
}
```

### 2. 生成仓库配置

```python
from skills.github_opensource.skill import GitHubOpenSourceManager

skill = GitHubOpenSourceManager()
result = skill.execute({"action": "config"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "repo_config": {
    "name": "ai-toolkit-ai_toolkit",
    "description": "AI工具集合，包含MCP技能、工作流和自动化工具",
    "private": false,
    "auto_init": true,
    "gitignore_template": "Python",
    "license_template": "MIT",
    "topics": ["python", "ai", "mcp", "automation", "toolkit"],
    "has_issues": true,
    "has_wiki": true,
    "has_projects": true
  }
}
```

### 3. 生成完整项目

```python
from skills.github_opensource.skill import GitHubOpenSourceManager

skill = GitHubOpenSourceManager()
result = skill.execute({"action": "full", "project_name": "my-ai-project", "project_type": "ai_toolkit"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "project_path": "/python\\GitHub\\my-ai-project",
    "repo_config": {
      "name": "ai-toolkit-ai_toolkit",
      "description": "AI工具集合，包含MCP技能、工作流和自动化工具",
      "private": false,
      "auto_init": true,
      "gitignore_template": "Python",
      "license_template": "MIT",
      "topics": ["python", "ai", "mcp", "automation", "toolkit"],
      "has_issues": true,
      "has_wiki": true,
      "has_projects": true
    }
  }
}
```

## 项目结构

生成的项目结构如下：

```
project-name/
├── src/
│   └── project-name/
│       └── __init__.py
├── tests/
│   └── test_project-name.py
├── docs/
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── setup.py
├── README.md
├── LICENSE
└── .gitignore
```

## 配置文件

### 1. pyproject.toml

包含项目的构建系统配置、依赖项、脚本等。

### 2. setup.py

传统的 setup.py 文件，用于项目安装和配置。

### 3. GitHub Actions 配置

包含测试、构建和发布的 CI/CD 流程配置。

### 4. README.md

包含项目的详细文档，包括特性、安装方法、使用示例等。

### 5. LICENSE

MIT 许可证文件。

### 6. .gitignore

标准的 Python 项目 .gitignore 文件。

## 环境变量

技能使用以下环境变量：

- **AI_ROOT**：AI 项目的根目录，默认为 "/python"

## 依赖项

- **Python 3.10+**
- **Git**（用于仓库同步）

## 注意事项

1. 在使用 `sync` 操作时，需要确保系统已安装 Git
2. 生成的项目需要手动在 GitHub 上创建仓库并添加远程仓库
3. 对于发布到 PyPI，需要在 GitHub Actions 中设置 PYPI_API_TOKEN 密钥

## 扩展开发

如果需要扩展技能功能，可以：

1. 在 `PROJECT_TEMPLATES` 中添加新的项目模板
2. 在 `RECOMMENDED_SETTINGS` 中修改推荐配置
3. 扩展 `generate_*` 方法以支持更多文件类型
4. 添加新的操作类型到 `execute` 方法

## 故障排除

### 常见问题

1. **Git 未安装**：安装 Git 并确保它在系统路径中
2. **权限不足**：确保对目标目录有写入权限
3. **路径不存在**：技能会自动创建必要的目录结构

### 错误处理

技能包含错误处理机制，会捕获并记录执行过程中的错误，并在返回结果中包含错误信息。

## 版本历史

- **1.0.0**：初始版本，包含基本的项目生成和配置功能

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个技能！
