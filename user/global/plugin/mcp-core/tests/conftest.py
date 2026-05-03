#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - Pytest 配置
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录"""
    return tmp_path


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "version": "2.0.0",
        "name": "Test MCP",
        "server": {
            "host": "localhost",
            "port": 8766,
            "protocol": "websocket",
            "max_connections": 100,
        },
        "skills": {"test_skill": {"enabled": True, "param1": "value1"}},
    }
