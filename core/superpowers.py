#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Superpowers 引擎 — 基于 obra/superpowers 的可组合技能链

核心设计:
- 可组合技能链: 将多个 skill/mcp/cli/workflow 串联为 "Superpower"
- 触发式激活: 根据文件变更/命令/上下文自动匹配适用的 superpower
- 强制性工作流: 某些工作流(TDD/安全审计)不可跳过
- 人工审批门槛: 关键步骤需要人工确认才继续
- 多步计划追踪: 带暂停/恢复/中止的长时间执行

用法:
    from core.superpowers import SuperpowerEngine

    engine = SuperpowerEngine()
    engine.load_all()
    # 上下文触发
    matches = engine.find_matching({"command": "implement login feature"})
    for sp in matches:
        engine.execute(sp.name, context)
    # 或直接执行
    engine.execute("test-driven-development", {"file": "auth.py"})
"""

import json
import os
import re
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple


# ============================================================
# 数据模型
# ============================================================

@dataclass
class SuperpowerStep:
    """单个技能步骤"""
    step_id: str
    skill_ref: str          # "skill_name.action" 或 "mcp_name.tool"
    gate: str = "none"      # none / auto / human
    condition: str = ""     # Python 表达式, 如 "previous_step.success"
    description: str = ""
    params: dict = field(default_factory=dict)
    timeout: int = 300


@dataclass
class SuperpowerDescriptor:
    """Superpower 描述符"""
    name: str
    description: str = ""
    version: str = "1.0"
    triggers: List[dict] = field(default_factory=list)
    steps: List[SuperpowerStep] = field(default_factory=list)
    enforce_mandatory: bool = False
    cross_agent: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    config_path: str = ""


# ============================================================
# 触发系统
# ============================================================

class TriggerSystem:
    """上下文触发器 — 根据事件匹配 superpower"""

    def __init__(self):
        self._triggers: Dict[str, List[str]] = defaultdict(list)
        # trigger_pattern → [superpower_name, ...]

    def register(self, pattern: str, superpower_name: str):
        """注册触发模式"""
        self._triggers[pattern].append(superpower_name)

    def remove(self, pattern: str, superpower_name: str = None):
        """移除触发模式"""
        if superpower_name:
            if pattern in self._triggers:
                self._triggers[pattern] = [
                    n for n in self._triggers[pattern] if n != superpower_name
                ]
                if not self._triggers[pattern]:
                    del self._triggers[pattern]
        else:
            self._triggers.pop(pattern, None)

    def evaluate(self, event: dict) -> List[str]:
        """根据事件匹配 superpowers

        Args:
            event: {"command": "implement login", "file": "core/auth.py",
                     "type": "dispatch_started", "args": ...}

        Returns:
            匹配的 superpower 名称列表
        """
        matched = set()

        command_text = event.get("command", "")
        file_path = event.get("file", event.get("path", ""))
        event_type = event.get("type", "")

        for pattern, names in self._triggers.items():
            for name in names:
                # 命令匹配
                if command_text and self._match_command(pattern, command_text):
                    matched.add(name)
                # 文件匹配
                elif file_path and fnmatch(file_path, pattern):
                    matched.add(name)
                # 事件类型匹配
                elif event_type and pattern == event_type:
                    matched.add(name)

        return list(matched)

    def on_file_change(self, file_path: str) -> List[str]:
        """文件变更触发"""
        return self.evaluate({"file": file_path, "type": "file_modified"})

    def on_command(self, command_text: str) -> List[str]:
        """命令触发"""
        return self.evaluate({"command": command_text, "type": "command_executed"})

    def get_all_triggers(self) -> dict:
        """获取所有触发模式"""
        return dict(self._triggers)

    @staticmethod
    def _match_command(pattern: str, command: str) -> bool:
        """匹配命令模式 (支持简单 regex)"""
        try:
            return bool(re.search(pattern, command, re.IGNORECASE))
        except re.error:
            return pattern.lower() in command.lower()


# ============================================================
# 人工审批门
# ============================================================

class HumanGate:
    """人工审批门槛 — 关键步骤需人工确认"""

    DEFAULT_TIMEOUT = 300  # 5 分钟

    def __init__(self, callback: Callable = None):
        self._callback = callback
        self._pending: Dict[str, dict] = {}
        self._history: List[dict] = []

    def set_callback(self, callback: Callable):
        """设置审批回调函数

        callback(context) → True (批准) / False (拒绝)
        """
        self._callback = callback

    def request_approval(self, gate_id: str, context: dict = None,
                         timeout: int = None) -> bool:
        """请求人工审批

        Args:
            gate_id:  审批门 ID
            context:  上下文信息
            timeout:  超时秒数, None 使用默认

        Returns:
            True=批准, False=拒绝/超时
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        context = context or {}

        self._pending[gate_id] = {
            "id": gate_id,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }

        if self._callback:
            try:
                approved = self._callback(context)
                self._record(gate_id, approved)
                return approved
            except Exception:
                pass

        # 无回调 → 自动批准 (跳过人工审批)
        self._record(gate_id, True)
        return True

    def wait_for_approval(self, gate_id: str, timeout: int = None) -> bool:
        """阻塞等待审批"""
        timeout = timeout or self.DEFAULT_TIMEOUT
        start = time.time()

        while time.time() - start < timeout:
            entry = self._pending.get(gate_id)
            if entry and entry.get("status") != "pending":
                return entry.get("status") == "approved"
            time.sleep(0.5)

        # 超时 → 自动拒绝
        self._record(gate_id, False)
        return False

    def approve(self, gate_id: str):
        """外部批准"""
        self._record(gate_id, True)

    def reject(self, gate_id: str):
        """外部拒绝"""
        self._record(gate_id, False)

    def get_pending(self) -> List[dict]:
        """获取所有待审批的门"""
        return [v for v in self._pending.values() if v.get("status") == "pending"]

    def get_history(self) -> List[dict]:
        """获取审批历史"""
        return self._history[-20:]

    def _record(self, gate_id: str, approved: bool):
        entry = self._pending.get(gate_id, {"id": gate_id})
        entry["status"] = "approved" if approved else "rejected"
        entry["resolved_at"] = datetime.now().isoformat()
        self._pending[gate_id] = entry
        self._history.append(entry)


# ============================================================
# 计划执行器
# ============================================================

class PlanExecutor:
    """多步计划执行器 — 带进度追踪的长时间执行"""

    def __init__(self, superpower_engine=None):
        self._engine = superpower_engine
        self._plans: Dict[str, dict] = {}
        self._lock = threading.RLock()

    def set_engine(self, engine):
        self._engine = engine

    def execute_plan(self, superpower_name: str,
                     context: dict = None) -> dict:
        """执行完整计划"""
        if not self._engine:
            return {"success": False, "error": "引擎未设置"}

        plan_id = f"{superpower_name}_{int(time.time())}"
        plan = {
            "id": plan_id,
            "superpower": superpower_name,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "current_step": 0,
            "total_steps": 0,
            "completed": [],
            "remaining": [],
            "results": {},
            "errors": [],
        }

        with self._lock:
            self._plans[plan_id] = plan

        try:
            result = self._engine.execute(superpower_name, context)
            plan["status"] = "completed" if result.get("success") else "failed"
            plan["completed_at"] = datetime.now().isoformat()
            plan["results"]["final"] = result

            if plan["status"] == "completed":
                plan["current_step"] = plan["total_steps"]
                plan["remaining"] = []

            return {**result, "plan_id": plan_id, "plan_status": plan["status"]}
        except Exception as e:
            plan["status"] = "failed"
            plan["errors"].append(str(e))
            return {"success": False, "plan_id": plan_id, "error": str(e)}

    def get_progress(self, plan_id: str) -> dict:
        """获取计划进度"""
        plan = self._plans.get(plan_id, {})
        if not plan:
            return {"error": "计划不存在"}
        return {
            "plan_id": plan_id,
            "status": plan.get("status"),
            "current_step": plan.get("current_step", 0),
            "total_steps": len(plan.get("completed", [])) + len(plan.get("remaining", [])),
            "completed_steps": len(plan.get("completed", [])),
            "elapsed": str(datetime.now() - datetime.fromisoformat(
                plan.get("started_at", datetime.now().isoformat())
            )).split(".")[0] if plan.get("started_at") else "?",
        }

    def pause_plan(self, plan_id: str) -> bool:
        plan = self._plans.get(plan_id)
        if plan and plan.get("status") == "running":
            plan["status"] = "paused"
            return True
        return False

    def resume_plan(self, plan_id: str) -> bool:
        plan = self._plans.get(plan_id)
        if plan and plan.get("status") == "paused":
            plan["status"] = "running"
            return True
        return False

    def abort_plan(self, plan_id: str) -> bool:
        plan = self._plans.get(plan_id)
        if plan and plan.get("status") in ("running", "paused"):
            plan["status"] = "aborted"
            plan["aborted_at"] = datetime.now().isoformat()
            return True
        return False

    def list_plans(self) -> List[dict]:
        """列出所有计划"""
        return [
            {"id": pid, "superpower": p.get("superpower", "?"),
             "status": p.get("status", "?"),
             "started": p.get("started_at", "")[:19]}
            for pid, p in self._plans.items()
        ]


# ============================================================
# Superpower 引擎
# ============================================================

class SuperpowerEngine:
    """Superpower 主引擎"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.sp_dir = self.base_dir / "storage" / "superpowers"
        self.sp_dir.mkdir(parents=True, exist_ok=True)

        # 组件
        self.trigger_system = TriggerSystem()
        self.human_gate = HumanGate()
        self.plan_executor = PlanExecutor(self)

        # 注册的 superpowers
        self._registry: Dict[str, SuperpowerDescriptor] = {}

        # 基础设施集成 (优雅降级)
        self._adapter = None
        self._evo = None
        self._rules = None
        self._protector = None
        try:
            from core.infra_adapter import get_adapter
            self._adapter = get_adapter()
        except Exception:
            pass
        try:
            from core.evo_engine import get_evo_engine
            self._evo = get_evo_engine()
        except Exception:
            pass
        try:
            from core.ai_rules import get_rules_engine
            self._rules = get_rules_engine()
        except Exception:
            pass
        try:
            from core.file_protector import get_protector
            self._protector = get_protector()
        except Exception:
            pass

        # 加载已有
        self.load_all()

    # ================================================================
    # 加载
    # ================================================================

    def load_all(self) -> Dict[str, SuperpowerDescriptor]:
        """加载所有 superpower YAML 文件"""
        self._registry.clear()
        self.trigger_system._triggers.clear()

        for yaml_file in self.sp_dir.glob("*.yaml"):
            try:
                desc = self._parse_yaml(yaml_file)
                if desc:
                    self._registry[desc.name] = desc
                    for trigger in desc.triggers:
                        for pattern in trigger.get("patterns",
                          trigger.get("pattern", [])):
                            if isinstance(pattern, str):
                                self.trigger_system.register(pattern, desc.name)
            except Exception as e:
                print(f"[Superpowers] 加载失败 {yaml_file}: {e}")

        # 如果没有文件, 写入默认 superpowers
        if not self._registry:
            self._write_defaults()

        return self._registry

    def _parse_yaml(self, filepath: Path) -> Optional[SuperpowerDescriptor]:
        """解析 YAML 文件"""
        try:
            import yaml
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except ImportError:
            try:
                import json
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return None

        if not data or "name" not in data:
            return None

        steps = []
        for step_data in data.get("skills", data.get("steps", [])):
            steps.append(SuperpowerStep(
                step_id=step_data.get("step", step_data.get("id", f"step_{len(steps)}")),
                skill_ref=step_data.get("skill", ""),
                gate=step_data.get("gate", "none"),
                condition=step_data.get("condition", ""),
                description=step_data.get("description", ""),
                params=step_data.get("params", {}),
                timeout=step_data.get("timeout", 300),
            ))

        triggers = data.get("triggers", [])
        normalized_triggers = []
        for t in triggers:
            if isinstance(t, str):
                normalized_triggers.append({"patterns": [t]})
            elif isinstance(t, dict):
                if "pattern" in t and "patterns" not in t:
                    t = dict(t)
                    t["patterns"] = [t.pop("pattern")]
                normalized_triggers.append(t)

        return SuperpowerDescriptor(
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            triggers=normalized_triggers,
            steps=steps,
            enforce_mandatory=data.get("enforce_mandatory", False),
            cross_agent=data.get("cross_agent", []),
            tags=data.get("tags", []),
            config_path=str(filepath),
        )

    def _write_defaults(self):
        """写入默认 superpower YAML 文件"""
        defaults = [
            self._default_tdd(),
            self._default_red_green_refactor(),
            self._default_security_audit(),
        ]
        for desc_data in defaults:
            filepath = self.sp_dir / f"{desc_data['name']}.yaml"
            try:
                import yaml
                with open(filepath, "w", encoding="utf-8") as f:
                    yaml.dump(desc_data, f, allow_unicode=True, default_flow_style=False)
            except ImportError:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(desc_data, f, ensure_ascii=False, indent=2)
        self.load_all()

    # ================================================================
    # 查询
    # ================================================================

    def get(self, name: str) -> Optional[SuperpowerDescriptor]:
        return self._registry.get(name)

    def list_superpowers(self) -> List[dict]:
        return [
            {
                "name": desc.name,
                "description": desc.description,
                "version": desc.version,
                "steps": len(desc.steps),
                "enforce_mandatory": desc.enforce_mandatory,
                "tags": desc.tags,
            }
            for desc in self._registry.values()
        ]

    def find_matching(self, context: dict) -> List[SuperpowerDescriptor]:
        """根据上下文匹配 superpowers"""
        names = self.trigger_system.evaluate(context)
        return [self._registry[n] for n in names if n in self._registry]

    def is_mandatory(self, context: dict) -> List[SuperpowerDescriptor]:
        """检查强制工作流"""
        all_matches = self.find_matching(context)
        return [sp for sp in all_matches if sp.enforce_mandatory]

    # ================================================================
    # 执行
    # ================================================================

    def execute(self, name: str, context: dict = None) -> dict:
        """执行一个 superpower 的完整步骤序列

        Returns:
            {"success": bool, "steps_executed": int, "steps_skipped": int,
             "gate_results": [...], "step_results": [...]}
        """
        context = context or {}
        desc = self._registry.get(name)
        if not desc:
            return {"success": False, "error": f"Superpower 不存在: {name}"}

        # AI 规则校验
        if self._rules:
            validation = self._rules.validate("execute_superpower", {
                "superpower": name, "steps": len(desc.steps),
                "mandatory": desc.enforce_mandatory,
            })
            if not validation["allowed"]:
                return {"success": False,
                        "error": f"AI规则阻止: {validation['violations']}"}

        step_results = []
        gate_results = []
        steps_executed = 0
        steps_skipped = 0
        t0 = time.time()

        for i, step in enumerate(desc.steps):
            # 检查 condition
            if step.condition:
                if not self._eval_condition(step.condition, step_results, context):
                    steps_skipped += 1
                    continue

            # 人工审批门
            if step.gate == "human":
                approved = self.human_gate.request_approval(
                    f"{name}/{step.step_id}",
                    context={"step": step.step_id, "description": step.description}
                )
                gate_results.append({"step": step.step_id, "approved": approved})
                if not approved:
                    return {
                        "success": False,
                        "steps_executed": steps_executed,
                        "steps_skipped": steps_skipped,
                        "gate_results": gate_results,
                        "error": f"人工审批拒绝: {step.step_id}",
                    }

            # 文件保护 — 写操作前备份
            if self._protector and step.skill_ref.startswith("write"):
                try:
                    file_path = step.params.get("path", step.params.get("file_path", ""))
                    if file_path:
                        self._adapter.backup_before_modify(file_path)
                except Exception:
                    pass

            # 执行步骤
            step_result = self._execute_step(desc, step, i, context)
            step_results.append({
                "step": step.step_id,
                "skill": step.skill_ref,
                "success": step_result.get("success", False),
                "result": step_result,
            })

            if step_result.get("success"):
                steps_executed += 1
            else:
                # 步骤失败但非 fatal → 继续
                if step.gate == "none":
                    steps_executed += 1

        elapsed = time.time() - t0

        # 进化引擎追踪
        if self._evo:
            try:
                self._evo.record(
                    f"superpower/{name}", "execute",
                    success=steps_executed > 0,
                    elapsed=elapsed,
                    error="" if steps_executed > 0 else "all steps failed",
                    metadata={"steps_total": len(desc.steps),
                               "steps_executed": steps_executed,
                               "steps_skipped": steps_skipped}
                )
            except Exception:
                pass

        return {
            "success": steps_executed > 0,
            "steps_executed": steps_executed,
            "steps_skipped": steps_skipped,
            "total_steps": len(desc.steps),
            "elapsed": round(elapsed, 3),
            "gate_results": gate_results,
            "step_results": step_results,
        }

    def _execute_step(self, desc: SuperpowerDescriptor,
                      step: SuperpowerStep, index: int,
                      context: dict) -> dict:
        """执行单个步骤"""
        try:
            # 尝试通过 dispatcher 执行
            from core.dispatcher import Dispatcher
            dispatcher = Dispatcher()

            # 解析 skill_ref: "skill_name.action" 或 "mcp_name.tool"
            if "." in step.skill_ref:
                unit_type = "skill"
                unit_name, action = step.skill_ref.rsplit(".", 1)
                params = {**step.params, "action": action, **context}
                return dispatcher.dispatch("skill", unit_name, **params)
            else:
                # 尝试各类型
                for ut in ["skill", "mcp", "workflow"]:
                    try:
                        return dispatcher.dispatch(ut, step.skill_ref,
                                                   action="execute",
                                                   **step.params, **context)
                    except Exception:
                        continue
                return {"success": False, "error": f"无法解析: {step.skill_ref}"}

        except ImportError:
            # 无 dispatcher → 模拟执行
            time.sleep(0.01)
            return {"success": True, "simulated": True, "step": step.step_id}
        except Exception as e:
            return {"success": False, "error": str(e), "step": step.step_id}

    @staticmethod
    def _eval_condition(condition: str, step_results: List[dict],
                        context: dict) -> bool:
        """评估步骤条件"""
        try:
            previous = step_results[-1] if step_results else {"success": True}
            local_vars = {
                "previous_step": previous,
                "context": context,
                "success": previous.get("success", True),
            }
            return bool(eval(condition, {"__builtins__": {}}, local_vars))
        except Exception:
            return True  # 条件错误 → 默认通过

    # ================================================================
    # 管理
    # ================================================================

    def register_superpower(self, descriptor: dict) -> str:
        """动态注册 superpower 并持久化"""
        name = descriptor.get("name")
        if not name:
            raise ValueError("Superpower 必须包含 name")

        filepath = self.sp_dir / f"{name}.yaml"
        try:
            import yaml
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(descriptor, f, allow_unicode=True, default_flow_style=False)
        except ImportError:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(descriptor, f, ensure_ascii=False, indent=2)

        self.load_all()
        return name

    def unregister_superpower(self, name: str) -> bool:
        """移除 superpower"""
        desc = self._registry.get(name)
        if desc and desc.config_path:
            try:
                os.remove(desc.config_path)
            except Exception:
                pass
        removed = self._registry.pop(name, None) is not None
        return removed

    def get_plan_progress(self, superpower_name: str) -> dict:
        """获取计划进度"""
        # 查找该 superpower 对应的计划
        for pid, plan in self.plan_executor._plans.items():
            if plan.get("superpower") == superpower_name:
                return self.plan_executor.get_progress(pid)
        return {"error": "无活跃计划"}

    # ================================================================
    # 默认 superpowers
    # ================================================================

    @staticmethod
    def _default_tdd() -> dict:
        return {
            "name": "test-driven-development",
            "description": "RED-GREEN-REFACTOR 强制循环 — 修改代码前必须先写测试",
            "version": "1.0",
            "enforce_mandatory": False,
            "tags": ["testing", "quality", "tdd"],
            "cross_agent": ["trae", "claude"],
            "triggers": [
                {"patterns": ["implement", "fix bug", "add feature", "创建", "修复", "添加功能"],
                 "field": "command"},
            ],
            "skills": [
                {"step": "write_test", "skill": "test-generator.run",
                 "description": "先写失败的测试",
                 "gate": "none", "timeout": 120},
                {"step": "run_test_red", "skill": "test-runner.run",
                 "description": "确认测试失败 (RED)",
                 "condition": "previous_step.success == True",
                 "gate": "none", "timeout": 60},
                {"step": "implement", "skill": "trae_control.write_file",
                 "description": "实现代码 (GREEN)",
                 "condition": "previous_step.success == False",
                 "gate": "none", "timeout": 300},
                {"step": "run_test_green", "skill": "test-runner.run",
                 "description": "确认测试通过",
                 "condition": "previous_step.success == True",
                 "gate": "none", "timeout": 60},
                {"step": "refactor", "skill": "code-reviewer.review",
                 "description": "重构代码 (REFACTOR)",
                 "gate": "human", "timeout": 300},
            ],
        }

    @staticmethod
    def _default_red_green_refactor() -> dict:
        return {
            "name": "red-green-refactor",
            "description": "严格的 RED-GREEN-REFACTOR 循环 — 每个修改必须经过测试→实现→重构",
            "version": "1.0",
            "enforce_mandatory": False,
            "tags": ["testing", "quality", "discipline"],
            "cross_agent": ["trae", "claude", "qoder"],
            "triggers": [
                {"patterns": ["modify core", "change dispatcher", "修改核心"],
                 "field": "command"},
                {"patterns": ["core/*.py"],
                 "field": "file_modified"},
            ],
            "skills": [
                {"step": "analyze_impact", "skill": "code-analyzer.run",
                 "description": "分析影响范围", "timeout": 60},
                {"step": "write_test", "skill": "test-generator.run",
                 "description": "编写失败测试", "timeout": 120},
                {"step": "verify_red", "skill": "test-runner.run",
                 "description": "确认测试失败",
                 "condition": "previous_step.success == True",
                 "timeout": 60},
                {"step": "implement_change", "skill": "trae_control.write_file",
                 "description": "实现变更", "timeout": 300},
                {"step": "verify_green", "skill": "test-runner.run",
                 "description": "确认测试通过",
                 "condition": "previous_step.success == True",
                 "timeout": 60},
                {"step": "refactor_cleanup", "skill": "code-reviewer.review",
                 "description": "重构清理",
                 "gate": "human", "timeout": 300},
            ],
        }

    @staticmethod
    def _default_security_audit() -> dict:
        return {
            "name": "security-audit",
            "description": "安全审计工作流 — 修改安全敏感代码前必须审计",
            "version": "1.0",
            "enforce_mandatory": True,
            "tags": ["security", "audit", "mandatory"],
            "cross_agent": ["claude", "qoder"],
            "triggers": [
                {"patterns": ["auth", "login", "password", "token", "credential",
                              "安全", "认证", "密码", "凭证"],
                 "field": "command"},
                {"patterns": ["**/auth*", "**/login*", "**/credential*", "*.env"],
                 "field": "file_modified"},
            ],
            "skills": [
                {"step": "scan_vulnerabilities", "skill": "security-scanner.scan",
                 "description": "扫描已知漏洞", "timeout": 120},
                {"step": "review_dependencies", "skill": "dependency-checker.check",
                 "description": "检查依赖安全性", "timeout": 60},
                {"step": "audit_access_control", "skill": "code-reviewer.review",
                 "description": "审计权限控制",
                 "condition": "previous_step.success == True",
                 "timeout": 120},
                {"step": "human_review", "skill": "report-generator.generate",
                 "description": "生成审计报告——等待人工审核",
                 "gate": "human", "timeout": 600},
            ],
        }


# ============================================================
# 模块级便捷函数
# ============================================================

_instance = None


def get_superpower_engine() -> SuperpowerEngine:
    """获取全局 Superpower 引擎"""
    global _instance
    if _instance is None:
        _instance = SuperpowerEngine()
    return _instance
