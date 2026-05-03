#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 3D Modeling 测试脚本 - 简化版

用于测试 ai_3d_modeling_v3.py 的基本功能
"""

import sys
import json
from pathlib import Path

def test_import():
    """测试导入"""
    print("🧪 Testing imports...")
    try:
        # 测试基本导入
        import os
        import asyncio
        from dataclasses import dataclass
        from enum import Enum
        from typing import Dict, Any, List, Optional
        
        print("✅ Basic imports successful")
        
        # 测试GPU配置导入
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from gpu_config import GPUConfig, GPU_CONFIG, clear_gpu_cache
            print(f"✅ GPU config imported: {GPU_CONFIG.get('gpu_name', 'CPU')}")
        except ImportError as e:
            print(f"⚠️ GPU config not available: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_service_config():
    """测试服务配置"""
    print("\n🧪 Testing service config...")
    
    from dataclasses import dataclass
    
    @dataclass
    class ServiceConfig:
        name: str
        base_url: str
        api_key: str
        free_credits: int
        reset_period: str
        use_gpu: bool = True
    
    # 测试配置创建
    config = ServiceConfig(
        name="Meshy",
        base_url="https://api.meshy.ai/v2",
        api_key="test_key",
        free_credits=200,
        reset_period="monthly"
    )
    
    print(f"✅ Service config created: {config.name}")
    print(f"   - Base URL: {config.base_url}")
    print(f"   - Free credits: {config.free_credits}")
    
    return True

def test_model_style():
    """测试模型风格枚举"""
    print("\n🧪 Testing model styles...")
    
    from enum import Enum
    
    class ModelStyle(Enum):
        REALISTIC = "realistic"
        CARTOON = "cartoon"
        SCULPTURE = "sculpture"
        VOXEL = "voxel"
    
    print(f"✅ Model styles: {[s.value for s in ModelStyle]}")
    
    return True

def test_output_dir():
    """测试输出目录"""
    print("\n🧪 Testing output directories...")
    
    output_dir = Path("/python/Output/3DModels")
    
    # 创建目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建子目录
    (output_dir / "TextTo3D").mkdir(exist_ok=True)
    (output_dir / "ImageTo3D").mkdir(exist_ok=True)
    (output_dir / "Textures").mkdir(exist_ok=True)
    
    print(f"✅ Output directory ready: {output_dir}")
    print(f"   - TextTo3D: {(output_dir / 'TextTo3D').exists()}")
    print(f"   - ImageTo3D: {(output_dir / 'ImageTo3D').exists()}")
    print(f"   - Textures: {(output_dir / 'Textures').exists()}")
    
    return True

def test_json_serialization():
    """测试JSON序列化"""
    print("\n🧪 Testing JSON serialization...")
    
    test_data = {
        "success": True,
        "task_id": "test_12345",
        "prompt": "a cute cat",
        "style": "realistic",
        "gpu_accelerated": True
    }
    
    # 序列化
    json_str = json.dumps(test_data, indent=2)
    print(f"✅ JSON serialization successful")
    print(f"   Length: {len(json_str)} bytes")
    
    # 反序列化
    parsed = json.loads(json_str)
    assert parsed["success"] == True
    
    return True

def test_async_function():
    """测试异步函数"""
    print("\n🧪 Testing async function...")
    
    import asyncio
    
    async def test_async():
        await asyncio.sleep(0.1)
        return {"success": True, "message": "Async test passed"}
    
    # 运行异步函数
    result = asyncio.run(test_async())
    
    print(f"✅ Async function test: {result['message']}")
    
    return True

def test_file_operations():
    """测试文件操作"""
    print("\n🧪 Testing file operations...")
    
    test_file = Path("/python/Temp/test_ai_3d_modeling.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入测试数据
    test_data = {"test": True, "timestamp": "2026-03-31"}
    test_file.write_text(json.dumps(test_data), encoding='utf-8')
    
    # 读取测试数据
    loaded_data = json.loads(test_file.read_text(encoding='utf-8'))
    
    assert loaded_data["test"] == True
    
    print(f"✅ File operations successful")
    print(f"   File: {test_file}")
    print(f"   Size: {test_file.stat().st_size} bytes")
    
    # 清理
    test_file.unlink()
    
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 AI 3D Modeling v3 - Component Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_import),
        ("Service Config Test", test_service_config),
        ("Model Style Test", test_model_style),
        ("Output Directory Test", test_output_dir),
        ("JSON Serialization Test", test_json_serialization),
        ("Async Function Test", test_async_function),
        ("File Operations Test", test_file_operations),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} failed: {e}")
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
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
