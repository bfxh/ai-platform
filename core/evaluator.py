#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评估系统 — 技能评测、代码质量评分、回归检测、健康报告

核心设计:
- SkillBenchmark: 技能基准测试 (成功率/延迟/资源)
- QualityScorer: 代码质量评分 (正确性/效率/风格/安全 0-100)
- EvolutionFeeder: 评估结果反馈到 evo_engine 自进化
- RegressionDetector: 快照对比检测退化
- DashboardGenerator: 聚合健康报告

用法:
    from core.evaluator import SkillBenchmark, QualityScorer, DashboardGenerator

    bench = SkillBenchmark()
    bench.add_test_case("test-generator", {"prompt": "write add func"}, ["code"])
    results = bench.run_benchmark("test-generator")

    scorer = QualityScorer()
    scores = scorer.score_code("def add(a,b): return a+b")

    dash = DashboardGenerator()
    print(dash.generate_full_dashboard())
"""

import ast
import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


# ================================================================
# 技能基准测试
# ================================================================

class SkillBenchmark:
    """技能性能基准测试"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "storage" / "evo" / "benchmarks"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._test_cases: Dict[str, List[dict]] = defaultdict(list)
        self._results: Dict[str, List[dict]] = defaultdict(list)

        # 加载历史
        self._load_history()

    def add_test_case(self, skill_name: str, test_input: dict,
                      expected_keys: List[str] = None,
                      description: str = "") -> str:
        """添加测试用例

        Args:
            skill_name:     技能名称
            test_input:     输入参数
            expected_keys:  期望输出包含的键
            description:    测试描述
        Returns:
            test_id
        """
        test_id = f"{skill_name}_{len(self._test_cases[skill_name]) + 1}"
        self._test_cases[skill_name].append({
            "id": test_id,
            "skill": skill_name,
            "input": test_input,
            "expected_keys": expected_keys or [],
            "description": description,
            "created_at": datetime.now().isoformat(),
        })
        return test_id

    def run_benchmark(self, skill_name: str,
                      warmup: int = 0) -> Dict[str, Any]:
        """运行技能基准测试

        Returns:
            {"results": [...], "summary": {...}}
        """
        cases = self._test_cases.get(skill_name, [])
        if not cases:
            return {"error": f"无测试用例: {skill_name}"}

        results = []
        for case in cases:
            t0 = time.time()
            try:
                # 通过 dispatcher 执行
                from core.dispatcher import Dispatcher
                dispatcher = Dispatcher()
                output = dispatcher.dispatch(
                    "skill", skill_name,
                    **case["input"]
                )
                elapsed = time.time() - t0
                success = output.get("success", output.get("status") == "success")

                # 检查期望键
                matched_keys = []
                missing_keys = []
                for key in case.get("expected_keys", []):
                    if key in output:
                        matched_keys.append(key)
                    else:
                        missing_keys.append(key)

                results.append({
                    "test_id": case["id"],
                    "success": success,
                    "elapsed_ms": int(elapsed * 1000),
                    "output_keys": list(output.keys())[:10],
                    "matched_keys": matched_keys,
                    "missing_keys": missing_keys,
                    "error": output.get("error", ""),
                })
            except Exception as e:
                elapsed = time.time() - t0
                results.append({
                    "test_id": case["id"],
                    "success": False,
                    "elapsed_ms": int(elapsed * 1000),
                    "error": str(e),
                })

        # 汇总
        successes = sum(1 for r in results if r["success"])
        avg_ms = sum(r["elapsed_ms"] for r in results) / len(results) if results else 0
        summary = {
            "skill": skill_name,
            "total_tests": len(results),
            "passed": successes,
            "failed": len(results) - successes,
            "pass_rate": round(successes / len(results) * 100, 1) if results else 0,
            "avg_latency_ms": int(avg_ms),
            "timestamp": datetime.now().isoformat(),
        }

        # 持久化
        self._results[skill_name].append({"summary": summary, "details": results})
        self._save_results(skill_name)

        # 反馈到 evo_engine
        self._feed_evo(skill_name, summary)

        return {"results": results, "summary": summary}

    def run_all_benchmarks(self) -> dict:
        """运行所有已注册技能的基准测试"""
        all_results = {}
        for skill_name in self._test_cases:
            all_results[skill_name] = self.run_benchmark(skill_name)
        return all_results

    def get_summary(self, skill_name: str = None) -> dict:
        """获取基准测试摘要"""
        if skill_name:
            records = self._results.get(skill_name, [])
            return records[-1]["summary"] if records else {"error": "无结果"}
        return {
            sk: records[-1]["summary"] if records else {}
            for sk, records in self._results.items()
        }

    def load_test_cases(self, source_file: str) -> int:
        """从 YAML/JSON 文件批量加载测试用例"""
        source = Path(source_file)
        if not source.exists():
            return 0
        try:
            with open(source, "r", encoding="utf-8") as f:
                if source.suffix in (".yaml", ".yml"):
                    import yaml
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
        except Exception:
            return 0

        count = 0
        for entry in data if isinstance(data, list) else data.get("test_cases", []):
            self.add_test_case(
                entry.get("skill", ""),
                entry.get("input", {}),
                entry.get("expected_keys", []),
                entry.get("description", ""),
            )
            count += 1
        return count

    def _feed_evo(self, skill_name: str, summary: dict):
        """反馈基准结果到进化引擎"""
        try:
            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            evo.record(
                f"benchmark/{skill_name}", "run_benchmark",
                success=summary["pass_rate"] >= 80,
                elapsed=summary["avg_latency_ms"] / 1000,
                error="" if summary["pass_rate"] >= 80 else f"pass_rate={summary['pass_rate']}%",
                metadata={"pass_rate": summary["pass_rate"], "total": summary["total_tests"]}
            )
        except Exception:
            pass

    def _save_results(self, skill_name: str):
        filepath = self.data_dir / f"{skill_name}_benchmark.json"
        try:
            filepath.write_text(
                json.dumps(self._results[skill_name][-5:],
                          ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def _load_history(self):
        for filepath in self.data_dir.glob("*_benchmark.json"):
            try:
                skill_name = filepath.stem.replace("_benchmark", "")
                data = json.loads(filepath.read_text(encoding="utf-8"))
                self._results[skill_name] = data
            except Exception:
                pass


# ================================================================
# 代码质量评分
# ================================================================

class QualityScorer:
    """代码质量评分器 — 正确性 / 效率 / 风格 / 安全"""

    DANGER_PATTERNS = [
        (r"os\.system\(", "使用 os.system() — 建议用 subprocess"),
        (r"eval\(", "使用 eval() — 有代码注入风险"),
        (r"exec\(", "使用 exec() — 有代码注入风险"),
        (r"subprocess\.call\(.*shell\s*=\s*True", "shell=True 有命令注入风险"),
        (r"import\s+pickle", "pickle 反序列化不安全"),
        (r"password\s*=\s*['\"]\w+['\"]", "硬编码密码"),
        (r"\.execute\([^)]*%[^)]*\)", "SQL 拼接有注入风险"),
    ]

    INEFFICIENCY_PATTERNS = [
        (r"for\s+\w+\s+in\s+range\(len\(", "使用 range(len()) 不Pythonic — 建议直接迭代"),
        (r"\+\s*=\s*['\"].*['\"]\s*\+\s*=", "字符串链式拼接 — 建议用 join()"),
        (r"for\s+\w+\s+in\s+\w+:\s*\n\s+for\s+\w+\s+in\s+\w+:", "嵌套循环 — 检查算法复杂度"),
        (r"except\s*:\s*$", "裸 except — 会捕获所有异常包括 KeyboardInterrupt"),
        (r"while\s+True\s*:\s*\n\s*sleep", "忙等待 — 考虑使用事件/信号"),
    ]

    def __init__(self):
        pass

    def score_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """评分一段代码

        Returns:
            {correctness, efficiency, style, security, overall, details}
        """
        if language != "python":
            return {"error": "目前仅支持 Python"}

        correctness = self._score_correctness(code)
        efficiency = self._score_efficiency(code)
        style = self._score_style(code)
        security = self._score_security(code)

        overall = int((correctness * 0.3 + efficiency * 0.2 +
                       style * 0.2 + security * 0.3))

        return {
            "correctness": correctness,
            "efficiency": efficiency,
            "style": style,
            "security": security,
            "overall": overall,
            "grade": self._grade(overall),
            "language": language,
        }

    def _score_correctness(self, code: str) -> int:
        """语法正确性检查 (0-100)"""
        try:
            ast.parse(code)
            # 检查是否有实际语句
            tree = ast.parse(code)
            has_body = any(
                isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Expr,
                                  ast.Assign, ast.If, ast.For, ast.While,
                                  ast.Import, ast.ImportFrom))
                for node in ast.walk(tree)
            )
            return 90 if has_body else 60  # 有可执行语句
        except SyntaxError as e:
            # 根据错误严重程度扣分
            return max(0, 70 - min(str(e).count("line") * 10, 70))
        except Exception:
            return 50  # 其他错误

    def _score_efficiency(self, code: str) -> int:
        """效率评分 (0-100)"""
        score = 100
        lines = [l.strip() for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]

        import re
        for pattern, _ in self.INEFFICIENCY_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 15

        # 过长行
        long_lines = sum(1 for l in lines if len(l) > 120)
        score -= min(long_lines * 5, 20)

        return max(0, min(100, score))

    def _score_style(self, code: str) -> int:
        """风格评分 (0-100)"""
        score = 80  # 基准分

        # 基本检查
        if not code.strip():
            return 0
        if code.startswith(" "):
            score -= 5
        if "\t" in code:
            score -= 10

        lines = code.split("\n")

        # 函数/类之间空两行
        class_or_func = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(("def ", "class ")):
                class_or_func += 1
                if i > 0 and lines[i - 1].strip() != "":
                    score -= 3

        # 导入在顶部
        imports_at_bottom = False
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                if i > len(lines) * 0.3:
                    imports_at_bottom = True
        if imports_at_bottom:
            score -= 10

        # 命名规范 (简易检查)
        for line in lines:
            if line.strip().startswith("def ") and "_" not in line:
                func_name = line.strip()[4:].split("(")[0]
                if func_name and func_name[0].isupper():
                    score -= 5  # 函数名不应大写开头

        return max(0, min(100, score))

    def _score_security(self, code: str) -> int:
        """安全评分 (0-100)"""
        score = 100

        import re
        for pattern, reason in self.DANGER_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 20

        return max(0, min(100, score))

    def _grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        return "F"

    def batch_score(self, files: List[Tuple[str, str]]) -> List[dict]:
        """批量评分多个文件

        Args:
            files: [(path, content), ...]
        """
        results = []
        for path, content in files:
            scores = self.score_code(content)
            results.append({"path": path, **scores})
        return results


# ================================================================
# 进化反馈
# ================================================================

class EvolutionFeeder:
    """评估结果 → evo_engine 反馈通道"""

    def __init__(self, evo_engine=None):
        if evo_engine:
            self._evo = evo_engine
        else:
            try:
                from core.evo_engine import get_evo_engine
                self._evo = get_evo_engine()
            except Exception:
                self._evo = None

    def feed_benchmark_results(self, skill_name: str,
                                results: dict) -> bool:
        if not self._evo:
            return False
        summary = results.get("summary", {})
        try:
            self._evo.record(
                f"benchmark/{skill_name}", "benchmark",
                success=summary.get("pass_rate", 0) >= 80,
                elapsed=summary.get("avg_latency_ms", 0) / 1000,
                metadata={"pass_rate": summary.get("pass_rate"),
                          "total": summary.get("total_tests")}
            )
            return True
        except Exception:
            return False

    def feed_quality_scores(self, superpower_name: str,
                             scores: dict) -> bool:
        if not self._evo:
            return False
        try:
            self._evo.record(
                f"quality/{superpower_name}", "quality_check",
                success=scores.get("overall", 0) >= 70,
                elapsed=0,
                metadata={"overall": scores.get("overall"),
                          "grade": scores.get("grade")}
            )
            return True
        except Exception:
            return False

    def generate_evolution_suggestions(self) -> List[dict]:
        """从评估结果生成进化建议"""
        if not self._evo:
            return []
        return self._evo.get_suggestions(min_severity="low")


# ================================================================
# 回归检测
# ================================================================

class RegressionDetector:
    """退化检测 — 对比快照识别性能/质量下降"""

    def __init__(self, evo_engine=None):
        if evo_engine:
            self._evo = evo_engine
        else:
            try:
                from core.evo_engine import get_evo_engine
                self._evo = get_evo_engine()
            except Exception:
                self._evo = None

    def take_baseline(self, label: str = "") -> str:
        """拍摄当前快照作为基线"""
        if not self._evo:
            return ""
        snap_id = self._evo.take_snapshot(label or "baseline")
        return snap_id

    def compare_to_baseline(self, baseline_label: str) -> dict:
        """对比当前状态与基线"""
        if not self._evo:
            return {"error": "evo_engine 不可用"}

        current_id = self._evo.take_snapshot("current")
        diff = self._evo.compare_snapshots(baseline_label, current_id)

        regressed = []
        for agent, delta in diff.items():
            if delta.get("delta", 0) < 0:
                regressed.append({
                    "agent": agent,
                    "before": delta["before"],
                    "after": delta["after"],
                    "delta": delta["delta"],
                    "severity": "high" if delta["delta"] < -10 else "medium",
                })

        return {
            "baseline": baseline_label,
            "current": current_id,
            "regressed": regressed,
            "total_regressions": len(regressed),
            "timestamp": datetime.now().isoformat(),
        }

    def detect_regression(self, current_results: dict,
                          historical_baseline: str = None) -> dict:
        """检测测试结果退化"""
        if not self._evo or not historical_baseline:
            return {"error": "无历史基线"}

        compare = self.compare_to_baseline(historical_baseline)
        regressions = compare.get("regressed", [])

        # 结合当前结果
        findings = []
        for reg in regressions:
            findings.append({
                "agent": reg["agent"],
                "before_pct": reg["before"],
                "after_pct": reg["after"],
                "delta": reg["delta"],
                "action": "建议暂停自动化操作并检查" if reg["severity"] == "high"
                          else "关注此模块的变化趋势",
            })

        return {
            "regression_detected": len(regressions) > 0,
            "findings": findings,
            "suggestion": ("需要回滚或修复" if len(regressions) > 0
                           else "无退化"),
        }

    def get_regression_report(self) -> str:
        """生成人类可读的退化报告"""
        lines = ["# 回归检测报告", f"生成: {datetime.now().isoformat()}", ""]
        try:
            baseline = self.take_baseline()
            compare = self.compare_to_baseline(baseline)
            regs = compare.get("regressed", [])

            if not regs:
                lines.append("✅ 无退化")
            else:
                lines.append(f"⚠️ 发现 {len(regs)} 项退化:")
                for r in regs:
                    lines.append(f"  - {r['agent']}: {r['before']:.1f}% →"
                                 f" {r['after']:.1f}% (Δ{r['delta']})")
            return "\n".join(lines)
        except Exception as e:
            return f"# 回归检测报告\n错误: {e}"


# ================================================================
# 仪表盘生成器
# ================================================================

class DashboardGenerator:
    """综合健康报告仪表盘"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.reports_dir = self.base_dir / "storage" / "evo" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_agent_report(self, agent_name: str) -> str:
        """单 agent 健康报告"""
        try:
            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            stats = evo.get_stats(agent_name)
            lines = [
                f"## {agent_name}",
                f"- 总执行: {stats.get('total', 0)} 次",
                f"- 成功率: {stats.get('success_rate', 0)}%",
                f"- 近期失败率: {stats.get('recent_failure_rate', 0)}%",
            ]
            suggestions = evo.get_suggestions(agent_name, "medium")
            if suggestions:
                lines.append("- 建议:")
                for s in suggestions[:3]:
                    lines.append(f"  * [{s.get('severity', '?')}] {s.get('suggestion', '')}")
            return "\n".join(lines)
        except Exception as e:
            return f"## {agent_name}\n错误: {e}"

    def generate_skill_report(self, skill_name: str) -> str:
        """单 skill 健康报告"""
        lines = [f"## Skill: {skill_name}"]

        try:
            bench = SkillBenchmark()
            summary = bench.get_summary(skill_name)
            if "error" not in summary:
                lines.append(f"- 通过率: {summary.get('pass_rate', 0)}%")
                lines.append(f"- 平均延迟: {summary.get('avg_latency_ms', 0)}ms")

            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            stats = evo.get_stats(f"skill/{skill_name}")
            if stats.get("total", 0) > 0:
                lines.append(f"- 技能执行: {stats['total']}次, "
                            f"成功率{stats['success_rate']}%")
            return "\n".join(lines)
        except Exception as e:
            return f"## Skill: {skill_name}\n错误: {e}"

    def generate_workflow_report(self, workflow_name: str) -> str:
        """单 workflow 健康报告"""
        try:
            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            stats = evo.get_stats(f"workflow/{workflow_name}")
            lines = [
                f"## Workflow: {workflow_name}",
                f"- 总执行: {stats.get('total', 0)} 次",
                f"- 成功率: {stats.get('success_rate', 0)}%",
                f"- 平均耗时: {stats.get('avg_elapsed_ms', 0)}ms",
            ]
            suggestions = evo.get_suggestions(f"workflow/{workflow_name}")
            if suggestions:
                lines.append("- 建议:")
                for s in suggestions[:3]:
                    lines.append(f"  * {s.get('suggestion', '')}")
            return "\n".join(lines)
        except Exception as e:
            return f"## Workflow: {workflow_name}\n错误: {e}"

    def generate_full_dashboard(self) -> str:
        """全量仪表盘"""
        lines = [
            "# CLAUSE 系统健康仪表盘",
            f"生成时间: {datetime.now().isoformat()}",
            "",
            "---",
            "",
        ]

        # EvoEngine 健康
        try:
            from core.evo_engine import get_evo_engine
            evo = get_evo_engine()
            lines.append(evo.get_health_report())
        except Exception as e:
            lines.append(f"进化引擎: 不可用 ({e})")

        lines.extend(["", "---", ""])

        # AI 规则统计
        try:
            from core.ai_rules import get_rules_engine
            rules = get_rules_engine()
            stats = rules.get_stats()
            lines.append("## AI 规则引擎")
            lines.append(f"- 规则数: {stats['total_rules']}")
            lines.append(f"- 总校验: {stats['total_validations']}")
            lines.append(f"- 阻止: {stats['denied']}, 警告: {stats['warned']}")
        except Exception:
            pass

        lines.extend(["", "---", ""])

        # Superpowers 状态
        try:
            from core.superpowers import get_superpower_engine
            sp = get_superpower_engine()
            lines.append("## Superpowers")
            for s in sp.list_superpowers():
                lines.append(f"- {s['name']}: {s['steps']}步, "
                            f"强制={s['enforce_mandatory']}")
        except Exception:
            pass

        report = "\n".join(lines)

        # 持久化
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"dashboard_{timestamp}.md"
        try:
            report_path.write_text(report, encoding="utf-8")
        except Exception:
            pass

        return report

    def export_dashboard_json(self) -> dict:
        """导出为机器可读 JSON"""
        return {
            "timestamp": datetime.now().isoformat(),
            "report": self.generate_full_dashboard(),
            "format": "markdown",
        }


# ============================================================
# 模块级便捷函数
# ============================================================

_benchmark_instance = None
_scorer_instance = None
_dashboard_instance = None


def get_benchmark() -> SkillBenchmark:
    global _benchmark_instance
    if _benchmark_instance is None:
        _benchmark_instance = SkillBenchmark()
    return _benchmark_instance


def get_quality_scorer() -> QualityScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = QualityScorer()
    return _scorer_instance


def get_dashboard() -> DashboardGenerator:
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = DashboardGenerator()
    return _dashboard_instance
