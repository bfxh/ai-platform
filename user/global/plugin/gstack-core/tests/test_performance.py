#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 性能测试
"""

import sys
import os
from pathlib import Path
import time
import tempfile

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestPerformance:
    """性能测试类"""

    def test_code_analysis_performance(self):
        """测试代码分析性能 - 应该在 5 秒内完成"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "narsil_mcp"))
        from ..skill import NarsilMCP

        # 创建一个测试文件
        test_code = '''
def function1():
    pass

def function2():
    pass

def function3():
    pass

class TestClass:
    def method1(self):
        pass
    def method2(self):
        pass
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(test_code * 10)  # 增加代码量
            temp_file = f.name

        try:
            narsil_skill = NarsilMCP()

            start_time = time.time()
            result = narsil_skill.analyze(temp_file)
            elapsed_time = time.time() - start_time

            assert result.get("success") == True
            assert elapsed_time < 5.0, f"代码分析耗时 {elapsed_time:.2f} 秒，超过 5 秒限制"
            print(f"✅ 代码分析性能测试通过，耗时 {elapsed_time:.3f} 秒")
        finally:
            os.unlink(temp_file)

    def test_service_status_check_performance(self):
        """测试服务状态检查性能 - 应该在 1 秒内完成"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "blender_mcp"))
        from ..skill import BlenderMCPSkill

        blender_skill = BlenderMCPSkill()

        start_time = time.time()
        status = blender_skill.status()
        elapsed_time = time.time() - start_time

        assert isinstance(status, bool)
        assert elapsed_time < 1.0, f"状态检查耗时 {elapsed_time:.2f} 秒，超过 1 秒限制"
        print(f"✅ 服务状态检查性能测试通过，耗时 {elapsed_time:.3f} 秒")

    def test_n8n_status_check_performance(self):
        """测试 n8n 状态检查性能 - 应该在 1 秒内完成"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "n8n_workflow"))
        from ..skill import N8nWorkflowSkill

        n8n_skill = N8nWorkflowSkill()

        start_time = time.time()
        status = n8n_skill.status()
        elapsed_time = time.time() - start_time

        assert isinstance(status, bool)
        assert elapsed_time < 1.0, f"n8n 状态检查耗时 {elapsed_time:.2f} 秒，超过 1 秒限制"
        print(f"✅ n8n 状态检查性能测试通过，耗时 {elapsed_time:.3f} 秒")

    def test_ask_skill_initialization_performance(self):
        """测试 ASK Skill 初始化性能 - 应该在 2 秒内完成"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "ask"))
        from ..skill import ASKSkill

        start_time = time.time()
        ask_skill = ASKSkill()
        elapsed_time = time.time() - start_time

        assert ask_skill is not None
        assert elapsed_time < 2.0, f"ASK Skill 初始化耗时 {elapsed_time:.2f} 秒，超过 2 秒限制"
        print(f"✅ ASK Skill 初始化性能测试通过，耗时 {elapsed_time:.3f} 秒")

    def test_concurrent_operations(self):
        """测试并发操作性能"""
        import threading
        import queue

        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "blender_mcp"))
        from ..skill import BlenderMCPSkill

        results = queue.Queue()
        num_threads = 5

        def check_status():
            blender_skill = BlenderMCPSkill()
            start_time = time.time()
            status = blender_skill.status()
            elapsed_time = time.time() - start_time
            results.put(("status", elapsed_time, status))

        # 并发执行多个状态检查
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=check_status)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 检查结果
        total_time = 0
        while not results.empty():
            op, elapsed, status = results.get()
            total_time += elapsed

        avg_time = total_time / num_threads
        assert avg_time < 1.0, f"并发状态检查平均耗时 {avg_time:.2f} 秒，超过 1 秒限制"
        print(f"✅ 并发操作性能测试通过，平均耗时 {avg_time:.3f} 秒")


def run_tests():
    """运行所有测试"""
    test_instance = TestPerformance()

    print("运行 GSTACK 性能测试...")
    print("=" * 50)

    # 测试代码分析性能
    try:
        test_instance.test_code_analysis_performance()
        print("✅ test_code_analysis_performance 通过")
    except Exception as e:
        print(f"❌ test_code_analysis_performance 失败: {e}")

    # 测试服务状态检查性能
    try:
        test_instance.test_service_status_check_performance()
        print("✅ test_service_status_check_performance 通过")
    except Exception as e:
        print(f"❌ test_service_status_check_performance 失败: {e}")

    # 测试 n8n 状态检查性能
    try:
        test_instance.test_n8n_status_check_performance()
        print("✅ test_n8n_status_check_performance 通过")
    except Exception as e:
        print(f"❌ test_n8n_status_check_performance 失败: {e}")

    # 测试 ASK Skill 初始化性能
    try:
        test_instance.test_ask_skill_initialization_performance()
        print("✅ test_ask_skill_initialization_performance 通过")
    except Exception as e:
        print(f"❌ test_ask_skill_initialization_performance 失败: {e}")

    # 测试并发操作性能
    try:
        test_instance.test_concurrent_operations()
        print("✅ test_concurrent_operations 通过")
    except Exception as e:
        print(f"❌ test_concurrent_operations 失败: {e}")

    print("=" * 50)
    print("GSTACK 性能测试完成")


if __name__ == "__main__":
    run_tests()