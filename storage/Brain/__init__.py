#!/usr/bin/env python
"""Brain System - AI大脑系统统一入口 (v2.0)

集成模块:
- MemoryEngine:   记忆持久化引擎 (LRU + 文件存储)
- MemoryRecaller: 记忆召回系统 (触发式 + 语义搜索)
- GrowthTracker:  成长追踪系统 (5维度 + 进化日志)
- ComplianceAuditor: 合规审计系统 (6种违规检测)
- EventBridge:    跨软件事件桥接器 (Brain ↔ EventBus)

使用方式:
    from storage.Brain import Brain
    
    brain = Brain()
    
    # 任务前后包裹
    brain.pre_task("用户指令")
    # ... 执行任务 ...
    brain.post_task(success=True, result="...")
    
    # 查询记忆
    context = brain.recall("用户输入")
    
    # 获取报告
    brain.report()
"""

import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# 确保导入路径
BRAIN_ROOT = Path(__file__).parent
if str(BRAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(BRAIN_ROOT))

from growth.tracker import GrowthTracker, get_growth_tracker
from memory.bug_memory import BugMemoryEngine, get_bug_memory
from memory.engine import MemoryEngine, get_memory_engine
from memory.recall import MemoryRecaller, get_recaller
from supervisor.audit import ComplianceAuditor, get_auditor


class Brain:
    """AI大脑系统 - 统一管理记忆、成长、合规"""

    def __init__(self, auto_start: bool = True):
        self._lock = threading.RLock()
        self._session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._session_start = datetime.now()

        # 核心模块
        self.memory: MemoryEngine = get_memory_engine()
        self.recall: MemoryRecaller = get_recaller()
        self.bug_memory: BugMemoryEngine = get_bug_memory()
        self.growth: GrowthTracker = get_growth_tracker()
        self.audit: ComplianceAuditor = get_auditor()

        # 事件桥接 (可选，依赖MCP Core)
        self._bridge = None
        if auto_start:
            self._try_connect_bridge()

        self._task_count = 0
        print(f"[Brain] 大脑系统已启动 session={self._session_id}")

    def _try_connect_bridge(self):
        """尝试连接事件桥接器"""
        try:
            from integration.event_bridge import get_event_bridge
            self._bridge = get_event_bridge(auto_connect=True)
        except ImportError:
            # 事件桥接模块不可用，非关键错误
            pass
        except OSError:
            # 事件桥接连接失败，非关键错误
            pass

    # ─── 任务生命周期 ──────────────────────────────────

    def pre_task(self, instruction: str,
                 planned_action: str = "",
                 expected_files: list = None) -> dict:
        """任务开始前的准备

        1. 合规检查
        2. Bug 记忆召回 (防止重犯历史错误)
        3. 记忆召回 (获取相关上下文)
        4. 加载用户偏好
        """
        with self._lock:
            # 合规检查
            compliance_result = self.audit.pre_action_check(
                instruction=instruction,
                planned_action=planned_action or instruction,
                expected_files=expected_files,
            )

            # Bug 记忆召回 — 查找历史上类似任务犯过的错
            bug_recall = self.bug_memory.recall_for_task(
                task_description=instruction,
                files_involved=expected_files,
            )

            # 记忆召回
            recall_result = self.recall.recall(instruction)
            context = self.recall.format_context(recall_result)

            # 工作记忆: 记录当前任务
            self.memory.wm_set("current_task", {
                "instruction": instruction,
                "started_at": datetime.now().isoformat(),
                "compliance": compliance_result["passed"],
            })

            self._task_count += 1

            # 共享上下文: 广播任务并检测冲突
            conflict_info = {}
            try:
                from integration.shared_context_bridge import hook_pre_task
                conflict_info = hook_pre_task(self, instruction, planned_action, expected_files)
            except ImportError:
                pass

            return {
                "compliance_passed": compliance_result["passed"],
                "compliance_warnings": compliance_result.get("warnings", []),
                "output_standards_violations": compliance_result.get("output_standards_violations", []),
                "bug_warnings": bug_recall.get("warnings", []),
                "bug_summary": bug_recall.get("summary", ""),
                "relevant_bugs": bug_recall.get("relevant_bugs", []),
                "memory_context": context,
                "recall_summary": recall_result.get("summary", ""),
                "user_prefs": recall_result.get("user_profile", {}),
                "conflicts": conflict_info.get("conflicts", []),
                "other_agents": conflict_info.get("other_agents", []),
            }

    def post_task(self, success: bool, result: str,
                  instruction: str = "",
                  duration_minutes: float = 0,
                  files_touched: list = None,
                  lessons: list = None) -> dict:
        """任务完成后的处理

        1. 合规验证
        2. 成长记录
        3. 记忆保存
        """
        with self._lock:
            # 合规验证
            compliance = self.audit.post_action_check(
                action=instruction or self.memory.wm_get("current_task", {}).get("instruction", ""),
                result=result,
                success=success,
                has_verified=True,
            )

            # 成长记录
            if success:
                self.growth.log_task_complete(
                    task=instruction[:200] if instruction else "unknown",
                    method="Brain系统执行",
                    result=result[:200],
                    experience="; ".join(lessons or []) or f"任务完成: {result[:100]}",
                    duration_minutes=duration_minutes,
                    files_touched=files_touched or [],
                )
            else:
                self.growth.log_error_resolved(
                    error=result[:200],
                    root_cause="执行失败",
                    fix="待分析",
                    prevention="记录失败信息供后续参考",
                )
                # 自动记录 bug 到 Bug 记忆引擎
                self.bug_memory.record_bug(
                    error_message=result[:1000],
                    task_description=instruction[:500],
                    error_type=self._classify_error(result),
                    fix_description="待分析" if not lessons else "; ".join(lessons[:3]),
                    files_involved=files_touched or [],
                    agent_id="Qoder",
                    severity="high" if "error" in result.lower() or "fail" in result.lower() else "medium",
                    tags=self._extract_tags(instruction, files_touched),
                )

            # 保存会话记忆 (每5个任务保存一次)
            if self._task_count % 5 == 0:
                session_summary = self.growth.generate_session_summary()
                self.memory.save_session(
                    session_id=self._session_id,
                    summary=f"已完成{self._task_count}个任务",
                    key_decisions=[f"Task #{self._task_count}: {instruction[:100]}" if instruction else ""],
                    lessons=lessons or [],
                    files_touched=files_touched or [],
                    duration_minutes=int((datetime.now() - self._session_start).total_seconds() / 60),
                )

            # 事件桥接: 通知系统
            if self._bridge:
                self._bridge.push_event("brain.task.completed", {
                    "success": success,
                    "instruction": instruction[:200],
                    "result": result[:200],
                    "task_number": self._task_count,
                })

            # 共享上下文: 记录文件操作并推送知识
            try:
                from integration.shared_context_bridge import hook_post_task
                hook_post_task(self, success, result, instruction, files_touched, lessons)
            except ImportError:
                pass

            return {
                "compliance_score": compliance.get("match_score", 100),
                "violations": compliance.get("violations", []),
                "session_summary_updated": self._task_count % 5 == 0,
            }

    # ─── 查询接口 ──────────────────────────────────────

    def recall(self, query: str) -> str:
        """召回相关记忆 (格式化为上下文)"""
        result = self.recall.recall(query)
        return self.recall.format_context(result)

    def search(self, keyword: str, scope: str = "all") -> dict:
        """搜索记忆"""
        results = {}
        if scope in ("all", "sessions"):
            results["sessions"] = self.memory.search_sessions(keyword)
        if scope in ("all", "knowledge"):
            results["knowledge"] = self.memory.kb_search(keyword)
        if scope in ("all", "patterns"):
            results["patterns"] = self.memory.search_patterns(keyword)
        return results

    # ─── 知识管理 ──────────────────────────────────────

    def learn(self, title: str, content: str,
              category: str = "domain_knowledge",
              tags: list = None, importance: int = 5):
        """学习新知识"""
        import uuid
        entry_id = f"learned_{uuid.uuid4().hex[:8]}"
        self.memory.kb_save(
            category=category,
            entry_id=entry_id,
            title=title,
            content=content,
            tags=tags or [],
            importance=importance,
        )

        if self._bridge:
            self._bridge.notify_knowledge_gained(title, content, category)

    def remember(self, key: str, value: Any):
        """短期记忆"""
        self.memory.wm_set(key, value)

    # ─── Bug 记忆辅助方法 ──────────────────────────────

    def _classify_error(self, error_msg: str) -> str:
        """根据错误信息自动分类错误类型。"""
        msg_lower = error_msg.lower()
        if "modulenotfound" in msg_lower or "importerror" in msg_lower or "no module" in msg_lower:
            return "import"
        if "syntaxerror" in msg_lower or "indentationerror" in msg_lower:
            return "syntax"
        if "filenotfound" in msg_lower or "no such file" in msg_lower:
            return "file_not_found"
        if "permission" in msg_lower or "access denied" in msg_lower or "eacces" in msg_lower:
            return "permission"
        if "timeout" in msg_lower or "timed out" in msg_lower or "connection" in msg_lower:
            return "network"
        if "jsondecode" in msg_lower or "decode" in msg_lower or "encode" in msg_lower:
            return "encoding"
        if "keyerror" in msg_lower or "attributeerror" in msg_lower or "typeerror" in msg_lower:
            return "logic"
        if "memory" in msg_lower or "out of memory" in msg_lower:
            return "resource"
        return "unknown"

    def _extract_tags(self, instruction: str, files: list) -> list:
        """从任务描述和文件列表中提取标签。"""
        tags = []
        instruction_lower = instruction.lower()
        # 关键词 → 标签映射
        tag_map = {
            "import": "dependency",
            "install": "dependency",
            "pip": "dependency",
            "file": "file_operation",
            "write": "file_operation",
            "read": "file_operation",
            "config": "configuration",
            "环境": "configuration",
            "变量": "configuration",
            "bug": "debug",
            "error": "debug",
            "fix": "debug",
            "修复": "debug",
            "login": "auth",
            "auth": "auth",
            "token": "auth",
            "brain": "brain_system",
            "memory": "brain_system",
            "shared_context": "cross_agent",
            "pipeline": "pipeline",
        }
        for keyword, tag in tag_map.items():
            if keyword in instruction_lower:
                tags.append(tag)

        # 从文件名提取
        if files:
            for f in files[:5]:
                name = Path(f).stem.lower()
                for part in name.replace("_", " ").replace("-", " ").split():
                    if len(part) > 2 and part not in ("the", "and", "for", "def"):
                        tags.append(part)

        return list(set(tags))[:10]

    # ─── 报告 ──────────────────────────────────────────

    def report(self) -> dict:
        """生成综合报告"""
        return {
            "system": "Brain v2.0",
            "session_id": self._session_id,
            "session_duration_minutes": round(
                (datetime.now() - self._session_start).total_seconds() / 60, 1
            ),
            "tasks_completed": self._task_count,
            "memory_status": self.memory.stats(),
            "growth_metrics": self.growth.get_metrics(),
            "compliance": self.audit.get_session_report(),
            "event_bridge": self._bridge.status() if self._bridge else {"connected": False},
        }

    def daily_review(self) -> dict:
        """每日回顾"""
        return {
            "daily_summary": self.growth.generate_daily_summary(),
            "growth_score": self.growth._calc_growth_score(),
            "weak_areas": self.growth._identify_weak_areas(),
        }

    def weekly_review(self) -> dict:
        """每周回顾"""
        return self.growth.generate_weekly_review()

    # ─── 关闭 ──────────────────────────────────────────

    def shutdown(self):
        """关闭大脑系统，保存所有状态"""
        # 保存最终会话
        session_summary = self.growth.generate_session_summary()
        self.memory.save_session(
            session_id=self._session_id,
            summary=f"会话结束: 共{self._task_count}个任务",
            key_decisions=session_summary.get("key_lessons", []),
            lessons=session_summary.get("key_lessons", []),
            duration_minutes=int((datetime.now() - self._session_start).total_seconds() / 60),
        )

        # 生成日报
        self.growth.generate_daily_summary()

        if self._bridge:
            self._bridge.disconnect()

        print(f"[Brain] 大脑系统已关闭 ({self._task_count} tasks)")


# ─── 全局单例 ───────────────────────────────────────────
_brain_instance: Optional[Brain] = None
_brain_lock = threading.Lock()


def get_brain() -> Brain:
    """获取Brain全局单例"""
    global _brain_instance
    if _brain_instance is None:
        with _brain_lock:
            if _brain_instance is None:
                _brain_instance = Brain()
    return _brain_instance


# ─── CLI ────────────────────────────────────────────────
if __name__ == "__main__":
    brain = Brain()

    # 模拟任务流
    print("\n=== 任务1 ===")
    pre = brain.pre_task("帮我创建一个Python测试脚本", "创建 D:/test_script.py")
    print(f"合规: {pre['compliance_passed']}, 召回: {pre['recall_summary']}")

    post = brain.post_task(True, "脚本创建成功", "帮我创建一个Python测试脚本",
                           files_touched=["D:/test_script.py"],
                           lessons=["Python脚本模板化可提高复用率"])
    print(f"合规分: {post['compliance_score']}, 违规: {post['violations']}")

    print("\n=== 任务2 ===")
    pre2 = brain.pre_task("运行测试并检查结果")
    print(f"记忆上下文: {pre2['memory_context'][:200]}...")

    print("\n=== 综合报告 ===")
    print(json.dumps(brain.report(), ensure_ascii=False, indent=2))

    brain.shutdown()
