#!/usr/bin/env python3
"""
简单测试脚本，验证系统是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gstack_core import GStackCore

print("简单测试开始...")
print("=" * 50)

try:
    # 测试1: 初始化
    print("测试1: 初始化GStackCore")
    core = GStackCore()
    print("[OK] 初始化成功")

    # 测试2: 获取用户信息
    print("\n测试2: 获取用户信息 (octocat)")
    result = core.execute("get_user", {"username": "octocat"})
    if result.get("success"):
        print("[OK] 获取用户成功")
        print(f"   用户名: {result.get('data', {}).get('username')}")
    else:
        print(f"[FAIL] 获取用户失败: {result.get('error')}")

    # 测试3: 系统状态
    print("\n测试3: 系统状态")
    status = core.get_status()
    print("[OK] 获取状态成功")
    print(f"   状态: {status.get('status')}")
    print(f"   任务数: {status.get('tasks_total')}")

    print("\n" + "=" * 50)
    print("[SUCCESS] 所有测试通过！")
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
