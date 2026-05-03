#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 测试配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 测试配置
TEST_CONFIG = {
    "ask_dir": "/python\\MCP\\Tools\\ask",
    "skills_dir": "/python\\MCP\\Tools\\ask\\skills",
    "blender_mcp_dir": "/python\\MCP\\JM\\blender_mcp",
    "n8n_dir": "/python\\MCP\\Tools\\n8n",
    "narsil_dir": "/python\\MCP\\BC\\narsil_mcp",
}

# 辅助函数
def get_test_data_path(filename):
    """获取测试数据文件路径"""
    return PROJECT_ROOT / "tests" / "data" / filename
