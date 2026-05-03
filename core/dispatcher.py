#!/usr/bin/env python3
"""
TRAE 调度
描注册调度所有能力单元（skill/mcp/cli/workflow/agent/plugin/model
"""

import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml
import yaml

UNIT_SIGNATURES = {
    "skill.yaml": "skill",
    "mcp.json": "mcp",
    "cli.yaml": "cli",
    "workflow.yaml": "workflow",
    "agent.yaml": "agent",
    "plugin.toml": "plugin",
    "model.yaml": "model",
}

YAML_EXTS = {".yaml", ".yml"}
JSON_EXTS = {".json"}

# 输出截断保护 — 不对生成内容做硬截断，仅在异常情况下限制
# 之前 4096 字节硬截断导致 TRAE+MCP skill 链路输出丢失
MAX_SUBPROCESS_OUTPUT = 10 * 1024 * 1024  # 10 MB (足够绝大多数场景)
MAX_ERROR_OUTPUT = 16 * 1024  # 16 KB (错误信息通常较短)
TOML_EXTS = {".toml"}


class SandboxManager:
    """沙理：负责隔离执行能力单"""

    def __init__(self, base_dir: Path, default_timeout: int = 600):
        self.base_dir = base_dir
        self.trash_dir = base_dir / "storage" / "trash"
        self.default_timeout = default_timeout

    def execute(self, entry: str, unit_type: str, timeout: Optional[int] = None, **kwargs) -> dict:
        actual_timeout = timeout or self.default_timeout
        start = datetime.now()
        task_id = uuid.uuid4().hex[:12]
        result = {
            "id": task_id,
            "type": unit_type,
            "entry": entry,
            "status": "success",
            "started_at": start.isoformat(),
        }
        try:
            entry_path = Path(entry)
            if not entry_path.is_absolute():
                entry_path = self.base_dir / entry
            if not entry_path.exists():
                raise FileNotFoundError(f"入口文件不存: {entry_path}")
            if entry_path.suffix == ".py":
                cmd = ["python", str(entry_path)]
                for k, v in kwargs.items():
                    cmd.extend([f"--{k}", str(v)])
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=actual_timeout,
                    cwd=str(entry_path.parent),
                )
                result["exit_code"] = proc.returncode
                result["stdout"] = proc.stdout[:MAX_SUBPROCESS_OUTPUT]
                result["stderr"] = proc.stderr[:MAX_SUBPROCESS_OUTPUT]
                if proc.returncode != 0:
                    result["status"] = "failed"
                    result["error"] = proc.stderr[:MAX_ERROR_OUTPUT] or f"exit code {proc.returncode}"
            elif entry_path.suffix == ".ps1":
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(entry_path)]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=actual_timeout,
                    cwd=str(entry_path.parent),
                )
                result["exit_code"] = proc.returncode
                result["stdout"] = proc.stdout[:MAX_SUBPROCESS_OUTPUT]
                result["stderr"] = proc.stderr[:MAX_SUBPROCESS_OUTPUT]
                if proc.returncode != 0:
                    result["status"] = "failed"
                    result["error"] = proc.stderr[:MAX_ERROR_OUTPUT] or f"exit code {proc.returncode}"
            else:
                result["status"] = "skipped"
                result["message"] = f"不支持的入口类型: {entry_path.suffix}"
        except subprocess.TimeoutExpired:
            result["status"] = "failed"
            result["error"] = f"执超 ({actual_timeout}s)"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        end = datetime.now()
        result["duration_ms"] = int((end - start).total_seconds() * 1000)
        result["finished_at"] = end.isoformat()
        return result

    def move_to_trash(self, src: Path, snapshot_name: Optional[str] = None) -> Optional[Path]:
        self.trash_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = snapshot_name or f"{src.stem}_{ts}"
        dest = self.trash_dir / f"{name}.snapshot"
        try:
            if src.is_dir():
                shutil.copytree(str(src), str(dest))
            else:
                shutil.copy2(str(src), str(dest))
            return dest
        except Exception:
            return None


class Dispatcher:
    """TRAE 调度：能力单元扫描注册调"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get("AI_BASE_DIR", str(Path(__file__).resolve().parent.parent))
        self.base_dir = Path(base_dir)
        self.storage_dir = self.base_dir / "storage"
        self.config_dir = self.base_dir / ".trae"
        self.registry: Dict[str, Dict[str, dict]] = {}
        self._task_log: List[dict] = []
        self._snapshot: Dict[str, set] = {}
        self.sandbox = SandboxManager(self.base_dir)
        for ut in UNIT_SIGNATURES.values():
            self.registry[ut] = {}

        # 基础设施适配器（可选）
        self._adapter = None
        try:
            from core.infra_adapter import get_adapter
            self._adapter = get_adapter()
        except Exception:
            pass

    def _read_descriptor(self, path: Path) -> Optional[dict]:
        suffix = path.suffix.lower()
        try:
            if suffix in YAML_EXTS:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                return data if isinstance(data, dict) else None
            elif suffix in JSON_EXTS:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else None
            elif suffix in TOML_EXTS:
                with open(path, "r", encoding="utf-8") as f:
                    data = toml.load(f)
                return data if isinstance(data, dict) else None
        except Exception:
            return None
        return None

    def _detect_unit_type(self, path: Path) -> Optional[str]:
        return UNIT_SIGNATURES.get(path.name)

    def scan(self) -> dict:
        """user/global/ + storage/ + projects/ 下所有能力单"""
        for ut in UNIT_SIGNATURES.values():
            self.registry[ut] = {}

        scan_dirs = [
            self.base_dir / "user" / "global",
            self.storage_dir,
            self.base_dir / "projects",
        ]

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for sig_name, unit_type in UNIT_SIGNATURES.items():
                for found in scan_dir.rglob(sig_name):
                    desc = self._read_descriptor(found)
                    if desc:
                        unit_name = desc.get("name", found.parent.name)
                        config_path = str(found)
                        if scan_dir.name != "global" and scan_dir.name != "storage":
                            qualified_name = f"{scan_dir.name}/{unit_name}"
                        else:
                            qualified_name = unit_name
                        self.register(unit_type, qualified_name, config_path, desc)
                        raw_name = unit_name
                        self.register(unit_type, raw_name, config_path, desc)

        self._snapshot = {ut: set(info.keys()) for ut, info in self.registry.items()}
        return self.registry

    def register(self, unit_type: str, name: str, config_path: str, descriptor: Optional[dict] = None):
        """注册能力单元"""
        if unit_type not in self.registry:
            self.registry[unit_type] = {}
        if descriptor is None:
            descriptor = self._read_descriptor(Path(config_path)) or {}
        self.registry[unit_type][name] = {
            "type": unit_type,
            "name": name,
            "config_path": config_path,
            "descriptor": descriptor,
            "registered_at": datetime.now().isoformat(),
        }

    def dispatch(self, unit_type: str, name: str, **kwargs) -> dict:
        """调度执一能力单元（含会话追踪）"""
        dispatch_key = f"{unit_type}/{name}"

        # 会话追踪：记录开始
        if self._adapter:
            self._adapter.add_session_note("Dispatch", f"{dispatch_key} 开始")

        if unit_type not in self.registry or name not in self.registry[unit_type]:
            err = {"status": "failed", "error": f"注册的能力单: {unit_type}/{name}"}
            if self._adapter:
                self._adapter.add_session_note("Dispatch", err["error"], err)
            return err

        unit = self.registry[unit_type][name]
        desc = unit.get("descriptor", {})
        timeout = desc.get("timeout") or kwargs.pop("_timeout", None)

        result = None
        if unit_type == "mcp":
            result = self._dispatch_mcp(desc, kwargs)
        elif unit_type == "workflow":
            result = self._dispatch_workflow(desc, kwargs)
        elif unit_type == "cli":
            result = self._dispatch_cli(desc, kwargs, timeout)
        elif unit_type == "agent":
            result = self._dispatch_agent(desc, kwargs, timeout)
        else:
            entry = desc.get("entry") or desc.get("exec_path") or desc.get("path") or desc.get("command")
            if not entry:
                err = {"status": "failed", "error": f"能力单元 {unit_type}/{name} 缺少入口定义"}
                if self._adapter:
                    self._adapter.add_session_note("Dispatch", err["error"], err)
                return err
            result = self.sandbox.execute(entry, unit_type, timeout=timeout, **kwargs)
            result["name"] = name

        self._task_log.append(result)

        # 会话追踪：记录结果
        if self._adapter:
            success = result.get("status") == "success"
            self._adapter.add_session_note("Dispatch",
                                           f"{dispatch_key}: {'成功' if success else '失败'}",
                                           result)

        return result

    def _dispatch_mcp(self, desc: dict, kwargs: dict) -> dict:
        mcp_json_path = desc.get("config_path", "")
        mcp_dir = Path(mcp_json_path).parent

        mcp_json_file = mcp_dir / "mcp.json"
        if mcp_json_file.exists():
            with open(mcp_json_file, "r", encoding="utf-8") as f:
                mcp_config = json.load(f)
            server_info = mcp_config.get("mcpServers", {}).get(desc.get("name", ""), {})
            command = server_info.get("command", "python")
            args = server_info.get("args", [])
            env = server_info.get("env", {})
            entry_script = None
            for arg in args:
                if isinstance(arg, str) and (arg.endswith(".py") or "mcp" in arg.lower()):
                    entry_script = arg
                    break
            if not entry_script:
                entry_script = str(mcp_dir / f"{desc.get('name', 'server').replace('-','_')}.py")
        else:
            entry_script = str(mcp_dir / f"{desc.get('name', 'server').replace('-','_')}.py")
            command = "python"
            args = [entry_script]
            env = {}

        method = kwargs.pop("method", "full_status")
        params = kwargs.pop("params", {})

        try:
            import urllib.request as urllib2
        except ImportError:
            import urllib2

        req_body = json.dumps({"method": method, "params": params}).encode("utf-8")
        req = urllib2.Request(
            f"http://localhost:{kwargs.pop('_port', 11436)}",
            data=req_body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib2.urlopen(req, timeout=30) as resp:
                result_data = json.loads(resp.read().decode("utf-8"))
                return {"status": "success", "data": result_data, "type": "mcp"}
        except Exception:
            pass

        cmd = [command] + args
        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps({"method": method, "params": params}),
                capture_output=True,
                text=True,
                timeout=kwargs.pop("_timeout", 30),
                cwd=str(mcp_dir),
                env={**os.environ, **env} if "env" in dir() else None,
            )
            if proc.stdout:
                try:
                    result_data = json.loads(proc.stdout)
                    return {"status": "success", "data": result_data, "type": "mcp"}
                except json.JSONDecodeError:
                    return {"status": "success", "stdout": proc.stdout[:MAX_SUBPROCESS_OUTPUT], "type": "mcp"}
            return {"status": "success", "returncode": proc.returncode, "type": "mcp"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "type": "mcp"}

    def _dispatch_workflow(self, desc: dict, kwargs: dict) -> dict:
        import sys as _sys

        _sys.path.insert(0, str(self.base_dir / "core"))
        try:
            from workflow_engine import run_workflow
        except ImportError:
            return {"status": "failed", "error": "workflow_engine.py not found", "type": "workflow"}

        wf_path = desc.get("config_path", "")
        project_name = kwargs.pop("project", Path(wf_path).parent.name)

        try:
            report = run_workflow(wf_path, project_name)
            return {"status": "success", "report": report, "type": "workflow"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "type": "workflow"}

    def _dispatch_cli(self, desc: dict, kwargs: dict, timeout: Optional[int]) -> dict:
        script = desc.get("exec_path", "python")
        if not Path(script).is_absolute() and not Path(script).exists():
            script = str(self.base_dir / script)

        params_list = desc.get("params", [])
        cli_args = []
        for p in params_list:
            pname = p.get("name", "")
            val = kwargs.pop(pname, p.get("default", ""))
            if val:
                cli_args.extend([f"--{pname}", str(val)])

        try:
            proc = subprocess.run(
                [script] + cli_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.base_dir),
            )
            result = {
                "status": "success" if proc.returncode == 0 else "failed",
                "stdout": proc.stdout[:MAX_SUBPROCESS_OUTPUT],
                "stderr": proc.stderr[:MAX_SUBPROCESS_OUTPUT],
                "returncode": proc.returncode,
                "type": "cli",
            }
            self._task_log.append(result)
            return result
        except Exception as e:
            return {"status": "failed", "error": str(e), "type": "cli"}

    def _dispatch_agent(self, desc: dict, kwargs: dict,
                        timeout: Optional[int] = None) -> dict:
        """调度代理类型的能力单元

        对于 agent 类型:
        1. claude_orchestrator → 完整的编排流程
        2. 其他 agent → AgentManager 或子进程执行
        """
        agent_name = desc.get("name", "unknown")
        agent_type_val = desc.get("type", "specialized")
        config_path = desc.get("config_path", "")

        task_text = kwargs.pop("task", kwargs.pop("command", kwargs.pop("_task", "")))

        logger.info(f"调度代理: {agent_name} (type={agent_type_val}), task={str(task_text)[:100]}")

        # 路径 1: Claude 编排代理
        if agent_name == "claude_orchestrator" or "orchestrator" in str(agent_type_val).lower():
            return self._dispatch_claude_orchestrator(desc, task_text, kwargs, timeout)

        # 路径 2: 其他代理 — AgentManager
        try:
            sys.path.insert(0, str(Path(config_path).parent if config_path else self.base_dir))
            from agent.base import get_agent_manager
            manager = get_agent_manager()
            agent = manager.get_agent(agent_name)
            if agent:
                task = {"task_type": desc.get("task_type", "execute"),
                        "command": task_text, **kwargs}
                result = agent.execute(task)
                result["type"] = "agent"
                result["agent"] = agent_name
                self._task_log.append(result)
                return result
        except Exception as e:
            logger.warning(f"AgentManager 执行失败: {e}")

        # 路径 3: 子进程回退
        entry = desc.get("entry") or desc.get("exec_path")
        if entry:
            result = self.sandbox.execute(entry, "agent", timeout=timeout,
                                          task=task_text, **kwargs)
            result["agent"] = agent_name
            self._task_log.append(result)
            return result

        return {"status": "failed",
                "error": f"无法执行代理 {agent_name}: 无可用执行路径",
                "type": "agent"}

    def _dispatch_claude_orchestrator(self, desc: dict, task_text: str,
                                      kwargs: dict,
                                      timeout: Optional[int] = None) -> dict:
        """Claude 编排代理特殊调度 — 导入并运行编排器"""
        config_path = desc.get("config_path", "")
        orch_dir = Path(config_path).parent if config_path else (
            self.base_dir / "user" / "global" / "plugin" /
            "mcp-core" / "agent" / "claude_orch"
        )

        sys.path.insert(0, str(orch_dir.parent))

        try:
            from claude_orch.claude_orchestrator import get_orchestrator
            orch = get_orchestrator()
            task = {"task": task_text, "task_type": "orchestrate", "context": kwargs}
            result = orch.execute(task)
            result["type"] = "agent"
            result["agent"] = "claude_orchestrator"
            self._task_log.append(result)
            return result
        except ImportError as e:
            logger.warning(f"Claude 编排代理导入失败: {e}")
            # 回退: 直接调用 TRAE 控制代理
            try:
                sys.path.insert(0, str(orch_dir.parent))
                from trae_control import get_tra_e_agent
                trae = get_tra_e_agent()
                result = trae.handle_task({
                    "type": "execute_command",
                    "command": task_text,
                    "shell": kwargs.get("shell", "powershell"),
                })
                result["type"] = "agent"
                result["agent"] = "trae_control (fallback)"
                self._task_log.append(result)
                return result
            except ImportError:
                pass
            return {"status": "failed", "error": f"编排代理不可用: {e}", "type": "agent"}
        except Exception as e:
            logger.error(f"编排代理执行失败: {e}")
            return {"status": "failed", "error": str(e), "type": "agent"}

    def setup_wizard(self):
        """安向导：初化 Git、写 config.toml"""
        config_path = self.config_dir / "config.toml"

        if config_path.exists():
            existing = self._read_descriptor(config_path) or {}
        else:
            existing = {}

        self.config_dir.mkdir(parents=True, exist_ok=True)

        git_initialized = False
        git_dir = self.base_dir / ".git"
        if not git_dir.exists():
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=str(self.base_dir),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                git_initialized = True
            except Exception:
                pass

        tool_paths = self.scan_tools()

        config_data = {
            "platform": {
                "version": existing.get("platform", {}).get("version", "1.0.0"),
                "base_dir": str(self.base_dir).replace("\\", "/"),
            },
            "paths": tool_paths,
            "sandbox": {
                "default_timeout": existing.get("sandbox", {}).get("default_timeout", 600),
                "trash_dir": "storage/trash",
            },
            "daily": {
                "enabled": existing.get("daily", {}).get("enabled", True),
                "auto_commit": existing.get("daily", {}).get("auto_commit", False),
            },
        }

        with open(config_path, "w", encoding="utf-8") as f:
            toml.dump(config_data, f)

        return {
            "config_path": str(config_path),
            "git_initialized": git_initialized,
            "tool_paths": tool_paths,
        }

    def scan_tools(self) -> dict:
        """描本地工具路径，生成映射"""
        paths = {}

        ollama_candidates = [
            Path("%OLLAMA_DIR%/ollama.exe"),
            Path("C:/Program Files/Ollama/ollama.exe"),
            Path("{USERPROFILE}/AppData/Local/Programs/Ollama/ollama.exe"),
        ]
        for c in ollama_candidates:
            if c.exists():
                paths["ollama"] = str(c).replace("\\", "/")
                break

        python_candidates = [
            Path("{USERPROFILE}/AppData/Local/Programs/Python/Python310/python.exe"),
            Path("C:/Python310/python.exe"),
            Path("C:/Python311/python.exe"),
            Path("C:/Python312/python.exe"),
        ]
        for c in python_candidates:
            if c.exists():
                paths["python"] = str(c).replace("\\", "/")
                break

        node_path = shutil.which("node")
        if node_path:
            paths["node"] = Path(node_path).name
        else:
            paths["node"] = "node"

        git_path = shutil.which("git")
        if git_path:
            paths["git"] = str(Path(git_path)).replace("\\", "/")

        ffmpeg_candidates = [
            Path("C:/tools/ffmpeg/bin/ffmpeg.exe"),
            Path("%SOFTWARE_DIR%/ffmpeg/bin/ffmpeg.exe"),
        ]
        for c in ffmpeg_candidates:
            if c.exists():
                paths["ffmpeg"] = str(c).replace("\\", "/")
                break

        return paths

    def generate_daily_summary(self, date_str: Optional[str] = None) -> dict:
        """生成每日摘 JSON"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        daily_dir = self.storage_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        day_tasks = [t for t in self._task_log if t.get("started_at", "").startswith(date_str)]

        succeeded = [t for t in day_tasks if t.get("status") == "success"]
        failed = [t for t in day_tasks if t.get("status") == "failed"]

        errors = []
        for t in failed:
            snapshot = None
            if t.get("entry"):
                snap = self.sandbox.move_to_trash(
                    Path(t["entry"]),
                    snapshot_name=f"{t.get('id', 'unknown')}_{date_str}",
                )
                if snap:
                    snapshot = str(snap).replace(str(self.base_dir) + "\\", "").replace("\\", "/")
            errors.append(
                {
                    "task_id": t.get("id", ""),
                    "error": t.get("error", "unknown"),
                    "snapshot": snapshot or "",
                }
            )

        summary = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "tasks_executed": len(day_tasks),
            "tasks_succeeded": len(succeeded),
            "tasks_failed": len(failed),
            "tasks": [
                {
                    "id": t.get("id", ""),
                    "type": t.get("type", ""),
                    "name": t.get("name", ""),
                    "status": t.get("status", ""),
                    "duration_ms": t.get("duration_ms", 0),
                }
                for t in day_tasks
            ],
            "errors": errors,
        }

        output_path = daily_dir / f"{date_str}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary

    def sync_architecture(self) -> dict:
        """架构同：测目录变更，更新调度逻辑"""
        current = self.scan()

        added = {}
        removed = {}
        changed = {}

        for ut in UNIT_SIGNATURES.values():
            old_names = self._snapshot.get(ut, set())
            new_names = set(current.get(ut, {}).keys())

            added_names = new_names - old_names
            removed_names = old_names - new_names

            if added_names:
                added[ut] = list(added_names)
            if removed_names:
                removed[ut] = list(removed_names)

            for name in new_names & old_names:
                old_path = None
                if ut in self._snapshot and name in self.registry.get(ut, {}):
                    old_path = self.registry[ut][name].get("config_path")

                new_path = current[ut][name].get("config_path")
                if old_path != new_path:
                    if ut not in changed:
                        changed[ut] = []
                    changed[ut].append(name)

        self._snapshot = {ut: set(info.keys()) for ut, info in self.registry.items()}

        # 检查共享上下文中的新 Agent
        try:
            from core.shared_context import get_shared_context

            ctx = get_shared_context(auto_start=False)
            if ctx and ctx._started:
                agents = ctx.registry.discover_agents()
                for agent_info in agents:
                    if "shared_context.agent.discovered" not in [
                        e.get("type") for e in getattr(self, "_pending_events", [])
                    ]:
                        pass  # 已发现，通过 EventBridge 推送
        except ImportError:
            pass

        return {
            "added": added,
            "removed": removed,
            "changed": changed,
            "total_units": sum(len(v) for v in self.registry.values()),
        }

    def get_registry_summary(self) -> dict:
        """获取注册表摘"""
        return {ut: list(units.keys()) for ut, units in self.registry.items() if units}


if __name__ == "__main__":
    d = Dispatcher()
    print("=" * 60)
    print("TRAE 调度")
    print("=" * 60)

    print("\n[1] 描能力单...")
    registry = d.scan()
    for ut, units in registry.items():
        if units:
            print(f"  {ut}: {list(units.keys())}")

    print("\n[2] 架构同...")
    sync = d.sync_architecture()
    print(f"  新: {sync['added']}")
    print(f"  移除: {sync['removed']}")
    print(f"  总: {sync['total_units']} 能力单元")

    print("\n[3] 安向...")
    wizard = d.setup_wizard()
    print(f"  配置文件: {wizard['config_path']}")
    print(f"  Git 初化: {'' if wizard['git_initialized'] else ''}")
    print(f"  工具: {wizard['tool_paths']}")

    print("\n[4] 每日摘...")
    summary = d.generate_daily_summary()
    print(f"  日期: {summary['date']}")
    print(f"  执: {summary['tasks_executed']}")
    print(f"  成功: {summary['tasks_succeeded']}")
    print(f"  失败: {summary['tasks_failed']}")

    print("\n完成")


# === Sub-Agent Orchestration (Phase 4) ===

import logging

logger = logging.getLogger(__name__)


def spawn_sub_agent(sub_agent_type: str, config: dict) -> dict:
    """
    Spawn a sub-agent (qoder, trae, claude) as a child process or container.
    Returns a spawn record with spawn_id for tracking.
    """
    import uuid as _uuid
    import json as _json
    import subprocess as sp

    spawn_id = str(_uuid.uuid4())
    logger.info(f"Spawning sub-agent: type={sub_agent_type}, spawn_id={spawn_id}")

    spawn_record = {
        "spawn_id": spawn_id,
        "sub_agent_type": sub_agent_type,
        "config": config,
        "status": "pending",
        "pid": None,
    }

    try:
        # Determine execution mode from config
        isolation_mode = config.get("isolation_mode", "process")

        if isolation_mode == "container":
            # Use sandbox API for containerized execution
            logger.info(f"Sub-agent {spawn_id} will run in container")
            spawn_record["sandbox_type"] = "container"
        else:
            # Process-based execution (default)
            cmd = _build_sub_agent_command(sub_agent_type, config)
            process = sp.Popen(
                cmd,
                stdout=sp.PIPE,
                stderr=sp.PIPE,
                text=True,
            )
            spawn_record["pid"] = process.pid
            spawn_record["status"] = "running"

    except Exception as e:
        logger.error(f"Failed to spawn sub-agent {spawn_id}: {e}")
        spawn_record["status"] = "failed"
        spawn_record["error"] = str(e)

    return spawn_record


def _build_sub_agent_command(sub_agent_type: str, config: dict) -> list:
    """Build the command line for spawning a sub-agent."""
    base_cmd = config.get("command", [])
    if base_cmd:
        return base_cmd

    # Default commands per agent type
    commands = {
        "qoder": ["qoder", "run"],
        "trae": ["trae", "agent"],
        "claude": ["claude", "code"],
    }
    cmd = commands.get(sub_agent_type, ["python", "-m", "sub_agent"])
    cmd.extend(config.get("args", []))
    return cmd


def reroute_on_timeout(task: dict, alternative_path: str) -> dict:
    """
    Reroute a timed-out task to an alternative execution path.
    """
    task_id = task.get("id", task.get("task_id", "unknown"))
    original_path = task.get("execution_path", "default")
    logger.warning(
        f"Rerouting task {task_id}: {original_path} -> {alternative_path}"
    )
    task["execution_path"] = alternative_path
    task["rerouted"] = True
    task["reroute_reason"] = "timeout"
    return task


def _check_container_health(container_id: str) -> bool:
    """Check if a container is healthy and running."""
    try:
        import subprocess as sp
        result = sp.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_id],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() == "true"
    except Exception:
        return False
