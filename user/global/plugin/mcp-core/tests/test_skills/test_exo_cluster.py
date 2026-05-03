#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXo集群技能测试
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.exo_cluster.skill import ExoClusterSkill


class TestExoClusterSkill:
    """EXo集群技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return ExoClusterSkill()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "exo_cluster"
        assert skill.version == "2.0.0"
        assert skill.description == "EXo分布式AI集群管理"

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "model" in params
        assert "message" in params

        # 检查 action 枚举值
        assert "install" in params["action"]["enum"]
        assert "start_node" in params["action"]["enum"]
        assert "list_models" in params["action"]["enum"]

    def test_list_models(self, skill):
        """测试列出模型"""
        result = skill.execute({"action": "list_models"})

        assert result["success"] is True
        assert "models" in result
        assert len(result["models"]) > 0

        # 检查模型结构
        model = result["models"][0]
        assert "id" in model
        assert "name" in model

    def test_get_status_without_requests(self, skill):
        """测试获取状态（无requests模块）"""
        # 模拟无requests的情况
        import skills.exo_cluster.skill as exo_module

        original_available = exo_module.REQUESTS_AVAILABLE

        try:
            exo_module.REQUESTS_AVAILABLE = False
            result = skill.execute({"action": "get_status"})

            assert result["success"] is False
            assert "requests" in result.get("error", "").lower()
        finally:
            exo_module.REQUESTS_AVAILABLE = original_available

    def test_execute_invalid_action(self, skill):
        """测试无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result
