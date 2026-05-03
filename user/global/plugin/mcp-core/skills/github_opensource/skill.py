#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 开源管理系统
GitHub Open Source Management System

功能:
- GitHub仓库管理
- 开源配置和优化
- 自动发布
- 项目文档生成
- CI/CD 配置

用法:
    python github_opensource.py init <repo_name>
    python github_opensource.py config
    python github_opensource.py publish
    python github_opensource.py update_docs
"""

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill, handle_errors

# 跨平台路径处理
import platform

# 获取用户主目录作为默认根目录
if platform.system() == "Windows":
    AI_ROOT = Path(os.environ.get("AI_ROOT", os.path.expanduser("~")))
else:
    AI_ROOT = Path(os.environ.get("AI_ROOT", os.path.expanduser("~")))

# 确保路径格式正确
AI_ROOT = AI_ROOT / "AI" if "AI" not in str(AI_ROOT) else AI_ROOT
GITHUB_CONFIG_DIR = AI_ROOT / "Config" / "github"


@dataclass
class GitHubRepo:
    """GitHub仓库信息"""

    name: str
    description: str
    private: bool
    auto_init: bool
    gitignore_template: str
    license_template: str
    topics: List[str]
    has_issues: bool
    has_wiki: bool
    has_projects: bool


class GitHubOpenSourceManager(Skill):
    """GitHub开源管理器"""

    # 技能元数据
    name = "github_opensource"
    description = "GitHub开源管理 - 仓库管理、配置优化、自动发布、文档生成、CI/CD配置"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "github_opensource"

    # 开源项目模板配置
    PROJECT_TEMPLATES = {
        "ai_toolkit": {
            "name": "AI Toolkit",
            "description": "AI工具集合，包含MCP技能、工作流和自动化工具",
            "topics": ["python", "ai", "mcp", "automation", "toolkit"],
            "features": ["MCP Skills", "Workflows", "AI Integration", "CLI Tools"],
        },
        "mcp_framework": {
            "name": "MCP Framework",
            "description": "MCP (Model Control Protocol) 开发框架",
            "topics": ["mcp", "python", "framework", "protocol"],
            "features": ["MCP Server", "Skills System", "Workflow Engine"],
        },
        "automation_tools": {
            "name": "Automation Tools",
            "description": "自动化工具集合",
            "topics": ["automation", "python", "scripts", "productivity"],
            "features": ["Task Automation", "Script Templates", "Scheduling"],
        },
    }

    # 推荐的开源配置
    RECOMMENDED_SETTINGS = {
        "license": "MIT",
        "visibility": "public",
        "package_manager": "pip",
        "python_version": "3.10",
        "ci_cd": ["github-actions"],
        "documentation": "markdown",
        "testing": "pytest",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.config: Dict[str, Any] = self._load_config()
        GITHUB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_file = GITHUB_CONFIG_DIR / "config.json"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self) -> None:
        """保存配置"""
        config_file = GITHUB_CONFIG_DIR / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def generate_repo_config(self, project_type: str = "ai_toolkit") -> Dict[str, Any]:
        """生成仓库配置"""
        print("\n" + "=" * 60)
        print("生成 GitHub 仓库配置")
        print("=" * 60 + "\n")

        template = self.PROJECT_TEMPLATES.get(project_type, self.PROJECT_TEMPLATES["ai_toolkit"])

        repo_config = {
            "name": f"ai-toolkit-{project_type}",
            "description": template["description"],
            "private": False,
            "auto_init": True,
            "gitignore_template": "Python",
            "license_template": "MIT",
            "topics": template["topics"],
            "has_issues": True,
            "has_wiki": True,
            "has_projects": True,
        }

        print(f"仓库名称: {repo_config['name']}")
        print(f"描述: {repo_config['description']}")
        print(f"主题: {', '.join(repo_config['topics'])}")
        print(f"许可证: {repo_config['license_template']}")
        print()

        return repo_config

    def generate_pyproject_toml(self, project_name: str, description: str) -> str:
        """生成 pyproject.toml"""
        content = f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "1.0.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.10"
license = {{text = "MIT"}}
authors = [
    {{name = "Your Name", email = "your.email@example.com"}}
]
keywords = ["ai", "mcp", "toolkit"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "requests>=2.28.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
my_cli = "{project_name}.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 100
target-version = ["py310", "py311"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
"""
        return content

    def generate_setup_py(self, project_name: str) -> str:
        """生成 setup.py"""
        content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="1.0.0",
    description="AI Toolkit Component",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/{project_name}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28.0",
        "click>=8.0.0",
    ],
    extras_require={{
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    }},
    entry_points={{
        "console_scripts": [
            "{project_name}={{project_name}}.cli:main",
        ],
    }},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
"""
        return content

    def generate_github_actions(self, project_name: str) -> str:
        """生成 GitHub Actions CI/CD 配置"""
        workflow_content = f"""name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python {{ {{ matrix.python-version }} }}
      uses: actions/setup-python@v5
      with:
        python-version: {{ {{ matrix.python-version }} }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=src tests/
    
    - name: Run linting
      run: |
        ruff check src/
        black --check src/

  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
    
    - name: Build package
      run: |
        python -m pip install build
        python -m build
    
    - name: Publish to PyPI
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}

  release:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/*
        generate_release_notes: true
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""
        return workflow_content

    def generate_readme(self, project_name: str, description: str, features: List[str]) -> str:
        """生成 README.md"""
        features_list = "\n".join([f"- {f}" for f in features])

        readme = f"""# {project_name}

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

{description}

## ✨ 特性

{features_list}

## 📦 安装

```bash
# 从 PyPI 安装
pip install {project_name}

# 从源码安装
git clone https://github.com/yourusername/{project_name}.git
cd {project_name}
pip install -e .
```

## 🚀 快速开始

```python
import {project_name}

# 使用示例
result = {project_name}.process("your input")
print(result)
```

## 📚 文档

详细的文档请访问 [Wiki](https://github.com/yourusername/{project_name}/wiki)

## 🔧 开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/{project_name}.git
cd {project_name}

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化和检查
black src/
ruff check src/
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- MCP (Model Control Protocol)
- Python Community
"""
        return readme

    def generate_license(self, year: int = None) -> str:
        """生成 MIT 许可证"""
        if year is None:
            year = datetime.now().year

        license_text = f"""MIT License

Copyright (c) {year} Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
        return license_text

    def generate_gitignore(self) -> str:
        """生成 .gitignore"""
        gitignore = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
logs/
*.log
temp/
cache/
*.tmp
"""
        return gitignore

    def create_project_structure(self, project_name: str, output_dir: str = None) -> Path:
        """创建项目结构"""
        if output_dir is None:
            output_dir = AI_ROOT / "GitHub" / project_name

        project_path = Path(output_dir)
        project_path.mkdir(parents=True, exist_ok=True)

        # 创建目录结构
        directories = [
            project_path / "src" / project_name,
            project_path / "tests",
            project_path / "docs",
            project_path / ".github" / "workflows",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # 生成配置文件
        configs = {
            "pyproject.toml": self.generate_pyproject_toml(project_name, "AI Toolkit Component"),
            "setup.py": self.generate_setup_py(project_name),
            "README.md": self.generate_readme(
                project_name, "AI Toolkit Component", ["MCP Skills", "CLI Tools"]
            ),
            "LICENSE": self.generate_license(),
            ".gitignore": self.generate_gitignore(),
            ".github/workflows/ci.yml": self.generate_github_actions(project_name),
        }

        for filename, content in configs.items():
            file_path = project_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"创建: {filename}")

        # 创建 __init__.py
        init_file = project_path / "src" / project_name / "__init__.py"
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f'''"""AI Toolkit - {project_name}"""

__version__ = "1.0.0"
''')

        # 创建测试文件
        test_file = project_path / "tests" / f"test_{project_name}.py"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(f'''"""Tests for {project_name}"""

import pytest
from {project_name} import __version__


def test_version():
    """Test version is set correctly."""
    assert __version__ == "1.0.0"
''')

        print(f"\n项目结构已创建: {project_path}")
        return project_path

    def sync_to_github(self, repo_path: Path, repo_name: str = None) -> bool:
        """同步到GitHub"""
        print("\n" + "=" * 60)
        print("同步到 GitHub")
        print("=" * 60 + "\n")

        if repo_name is None:
            repo_name = repo_path.name

        # 检查git是否安装
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
        except:
            print("错误: Git 未安装")
            return False

        # 初始化git仓库
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            # 检查是否已经是git仓库
            subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, check=True)
            print("Git仓库已存在")
        except:
            try:
                subprocess.run(["git", "init"], check=True, cwd=repo_path)
                subprocess.run(["git", "add", "."], check=True, cwd=repo_path)
                subprocess.run(
                    ["git", "commit", "-m", "Initial commit - AI Toolkit"],
                    check=True,
                    cwd=repo_path,
                )
                print("Git仓库已初始化")
            except Exception as e:
                print(f"Git操作失败: {e}")
        finally:
            os.chdir(original_cwd)

        print("\n下一步操作:")
        print(f"1. 在 GitHub 上创建仓库: {repo_name}")
        print(f"2. 添加远程仓库:")
        print(f"   git remote add origin https://github.com/yourusername/{repo_name}.git")
        print(f"3. 推送代码:")
        print(f"   git push -u origin main")

        return True

    def generate_full_project(self, project_name: str, project_type: str = "ai_toolkit") -> Dict:
        """生成完整项目"""
        print("\n" + "=" * 60)
        print("生成完整开源项目")
        print("=" * 60 + "\n")

        template = self.PROJECT_TEMPLATES.get(project_type, self.PROJECT_TEMPLATES["ai_toolkit"])

        # 创建项目结构
        project_path = self.create_project_structure(project_name)

        # 生成配置
        repo_config = self.generate_repo_config(project_type)

        # 保存配置
        config_file = GITHUB_CONFIG_DIR / f"{project_name}_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "project_name": project_name,
                    "project_type": project_type,
                    "template": template,
                    "repo_config": repo_config,
                    "created_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n配置已保存: {config_file}")

        # 同步到Git
        self.sync_to_github(project_path, project_name)

        return {"project_path": str(project_path), "repo_config": repo_config}

    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "enum": ["init", "config", "structure", "sync", "full", "templates"],
                "description": "操作类型",
            },
            "project_name": {"type": "string", "required": False, "description": "项目名称"},
            "project_type": {
                "type": "string",
                "required": False,
                "default": "ai_toolkit",
                "description": "项目类型",
            },
            "repo_path": {"type": "string", "required": False, "description": "仓库路径"},
        }

    @handle_errors
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        action = params.get("action")
        project_name = params.get("project_name")
        project_type = params.get("project_type", "ai_toolkit")
        repo_path = params.get("repo_path")

        if action == "init" and project_name:
            result = self.generate_full_project(project_name, project_type)
            return {"success": True, "result": result}
        elif action == "config":
            repo_config = self.generate_repo_config(project_type)
            return {"success": True, "repo_config": repo_config}
        elif action == "structure" and project_name:
            project_path = self.create_project_structure(project_name)
            return {"success": True, "project_path": str(project_path)}
        elif action == "sync" and repo_path:
            success = self.sync_to_github(Path(repo_path))
            return {"success": success}
        elif action == "full" and project_name:
            result = self.generate_full_project(project_name, project_type)
            return {"success": True, "result": result}
        elif action == "templates":
            templates = {}
            for key, template in self.PROJECT_TEMPLATES.items():
                templates[key] = template
            return {"success": True, "templates": templates}
        else:
            return {"success": False, "error": "无效的操作或参数不足"}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python github_opensource.py <命令>")
        print("命令:")
        print("  init <project_name>       初始化新项目")
        print("  config [project_type]     生成仓库配置")
        print("  structure <name>         创建项目结构")
        print("  sync <path>             同步到GitHub")
        print("  full <name> [type]      生成完整项目")
        print("  templates               列出项目模板")
        return

    manager = GitHubOpenSourceManager()
    command = sys.argv[1]

    if command == "init" and len(sys.argv) >= 3:
        project_name = sys.argv[2]
        manager.generate_full_project(project_name)

    elif command == "config":
        project_type = sys.argv[2] if len(sys.argv) >= 3 else "ai_toolkit"
        manager.generate_repo_config(project_type)

    elif command == "structure" and len(sys.argv) >= 3:
        project_name = sys.argv[2]
        manager.create_project_structure(project_name)

    elif command == "sync" and len(sys.argv) >= 3:
        repo_path = Path(sys.argv[2])
        manager.sync_to_github(repo_path)

    elif command == "full" and len(sys.argv) >= 3:
        project_name = sys.argv[2]
        project_type = sys.argv[3] if len(sys.argv) >= 4 else "ai_toolkit"
        manager.generate_full_project(project_name, project_type)

    elif command == "templates":
        print("\n可用模板:")
        for key, template in manager.PROJECT_TEMPLATES.items():
            print(f"\n{key}:")
            print(f"  名称: {template['name']}")
            print(f"  描述: {template['description']}")
            print(f"  主题: {', '.join(template['topics'])}")

    else:
        print(f"未知命令或参数不足: {command}")


if __name__ == "__main__":
    main()
