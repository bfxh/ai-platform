#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAE启动时自动运行的GStack技能管理初始化脚本

此脚本在TRAE/MCP Core启动时自动运行，初始化GStack技能管理系统。
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def initialize_gstack_skills():
    """初始化GStack技能管理系统"""
    print("=" * 60)
    print("🚀 GStack技能管理系统初始化")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 导入GStack技能管理器
        from gstack_skill_manager import GStackSkillManager

        # 创建技能管理器实例
        print("📦 创建GStack技能管理器...")
        manager = GStackSkillManager()

        # 注册GitHub工具技能
        print("\n📝 注册GitHub工具技能...")

        # 智能GitHub API管理器
        print("  - 注册智能GitHub API管理器...")
        manager.register_skill("smart_github_api_manager", {
            "name": "smart_github_api_manager",
            "version": "2.0.0",
            "description": "智能GitHub API管理 - 实时同步、智能分类、版本管理",
            "author": "MCP Core Team",
            "path": "/python/MCP_Core/skills/smart_github_api_manager/skill.py",
            "dependencies": ["requests", "beautifulsoup4", "lxml"]
        })

        # GitHub NLP搜索
        print("  - 注册GitHub NLP搜索...")
        manager.register_skill("github_nlp_search", {
            "name": "github_nlp_search",
            "version": "1.0.0",
            "description": "GitHub API自然语言搜索与推荐 - 理解自然语言查询，智能推荐API，生成示例代码",
            "author": "MCP Core Team",
            "path": "/python/MCP_Core/skills/github_nlp_search/skill.py",
            "dependencies": ["requests"]
        })

        # GitHub API测试工具
        print("  - 注册GitHub API测试工具...")
        manager.register_skill("github_api_tester", {
            "name": "github_api_tester",
            "version": "1.0.0",
            "description": "高级GitHub API测试工具 - 批量测试、实时调试、性能测试",
            "author": "MCP Core Team",
            "path": "/python/MCP_Core/skills/github_api_tester/skill.py",
            "dependencies": ["requests", "concurrent.futures"]
        })

        # GitHub扩展功能
        print("  - 注册GitHub扩展功能...")
        manager.register_skill("github_extended", {
            "name": "github_extended",
            "version": "1.0.0",
            "description": "GitHub扩展功能系统 - 速率限制管理、批量操作、数据处理、分析工具",
            "author": "MCP Core Team",
            "path": "/python/MCP_Core/skills/github_extended/skill.py",
            "dependencies": ["requests", "matplotlib", "pandas"]
        })

        # 列出所有已注册的技能
        print("\n✅ 已注册的技能:")
        skills = manager.list_skills()
        for skill in skills:
            print(f"  - {skill['name']} v{skill['version']}")

        # 检查技能更新
        print("\n🔍 检查技能更新...")
        updates = manager.check_skill_updates()
        has_updates = False
        for update in updates:
            if update['current_version'] != update['latest_version']:
                print(f"  - {update['name']}: v{update['current_version']} -> v{update['latest_version']}")
                has_updates = True

        if not has_updates:
            print("  ✓ 所有技能都是最新版本")

        # 导出技能配置
        print("\n💾 导出技能配置...")
        export_result = manager.export_skills()
        print(f"  ✓ {export_result['message']}")

        print()
        print("=" * 60)
        print("✅ GStack技能管理系统初始化完成！")
        print("=" * 60)
        print()
        print("📚 可用技能:")
        print("  1. smart_github_api_manager - 智能GitHub API管理")
        print("  2. github_nlp_search - 自然语言搜索与推荐")
        print("  3. github_api_tester - 高级API测试工具")
        print("  4. github_extended - 扩展功能系统")
        print()
        print("🌐 Web界面: http://localhost:8000")
        print("📊 仪表盘: http://localhost:8000/dashboard")
        print()

        return True

    except Exception as e:
        print(f"\n❌ GStack技能管理系统初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = initialize_gstack_skills()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
