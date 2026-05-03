#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单集成测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from skills.base import SkillRegistry
from skills.ai_toolkit_ecosystem.skill import AIToolkitEcosystem
from skills.download_manager.skill import DownloadManagerSkill
from skills.system_optimizer.skill import SystemOptimizerSkill

def test_skill_registry():
    """测试技能注册表"""
    print("测试技能注册表...")
    registry = SkillRegistry()
    skill = AIToolkitEcosystem()
    registry.register(skill)
    print(f"  技能注册成功: {skill.name}")
    print(f"  技能数量: {len(registry._skills)}")
    assert skill.name in registry._skills
    print("  ✓ 通过")

def test_skill_execution():
    """测试技能执行"""
    print("\n测试技能执行...")
    skill = AIToolkitEcosystem()
    result = skill.execute({'action': 'list'})
    print(f"  执行结果: {result['success']}")
    assert result['success'] is True
    print("  ✓ 通过")

def test_multiple_skills():
    """测试多个技能"""
    print("\n测试多个技能...")
    skills = {
        'ai_ecosystem': AIToolkitEcosystem(),
        'download_manager': DownloadManagerSkill(),
        'system_optimizer': SystemOptimizerSkill(),
    }
    
    for name, skill in skills.items():
        print(f"  测试 {name}...")
        assert skill.name is not None
        assert skill.version is not None
        print(f"    名称: {skill.name}, 版本: {skill.version}")
    
    print("  ✓ 通过")

def test_error_handling():
    """测试错误处理"""
    print("\n测试错误处理...")
    skill = AIToolkitEcosystem()
    result = skill.execute({'action': 'invalid_action'})
    print(f"  错误结果: {result}")
    assert result['success'] is False
    assert 'error' in result
    print("  ✓ 通过")

if __name__ == '__main__':
    print("=" * 50)
    print("开始集成测试")
    print("=" * 50)
    
    try:
        test_skill_registry()
        test_skill_execution()
        test_multiple_skills()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("所有集成测试通过!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
