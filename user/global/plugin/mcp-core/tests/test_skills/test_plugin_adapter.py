#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_adapter 技能测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from skills.plugin_adapter.skill import PluginAdapterSkill


class TestPluginAdapterSkill:
    """PluginAdapterSkill 测试类"""

    def test_skill_initialization(self):
        """测试技能初始化"""
        skill = PluginAdapterSkill()
        assert skill.name == "plugin_adapter"
        assert skill.version is not None
        assert skill.description is not None

    def test_get_parameters(self):
        """测试获取参数定义"""
        skill = PluginAdapterSkill()
        params = skill.get_parameters()
        assert isinstance(params, dict)
        assert "action" in params

    def test_validate_params_missing_action(self):
        """测试参数验证 - 缺少 action"""
        skill = PluginAdapterSkill()
        is_valid, error = skill.validate_params(dict())
        assert is_valid is False
        assert "action" in error.lower()

    def test_validate_params_valid(self):
        """测试参数验证 - 有效参数"""
        skill = PluginAdapterSkill()
        is_valid, error = skill.validate_params({"action": "adapt"})
        assert is_valid is True
        assert error is None

    def test_execute_adapt(self):
        """测试执行 adapt"""
        skill = PluginAdapterSkill()
        result = skill.execute({"action": "adapt"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_convert(self):
        """测试执行 convert"""
        skill = PluginAdapterSkill()
        result = skill.execute({"action": "convert"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_validate(self):
        """测试执行 validate"""
        skill = PluginAdapterSkill()
        result = skill.execute({"action": "validate"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_invalid_action(self):
        """测试执行无效动作"""
        skill = PluginAdapterSkill()
        result = skill.execute({"action": "invalid_action"})
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_none_params(self):
        """测试执行 - None 参数"""
        skill = PluginAdapterSkill()
        result = skill.execute(None)
        assert result["success"] is False

    def test_execute_with_empty_params(self):
        """测试执行 - 空参数字典"""
        skill = PluginAdapterSkill()
        result = skill.execute(dict())
        assert result["success"] is False

    def test_config_access(self):
        """测试配置访问"""
        skill = PluginAdapterSkill()
        config_value = skill.get_config("test_key", "default")
        assert config_value == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
