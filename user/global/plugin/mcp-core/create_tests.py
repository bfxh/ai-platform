#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量创建技能测试文件
"""

from pathlib import Path

# 需要创建测试的技能列表
SKILLS_TO_TEST = [
    ("steam_plugin_manager", "SteamPluginManagerSkill", ["list", "install", "update"]),
    ("ue5_plugin_manager", "UE5PluginManagerSkill", ["download_plugins", "install_plugin", "get_recommendations"]),
    ("system_config", "SystemConfigSkill", ["configure_firewall", "enable_sharing", "get_status"]),
    ("ai_toolkit_linkage", "AIToolkitLinkageSkill", ["link", "unlink", "sync"]),
    ("plugin_adapter", "PluginAdapterSkill", ["adapt", "convert", "validate"]),
    ("godot_project_manager", "GodotProjectManagerSkill", ["open_project", "create_scene", "verify_physics"]),
    ("github_download", "GitHubDownloadSkill", ["download_repo", "download_release", "clone"]),
    ("github_repo_manager", "GitHubRepoManagerSkill", ["create_repo", "delete_repo", "list_repos"]),
    ("file_backup", "FileBackupSkill", ["backup", "restore", "list_backups"]),
    ("notification", "NotificationSkill", ["send", "schedule", "list"]),
    ("ai_toolkit_manager", "AIToolkitManagerSkill", ["install", "uninstall", "update"]),
    ("plugin_manager", "PluginManagerSkill", ["search", "install", "uninstall"]),
]


def generate_test_file(name, class_name, actions):
    """生成测试文件内容"""
    action_tests = ""
    for action in actions:
        action_tests += f"""
    def test_execute_{action}(self):
        \"\"\"测试执行 {action}\"\"\"
        skill = {class_name}()
        result = skill.execute({{"action": "{action}"}})
        assert isinstance(result, dict)
        assert "success" in result
"""

    return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} 技能测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from skills.{name}.skill import {class_name}


class Test{class_name}:
    """{class_name} 测试类"""

    def test_skill_initialization(self):
        """测试技能初始化"""
        skill = {class_name}()
        assert skill.name == "{name}"
        assert skill.version is not None
        assert skill.description is not None

    def test_get_parameters(self):
        """测试获取参数定义"""
        skill = {class_name}()
        params = skill.get_parameters()
        assert isinstance(params, dict)
        assert "action" in params

    def test_validate_params_missing_action(self):
        """测试参数验证 - 缺少 action"""
        skill = {class_name}()
        is_valid, error = skill.validate_params(dict())
        assert is_valid is False
        assert "action" in error.lower()

    def test_validate_params_valid(self):
        """测试参数验证 - 有效参数"""
        skill = {class_name}()
        is_valid, error = skill.validate_params({{"action": "{actions[0]}"}})
        assert is_valid is True
        assert error is None
{action_tests}
    def test_execute_invalid_action(self):
        """测试执行无效动作"""
        skill = {class_name}()
        result = skill.execute({{"action": "invalid_action"}})
        assert result["success"] is False
        assert "error" in result

    def test_execute_with_none_params(self):
        """测试执行 - None 参数"""
        skill = {class_name}()
        result = skill.execute(None)
        assert result["success"] is False

    def test_execute_with_empty_params(self):
        """测试执行 - 空参数字典"""
        skill = {class_name}()
        result = skill.execute(dict())
        assert result["success"] is False

    def test_config_access(self):
        """测试配置访问"""
        skill = {class_name}()
        config_value = skill.get_config("test_key", "default")
        assert config_value == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''


def main():
    """主函数"""
    tests_dir = Path("/python/MCP_Core/tests/test_skills")
    tests_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("开始创建技能测试文件")
    print("=" * 60)

    created_count = 0

    for name, class_name, actions in SKILLS_TO_TEST:
        test_file = tests_dir / f"test_{name}.py"

        if test_file.exists():
            print(f"  - 测试文件已存在: {test_file.name}")
            continue

        test_content = generate_test_file(name, class_name, actions)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        print(f"  ✓ 创建测试文件: {test_file.name}")
        created_count += 1

    print("\n" + "=" * 60)
    print(f"完成！创建了 {created_count} 个测试文件")
    print("=" * 60)


if __name__ == "__main__":
    main()
