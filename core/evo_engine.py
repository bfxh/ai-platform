#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进化引擎 — EvoAgentX 启发：自进化 Agent 生态

核心设计:
- 性能追踪: 记录每次 agent/skill/workflow 的执行指标
- 失败学习: 从失败中提取模式，生成改进建议
- 变异优化: 对低效配置自动生成变体并评估
- 记忆增强: 将成功模式注入会话上下文

EvoAgentX 核心循环:
    Execute → Evaluate → Mutate → Select → Repeat

用法:
    from core.evo_engine import EvoEngine

    evo = EvoEngine()
    evo.record("trae_control", "write_file", success=True, elapsed=0.3)
    evo.record("trae_control", "execute_command", success=False, error="timeout")
    suggestions = evo.get_suggestions("trae_control")
    # → ["增加 write_file 超时限制", "execute_command 失败率 15%，建议重试策略"]
"""

import json
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


class EvoEngine:
    """EvoAgentX 风格进化引擎"""

    MAX_RECORDS_PER_AGENT = 500
    FAILURE_THRESHOLD = 0.15          # 失败率超过 15% 触发建议
    SLOW_THRESHOLD_MS = 5000          # 超过 5 秒视为慢操作
    MIN_SAMPLES_FOR_SUGGESTION = 10   # 至少 10 次样本才生成建议

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "storage" / "evo"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 内存中的性能记录
        self._records: Dict[str, List[dict]] = defaultdict(list)
        self._snapshots: Dict[str, dict] = {}
        self._suggestions: Dict[str, List[dict]] = defaultdict(list)

        # 加载历史
        self._load_history()

    # ================================================================
    # 记录
    # ================================================================

    def record(self, agent: str, action: str, success: bool,
               elapsed: float = 0, error: str = "",
               metadata: dict = None) -> str:
        """记录一次执行

        Args:
            agent:    代理名称 (trae_control, claude_orchestrator, ...)
            action:   操作 (write_file, execute_command, dispatch, ...)
            success:  是否成功
            elapsed:  耗时（秒）
            error:    错误信息
            metadata: 额外数据

        Returns:
            记录 ID
        """
        record_id = f"{agent}_{action}_{int(time.time() * 1000)}"
        entry = {
            "id": record_id,
            "agent": agent,
            "action": action,
            "success": success,
            "elapsed": elapsed,
            "elapsed_ms": int(elapsed * 1000),
            "error": error[:500] if error else "",
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._records[agent].append(entry)

        # 限制记录数
        if len(self._records[agent]) > self.MAX_RECORDS_PER_AGENT:
            self._records[agent] = self._records[agent][-self.MAX_RECORDS_PER_AGENT:]

        # 检查是否需要生成建议
        if not success and len(self._records[agent]) >= self.MIN_SAMPLES_FOR_SUGGESTION:
            self._analyze_and_suggest(agent)

        # 定期持久化
        if sum(len(v) for v in self._records.values()) % 50 == 0:
            self._save_history()

        return record_id

    # ================================================================
    # 分析
    # ================================================================

    def get_stats(self, agent: str = None) -> dict:
        """获取代理的性能统计"""
        if agent:
            return self._agent_stats(agent)

        all_stats = {}
        for ag in self._records:
            all_stats[ag] = self._agent_stats(ag)
        return all_stats

    def _agent_stats(self, agent: str) -> dict:
        """单个代理统计"""
        records = self._records.get(agent, [])
        if not records:
            return {"agent": agent, "total": 0}

        total = len(records)
        successes = sum(1 for r in records if r["success"])
        failures = total - successes
        avg_elapsed = sum(r["elapsed"] for r in records) / total if total > 0 else 0
        recent_50 = records[-50:]
        recent_failure_rate = (
            sum(1 for r in recent_50 if not r["success"]) / len(recent_50)
            if recent_50 else 0
        )

        # 按操作分类
        by_action = defaultdict(lambda: {"total": 0, "success": 0, "avg_elapsed": 0})
        for r in records:
            a = by_action[r["action"]]
            a["total"] += 1
            if r["success"]:
                a["success"] += 1
            a["avg_elapsed"] = ((a["avg_elapsed"] * (a["total"] - 1)) + r["elapsed"]) / a["total"]

        action_stats = {}
        for action, stats in by_action.items():
            action_stats[action] = {
                "total": stats["total"],
                "success_rate": round(stats["success"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
                "avg_elapsed_ms": int(stats["avg_elapsed"] * 1000),
            }

        return {
            "agent": agent,
            "total": total,
            "successes": successes,
            "failures": failures,
            "success_rate": round(successes / total * 100, 1) if total > 0 else 0,
            "avg_elapsed_ms": int(avg_elapsed * 1000),
            "recent_failure_rate": round(recent_failure_rate * 100, 1),
            "by_action": action_stats,
        }

    def _analyze_and_suggest(self, agent: str):
        """分析代理表现并生成改进建议"""
        stats = self._agent_stats(agent)
        records = self._records.get(agent, [])
        suggestions = []

        # 1. 高失败率操作
        for action, astats in stats.get("by_action", {}).items():
            if astats["total"] >= self.MIN_SAMPLES_FOR_SUGGESTION:
                failure_rate = 100 - astats["success_rate"]
                if failure_rate >= self.FAILURE_THRESHOLD * 100:
                    # 分析失败原因
                    failures = [r for r in records
                              if r["action"] == action and not r["success"]]
                    error_patterns = defaultdict(int)
                    for f in failures[-20:]:
                        err = f.get("error", "unknown")
                        # 提取错误关键词
                        for keyword in ["timeout", "denied", "not found", "permission",
                                      "connection", "syntax", "import", "encoding"]:
                            if keyword in err.lower():
                                error_patterns[keyword] += 1

                    top_errors = sorted(error_patterns.items(), key=lambda x: -x[1])[:3]
                    suggestions.append({
                        "type": "high_failure",
                        "agent": agent,
                        "action": action,
                        "failure_rate": round(failure_rate, 1),
                        "top_errors": [e[0] for e in top_errors],
                        "suggestion": self._generate_fix_suggestion(action, top_errors),
                        "severity": "high" if failure_rate > 30 else "medium",
                    })

        # 2. 慢操作
        for action, astats in stats.get("by_action", {}).items():
            if astats["avg_elapsed_ms"] >= self.SLOW_THRESHOLD_MS:
                suggestions.append({
                    "type": "slow_operation",
                    "agent": agent,
                    "action": action,
                    "avg_elapsed_ms": astats["avg_elapsed_ms"],
                    "suggestion": f"{action} 平均耗时 {astats['avg_elapsed_ms']}ms，考虑优化或增加超时",
                    "severity": "low",
                })

        # 3. 趋势恶化
        recent_50 = records[-50:]
        if len(recent_50) >= 20:
            recent_fail_rate = sum(1 for r in recent_50 if not r["success"]) / len(recent_50)
            older = records[:-50]
            if older:
                older_fail_rate = sum(1 for r in older if not r["success"]) / len(older)
                if recent_fail_rate > older_fail_rate * 1.5:
                    suggestions.append({
                        "type": "trend_decay",
                        "agent": agent,
                        "older_rate": round(older_fail_rate * 100, 1),
                        "recent_rate": round(recent_fail_rate * 100, 1),
                        "suggestion": f"近期失败率从 {older_fail_rate*100:.1f}% 升至 {recent_fail_rate*100:.1f}%，建议暂停自动操作并检查",
                        "severity": "high",
                    })

        if suggestions:
            self._suggestions[agent] = suggestions

    def _generate_fix_suggestion(self, action: str,
                                  top_errors: List[Tuple[str, int]]) -> str:
        """根据错误模式生成修复建议"""
        error_keywords = [e[0] for e in top_errors]

        suggestions = []
        if "timeout" in error_keywords:
            suggestions.append("增加超时时间")
        if "not found" in error_keywords:
            suggestions.append("添加路径验证前检查")
        if "permission" in error_keywords or "denied" in error_keywords:
            suggestions.append("检查权限配置")
        if "connection" in error_keywords:
            suggestions.append("添加连接重试逻辑")
        if "syntax" in error_keywords:
            suggestions.append("在写入前做语法检查")
        if "encoding" in error_keywords:
            suggestions.append("统一使用 UTF-8 编码")

        if suggestions:
            return f"{action}: {', '.join(suggestions)}"
        return f"{action}: 检查失败原因并改进"

    # ================================================================
    # 建议
    # ================================================================

    def get_suggestions(self, agent: str = None, min_severity: str = "low") -> List[dict]:
        """获取改进建议

        Args:
            agent:         代理名称，None 返回所有
            min_severity:  最低严重级别 (low/medium/high)
        """
        severity_order = {"low": 0, "medium": 1, "high": 2}
        min_level = severity_order.get(min_severity, 0)

        all_suggestions = []
        if agent:
            all_suggestions = self._suggestions.get(agent, [])
        else:
            for ag in self._suggestions:
                all_suggestions.extend(self._suggestions[ag])

        return [s for s in all_suggestions
                if severity_order.get(s.get("severity", "low"), 0) >= min_level]

    def get_health_report(self) -> str:
        """生成健康报告"""
        lines = ["# 进化引擎 - 健康报告", f"生成时间: {datetime.now().isoformat()}", ""]

        for agent in sorted(self._records.keys()):
            stats = self._agent_stats(agent)
            if stats["total"] == 0:
                continue

            health = "HEALTHY" if stats["success_rate"] >= 90 else (
                "WARNING" if stats["success_rate"] >= 70 else "CRITICAL"
            )
            lines.append(f"## {agent} [{health}]")
            lines.append(f"- 总计: {stats['total']} 次, "
                        f"成功率: {stats['success_rate']}%")
            lines.append(f"- 近期失败率: {stats['recent_failure_rate']}%")

            for action, astats in stats.get("by_action", {}).items():
                flag = "[!]" if astats["success_rate"] < 70 else "[OK]"
                lines.append(f"  {flag} {action}: "
                           f"{astats['total']}次, "
                           f"成功率{astats['success_rate']}%, "
                           f"{astats['avg_elapsed_ms']}ms")

            suggestions = self.get_suggestions(agent, "medium")
            if suggestions:
                lines.append("- 建议:")
                for s in suggestions[:3]:
                    lines.append(f"  * [{s['severity']}] {s['suggestion']}")
            lines.append("")

        return "\n".join(lines)

    # ================================================================
    # 持久化
    # ================================================================

    def _save_history(self):
        """保存记录到文件"""
        for agent, records in self._records.items():
            if records:
                filepath = self.data_dir / f"{agent}_records.json"
                try:
                    filepath.write_text(
                        json.dumps(records[-200:], ensure_ascii=False, indent=2),
                        encoding="utf-8"
                    )
                except Exception:
                    pass

        # 保存建议
        if self._suggestions:
            sug_path = self.data_dir / "suggestions.json"
            try:
                sug_path.write_text(
                    json.dumps(dict(self._suggestions), ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except Exception:
                pass

    def _load_history(self):
        """从文件加载历史记录"""
        for filepath in self.data_dir.glob("*_records.json"):
            try:
                agent = filepath.stem.replace("_records", "")
                data = json.loads(filepath.read_text(encoding="utf-8"))
                self._records[agent] = data
            except Exception:
                pass

        # 加载建议
        sug_path = self.data_dir / "suggestions.json"
        if sug_path.exists():
            try:
                data = json.loads(sug_path.read_text(encoding="utf-8"))
                for agent, sugs in data.items():
                    self._suggestions[agent] = sugs
            except Exception:
                pass

    # ================================================================
    # 快照
    # ================================================================

    def take_snapshot(self, label: str = "") -> str:
        """拍摄当前状态快照"""
        snap_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        snapshot = {
            "id": snap_id,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "stats": {ag: self._agent_stats(ag) for ag in self._records},
            "suggestions": dict(self._suggestions),
        }
        self._snapshots[snap_id] = snapshot

        # 持久化
        snap_path = self.data_dir / f"{snap_id}.json"
        snap_path.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return snap_id

    def compare_snapshots(self, snap_id_a: str, snap_id_b: str) -> dict:
        """比较两个快照"""
        a = self._snapshots.get(snap_id_a)
        b = self._snapshots.get(snap_id_b)
        if not a or not b:
            # 从文件加载
            a = self._load_snapshot(snap_id_a)
            b = self._load_snapshot(snap_id_b)

        diff = {}
        all_agents = set(list(a.get("stats", {}).keys()) + list(b.get("stats", {}).keys()))
        for agent in all_agents:
            a_stats = a.get("stats", {}).get(agent, {})
            b_stats = b.get("stats", {}).get(agent, {})
            if a_stats.get("success_rate", 0) != b_stats.get("success_rate", 0):
                diff[agent] = {
                    "before": a_stats.get("success_rate", 0),
                    "after": b_stats.get("success_rate", 0),
                    "delta": round(b_stats.get("success_rate", 0) - a_stats.get("success_rate", 0), 1),
                }
        return diff

    def _load_snapshot(self, snap_id: str) -> Optional[dict]:
        """从文件加载快照"""
        snap_path = self.data_dir / f"{snap_id}.json"
        if snap_path.exists():
            try:
                return json.loads(snap_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    # ================================================================
    # 生命周期
    # ================================================================

    def cleanup_old_records(self, max_age_days: int = 90):
        """清理过期记录"""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for filepath in self.data_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff.timestamp():
                filepath.unlink(missing_ok=True)

    def shutdown(self):
        """关闭引擎"""
        self._save_history()


# ============================================================
# 模块级便捷函数
# ============================================================

_evo_instance = None


def get_evo_engine() -> EvoEngine:
    """获取全局进化引擎"""
    global _evo_instance
    if _evo_instance is None:
        _evo_instance = EvoEngine()
    return _evo_instance
