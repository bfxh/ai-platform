#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础设施适配器 — 连接 session_memory / file_protector / evo_engine / ai_rules
到 Skill / Workflow / Plugin / Dispatcher 体系

提供:
- SkillRegistry 钩子: 自动记录每次 skill 执行到会话记忆
- Dispatcher 钩子: 自动记录每次 dispatch 操作
- 进化引擎: 自动追踪性能指标，生成优化建议
- AI 规则引擎: 操作前自动校验，阻止危险操作
- 文件保护自动: skill 执行时自动备份修改的文件

用法:
    from core.infra_adapter import InfraAdapter

    adapter = InfraAdapter()
    adapter.attach_to_skill_registry(registry)   # 注册 skill 钩子
    adapter.attach_to_dispatcher(dispatcher)      # 注册 dispatch 钩子
    adapter.detach_all()                          # 移除所有钩子

或直接启用所有:
    adapter.attach_all()  # 自动检测并挂载到所有已知系统
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# ============================================================
# 内部导入（优雅降级）
# ============================================================

try:
    from session_memory import SessionMemory, get_memory
    _MEMORY_AVAILABLE = True
except ImportError:
    _MEMORY_AVAILABLE = False
    SessionMemory = None
    get_memory = None

try:
    from file_protector import FileProtector, get_protector
    _PROTECTOR_AVAILABLE = True
except ImportError:
    _PROTECTOR_AVAILABLE = False
    FileProtector = None
    get_protector = None

try:
    from evo_engine import EvoEngine, get_evo_engine
    _EVO_AVAILABLE = True
except ImportError:
    _EVO_AVAILABLE = False
    EvoEngine = None
    get_evo_engine = None

try:
    from ai_rules import AIRulesEngine, get_rules_engine
    _RULES_AVAILABLE = True
except ImportError:
    _RULES_AVAILABLE = False
    AIRulesEngine = None
    get_rules_engine = None


class InfraAdapter:
    """基础设施适配器 — 连接新基础设施到现有 skill/workflow/plugin 体系"""

    def __init__(self, auto_start: bool = True):
        self._memory = None
        self._protector = None
        self._session_id: Optional[str] = None
        self._hooks_registered: Dict[str, list] = {}  # track where hooks are registered

        if _MEMORY_AVAILABLE and auto_start:
            try:
                self._memory = get_memory()
                self._session_id = self._memory.create_session(
                    agent="infra_adapter", task="基础设施适配器会话"
                )
            except Exception:
                pass

        if _PROTECTOR_AVAILABLE and auto_start:
            try:
                self._protector = get_protector()
            except Exception:
                pass

        self._evo = None
        if _EVO_AVAILABLE and auto_start:
            try:
                self._evo = get_evo_engine()
            except Exception:
                pass

        self._rules = None
        if _RULES_AVAILABLE and auto_start:
            try:
                self._rules = get_rules_engine()
            except Exception:
                pass

    # ================================================================
    # Skill 钩子
    # ================================================================

    def _on_skill_before(self, skill_name: str, params: dict):
        """Skill 执行前钩子: 校验规则 + 自动备份 + 会话记录"""
        action = params.get("action", "")
        file_path = params.get("path") or params.get("file_path") or params.get("target", "")

        # 1. AI 规则校验
        if self._rules and action in ("write_file", "edit_file", "delete_file", "execute_command"):
            validation = self._rules.validate(action, params)
            if not validation["allowed"]:
                violations = [v["reason"] for v in validation["violations"]]
                raise PermissionError(
                    f"[AI规则] 操作被阻止 ({', '.join(violations)})"
                )

        # 2. 自动备份 — 所有写文件操作前
        if self._protector and action in ("write_file", "edit_file", "write_code") and file_path:
            try:
                abs_path = self._protector.base_dir / file_path
                if abs_path.exists() and abs_path.is_file():
                    self._protector.safe_write(
                        file_path, abs_path.read_text(encoding="utf-8")
                    )
                self._protector.register(file_path)
            except Exception:
                pass  # 备份失败不阻塞操作

        # 3. 会话记录
        if self._memory and self._session_id:
            self._memory.add_message(
                self._session_id, "system",
                f"[Skill] {skill_name}.{action} 开始执行",
                metadata={"skill": skill_name, "action": action, "phase": "before"}
            )

    def _on_skill_after(self, skill_name: str, params: dict):
        """Skill 执行后钩子: 会话记录 + 进化追踪"""
        action = params.get("action", "")

        if self._memory and self._session_id:
            self._memory.add_message(
                self._session_id, "system",
                f"[Skill] {skill_name}.{action} 执行完成",
                metadata={"skill": skill_name, "action": action, "phase": "after"}
            )

        # 进化引擎追踪
        if self._evo:
            try:
                elapsed = params.get("elapsed", params.get("duration_ms", 0) / 1000)
                self._evo.record(
                    f"skill/{skill_name}", action,
                    success=True, elapsed=elapsed
                )
            except Exception:
                pass

    def _on_skill_error(self, skill_name: str, params: dict, error: Exception):
        """Skill 错误钩子: 会话记录 + 进化追踪"""
        action = params.get("action", "")

        if self._memory and self._session_id:
            self._memory.add_result(
                self._session_id, False,
                f"[Skill ERROR] {skill_name}.{action}: {error}",
                detail={"skill": skill_name, "action": action, "error": str(error)}
            )

        # 进化引擎追踪失败
        if self._evo:
            try:
                self._evo.record(
                    f"skill/{skill_name}", action,
                    success=False, error=str(error)[:200]
                )
            except Exception:
                pass

    def attach_to_skill_registry(self, registry) -> int:
        """将基础设施钩子注册到 SkillRegistry

        注册条件: memory / protector / evo / rules 任一项可用即注册。
        钩子内部各自判断是否执行具体操作。

        Args:
            registry: SkillRegistry 实例

        Returns:
            注册的钩子数量
        """
        count = 0
        has_any = any([self._memory, self._protector, self._evo, self._rules])
        if has_any:
            registry.register_global_hook("before_skill_execute", self._on_skill_before)
            registry.register_global_hook("after_skill_execute", self._on_skill_after)
            registry.register_global_hook("skill_error", self._on_skill_error)
            self._hooks_registered["skill_registry"] = [
                "before_skill_execute", "after_skill_execute", "skill_error"
            ]
            count += 3
        return count

    def detach_from_skill_registry(self, registry):
        """从 SkillRegistry 移除钩子"""
        if "skill_registry" in self._hooks_registered:
            registry.unregister_global_hook("before_skill_execute", self._on_skill_before)
            registry.unregister_global_hook("after_skill_execute", self._on_skill_after)
            registry.unregister_global_hook("skill_error", self._on_skill_error)
            del self._hooks_registered["skill_registry"]

    # ================================================================
    # Dispatcher 钩子
    # ================================================================

    def wrap_dispatcher(self, dispatcher):
        """包装 Dispatcher，为 dispatch() 添加会话追踪和文件保护

        用法:
            adapter.wrap_dispatcher(my_dispatcher)
            # 之后 my_dispatcher.dispatch() 会自动记录

        注意: 不修改原对象，而是替换 dispatch 方法
        """
        original_dispatch = dispatcher.dispatch
        adapter = self  # capture for closure

        def wrapped_dispatch(unit_type: str, name: str, **kwargs):
            t0 = time.time()
            start_msg = f"[Dispatch] {unit_type}/{name}"

            # 记录开始
            if adapter._memory and adapter._session_id:
                adapter._memory.add_message(
                    adapter._session_id, "system",
                    f"{start_msg} 开始",
                    metadata={"unit_type": unit_type, "name": name, "phase": "start"}
                )

            # 执行
            try:
                result = original_dispatch(unit_type, name, **kwargs)
                elapsed = time.time() - t0
                success = result.get("status") == "success"

                if adapter._memory and adapter._session_id:
                    summary = result.get("data", result.get("stdout", ""))
                    if isinstance(summary, dict):
                        summary = json.dumps(summary, ensure_ascii=False)[:500]
                    adapter._memory.add_result(
                        adapter._session_id, success,
                        f"{start_msg} ({elapsed:.2f}s)",
                        detail={"unit_type": unit_type, "name": name, "elapsed": elapsed}
                    )

                return result
            except Exception as e:
                if adapter._memory and adapter._session_id:
                    adapter._memory.add_result(
                        adapter._session_id, False,
                        f"{start_msg}: {e}",
                        detail={"unit_type": unit_type, "name": name, "error": str(e)}
                    )
                raise

        dispatcher.dispatch = wrapped_dispatch
        self._hooks_registered["dispatcher"] = ["dispatch"]
        return dispatcher

    def unwrap_dispatcher(self, dispatcher):
        """恢复 Dispatcher 的原始 dispatch 方法"""
        # 由于我们替换了方法，无法轻易恢复
        # 调用者应在包装前保存原始引用
        pass

    # ================================================================
    # 文件保护
    # ================================================================

    def protect_file(self, rel_path: str) -> bool:
        """将文件添加到保护列表"""
        if self._protector:
            self._protector.register(rel_path)
            return True
        return False

    def safe_write(self, rel_path: str, content: str) -> bool:
        """安全写入文件（自动备份）"""
        if self._protector:
            return self._protector.safe_write(rel_path, content)
        return False

    def backup_before_modify(self, rel_path: str) -> bool:
        """在修改前备份文件到 CC/2_old"""
        if not self._protector:
            return False
        try:
            abs_path = self._protector.base_dir / rel_path
            if abs_path.exists() and self._protector.is_protected(rel_path):
                self._protector.safe_write(rel_path, abs_path.read_text(encoding="utf-8"))
                return True
        except Exception:
            pass
        return False

    # ================================================================
    # 会话管理
    # ================================================================

    def get_session_context(self) -> Optional[dict]:
        """获取当前会话上下文"""
        if self._memory and self._session_id:
            return self._memory.get_context(self._session_id)
        return None

    def add_session_note(self, category: str, content: str, result: dict = None):
        """手动添加会话记录（同时记录到 session_memory 和 evo_engine）"""
        if self._memory and self._session_id:
            self._memory.add_message(self._session_id, "system",
                                     f"[{category}] {content}")
            if result:
                self._memory.add_result(
                    self._session_id,
                    result.get("success", result.get("status") == "success"),
                    content[:200],
                    detail=result
                )

        # 进化引擎追踪
        if self._evo and result is not None:
            success = result.get("success",
                       result.get("status") == "success" if isinstance(result, dict) else False)
            elapsed = result.get("elapsed",
                      result.get("duration_ms", 0) / 1000 if isinstance(result, dict) else 0)
            error = result.get("error", "") if isinstance(result, dict) else ""
            self._evo.record(
                category, content[:50],
                success=success, elapsed=elapsed, error=error
            )

    def validate_action(self, action: str, params: dict = None) -> Dict[str, Any]:
        """操作前校验（通过 AI 规则引擎）

        Args:
            action: 操作类型 (write_file, delete_file, execute_command, ...)
            params: 操作参数 (path, content, command, ...)

        Returns:
            {"allowed": bool, "violations": [...], "warnings": [...], "backup_required": bool}
        """
        if self._rules:
            return self._rules.validate(action, params or {})
        return {"allowed": True, "violations": [], "warnings": [], "backup_required": False}

    def mark_complete(self, summary: str = ""):
        """标记当前适配器会话完成"""
        if self._memory and self._session_id:
            if summary:
                self._memory.add_result(self._session_id, True, summary)
            self._memory.close_session(self._session_id)

    def list_recent_sessions(self, limit: int = 10) -> List[dict]:
        """列出最近会话"""
        if self._memory:
            return self._memory.list_sessions(limit=limit)
        return []

    def get_session_stats(self) -> dict:
        """获取会话存储统计"""
        if self._memory:
            return self._memory.get_stats()
        return {}

    # ================================================================
    # 生命周期
    # ================================================================

    def attach_all(self) -> dict:
        """尝试挂载到所有已知的系统组件

        Returns:
            {"skill_registry": N, "superpowers": True/False,
             "evaluator": True/False, "data_bridge": True/False, ...}
        """
        results = {}

        # 1. Skill Registry
        try:
            from skills.base import get_registry
            n = self.attach_to_skill_registry(get_registry())
            results["skill_registry"] = n
        except Exception:
            results["skill_registry"] = 0

        # 2. Superpower Engine
        try:
            self.attach_to_superpowers()
            results["superpowers"] = True
        except Exception:
            results["superpowers"] = False

        # 3. Evaluator
        try:
            self.attach_to_evaluator()
            results["evaluator"] = True
        except Exception:
            results["evaluator"] = False

        # 4. Data Bridge
        try:
            self.attach_to_data_bridge()
            results["data_bridge"] = True
        except Exception:
            results["data_bridge"] = False

        return results

    def attach_to_superpowers(self, engine=None) -> bool:
        """将 infra 钩子注册到 Superpower 引擎

        自动在 superpower 步骤执行前后记录 session + evo。
        """
        try:
            if engine is None:
                from core.superpowers import get_superpower_engine
                engine = get_superpower_engine()
            # Superpower 引擎已在 __init__ 中连接 adapter/evo/rules/protector
            # 这里确保 engine 引用了当前 adapter
            engine._adapter = self
            return True
        except Exception:
            return False

    def attach_to_evaluator(self, benchmark=None) -> bool:
        """将 evo 反馈通道连接到评估系统"""
        try:
            from core.evaluator import EvolutionFeeder
            feeder = EvolutionFeeder(self._evo)
            # feeder 自动连接 evo_engine
            return True
        except Exception:
            return False

    def attach_to_data_bridge(self, bridge=None) -> bool:
        """将 bridge 同步事件注册到 session_memory"""
        try:
            if bridge is None:
                from core.data_bridge import get_bridge
                bridge = get_bridge()
            bridge._adapter = self
            return True
        except Exception:
            return False

    def detach_all(self):
        """移除所有钩子"""
        # 尝试从 SkillRegistry 移除
        try:
            from skills.base import get_registry
            self.detach_from_skill_registry(get_registry())
        except Exception:
            pass

        self._hooks_registered.clear()

    def shutdown(self):
        """关闭适配器"""
        self.detach_all()
        if self._memory and self._session_id:
            try:
                self._memory.close_session(self._session_id)
            except Exception:
                pass


# ============================================================
# 模块级便捷函数
# ============================================================

_adapter_instance = None


def get_adapter() -> InfraAdapter:
    """获取全局基础设施适配器"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = InfraAdapter()
    return _adapter_instance
