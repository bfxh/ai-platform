#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络传输技能测试
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.network_transfer.skill import NetworkTransferSkill


class TestNetworkTransferSkill:
    """网络传输技能测试类"""

    @pytest.fixture
    def skill(self):
        """创建技能实例"""
        return NetworkTransferSkill()

    def test_skill_initialization(self, skill):
        """测试技能初始化"""
        assert skill.name == "network_transfer"
        assert skill.version == "2.0.0"
        assert skill.description == "高速局域网文件传输"

    def test_get_parameters(self, skill):
        """测试参数定义"""
        params = skill.get_parameters()

        assert "action" in params
        assert "target" in params
        assert "files" in params
        assert "save_dir" in params
        assert "port" in params

        # 检查 action 枚举值
        assert params["action"]["required"] is True
        assert "send" in params["action"]["enum"]
        assert "receive" in params["action"]["enum"]
        assert "discover" in params["action"]["enum"]
        assert "scan" in params["action"]["enum"]

    def test_validate_params_missing_action(self, skill):
        """测试缺少 action 参数"""
        valid, error = skill.validate_params({})
        assert valid is False
        assert "action" in error

    def test_validate_params_valid(self, skill):
        """测试有效参数"""
        valid, error = skill.validate_params({"action": "discover"})
        assert valid is True
        assert error is None

    def test_execute_discover(self, skill):
        """测试设备发现"""
        result = skill.execute({"action": "discover"})

        assert "success" in result
        # 可能成功或失败，取决于网络环境

    def test_execute_scan(self, skill):
        """测试网络扫描"""
        result = skill.execute({"action": "scan", "subnet": "192.168.1"})

        assert "success" in result
        if result["success"]:
            assert "devices" in result

    def test_execute_send_missing_target(self, skill):
        """测试发送文件缺少目标地址"""
        result = skill.execute({"action": "send", "files": ["test.txt"]})

        assert result["success"] is False
        assert "目标" in result.get("error", "") or "target" in result.get("error", "").lower()

    def test_execute_send_missing_files(self, skill):
        """测试发送文件缺少文件列表"""
        result = skill.execute({"action": "send", "target": "192.168.1.1"})

        assert result["success"] is False
        assert "文件" in result.get("error", "") or "file" in result.get("error", "").lower()

    def test_execute_invalid_action(self, skill):
        """测试无效操作"""
        result = skill.execute({"action": "invalid_action"})

        assert result["success"] is False
        assert "error" in result

    def test_calculate_hash(self, skill):
        """测试计算文件哈希"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_file = f.name

        try:
            file_path = Path(temp_file)
            hash_value = skill._calculate_hash(file_path)

            assert isinstance(hash_value, str)
            assert len(hash_value) == 32  # MD5 hash length
        finally:
            Path(temp_file).unlink()

    def test_config_values(self, skill):
        """测试配置值"""
        assert skill.transfer_port == 50000
        assert skill.buffer_size == 65536
        assert skill.chunk_size == 1048576
        assert skill.max_retries == 3
        assert skill.timeout == 300
