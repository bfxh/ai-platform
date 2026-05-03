#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narsil MCP 单元测试
"""

import sys
import os
from pathlib import Path
import tempfile
import ast

# 添加项目根目录到 Python 路径

# 导入 Narsil MCP Skill
from ..skill import NarsilMCPSkill


class TestNarsilMCP:
    """Narsil MCP 测试类"""

    def setup_method(self):
        """测试前设置"""
        self.narsil_skill = NarsilMCP()

    def test_initialization(self):
        """测试 Narsil MCP 初始化"""
        assert self.narsil_skill is not None
        assert self.narsil_skill.server_url == "http://localhost:8401"

    def test_status_check(self):
        """测试状态检查"""
        # 服务可能离线，这是预期的
        status = self.narsil_skill.status()
        assert isinstance(status, bool)

    def test_analyze_code_local(self):
        """测试本地代码分析"""
        # 创建一个临时 Python 文件进行分析
        test_code = '''
def hello():
    """测试函数"""
    print("Hello, World!")

class TestClass:
    """测试类"""
    def method(self):
        return 42
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code)
            temp_file = f.name

        try:
            result = self.narsil_skill.analyze(temp_file)
            assert result is not None
            assert result.get("success") == True
            data = result.get("data", {})
            assert "files" in data
            assert len(data["files"]) > 0
        finally:
            os.unlink(temp_file)

    def test_analyze_nonexistent_file(self):
        """测试分析不存在的文件"""
        result = self.narsil_skill.analyze("nonexistent_file_xyz.py")
        assert result is not None
        assert result.get("success") == False

    def test_execute_status(self):
        """测试 execute 函数 status 命令"""
        from ..skill import execute
        result = execute("status")
        assert result is not None
        assert "success" in result
        assert result["success"] == True

    def test_execute_analyze_missing_path(self):
        """测试 execute 函数 analyze 缺少路径"""
        from ..skill import execute
        result = execute("analyze")
        assert result is not None
        assert result.get("success") == False

    def test_execute_unknown_command(self):
        """测试执行未知命令"""
        from ..skill import execute
        result = execute("unknown_command")
        assert result is not None
        assert result.get("success") == False


class TestNarsilMCPAnalysis:
    """Narsil MCP 代码分析测试"""

    def setup_method(self):
        """测试前设置"""
        self.narsil_skill = NarsilMCP()

    def test_symbol_extraction(self):
        """测试符号提取"""
        test_code = '''
def function_a():
    pass

def function_b():
    pass

class MyClass:
    def method_a(self):
        pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code)
            temp_file = f.name

        try:
            result = self.narsil_skill.analyze(temp_file)
            assert result.get("success") == True
            data = result.get("data", {})
            files = data.get("files", [])
            if files:
                file_data = files[0]
                assert file_data.get("function_count", 0) >= 2
                assert file_data.get("class_count", 0) >= 1
        finally:
            os.unlink(temp_file)

    def test_import_analysis(self):
        """测试导入分析"""
        test_code = '''
import os
import sys
from pathlib import Path

def test():
    pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code)
            temp_file = f.name

        try:
            result = self.narsil_skill.analyze(temp_file)
            assert result.get("success") == True
            data = result.get("data", {})
            files = data.get("files", [])
            if files:
                file_data = files[0]
                assert file_data.get("import_count", 0) >= 3
        finally:
            os.unlink(temp_file)

    def test_hardcoded_path_detection(self):
        """测试硬编码路径检测"""
        test_code = '''
def test():
    path = "C:\\\\Users\\\\test"
    return path
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code)
            temp_file = f.name

        try:
            result = self.narsil_skill.analyze(temp_file)
            assert result.get("success") == True
            data = result.get("data", {})
            files = data.get("files", [])
            if files:
                file_data = files[0]
                # 检查是否有硬编码路径
                hardcoded_paths = file_data.get("hardcoded_paths", [])
                assert isinstance(hardcoded_paths, list)
        finally:
            os.unlink(temp_file)

    def test_empty_except_detection(self):
        """测试空异常处理检测"""
        test_code = '''
def test():
    try:
        x = 1
    except:
        pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code)
            temp_file = f.name

        try:
            result = self.narsil_skill.analyze(temp_file)
            assert result.get("success") == True
            data = result.get("data", {})
            files = data.get("files", [])
            if files:
                file_data = files[0]
                assert file_data.get("empty_except_count", 0) >= 1
        finally:
            os.unlink(temp_file)


def run_tests():
    """运行所有测试"""
    test_instance = TestNarsilMCP()

    print("运行 Narsil MCP 测试...")
    print("=" * 50)

    # 测试初始化
    try:
        test_instance.setup_method()
        test_instance.test_initialization()
        print("✅ test_initialization 通过")
    except Exception as e:
        print(f"❌ test_initialization 失败: {e}")

    # 测试状态检查
    try:
        test_instance.setup_method()
        test_instance.test_status_check()
        print("✅ test_status_check 通过")
    except Exception as e:
        print(f"❌ test_status_check 失败: {e}")

    # 测试本地代码分析
    try:
        test_instance.setup_method()
        test_instance.test_analyze_code_local()
        print("✅ test_analyze_code_local 通过")
    except Exception as e:
        print(f"❌ test_analyze_code_local 失败: {e}")

    # 测试分析不存在的文件
    try:
        test_instance.setup_method()
        test_instance.test_analyze_nonexistent_file()
        print("✅ test_analyze_nonexistent_file 通过")
    except Exception as e:
        print(f"❌ test_analyze_nonexistent_file 失败: {e}")

    # 测试 execute status
    try:
        test_instance.setup_method()
        test_instance.test_execute_status()
        print("✅ test_execute_status 通过")
    except Exception as e:
        print(f"❌ test_execute_status 失败: {e}")

    # 测试符号提取
    try:
        TestNarsilMCPAnalysis().test_symbol_extraction()
        print("✅ test_symbol_extraction 通过")
    except Exception as e:
        print(f"❌ test_symbol_extraction 失败: {e}")

    # 测试导入分析
    try:
        TestNarsilMCPAnalysis().test_import_analysis()
        print("✅ test_import_analysis 通过")
    except Exception as e:
        print(f"❌ test_import_analysis 失败: {e}")

    # 测试硬编码路径检测
    try:
        TestNarsilMCPAnalysis().test_hardcoded_path_detection()
        print("✅ test_hardcoded_path_detection 通过")
    except Exception as e:
        print(f"❌ test_hardcoded_path_detection 失败: {e}")

    # 测试空异常处理检测
    try:
        TestNarsilMCPAnalysis().test_empty_except_detection()
        print("✅ test_empty_except_detection 通过")
    except Exception as e:
        print(f"❌ test_empty_except_detection 失败: {e}")

    print("=" * 50)
    print("Narsil MCP 测试完成")


if __name__ == "__main__":
    run_tests()