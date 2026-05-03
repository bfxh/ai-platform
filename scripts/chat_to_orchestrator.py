#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat-to-Orchestrator 直接桥 — 无需 Daemon 即可测试端到端编排流程

模拟 Multica 聊天 → Claude 编排 → TRAE IDE 执行的完整数据流。

用法:
    # 交互模式
    python scripts/chat_to_orchestrator.py

    # 单次执行
    python scripts/chat_to_orchestrator.py "创建 React 登录页面"

    # 不带 TRAE IDE 的纯分析模式
    python scripts/chat_to_orchestrator.py --dry-run "分析 dispatcher.py"

    # 批量测试所有路由规则
    python scripts/chat_to_orchestrator.py --test-rules

    # 指定工作目录
    python scripts/chat_to_orchestrator.py --work-dir D:/projects/myapp "创建文件"
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

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

# 会话记忆
try:
    from session_memory import get_memory
    _MEMORY_AVAILABLE = True
except ImportError:
    _MEMORY_AVAILABLE = False
    get_memory = None


# ============================================================
# 颜色输出
# ============================================================

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"


def print_step(n: int, desc: str):
    print(f"\n{c(f'[{n}]', Colors.CYAN)} {desc}")


def print_intent(intent: str, agent: str):
    print(f"  {c('Intent:', Colors.YELLOW)} {intent}")
    print(f"  {c('Agent:', Colors.YELLOW)}  {agent}")


def print_result(success: bool, summary: str):
    icon = c("OK", Colors.GREEN) if success else c("FAILED", Colors.RED)
    print(f"  {c('Result:', Colors.YELLOW)} {icon} {summary[:200]}")


# ============================================================
# 桥接逻辑
# ============================================================

class ChatOrchestratorBridge:
    """聊天 → 编排器直接桥"""

    def __init__(self, dry_run: bool = False, work_dir: str = None,
                 resume_session: str = None):
        self.dry_run = dry_run
        self.work_dir = work_dir or str(_BASE_DIR)
        self._orch = None
        self._bridge = None
        self._trae = None
        # 会话记忆
        self._memory = None
        self._session_id = None
        if _MEMORY_AVAILABLE:
            try:
                self._memory = get_memory()
            except Exception:
                pass
        if resume_session and self._memory:
            loaded = self._memory.load_session(resume_session)
            if loaded:
                self._session_id = resume_session
                print(f"  {c('续接会话:', Colors.CYAN)} {resume_session}")
                print(f"  {c('历史:', Colors.CYAN)} "
                      f"{loaded.get('message_count', 0)} 条消息, "
                      f"{loaded.get('result_count', 0)} 次任务")
        if not self._session_id and self._memory:
            self._session_id = self._memory.create_session(
                agent="chat_bridge", task="聊天桥接会话"
            )

    @property
    def orchestrator(self):
        if self._orch is None:
            try:
                from claude_orch.claude_orchestrator import get_orchestrator
                self._orch = get_orchestrator()
            except Exception:
                pass
        return self._orch

    @property
    def bridge(self):
        if self._bridge is None:
            try:
                from trae_ide_bridge import get_bridge
                self._bridge = get_bridge()
            except Exception:
                pass
        return self._bridge

    @property
    def trae_agent(self):
        if self._trae is None:
            try:
                from trae_control import get_tra_e_agent
                self._trae = get_tra_e_agent()
            except Exception:
                pass
        return self._trae

    def send_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """模拟聊天消息发送 → 编排流程

        返回完整的执行报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "mode": "dry_run" if self.dry_run else "live",
            "steps": [],
        }

        # 记录用户消息到会话记忆
        if self._memory and self._session_id:
            self._memory.add_message(self._session_id, "user", message)

        # ---- Step 1: 意图分析 ----
        intent = None
        target_agent = None

        if self.orchestrator and self.orchestrator._initialized:
            t0 = time.time()
            intent = self.orchestrator._analyze_intent(message)
            target_agent = self.orchestrator._route_intent(intent)
            elapsed = time.time() - t0
            report["steps"].append({
                "step": "intent_analysis",
                "intent": intent,
                "agent": target_agent,
                "duration_ms": int(elapsed * 1000),
                "success": bool(intent),
            })
            print_step(1, f"意图分析 ({elapsed:.2f}s)")
            print_intent(intent, target_agent)
        else:
            report["steps"].append({
                "step": "intent_analysis",
                "success": False,
                "error": "编排代理不可用",
            })
            print_step(1, f"意图分析 {c('(编排代理不可用)', Colors.YELLOW)}")

        # ---- Step 2: 环境检查 ----
        ide_status = None
        if self.bridge:
            ide_status = self.bridge.get_status()
            report["steps"].append({
                "step": "env_check",
                "ide_status": ide_status["status"],
                "success": True,
            })
            status_color = Colors.GREEN if ide_status["status"] == "running" else Colors.YELLOW
            print_step(2, f"TRAE IDE 状态: {c(ide_status['status'], status_color)}")
        else:
            report["steps"].append({
                "step": "env_check",
                "success": False,
                "error": "Bridge 不可用",
            })
            print_step(2, f"TRAE IDE: {c('Bridge 不可用', Colors.RED)}")

        # ---- Step 3: 执行 (或 dry-run) ----
        if self.dry_run:
            print_step(3, f"执行 {c('(DRY-RUN 跳过)', Colors.YELLOW)}")
            report["steps"].append({
                "step": "execute",
                "mode": "dry_run",
                "success": True,
            })
            report["status"] = "dry_run_completed"
            return report

        print_step(3, "执行任务...")
        t0 = time.time()

        exec_result = self._execute_task(message, intent, target_agent)

        elapsed = time.time() - t0
        report["steps"].append({
            "step": "execute",
            "duration_ms": int(elapsed * 1000),
            "success": exec_result.get("success", False),
            "result": exec_result,
        })
        print_result(exec_result.get("success", False),
                     exec_result.get("message", exec_result.get("error", "")))

        # ---- Step 4: 汇总 ----
        print_step(4, "汇总")
        print(f"  {c('总耗时:', Colors.CYAN)} {elapsed:.2f}s")
        print(f"  {c('状态:', Colors.CYAN)} "
              f"{c('成功', Colors.GREEN) if exec_result.get('success') else c('失败', Colors.RED)}")

        report["status"] = "completed" if exec_result.get("success") else "failed"
        report["result"] = exec_result

        # 记录结果到会话记忆
        if self._memory and self._session_id:
            summary = exec_result.get("message", exec_result.get("error", ""))
            self._memory.add_result(
                self._session_id,
                exec_result.get("success", False),
                summary,
                detail={"intent": intent, "agent": target_agent}
            )
            # 同时记录意图分析
            if intent:
                self._memory.add_message(self._session_id, "agent",
                                         f"意图: {intent} → 代理: {target_agent}")

        return report

    def _execute_task(self, message: str, intent: str,
                      target_agent: str) -> Dict[str, Any]:
        """执行任务 — 根据目标代理分发"""

        # 尝试通过编排器完整执行
        if self.orchestrator and self.orchestrator._initialized:
            try:
                result = self.orchestrator.execute({
                    "task": message,
                    "task_type": "orchestrate",
                })
                return {
                    "success": result.get("success", False),
                    "method": "orchestrator",
                    "message": result.get("summary", result.get("result", {}).get("message", "")),
                    "detail": result,
                }
            except Exception as e:
                print(f"  {c('编排器执行失败:', Colors.YELLOW)} {e}")

        # 回退: TRAE Control 代理
        if self.trae_agent:
            try:
                result = self.trae_agent.handle_task({
                    "type": "trae_command",
                    "command": message,
                })
                return {
                    "success": result.get("success", False),
                    "method": "trae_control",
                    "message": result.get("result", result.get("output", "")),
                    "detail": result,
                }
            except Exception as e:
                print(f"  {c('TRAE Control 失败:', Colors.YELLOW)} {e}")

        # 最终回退
        return {
            "success": False,
            "method": "none",
            "message": "没有可用的执行路径",
            "error": "所有代理不可用",
        }

    def test_rules(self) -> List[Dict[str, Any]]:
        """批量测试所有路由规则"""
        test_cases = [
            "创建 React 登录组件，包含用户名密码输入框",
            "修改 dispatcher.py 中的 _dispatch_agent 方法",
            "分析 /python/core/dispatcher.py 的代码质量",
            "读取 README.md 文件内容",
            "执行 npm install 安装依赖",
            "搜索 Python asyncio 最佳实践",
            "截取当前 IDE 窗口的截图",
        ]

        results = []
        print(f"\n{c('=== 路由规则测试 ===', Colors.BOLD)}")
        print()

        for msg in test_cases:
            print(f"  {c('>', Colors.CYAN)} {msg[:70]}...")

            if self.orchestrator and self.orchestrator._initialized:
                intent = self.orchestrator._analyze_intent(msg)
                agent = self.orchestrator._route_intent(intent)
                print(f"    {c('intent:', Colors.YELLOW)} {intent:<25} "
                      f"{c('→', Colors.BLUE)} {agent}")
                results.append({
                    "message": msg[:70],
                    "intent": intent,
                    "agent": agent,
                    "success": bool(intent),
                })
            else:
                print(f"    {c('编排代理不可用', Colors.RED)}")
                results.append({
                    "message": msg[:70],
                    "success": False,
                    "error": "编排代理不可用",
                })

        # 统计
        unique_intents = set(r.get("intent") for r in results if r.get("intent"))
        print(f"\n  {c('覆盖意图:', Colors.CYAN)} {len(unique_intents)} 种")
        print(f"  {c('成功率:', Colors.CYAN)} "
              f"{sum(1 for r in results if r.get('success'))}/{len(results)}")

        return results


# ============================================================
# 交互模式
# ============================================================

def interactive_mode(bridge: ChatOrchestratorBridge):
    """交互式聊天模式"""
    print(f"\n{c('Multica Chat → Orchestrator 交互模式', Colors.BOLD)}")
    print(f"模式: {c('DRY-RUN' if bridge.dry_run else 'LIVE', Colors.YELLOW)}")
    print(f"工作目录: {bridge.work_dir}")
    print()
    print("输入任务描述来测试编排流程，输入 'quit' 退出，'test' 测试路由。")
    print()

    while True:
        try:
            user_input = input(f"{c('Chat >', Colors.CYAN)} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n退出")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("退出")
            break

        if user_input.lower() in ("test", "test-rules"):
            bridge.test_rules()
            continue

        # 执行
        report = bridge.send_message(user_input)

        # 如果是 live 模式且有详细结果，打印子代理输出
        if not bridge.dry_run:
            detail = report.get("result", {}).get("detail", {})
            if detail.get("result"):
                inner = detail["result"]
                output = inner.get("output", inner.get("result", ""))
                if output:
                    print(f"\n  {c('--- 输出 ---', Colors.BLUE)}")
                    print(f"  {output[:500]}")
                    if len(str(output)) > 500:
                        print(f"  ...({len(str(output))} 字符，已截断)")
                    print(f"  {c('-------------', Colors.BLUE)}")


# ============================================================
# 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Chat-to-Orchestrator 直接桥 — 无需 Daemon 的端到端测试"
    )
    parser.add_argument(
        "message", nargs="?",
        help="单条任务消息"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="仅分析意图+路由，不实际执行"
    )
    parser.add_argument(
        "--test-rules", "-t",
        action="store_true",
        help="批量测试所有路由规则"
    )
    parser.add_argument(
        "--work-dir", "-w",
        type=str,
        help="指定工作目录"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="以 JSON 格式输出结果"
    )
    parser.add_argument(
        "--resume", "-r",
        type=str,
        help="续接指定会话 ID"
    )
    parser.add_argument(
        "--list-sessions", "-l",
        action="store_true",
        help="列出最近的会话记录"
    )

    args = parser.parse_args()

    # 模式 0: 列出会话
    if args.list_sessions:
        if _MEMORY_AVAILABLE:
            mem = get_memory()
            sessions = mem.list_sessions(limit=20)
            print(f"\n{c('=== 最近会话 ===', Colors.BOLD)}")
            print()
            for s in sessions:
                status_icon = {"active": "●", "completed": "○", "archived": "◇"}.get(
                    s.get("status", ""), "?"
                )
                print(f"  {c(status_icon, Colors.GREEN)} "
                      f"{c(s['session_id'], Colors.CYAN)} "
                      f"[{s.get('agent', '?')}] "
                      f"{s.get('task', '')[:60]}")
                print(f"    消息: {s.get('message_count', 0)} | "
                      f"结果: {s.get('result_count', 0)} | "
                      f"更新: {s.get('updated_at', '')[:19]}")
            print(f"\n  {c('统计:', Colors.CYAN)}")
            stats = mem.get_stats()
            print(f"  活跃: {stats['active_sessions']}, "
                  f"大小: {stats['total_size_mb']} MB")
        else:
            print(f"{c('会话记忆不可用', Colors.RED)}")
        return

    bridge = ChatOrchestratorBridge(
        dry_run=args.dry_run,
        work_dir=args.work_dir,
        resume_session=args.resume,
    )

    # 模式 1: 路由规则测试
    if args.test_rules:
        results = bridge.test_rules()
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    # 模式 2: 单次执行
    if args.message:
        report = bridge.send_message(args.message)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    # 模式 3: 交互模式
    interactive_mode(bridge)


if __name__ == "__main__":
    main()
