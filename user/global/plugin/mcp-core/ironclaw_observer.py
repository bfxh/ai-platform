# -*- coding: utf-8 -*-
"""
IronClaw Observer - AI行为实时追踪系统
小龙虾行为观测站 v1.0

功能：
- 记录 AI 的每一步操作（工具调用、Skill执行、文件修改）
- 对比"声称做的事" vs "实际做的事"
- 生成思维导图（workflow 可视化）
- Skill 审查与质量评分
- 实时 Web 监控面板数据接口

用法：
    from ironclaw_observer import IronClawObserver, get_observer
    obs = get_observer()
    obs.record_action("tool_call", {"tool": "read_file", "path": "..."})
    obs.record_claim("正在读取文件 X")
    obs.verify_and_log()  # 对比声称 vs 实际
"""

import json
import time
import threading
import traceback
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_DIR = Path("/python/MCP_Core/logs/observer")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class ActionType(Enum):
    TOOL_CALL = "tool_call"          # 工具调用
    SKILL_INVOKE = "skill_invoke"     # Skill调用
    FILE_READ = "file_read"           # 文件读取
    FILE_WRITE = "file_write"         # 文件写入
    FILE_DELETE = "file_delete"       # 文件删除
    COMMAND_EXEC = "command_exec"     # 命令执行
    SEARCH = "search"                 # 搜索操作
    API_CALL = "api_call"             # API调用
    WORKFLOW_START = "workflow_start" # 工作流开始
    WORKFLOW_STEP = "workflow_step"  # 工作流步骤
    WORKFLOW_END = "workflow_end"    # 工作流结束
    CLAIM = "claim"                   # AI声称（待验证）
    VERIFY_OK = "verify_ok"          # 验证通过
    VERIFY_FAIL = "verify_fail"      # 验证失败
    THINKING = "thinking"             # 思考过程
    ERROR = "error"                  # 错误


@dataclass
class AIAction:
    """单条AI行为记录"""
    timestamp: str
    session_id: str
    action_type: str
    details: Dict[str, Any]
    claim_text: Optional[str] = None       # AI声称的描述
    verified: bool = False                 # 是否已验证
    verify_result: Optional[str] = None     # 验证结果
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    parent_action_id: Optional[str] = None  # 父行为ID（用于嵌套）

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class WorkflowNode:
    """思维导图节点"""
    id: str
    label: str
    type: str                    # thinking/tool/skill/claim/result
    status: str                  # pending/running/success/fail
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    children: List["WorkflowNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
            "verified": self.verified,
        }


class IronClawObserver:
    """
    小龙虾行为追踪器
    核心：记录AI实际行为，与声称对比，发现偏差立即标记
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.actions: List[AIAction] = []
        self.current_session_id = self._new_session_id()
        self.workflow_stack: List[WorkflowNode] = []
        self.root_node: Optional[WorkflowNode] = None
        self._pending_claim: Optional[str] = None
        self._pending_claim_action_id: Optional[str] = None
        self.max_actions = 10000
        self._lock = threading.Lock()
        self._action_counter = 0
        self.session_start = datetime.now()
        self._stats = {
            "total_actions": 0,
            "total_claims": 0,
            "verified_ok": 0,
            "verified_fail": 0,
            "errors": 0,
        }
        self._initialized = True

    @staticmethod
    def _new_session_id() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _ts() -> str:
        return datetime.now().isoformat(timespec="milliseconds")

    def _next_id(self) -> str:
        self._action_counter += 1
        return f"{self.current_session_id}_{self._action_counter:04d}"

    # ─── 行为记录 ───────────────────────────────────────

    def record_action(
        self,
        action_type: str | ActionType,
        details: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        """记录一条AI行为"""
        with self._lock:
            at = action_type.value if isinstance(action_type, ActionType) else action_type
            action = AIAction(
                timestamp=self._ts(),
                session_id=self.current_session_id,
                action_type=at,
                details=details or {},
                parent_action_id=parent_id,
            )
            self.actions.append(action)
            self._stats["total_actions"] += 1

            # 截断
            if len(self.actions) > self.max_actions:
                self.actions = self.actions[-self.max_actions:]

            return action.timestamp + "_" + str(self._action_counter)

    def record_claim(self, claim_text: str) -> str:
        """记录AI的声称（待验证）"""
        with self._lock:
            self._pending_claim = claim_text
            self._stats["total_claims"] += 1
            action = AIAction(
                timestamp=self._ts(),
                session_id=self.current_session_id,
                action_type=ActionType.CLAIM.value,
                details={},
                claim_text=claim_text,
            )
            self.actions.append(action)
            self._pending_claim_action_id = str(self._action_counter)
            return str(self._action_counter)

    def verify_last_action(
        self,
        expected_action: Optional[str] = None,
        success: bool = True,
        result: Optional[str] = None,
    ) -> None:
        """
        验证最后的行为是否与声称一致
        success=True  → 验证通过（声称 = 实际做了）
        success=False → 验证失败（声称了但没做，或做的不一样）
        """
        with self._lock:
            if not self._pending_claim:
                return

            # 找最近的非claim行为
            verified = False
            for i in range(len(self.actions) - 1, -1, -1):
                a = self.actions[i]
                if a.action_type != ActionType.CLAIM.value:
                    a.verified = success
                    a.verify_result = result or ("OK" if success else f"声称: {self._pending_claim}")
                    verified = True
                    break

            if not verified:
                # 没有对应行为，说明AI只声称没做
                action = AIAction(
                    timestamp=self._ts(),
                    session_id=self.current_session_id,
                    action_type=ActionType.VERIFY_FAIL.value,
                    details={},
                    claim_text=self._pending_claim,
                    verified=False,
                    verify_result="声称了但没有任何实际行为",
                )
                self.actions.append(action)
                self._stats["verified_fail"] += 1

            if success:
                self._stats["verified_ok"] += 1
            else:
                self._stats["verified_fail"] += 1

            self._pending_claim = None
            self._pending_claim_action_id = None

    def record_error(self, error_msg: str, context: Optional[Dict] = None) -> None:
        """记录错误"""
        with self._lock:
            self._stats["errors"] += 1
            action = AIAction(
                timestamp=self._ts(),
                session_id=self.current_session_id,
                action_type=ActionType.ERROR.value,
                details=context or {},
                success=False,
                error=error_msg,
                verify_result=f"ERROR: {error_msg}",
            )
            self.actions.append(action)

    def record_workflow_start(self, workflow_name: str, metadata: Optional[Dict] = None) -> str:
        """记录工作流开始"""
        node = WorkflowNode(
            id=self._next_id(),
            label=workflow_name,
            type="workflow",
            status="running",
            start_time=self._ts(),
            metadata=metadata or {},
        )
        with self._lock:
            self.workflow_stack.append(node)
            if self.root_node is None:
                self.root_node = node
        self.record_action(ActionType.WORKFLOW_START, {
            "workflow": workflow_name,
            "node_id": node.id,
            **(metadata or {})
        })
        return node.id

    def record_workflow_step(
        self,
        step_name: str,
        step_type: str = "step",
        metadata: Optional[Dict] = None,
    ) -> str:
        """记录工作流中的单个步骤"""
        node = WorkflowNode(
            id=self._next_id(),
            label=step_name,
            type=step_type,
            status="running",
            start_time=self._ts(),
            metadata=metadata or {},
        )
        with self._lock:
            if self.workflow_stack:
                self.workflow_stack[-1].children.append(node)
        self.record_action(ActionType.WORKFLOW_STEP, {
            "step": step_name,
            "node_id": node.id,
            "step_type": step_type,
            **(metadata or {})
        })
        return node.id

    def record_workflow_end(
        self,
        status: str = "success",
        result: Optional[Dict] = None,
    ) -> None:
        """记录工作流结束"""
        with self._lock:
            if not self.workflow_stack:
                return
            node = self.workflow_stack.pop()
            node.status = status
            node.end_time = self._ts()
            if node.start_time and node.end_time:
                try:
                    s = datetime.fromisoformat(node.start_time)
                    e = datetime.fromisoformat(node.end_time)
                    node.duration_ms = (e - s).total_seconds() * 1000
                except Exception:
                    pass
            if result:
                node.metadata.update(result)

        self.record_action(ActionType.WORKFLOW_END, {
            "workflow": node.label,
            "node_id": node.id,
            "status": status,
            "duration_ms": node.duration_ms,
            **(result or {})
        })

    def record_thinking(self, thought: str, metadata: Optional[Dict] = None) -> str:
        """记录AI思考过程"""
        node = WorkflowNode(
            id=self._next_id(),
            label=thought[:80] + ("..." if len(thought) > 80 else ""),
            type="thinking",
            status="success",
            start_time=self._ts(),
            end_time=self._ts(),
            metadata=metadata or {"full_thought": thought},
        )
        with self._lock:
            if self.workflow_stack:
                self.workflow_stack[-1].children.append(node)
            elif self.root_node:
                self.root_node.children.append(node)
        self.record_action(ActionType.THINKING, {
            "thought": thought,
            "node_id": node.id,
            **(metadata or {})
        })
        return node.id

    # ─── 导出与统计 ───────────────────────────────────────

    def get_mind_map_data(self) -> Dict[str, Any]:
        """导出思维导图数据（D3.js 可用格式）"""
        with self._lock:
            if self.root_node:
                return self.root_node.to_dict()

            # 没有root则从actions构建
            actions_copy = list(self.actions)
            return {
                "id": self.current_session_id,
                "label": f"Session {self.current_session_id}",
                "type": "session",
                "status": "running",
                "start_time": self.session_start.isoformat(),
                "children": [],
                "actions": [a.to_dict() for a in actions_copy[-100:]],
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计摘要"""
        with self._lock:
            total = self._stats["total_actions"]
            claims = self._stats["total_claims"]
            verified = self._stats["verified_ok"] + self._stats["verified_fail"]
            fail_rate = (
                self._stats["verified_fail"] / verified * 100
                if verified > 0 else 0
            )
            return {
                **self._stats,
                "session_id": self.current_session_id,
                "session_duration_min": (datetime.now() - self.session_start).total_seconds() / 60,
                "verify_fail_rate_pct": round(fail_rate, 1),
                "pending_claim": self._pending_claim,
                "active_workflows": len(self.workflow_stack),
            }

    def get_recent_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近N条行为"""
        with self._lock:
            actions = self.actions[-limit:]
            return [a.to_dict() for a in actions]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘完整数据"""
        return {
            "stats": self.get_stats(),
            "recent_actions": self.get_recent_actions(30),
            "mind_map": self.get_mind_map_data(),
            "active_workflow": (
                self.workflow_stack[-1].to_dict()
                if self.workflow_stack else None
            ),
            "pending_claim": self._pending_claim,
            "session_start": self.session_start.isoformat(),
        }

    def export_session(self, filepath: Optional[Path] = None) -> Path:
        """导出会话数据到JSON"""
        if filepath is None:
            filepath = LOG_DIR / f"session_{self.current_session_id}.json"
        with self._lock:
            data = {
                "session_id": self.current_session_id,
                "session_start": self.session_start.isoformat(),
                "stats": self._stats,
                "mind_map": self.get_mind_map_data(),
                "actions": [a.to_dict() for a in self.actions],
            }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def new_session(self) -> str:
        """开启新会话"""
        # 导出旧会话
        if self.actions:
            self.export_session()
        # 重置
        with self._lock:
            self.actions.clear()
            self.workflow_stack.clear()
            self.root_node = None
            self._pending_claim = None
            self._pending_claim_action_id = None
            self._action_counter = 0
            self.current_session_id = self._new_session_id()
            self.session_start = datetime.now()
            self._stats = {
                "total_actions": 0,
                "total_claims": 0,
                "verified_ok": 0,
                "verified_fail": 0,
                "errors": 0,
            }
        return self.current_session_id

    # ─── 上下文管理器（用于with语句） ─────────────────────

    def track(self, label: str, metadata: Optional[Dict] = None):
        """上下文管理器，自动记录工作流步骤"""
        return _TrackContext(self, label, metadata)


class _TrackContext:
    """with语句上下文"""
    def __init__(self, observer: IronClawObserver, label: str, metadata: Optional[Dict]):
        self.obs = observer
        self.label = label
        self.metadata = metadata or {}
        self.node_id: Optional[str] = None

    def __enter__(self):
        self.node_id = self.obs.record_workflow_step(self.label, metadata=self.metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.obs.record_workflow_end(status="fail", result={
                "error": str(exc_val),
                "traceback": traceback.format_exception(exc_type, exc_val, exc_tb)[-3:]
            })
        else:
            self.obs.record_workflow_end(status="success")
        return False


# 全局单例
_observer_instance: Optional[IronClawObserver] = None
_observer_lock = threading.Lock()


def get_observer() -> IronClawObserver:
    """获取全局Observer实例"""
    global _observer_instance
    if _observer_instance is None:
        with _observer_lock:
            if _observer_instance is None:
                _observer_instance = IronClawObserver()
    return _observer_instance


# ─── 装饰器：自动追踪函数 ─────────────────────────────────

def trace_ai_action(action_label: str = None):
    """自动追踪AI函数的装饰器"""
    def decorator(func):
        name = action_label or func.__name__
        def wrapper(*args, **kwargs):
            obs = get_observer()
            obs.record_action("function_call", {
                "function": name,
                "args": str(args)[:200],
                "kwargs": str(kwargs)[:200],
            })
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                obs.record_error(str(e), {"function": name})
                raise
        return wrapper
    return decorator


if __name__ == "__main__":
    # 演示
    obs = get_observer()
    obs.new_session()

    obs.record_workflow_start("测试工作流", {"user_query": "整理/python目录"})

    obs.record_thinking("需要先了解当前目录结构，然后制定迁移计划", {
        "approach": "分类整理"
    })

    obs.record_claim("正在扫描目录结构")
    with obs.track("扫描 /python 目录"):
        obs.record_action("tool_call", {"tool": "list_dir", "path": "/python"})
    obs.verify_last_action(success=True, result="目录扫描完成，发现78个目录")

    obs.record_workflow_end(status="success", result={"migrated": 10})
    print("Session:", obs.current_session_id)
    print("Stats:", obs.get_stats())
    print("Dashboard:", json.dumps(obs.get_dashboard_data(), ensure_ascii=False, indent=2)[:1000])
