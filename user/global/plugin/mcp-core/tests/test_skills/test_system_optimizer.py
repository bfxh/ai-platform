#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统优化技能测试
"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.system_optimizer.skill import SystemOptimizerSkill


class TestSystemOptimizerSkill:
    """系统优化技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return SystemOptimizerSkill()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "system_optimizer"
        assert skill.version == "1.0.0"
        assert skill.description == "系统优化 - 清理备份文件、临时文件、统一日志和配置管理"

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "max_age_days" in params
        assert "keep_count" in params
        assert "max_age_hours" in params

        # 检查 action 枚举值
        assert params["action"]["required"] is True
        assert "clean_backups" in params["action"]["enum"]
        assert "clean_temp" in params["action"]["enum"]
        assert "unify_logs" in params["action"]["enum"]
        assert "unify_config" in params["action"]["enum"]
        assert "check_dependencies" in params["action"]["enum"]
        assert "full_optimize" in params["action"]["enum"]

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params(
            {"action": "clean_backups", "max_age_days": 30, "keep_count": 5}
        )
        assert valid is True
        assert error is None

    def test_clean_backups(self, skill, monkeypatch):
        """测试清理备份文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建模拟的备份目录结构
            backup_dir = temp_path / "backups"
            backup_dir.mkdir()

            # 创建一些模拟的备份文件夹
            for i in range(3):
                folder = backup_dir / f"backup_{i}"
                folder.mkdir()
                # 创建一些文件
                (folder / "test.txt").write_text("test content")

            # 修改 BACKUPS_DIR 指向临时目录
            import skills.system_optimizer.skill as skill_module

            original_backups_dir = skill_module.BACKUPS_DIR
            skill_module.BACKUPS_DIR = backup_dir

            try:
                result = skill.clean_backups(max_age_days=0, keep_count=0)

                assert isinstance(result, dict)
                assert "cleaned_files" in result
                assert "cleaned_size" in result
                assert "errors" in result
            finally:
                skill_module.BACKUPS_DIR = original_backups_dir

    def test_clean_temp(self, skill, monkeypatch):
        """测试清理临时文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建模拟的临时目录
            temp_dir_path = temp_path / "temp"
            temp_dir_path.mkdir()

            # 创建一些临时文件
            old_file = temp_dir_path / "old_file.txt"
            old_file.write_text("old content")

            # 修改 TEMP_DIR 指向临时目录
            import skills.system_optimizer.skill as skill_module

            original_temp_dir = skill_module.TEMP_DIR
            skill_module.TEMP_DIR = temp_dir_path

            try:
                result = skill.clean_temp(max_age_hours=0)

                assert isinstance(result, dict)
                assert "cleaned_files" in result
                assert "cleaned_size" in result
                assert "errors" in result
            finally:
                skill_module.TEMP_DIR = original_temp_dir

    def test_unify_logs(self, skill, monkeypatch):
        """测试统一日志管理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建模拟的日志目录
            logs_dir = temp_path / "logs"
            logs_dir.mkdir()

            # 修改 LOGS_DIR 指向临时目录
            import skills.system_optimizer.skill as skill_module

            original_logs_dir = skill_module.LOGS_DIR
            skill_module.LOGS_DIR = logs_dir

            try:
                result = skill.unify_logs()

                assert isinstance(result, dict)
                assert "updated_configs" in result

                # 检查配置文件是否创建
                config_file = logs_dir / "log_config.json"
                assert config_file.exists()
            finally:
                skill_module.LOGS_DIR = original_logs_dir

    def test_unify_config(self, skill, monkeypatch):
        """测试统一配置管理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建模拟的配置目录
            config_dir = temp_path / "config"
            config_dir.mkdir()

            # 修改 CONFIG_DIR 指向临时目录
            import skills.system_optimizer.skill as skill_module

            original_config_dir = skill_module.CONFIG_DIR
            skill_module.CONFIG_DIR = config_dir

            try:
                result = skill.unify_config()

                assert isinstance(result, dict)
                assert "updated_configs" in result

                # 检查主配置文件是否创建
                master_config = config_dir / "master_config.json"
                assert master_config.exists()
            finally:
                skill_module.CONFIG_DIR = original_config_dir

    def test_check_dependencies(self, skill):
        """测试检查依赖关系"""
        result = skill.check_dependencies()

        assert isinstance(result, dict)
        assert "backup_dependencies" in result
        assert "temp_dependencies" in result
        assert "log_dependencies" in result
        assert "config_dependencies" in result

        assert isinstance(result["backup_dependencies"], list)
        assert isinstance(result["temp_dependencies"], list)
        assert isinstance(result["log_dependencies"], list)
        assert isinstance(result["config_dependencies"], list)

    def test_full_optimize(self, skill):
        """测试完整优化"""
        result = skill.full_optimize()

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "summary" in result
        assert "details" in result

        summary = result["summary"]
        assert "cleaned_files_count" in summary
        assert "cleaned_size_mb" in summary
        assert "errors_count" in summary
        assert "warnings_count" in summary
        assert "updated_configs_count" in summary

    def test_execute_clean_backups(self, skill):
        """测试执行 clean_backups 操作"""
        result = skill.execute({"action": "clean_backups", "max_age_days": 30, "keep_count": 5})

        assert result["success"] is True
        assert "result" in result

    def test_execute_clean_temp(self, skill):
        """测试执行 clean_temp 操作"""
        result = skill.execute({"action": "clean_temp", "max_age_hours": 24})

        assert result["success"] is True
        assert "result" in result

    def test_execute_unify_logs(self, skill):
        """测试执行 unify_logs 操作"""
        result = skill.execute({"action": "unify_logs"})

        assert result["success"] is True
        assert "result" in result

    def test_execute_unify_config(self, skill):
        """测试执行 unify_config 操作"""
        result = skill.execute({"action": "unify_config"})

        assert result["success"] is True
        assert "result" in result

    def test_execute_check_dependencies(self, skill):
        """测试执行 check_dependencies 操作"""
        result = skill.execute({"action": "check_dependencies"})

        assert result["success"] is True
        assert "result" in result

    def test_execute_full_optimize(self, skill):
        """测试执行 full_optimize 操作"""
        result = skill.execute({"action": "full_optimize"})

        assert result["success"] is True
        assert "result" in result

    def test_execute_invalid_action(self, skill):
        """测试执行无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result
