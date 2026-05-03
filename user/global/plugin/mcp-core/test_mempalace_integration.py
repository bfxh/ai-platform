#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 MemPalace 技能集成到 MCP Core
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from skills.base import get_registry
from skills.mempalace import MemPalaceSkill

def test_skill_integration():
    """测试技能集成"""
    print("=" * 60)
    print("测试 MemPalace 技能集成")
    print("=" * 60)

    # 1. 测试技能实例化
    print("\n1. 测试技能实例化...")
    try:
        skill = MemPalaceSkill()
        print(f"   ✓ 技能名称: {skill.name}")
        print(f"   ✓ 技能描述: {skill.description}")
        print(f"   ✓ 技能版本: {skill.version}")
        print(f"   ✓ 技能作者: {skill.author}")
    except Exception as e:
        print(f"   ✗ 实例化失败: {e}")
        return False

    # 2. 测试技能初始化
    print("\n2. 测试技能初始化...")
    try:
        skill.initialize()
        print("   ✓ 技能初始化成功")
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        return False

    # 3. 测试技能注册
    print("\n3. 测试技能注册...")
    try:
        registry = get_registry()
        registry.register(skill)
        print("   ✓ 技能注册成功")
    except Exception as e:
        print(f"   ✗ 注册失败: {e}")
        return False

    # 4. 测试技能列表
    print("\n4. 测试技能列表...")
    try:
        skills = registry.list_skills()
        mempalace_found = any(s.name == "mempalace" for s in skills)
        if mempalace_found:
            print("   ✓ MemPalace 技能在技能列表中")
        else:
            print("   ✗ MemPalace 技能未在技能列表中")
            return False
    except Exception as e:
        print(f"   ✗ 获取技能列表失败: {e}")
        return False

    # 5. 测试参数定义
    print("\n5. 测试参数定义...")
    try:
        params = skill.get_parameters()
        print(f"   ✓ 参数定义: {len(params)} 个参数")
        print(f"   ✓ 支持的动作: {params.get('action', {}).get('enum', [])}")
    except Exception as e:
        print(f"   ✗ 获取参数定义失败: {e}")
        return False

    # 6. 测试参数验证
    print("\n6. 测试参数验证...")
    try:
        # 测试有效参数
        is_valid, error = skill.validate_params({"action": "create_wing", "wing_name": "test", "wing_type": "project"})
        if is_valid:
            print("   ✓ 有效参数验证通过")
        else:
            print(f"   ✗ 有效参数验证失败: {error}")
            return False

        # 测试无效参数
        is_valid, error = skill.validate_params({})
        if not is_valid:
            print("   ✓ 无效参数验证通过")
        else:
            print("   ✗ 无效参数验证失败")
            return False
    except Exception as e:
        print(f"   ✗ 参数验证失败: {e}")
        return False

    # 7. 测试技能执行 - 创建侧厅
    print("\n7. 测试技能执行 - 创建侧厅...")
    try:
        result = skill.execute({
            "action": "create_wing",
            "wing_name": "测试侧厅",
            "wing_type": "project"
        })
        if result.get("success"):
            print(f"   ✓ 创建侧厅成功: {result.get('message')}")
        else:
            print(f"   ✗ 创建侧厅失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ✗ 执行失败: {e}")
        return False

    # 8. 测试技能执行 - 创建房间
    print("\n8. 测试技能执行 - 创建房间...")
    try:
        result = skill.execute({
            "action": "create_room",
            "wing_name": "测试侧厅",
            "room_name": "测试房间"
        })
        if result.get("success"):
            print(f"   ✓ 创建房间成功: {result.get('message')}")
        else:
            print(f"   ✗ 创建房间失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ✗ 执行失败: {e}")
        return False

    # 9. 测试技能执行 - 存储记忆
    print("\n9. 测试技能执行 - 存储记忆...")
    try:
        result = skill.execute({
            "action": "store_memory",
            "wing_name": "测试侧厅",
            "room_name": "测试房间",
            "memory_text": "这是一条测试记忆，用于验证 MemPalace 技能的集成。",
            "metadata": {"test": True}
        })
        if result.get("success"):
            print(f"   ✓ 存储记忆成功: {result.get('message')}")
            print(f"   ✓ 压缩比: {result.get('compression_ratio', 0):.2f}")
        else:
            print(f"   ✗ 存储记忆失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ✗ 执行失败: {e}")
        return False

    # 10. 测试技能执行 - 检索记忆
    print("\n10. 测试技能执行 - 检索记忆...")
    try:
        result = skill.execute({
            "action": "retrieve_memory",
            "wing_name": "测试侧厅",
            "room_name": "测试房间",
            "limit": 5
        })
        if result.get("success"):
            print(f"   ✓ 检索记忆成功: 找到 {result.get('count', 0)} 条记忆")
        else:
            print(f"   ✗ 检索记忆失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ✗ 执行失败: {e}")
        return False

    # 11. 测试技能执行 - 获取统计信息
    print("\n11. 测试技能执行 - 获取统计信息...")
    try:
        result = skill.execute({"action": "get_stats"})
        if result.get("success"):
            stats = result.get("stats", {})
            print(f"   ✓ 侧厅数量: {stats.get('wings', 0)}")
            print(f"   ✓ 房间数量: {stats.get('rooms', 0)}")
            print(f"   ✓ 记忆数量: {stats.get('memories', 0)}")
            print(f"   ✓ 知识数量: {stats.get('knowledge', 0)}")
        else:
            print(f"   ✗ 获取统计信息失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ✗ 执行失败: {e}")
        return False

    # 12. 测试技能关闭
    print("\n12. 测试技能关闭...")
    try:
        skill.shutdown()
        print("   ✓ 技能关闭成功")
    except Exception as e:
        print(f"   ✗ 关闭失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ 所有测试通过！MemPalace 技能已成功集成到 MCP Core")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_skill_integration()
    sys.exit(0 if success else 1)
