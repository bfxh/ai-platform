#!/usr/bin/env python3
"""
GStackCore 系统验证脚本

验证所有核心功能是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from gstack_core import GStackCore


def test_case(name, func):
    """执行单个测试"""
    print(f"\n[TEST] {name}")
    try:
        result = func()
        if result:
            print(f"   [OK] 通过")
            return True
        else:
            print(f"   [FAIL] 失败")
            return False
    except Exception as e:
        print(f"   [ERROR] 异常: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("[TEST] GStackCore 系统验证")
    print("=" * 60)

    core = GStackCore()
    results = []

    # 测试1: 获取用户
    results.append(test_case(
        "测试1: 获取用户信息 (octocat)",
        lambda: (
            core.execute("get_user", {"username": "octocat"}).get("success")
        )
    ))

    # 测试2: 获取仓库
    results.append(test_case(
        "测试2: 获取仓库信息 (microsoft/vscode)",
        lambda: (
            core.execute("get_repo", {"owner": "microsoft", "repo": "vscode"}).get("success")
        )
    ))

    # 测试3: 搜索仓库
    results.append(test_case(
        "测试3: 搜索仓库 (python)",
        lambda: (
            core.execute("search_repos", {"query": "python", "limit": 5}).get("success")
        )
    ))

    # 测试4: 分析仓库
    results.append(test_case(
        "测试4: 分析仓库 (microsoft/vscode)",
        lambda: (
            core.execute("analyze_repo", {"owner": "microsoft", "repo": "vscode"}).get("success")
        )
    ))

    # 测试5: 批量获取
    results.append(test_case(
        "测试5: 批量获取",
        lambda: (
            core.execute("batch_get", {
                "type": "repo",
                "items": ["microsoft/vscode", "facebook/react"]
            }).get("success")
        )
    ))

    # 测试6: 系统状态
    results.append(test_case(
        "测试6: 系统状态",
        lambda: (
            core.get_status().get("status") == "running"
        )
    ))

    # 测试7: 任务历史
    results.append(test_case(
        "测试7: 任务历史",
        lambda: (
            len(core.get_task_history()) > 0
        )
    ))

    # 总结
    print("\n" + "=" * 60)
    print("[SUMMARY] 测试结果汇总")
    print("=" * 60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总测试数: {total}")
    print(f"通过: {passed} [OK]")
    print(f"失败: {failed} [FAIL]")
    print(f"通过率: {passed/total*100:.1f}%")

    # 显示API状态
    status = core.get_status()
    rate_limit = status.get("rate_limit", {})
    print(f"\n[API] API状态:")
    print(f"   Core API: {rate_limit.get('remaining', 'N/A')}/{rate_limit.get('limit', 'N/A')}")

    # 显示任务历史
    history = core.get_task_history(5)
    print(f"\n[HISTORY] 最近任务:")
    for task in history[:3]:
        print(f"   - {task['type']}: {task['status']}")

    print("\n" + "=" * 60)

    if failed == 0:
        print("[SUCCESS] 所有测试通过！系统运行正常！")
        return 0
    else:
        print(f"[WARNING] {failed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
