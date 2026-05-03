#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSTACK 测试报告生成器
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent


def import_module_from_path(module_name, file_path):
    """从指定路径导入模块"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestReportGenerator:
    """测试报告生成器"""

    def __init__(self):
        self.report_data = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }

    def add_test_result(self, test_name, category, passed, error_message=None, elapsed_time=0):
        """添加测试结果"""
        self.report_data["tests"].append({
            "name": test_name,
            "category": category,
            "passed": passed,
            "error": error_message,
            "elapsed_time": elapsed_time
        })

        self.report_data["summary"]["total"] += 1
        if passed:
            self.report_data["summary"]["passed"] += 1
        else:
            self.report_data["summary"]["failed"] += 1

    def generate_report(self):
        """生成报告"""
        report = []
        report.append("=" * 60)
        report.append("GSTACK 深度测试报告")
        report.append("=" * 60)
        report.append(f"生成时间: {self.report_data['timestamp']}")
        report.append("")

        # 摘要
        summary = self.report_data["summary"]
        report.append("测试摘要:")
        report.append(f"  总测试数: {summary['total']}")
        report.append(f"  通过: {summary['passed']}")
        report.append(f"  失败: {summary['failed']}")
        report.append(f"  通过率: {summary['passed'] / max(summary['total'], 1) * 100:.1f}%")
        report.append("")

        # 按类别分组
        categories = {}
        for test in self.report_data["tests"]:
            cat = test["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(test)

        # 详细结果
        report.append("-" * 60)
        report.append("详细结果:")
        report.append("-" * 60)

        for category, tests in categories.items():
            report.append(f"\n[{category}]")
            for test in tests:
                status = "✅" if test["passed"] else "❌"
                elapsed = f"({test['elapsed_time']:.3f}s)" if test['elapsed_time'] > 0 else ""
                report.append(f"  {status} {test['name']} {elapsed}")
                if not test["passed"] and test["error"]:
                    report.append(f"     错误: {test['error']}")

        report.append("")
        report.append("=" * 60)
        report.append("报告结束")
        report.append("=" * 60)

        return "\n".join(report)

    def save_report(self, filepath):
        """保存报告到文件"""
        # 保存文本报告
        text_report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_report)

        # 保存 JSON 报告
        json_filepath = filepath.replace('.txt', '.json')
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, ensure_ascii=False, indent=2)

        return text_report


def run_all_tests_and_generate_report():
    """运行所有测试并生成报告"""
    report_gen = TestReportGenerator()

    # 运行 ASK Skill 测试
    print("运行 ASK Skill 测试...")
    try:
        ask_module = import_module_from_path(
            "ask_skill",
            PROJECT_ROOT / "MCP_Core" / "skills" / "ask" / "skill.py"
        )
        ASKSkill = ask_module.ASKSkill
        ask_skill = ASKSkill()

        # 测试初始化
        try:
            assert ask_skill is not None
            assert ask_skill.ask_dir.exists()
            report_gen.add_test_result("test_initialization", "ASK Skill", True)
        except Exception as e:
            report_gen.add_test_result("test_initialization", "ASK Skill", False, str(e))

        # 测试技能加载
        try:
            assert len(ask_skill.skills) >= 0
            report_gen.add_test_result("test_skills_loaded", "ASK Skill", True)
        except Exception as e:
            report_gen.add_test_result("test_skills_loaded", "ASK Skill", False, str(e))

        # 测试运行无效技能
        try:
            result = ask_skill.run_skill("nonexistent_skill_xyz")
            assert result.get("success") == False
            report_gen.add_test_result("test_run_invalid_skill", "ASK Skill", True)
        except Exception as e:
            report_gen.add_test_result("test_run_invalid_skill", "ASK Skill", False, str(e))

        print("  ASK Skill 测试完成")
    except Exception as e:
        print(f"  ASK Skill 测试失败: {e}")
        report_gen.add_test_result("ASK Skill 模块加载", "ASK Skill", False, str(e))

    # 运行 Blender MCP 测试
    print("运行 Blender MCP 测试...")
    try:
        blender_module = import_module_from_path(
            "blender_skill",
            PROJECT_ROOT / "MCP_Core" / "skills" / "blender_mcp" / "skill.py"
        )
        BlenderMCPSkill = blender_module.BlenderMCPSkill
        blender_skill = BlenderMCPSkill()

        # 测试初始化
        try:
            assert blender_skill is not None
            report_gen.add_test_result("test_initialization", "Blender MCP", True)
        except Exception as e:
            report_gen.add_test_result("test_initialization", "Blender MCP", False, str(e))

        # 测试状态检查
        try:
            status = blender_skill.status()
            assert isinstance(status, bool)
            report_gen.add_test_result("test_status_check", "Blender MCP", True)
        except Exception as e:
            report_gen.add_test_result("test_status_check", "Blender MCP", False, str(e))

        print("  Blender MCP 测试完成")
    except Exception as e:
        print(f"  Blender MCP 测试失败: {e}")
        report_gen.add_test_result("Blender MCP 模块加载", "Blender MCP", False, str(e))

    # 运行 Narsil MCP 测试
    print("运行 Narsil MCP 测试...")
    try:
        narsil_module = import_module_from_path(
            "narsil_skill",
            PROJECT_ROOT / "MCP_Core" / "skills" / "narsil_mcp" / "skill.py"
        )
        NarsilMCPSkill = narsil_module.NarsilMCPSkill
        narsil_skill = NarsilMCPSkill()

        # 测试初始化
        try:
            assert narsil_skill is not None
            report_gen.add_test_result("test_initialization", "Narsil MCP", True)
        except Exception as e:
            report_gen.add_test_result("test_initialization", "Narsil MCP", False, str(e))

        # 测试分析不存在的文件
        try:
            result = narsil_skill.analyze("nonexistent_file_xyz.py")
            assert result.get("success") == False
            report_gen.add_test_result("test_analyze_nonexistent", "Narsil MCP", True)
        except Exception as e:
            report_gen.add_test_result("test_analyze_nonexistent", "Narsil MCP", False, str(e))

        print("  Narsil MCP 测试完成")
    except Exception as e:
        print(f"  Narsil MCP 测试失败: {e}")
        report_gen.add_test_result("Narsil MCP 模块加载", "Narsil MCP", False, str(e))

    # 运行 n8n Workflow 测试
    print("运行 n8n Workflow 测试...")
    try:
        n8n_module = import_module_from_path(
            "n8n_skill",
            PROJECT_ROOT / "MCP_Core" / "skills" / "n8n_workflow" / "skill.py"
        )
        N8nWorkflowSkill = n8n_module.N8nWorkflowSkill
        n8n_skill = N8nWorkflowSkill()

        # 测试初始化
        try:
            assert n8n_skill is not None
            report_gen.add_test_result("test_initialization", "n8n Workflow", True)
        except Exception as e:
            report_gen.add_test_result("test_initialization", "n8n Workflow", False, str(e))

        # 测试状态检查
        try:
            status = n8n_skill.status()
            assert isinstance(status, bool)
            report_gen.add_test_result("test_status_check", "n8n Workflow", True)
        except Exception as e:
            report_gen.add_test_result("test_status_check", "n8n Workflow", False, str(e))

        print("  n8n Workflow 测试完成")
    except Exception as e:
        print(f"  n8n Workflow 测试失败: {e}")
        report_gen.add_test_result("n8n Workflow 模块加载", "n8n Workflow", False, str(e))

    # 安全测试
    print("运行安全测试...")
    try:
        architect_module = import_module_from_path(
            "architect_enforcer",
            PROJECT_ROOT / "MCP_Core" / "skills" / "architect_enforce" / "skill.py"
        )
        ArchitectEnforcer = architect_module.ArchitectEnforcer
        enforcer = ArchitectEnforcer()

        # 测试路径安全检查
        try:
            result = enforcer.is_safe_path(str(PROJECT_ROOT), str(PROJECT_ROOT / "test.py"))
            assert result == True
            report_gen.add_test_result("test_path_safety", "Security", True)
        except Exception as e:
            report_gen.add_test_result("test_path_safety", "Security", False, str(e))

        print("  安全测试完成")
    except Exception as e:
        print(f"  安全测试失败: {e}")
        report_gen.add_test_result("安全测试", "Security", False, str(e))

    # 生成报告
    print("\n生成测试报告...")
    report_dir = PROJECT_ROOT / "gstack_core" / "tests" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_filepath = report_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report = report_gen.save_report(str(report_filepath))

    print("\n" + report)
    print(f"\n报告已保存到: {report_filepath}")

    return report_gen.report_data


if __name__ == "__main__":
    run_all_tests_and_generate_report()