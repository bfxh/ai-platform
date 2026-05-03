#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编排代理入口脚本 — 被 Multica Daemon 或 Dispatcher 调用的 CLI

功能:
- 接收任务请求（stdin JSON 或 CLI 参数）
- 通过 Claude 编排代理分析意图并路由
- 在目标子代理上执行任务
- 返回 Daemon 兼容的结构化结果

用法:
    # 从 stdin 传入 JSON
    echo '{"task": "创建 React Login 组件", "session_id": "abc"}' | \
        python scripts/run_orchestrated_agent.py

    # 直接传入任务文本
    python scripts/run_orchestrated_agent.py --task "读取 /main.py"

    # 详细输出模式
    python scripts/run_orchestrated_agent.py --task "执行 npm install" --verbose

输出 (JSON, stdout):
{
    "status": "completed",
    "comment": "...",
    "session_id": "...",
    "work_dir": "...",
    "usage": [],
    "result": {...}
}
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# ============================================================
# 路径设置
# ============================================================
_SCRIPT_DIR = Path(__file__).resolve().parent
_BASE_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_BASE_DIR))
sys.path.insert(0, str(_BASE_DIR / "core"))
sys.path.insert(0, str(_BASE_DIR / "user" / "global" / "plugin" /
                       "mcp-core" / "agent"))
os.environ.setdefault("AI_BASE_DIR", str(_BASE_DIR))

# 导入新基础设施
try:
    from session_memory import SessionMemory, get_memory
    _MEMORY_AVAILABLE = True
except ImportError:
    _MEMORY_AVAILABLE = False

try:
    from file_protector import FileProtector, get_protector
    _PROTECTOR_AVAILABLE = True
except ImportError:
    _PROTECTOR_AVAILABLE = False


# ============================================================
# 结果格式化
# ============================================================

def format_daemon_result(
    status: str,
    comment: str,
    session_id: Optional[str] = None,
    work_dir: Optional[str] = None,
    usage: Optional[list] = None,
    result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """格式化为 Daemon 兼容的 TaskResult"""
    return {
        "status": status,                 # "completed" | "failed" | "blocked"
        "comment": comment[:4096],        # 输出文本（截断到 4KB）
        "session_id": session_id or str(uuid.uuid4().hex[:12]),
        "work_dir": work_dir or str(_BASE_DIR),
        "env_type": "python",
        "usage": usage or [],
        "branch_name": "",
        # 附加字段（非 daemon 标准，供调试用）
        "result": result or {},
    }


# ============================================================
# 编排引擎
# ============================================================

class OrchestratedAgentRunner:
    """编排代理运行器 — 连接 Claude 编排器并执行任务

    集成: session_memory (会话持久化) + file_protector (安全写入)
    """

    def __init__(self, verbose: bool = False, resume_session: str = None):
        self.verbose = verbose
        self.start_time = datetime.now()
        self._orch = None

        # ---- 会话记忆 ----
        self.memory = None
        if _MEMORY_AVAILABLE:
            self.memory = get_memory()
            if resume_session:
                loaded = self.memory.load_session(resume_session)
                if loaded:
                    self.session_id = resume_session
                    self.log(f"恢复会话: {resume_session}")
                    # 更新任务
                    self.memory.add_message(resume_session, "system",
                                            "会话已恢复，继续执行")
                    return
            self.session_id = self.memory.create_session(
                agent="orchestrator", task=""
            )
        else:
            self.session_id = str(uuid.uuid4().hex[:12])

        # ---- 文件保护 ----
        self.protector = None
        if _PROTECTOR_AVAILABLE:
            self.protector = get_protector()

    def log(self, msg: str):
        if self.verbose:
            print(f"[{self.session_id[:8]}] {msg}", file=sys.stderr)

    @property
    def orchestrator(self):
        """延迟加载编排器"""
        if self._orch is None:
            try:
                from claude_orch.claude_orchestrator import get_orchestrator
                self._orch = get_orchestrator()
                self.log(f"编排代理已加载 (status={self._orch.status})")
            except ImportError as e:
                self.log(f"编排代理导入失败: {e}")
                return None
            except Exception as e:
                self.log(f"编排代理初始化失败: {e}")
                return None
        return self._orch

    def execute(self, task_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行编排任务

        Args:
            task_text: 用户输入的自然语言任务
            context:   可选的上下文信息

        Returns:
            Daemon 兼容的结果字典
        """
        self.log(f"接收任务: {task_text[:120]}")

        # ---- 记录到会话记忆 ----
        if self.memory:
            self.memory.add_message(self.session_id, "user", task_text)

        # ---- 注入会话上下文 ----
        enriched_context = context or {}
        if self.memory:
            ctx_summary = self.memory.get_context(self.session_id,
                                                  max_messages=10)
            if ctx_summary.get("available"):
                enriched_context["session_summary"] = ctx_summary.get("summary", "")
                enriched_context["prior_results"] = [
                    r for r in ctx_summary.get("recent_results", [])
                ]

        # ---- 路径 1: Claude 编排代理 ----
        orch = self.orchestrator
        if orch is not None and orch._initialized:
            try:
                task = {
                    "task": task_text,
                    "task_type": "orchestrate",
                    "context": enriched_context,
                }
                orch_result = orch.execute(task)
                self.log(f"编排完成: intent={orch_result.get('intent')}, "
                          f"agent={orch_result.get('agent')}, "
                          f"success={orch_result.get('success')}")

                result = format_daemon_result(
                    status="completed" if orch_result.get("success") else "failed",
                    comment=orch_result.get("summary",
                        orch_result.get("result", {}).get("message", "")),
                    session_id=self.session_id,
                    result=orch_result,
                )
                self._record_result(result)
                return result
            except Exception as e:
                self.log(f"编排代理执行失败: {e}")

        # ---- 路径 2: TRAE Control 回退 ----
        try:
            from trae_control import get_tra_e_agent
            trae = get_tra_e_agent()
            self.log("使用 TRAE Control 直接执行 (回退)")

            result = trae.handle_task({
                "type": "trae_command",
                "command": task_text,
            })

            final = format_daemon_result(
                status="completed" if result.get("success") else "failed",
                comment=result.get("result", result.get("output", str(result))),
                session_id=self.session_id,
                result=result,
            )
            self._record_result(final)
            return final
        except ImportError as e:
            self.log(f"TRAE Control 导入失败: {e}")

        # ---- 路径 3: IDE Bridge 直接调用 (最终回退) ----
        try:
            from trae_ide_bridge import get_bridge
            bridge = get_bridge()
            status = bridge.get_status()
            self.log(f"TRAE IDE Bridge: {status['status']}")

            if status["status"] == "running":
                bridge.focus_ide()
                final = format_daemon_result(
                    status="completed",
                    comment=f"TRAE IDE 已聚焦，等待指令: {task_text[:200]}",
                    session_id=self.session_id,
                    result={"bridge_status": status},
                )
            else:
                final = format_daemon_result(
                    status="blocked",
                    comment=f"TRAE IDE 未运行 ({status['status']})，请先启动 TRAE IDE",
                    session_id=self.session_id,
                    result={"bridge_status": status},
                )
            self._record_result(final)
            return final
        except ImportError as e:
            self.log(f"TRAE IDE Bridge 导入失败: {e}")
        except Exception as e:
            self.log(f"Bridge 调用失败: {e}")

        # ---- 路径 4: 完全不可用 ----
        final = format_daemon_result(
            status="failed",
            comment="所有执行路径不可用: 编排代理、TRAE Control、IDE Bridge 均无法加载",
            session_id=self.session_id,
            result={"error": "no_execution_path_available"},
        )
        self._record_result(final)
        return final

    def _record_result(self, result: dict):
        """记录执行结果到会话记忆"""
        if self.memory:
            success = result.get("status") == "completed"
            summary = result.get("comment", "")[:500]
            self.memory.add_result(self.session_id, success, summary,
                                   {"status": result.get("status"),
                                    "result": result.get("result", {})})


# ============================================================
# CLI 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="编排代理入口 — 通过 Claude 编排器执行任务"
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        help="任务描述文本"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="输出详细日志到 stderr"
    )
    parser.add_argument(
        "--json-input",
        action="store_true",
        help="从 stdin 读取 JSON 格式的任务"
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="输出格式 (默认: json)"
    )

    args = parser.parse_args()

    task_text = ""
    context = {}

    # 模式 1: 从 stdin 读取 JSON
    if args.json_input or (not args.task and not sys.stdin.isatty()):
        try:
            raw = sys.stdin.read()
            if raw.strip():
                data = json.loads(raw)
                task_text = data.get("task", data.get("command", data.get("message", "")))
                context = data.get("context", {})
                # 提取 session_id 等元信息
                if data.get("session_id"):
                    pass  # 由 runner 管理
        except json.JSONDecodeError:
            # 非 JSON stdin → 作为纯文本任务
            task_text = raw.strip()
        except Exception:
            pass

    # 模式 2: CLI 参数
    if args.task:
        task_text = args.task

    if not task_text:
        print(json.dumps(format_daemon_result(
            "failed", "未提供任务文本 (--task 或 stdin)"
        )))
        sys.exit(1)

    # 执行
    runner = OrchestratedAgentRunner(verbose=args.verbose)
    result = runner.execute(task_text, context)

    # 输出
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Status:   {result['status']}")
        print(f"Session:  {result['session_id']}")
        print(f"Comment:  {result['comment'][:200]}")
        if result.get("result"):
            inner = result["result"]
            print(f"Intent:   {inner.get('intent', 'N/A')}")
            print(f"Agent:    {inner.get('agent', 'N/A')}")

    # 退出码
    if result["status"] == "failed":
        sys.exit(1)
    elif result["status"] == "blocked":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
