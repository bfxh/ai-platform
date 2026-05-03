#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载管理技能测试
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.download_manager.skill import DownloadManagerSkill


class TestDownloadManagerSkill:
    """下载管理技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return DownloadManagerSkill()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "download_manager"
        assert skill.version == "1.1.0"
        assert "下载" in skill.description or "download" in skill.description.lower()

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "url" in params
        assert "urls" in params
        assert "output_dir" in params
        assert "filename" in params
        assert "task_id" in params
        assert "max_concurrent" in params

        # 检查 action 枚举值
        assert params["action"]["required"] is True
        assert "download" in params["action"]["enum"]
        assert "batch_download" in params["action"]["enum"]
        assert "queue_status" in params["action"]["enum"]
        assert "pause" in params["action"]["enum"]
        assert "resume" in params["action"]["enum"]
        assert "cancel" in params["action"]["enum"]

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params(
            {"action": "download", "url": "https://example.com/file.txt"}
        )
        assert valid is True
        assert error is None

    def test_execute_queue_status(self, skill):
        """测试获取队列状态"""
        result = skill.execute({"action": "queue_status"})

        assert "success" in result
        assert "tasks" in result or "queue" in result or "active_tasks" in result

    def test_execute_invalid_action(self, skill):
        """测试无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result

    def test_do_download_function(self):
        """测试下载函数"""
        # 使用一个已知的小文件URL进行测试
        # 注意：这个测试可能需要网络连接
        import tempfile

        from skills.download_manager.skill import _do_download

        with tempfile.TemporaryDirectory() as temp_dir:
            # 使用一个稳定的测试URL
            result = _do_download(
                "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                temp_dir,
                "test.pdf",
            )

            # 不检查成功与否，因为网络可能不可用
            # 只检查结果格式是否正确
            assert "success" in result
            if result["success"]:
                assert "path" in result
                assert "size" in result
