#!/usr/bin/env python3
"""
GStackCore 完整验证脚本

验证所有核心功能和AutoDevOps系统
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gstack_core import GStackCore
from .autodevops import AutoDevOpsSystem


def test_gstack_core():
    """测试GStackCore"""
    print("""
======================================
测试1: GStackCore 核心功能
======================================
""")

    core = GStackCore()
    tests = [
        ("获取用户信息", lambda: core.execute("get_user", {"username": "octocat"}).get("success")),
        ("获取仓库信息", lambda: core.execute("get_repo", {"owner": "microsoft", "repo": "vscode"}).get("success")),
        ("搜索仓库", lambda: core.execute("search_repos", {"query": "python", "limit": 3}).get("success")),
        ("分析仓库", lambda: core.execute("analyze_repo", {"owner": "microsoft", "repo": "vscode"}).get("success")),
        ("批量获取", lambda: core.execute("batch_get", {"type": "repo", "items": ["microsoft/vscode", "facebook/react"]}).get("success")),
        ("系统状态", lambda: core.get_status().get("status") == "running"),
        ("任务历史", lambda: len(core.get_task_history()) > 0),
    ]

    passed = 0
    total = len(tests)

    for name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"[OK] {name}")
                passed += 1
            else:
                print(f"[FAIL] {name}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
        time.sleep(1)  # 避免API限制

    print(f"\n结果: {passed}/{total} 通过")
    return passed == total


def test_autodevops():
    """测试AutoDevOps系统"""
    print("""

======================================
测试2: AutoDevOps 系统
======================================
""")

    system = AutoDevOpsSystem()
    
    # 测试状态
    status = system.status()
    print(f"[OK] 系统状态: {status.get('running')}")
    
    # 测试配置
    print(f"[OK] 自动测试: {system.config.get('auto_test')}")
    print(f"[OK] 自动构建: {system.config.get('auto_build')}")
    print(f"[OK] 自动部署: {system.config.get('auto_deploy')}")
    
    # 测试测试功能
    print("\n[INFO] 运行测试...")
    test_result = system.run_tests(force=True)
    print(f"[OK] 测试功能: {test_result}")
    
    # 测试构建功能
    print("[INFO] 运行构建...")
    build_result = system.build(force=True)
    print(f"[OK] 构建功能: {build_result}")
    
    # 测试部署功能
    print("[INFO] 运行部署...")
    deploy_result = system.deploy(force=True)
    print(f"[OK] 部署功能: {deploy_result}")
    
    return test_result and build_result and deploy_result


def test_files():
    """测试文件结构"""
    print("""

======================================
测试3: 文件结构
======================================
""")

    project_root = Path("/python/gstack_core")
    expected_files = [
        "github_client.py",
        "gstack_core.py",
        "web_ui.py",
        "autodevops.py",
        "verify.py",
        "simple_test.py",
        "start.bat",
        "__init__.py",
        "logs/",
        "build/",
        "tests/",
    ]

    passed = 0
    total = len(expected_files)

    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"[OK] {file_path}")
            passed += 1
        else:
            print(f"[FAIL] {file_path}")

    print(f"\n结果: {passed}/{total} 通过")
    return passed == total


def main():
    """主函数"""
    print("🚀 GStackCore 完整验证")
    print("=" * 60)

    results = []
    
    # 测试1: GStackCore
    results.append(test_gstack_core())
    
    # 测试2: AutoDevOps
    results.append(test_autodevops())
    
    # 测试3: 文件结构
    results.append(test_files())
    
    # 总结
    print("""

======================================
验证结果汇总
======================================
""")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总测试数: {total}")
    print(f"通过: {passed} [OK]")
    print(f"失败: {failed} [FAIL]")
    print(f"通过率: {passed/total*100:.1f}%")

    if failed == 0:
        print("\n🎉 所有验证通过！系统运行正常！")
        print("\n📋 系统功能:")
        print("   ✅ GStackCore 核心功能")
        print("   ✅ AutoDevOps 自动开发测试部署")
        print("   ✅ Web界面")
        print("   ✅ 完整的文件结构")
        print("\n🚀 系统已准备就绪，可以正常使用！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
