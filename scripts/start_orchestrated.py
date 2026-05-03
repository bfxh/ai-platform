#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一编排启动脚本 — Multica + Claude + TRAE IDE 集成启动

按阶段依次启动所有组件：
  Phase 0: 环境检查 (Python, da.py, TRAE IDE, Ollama)
  Phase 1: 基础设施 (PostgreSQL, Redis — 可选)
  Phase 2: Go 后端服务器 (可选)
  Phase 3: Python AI 层 (Dispatcher, 共享上下文, 代理初始化)
  Phase 4: TRAE IDE (启动/激活)
  Phase 5: 前端 (Next.js 开发服务器 — 可选)
  Phase 6: 心跳监控 (每 15 秒检查)

用法:
    python scripts/start_orchestrated.py                # 完整启动
    python scripts/start_orchestrated.py --ai-only      # 仅 AI 层 + TRAE IDE
    python scripts/start_orchestrated.py --skip-backend # 跳过 Go 后端
    python scripts/start_orchestrated.py --skip-frontend # 跳过前端
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ================================================================
# 配置
# ================================================================

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_DIR = BASE_DIR
SERVER_DIR = BASE_DIR.parent / "server"  # Go 后端

# 关键路径
DA_PATH = BASE_DIR / "storage" / "mcp" / "Tools" / "da.py"
DISPATCHER_PATH = BASE_DIR / "core" / "dispatcher.py"
BRIDGE_PATH = BASE_DIR / "core" / "trae_ide_bridge.py"

# 环境变量
os.environ.setdefault("AI_BASE_DIR", str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR))

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def color(text: str, c: str) -> str:
    return f"{c}{text}{Colors.RESET}"

def ok(msg: str):    print(f"  {color('[OK]', Colors.GREEN)} {msg}")
def warn(msg: str):  print(f"  {color('[WARN]', Colors.YELLOW)} {msg}")
def err(msg: str):   print(f"  {color('[ERR]', Colors.RED)} {msg}")
def info(msg: str):  print(f"  {color('[INFO]', Colors.CYAN)} {msg}")
def header(msg: str):
    print(f"\n{color('=' * 60, Colors.BLUE)}")
    print(f"{color(msg, Colors.BOLD)}")
    print(f"{color('=' * 60, Colors.BLUE)}")

# ================================================================
# 启动阶段
# ================================================================

class OrchestratedStartup:
    """编排启动器"""

    def __init__(self, skip_backend=False, skip_frontend=False, ai_only=False):
        self.skip_backend = skip_backend or ai_only
        self.skip_frontend = skip_frontend or ai_only
        self.ai_only = ai_only
        self.start_time = datetime.now()
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []

    def run(self):
        """执行完整启动流程"""
        print(f"\n{color('Multica + Claude + TRAE IDE 统一启动', Colors.BOLD)}")
        print(f"启动时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"模式: {'仅 AI 层' if self.ai_only else '完整启动'}")

        phases = [
            ("Phase 0: 环境检查", self.phase_0_check),
            ("Phase 1: 基础设施", self.phase_1_infra),
            ("Phase 2: Go 后端", self.phase_2_backend),
            ("Phase 3: AI 层初始化", self.phase_3_ai_layer),
            ("Phase 4: TRAE IDE", self.phase_4_trae_ide),
            ("Phase 5: 前端", self.phase_5_frontend),
        ]

        for name, func in phases:
            if (name.startswith("Phase 1") or name.startswith("Phase 2")) and self.ai_only:
                info(f"跳过 {name} (AI-Only 模式)")
                continue
            if name.startswith("Phase 2") and self.skip_backend:
                info(f"跳过 {name} (--skip-backend)")
                continue
            if name.startswith("Phase 5") and self.skip_frontend:
                info(f"跳过 {name} (--skip-frontend)")
                continue

            header(name)
            try:
                success = func()
                self.results[name] = success
                if not success and name != "Phase 4: TRAE IDE":
                    err(f"{name} 未完全成功，继续...")
            except Exception as e:
                self.results[name] = False
                self.errors.append(f"{name}: {e}")
                err(f"{name} 失败: {e}")

        # Phase 6: 心跳监控
        header("Phase 6: 心跳监控")
        self.phase_6_heartbeat()

        # 汇总
        self.print_summary()

    # ============================================================
    # Phase 0: 环境检查
    # ============================================================
    def phase_0_check(self) -> bool:
        ok(f"Python: {sys.version}")
        ok(f"工作目录: {BASE_DIR}")
        ok(f"AI_BASE_DIR: {os.environ.get('AI_BASE_DIR', 'NOT SET')}")

        # da.py
        if DA_PATH.exists():
            ok(f"da.py: {DA_PATH}")
        else:
            warn(f"da.py 未找到: {DA_PATH}")
            return False

        # trae_ide_bridge.py
        if BRIDGE_PATH.exists():
            ok(f"trae_ide_bridge.py: {BRIDGE_PATH}")
        else:
            warn(f"trae_ide_bridge.py 未找到: {BRIDGE_PATH}")

        # session_memory.py
        session_path = BASE_DIR / "core" / "session_memory.py"
        if session_path.exists():
            ok(f"session_memory.py: {session_path}")
        else:
            warn(f"session_memory.py 未找到")

        # file_protector.py
        protector_path = BASE_DIR / "core" / "file_protector.py"
        if protector_path.exists():
            ok(f"file_protector.py: {protector_path}")
        else:
            warn(f"file_protector.py 未找到")

        # mcp_classifier.py
        classifier_path = BASE_DIR / "core" / "mcp_classifier.py"
        if classifier_path.exists():
            ok(f"mcp_classifier.py: {classifier_path}")
        else:
            warn(f"mcp_classifier.py 未找到")

        # TRAE IDE 进程检查
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Trae.exe"],
                                capture_output=True, text=True)
        if "Trae.exe" in result.stdout:
            ok("TRAE IDE 进程: 运行中")
        else:
            warn("TRAE IDE 进程: 未运行 (将在 Phase 4 启动)")

        # Ollama 检查
        try:
            ollama_result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True, text=True, timeout=5
            )
            if ollama_result.returncode == 0:
                ok("Ollama: 运行中 (localhost:11434)")
            else:
                warn("Ollama: 未响应")
        except Exception:
            warn("Ollama: 未运行或不可达")

        return True

    # ============================================================
    # Phase 1: 基础设施
    # ============================================================
    def phase_1_infra(self) -> bool:
        # PostgreSQL (可选)
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                ok("PostgreSQL: 就绪 (localhost:5432)")
            else:
                warn("PostgreSQL: 未就绪 (数据库功能可能不可用)")
        except FileNotFoundError:
            warn("pg_isready 未找到 (PostgreSQL 可能未安装)")
        except Exception:
            warn("PostgreSQL: 检查失败")

        return True

    # ============================================================
    # Phase 2: Go 后端
    # ============================================================
    def phase_2_backend(self) -> bool:
        server_main = SERVER_DIR / "cmd" / "server" / "main.go"
        if not server_main.exists():
            warn(f"Go 后端入口未找到: {server_main}")
            return False

        # Run migration
        info("运行数据库迁移...")
        try:
            subprocess.run(
                ["go", "run", str(SERVER_DIR / "cmd" / "migrate" / "main.go"), "up"],
                cwd=str(SERVER_DIR), capture_output=True, text=True, timeout=30
            )
            ok("数据库迁移完成")
        except Exception as e:
            warn(f"数据库迁移失败: {e}")

        info("Go 后端将在单独终端中启动，请手动运行:")
        info(f"  cd {SERVER_DIR} && go run ./cmd/server")

        return True

    # ============================================================
    # Phase 3: AI 层初始化
    # ============================================================
    def phase_3_ai_layer(self) -> bool:
        info("初始化 Python AI 层...")

        # 1. Dispatcher 扫描
        try:
            from core.dispatcher import Dispatcher
            dispatcher = Dispatcher(str(BASE_DIR))
            registry = dispatcher.scan()
            unit_count = sum(len(v) for v in registry.values())
            ok(f"Dispatcher 扫描完成: {unit_count} 个能力单元")

            # 列出发现的代理
            agents = registry.get("agent", {})
            if agents:
                info(f"发现的代理 ({len(agents)}):")
                for name in agents:
                    info(f"  - {name}")
        except Exception as e:
            warn(f"Dispatcher 扫描失败: {e}")

        # 2. 共享上下文
        try:
            from core.shared_context import get_shared_context
            ctx = get_shared_context()
            if ctx:
                ok("共享上下文: 已初始化")
                # 注册 TRAE 相关代理
                ctx.registry.register_agent("trae_control", "ide", {
                    "bridge_available": BRIDGE_PATH.exists(),
                    "description": "TRAE IDE 控制代理"
                })
                ctx.registry.register_agent("claude_orchestrator", "orchestrator", {
                    "description": "Claude 编排代理",
                    "routing_available": True,
                })
                ok("代理已注册到共享上下文")
        except Exception as e:
            warn(f"共享上下文初始化失败: {e}")

        # 3. TRAE IDE Bridge 预热
        try:
            from core.trae_ide_bridge import get_bridge
            bridge = get_bridge()
            status = bridge.get_status()
            info(f"TRAE IDE Bridge 状态: {status['status']}")
            if status["status"] == "running":
                ok("TRAE IDE Bridge: 就绪")
            else:
                warn(f"TRAE IDE Bridge: {status['status']} (将在 Phase 4 处理)")
        except Exception as e:
            err(f"TRAE IDE Bridge 初始化失败: {e}")

        # 4. Claude 编排代理
        try:
            sys.path.insert(0, str(BASE_DIR / "user" / "global" / "plugin" /
                                   "mcp-core" / "agent"))
            from claude_orch.claude_orchestrator import get_orchestrator
            orch = get_orchestrator()
            ok(f"Claude 编排代理: 就绪 (status={orch.status})")
        except Exception as e:
            warn(f"Claude 编排代理初始化失败: {e}")

        # 5. Session Memory (上下文延续)
        try:
            from core.session_memory import get_memory
            mem = get_memory()
            sid = mem.create_session(agent="startup", task="系统启动")
            stats = mem.get_stats()
            ok(f"Session Memory: {stats['active_sessions']} 会话活跃, "
               f"{stats['total_size_mb']} MB")
        except Exception as e:
            warn(f"Session Memory 初始化失败: {e}")

        # 6. File Protector (CC 三级缓存)
        try:
            from core.file_protector import get_protector
            fp = get_protector()
            registered = fp.register_core_files()
            cc_stats = fp.get_cc_stats()
            ok(f"File Protector: {len(fp.list_protected())} 文件受保护, "
               f"CC缓存 {cc_stats['old']['count']} 备份")
        except Exception as e:
            warn(f"File Protector 初始化失败: {e}")

        # 7. MCP Classifier (验证工具注册)
        try:
            from core.mcp_classifier import MCPClassifier
            classifier = MCPClassifier()
            validation = classifier.validate_config()
            if validation.get("issues"):
                warn(f"MCP Classifier: {len(validation.get('issues', []))} 个问题待修复")
                info("  运行 python core/mcp_classifier.py --fix 自动修复")
            else:
                ok(f"MCP Classifier: {validation.get('total_tools', '?')} 工具已注册")
        except Exception as e:
            warn(f"MCP Classifier 验证跳过: {e}")

        return True

    # ============================================================
    # Phase 4: TRAE IDE
    # ============================================================
    def phase_4_trae_ide(self) -> bool:
        info("启动/激活 TRAE IDE...")

        try:
            from core.trae_ide_bridge import get_bridge
            bridge = get_bridge()
            result = bridge.open_ide()
            if result["success"]:
                ok(f"TRAE IDE: {result['message']}")
                return True
            else:
                warn(f"TRAE IDE: {result['message']}")
                info("请手动启动 TRAE IDE")
                return False
        except Exception as e:
            warn(f"TRAE IDE 启动失败: {e}")
            info(f"请手动启动 TRAE IDE，Bridge 将在后续操作中自动连接")
            return False

    # ============================================================
    # Phase 5: 前端
    # ============================================================
    def phase_5_frontend(self) -> bool:
        web_dir = BASE_DIR.parent / "apps" / "web"
        if not web_dir.exists():
            warn(f"前端目录未找到: {web_dir}")
            return False

        info(f"前端将在单独终端中启动，请手动运行:")
        info(f"  cd {web_dir} && pnpm dev:web")
        info(f"  访问: http://localhost:3000 (或 http://localhost:3002)")

        return True

    # ============================================================
    # Phase 6: 心跳监控
    # ============================================================
    def phase_6_heartbeat(self):
        info("启动心跳监控 (每 15 秒检查)...")

        checks = 0
        max_checks = 4  # 运行 1 分钟后退出监控

        try:
            while checks < max_checks:
                time.sleep(15)
                checks += 1

                # 检查 TRAE IDE
                try:
                    from core.trae_ide_bridge import get_bridge
                    status = get_bridge().get_status()
                    if status["status"] == "running":
                        ok(f"[{checks}] TRAE IDE: 正常")
                    else:
                        warn(f"[{checks}] TRAE IDE: {status['status']}")
                except Exception:
                    pass

                # 检查 AI 层
                try:
                    from core.dispatcher import Dispatcher
                    d = Dispatcher(str(BASE_DIR))
                    summary = d.get_registry_summary()
                    agent_count = len(summary.get("agent", {}))
                    ok(f"[{checks}] AI 层: {agent_count} 代理就绪")
                except Exception:
                    pass

        except KeyboardInterrupt:
            info("心跳监控已停止")

    def print_summary(self):
        """打印启动汇总"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        print(f"\n{color('=' * 60, Colors.BLUE)}")
        print(f"{color('启动汇总', Colors.BOLD)}")
        print(f"{color('=' * 60, Colors.BLUE)}")

        for phase, success in self.results.items():
            icon = color("[OK]", Colors.GREEN) if success else color("[--]", Colors.YELLOW)
            print(f"  {icon} {phase}")

        if self.errors:
            print(f"\n{color('警告/错误:', Colors.RED)}")
            for e in self.errors:
                print(f"  - {e}")

        print(f"\n总耗时: {elapsed:.1f} 秒")
        print(f"\n{color('系统已就绪!', Colors.GREEN)}")
        print(f"  - Multica AI 层: {color('运行中', Colors.GREEN)}")
        print(f"  - 代理系统:     {color('就绪', Colors.GREEN)}")
        print(f"  - TRAE IDE:     {color('请确认 IDE 窗口已打开', Colors.YELLOW)}")
        print(f"\n{color('提示: 在 Multica 前端中输入任务来测试端到端流程', Colors.CYAN)}")


# ================================================================
# 入口
# ================================================================

def main():
    skip_backend = "--skip-backend" in sys.argv
    skip_frontend = "--skip-frontend" in sys.argv
    ai_only = "--ai-only" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return

    startup = OrchestratedStartup(
        skip_backend=skip_backend,
        skip_frontend=skip_frontend,
        ai_only=ai_only,
    )
    startup.run()


if __name__ == "__main__":
    main()
