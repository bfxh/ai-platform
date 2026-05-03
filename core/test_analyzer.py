#!/usr/bin/env python
"""AI Test Analyzer - AI驱动的测试分析器

Codex风格的自动化测试增强:
- Flake检测与根因分析
- AI驱动测试生成 (基于功能描述生成测试用例)
- 测试影响分析 (哪些代码变更影响哪些测试)
- 智能测试优先级
- 统一测试报告
- 自愈测试建议
"""

import json
import re
import sqlite3
import sys
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# 项目根路径
ROOT = Path(__file__).parent.parent  # \python\

# 尝试导入统一测试DB
try:
    from unified_test_db import UnifiedTestDB, get_test_db
except ImportError:
    UnifiedTestDB = None


class TestAnalyzer:
    """AI驱动测试分析器"""

    def __init__(self):
        self._db = None
        if UnifiedTestDB:
            try:
                self._db = get_test_db()
            except Exception:
                pass
        self._lock = threading.Lock()
        self._analysis_cache = {}

    @property
    def db(self):
        return self._db

    # ─── Flake检测与分析 ───────────────────────────────

    def detect_flakes(self, min_runs: int = 5, fail_rate_min: float = 0.1, fail_rate_max: float = 0.9) -> list:
        """检测不稳定的测试"""
        if not self._db:
            return self._basic_flake_detection()

        flakes = self._db.detect_flakes(min_runs, fail_rate_min, fail_rate_max)
        return self._enrich_flake_analysis(flakes)

    def _basic_flake_detection(self) -> list:
        """基本flake检测 (无需数据库)"""
        return [{"message": "统一测试DB未初始化，请先运行 unified_test_db 模块"}]

    def _enrich_flake_analysis(self, flakes: list) -> list:
        """用AI分析丰富flake信息"""
        for flake in flakes:
            flake["analysis"] = self._analyze_flake_pattern(flake)
            flake["recommendation"] = self._recommend_flake_fix(flake)
        return flakes

    def _analyze_flake_pattern(self, flake: dict) -> dict:
        """分析flake模式"""
        fail_rate = flake.get("fail_rate", 0)
        total_runs = flake.get("total_runs", 0)
        test_name = flake.get("test_name", "")

        patterns = []

        if fail_rate > 0.7:
            patterns.append(
                {
                    "type": "high_failure",
                    "confidence": 0.9,
                    "explanation": "该测试失败率较高，可能不是flake而是真实bug",
                }
            )
        elif 0.3 <= fail_rate <= 0.7:
            patterns.append(
                {
                    "type": "intermittent",
                    "confidence": 0.7,
                    "explanation": "间歇性失败，典型flake模式",
                }
            )

        if "timeout" in test_name.lower():
            patterns.append(
                {
                    "type": "timeout_sensitive",
                    "confidence": 0.8,
                    "explanation": "测试名称包含timeout，可能是网络/异步时序问题",
                }
            )
        if "wait" in test_name.lower() or "delay" in test_name.lower():
            patterns.append(
                {
                    "type": "timing_dependent",
                    "confidence": 0.6,
                    "explanation": "测试依赖等待/延迟，可能是竞态条件",
                }
            )

        if not patterns:
            patterns.append(
                {
                    "type": "unknown",
                    "confidence": 0.3,
                    "explanation": "需要更多数据来分析模式",
                }
            )

        return {
            "patterns": patterns,
            "suspected_causes": self._suggest_causes(flake),
            "confidence": max(p["confidence"] for p in patterns),
        }

    def _suggest_causes(self, flake: dict) -> list:
        """推测flake根因"""
        causes = []
        fail_rate = flake.get("fail_rate", 0)
        test_name = flake.get("test_name", "").lower()

        if "timeout" in test_name:
            causes.append("网络超时或服务器响应过慢")
        if "click" in test_name or "selector" in test_name:
            causes.append("元素选择器不稳定或页面加载时序问题")
        if "api" in test_name:
            causes.append("API响应不一致或数据依赖问题")
        if fail_rate < 0.3:
            causes.append("环境波动 (负载、网络延迟)")
        if "auth" in test_name or "login" in test_name:
            causes.append("认证状态/token过期")

        if not causes:
            causes.append("环境/数据/时序相关问题")

        return causes

    def _recommend_flake_fix(self, flake: dict) -> list:
        """推荐flake修复方案"""
        recommendations = []
        test_name = flake.get("test_name", "").lower()

        if "timeout" in test_name or "wait" in test_name:
            recommendations.append("增加等待超时时间或使用更可靠的等待策略(waitForSelector代替固定delay)")
        if "click" in test_name:
            recommendations.append("使用data-testid属性代替CSS选择器，提高选择器稳定性")
        if "api" in test_name:
            recommendations.append("使用mock数据代替真实API调用，消除外部依赖")
        if flake.get("fail_rate", 0) > 0.5:
            recommendations.append("考虑重试机制: 失败后自动retry 2-3次")

        if not recommendations:
            recommendations.append("增加日志输出以追踪失败根因")

        recommendations.append("将该测试加入flake监控列表，持续观察")
        return recommendations

    # ─── AI测试生成 (Codex风格) ────────────────────────

    def generate_tests_from_description(
        self, description: str, framework: str = "playwright", language: str = "python"
    ) -> dict:
        """基于功能描述生成测试用例 (prompt engineering)

        Args:
            description: 功能描述文本
            framework: 目标测试框架
            language: 输出语言
        """
        # 解析描述
        features = self._parse_description(description)
        test_cases = self._generate_test_scenarios(features, framework)

        return {
            "description": description,
            "features_extracted": features,
            "test_cases": test_cases,
            "generated_at": datetime.now().isoformat(),
            "framework": framework,
        }

    def _parse_description(self, description: str) -> list:
        """从描述中提取测试点"""
        features = []

        # 提取关键词
        action_keywords = [
            "点击",
            "输入",
            "选择",
            "上传",
            "下载",
            "删除",
            "创建",
            "修改",
            "查询",
            "导出",
            "导入",
            "click",
            "input",
            "select",
            "upload",
            "download",
            "delete",
            "create",
            "update",
            "query",
            "export",
        ]

        ui_elements = [
            "按钮",
            "表单",
            "输入框",
            "下拉框",
            "弹窗",
            "模态框",
            "button",
            "form",
            "input",
            "dropdown",
            "modal",
            "dialog",
        ]

        scenarios = ["正常", "错误", "空值", "边界", "并发", "happy_path", "error", "empty", "edge_case", "boundary"]

        # 简单NLP: 按句号/换行分割
        sentences = re.split(r"[。！\n]", description)

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            actions_found = [kw for kw in action_keywords if kw in sentence.lower()]
            elements_found = [kw for kw in ui_elements if kw in sentence.lower()]

            features.append(
                {
                    "id": f"feature_{i+1}",
                    "description": sentence,
                    "actions": actions_found or ["操作"],
                    "elements": elements_found or ["界面"],
                }
            )

        return features

    def _generate_test_scenarios(self, features: list, framework: str) -> list:
        """为每个feature生成测试场景"""
        test_cases = []

        scenarios_map = {
            "happy_path": "正常流程测试",
            "validation": "输入验证测试",
            "empty_state": "空状态测试",
            "error_handling": "错误处理测试",
            "boundary": "边界值测试",
        }

        for feature in features:
            for sc_key, sc_name in scenarios_map.items():
                test_case = {
                    "id": f"tc_{feature['id']}_{sc_key}",
                    "name": f"[{sc_name}] {feature['description'][:80]}",
                    "feature": feature["description"][:200],
                    "scenario": sc_name,
                    "priority": "high" if sc_key == "happy_path" else "medium",
                    "steps": self._generate_test_steps(feature, sc_key, framework),
                }
                test_cases.append(test_case)

        return test_cases

    def _generate_test_steps(self, feature: dict, scenario: str, framework: str) -> list:
        """生成测试步骤"""
        steps = []

        if framework in ("playwright", "cypress"):
            steps.append("打开测试页面")
            steps.append(f"执行操作: {', '.join(feature['actions'])}")

            if scenario == "happy_path":
                steps.append("验证操作成功完成")
                steps.append("检查预期结果显示")
            elif scenario == "validation":
                steps.append("输入无效数据")
                steps.append("验证错误提示显示")
            elif scenario == "empty_state":
                steps.append("确认页面初始状态")
                steps.append("验证无数据时的占位符显示")
            elif scenario == "error_handling":
                steps.append("模拟错误条件")
                steps.append("验证错误处理机制")
            elif scenario == "boundary":
                steps.append("输入边界值 (最大值/最小值)")
                steps.append("验证边界处理正确")

        elif framework == "gametest":
            steps.append("启动游戏")
            steps.append(f"执行: {', '.join(feature['actions'])}")
            steps.append("截图验证结果")

        elif framework == "pytest":
            steps.append("准备测试数据")
            steps.append(f"调用: {', '.join(feature['actions'])}")
            steps.append("断言返回结果")

        return steps

    # ─── 测试影响分析 ──────────────────────────────────

    def analyze_impact(self, changed_files: list, project_root: Path = None) -> dict:
        """分析代码变更对测试的影响

        Args:
            changed_files: 变更的文件列表
            project_root: 项目根目录
        """
        if project_root is None:
            project_root = ROOT

        impacted_tests = []
        affected_suites = set()

        for file_path in changed_files:
            file_str = str(file_path)

            # 基于路径推断影响的测试套件
            if "cypress" in file_str:
                affected_suites.add("cypress")
            if "playwright" in file_str or "kit-qa" in file_str:
                affected_suites.add("playwright")
            if "game_test" in file_str or "minecraft" in file_str:
                affected_suites.add("gametest")

            # 查找最近的测试文件
            # 1. 同目录下查找 test_* 或 *_test 文件
            # 2. 在 tests/ 目录下查找同名文件
            parent_dir = Path(file_path).parent
            test_patterns = [
                parent_dir / f"test_{Path(file_path).stem}.py",
                parent_dir / f"{Path(file_path).stem}_test.py",
            ]
            for tp in test_patterns:
                if tp.exists():
                    impacted_tests.append(str(tp))

        return {
            "changed_files": changed_files,
            "affected_test_suites": list(affected_suites),
            "likely_impacted_tests": impacted_tests,
            "risk_level": "high" if len(affected_suites) > 2 else "medium" if affected_suites else "low",
            "recommendation": self._recommend_test_strategy(affected_suites),
        }

    def _recommend_test_strategy(self, affected_suites: set) -> list:
        """推荐测试策略"""
        recs = []
        if "cypress" in affected_suites:
            recs.append("运行 Cypress UI测试以验证前端变更")
        if "playwright" in affected_suites:
            recs.append("运行 Playwright E2E 和 API 测试")
        if "gametest" in affected_suites:
            recs.append("运行游戏自动化测试")
        if not recs:
            recs.append("运行冒烟测试集合")
        return recs

    # ─── 智能测试优先级 ────────────────────────────────

    def prioritize_tests(
        self,
        test_list: list = None,
        recent_failures: bool = True,
        flake_weight: float = 0.4,
        failure_weight: float = 0.4,
        duration_weight: float = 0.2,
    ) -> list:
        """按风险/优先级排序测试

        优先执行:
        1. 最近失败的测试
        2. 被标记为flaky的测试
        3. 快速执行的测试 (以便快速反馈)
        """
        if test_list is None and self._db:
            # 获取所有测试
            test_list = self._db.list_runs(limit=100)

        if not test_list:
            return []

        scored_tests = []
        for test in test_list:
            score = 0
            test_data = test if isinstance(test, dict) else {"name": str(test)}

            # 最近失败权重
            status = test_data.get("status", "")
            if status == "failed":
                score += failure_weight * 100
            elif status == "flaky" or test_data.get("is_flaky"):
                score += flake_weight * 100

            # 快速测试优先 (duration小的优先)
            duration = test_data.get("duration_ms", 0)
            if duration > 0:
                speed_score = max(0, (1 - duration / 300000)) * duration_weight * 100
                score += speed_score

            test_data["_priority_score"] = round(score, 1)
            scored_tests.append(test_data)

        scored_tests.sort(key=lambda x: x["_priority_score"], reverse=True)
        return scored_tests

    # ─── 统一报告生成 ──────────────────────────────────

    def generate_smart_report(self, date: str = None, include_ai_analysis: bool = True) -> dict:
        """生成智能统一报告"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        report = {
            "report_type": "ai_enhanced",
            "generated_at": datetime.now().isoformat(),
            "period": date,
            "summary": {},
            "flakes": {},
            "trends": {},
            "recommendations": [],
        }

        # 基础摘要
        if self._db:
            report["summary"] = self._db.get_summary(7)

        # Flake分析
        if include_ai_analysis:
            report["flakes"] = {
                "detected": self.detect_flakes(),
                "analysis": "AI驱动的flake检测基于统计模式和历史数据",
                "active_flake_count": len(self.detect_flakes()),
            }

        # 趋势
        if self._db:
            report["trends"] = self._db.get_trends(7)

        # AI建议
        report["recommendations"] = self._generate_ai_recommendations(report)

        return report

    def _generate_ai_recommendations(self, report: dict) -> list:
        """生成AI改进建议"""
        recs = []

        summary = report.get("summary", {})
        flakes = report.get("flakes", {}).get("detected", [])

        if flakes:
            recs.append(f"优先修复 {len(flakes)} 个不稳定测试以提高CI可靠性")

        total_passed = summary.get("total_passed", 0)
        total_failed = summary.get("total_failed", 0)
        if total_failed > total_passed * 0.1:
            recs.append("失败率较高，建议审查失败模式并进行批量修复")

        by_framework = summary.get("by_framework", [])
        for fw in by_framework:
            pass_rate = fw.get("pass_rate", 0)
            if pass_rate < 0.9:
                recs.append(f"{fw.get('framework', 'unknown')} 通过率低于90% ({pass_rate*100:.1f}%)，需要关注")

        if not recs:
            recs.append("测试整体状态良好")

        return recs

    # ─── 自愈建议 ──────────────────────────────────────

    def suggest_self_healing(self, failed_test: dict, error_message: str) -> dict:
        """对失败的测试提30供自愈建议

        分析失败原因并建议自动修复策略
        """
        suggestions = []

        error_lower = error_message.lower()

        # 选择器问题
        if "selector" in error_lower or "locator" in error_lower:
            suggestions.append(
                {
                    "type": "selector_healing",
                    "action": "自动修复选择器",
                    "method": "使用ai定位相似元素并生成新选择器",
                    "confidence": 0.7,
                }
            )

        # 超时问题
        if "timeout" in error_lower or "timed out" in error_lower:
            suggestions.append(
                {
                    "type": "timeout_healing",
                    "action": "调整超时参数",
                    "method": "自动增加等待时间或使用更智能的等待策略",
                    "confidence": 0.8,
                }
            )

        # 断言问题
        if "assert" in error_lower or "expect" in error_lower:
            suggestions.append(
                {
                    "type": "assertion_healing",
                    "action": "检查断言是否正确",
                    "method": "对比实际值和期望值，检查是否UI变更导致",
                    "confidence": 0.6,
                }
            )

        if not suggestions:
            suggestions.append(
                {
                    "type": "manual_review",
                    "action": "需要人工审查",
                    "method": "建议查看截图和日志分析根因",
                    "confidence": 0.3,
                }
            )

        return {
            "test": failed_test.get("test_name", "unknown"),
            "error": error_message[:500],
            "self_healing_suggestions": suggestions,
            "auto_fixable": any(s["confidence"] > 0.7 for s in suggestions),
        }

    # ─── 代码覆盖建议 ──────────────────────────────────

    def suggest_missing_tests(self, check_path: Path = None) -> list:
        """扫描代码文件并建议缺失的测试"""
        if check_path is None:
            check_path = ROOT / "core"

        missing = []
        code_files = list(check_path.rglob("*.py"))

        for cf in code_files[:50]:  # 限制数量
            test_file = check_path.parent / "tests" / f"test_{cf.name}"
            if not test_file.exists() and "test" not in cf.name.lower():
                # 尝试在其他常见位置查找
                alt_test = cf.parent / f"test_{cf.stem}.py"
                if not alt_test.exists():
                    missing.append(
                        {
                            "code_file": str(cf.relative_to(ROOT)),
                            "suggested_test": f"tests/test_{cf.name}",
                            "priority": "high" if cf.stat().st_size > 5000 else "low",
                        }
                    )

        return missing


# ─── 全局单例 ───────────────────────────────────────────
_analyzer_instance: Optional[TestAnalyzer] = None


def get_test_analyzer() -> TestAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TestAnalyzer()
    return _analyzer_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    analyzer = get_test_analyzer()
    print("=== AI Test Analyzer ===")

    # 测试生成
    result = analyzer.generate_tests_from_description(
        "用户登录页面：输入用户名和密码，点击登录按钮。" "登录成功后跳转到首页，登录失败显示错误提示。",
        framework="playwright",
    )
    print("\n### AI生成的测试用例 ###")
    for tc in result["test_cases"][:3]:
        print(f"  [{tc['priority']}] {tc['name']}")
        for step in tc["steps"]:
            print(f"    - {step}")

    # Flake检测
    print("\n### Flake检测 ###")
    flakes = analyzer.detect_flakes()
    print(f"检测到 {len(flakes)} 个潜在flake测试" if flakes else "数据库未连接")

    # 影响分析
    impact = analyzer.analyze_impact(["core/dispatcher.py", "core/workflow_engine.py"])
    print(f"\n### 影响分析 ###")
    print(f"风险等级: {impact['risk_level']}")
    print(f"影响套件: {impact['affected_test_suites']}")
