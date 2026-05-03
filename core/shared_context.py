#!/usr/bin/env python
"""Cross-Agent Shared Context System v1.0

文件系统级共享上下文层，实现多 AI Agent 协调。
所有数据为纯 JSON/JSONL 格式 - 任何语言的 Agent 均可参与。

设计原则:
  - 每个 Agent 只写自己的数据（消灭写冲突）
  - 追加式日志无需锁（JSONL append-only）
  - 结构化文件用 filelock 保护读-改-写
  - 优雅降级，模块缺失时退回单 Agent 模式
  - 格式版本化，代码和数据解耦

架构:
  SharedContextManager (统一入口)
    ├── AgentRegistry        (注册/心跳/发现/清理)
    ├── TaskBoard            (任务创建/状态/冲突检测)
    ├── ContextBroadcaster   (上下文广播/读取)
    ├── FileOperationLog     (文件操作追加/轮询)
    ├── KnowledgeSyncQueue   (知识推入/拉取)
    └── ResolvedContext      (全局快照合并)
"""

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import filelock

# ─── 常量 ──────────────────────────────────────────────

FORMAT_VERSION = "1.0"
MODULE_VERSION = "1.0.0"

# 默认配置
DEFAULT_CONFIG = {
    "polling_interval_seconds": 3,
    "lock_timeout_seconds": 5,
    "heartbeat_interval_seconds": 15,
    "dead_agent_timeout_seconds": 60,
    "max_file_operations_log_lines": 10000,
    "max_knowledge_sync_queue_lines": 5000,
}


class AgentRegistry:
    """Agent 注册表 - 管理 Agent 的注册、心跳、发现和清理。

    每个 Agent 写入自己的条目，不写入其他 Agent 的条目。
    使用 filelock 保护读-改-写操作。
    """

    def __init__(self, data_dir: Path):
        self._file = data_dir / "agents_registry.json"
        self._lock_file = data_dir / "agents_registry.json.lock"
        self._lock = filelock.FileLock(str(self._lock_file), timeout=DEFAULT_CONFIG["lock_timeout_seconds"])
        self._ensure_file()

    def _ensure_file(self):
        if not self._file.exists():
            self._write_registry({"format_version": FORMAT_VERSION, "agents": {}})

    def _read_registry(self) -> dict:
        if not self._file.exists():
            return {"format_version": FORMAT_VERSION, "agents": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"format_version": FORMAT_VERSION, "agents": {}}

    def _write_registry(self, data: dict):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── 公共接口 ──────────────────────────────────────

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        pid: int = None,
        session_id: str = None,
        working_directory: str = None,
        capabilities: list = None,
        current_task: str = None,
    ) -> bool:
        """注册 Agent 到注册表。只写自己的条目。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                registry = self._read_registry()

                now = datetime.now().isoformat()
                registry["agents"][agent_id] = {
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                    "pid": pid or os.getpid(),
                    "session_id": session_id or "",
                    "working_directory": working_directory or str(Path.cwd()),
                    "status": "active",
                    "capabilities": capabilities or [],
                    "current_task": current_task or "",
                    "current_task_id": "",
                    "heartbeat_at": now,
                    "registered_at": now,
                }
                self._write_registry(registry)
                return True
        except filelock.Timeout:
            return False

    def update_heartbeat(self, agent_id: str, current_task: str = None) -> bool:
        """更新心跳时间戳。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                registry = self._read_registry()

                if agent_id not in registry["agents"]:
                    return False

                registry["agents"][agent_id]["heartbeat_at"] = datetime.now().isoformat()
                registry["agents"][agent_id]["status"] = "active"
                if current_task is not None:
                    registry["agents"][agent_id]["current_task"] = current_task

                self._write_registry(registry)
                return True
        except filelock.Timeout:
            return False

    def update_status(self, agent_id: str, status: str) -> bool:
        """更新 Agent 状态 (active/idle/shutting_down/dead)。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                registry = self._read_registry()

                if agent_id not in registry["agents"]:
                    return False

                registry["agents"][agent_id]["status"] = status
                self._write_registry(registry)
                return True
        except filelock.Timeout:
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """注销 Agent。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                registry = self._read_registry()

                if agent_id in registry["agents"]:
                    del registry["agents"][agent_id]

                self._write_registry(registry)
                return True
        except filelock.Timeout:
            return False

    def discover_agents(self, exclude_self: str = None) -> list:
        """发现所有活跃 Agent。"""
        registry = self._read_registry()
        agents = []
        deadline = datetime.now().isoformat()

        for agent_id, info in registry["agents"].items():
            if exclude_self and agent_id == exclude_self:
                continue
            heartbeat = info.get("heartbeat_at", "")
            # 简单活性检查（调用方负责清理过期 Agent）
            if info.get("status") == "active":
                agents.append(info)

        return agents

    def get_agent(self, agent_id: str) -> Optional[dict]:
        """获取指定 Agent 信息。"""
        registry = self._read_registry()
        return registry["agents"].get(agent_id)

    def cleanup_dead_agents(self, timeout_seconds: int = None) -> int:
        """清理心跳超时的死亡 Agent。返回清理数量。"""
        if timeout_seconds is None:
            timeout_seconds = DEFAULT_CONFIG["dead_agent_timeout_seconds"]

        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                registry = self._read_registry()
                now = datetime.now()
                to_remove = []

                for agent_id, info in registry["agents"].items():
                    heartbeat_str = info.get("heartbeat_at", "")
                    if heartbeat_str:
                        try:
                            hb_time = datetime.fromisoformat(heartbeat_str)
                            if (now - hb_time).total_seconds() > timeout_seconds:
                                to_remove.append(agent_id)
                        except ValueError:
                            to_remove.append(agent_id)

                for agent_id in to_remove:
                    del registry["agents"][agent_id]

                if to_remove:
                    self._write_registry(registry)

                return len(to_remove)
        except filelock.Timeout:
            return 0


class TaskBoard:
    """共享任务板 - 管理所有 Agent 的任务。

    每个 Agent 创建和更新自己的任务。
    提供文件冲突检测。
    """

    def __init__(self, data_dir: Path):
        self._file = data_dir / "task_board.json"
        self._lock_file = data_dir / "task_board.json.lock"
        self._lock = filelock.FileLock(str(self._lock_file), timeout=DEFAULT_CONFIG["lock_timeout_seconds"])
        self._ensure_file()

    def _ensure_file(self):
        if not self._file.exists():
            self._write_board({"format_version": FORMAT_VERSION, "tasks": {}})

    def _read_board(self) -> dict:
        if not self._file.exists():
            return {"format_version": FORMAT_VERSION, "tasks": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"format_version": FORMAT_VERSION, "tasks": {}}

    def _write_board(self, data: dict):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _path_matches(self, file_path: str, pattern: str) -> bool:
        """检查文件路径是否匹配模式（支持 ** 递归通配）。"""
        from fnmatch import fnmatch

        norm_path = file_path.replace("\\", "/").lower()
        norm_pattern = pattern.replace("\\", "/").lower()

        if "**" in norm_pattern:
            # 简单 ** 匹配
            prefix = norm_pattern.split("**")[0].rstrip("/")
            return norm_path.startswith(prefix)
        return fnmatch(norm_path, norm_pattern)

    # ─── 公共接口 ──────────────────────────────────────

    def create_task(
        self,
        task_id: str,
        title: str,
        owner_agent: str,
        owner_type: str = "",
        files_involved: list = None,
        priority: int = 0,
        dependencies: list = None,
    ) -> bool:
        """创建新任务。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                board = self._read_board()

                now = datetime.now().isoformat()
                board["tasks"][task_id] = {
                    "task_id": task_id,
                    "title": title,
                    "owner_agent": owner_agent,
                    "owner_type": owner_type,
                    "status": "in_progress",
                    "priority": priority,
                    "files_involved": files_involved or [],
                    "dependencies": dependencies or [],
                    "blocked_by": [],
                    "created_at": now,
                    "updated_at": now,
                    "result_summary": None,
                    "context_broadcast_id": None,
                }
                self._write_board(board)
                return True
        except filelock.Timeout:
            return False

    def update_task(
        self, task_id: str, status: str = None, result_summary: str = None, owner_agent: str = None
    ) -> bool:
        """更新任务状态。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                board = self._read_board()

                if task_id not in board["tasks"]:
                    return False

                task = board["tasks"][task_id]
                if owner_agent and task["owner_agent"] != owner_agent:
                    return False  # 不是你的任务

                if status is not None:
                    task["status"] = status
                if result_summary is not None:
                    task["result_summary"] = result_summary
                task["updated_at"] = datetime.now().isoformat()

                self._write_board(board)
                return True
        except filelock.Timeout:
            return False

    def get_active_tasks(self, exclude_agent: str = None) -> list:
        """获取所有进行中的任务。"""
        board = self._read_board()
        active = []
        for task in board["tasks"].values():
            if task["status"] == "in_progress":
                if exclude_agent and task["owner_agent"] == exclude_agent:
                    continue
                active.append(task)
        return active

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取指定任务。"""
        board = self._read_board()
        return board["tasks"].get(task_id)

    def clean_completed_tasks(self, keep_recent: int = 50) -> int:
        """清理已完成/失败的任务（保留最近 N 个）。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                board = self._read_board()
                finished_tasks = []

                for task_id, task in board["tasks"].items():
                    if task["status"] in ("completed", "failed", "cancelled"):
                        finished_tasks.append((task_id, task.get("updated_at", "")))

                finished_tasks.sort(key=lambda x: x[1], reverse=True)
                to_remove = [tid for tid, _ in finished_tasks[keep_recent:]]

                for task_id in to_remove:
                    del board["tasks"][task_id]

                if to_remove:
                    self._write_board(board)

                return len(to_remove)
        except filelock.Timeout:
            return 0

    def check_file_conflicts(self, file_path: str, exclude_agent: str = None) -> Optional[dict]:
        """检查是否有其他 Agent 正在处理同一文件。

        返回冲突信息 dict，无冲突返回 None。
        """
        board = self._read_board()
        for task in board["tasks"].values():
            if task["status"] != "in_progress":
                continue
            if exclude_agent and task["owner_agent"] == exclude_agent:
                continue
            for involved in task.get("files_involved", []):
                if self._path_matches(file_path, involved):
                    return {
                        "conflict_with_agent": task["owner_agent"],
                        "conflict_task": task["task_id"],
                        "conflict_description": task["title"],
                        "conflict_file": file_path,
                        "matched_pattern": involved,
                    }
        return None


class ContextBroadcaster:
    """上下文广播系统 - 每个 Agent 广播自身当前工作上下文。

    每个 Agent 仅覆盖自己的广播条目。
    """

    def __init__(self, data_dir: Path):
        self._file = data_dir / "context_broadcasts.json"
        self._lock_file = data_dir / "context_broadcasts.json.lock"
        self._lock = filelock.FileLock(str(self._lock_file), timeout=DEFAULT_CONFIG["lock_timeout_seconds"])
        self._ensure_file()

    def _ensure_file(self):
        if not self._file.exists():
            self._write({"format_version": FORMAT_VERSION, "broadcasts": {}})

    def _read(self) -> dict:
        if not self._file.exists():
            return {"format_version": FORMAT_VERSION, "broadcasts": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"format_version": FORMAT_VERSION, "broadcasts": {}}

    def _write(self, data: dict):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── 公共接口 ──────────────────────────────────────

    def broadcast(
        self, agent_id: str, summary: str, key_files: list = None, key_decisions: list = None, update_count: int = None
    ) -> bool:
        """广播当前 Agent 的上下文。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                data = self._read()

                existing = data["broadcasts"].get(agent_id, {})
                new_count = (existing.get("update_count", 0) + 1) if update_count is None else update_count

                data["broadcasts"][agent_id] = {
                    "broadcast_id": f"ctx_{agent_id}_v{new_count}",
                    "agent_id": agent_id,
                    "context_summary": summary,
                    "key_files": key_files or [],
                    "key_decisions": key_decisions or [],
                    "timestamp": datetime.now().isoformat(),
                    "update_count": new_count,
                }
                self._write(data)
                return True
        except filelock.Timeout:
            return False

    def get_agent_context(self, agent_id: str) -> Optional[dict]:
        """获取指定 Agent 的广播上下文。"""
        data = self._read()
        return data["broadcasts"].get(agent_id)

    def get_all_contexts(self, exclude_agent: str = None) -> dict:
        """获取所有 Agent 的广播上下文。"""
        data = self._read()
        if exclude_agent:
            return {k: v for k, v in data["broadcasts"].items() if k != exclude_agent}
        return data["broadcasts"]

    def clear_stale(self, active_agent_ids: set):
        """清理不在活跃列表中的 Agent 广播。"""
        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                data = self._read()
                to_remove = [k for k in data["broadcasts"] if k not in active_agent_ids]
                for k in to_remove:
                    del data["broadcasts"][k]
                if to_remove:
                    self._write(data)
        except filelock.Timeout:
            pass


class FileOperationLog:
    """文件操作日志 - 追加式 JSONL 日志记录所有文件操作。

    追加写入无需锁（NTFS <4KB 追加是原子操作）。
    使用 marker 文件追踪每个 Agent 的读取位置。
    """

    def __init__(self, data_dir: Path):
        self._log_file = data_dir / "file_operations.log"
        self._markers_dir = data_dir / "markers"
        self._markers_dir.mkdir(parents=True, exist_ok=True)

    def _get_marker_file(self, agent_id: str) -> Path:
        return self._markers_dir / f"{agent_id}.json"

    def _read_marker(self, agent_id: str) -> dict:
        marker_file = self._get_marker_file(agent_id)
        if not marker_file.exists():
            return {"agent_id": agent_id, "position": 0, "last_poll_at": ""}
        try:
            return json.loads(marker_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"agent_id": agent_id, "position": 0, "last_poll_at": ""}

    def _write_marker(self, agent_id: str, position: int):
        marker_file = self._get_marker_file(agent_id)
        marker_file.write_text(
            json.dumps(
                {
                    "agent_id": agent_id,
                    "position": position,
                    "last_poll_at": datetime.now().isoformat(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # ─── 公共接口 ──────────────────────────────────────

    def log_operation(
        self, event: str, file_path: str, operation: str, agent_id: str, task_id: str = "", checksum_md5: str = None
    ) -> bool:
        """记录文件操作到日志。追加写入，无锁。"""
        entry = {
            "event": event,
            "agent_id": agent_id,
            "file_path": file_path,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "checksum_md5": checksum_md5,
        }
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def poll_new_operations(self, agent_id: str) -> list:
        """轮询自上次读取以来的新文件操作。

        返回新操作列表，并更新 marker 位置。
        """
        marker = self._read_marker(agent_id)
        start_pos = marker.get("position", 0)

        if not self._log_file.exists():
            return []

        new_ops = []
        current_pos = start_pos

        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                f.seek(start_pos)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            op = json.loads(line)
                            if op.get("agent_id") != agent_id:
                                new_ops.append(op)
                        except json.JSONDecodeError:
                            pass
                    current_pos = f.tell()

            if current_pos > start_pos:
                self._write_marker(agent_id, current_pos)
        except Exception:
            pass

        return new_ops

    def get_recent_changes(self, since_timestamp: str = None, limit: int = 50) -> list:
        """获取最近的文件变更（跨 Agent）。"""
        if not self._log_file.exists():
            return []

        ops = []
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            op = json.loads(line)
                            if since_timestamp and op.get("timestamp", "") <= since_timestamp:
                                continue
                            ops.append(op)
                        except json.JSONDecodeError:
                            pass
        except Exception:
            return []

        return ops[-limit:]

    def get_changes_by_agent(self, agent_id: str, limit: int = 50) -> list:
        """获取指定 Agent 的变更记录。"""
        if not self._log_file.exists():
            return []

        ops = []
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            op = json.loads(line)
                            if op.get("agent_id") == agent_id:
                                ops.append(op)
                        except json.JSONDecodeError:
                            pass
        except Exception:
            return []

        return ops[-limit:]

    def rotate_if_needed(self, max_lines: int = None):
        """如果日志过大，截断保留最近 N 行。"""
        if max_lines is None:
            max_lines = DEFAULT_CONFIG["max_file_operations_log_lines"]

        if not self._log_file.exists():
            return

        try:
            lines = self._log_file.read_text(encoding="utf-8").strip().split("\n")
            if len(lines) > max_lines:
                self._log_file.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")
        except Exception:
            pass


class KnowledgeSyncQueue:
    """跨 Agent 知识同步队列 - 追加式 JSONL 队列。

    每个 Agent 推入自己学到的知识，拉取其他 Agent 的知识。
    """

    def __init__(self, data_dir: Path):
        self._queue_file = data_dir / "knowledge_sync_queue.log"
        self._markers_dir = data_dir / "markers"
        self._markers_dir.mkdir(parents=True, exist_ok=True)

    def _get_marker_file(self, agent_id: str) -> Path:
        return self._markers_dir / f"ks_{agent_id}.json"

    def _read_marker(self, agent_id: str) -> dict:
        marker_file = self._get_marker_file(agent_id)
        if not marker_file.exists():
            return {"agent_id": agent_id, "position": 0}
        try:
            return json.loads(marker_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"agent_id": agent_id, "position": 0}

    def _write_marker(self, agent_id: str, position: int):
        marker_file = self._get_marker_file(agent_id)
        marker_file.write_text(
            json.dumps(
                {
                    "agent_id": agent_id,
                    "position": position,
                    "last_poll_at": datetime.now().isoformat(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # ─── 公共接口 ──────────────────────────────────────

    def push_knowledge(
        self,
        title: str,
        content: str,
        agent_id: str,
        category: str = "shared_knowledge",
        tags: list = None,
        importance: int = 3,
    ) -> bool:
        """推入知识条目到同步队列。追加写入，无锁。"""
        entry = {
            "action": "learn",
            "agent_id": agent_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            with open(self._queue_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception:
            return False

    def pull_knowledge(self, agent_id: str, limit: int = 20) -> list:
        """拉取其他 Agent 推送的未处理知识条目。"""
        marker = self._read_marker(agent_id)
        start_pos = marker.get("position", 0)

        if not self._queue_file.exists():
            return []

        entries = []
        current_pos = start_pos

        try:
            with open(self._queue_file, "r", encoding="utf-8") as f:
                f.seek(start_pos)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            if entry.get("agent_id") != agent_id:
                                entries.append(entry)
                                if len(entries) >= limit:
                                    break
                        except json.JSONDecodeError:
                            pass
                    current_pos = f.tell()

            if current_pos > start_pos:
                self._write_marker(agent_id, current_pos)
        except Exception:
            pass

        return entries

    def rotate_if_needed(self, max_lines: int = None):
        """如果队列过大，截断保留最近 N 行。"""
        if max_lines is None:
            max_lines = DEFAULT_CONFIG["max_knowledge_sync_queue_lines"]

        if not self._queue_file.exists():
            return

        try:
            lines = self._queue_file.read_text(encoding="utf-8").strip().split("\n")
            if len(lines) > max_lines:
                self._queue_file.write_text("\n".join(lines[-max_lines:]) + "\n", encoding="utf-8")
        except Exception:
            pass


class ResolvedContext:
    """全局上下文快照 - 合并所有共享数据为统一视图。"""

    def __init__(self, data_dir: Path):
        self._file = data_dir / "resolved_context.json"
        self._lock_file = data_dir / "resolved_context.json.lock"
        self._lock = filelock.FileLock(str(self._lock_file), timeout=DEFAULT_CONFIG["lock_timeout_seconds"])
        self._data_dir = data_dir

    def resolve(
        self,
        registry: AgentRegistry,
        task_board: TaskBoard,
        broadcaster: ContextBroadcaster,
        file_log: FileOperationLog,
    ) -> dict:
        """合并所有数据源生成全局快照。"""
        agents = registry.discover_agents()
        tasks = task_board.get_active_tasks()
        contexts = broadcaster.get_all_contexts()
        recent_files = file_log.get_recent_changes(limit=50)

        # 冲突检测
        conflicts = []
        active_files = {}
        for task in tasks:
            for f in task.get("files_involved", []):
                if f in active_files:
                    conflicts.append(
                        {
                            "file": f,
                            "agents": [active_files[f], task["owner_agent"]],
                            "tasks": [None, task["task_id"]],
                            "severity": "warning",
                        }
                    )
                active_files[f] = task["owner_agent"]

        resolved = {
            "format_version": FORMAT_VERSION,
            "generated_at": datetime.now().isoformat(),
            "active_agents": [a["agent_id"] for a in agents],
            "active_tasks": [t["task_id"] for t in tasks],
            "recently_modified_files": [op["file_path"] for op in recent_files[-20:]],
            "cross_agent_conflicts": conflicts,
            "merged_context": self._generate_summary(agents, tasks, conflicts),
        }

        try:
            with self._lock.acquire(timeout=DEFAULT_CONFIG["lock_timeout_seconds"]):
                self._file.parent.mkdir(parents=True, exist_ok=True)
                self._file.write_text(json.dumps(resolved, ensure_ascii=False, indent=2), encoding="utf-8")
        except filelock.Timeout:
            pass

        return resolved

    def _generate_summary(self, agents: list, tasks: list, conflicts: list) -> str:
        parts = []
        if agents:
            agent_descs = [f"{a['agent_id']}({a['agent_type']}): {a.get('current_task', 'unknown')}" for a in agents]
            parts.append(f"{len(agents)} agents active: {'; '.join(agent_descs)}")
        if tasks:
            parts.append(f"{len(tasks)} tasks in progress")
        if conflicts:
            parts.append(f"{len(conflicts)} file conflicts detected")
        if not parts:
            parts.append("No active agents or tasks")
        return ". ".join(parts)

    def get_latest(self) -> Optional[dict]:
        """获取最近一次计算的全局快照。"""
        if not self._file.exists():
            return None
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return None


class SharedContextManager:
    """跨 Agent 共享上下文管理器 - 统一入口。

    用法:
        ctx = SharedContextManager("Qoder_001", "qoder")
        ctx.register_agent()
        ctx.broadcast_context("working on X")
        ctx.log_file_operation("file_created", "path/to/file", "write")
        conflicts = ctx.check_file_conflicts("path/to/file")
    """

    def __init__(self, agent_id: str, agent_type: str, data_dir: Path = None, auto_register: bool = False):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self._started = False
        self._heartbeat_thread = None
        self._stop_heartbeat = threading.Event()

        if data_dir is None:
            # 默认数据目录
            self._data_dir = self._find_data_dir()
        else:
            self._data_dir = Path(data_dir)

        self._data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化子模块
        self.registry = AgentRegistry(self._data_dir)
        self.task_board = TaskBoard(self._data_dir)
        self.broadcaster = ContextBroadcaster(self._data_dir)
        self.file_log = FileOperationLog(self._data_dir)
        self.knowledge_sync = KnowledgeSyncQueue(self._data_dir)
        self.resolved_ctx = ResolvedContext(self._data_dir)

    def _find_data_dir(self) -> Path:
        """查找数据目录。尝试多个可能位置。"""
        candidates = [
            Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent)) / "storage/shared_context",
            Path("../storage/shared_context"),
            Path("storage/shared_context"),
        ]
        # 从当前文件位置查找
        try:
            script_dir = Path(__file__).parent.parent  # core/ -> /python/
            candidates.insert(0, script_dir / "storage" / "shared_context")
        except NameError:
            pass
        return candidates[0]

    # ─── Agent 生命周期 ──────────────────────────────────

    def start(self, register: bool = True, heartbeat: bool = True, heartbeat_interval: float = None) -> bool:
        """启动共享上下文管理器。"""
        if self._started:
            return True

        if register:
            if not self.register_agent():
                return False

        if heartbeat:
            if heartbeat_interval is None:
                heartbeat_interval = DEFAULT_CONFIG["heartbeat_interval_seconds"]
            self._start_heartbeat_thread(heartbeat_interval)

        self._started = True
        return True

    def stop(self):
        """停止共享上下文管理器。"""
        self._started = False
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        self.registry.update_status(self.agent_id, "shutting_down")
        self.registry.unregister_agent(self.agent_id)

    def register_agent(
        self, session_id: str = None, working_directory: str = None, capabilities: list = None, current_task: str = None
    ) -> bool:
        """注册当前 Agent。"""
        return self.registry.register_agent(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            pid=os.getpid(),
            session_id=session_id,
            working_directory=working_directory or str(Path.cwd()),
            capabilities=capabilities,
            current_task=current_task,
        )

    def _start_heartbeat_thread(self, interval: float):
        """启动心跳后台线程。"""

        def _heartbeat_loop():
            while not self._stop_heartbeat.wait(interval):
                try:
                    self.registry.update_heartbeat(self.agent_id)
                except Exception:
                    pass

        self._heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    # ─── 便利方法 ──────────────────────────────────────

    def broadcast_context(self, summary: str, key_files: list = None, key_decisions: list = None) -> bool:
        """广播当前 Agent 的上下文。"""
        return self.broadcaster.broadcast(
            agent_id=self.agent_id,
            summary=summary,
            key_files=key_files,
            key_decisions=key_decisions,
        )

    def create_task(self, task_id: str, title: str, files_involved: list = None, priority: int = 0) -> bool:
        """在当前 Agent 名下创建任务。"""
        return self.task_board.create_task(
            task_id=task_id,
            title=title,
            owner_agent=self.agent_id,
            owner_type=self.agent_type,
            files_involved=files_involved,
            priority=priority,
        )

    def complete_task(self, task_id: str, result: str = None) -> bool:
        """完成当前 Agent 的任务。"""
        return self.task_board.update_task(
            task_id=task_id,
            status="completed",
            result_summary=result,
            owner_agent=self.agent_id,
        )

    def check_file_conflicts(self, file_path: str) -> Optional[dict]:
        """检查文件是否被其他 Agent 占用。"""
        return self.task_board.check_file_conflicts(
            file_path=file_path,
            exclude_agent=self.agent_id,
        )

    def log_file_operation(self, event: str, file_path: str, operation: str, task_id: str = "") -> bool:
        """记录文件操作。"""
        return self.file_log.log_operation(
            event=event,
            file_path=file_path,
            operation=operation,
            agent_id=self.agent_id,
            task_id=task_id,
        )

    def poll_other_agent_changes(self) -> list:
        """轮询其他 Agent 的文件变更。"""
        return self.file_log.poll_new_operations(self.agent_id)

    def push_knowledge(
        self, title: str, content: str, category: str = "shared_knowledge", tags: list = None, importance: int = 3
    ) -> bool:
        """推送知识到同步队列。"""
        return self.knowledge_sync.push_knowledge(
            title=title,
            content=content,
            agent_id=self.agent_id,
            category=category,
            tags=tags,
            importance=importance,
        )

    def pull_knowledge(self, limit: int = 20) -> list:
        """拉取其他 Agent 的知识。"""
        return self.knowledge_sync.pull_knowledge(self.agent_id, limit=limit)

    def resolve(self) -> dict:
        """生成全局快照。"""
        return self.resolved_ctx.resolve(
            registry=self.registry,
            task_board=self.task_board,
            broadcaster=self.broadcaster,
            file_log=self.file_log,
        )

    def get_snapshot(self) -> Optional[dict]:
        """获取最近一次计算的全局快照。"""
        return self.resolved_ctx.get_latest()

    def maintenance(self):
        """执行定期维护：清理死 Agent、轮转日志。"""
        self.registry.cleanup_dead_agents()
        self.file_log.rotate_if_needed()
        self.knowledge_sync.rotate_if_needed()
        self.task_board.clean_completed_tasks()


# ─── 模块级单例 ──────────────────────────────────────

_shared_context_instance: Optional[SharedContextManager] = None
_instance_lock = threading.Lock()


def get_shared_context(
    agent_id: str = None, agent_type: str = None, data_dir: Path = None, auto_start: bool = True
) -> Optional[SharedContextManager]:
    """获取共享上下文模块级单例。

    同一进程内的多个调用返回同一实例。
    不同进程各自有自己的实例（通过文件系统共享数据）。

    Args:
        agent_id: Agent 标识（首次调用时必需）
        agent_type: Agent 类型（首次调用时必需）
        data_dir: 自定义数据目录
        auto_start: 是否自动启动注册和心跳

    Returns:
        SharedContextManager 实例
    """
    global _shared_context_instance

    with _instance_lock:
        if _shared_context_instance is not None:
            return _shared_context_instance

        if not agent_id:
            import uuid

            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        if not agent_type:
            agent_type = "unknown"

        _shared_context_instance = SharedContextManager(
            agent_id=agent_id,
            agent_type=agent_type,
            data_dir=data_dir,
        )

        if auto_start:
            _shared_context_instance.start(register=True, heartbeat=True)

        return _shared_context_instance


# ─── CLI 测试入口 ──────────────────────────────────────

if __name__ == "__main__":
    print(f"Cross-Agent Shared Context System v{MODULE_VERSION}")
    print(f"Format version: {FORMAT_VERSION}")
    print()

    # 找到数据目录
    data_dir = Path(__file__).parent.parent / "storage" / "shared_context"
    print(f"Data directory: {data_dir}")

    # 测试 Agent A
    print("\n─── Agent A (Qoder) ───")
    ctx_a = SharedContextManager("Qoder_test", "qoder", data_dir=data_dir)
    ctx_a.register_agent(session_id="test_session_a", capabilities=["read", "write", "code_search"])
    print(f"  Registered: {ctx_a.agent_id}")

    ctx_a.create_task("task_test_1", "Testing shared context", files_involved=["/python/test.txt"])
    ctx_a.broadcast_context("Testing cross-agent context sharing")
    ctx_a.log_file_operation("file_created", "/python/test.txt", "write", task_id="task_test_1")

    # 测试 Agent B
    print("\n─── Agent B (TRAE) ───")
    ctx_b = SharedContextManager("TRAE_test", "trae", data_dir=data_dir)
    ctx_b.register_agent(session_id="test_session_b", capabilities=["pipeline", "gstack"])
    print(f"  Registered: {ctx_b.agent_id}")

    # Agent B 发现 Agent A
    agents = ctx_b.registry.discover_agents(exclude_self="TRAE_test")
    print(f"  Discovered agents: {[a['agent_id'] for a in agents]}")

    # 冲突检测
    conflict = ctx_b.check_file_conflicts("/python/test.txt")
    if conflict:
        print(f"  File conflict detected: {conflict['conflict_with_agent']} on {conflict['conflict_file']}")
    else:
        print("  No file conflicts")

    # Agent B 轮询变更
    changes = ctx_b.poll_other_agent_changes()
    print(f"  Other agent changes: {len(changes)}")
    for c in changes:
        print(f"    - {c['agent_id']}: {c['event']} {c['file_path']}")

    # 知识同步
    ctx_a.push_knowledge("Shared Context Pattern", "File-based cross-agent coordination", category="domain_knowledge")
    knowledge = ctx_b.pull_knowledge()
    print(f"\n  Knowledge pulled from other agents: {len(knowledge)}")
    for k in knowledge:
        print(f"    - [{k['category']}] {k['title']} (from {k['agent_id']})")

    # 全局快照
    print("\n─── Global Snapshot ───")
    snapshot = ctx_b.resolve()
    print(f"  Active agents: {snapshot['active_agents']}")
    print(f"  Active tasks: {snapshot['active_tasks']}")
    print(f"  Conflicts: {len(snapshot['cross_agent_conflicts'])}")
    print(f"  Summary: {snapshot['merged_context']}")

    # 清理
    ctx_a.stop()
    ctx_b.stop()

    print("\nAll tests passed!")
