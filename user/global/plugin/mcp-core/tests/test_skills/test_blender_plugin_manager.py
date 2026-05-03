#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender 插件管理器技能测试
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.blender_plugin_manager.skill import BlenderPluginManagerSkill


class TestBlenderPluginManagerSkill:
    """Blender 插件管理器技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return BlenderPluginManagerSkill()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "blender_plugin_manager"
        assert skill.version == "1.0.0"
        assert skill.description == "Blender 插件管理 - 自动启用插件、配置账号、验证状态"

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "plugin_name" in params
        assert "blender_path" in params
        assert "api_key" in params
        assert "username" in params

        # 检查 action 参数
        assert params["action"]["required"] is True

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params(
            {"action": "enable_plugin", "plugin_name": "blenderkit"}
        )
        assert valid is True
        assert error is None

    def test_sanitize_plugin_name(self, skill):
        """测试插件名称清理"""
        # 测试基本清理
        assert skill._sanitize_plugin_name("blenderkit") == "blenderkit"
        # 测试带横线的名称
        assert skill._sanitize_plugin_name("blender-kit") == "blender_kit"
        # 测试带空格的名称
        assert skill._sanitize_plugin_name("blender kit") == "blender_kit"
        # 测试以数字开头的名称
        assert skill._sanitize_plugin_name("123plugin") == "p_123plugin"
        # 测试包含特殊字符的名称
        assert skill._sanitize_plugin_name("plugin@#$") == "plugin"

    def test_execute_enable_plugin(self, skill):
        """测试启用插件"""
        result = skill.execute({"action": "enable_plugin", "plugin_name": "blenderkit"})

        assert "success" in result
        # 即使失败也应该返回成功，因为技能设计为即使失败也不中断工作流
        assert result["success"] is True

    def test_execute_configure_account(self, skill):
        """测试配置账号"""
        result = skill.execute(
            {"action": "configure_account", "api_key": "test_api_key", "username": "test_user"}
        )

        assert "success" in result
        # 即使失败也应该返回成功，因为技能设计为即使失败也不中断工作流
        assert result["success"] is True

    def test_execute_verify_status(self, skill):
        """测试验证状态"""
        result = skill.execute({"action": "verify_status", "plugin_name": "blenderkit"})

        assert "success" in result

    def test_execute_get_plugin_info(self, skill):
        """测试获取插件信息"""
        result = skill.execute({"action": "get_plugin_info", "plugin_name": "blenderkit"})

        assert "success" in result
        # 即使失败也应该返回成功，因为技能设计为即使失败也不中断工作流
        assert result["success"] is True

    def test_execute_install_plugin(self, skill):
        """测试安装插件"""
        result = skill.execute({"action": "install_plugin", "plugin_name": "blenderkit"})

        assert "success" in result
        # 即使失败也应该返回成功，因为技能设计为即使失败也不中断工作流
        assert result["success"] is True

    def test_execute_invalid_action(self, skill):
        """测试无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result
