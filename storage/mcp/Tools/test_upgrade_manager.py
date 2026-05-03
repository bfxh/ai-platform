#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件升级管理器测试脚本
"""

import sys
import os
sys.path.insert(0, str(os.path.dirname(os.path.abspath(__file__))))

from .software_upgrade_manager import SoftwareUpgradeManager, compare_versions

def test_version_compare():
    """测试版本比较功能"""
    print("=== 测试版本比较 ===")
    
    tests = [
        ("1.0.0", "1.0.0", 0),
        ("1.0.0", "1.0.1", -1),
        ("1.1.0", "1.0.9", 1),
        ("v2.0", "2.0.0", 0),
        ("3.1.4", "3.1.4.1", -1),
        ("1.0-beta", "1.0", -1),
    ]
    
    all_pass = True
    for v1, v2, expected in tests:
        result = compare_versions(v1, v2)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {v1} vs {v2} = {result} (期望: {expected})")
        if result != expected:
            all_pass = False
    
    return all_pass

def test_manager_init():
    """测试管理器初始化"""
    print("\n=== 测试管理器初始化 ===")
    
    try:
        manager = SoftwareUpgradeManager()
        software_list = manager.list_software()
        print(f"  ✓ 管理器初始化成功")
        print(f"  ✓ 已加载 {len(software_list)} 个软件")
        return True
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return False

def test_list_software():
    """测试列出软件功能"""
    print("\n=== 测试列出软件 ===")
    
    try:
        manager = SoftwareUpgradeManager()
        software_list = manager.list_software()
        
        print(f"  软件列表 ({len(software_list)} 个):")
        for s in software_list:
            print(f"    - {s.display_name} ({s.category})")
        
        return True
    except Exception as e:
        print(f"  ✗ 列出失败: {e}")
        return False

def test_check_updates():
    """测试检查更新功能"""
    print("\n=== 测试检查更新 ===")
    
    try:
        manager = SoftwareUpgradeManager()
        
        # 检查单个软件
        print("  检查单个软件更新...")
        results = manager.check_updates("godot")
        if results:
            s = results[0]
            print(f"    {s.display_name}: {s.current_version} → {s.latest_version}")
        
        return True
    except Exception as e:
        print(f"  ✗ 检查更新失败: {e}")
        return False

def test_summary():
    """测试获取摘要功能"""
    print("\n=== 测试获取摘要 ===")
    
    try:
        manager = SoftwareUpgradeManager()
        summary = manager.get_upgrade_summary()
        
        print(f"  总软件数: {summary['total']}")
        print(f"  已是最新: {summary['up_to_date']}")
        print(f"  有更新: {summary['available']}")
        print(f"  升级中: {summary['upgrading']}")
        print(f"  错误: {summary['error']}")
        
        return True
    except Exception as e:
        print(f"  ✗ 获取摘要失败: {e}")
        return False

def test_add_remove_software():
    """测试添加和移除软件"""
    print("\n=== 测试添加和移除软件 ===")
    
    try:
        manager = SoftwareUpgradeManager()
        
        # 添加测试软件
        from .software_upgrade_manager import SoftwareInfo
        test_info = SoftwareInfo(
            name="test_app",
            display_name="Test Application",
            current_version="1.0.0",
            latest_version="",
            upgrade_source="github",
            source_url="https://github.com/test/test",
            install_path=__import__('pathlib').Path("D:/Test/App"),
            category="dev_tool",
            auto_upgrade=False
        )
        
        manager.add_software(test_info)
        print("  ✓ 添加软件成功")
        
        # 验证添加
        software = manager.get_software("test_app")
        if software:
            print(f"  ✓ 已找到软件: {software.display_name}")
        else:
            print("  ✗ 未找到添加的软件")
            return False
        
        # 移除软件
        manager.remove_software("test_app")
        print("  ✓ 移除软件成功")
        
        # 验证移除
        software = manager.get_software("test_app")
        if not software:
            print("  ✓ 软件已成功移除")
        else:
            print("  ✗ 软件移除失败")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ 添加/移除失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("软件升级管理器测试")
    print("=" * 60)
    
    tests = [
        ("版本比较", test_version_compare),
        ("管理器初始化", test_manager_init),
        ("列出软件", test_list_software),
        ("检查更新", test_check_updates),
        ("获取摘要", test_summary),
        ("添加/移除软件", test_add_remove_software),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {name} 异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)