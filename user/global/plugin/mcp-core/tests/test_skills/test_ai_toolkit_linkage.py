#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_toolkit_linkage 技能测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from skills.ai_toolkit_linkage.skill import AIToolkitLinkageSkill


class TestAIToolkitLinkageSkill:
    """AIToolkitLinkageSkill 测试类"""

    def test_skill_initialization(self):
        """测试技能初始化"""
        skill = AIToolkitLinkageSkill()
        assert skill.name == "ai_toolkit_linkage"
        assert skill.version is not None
        assert skill.description is not None

    def test_get_parameters(self):
        """测试获取参数定义"""
        skill = AIToolkitLinkageSkill()
        params = skill.get_parameters()
        assert isinstance(params, dict)
        assert "action" in params

    def test_validate_params_missing_action(self):
        """测试参数验证 - 缺少 action"""
        skill = AIToolkitLinkageSkill()
        is_valid, error = skill.validate_params(dict())
        assert is_valid is False
        assert "action" in error.lower()

    def test_validate_params_valid(self):
        """测试参数验证 - 有效参数"""
        skill = AIToolkitLinkageSkill()
        is_valid, error = skill.validate_params({"action": "link"})
        assert is_valid is True
        assert error is None

    def test_execute_link(self):
        """测试执行 link"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute({"action": "link"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_unlink(self):
        """测试执行 unlink"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute({"action": "unlink"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_sync(self):
        """测试执行 sync"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute({"action": "sync"})
        assert isinstance(result, dict)
        assert "success" in result

    def test_execute_invalid_action(self):
        """测试执行无效动作"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute({"action": "invalid_action"})
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_none_params(self):
        """测试执行 - None 参数"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute(None)
        assert result["success"] is False

    def test_execute_with_empty_params(self):
        """测试执行 - 空参数字典"""
        skill = AIToolkitLinkageSkill()
        result = skill.execute(dict())
        assert result["success"] is False

    def test_config_access(self):
        """测试配置访问"""
        skill = AIToolkitLinkageSkill()
        config_value = skill.get_config("test_key", "default")
        assert config_value == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
