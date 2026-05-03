#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 开源管理技能测试
"""

import sys
import tempfile
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.github_opensource.skill import GitHubOpenSourceManager


class TestGitHubOpenSourceManager:
    """GitHub 开源管理技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return GitHubOpenSourceManager()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "github_opensource"
        assert skill.version == "1.0.0"
        assert (
            skill.description
            == "GitHub开源管理 - 仓库管理、配置优化、自动发布、文档生成、CI/CD配置"
        )

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "project_name" in params
        assert "project_type" in params
        assert "repo_path" in params

        # 检查 action 枚举值
        assert params["action"]["required"] is True
        assert "init" in params["action"]["enum"]
        assert "config" in params["action"]["enum"]
        assert "structure" in params["action"]["enum"]
        assert "sync" in params["action"]["enum"]
        assert "full" in params["action"]["enum"]
        assert "templates" in params["action"]["enum"]

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params({"action": "templates"})
        assert valid is True
        assert error is None

    def test_generate_repo_config(self, skill):
        """测试生成仓库配置"""
        config = skill.generate_repo_config()

        assert "name" in config
        assert "description" in config
        assert "private" in config
        assert "auto_init" in config
        assert "gitignore_template" in config
        assert "license_template" in config
        assert "topics" in config
        assert "has_issues" in config
        assert "has_wiki" in config
        assert "has_projects" in config

    def test_generate_pyproject_toml(self, skill):
        """测试生成 pyproject.toml"""
        content = skill.generate_pyproject_toml("test-project", "Test Project")

        assert "[build-system]" in content
        assert "[project]" in content
        assert 'name = "test-project"' in content
        assert 'description = "Test Project"' in content

    def test_generate_setup_py(self, skill):
        """测试生成 setup.py"""
        content = skill.generate_setup_py("test-project")

        assert "from setuptools import setup, find_packages" in content
        assert 'name="test-project"' in content

    def test_generate_github_actions(self, skill):
        """测试生成 GitHub Actions 配置"""
        content = skill.generate_github_actions("test-project")

        assert "name: CI/CD" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "test:" in content
        assert "build:" in content
        assert "release:" in content

    def test_generate_readme(self, skill):
        """测试生成 README.md"""
        content = skill.generate_readme("test-project", "Test Project", ["Feature 1", "Feature 2"])

        assert "# test-project" in content
        assert "Test Project" in content
        assert "- Feature 1" in content
        assert "- Feature 2" in content

    def test_generate_license(self, skill):
        """测试生成 MIT 许可证"""
        content = skill.generate_license(2024)

        assert "MIT License" in content
        assert "Copyright (c) 2024 Your Name" in content

    def test_generate_gitignore(self, skill):
        """测试生成 .gitignore"""
        content = skill.generate_gitignore()

        assert "__pycache__/" in content
        assert "*.py[cod]" in content
        assert "build/" in content
        assert "dist/" in content

    def test_create_project_structure(self, skill):
        """测试创建项目结构"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = skill.create_project_structure("test-project", temp_dir)

            # 检查目录结构
            assert (project_path / "src" / "test-project").exists()
            assert (project_path / "tests").exists()
            assert (project_path / "docs").exists()
            assert (project_path / ".github" / "workflows").exists()

            # 检查文件
            assert (project_path / "pyproject.toml").exists()
            assert (project_path / "setup.py").exists()
            assert (project_path / "README.md").exists()
            assert (project_path / "LICENSE").exists()
            assert (project_path / ".gitignore").exists()
            assert (project_path / ".github" / "workflows" / "ci.yml").exists()
            assert (project_path / "src" / "test-project" / "__init__.py").exists()
            assert (project_path / "tests" / "test_test-project.py").exists()

    def test_execute_templates(self, skill):
        """测试执行 templates 操作"""
        result = skill.execute({"action": "templates"})

        assert result["success"] is True
        assert "templates" in result
        assert isinstance(result["templates"], dict)

    def test_execute_config(self, skill):
        """测试执行 config 操作"""
        result = skill.execute({"action": "config"})

        assert result["success"] is True
        assert "repo_config" in result

    def test_execute_invalid_action(self, skill):
        """测试执行无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result
