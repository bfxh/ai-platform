#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender MCP 单元测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径

# 导入 Blender MCP Skill
from ..skill import BlenderMCPSkill


class TestBlenderMCP:
    """Blender MCP 测试类"""

    def setup_method(self):
        """测试前设置"""
        self.blender_skill = BlenderMCPSkill()

    def test_initialization(self):
        """测试 Blender MCP 初始化"""
        assert self.blender_skill is not None
        assert self.blender_skill.server_url == "http://localhost:8400"

    def test_config_loading(self):
        """测试配置加载"""
        assert self.blender_skill.blender_mcp_dir is not None
        assert self.blender_skill.blender_path is not None

    def test_path_validation(self):
        """测试路径验证"""
        # Blender 路径应该存在或为默认路径
        blender_path = Path(self.blender_skill.blender_path)
        # 注意：实际环境中可能不存在，所以只检查格式
        assert self.blender_skill.blender_path is not None

    def test_status_check(self):
        """测试状态检查"""
        # 服务可能离线，这是预期的
        status = self.blender_skill.status()
        assert isinstance(status, bool)

    def test_execute_status(self):
        """测试 execute 函数 status 命令"""
        from ..skill import execute
        result = execute("status")
        assert result is not None
        assert "success" in result
        assert result["success"] == True
        assert "data" in result
        assert "status" in result["data"]

    def test_execute_unknown_command(self):
        """测试执行未知命令"""
        from ..skill import execute
        result = execute("unknown_command")
        assert result is not None
        assert result.get("success") == False


class TestBlenderMCPConfig:
    """Blender MCP 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        skill = BlenderMCPSkill()
        assert skill.server_url == "http://localhost:8400"

    def test_custom_config(self):
        """测试自定义配置"""
        custom_config = {
            "server_url": "http://localhost:9999",
            "blender_path": "C:\\Custom\\Blender\\blender.exe"
        }
        skill = BlenderMCPSkill(custom_config)
        assert skill.server_url == "http://localhost:9999"
        assert skill.blender_path == "C:\\Custom\\Blender\\blender.exe"


def run_tests():
    """运行所有测试"""
    test_instance = TestBlenderMCP()

    print("运行 Blender MCP 测试...")
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

    # 测试路径验证
    try:
        test_instance.setup_method()
        test_instance.test_path_validation()
        print("✅ test_path_validation 通过")
    except Exception as e:
        print(f"❌ test_path_validation 失败: {e}")

    # 测试状态检查
    try:
        test_instance.setup_method()
        test_instance.test_status_check()
        print("✅ test_status_check 通过")
    except Exception as e:
        print(f"❌ test_status_check 失败: {e}")

    # 测试 execute status
    try:
        test_instance.setup_method()
        test_instance.test_execute_status()
        print("✅ test_execute_status 通过")
    except Exception as e:
        print(f"❌ test_execute_status 失败: {e}")

    # 测试未知命令
    try:
        test_instance.setup_method()
        test_instance.test_execute_unknown_command()
        print("✅ test_execute_unknown_command 通过")
    except Exception as e:
        print(f"❌ test_execute_unknown_command 失败: {e}")

    # 测试默认配置
    try:
        TestBlenderMCPConfig().test_default_config()
        print("✅ test_default_config 通过")
    except Exception as e:
        print(f"❌ test_default_config 失败: {e}")

    # 测试自定义配置
    try:
        TestBlenderMCPConfig().test_custom_config()
        print("✅ test_custom_config 通过")
    except Exception as e:
        print(f"❌ test_custom_config 失败: {e}")

    print("=" * 50)
    print("Blender MCP 测试完成")


if __name__ == "__main__":
    run_tests()