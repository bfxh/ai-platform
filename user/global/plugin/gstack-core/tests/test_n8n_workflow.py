#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
n8n Workflow 单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径

# 导入 n8n Workflow Skill
from ..skill import N8nWorkflowSkill


class TestN8nWorkflow:
    """n8n Workflow 测试类"""

    def setup_method(self):
        """测试前设置"""
        self.n8n_skill = N8nWorkflowSkill()

    def test_initialization(self):
        """测试 n8n Workflow 初始化"""
        assert self.n8n_skill is not None
        assert self.n8n_skill.server_url == "http://localhost:5678"

    def test_config_loading(self):
        """测试配置加载"""
        assert self.n8n_skill.n8n_dir is not None
        assert self.n8n_skill.compose_file is not None

    def test_status_check(self):
        """测试状态检查"""
        # 服务可能离线，这是预期的
        status = self.n8n_skill.status()
        assert isinstance(status, bool)

    def test_list_workflows(self):
        """测试列出工作流"""
        workflows = self.n8n_skill.list_workflows()
        assert isinstance(workflows, list)

    def test_execute_status(self):
        """测试 execute 函数 status 命令"""
        from ..skill import execute
        result = execute("status")
        assert result is not None
        assert "success" in result
        assert result["success"] == True
        assert "data" in result
        assert "status" in result["data"]

    def test_execute_trigger_no_workflow(self):
        """测试 execute 函数 trigger 不指定工作流"""
        from ..skill import execute
        result = execute("trigger")
        assert result is not None
        assert result.get("success") == True
        assert "workflows" in result.get("data", {})

    def test_execute_unknown_command(self):
        """测试执行未知命令"""
        from ..skill import execute
        result = execute("unknown_command")
        assert result is not None
        assert result.get("success") == False


class TestN8nWorkflowConfig:
    """n8n Workflow 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        skill = N8nWorkflowSkill()
        assert skill.server_url == "http://localhost:5678"

    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = {
            "server_url": "http://localhost:9999",
            "n8n_dir": "C:\\Custom\\n8n"
        }
        skill = N8nWorkflowSkill(custom_config)
        assert skill.server_url == "http://localhost:9999"


class TestN8nWorkflowDocker:
    """n8n Workflow Docker 检测测试"""

    def test_docker_detection(self):
        """测试 Docker 检测"""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            docker_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            docker_available = False

        # 如果 Docker 不可用，测试应该跳过或给出警告
        if not docker_available:
            print("⚠️ Docker 不可用，某些测试将被跳过")


def run_tests():
    """运行所有测试"""
    test_instance = TestN8nWorkflow()

    print("运行 n8n Workflow 测试...")
    print("=" * 50)

    # 测试初始化
    try:
        test_instance.setup_method()
        test_instance.test_initialization()
        print("✅ test_initialization 通过")
    except Exception as e:
        print(f"❌ test_initialization 失败: {e}")

    # 测试配置加载
    try:
        test_instance.setup_method()
        test_instance.test_config_loading()
        print("✅ test_config_loading 通过")
    except Exception as e:
        print(f"❌ test_config_loading 失败: {e}")

    # 测试状态检查
    try:
        test_instance.setup_method()
        test_instance.test_status_check()
        print("✅ test_status_check 通过")
    except Exception as e:
        print(f"❌ test_status_check 失败: {e}")

    # 测试列出工作流
    try:
        test_instance.setup_method()
        test_instance.test_list_workflows()
        print("✅ test_list_workflows 通过")
    except Exception as e:
        print(f"❌ test_list_workflows 失败: {e}")

    # 测试 execute status
    try:
        test_instance.setup_method()
        test_instance.test_execute_status()
        print("✅ test_execute_status 通过")
    except Exception as e:
        print(f"❌ test_execute_status 失败: {e}")

    # 测试 execute trigger
    try:
        test_instance.setup_method()
        test_instance.test_execute_trigger_no_workflow()
        print("✅ test_execute_trigger_no_workflow 通过")
    except Exception as e:
        print(f"❌ test_execute_trigger_no_workflow 失败: {e}")

    # 测试未知命令
    try:
        test_instance.setup_method()
        test_instance.test_execute_unknown_command()
        print("✅ test_execute_unknown_command 通过")
    except Exception as e:
        print(f"❌ test_execute_unknown_command 失败: {e}")

    # 测试默认配置
    try:
        TestN8nWorkflowConfig().test_default_config()
        print("✅ test_default_config 通过")
    except Exception as e:
        print(f"❌ test_default_config 失败: {e}")

    # 测试自定义配置
    try:
        TestN8nWorkflowConfig().test_custom_config()
        print("✅ test_custom_config 通过")
    except Exception as e:
        print(f"❌ test_custom_config 失败: {e}")

    print("=" * 50)
    print("n8n Workflow 测试完成")


if __name__ == "__main__":
    run_tests()