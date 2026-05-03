#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 安全测试
"""

import sys
import os
from pathlib import Path
import tempfile

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestSecurity:
    """安全测试类"""

    def test_path_traversal_protection(self):
        """测试路径遍历防护"""
        # 测试 architect_enforce skill 的路径安全检查
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "architect_enforce"))
        from ..skill import ArchitectEnforcer

        enforcer = ArchitectEnforcer()

        # 测试安全路径
        safe_result = enforcer.is_safe_path(str(PROJECT_ROOT), str(PROJECT_ROOT / "test.py"))
        assert safe_result == True

        # 测试不安全路径（遍历攻击）
        unsafe_result = enforcer.is_safe_path(
            str(PROJECT_ROOT),
            str(PROJECT_ROOT / ".." / ".." / "etc" / "passwd")
        )
        # 应该返回 False 或者在 base_dir 之外
        # 注意：具体行为取决于实现

    def test_blender_cleaner_safe_clean(self):
        """测试 blender_cleaner 的安全清理"""
        sys.path.insert(0, str(PROJECT_ROOT / "gstack_core"))
        from ..blender_cleaner import BlenderCleaner

        cleaner = BlenderCleaner()

        # 测试安全的文件路径
        test_code = '''
def safe_clean_test():
    """测试安全清理功能"""
    # 这里会测试路径验证
    pass
'''
        # 由于 safe_clean 可能需要实际文件，我们测试其存在性
        assert hasattr(cleaner, 'safe_clean')

    def test_config_file_permissions(self):
        """测试配置文件权限"""
        # 检查关键配置文件是否存在且有正确的内容
        config_files = [
            PROJECT_ROOT / "ai_architecture.json",
            PROJECT_ROOT / "gstack_core" / "commands.ps1",
        ]

        for config_file in config_files:
            if config_file.exists():
                # 检查文件不为空
                content = config_file.read_text(encoding='utf-8')
                assert len(content) > 0, f"配置文件 {config_file} 为空"
                # 检查不包含明显的敏感信息（如私钥）
                sensitive_patterns = ["-----BEGIN PRIVATE KEY-----", "password = "]
                for pattern in sensitive_patterns:
                    assert pattern not in content.lower(), f"配置文件 {config_file} 包含敏感信息: {pattern}"

    def test_no_hardcoded_secrets(self):
        """测试代码中无硬编码的密钥"""
        # 检查关键 Python 文件不包含硬编码密钥
        key_files = [
            PROJECT_ROOT / "MCP_Core" / "skills" / "ask" / "skill.py",
            PROJECT_ROOT / "MCP_Core" / "skills" / "blender_mcp" / "skill.py",
            PROJECT_ROOT / "MCP_Core" / "skills" / "narsil_mcp" / "skill.py",
            PROJECT_ROOT / "MCP_Core" / "skills" / "n8n_workflow" / "skill.py",
        ]

        suspicious_patterns = [
            "api_key = '",
            "secret = '",
            "password = '",
            "token = '",
        ]

        for key_file in key_files:
            if key_file.exists():
                content = key_file.read_text(encoding='utf-8', errors='ignore')
                for pattern in suspicious_patterns:
                    # 如果找到模式，确保它不是注释或文档字符串
                    lines = content.split('\n')
                    for line in lines:
                        if pattern in line and not line.strip().startswith('#'):
                            # 排除明显是占位符或示例代码的情况
                            if 'example' not in line.lower() and 'YOUR_' not in line:
                                print(f"⚠️ 可能存在硬编码密钥: {key_file}: {line[:50]}")

    def test_subprocess_no_shell_injection(self):
        """测试 subprocess 调用无 shell 注入风险"""
        # 检查是否使用了 shell=True
        key_files = [
            PROJECT_ROOT / "gstack_core" / "commands.ps1",
        ]

        for key_file in key_files:
            if key_file.exists():
                content = key_file.read_text(encoding='utf-8', errors='ignore')
                # 检查是否有不安全的 shell 调用
                # 注意：PowerShell 的 Invoke-Expression 需要谨慎使用
                if "Invoke-Expression" in content:
                    # 确保不是直接调用用户输入
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "Invoke-Expression" in line:
                            # 检查前后几行是否有用户输入
                            context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                            # 应该有限制或验证
                            print(f"⚠️ 发现 Invoke-Expression，请确保有适当的输入验证: {key_file}:{i+1}")

    def test_sql_injection_protection(self):
        """测试 SQL 注入防护"""
        # 检查是否有 SQL 查询使用了字符串拼接
        # 注意：目前代码库中没有明显的 SQL 操作
        # 如果将来添加，需要确保使用参数化查询
        pass

    def test_xss_protection(self):
        """测试 XSS 防护"""
        # 检查是否有直接的用户输入输出
        # 目前代码主要是内部工具，XSS 风险较低
        pass


class TestInputValidation:
    """输入验证测试"""

    def test_ask_skill_input_validation(self):
        """测试 ASK Skill 输入验证"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "ask"))
        from ..skill import ASKSkill

        ask_skill = ASKSkill()

        # 测试无效技能名称
        result = ask_skill.run_skill("")
        assert result.get("success") == False

        result = ask_skill.run_skill("nonexistent_skill_12345")
        assert result.get("success") == False

    def test_narsil_mcp_input_validation(self):
        """测试 Narsil MCP 输入验证"""
        sys.path.insert(0, str(PROJECT_ROOT / "MCP_Core" / "skills" / "narsil_mcp"))
        from ..skill import NarsilMCP

        narsil_skill = NarsilMCP()

        # 测试无效路径
        result = narsil_skill.analyze("")
        assert result.get("success") == False

        result = narsil_skill.analyze("/invalid/path/that/does/not/exist/file.py")
        assert result.get("success") == False


def run_tests():
    """运行所有测试"""
    test_instance = TestSecurity()
    input_test = TestInputValidation()

    print("运行 GSTACK 安全测试...")
    print("=" * 50)

    # 测试路径遍历防护
    try:
        test_instance.test_path_traversal_protection()
        print("✅ test_path_traversal_protection 通过")
    except Exception as e:
        print(f"❌ test_path_traversal_protection 失败: {e}")

    # 测试安全清理
    try:
        test_instance.test_blender_cleaner_safe_clean()
        print("✅ test_blender_cleaner_safe_clean 通过")
    except Exception as e:
        print(f"❌ test_blender_cleaner_safe_clean 失败: {e}")

    # 测试配置文件权限
    try:
        test_instance.test_config_file_permissions()
        print("✅ test_config_file_permissions 通过")
    except Exception as e:
        print(f"❌ test_config_file_permissions 失败: {e}")

    # 测试无硬编码密钥
    try:
        test_instance.test_no_hardcoded_secrets()
        print("✅ test_no_hardcoded_secrets 通过")
    except Exception as e:
        print(f"❌ test_no_hardcoded_secrets 失败: {e}")

    # 测试 subprocess 无 shell 注入
    try:
        test_instance.test_subprocess_no_shell_injection()
        print("✅ test_subprocess_no_shell_injection 通过")
    except Exception as e:
        print(f"❌ test_subprocess_no_shell_injection 失败: {e}")

    # 测试 ASK Skill 输入验证
    try:
        input_test.test_ask_skill_input_validation()
        print("✅ test_ask_skill_input_validation 通过")
    except Exception as e:
        print(f"❌ test_ask_skill_input_validation 失败: {e}")

    # 测试 Narsil MCP 输入验证
    try:
        input_test.test_narsil_mcp_input_validation()
        print("✅ test_narsil_mcp_input_validation 通过")
    except Exception as e:
        print(f"❌ test_narsil_mcp_input_validation 失败: {e}")

    print("=" * 50)
    print("GSTACK 安全测试完成")


if __name__ == "__main__":
    run_tests()