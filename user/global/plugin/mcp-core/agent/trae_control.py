#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - TRAE IDE 控制智能体

功能:
- 通过 TRAE IDE Bridge (da.py 桌面自动化) 操控 TRAE IDE
- 执行文件操作（读/写/搜索）
- 运行终端命令
- 搜索Web内容
- 执行顺序思考

底层依赖:
    core/trae_ide_bridge.py  ←→  da.py (Windows GUI 自动化)

用法:
    from agent.trae_control import TRAEControlAgent, get_tra_e_agent

    trae_agent = get_tra_e_agent()  # 自动初始化 + 连接 IDE Bridge
    result = trae_agent.handle_task({"type": "write_file", "file_path": "test.py", "content": "..."})
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
# 导入技能系统
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.base import Skill, get_registry
from config_manager import get_config_manager
# 导入大模型集成
from agent.llm_integration import LLMIntegrator, LLMAgentEnhancer
# 导入数据库集成
from agent.database_integration import get_database_manager

# 导入 TRAE IDE Bridge (核心依赖)
_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_BASE_DIR / "core"))
try:
    from trae_ide_bridge import TRAEIDEBridge, get_bridge
    _BRIDGE_AVAILABLE = True
except ImportError:
    _BRIDGE_AVAILABLE = False
    print("[WARN] trae_ide_bridge.py 未找到，将使用文件系统回退")

# 导入会话记忆 (上下文延续)
try:
    from session_memory import SessionMemory, get_memory
    _MEMORY_AVAILABLE = True
except ImportError:
    _MEMORY_AVAILABLE = False
    SessionMemory = None
    get_memory = None

# 导入文件保护 (CC 三级缓存 + 安全写入)
try:
    from file_protector import FileProtector, get_protector
    _PROTECTOR_AVAILABLE = True
except ImportError:
    _PROTECTOR_AVAILABLE = False
    FileProtector = None
    get_protector = None

# 配置日志
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(str(log_dir / "trae_control.log")), logging.StreamHandler()],
)


class TRAEControlAgent:
    """TRAE IDE 控制智能体 — 通过 Bridge 操控 TRAE IDE"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or {}
        self.status: str = "DISABLED"
        self._initialized: bool = False
        self._last_error: Optional[str] = None
        # 初始化日志
        self.logger = logging.getLogger("TRAEControlAgent")
        # 初始化配置管理器
        self.config_manager = get_config_manager()
        # 初始化技能注册中心
        self.skill_registry = get_registry()
        # 初始化大模型集成
        self.llm_integrator = LLMIntegrator()
        self.llm_enhancer = LLMAgentEnhancer(self.llm_integrator)
        # 初始化数据库管理器
        self.db_manager = get_database_manager()
        # TRAE IDE Bridge（核心依赖，延迟初始化）
        self._bridge: Optional[Any] = None
        # 会话记忆（上下文延续）
        self._memory: Optional[Any] = None
        self._session_id: Optional[str] = None
        if _MEMORY_AVAILABLE:
            try:
                self._memory = get_memory()
                self._session_id = self._memory.create_session(
                    agent="trae_control", task="TRAE IDE 控制会话"
                )
                self.logger.info(f"会话记忆已初始化: {self._session_id}")
            except Exception as e:
                self.logger.warning(f"会话记忆初始化失败: {e}")
        # 文件保护（CC 三级缓存 + 安全写入）
        self._protector: Optional[Any] = None
        if _PROTECTOR_AVAILABLE:
            try:
                self._protector = get_protector()
                self.logger.info("文件保护已初始化")
            except Exception as e:
                self.logger.warning(f"文件保护初始化失败: {e}")
        # 加载智能体配置
        self._load_config()
        # 从数据库加载智能体状态
        self._load_from_database()

    @property
    def bridge(self) -> Optional[Any]:
        """获取 TRAE IDE Bridge 实例（延迟初始化）"""
        if self._bridge is None and _BRIDGE_AVAILABLE:
            try:
                self._bridge = TRAEIDEBridge()
                self.logger.info("TRAE IDE Bridge 已连接")
            except Exception as e:
                self.logger.warning(f"TRAE IDE Bridge 初始化失败: {e}")
                self._bridge = None
        return self._bridge

    def _load_config(self) -> None:
        config_name = "trae_control"
        agent_config = self.config_manager.load_config(config_name)
        if agent_config:
            self.config.update(agent_config)
            self.logger.info(f"加载智能体配置: {config_name}")

    def _load_from_database(self) -> None:
        agent_data = self.db_manager.get_agent("trae_control")
        if agent_data:
            self.logger.info("从数据库加载智能体状态: trae_control")

    def _save_to_database(self) -> None:
        self.db_manager.save_agent({
            "name": "trae_control",
            "description": "TRAE IDE 控制智能体",
            "version": "2.0.0",
            "agent_type": "control",
            "level": 1, "experience": 0, "wins": 0, "losses": 0,
            "abilities": {"trae_control": 100, "file_operations": 90, "terminal_commands": 90},
            "skills": ["filesystem", "terminal", "git", "ide_bridge"]
        })

    def initialize(self) -> bool:
        if self._initialized:
            return True
        try:
            self.status = "INITIALIZING"
            self.logger.info("初始化 TRAE 控制智能体")
            self._init_mcp_connections()
            self.status = "READY"
            self._initialized = True
            self.logger.info("TRAE 控制智能体初始化成功")
            self._save_to_database()
            return True
        except Exception as e:
            self._last_error = str(e)
            self.status = "ERROR"
            self.logger.error(f"初始化失败: {e}")
            return False

    def _init_mcp_connections(self) -> None:
        """初始化 TRAE IDE Bridge 连接（替代原 MCP 桩调用）"""
        self.logger.info("初始化 TRAE IDE Bridge 连接...")
        if self.bridge:
            try:
                status = self.bridge.get_status()
                self.logger.info(f"TRAE IDE 状态: {status['status']}")
                if status["status"] == "not_found":
                    self.logger.warning("TRAE IDE 未运行，将在首次操作时自动启动")
            except Exception as e:
                self.logger.warning(f"TRAE IDE 状态检查失败: {e}")
        else:
            self.logger.warning("TRAE IDE Bridge 不可用，将使用文件系统回退")

    # ================================================================
    # 核心操作 — IDE Bridge 优先 + 文件系统回退
    # ================================================================

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """读取文件（IDE Bridge 优先 → 文件系统回退）"""
        try:
            self.logger.info(f"读取文件: {file_path}")
            abs_path = Path(file_path)
            if not abs_path.is_absolute():
                abs_path = Path(os.getcwd()) / file_path

            if self.bridge:
                result = self.bridge.read_file(str(abs_path))
                if result["success"]:
                    return {"success": True, "content": result.get("content", "")}

            if abs_path.exists():
                content = abs_path.read_text(encoding="utf-8")
                return {"success": True, "content": content}
            return {"success": False, "error": f"文件不存在: {file_path}"}
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入文件（IDE Bridge 优先 → 文件系统回退，受保护文件自动备份）"""
        try:
            self.logger.info(f"写入文件: {file_path} ({len(content)} 字符)")

            if self.bridge:
                result = self.bridge.write_code(file_path, content)
                if result["success"]:
                    return {"success": True, "result": result.get("message", "已写入 IDE")}

            abs_path = Path(file_path)
            if not abs_path.is_absolute():
                abs_path = Path(os.getcwd()) / file_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)

            # 使用文件保护器进行安全写入（自动备份受保护文件）
            try:
                rel_path = str(abs_path.relative_to(_BASE_DIR)).replace("\\", "/")
            except ValueError:
                rel_path = str(abs_path).replace("\\", "/")

            if self._protector and self._protector.is_protected(rel_path):
                self._protector.safe_write(rel_path, content)
                self.logger.info(f"受保护文件已安全写入: {rel_path}")
            else:
                abs_path.write_text(content, encoding="utf-8")
                # 如果保护器可用但文件未注册，仍尝试备份
                if self._protector:
                    self._protector.safe_write(rel_path, content)

            return {"success": True, "result": f"已写入文件系统: {abs_path}"}
        except Exception as e:
            self.logger.error(f"写入文件失败: {e}")
            return {"success": False, "error": str(e)}

    def execute_command(self, command: str, shell: str = "powershell") -> Dict[str, Any]:
        """执行终端命令（IDE Bridge 优先 → subprocess 回退）"""
        try:
            self.logger.info(f"执行命令: {command}")

            if self.bridge:
                result = self.bridge.run_command(command)
                if result["success"]:
                    return {"success": True, "output": result.get("message", "")}

            shell_cmd = (["powershell", "-Command", command]
                         if shell == "powershell" else ["cmd", "/c", command])
            proc = subprocess.run(shell_cmd, capture_output=True, text=True, timeout=60)
            output = proc.stdout + (f"\n[STDERR]\n{proc.stderr}" if proc.stderr else "")
            return {"success": proc.returncode == 0, "output": output}
        except Exception as e:
            self.logger.error(f"执行命令失败: {e}")
            return {"success": False, "error": str(e)}

    # ================================================================
    # 文件系统操作
    # ================================================================

    def list_directory(self, path: str) -> Dict[str, Any]:
        """列出目录内容"""
        try:
            self.logger.info(f"列出目录: {path}")
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = Path(os.getcwd()) / path
            if not dir_path.exists() or not dir_path.is_dir():
                return {"success": False, "error": f"目录不存在: {path}"}
            entries = []
            for item in sorted(dir_path.iterdir()):
                suffix = "/" if item.is_dir() else ""
                entries.append(f"{item.name}{suffix}")
            return {"success": True, "entries": entries[:200]}
        except Exception as e:
            self.logger.error(f"列出目录失败: {e}")
            return {"success": False, "error": str(e)}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            self.logger.info(f"创建目录: {path}")
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = Path(os.getcwd()) / path
            dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "result": f"目录已创建: {dir_path}"}
        except Exception as e:
            self.logger.error(f"创建目录失败: {e}")
            return {"success": False, "error": str(e)}

    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """移动文件"""
        try:
            self.logger.info(f"移动文件: {source} -> {destination}")
            src = Path(source) if Path(source).is_absolute() else Path(os.getcwd()) / source
            dst = Path(destination) if Path(destination).is_absolute() else Path(os.getcwd()) / destination
            if not src.exists():
                return {"success": False, "error": f"源文件不存在: {source}"}
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return {"success": True, "result": f"已移动: {src} -> {dst}"}
        except Exception as e:
            self.logger.error(f"移动文件失败: {e}")
            return {"success": False, "error": str(e)}

    def search_files(self, path: str, pattern: str) -> Dict[str, Any]:
        """搜索文件"""
        try:
            self.logger.info(f"搜索文件: {path} 匹配 {pattern}")
            from fnmatch import fnmatch
            dir_path = Path(path) if Path(path).is_absolute() else Path(os.getcwd()) / path
            if not dir_path.exists():
                return {"success": False, "error": f"路径不存在: {path}"}
            files = [str(item) for item in dir_path.rglob("*")
                     if item.is_file() and fnmatch(item.name, pattern)]
            return {"success": True, "files": files[:500]}
        except Exception as e:
            self.logger.error(f"搜索文件失败: {e}")
            return {"success": False, "error": str(e)}

    # ================================================================
    # Web 搜索
    # ================================================================

    def web_search(self, query: str) -> Dict[str, Any]:
        """搜索Web内容（使用内置 web_search 能力）"""
        try:
            self.logger.info(f"Web搜索: {query}")
            try:
                from core.ai_new import AI
                ai = AI(provider="ollama")
                result = ai(f"请搜索以下问题并提供答案: {query}", max_tokens=500)
                return {"success": True, "results": str(result)}
            except Exception:
                # 回退: 使用系统默认浏览器搜索
                import webbrowser
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return {"success": True,
                        "results": f"已在浏览器中打开搜索: {query}",
                        "note": "需要通过 TRAE IDE 的 Web 搜索 MCP 服务获取更完整的搜索结果"}
        except Exception as e:
            self.logger.error(f"Web搜索失败: {e}")
            return {"success": False, "error": str(e)}

    def visit_webpage(self, url: str, take_screenshot: bool = False) -> Dict[str, Any]:
        """访问网页"""
        try:
            self.logger.info(f"访问网页: {url}")
            import webbrowser
            webbrowser.open(url)
            return {"success": True,
                    "content": f"已在浏览器中打开: {url}",
                    "note": "截图功能需要桌面自动化 MCP 服务"}
        except Exception as e:
            self.logger.error(f"访问网页失败: {e}")
            return {"success": False, "error": str(e)}

    def sequential_thinking(self, thoughts: List[str]) -> Dict[str, Any]:
        """执行顺序思考（本地推理）"""
        try:
            self.logger.info(f"执行顺序思考: {len(thoughts)} 步")
            # 本地推理：不作外部调用，返回思考摘要
            summary_lines = []
            for i, thought in enumerate(thoughts):
                summary_lines.append(f"Step {i + 1}: {thought[:100]}")
            return {"success": True, "result": "\n".join(summary_lines)}
        except Exception as e:
            self.logger.error(f"顺序思考失败: {e}")
            return {"success": False, "error": str(e)}

    # ================================================================
    # IDE 专用操作（Bridge 直达）
    # ================================================================

    def ide_status(self) -> Dict[str, Any]:
        """获取 TRAE IDE 状态"""
        if self.bridge:
            return self.bridge.get_status()
        return {"status": "bridge_unavailable", "window": False, "process": False}

    def ide_open(self, project_path: str = None) -> Dict[str, Any]:
        """打开/激活 TRAE IDE"""
        if self.bridge:
            return self.bridge.open_ide(project_path)
        return {"success": False, "message": "Bridge 不可用"}

    def ide_focus(self) -> Dict[str, Any]:
        """聚焦 TRAE IDE"""
        if self.bridge:
            return self.bridge.focus_ide()
        return {"success": False, "message": "Bridge 不可用"}

    def ide_save(self) -> Dict[str, Any]:
        """保存当前文件"""
        if self.bridge:
            return self.bridge.save_current_file()
        return {"success": False, "message": "Bridge 不可用"}

    # ================================================================
    # 任务处理
    # ================================================================

    def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务调度（含会话记忆记录）"""
        try:
            task_type = task.get("type", task.get("task_type", ""))
            task_content = task.get("command", task.get("content", task.get("query", "")))
            task_map = {
                "read_file": lambda: self.read_file(task.get("file_path")),
                "write_file": lambda: self.write_file(task.get("file_path"), task.get("content", "")),
                "execute_command": lambda: self.execute_command(
                    task.get("command", ""), task.get("shell", "powershell")),
                "trae_command": lambda: self.execute_command(task.get("command", "")),
                "code_generation": lambda: self.write_file(
                    task.get("file_path", "generated.py"), task.get("content", task.get("command", ""))),
                "list_directory": lambda: self.list_directory(task.get("path")),
                "create_directory": lambda: self.create_directory(task.get("path")),
                "move_file": lambda: self.move_file(task.get("source"), task.get("destination")),
                "search_files": lambda: self.search_files(task.get("path"), task.get("pattern", "*")),
                "web_search": lambda: self.web_search(task.get("query")),
                "visit_webpage": lambda: self.visit_webpage(task.get("url"), task.get("take_screenshot", False)),
                "sequential_thinking": lambda: self.sequential_thinking(task.get("thoughts", [])),
                "ide_status": lambda: self.ide_status(),
                "ide_open": lambda: self.ide_open(task.get("project_path")),
                "ide_focus": lambda: self.ide_focus(),
                "ide_save": lambda: self.ide_save(),
            }
            handler = task_map.get(task_type)
            if not handler:
                err = {"success": False, "error": f"未知任务类型: {task_type}"}
                self._record_to_memory(task_type, task_content, err)
                return err

            result = handler()
            self._record_to_memory(task_type, task_content, result)
            return result
        except Exception as e:
            self.logger.error(f"处理任务失败: {e}")
            err = {"success": False, "error": str(e)}
            self._record_to_memory(task.get("type", ""), "", err)
            return err

    def _record_to_memory(self, task_type: str, content: str,
                          result: Dict[str, Any]):
        """将任务结果记录到会话记忆"""
        if not self._memory or not self._session_id:
            return
        try:
            summary = f"[{task_type}] "
            if result.get("success"):
                summary += result.get("result", result.get("output", result.get("message", "成功")))[:200]
            else:
                summary += result.get("error", "失败")[:200]
            # 记录用户指令
            if content:
                self._memory.add_message(self._session_id, "user",
                                         f"{task_type}: {content[:500]}")
            # 记录执行结果
            self._memory.add_result(self._session_id, result.get("success", False),
                                    summary, detail={"task_type": task_type})
        except Exception:
            pass  # 静默失败，不影响主流程

    # ================================================================
    # 生命周期
    # ================================================================

    def optimize_memory(self) -> bool:
        try:
            self.logger.info("优化内存使用")
            self.llm_integrator.optimize_memory()
            return True
        except Exception as e:
            self.logger.error(f"内存优化失败: {e}")
            return False

    def shutdown(self) -> None:
        # 关闭会话记忆
        if self._memory and self._session_id:
            try:
                self._memory.close_session(self._session_id)
                self.logger.info(f"会话已关闭: {self._session_id}")
            except Exception:
                pass
        self._save_to_database()
        self.optimize_memory()
        self.status = "DISABLED"
        self._initialized = False
        self.logger.info("TRAE 控制智能体已关闭")


# ============================================================
# 全局实例
# ============================================================

_trae_agent_instance = None


def get_tra_e_agent() -> TRAEControlAgent:
    """获取全局TRAE控制智能体（自动初始化）"""
    global _trae_agent_instance
    if _trae_agent_instance is None:
        _trae_agent_instance = TRAEControlAgent()
        _trae_agent_instance.initialize()
    return _trae_agent_instance


# ============================================================
# 自测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TRAE 控制智能体 v2.0 — 自测试")
    print("=" * 60)

    trae_agent = get_tra_e_agent()

    # 1. IDE 状态
    print("\n[1] IDE 状态检查...")
    status = trae_agent.ide_status()
    print(f"    状态: {status.get('status', 'unknown')}")

    # 2. 列出目录
    print("\n[2] 列出目录...")
    result = trae_agent.list_directory(str(_BASE_DIR))
    if result["success"]:
        print(f"    条目: {len(result['entries'])}")
        for e in result["entries"][:5]:
            print(f"      - {e}")
    else:
        print(f"    失败: {result['error']}")

    # 3. 执行命令
    print("\n[3] 执行命令...")
    result = trae_agent.execute_command("echo Hello from TRAE Control Agent", "cmd")
    print(f"    成功: {result['success']}")
    print(f"    输出: {result.get('output', '')[:200]}")

    print("\n" + "=" * 60)
    print("测试完成")
