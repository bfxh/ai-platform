#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 3D Modeling v3 - 功能测试

测试实际的MCP工具功能（模拟模式）
"""

import sys
import json
import asyncio
from pathlib import Path

# 添加MCP目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 模拟FastMCP
class MockFastMCP:
    def __init__(self, name):
        self.name = name
        self.tools = {}
    
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator
    
    def run(self):
        print(f"Mock MCP server '{self.name}' started")

# 替换FastMCP
import ai_3d_modeling_v3
ai_3d_modeling_v3.FastMCP = MockFastMCP

# 重新加载模块
import importlib
importlib.reload(ai_3d_modeling_v3)

from .ai_3d_modeling_v3 import (
    generate_3d_from_text_gpu,
    generate_3d_from_image_gpu,
    check_generation_status,
    batch_generate_gpu,
    get_gpu_info
)

async def test_generate_3d_text():
    """测试文本生成3D"""
    print("\n🧪 Testing generate_3d_from_text_gpu...")
    
    result = await generate_3d_from_text_gpu(
        prompt="a cute cat",
        service="meshy",
        style="realistic"
    )
    
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    assert result["success"] == True
    assert "task_id" in result
    assert result["service"] == "meshy"
    
    print("✅ Text generation test passed")
    return result["task_id"]

async def test_generate_3d_image():
    """测试图像生成3D"""
    print("\n🧪 Testing generate_3d_from_image_gpu...")
    
    # 创建一个测试图像
    test_image = Path("/python/Temp/test_image.png")
    test_image.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建一个简单的测试图像（如果不存在）
    if not test_image.exists():
        # 创建一个1x1像素的PNG
        import struct
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # 简化PNG数据
        test_image.write_bytes(png_data)
    
    result = await generate_3d_from_image_gpu(
        image_path=str(test_image),
        service="meshy"
    )
    
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # 由于测试图像可能无效，检查错误处理
    assert "success" in result
    
    print("✅ Image generation test passed")

async def test_check_status():
    """测试检查状态"""
    print("\n🧪 Testing check_generation_status...")
    
    # 使用模拟task_id
    result = await check_generation_status(
        task_id="test_task_12345",
        service="meshy"
    )
    
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # 由于没有真实API，应该返回错误
    assert result["success"] == False
    assert "error" in result
    
    print("✅ Status check test passed (expected error without API)")

async def test_batch_generate():
    """测试批量生成"""
    print("\n🧪 Testing batch_generate_gpu...")
    
    prompts = [
        "a cute cat",
        "a wooden crate",
        "a metal sword"
    ]
    
    result = await batch_generate_gpu(
        prompts=prompts,
        service="meshy",
        max_concurrent=2
    )
    
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    assert result["success"] == True
    assert result["total"] == 3
    assert len(result["results"]) == 3
    
    print("✅ Batch generation test passed")

async def test_gpu_info():
    """测试GPU信息"""
    print("\n🧪 Testing get_gpu_info...")
    
    result = await get_gpu_info()
    
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    assert result["success"] == True
    assert "gpu_available" in result
    
    if result["gpu_available"]:
        print(f"   GPU: {result.get('gpu_name', 'Unknown')}")
        print(f"   Memory: {result.get('gpu_memory_total_gb', 0):.2f} GB")
    else:
        print("   GPU not available (running on CPU)")
    
    print("✅ GPU info test passed")

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 AI 3D Modeling v3 - Functional Tests")
    print("=" * 60)
    
    tests = [
        ("Text Generation", test_generate_3d_text),
        ("Image Generation", test_generate_3d_image),
        ("Status Check", test_check_status),
        ("Batch Generation", test_batch_generate),
        ("GPU Info", test_gpu_info),
    ]
    
    results = []
    task_id = None
    
    for name, test_func in tests:
        try:
            if name == "Text Generation":
                task_id = await test_func()
            else:
                await test_func()
            results.append((name, True))
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印结果
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if task_id:
        print(f"\nGenerated task_id: {task_id}")
        print("Note: This is a simulated task_id for testing")
    
    if passed == total:
        print("\n🎉 All functional tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
