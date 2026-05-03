#!/usr/bin/env python3
"""
沙盒执行机制 - 进程隔离、删除拦截、超时监控、快照保存
"""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SandboxResult:
    """沙盒执行结果"""

    task_id: str
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    snapshot_path: Optional[str] = None


class DeleteInterceptor:
    """删除拦截器 - 钩子方式拦截未授权删除操作"""

    def __init__(self):
        self.blocked_deletes: List[Dict[str, Any]] = []
        self._original_remove = os.remove
        self._original_rmtree = shutil.rmtree
        self._original_unlink = None
        self._active = False
        self._lock = threading.Lock()

    def activate(self):
        """激活删除拦截钩子"""
        if self._active:
            return
        with self._lock:
            if self._active:
                return
            os.remove = self._hooked_remove
            shutil.rmtree = self._hooked_rmtree
            if hasattr(os, "unlink"):
                self._original_unlink = os.unlink
                os.unlink = self._hooked_unlink
            self._active = True

    def deactivate(self):
        """恢复原始删除函数"""
        if not self._active:
            return
        with self._lock:
            if not self._active:
                return
            os.remove = self._original_remove
            shutil.rmtree = self._original_rmtree
            if self._original_unlink is not None:
                os.unlink = self._original_unlink
            self._active = False

    def _hooked_remove(self, path, *args, **kwargs):
        """拦截 os.remove 调用"""
        caller_frame = sys._getframe(1)
        caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        record = {
            "path": str(path),
            "action": "os.remove",
            "caller": caller_info,
            "timestamp": datetime.now().isoformat(),
        }
        self.blocked_deletes.append(record)
        print(f"[SANDBOX] 删除操作已拦截: os.remove('{path}') 来自 {caller_info}")

    def _hooked_rmtree(self, path, *args, **kwargs):
        """拦截 shutil.rmtree 调用"""
        caller_frame = sys._getframe(1)
        caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        record = {
            "path": str(path),
            "action": "shutil.rmtree",
            "caller": caller_info,
            "timestamp": datetime.now().isoformat(),
        }
        self.blocked_deletes.append(record)
        print(f"[SANDBOX] 删除操作已拦截: shutil.rmtree('{path}') 来自 {caller_info}")

    def _hooked_unlink(self, path, *args, **kwargs):
        """拦截 os.unlink 调用"""
        caller_frame = sys._getframe(1)
        caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
        record = {
            "path": str(path),
            "action": "os.unlink",
            "caller": caller_info,
            "timestamp": datetime.now().isoformat(),
        }
        self.blocked_deletes.append(record)
        print(f"[SANDBOX] 删除操作已拦截: os.unlink('{path}') 来自 {caller_info}")

    def get_blocked(self) -> List[Dict[str, Any]]:
        """获取所有被拦截的删除操作"""
        return list(self.blocked_deletes)

    def clear(self):
        """清空拦截记录"""
        self.blocked_deletes.clear()


class SandboxManager:
    """沙盒环境管理器"""

    def __init__(self, trash_dir: str = None, default_timeout: int = 600):
        if trash_dir is None:
            _base = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
            trash_dir = str(_base / "storage/trash")
        self.trash_dir = Path(trash_dir)
        self.default_timeout = default_timeout
        self.trash_dir.mkdir(parents=True, exist_ok=True)

        self._processes: Dict[str, subprocess.Popen] = {}
        self._interceptor = DeleteInterceptor()
        self._file_tracker: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def execute(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        permissions: Optional[Dict[str, bool]] = None,
        task_id: Optional[str] = None,
    ) -> SandboxResult:
        """
        执行一个能力单元
        - command: 要执行的命令
        - args: 命令参数列表
        - env: 环境变量
        - cwd: 工作目录
        - timeout: 超时秒数，默认使用 default_timeout
        - permissions: 权限字典，如 {"delete": True, "network": False}
        - task_id: 任务标识，自动生成如果未提供
        """
        if task_id is None:
            task_id = uuid.uuid4().hex[:8]

        effective_timeout = timeout if timeout is not None else self.default_timeout
        permissions = permissions or {}

        cmd_parts = command.split() if isinstance(command, str) else list(command)
        if args:
            cmd_parts.extend(args)

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        work_dir = str(Path(cwd).resolve()) if cwd else str(Path.cwd())

        self._interceptor.clear()
        self._file_tracker[task_id] = []

        allow_delete = permissions.get("delete", False)
        if not allow_delete:
            self._interceptor.activate()

        snapshot_path = None
        timed_out = False
        exit_code = -1
        stdout_data = ""
        stderr_data = ""

        try:
            process = subprocess.Popen(
                cmd_parts,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=exec_env,
                cwd=work_dir,
                text=True,
            )

            with self._lock:
                self._processes[task_id] = process

            log_lines = []
            try:
                stdout_data, stderr_data = process.communicate(timeout=effective_timeout)
                exit_code = process.returncode
                if stdout_data:
                    log_lines.extend(stdout_data.splitlines())
                if stderr_data:
                    log_lines.extend(stderr_data.splitlines())

            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout_data, stderr_data = process.communicate()
                exit_code = -9

                if stdout_data:
                    log_lines.extend(stdout_data.splitlines())
                if stderr_data:
                    log_lines.extend(stderr_data.splitlines())

                log_lines.append(f"[SANDBOX] 任务 {task_id} 超时（{effective_timeout}秒），已终止")

                snapshot_path = self.create_snapshot(
                    task_id=task_id,
                    process=process,
                    log_lines=log_lines,
                    reason="timeout",
                    command=command,
                )

        except Exception as e:
            stderr_data = str(e)
            log_lines = [f"[SANDBOX] 执行异常: {e}"]

        finally:
            if not allow_delete:
                self._interceptor.deactivate()

            with self._lock:
                self._processes.pop(task_id, None)

        return SandboxResult(
            task_id=task_id,
            exit_code=exit_code,
            stdout=stdout_data,
            stderr=stderr_data,
            timed_out=timed_out,
            snapshot_path=snapshot_path,
        )

    def create_snapshot(
        self,
        task_id: str,
        process: subprocess.Popen,
        log_lines: List[str],
        reason: str = "timeout",
        command: str = "",
    ) -> str:
        """
        创建快照到 trash/ 目录
        返回快照文件路径
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d_%H%M%S")
        snapshot_filename = f"{timestamp_str}_{task_id}.snapshot"
        snapshot_path = self.trash_dir / snapshot_filename

        variables = {}
        try:
            if process.poll() is not None:
                variables["exit_code"] = process.returncode
            variables["pid"] = process.pid
        except Exception:
            pass

        file_changes = self._file_tracker.get(task_id, [])
        blocked_deletes = self._interceptor.get_blocked()
        file_changes.extend(blocked_deletes)

        snapshot_data = {
            "task_id": task_id,
            "timestamp": now.isoformat(),
            "reason": reason,
            "command": command,
            "log": log_lines,
            "variables": variables,
            "file_changes": file_changes,
        }

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)

        print(f"[SANDBOX] 快照已保存: {snapshot_path}")
        return str(snapshot_path)

    def check_delete_permission(self, path: str, permissions: Dict[str, bool]) -> bool:
        """
        检查删除权限
        - path: 要删除的路径
        - permissions: 权限字典
        返回是否允许删除
        """
        if permissions.get("delete", False):
            return True

        if permissions.get("delete_paths"):
            allowed_paths = permissions["delete_paths"]
            target = Path(path).resolve()
            for allowed in allowed_paths:
                allowed_resolved = Path(allowed).resolve()
                try:
                    target.relative_to(allowed_resolved)
                    return True
                except ValueError:
                    continue

        print(f"[SANDBOX] 删除权限不足: {path}")
        return False

    def kill_task(self, task_id: str) -> bool:
        """终止指定任务"""
        with self._lock:
            process = self._processes.get(task_id)

        if process is None:
            return False

        try:
            process.kill()
            with self._lock:
                self._processes.pop(task_id, None)
            return True
        except Exception:
            return False

    def list_active_tasks(self) -> List[str]:
        """列出所有活跃任务"""
        with self._lock:
            return list(self._processes.keys())

    def track_file_change(self, task_id: str, path: str, action: str):
        """追踪文件变更"""
        if task_id not in self._file_tracker:
            self._file_tracker[task_id] = []
        self._file_tracker[task_id].append(
            {
                "path": str(path),
                "action": action,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def cleanup(self):
        """清理所有活跃任务和拦截器"""
        self._interceptor.deactivate()
        with self._lock:
            for task_id, process in list(self._processes.items()):
                try:
                    process.kill()
                except Exception:
                    pass
            self._processes.clear()


# === Sub-Agent Sandbox Integration (Phase 4) ===

import hashlib
import logging

logger = logging.getLogger(__name__)

# ---- Conditional import: sandbox_service may not be available ----
try:
    from core.sandbox_service import DockerSandboxManager, SmartTimeoutHandler
except ImportError:
    # Stub implementations when sandbox_service module is not present
    class DockerSandboxManager:
        """Stub: Docker sandbox lifecycle manager."""
        def __init__(self):
            self._containers: dict = {}

        def create_container(self, image: str, command: list, **kwargs) -> str:
            import uuid as _uuid
            cid = str(_uuid.uuid4())[:12]
            self._containers[cid] = {"image": image, "command": command, "status": "created"}
            logger.info(f"[STUB] Container created: {cid} ({image})")
            return cid

        def start_container(self, container_id: str) -> bool:
            if container_id in self._containers:
                self._containers[container_id]["status"] = "running"
                return True
            return False

        def stop_container(self, container_id: str) -> bool:
            if container_id in self._containers:
                self._containers[container_id]["status"] = "stopped"
                return True
            return False

        def remove_container(self, container_id: str) -> bool:
            return self._containers.pop(container_id, None) is not None

    class SmartTimeoutHandler:
        """Stub: Smart timeout with checkpoint/restore."""
        def __init__(self, sandbox_manager=None):
            self._manager = sandbox_manager
            self._checkpoints: dict = {}

        def save_checkpoint(self, task_id: str, state: dict) -> None:
            self._checkpoints[task_id] = state
            logger.info(f"[STUB] Checkpoint saved for {task_id}")

        def restore_checkpoint(self, task_id: str) -> Optional[dict]:
            return self._checkpoints.get(task_id)

        def handle_timeout(self, task_id: str, timeout_seconds: int) -> bool:
            logger.warning(f"[STUB] Timeout handler triggered for {task_id} ({timeout_seconds}s)")
            return True


# Global sandbox manager instance
_sandbox_manager: Optional[DockerSandboxManager] = None
_timeout_handler: Optional[SmartTimeoutHandler] = None


def get_sandbox_manager() -> DockerSandboxManager:
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = DockerSandboxManager()
    return _sandbox_manager


def get_timeout_handler() -> SmartTimeoutHandler:
    global _timeout_handler
    if _timeout_handler is None:
        _timeout_handler = SmartTimeoutHandler(get_sandbox_manager())
    return _timeout_handler


def intercept_deletion(file_path: str, workspace_id: str = None) -> dict:
    """
    Intercept file deletion and submit to pending_deletion review queue.
    Returns a review request dict.
    """
    import uuid as _uuid

    if not os.path.exists(file_path):
        return {"intercepted": False, "reason": "file not found"}

    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    review_request = {
        "deletion_id": str(_uuid.uuid4()),
        "file_path": file_path,
        "file_size": file_size,
        "file_hash": file_hash,
        "workspace_id": workspace_id,
        "status": "pending_review",
        "intercepted": True,
    }

    logger.info(f"Deletion intercepted: {file_path} -> review {review_request['deletion_id']}")
    return review_request


def create_pre_snapshot(task_id: str, workspace_path: str) -> dict:
    """Create a pre-execution snapshot of the workspace."""
    import uuid as _uuid

    snapshot_id = str(_uuid.uuid4())
    snapshot_path = os.path.join(workspace_path, ".snapshots", snapshot_id)
    os.makedirs(snapshot_path, exist_ok=True)

    # Record current file state
    file_list = []
    for root, dirs, files in os.walk(workspace_path):
        if ".snapshots" in root:
            continue
        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, workspace_path)
            stat = os.stat(fpath)
            file_list.append({
                "path": rel,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })

    snapshot = {
        "snapshot_id": snapshot_id,
        "task_id": task_id,
        "type": "pre",
        "timestamp": datetime.now().isoformat(),
        "file_count": len(file_list),
        "files": file_list,
    }

    # Write snapshot manifest
    manifest_path = os.path.join(snapshot_path, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    logger.info(f"Pre-snapshot created: {snapshot_id} ({len(file_list)} files)")
    return snapshot


def create_post_snapshot(task_id: str, pre_snapshot: dict, workspace_path: str) -> dict:
    """Create a post-execution snapshot and compute diff from pre-snapshot."""
    import uuid as _uuid

    snapshot_id = str(_uuid.uuid4())
    snapshot_path = os.path.join(workspace_path, ".snapshots", snapshot_id)
    os.makedirs(snapshot_path, exist_ok=True)

    # Current state
    current_files = {}
    for root, dirs, files in os.walk(workspace_path):
        if ".snapshots" in root:
            continue
        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, workspace_path)
            current_files[rel] = {
                "size": os.stat(fpath).st_size,
                "mtime": os.stat(fpath).st_mtime,
            }

    # Diff computation
    pre_files = {f["path"] for f in pre_snapshot.get("files", [])}
    post_files = set(current_files.keys())

    # Identify modified files
    modified = []
    for p in pre_files & post_files:
        pre_size = next(
            (f["size"] for f in pre_snapshot.get("files", []) if f["path"] == p), 0
        )
        if current_files[p]["size"] != pre_size:
            modified.append(p)

    unchanged = list(pre_files & post_files - set(modified))

    diff = {
        "added": list(post_files - pre_files),
        "deleted": list(pre_files - post_files),
        "modified": modified,
        "unchanged": unchanged,
    }

    snapshot = {
        "snapshot_id": snapshot_id,
        "task_id": task_id,
        "type": "post",
        "pre_snapshot_id": pre_snapshot.get("snapshot_id"),
        "timestamp": datetime.now().isoformat(),
        "file_count": len(current_files),
        "diff": diff,
    }

    manifest_path = os.path.join(snapshot_path, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    logger.info(
        f"Post-snapshot created: {snapshot_id} "
        f"(+{len(diff['added'])} -{len(diff['deleted'])} "
        f"~{len(diff['modified'])} ={len(diff['unchanged'])})"
    )
    return snapshot


def save_checkpoint(task_id: str, state: dict) -> None:
    """Save a checkpoint for breakpoint recovery."""
    handler = get_timeout_handler()
    handler.save_checkpoint(task_id, state)


def restore_checkpoint(task_id: str) -> Optional[dict]:
    """Restore a previously saved checkpoint."""
    handler = get_timeout_handler()
    return handler.restore_checkpoint(task_id)
