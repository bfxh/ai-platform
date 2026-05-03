#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK Commands 集成测试
"""

import sys
import os
from pathlib import Path
import subprocess
import tempfile

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestGstackCommands:
    """GSTACK Commands 测试类"""

    def test_anchor_command(self):
        """测试 gstack anchor 命令"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack anchor"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0 or "GSTACK" in result.stdout or "Anchor" in result.stdout

    def test_log_command(self):
        """测试 gstack log 命令"""
        test_error = "Test error message"
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack log '{test_error}'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0

    def test_memo_command(self):
        """测试 gstack memo 命令"""
        test_memo = "Test memo content"
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack memo '{test_memo}'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0

    def test_blender_command_no_args(self):
        """测试 gstack blender 命令无参数"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack blender"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行，显示帮助信息
        assert result.returncode == 0

    def test_blender_status_command(self):
        """测试 gstack blender status 命令"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack blender status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0

    def test_workflow_command_no_args(self):
        """测试 gstack workflow 命令无参数"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack workflow"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行，显示帮助信息
        assert result.returncode == 0

    def test_workflow_status_command(self):
        """测试 gstack workflow status 命令"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack workflow status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0

    def test_narsil_command_no_args(self):
        """测试 gstack narsil 命令无参数"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack narsil"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行，显示帮助信息
        assert result.returncode == 0

    def test_narsil_status_command(self):
        """测试 gstack narsil status 命令"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack narsil status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行
        assert result.returncode == 0

    def test_ask_command_no_args(self):
        """测试 gstack ask 命令无参数"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack ask"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # 命令应该成功执行，显示帮助信息
        assert result.returncode == 0

    def test_ask_dashboard_command(self):
        """测试 gstack ask dashboard 命令"""
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command",
             f"cd {PROJECT_ROOT}; Import-Module '{PROJECT_ROOT}\\gstack_core\\commands.ps1'; gstack ask dashboard"],
            capture_output=True,
            text=True,
            timeout=15
        )
        # 命令应该成功执行
        assert result.returncode == 0


def run_tests():
    """运行所有测试"""
    test_instance = TestGstackCommands()

    print("运行 GSTACK Commands 集成测试...")
    print("=" * 50)

    # 测试 anchor 命令
    try:
        test_instance.test_anchor_command()
        print("✅ test_anchor_command 通过")
    except Exception as e:
        print(f"❌ test_anchor_command 失败: {e}")

    # 测试 log 命令
    try:
        test_instance.test_log_command()
        print("✅ test_log_command 通过")
    except Exception as e:
        print(f"❌ test_log_command 失败: {e}")

    # 测试 memo 命令
    try:
        test_instance.test_memo_command()
        print("✅ test_memo_command 通过")
    except Exception as e:
        print(f"❌ test_memo_command 失败: {e}")

    # 测试 blender 无参数
    try:
        test_instance.test_blender_command_no_args()
        print("✅ test_blender_command_no_args 通过")
    except Exception as e:
        print(f"❌ test_blender_command_no_args 失败: {e}")

    # 测试 blender status
    try:
        test_instance.test_blender_status_command()
        print("✅ test_blender_status_command 通过")
    except Exception as e:
        print(f"❌ test_blender_status_command 失败: {e}")

    # 测试 workflow 无参数
    try:
        test_instance.test_workflow_command_no_args()
        print("✅ test_workflow_command_no_args 通过")
    except Exception as e:
        print(f"❌ test_workflow_command_no_args 失败: {e}")

    # 测试 workflow status
    try:
        test_instance.test_workflow_status_command()
        print("✅ test_workflow_status_command 通过")
    except Exception as e:
        print(f"❌ test_workflow_status_command 失败: {e}")

    # 测试 narsil 无参数
    try:
        test_instance.test_narsil_command_no_args()
        print("✅ test_narsil_command_no_args 通过")
    except Exception as e:
        print(f"❌ test_narsil_command_no_args 失败: {e}")

    # 测试 narsil status
    try:
        test_instance.test_narsil_status_command()
        print("✅ test_narsil_status_command 通过")
    except Exception as e:
        print(f"❌ test_narsil_status_command 失败: {e}")

    # 测试 ask 无参数
    try:
        test_instance.test_ask_command_no_args()
        print("✅ test_ask_command_no_args 通过")
    except Exception as e:
        print(f"❌ test_ask_command_no_args 失败: {e}")

    # 测试 ask dashboard
    try:
        test_instance.test_ask_dashboard_command()
        print("✅ test_ask_dashboard_command 通过")
    except Exception as e:
        print(f"❌ test_ask_dashboard_command 失败: {e}")

    print("=" * 50)
    print("GSTACK Commands 集成测试完成")


if __name__ == "__main__":
    run_tests()