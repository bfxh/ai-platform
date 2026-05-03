#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_manager 技能测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from skills.plugin_manager.skill import PluginManagerSkill


class TestPluginManagerSkill:
    """PluginManagerSkill 测试类"""

    def test_skill_initialization(self):
        """测试技能初始化"""
        skill = PluginManagerSkill()
        assert skill.name == "plugin_manager"
        assert skill.version is not None
        assert skill.description is not None

    def test_get_parameters(self):
        """测试获取参数定义"""
        skill = PluginManagerSkill()
        params = skill.get_parameters()
        assert isinstance(params, dict)
        assert "action" in params

    def test_validate_params_missing_action(self):
        """测试参数验证 - 缺少 action"""
        skill = PluginManagerSkill()
        is_valid, error = skill.validate_params(dict())
        assert is_valid is False
        assert "action" in error.lower()

    def test_validate_params_valid(self):
        """测试参数验证 - 有效参数"""
        skill = PluginManagerSkill()
        is_valid, error = skill.validate_params({"action": "search"})
        assert is_valid is True
        assert error is None

    def test_execute_search(self):
        """测试执行 search"""
        skill = PluginManagerSkill()
        result = skill.execute({"action": "search"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_install(self):
        """测试执行 install"""
        skill = PluginManagerSkill()
        result = skill.execute({"action": "install"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_uninstall(self):
        """测试执行 uninstall"""
        skill = PluginManagerSkill()
        result = skill.execute({"action": "uninstall"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_invalid_action(self):
        """测试执行无效动作"""
        skill = PluginManagerSkill()
        result = skill.execute({"action": "invalid_action"})
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_none_params(self):
        """测试执行 - None 参数"""
        skill = PluginManagerSkill()
        result = skill.execute(None)
        assert result["success"] is False

    def test_execute_with_empty_params(self):
        """测试执行 - 空参数字典"""
        skill = PluginManagerSkill()
        result = skill.execute(dict())
        assert result["success"] is False

    def test_config_access(self):
        """测试配置访问"""
        skill = PluginManagerSkill()
        config_value = skill.get_config("test_key", "default")
        assert config_value == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
