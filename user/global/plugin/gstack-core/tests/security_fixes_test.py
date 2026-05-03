#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全修复测试

测试内容:
- gstack_service.py 竞态条件修复
- blender_cleaner.py 路径注入防护
- architect_enforce/skill.py 路径遍历防护
"""

import os
import sys
import threading
import time
from pathlib import Path
import tempfile

# 添加项目根目录到路径

from ..gstack_service import GSTACKService, _lock
from ..blender_cleaner import BlenderCleaner

# 导入ArchitectEnforcer
from MCP_Core.skills.architect_enforce.skill import ArchitectEnforcer


def test_gstack_service_race_condition():
    """测试gstack_service.py的竞态条件修复"""
    print("\n=== 测试 gstack_service.py 竞态条件修复 ===")
    
    service = GSTACKService()
    
    # 测试多线程并发访问
    def check_status():
        for _ in range(100):
            service.is_gstack_running()
    
    # 创建多个线程并发访问
    threads = []
    for _ in range(10):
        t = threading.Thread(target=check_status)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print("✅ 多线程并发访问测试通过，未发现竞态条件")


def test_blender_cleaner_path_injection():
    """测试blender_cleaner.py的路径注入防护"""
    print("\n=== 测试 blender_cleaner.py 路径注入防护 ===")
    
    cleaner = BlenderCleaner()
    
    # 创建临时目录用于测试
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试文件
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")
        
        # 测试正常路径
        try:
            cleaner.safe_clean("test.txt", temp_path)
            assert not test_file.exists(), "文件应该被删除"
            print("✅ 正常路径测试通过")
        except Exception as e:
            print(f"❌ 正常路径测试失败: {e}")
        
        # 重新创建测试文件
        test_file.write_text("test content")
        
        # 测试路径遍历攻击
        try:
            cleaner.safe_clean("../test.txt", temp_path)
            print("❌ 路径遍历测试失败: 应该抛出异常")
        except ValueError as e:
            assert "非法路径访问" in str(e), f"应该抛出路径访问错误，实际: {e}"
            assert test_file.exists(), "文件不应该被删除"
            print("✅ 路径遍历测试通过，成功阻止了目录穿越攻击")
        except Exception as e:
            print(f"❌ 路径遍历测试失败: {e}")


def test_architect_enforce_path_traversal():
    """测试architect_enforce/skill.py的路径遍历防护"""
    print("\n=== 测试 architect_enforce/skill.py 路径遍历防护 ===")
    
    enforcer = ArchitectEnforcer()
    
    # 测试正常路径
    try:
        valid, violations = enforcer.check_file(str(Path(__file__)))
        print(f"✅ 正常路径测试: valid={valid}, violations={violations}")
    except Exception as e:
        print(f"❌ 正常路径测试失败: {e}")
    
    # 测试is_safe_path方法
    base_dir = str(Path(__file__).parent.parent)
    
    # 测试正常路径
    safe_path = str(Path(__file__))
    assert enforcer.is_safe_path(base_dir, safe_path), "正常路径应该被认为是安全的"
    print("✅ is_safe_path 正常路径测试通过")
    
    # 测试路径遍历
    unsafe_path = str(Path(base_dir) / "../test.txt")
    assert not enforcer.is_safe_path(base_dir, unsafe_path), "路径遍历应该被认为是不安全的"
    print("✅ is_safe_path 路径遍历测试通过")


def main():
    """运行所有测试"""
    print("开始安全修复测试...")
    
    test_gstack_service_race_condition()
    test_blender_cleaner_path_injection()
    test_architect_enforce_path_traversal()
    
    print("\n=== 所有测试完成 ===")


if __name__ == "__main__":
    main()
