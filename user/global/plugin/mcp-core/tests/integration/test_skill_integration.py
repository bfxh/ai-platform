#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能集成测试
测试技能之间的协作和完整工作流
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.ai_toolkit_ecosystem.skill import AIToolkitEcosystem
from skills.base import SkillRegistry
from skills.download_manager.skill import DownloadManagerSkill
from skills.network_transfer.skill import NetworkTransferSkill
from skills.system_optimizer.skill import SystemOptimizerSkill


class TestSkillIntegration:
    """技能集成测试类"""

    @pytest.fixture
    def registry(self):
        """创建技能注册表"""
        return SkillRegistry()

    @pytest.fixture
    def skills(self):
        """创建多个技能实例"""
        return {
            "ai_ecosystem": AIToolkitEcosystem(),
            "download_manager": DownloadManagerSkill(),
            "system_optimizer": SystemOptimizerSkill(),
            "network_transfer": NetworkTransferSkill(),
        }

    def test_skill_registry_registration(self, registry):
        """测试技能注册表注册功能"""
        skill = AIToolkitEcosystem()

        # 注册技能
        result = registry.register(skill)
        assert result is True

        # 验证技能已注册
        assert skill.name in registry._skills
        assert registry.get_skill(skill.name) == skill

    def test_skill_registry_auto_discover(self, registry):
        """测试技能自动发现"""
        # 自动发现技能
        registry.auto_discover()

        # 验证发现了一些技能
        assert len(registry._skills) > 0

        # 验证可以列出所有技能
        skills = registry.list_skills()
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_multiple_skills_initialization(self, skills):
        """测试多个技能同时初始化"""
        for name, skill in skills.items():
            assert skill.name is not None
            assert skill.version is not None
            assert skill.description is not None

            # 验证所有技能都有 execute 方法
            assert hasattr(skill, "execute")
            assert callable(getattr(skill, "execute"))

    def test_skill_parameter_compatibility(self, skills):
        """测试技能参数兼容性"""
        for name, skill in skills.items():
            params = skill.get_parameters()

            # 验证所有技能都有 action 参数
            assert "action" in params, f"{name} 缺少 action 参数"

            # 验证 action 参数结构
            assert "type" in params["action"]
            assert "required" in params["action"]
            assert params["action"]["required"] is True

    def test_ai_ecosystem_to_download_workflow(self, skills):
        """测试 AI 生态系统到下载管理器的工作流"""
        ai_ecosystem = skills["ai_ecosystem"]
        download_manager = skills["download_manager"]

        # 1. 获取 AI 工具列表
        result = ai_ecosystem.execute({"action": "list"})
        assert result["success"] is True

        # 2. 获取推荐
        recommend_result = ai_ecosystem.execute({"action": "recommend", "task": "数据分析"})
        assert recommend_result["success"] is True

        # 3. 检查下载管理器状态
        queue_result = download_manager.execute({"action": "queue_status"})
        assert "success" in queue_result

    def test_system_optimizer_and_network_transfer(self, skills):
        """测试系统优化器和网络传输的协作"""
        system_optimizer = skills["system_optimizer"]
        network_transfer = skills["network_transfer"]

        # 1. 系统优化 - 检查依赖
        deps_result = system_optimizer.execute({"action": "check_dependencies"})
        assert "success" in deps_result

        # 2. 网络传输 - 扫描网络
        scan_result = network_transfer.execute({"action": "scan", "subnet": "192.168.1"})
        assert "success" in scan_result

    def test_error_handling_consistency(self, skills):
        """测试错误处理一致性"""
        for name, skill in skills.items():
            # 测试无效操作
            result = skill.execute({"action": "invalid_action"})

            # 所有技能都应该返回统一的错误格式
            assert "success" in result
            assert result["success"] is False
            assert "error" in result

    def test_skill_status_management(self, skills):
        """测试技能状态管理"""
        for name, skill in skills.items():
            # 获取初始状态
            initial_status = skill.get_status()

            # 验证状态包含必要字段
            assert "name" in initial_status
            assert "version" in initial_status
            assert "status" in initial_status

            # 验证状态值有效
            assert initial_status["name"] == skill.name
            assert initial_status["version"] == skill.version

    def test_config_management_integration(self, skills):
        """测试配置管理集成"""
        for name, skill in skills.items():
            # 测试获取配置
            config_value = skill.get_config("nonexistent_key", "default_value")
            assert config_value == "default_value"

            # 测试获取所有配置
            all_config = skill.get_all_config()
            assert isinstance(all_config, dict)


class TestSkillWorkflows:
    """技能工作流测试类"""

    def test_complete_ai_toolkit_workflow(self):
        """测试完整的 AI 工具包工作流"""
        ai_ecosystem = AIToolkitEcosystem()

        # 步骤 1: 列出市场工具
        list_result = ai_ecosystem.execute({"action": "list"})
        assert list_result["success"] is True
        assert "result" in list_result

        # 步骤 2: 获取统计信息
        stats_result = ai_ecosystem.execute({"action": "stats"})
        assert stats_result["success"] is True

        # 步骤 3: 获取推荐
        recommend_result = ai_ecosystem.execute({"action": "recommend", "task": "自然语言处理"})
        assert recommend_result["success"] is True
        assert "result" in recommend_result
        assert isinstance(recommend_result["result"], list)

    def test_system_maintenance_workflow(self):
        """测试系统维护工作流"""
        system_optimizer = SystemOptimizerSkill()

        # 步骤 1: 检查依赖
        deps_result = system_optimizer.execute({"action": "check_dependencies"})
        assert "success" in deps_result

        # 步骤 2: 清理临时文件
        temp_result = system_optimizer.clean_temp(days=7)
        assert isinstance(temp_result, dict)
        assert "cleaned_files" in temp_result

        # 步骤 3: 统一日志
        logs_result = system_optimizer.unify_logs()
        assert isinstance(logs_result, dict)
        assert "processed_files" in logs_result

    def test_network_file_transfer_workflow(self):
        """测试网络文件传输工作流"""
        network_transfer = NetworkTransferSkill()

        # 步骤 1: 发现设备
        discover_result = network_transfer.execute({"action": "discover"})
        assert "success" in discover_result

        # 步骤 2: 扫描网络
        scan_result = network_transfer.execute({"action": "scan", "subnet": "192.168.1"})
        assert "success" in scan_result

        # 步骤 3: 验证错误处理（缺少目标）
        send_result = network_transfer.execute({"action": "send", "files": ["test.txt"]})
        assert send_result["success"] is False
        assert "error" in send_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
