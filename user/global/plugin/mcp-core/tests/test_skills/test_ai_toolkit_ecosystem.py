#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI工具生态系统技能测试
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.ai_toolkit_ecosystem.skill import AIToolkitEcosystem


class TestAIToolkitEcosystem:
    """AI工具生态系统技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return AIToolkitEcosystem()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "ai_toolkit_ecosystem"
        assert skill.version == "1.0.0"
        assert "多AI工具生态系统" in skill.description

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "tool_id" in params
        assert "category" in params
        assert "task_description" in params

        # 检查 action 枚举值
        assert params["action"]["required"] is True
        assert "list" in params["action"]["enum"]
        assert "install" in params["action"]["enum"]
        assert "recommend" in params["action"]["enum"]
        assert "stats" in params["action"]["enum"]

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params({"action": "list_market"})
        assert valid is True
        assert error is None

    def test_execute_list(self, skill):
        """测试列出工具市场"""
        result = skill.execute({"action": "list"})

        assert "success" in result
        if result["success"]:
            assert "result" in result
            assert isinstance(result["result"], list)

    def test_execute_recommend(self, skill):
        """测试工具推荐"""
        result = skill.execute({"action": "recommend", "task": "数据分析"})

        assert "success" in result
        if result["success"]:
            assert "result" in result
            assert isinstance(result["result"], list)

    def test_execute_stats(self, skill):
        """测试生态统计"""
        result = skill.execute({"action": "stats"})

        assert "success" in result
        if result["success"]:
            assert "result" in result

    def test_execute_invalid_action(self, skill):
        """测试无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result
