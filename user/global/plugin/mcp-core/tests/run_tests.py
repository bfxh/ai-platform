#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 测试运行器

用法:
    python run_tests.py              # 运行所有测试
    python run_tests.py -v           # 详细输出
    python run_tests.py -k skill     # 只运行技能测试
"""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """运行测试"""
    # 获取测试目录
    test_dir = Path(__file__).parent

    # 构建 pytest 命令
    cmd = [sys.executable, "-m", "pytest", str(test_dir)]

    # 添加命令行参数
    cmd.extend(sys.argv[1:])

    # 运行测试
    result = subprocess.run(cmd)

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
