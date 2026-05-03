#!/usr/bin/env python
"""Brain ↔ Shared Context Bridge

将 Brain 的任务生命周期事件同步到跨 Agent 共享上下文系统。
遵循 event_bridge.py 的同一集成模式。

使用方式:
    from integration.shared_context_bridge import hook_pre_task, hook_post_task
"""

import json
from datetime import datetime
from pathlib import Path


def _get_scm():
    """延迟导入共享上下文管理器（优雅降级）。"""
    try:
        from core.shared_context import get_shared_context
        return get_shared_context(agent_id="Qoder", agent_type="qoder", auto_start=True)
    except ImportError:
        return None
    except Exception:
        # 共享上下文初始化失败时优雅降级为单 Agent 模式
        return None


def hook_pre_task(brain, instruction: str,
                  planned_action: str = "",
                  expected_files: list = None) -> dict:
    """在 Brain.pre_task() 完成后调用。

    功能:
    1. 广播当前 Agent 即将执行的任务
    2. 创建共享任务条目
    3. 检测文件冲突

    Returns:
        {"conflicts": [...], "other_agents": [...]} 或空 dict
    """
    ctx = _get_scm()
    if ctx is None:
        return {}

    conflict_info = {}

    try:
        # 创建任务 ID
        task_id = f"task_{brain._session_id}_{brain._task_count + 1}"

        # 注册任务
        ctx.create_task(
            task_id=task_id,
            title=instruction[:200],
            files_involved=expected_files or [],
            priority=0,
        )

        # 广播上下文
        ctx.broadcast_context(
            summary=instruction[:200],
            key_files=expected_files or [],
            key_decisions=[f"Task started: {planned_action or instruction[:100]}"],
        )

        # 检测冲突
        if expected_files:
            conflicts = []
            for f in expected_files:
                c = ctx.check_file_conflicts(f)
                if c:
                    conflicts.append(c)
            if conflicts:
                conflict_info["conflicts"] = conflicts

        # 获取其他活跃 Agent
        others = ctx.registry.discover_agents(exclude_self=ctx.agent_id)
        if others:
            conflict_info["other_agents"] = [
                {"id": a["agent_id"], "type": a["agent_type"], "task": a.get("current_task", "")}
                for a in others
            ]

    except (OSError, json.JSONDecodeError):
        # 共享上下文操作失败时优雅降级，不阻塞主流程
        pass

    return conflict_info


def hook_post_task(brain, success: bool, result: str,
                   instruction: str = "",
                   files_touched: list = None,
                   lessons: list = None) -> dict:
    """在 Brain.post_task() 完成后调用。

    功能:
    1. 更新任务状态
    2. 记录文件操作日志
    3. 推送知识到同步队列

    Returns:
        {"logged_files": N, "pushed_knowledge": True/False}
    """
    ctx = _get_scm()
    if ctx is None:
        return {}

    ret = {"logged_files": 0, "pushed_knowledge": False}

    try:
        task_id = f"task_{brain._session_id}_{brain._task_count}"

        # 更新任务状态
        ctx.task_board.update_task(
            task_id=task_id,
            status="completed" if success else "failed",
            result_summary=result[:200],
        )

        # 记录文件操作
        if files_touched:
            for f in files_touched:
                ctx.log_file_operation(
                    event="file_modified",
                    file_path=f,
                    operation="write",
                    task_id=task_id,
                )
            ret["logged_files"] = len(files_touched)

        # 推送知识（如果任务成功且有经验教训）
        if success and lessons:
            ctx.push_knowledge(
                title=instruction[:150] if instruction else "task_result",
                content=f"Result: {result[:300]}. Lessons: {'; '.join(lessons[:3])}",
                category="project_context" if files_touched else "domain_knowledge",
                tags=["brain_task", f"session_{brain._session_id}"],
                importance=5,
            )
            ret["pushed_knowledge"] = True

        # 推送产出标准合规检查结果
        if files_touched:
            std_result = brain.audit.check_output_standards(files_touched)
            if not std_result["passed"]:
                ctx.push_knowledge(
                    title="Output standard violations detected",
                    content=f"Task: {instruction[:100]}. "
                            f"Violations: {len(std_result['violations'])}. "
                            f"Files: {', '.join([v.get('file', '?') for v in std_result['violations'][:5]])}",
                    category="compliance",
                    tags=["output_standards", f"session_{brain._session_id}"],
                    importance=8,
                )
                ret["output_standards_checked"] = True
                ret["output_standards_violations"] = len(std_result["violations"])

    except (OSError, json.JSONDecodeError):
        # 共享上下文操作失败时优雅降级，不阻塞主流程
        pass

    return ret
