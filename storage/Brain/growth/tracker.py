#!/usr/bin/env python
"""Growth Tracker - AI成长追踪系统

追踪AI从每次任务中的学习、改进、进化:
- 5个成长维度: accuracy, efficiency, compliance, knowledge, adaptability
- 4种学习触发器: task_complete, error_resolved, user_correction, new_pattern
- 每日/每周回顾
- 进化日志管理
"""

import json
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent  # storage/Brain/
GROWTH_DIR = ROOT / "growth"
CONFIG_FILE = GROWTH_DIR / "config.json"
EVOLUTION_LOG = GROWTH_DIR / "evolution.log"
TRENDS_FILE = GROWTH_DIR / "trends.json"
DAILY_DIR = GROWTH_DIR / "daily"
WEEKLY_DIR = GROWTH_DIR / "weekly"


class GrowthTracker:
    """AI成长追踪器 - 记录每次学习成长"""

    def __init__(self):
        self._ensure_dirs()
        self.config = self._load_config()
        self._lock = threading.Lock()
        self._session_start = time.time()
        self._session_events = []
        self._metrics = self._load_metrics()

    def _ensure_dirs(self):
        for d in [GROWTH_DIR, DAILY_DIR, WEEKLY_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {}

    def _load_metrics(self) -> dict:
        if TRENDS_FILE.exists():
            try:
                return json.loads(TRENDS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "accuracy": {"current": 1.0, "history": [], "target": 0.95},
            "efficiency": {"current": 1.0, "history": [], "target": 0.9},
            "compliance": {"current": 1.0, "history": [], "target": 1.0},
            "knowledge": {"current": 0, "history": [], "target": 100},
            "adaptability": {"current": 1.0, "history": [], "target": 0.8},
        }

    # ─── 事件记录 ──────────────────────────────────────

    def log_task_complete(self, task: str, method: str,
                          result: str, experience: str,
                          duration_minutes: float = 0,
                          files_touched: list = None):
        """记录任务完成"""
        return self._log_event(
            event_type="task_complete",
            description=f"任务: {task}",
            method=method,
            result=result,
            lesson=experience,
            duration_minutes=duration_minutes,
            files_touched=files_touched or [],
            category=self._classify_event(task, result),
        )

    def log_error_resolved(self, error: str, root_cause: str,
                           fix: str, prevention: str):
        """记录错误解决"""
        return self._log_event(
            event_type="error_resolved",
            description=f"错误: {error}",
            method=f"根因: {root_cause}",
            result=f"修复: {fix}",
            lesson=f"预防: {prevention}",
            category="accuracy",
        )

    def log_user_correction(self, what_i_did_wrong: str,
                            user_expected: str,
                            gap_analysis: str,
                            improvement: str):
        """记录用户纠正"""
        return self._log_event(
            event_type="user_correction",
            description=f"我做错了: {what_i_did_wrong}",
            method=f"用户期望: {user_expected}",
            result=f"差距: {gap_analysis}",
            lesson=improvement,
            category="compliance",
        )

    def log_new_pattern(self, scenario: str, method: str,
                        reusable_contexts: list = None):
        """记录新发现模式"""
        return self._log_event(
            event_type="new_pattern",
            description=f"场景: {scenario}",
            method=method,
            result=f"可复用场景: {', '.join(reusable_contexts or [])}",
            lesson=f"模式: {method}",
            category="knowledge",
        )

    def _log_event(self, event_type: str, description: str,
                   method: str, result: str, lesson: str,
                   category: str = "accuracy",
                   duration_minutes: float = 0,
                   files_touched: list = None) -> dict:
        """通用事件记录"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "method": method,
            "result": result,
            "lesson": lesson,
            "action_item": f"以后: {lesson}",
            "category": category,
            "duration_minutes": duration_minutes,
            "files_touched": files_touched or [],
        }

        with self._lock:
            self._session_events.append(event)
            self._append_to_log(event)
            self._update_metrics(event)

        return event

    def _append_to_log(self, event: dict):
        """追加到进化日志"""
        try:
            with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _classify_event(self, task: str, result: str) -> str:
        """根据任务和结果分类"""
        if "fix" in task.lower() or "error" in task.lower() or "bug" in task.lower():
            return "accuracy"
        if "new" in task.lower() or "create" in task.lower() or "实现" in task:
            return "knowledge"
        if result.lower() in ("success", "passed", "完成"):
            return "efficiency"
        return "adaptability"

    # ─── 指标更新 ──────────────────────────────────────

    def _update_metrics(self, event: dict):
        """根据事件更新指标"""
        category = event["category"]
        if category not in self._metrics:
            return

        metric = self._metrics[category]

        if category == "accuracy":
            # 成功=+0.02, 失败=-0.05
            if event["event_type"] == "error_resolved":
                metric["current"] = max(0, metric["current"] - 0.05)
            else:
                metric["current"] = min(1.0, metric["current"] + 0.02)

        elif category == "efficiency":
            if event["event_type"] == "task_complete":
                duration = event.get("duration_minutes", 0)
                if duration > 0:
                    efficiency_gain = min(0.03, 5.0 / max(duration, 1))
                    metric["current"] = min(1.0, metric["current"] + efficiency_gain)

        elif category == "compliance":
            if event["event_type"] == "user_correction":
                metric["current"] = max(0, metric["current"] - 0.1)
            else:
                metric["current"] = min(1.0, metric["current"] + 0.01)

        elif category == "knowledge":
            metric["current"] += 1

        elif category == "adaptability":
            if event["event_type"] == "new_pattern":
                metric["current"] = min(1.0, metric["current"] + 0.05)

        metric["history"].append({
            "date": datetime.now().isoformat(),
            "value": metric["current"],
            "event": event["event_type"],
        })
        # 只保留最近100条历史
        if len(metric["history"]) > 100:
            metric["history"] = metric["history"][-100:]

        self._save_metrics()

    def _save_metrics(self):
        """持久化指标"""
        try:
            TRENDS_FILE.write_text(
                json.dumps(self._metrics, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    # ─── 汇总报告 ──────────────────────────────────────

    def generate_session_summary(self) -> dict:
        """生成会话摘要"""
        duration_minutes = (time.time() - self._session_start) / 60

        event_types = defaultdict(int)
        categories = defaultdict(int)
        for e in self._session_events:
            event_types[e["event_type"]] += 1
            categories[e["category"]] += 1

        return {
            "session_duration_minutes": round(duration_minutes, 1),
            "total_events": len(self._session_events),
            "event_types": dict(event_types),
            "categories_impacted": dict(categories),
            "key_lessons": [e["lesson"] for e in self._session_events[-5:]],
            "metrics_snapshot": {
                k: round(v["current"], 3) if isinstance(v["current"], float) else v["current"]
                for k, v in self._metrics.items()
            },
        }

    def generate_daily_summary(self, date: str = None) -> dict:
        """生成每日汇总"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        today_events = []
        today_prefix = date
        try:
            if EVOLUTION_LOG.exists():
                for line in EVOLUTION_LOG.read_text(encoding="utf-8").strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                        if event.get("timestamp", "").startswith(today_prefix):
                            today_events.append(event)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        event_types = defaultdict(int)
        lessons = []
        for e in today_events:
            event_types[e["event_type"]] += 1
            if e.get("lesson"):
                lessons.append(e["lesson"])

        summary = {
            "date": date,
            "total_events": len(today_events),
            "event_types": dict(event_types),
            "top_lessons": list(set(lessons))[-10:],
            "growth_score": self._calc_growth_score(),
        }

        # 保存日报
        daily_file = DAILY_DIR / f"{date}.json"
        daily_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return summary

    def generate_weekly_review(self, end_date: str = None) -> dict:
        """生成每周回顾"""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")

        # 合并每日数据
        daily_data = []
        for df in sorted(DAILY_DIR.glob("*.json")):
            if start_date <= df.stem <= end_date:
                try:
                    daily_data.append(json.loads(df.read_text(encoding="utf-8")))
                except Exception:
                    continue

        total_events = sum(d.get("total_events", 0) for d in daily_data)
        metrics_trend = {}
        for dim_name, dim_data in self._metrics.items():
            history = dim_data.get("history", [])
            weekly_vals = [h["value"] for h in history
                          if h["date"][:10] >= start_date]
            if weekly_vals:
                metrics_trend[dim_name] = {
                    "start": weekly_vals[0] if weekly_vals else dim_data["current"],
                    "end": weekly_vals[-1] if weekly_vals else dim_data["current"],
                    "change": weekly_vals[-1] - weekly_vals[0] if len(weekly_vals) > 1 else 0,
                }

        review = {
            "period": f"{start_date} →30: {end_date}",
            "active_days": len(daily_data),
            "total_events": total_events,
            "metrics_trend": metrics_trend,
            "growth_score": self._calc_growth_score(),
            "weak_areas": self._identify_weak_areas(),
            "focus_next_week": self._recommend_focus(),
        }

        weekly_file = WEEKLY_DIR / f"week_ending_{end_date}.json"
        weekly_file.write_text(
            json.dumps(review, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return review

    def _calc_growth_score(self) -> float:
        """计算综合成长分数"""
        weights = {
            "accuracy": 0.3,
            "efficiency": 0.2,
            "compliance": 0.25,
            "knowledge": 0.15,
            "adaptability": 0.1,
        }
        total = 0
        for dim, weight in weights.items():
            metric = self._metrics.get(dim, {})
            current = metric.get("current", 0)
            target = metric.get("target", 0.9)
            if isinstance(current, (int, float)) and target > 0:
                total += (min(current, target) / target) * weight * 100
        return round(total, 1)

    def _identify_weak_areas(self) -> list:
        """识别薄弱环节"""
        weak = []
        for name, data in self._metrics.items():
            current = data.get("current", 0)
            target = data.get("target", 0.9)
            if isinstance(current, float) and target > 0:
                ratio = current / target if target else 0
                if ratio < 0.7:
                    weak.append({"dimension": name, "current": current,
                                 "target": target, "gap_pct": round((1 - ratio) * 100, 1)})
        return sorted(weak, key=lambda x: x["gap_pct"], reverse=True)

    def _recommend_focus(self) -> list:
        """推荐下周重点"""
        weak = self._identify_weak_areas()
        recommendations = []
        for w in weak[:3]:
            dim = w["dimension"]
            rec_map = {
                "accuracy": "每次操作后加强验证，减少错误重复",
                "efficiency": "减少不必要步骤，合并相似操作",
                "compliance": "严格按用户要求执行，不确定时问清楚",
                "knowledge": "多记录新学到的模式和方案",
                "adaptability": "面对新问题时先搜索知识库再动手",
            }
            recommendations.append({"dimension": dim, "recommendation": rec_map.get(dim, "持续改进")})
        return recommendations

    # ─── 查询 ──────────────────────────────────────────

    def get_metrics(self) -> dict:
        """获取当前指标"""
        return {
            name: {
                "current": round(data["current"], 3) if isinstance(data["current"], float) else data["current"],
                "target": data["target"],
                "progress_pct": round(
                    min(data["current"], data["target"]) / data["target"] * 100, 1
                ) if isinstance(data["current"], float) and data["target"] > 0 else 0,
            }
            for name, data in self._metrics.items()
        }

    def get_recent_events(self, limit: int = 20) -> list:
        """获取最近的事件"""
        if not EVOLUTION_LOG.exists():
            return []

        events = []
        try:
            lines = EVOLUTION_LOG.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-limit * 3:]:  # 多读一些以应对空行
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return events[-limit:]
        except Exception:
            return self._session_events[-limit:]


# ─── 全局单例 ───────────────────────────────────────────
_tracker_instance: Optional[GrowthTracker] = None


def get_growth_tracker() -> GrowthTracker:
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = GrowthTracker()
    return _tracker_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    tracker = get_growth_tracker()

    # 模拟一些事件
    tracker.log_task_complete("实现记忆引擎", "Python模块开发",
                              "success", "分模块设计提高可维护性",
                              duration_minutes=15)
    tracker.log_error_resolved("JSON解析失败", "编码问题",
                               "指定utf-8编码", "所有文件IO都要指定编码")
    tracker.log_new_pattern("代码搜索任务", "先搜索再读取，减少IO",
                            ["代码分析", "错误排查"])

    print("=== Metrics ===")
    print(json.dumps(tracker.get_metrics(), ensure_ascii=False, indent=2))
    print("\n=== Session Summary ===")
    print(json.dumps(tracker.generate_session_summary(), ensure_ascii=False, indent=2))
