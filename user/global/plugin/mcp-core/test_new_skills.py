#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新技能集成到 MCP Core
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from skills.base import get_registry
from skills.github_api_manager import GitHubAPIManager
from skills.software_location_manager import SoftwareLocationManager

def test_github_api_manager():
    """测试GitHub API管理器技能"""
    print("=" * 60)
    print("测试 GitHub API 管理器技能")
    print("=" * 60)

    # 创建技能实例
    skill = GitHubAPIManager()
    assert skill.name == "github_api_manager"
    assert skill.description == "GitHub API管理 - 获取和管理GitHub所有API端点"
    print("✓ 技能实例化成功")

    # 初始化技能
    assert skill.initialize()
    print("✓ 技能初始化成功")

    # 测试获取所有API
    result = skill.execute({"action": "get_all_apis"})
    assert result["success"]
    assert "apis" in result
    print(f"✓ 获取所有API成功，共 {result['count']} 个API")

    # 测试搜索API
    result = skill.execute({"action": "search_apis", "query": "user"})
    assert result["success"]
    print(f"✓ 搜索API成功，找到 {result['count']} 个匹配结果")

    # 测试更新API
    result = skill.execute({"action": "update_apis"})
    assert result["success"]
    print("✓ 更新API成功")

    # 关闭技能
    skill.shutdown()
    print("✓ 技能关闭成功")

    print("\nGitHub API 管理器技能测试通过！")

def test_software_location_manager():
    """测试软件位置管理器技能"""
    print("\n" + "=" * 60)
    print("测试 软件位置管理器技能")
    print("=" * 60)

    # 创建技能实例
    skill = SoftwareLocationManager()
    assert skill.name == "software_location_manager"
    assert skill.description == "软件位置管理 - 管理软件安装位置和自动扫描"
    print("✓ 技能实例化成功")

    # 初始化技能
    assert skill.initialize()
    print("✓ 技能初始化成功")

    # 测试列出位置
    result = skill.execute({"action": "list_locations"})
    assert result["success"]
    assert "locations" in result
    print(f"✓ 列出位置成功，共 {result['count']} 个位置")
    for loc in result['locations']:
        print(f"  - {loc['path']} (类型: {loc['type']})")

    # 测试扫描位置
    result = skill.execute({"action": "scan_locations"})
    assert result["success"]
    print(f"✓ 扫描位置成功，{result['message']}")

    # 测试列出软件
    result = skill.execute({"action": "list_software"})
    assert result["success"]
    print(f"✓ 列出软件成功，共 {result['total_software']} 个软件")

    # 关闭技能
    skill.shutdown()
    print("✓ 技能关闭成功")

    print("\n软件位置管理器技能测试通过！")

def test_skill_registration():
    """测试技能注册"""
    print("\n" + "=" * 60)
    print("测试 技能注册")
    print("=" * 60)

    # 获取注册中心
    registry = get_registry()

    # 注册GitHub API管理器
    github_skill = GitHubAPIManager()
    assert registry.register(github_skill)
    print("✓ GitHub API管理器注册成功")

    # 注册软件位置管理器
    software_skill = SoftwareLocationManager()
    assert registry.register(software_skill)
    print("✓ 软件位置管理器注册成功")

    # 列出所有技能
    skills = registry.list_skills()
    github_found = any(s.name == "github_api_manager" for s in skills)
    software_found = any(s.name == "software_location_manager" for s in skills)

    assert github_found
    assert software_found
    print(f"✓ 技能列表中找到新技能，共 {len(skills)} 个技能")

    # 测试通过注册中心执行技能
    result = registry.execute("github_api_manager", {"action": "get_all_apis"})
    assert result["success"]
    print("✓ 通过注册中心执行GitHub API管理器成功")

    result = registry.execute("software_location_manager", {"action": "list_locations"})
    assert result["success"]
    print("✓ 通过注册中心执行软件位置管理器成功")

    # 关闭所有技能
    registry.shutdown_all()
    print("✓ 所有技能关闭成功")

    print("\n技能注册测试通过！")

if __name__ == "__main__":
    print("开始测试新技能集成...\n")

    try:
        test_github_api_manager()
        test_software_location_manager()
        test_skill_registration()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！新技能已成功集成到 MCP Core")
        print("=" * 60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
