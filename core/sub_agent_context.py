"""
Sub-agent shared context for cross-agent coordination.
Extends shared_context.py patterns for sub-agent registration,
heartbeat, context broadcasts, and task board management.
"""
import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SubAgentContext:
    """Context manager for sub-agent registration and coordination."""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.context_dir = self.workspace_path / ".sub_agent_context"
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def register_agent(self, agent_id: str, agent_type: str, metadata: dict = None) -> dict:
        agent_file = self.context_dir / f"{agent_id}.json"
        agent_data = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "status": "registered",
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat(),
        }
        with open(agent_file, "w") as f:
            json.dump(agent_data, f, indent=2)
        logger.info(f"Sub-agent registered: {agent_id} ({agent_type})")
        return agent_data

    def heartbeat(self, agent_id: str) -> bool:
        agent_file = self.context_dir / f"{agent_id}.json"
        if not agent_file.exists():
            return False
        try:
            with open(agent_file, "r") as f:
                data = json.load(f)
            data["last_heartbeat"] = datetime.now().isoformat()
            data["status"] = "active"
            with open(agent_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Heartbeat failed for {agent_id}: {e}")
            return False

    def deregister_agent(self, agent_id: str) -> None:
        agent_file = self.context_dir / f"{agent_id}.json"
        if agent_file.exists():
            agent_file.unlink()
            logger.info(f"Sub-agent deregistered: {agent_id}")

    def broadcast_context(self, agent_id: str, context: dict) -> None:
        broadcast_file = self.context_dir / f"broadcast_{agent_id}.json"
        context["timestamp"] = datetime.now().isoformat()
        context["from_agent"] = agent_id
        with open(broadcast_file, "w") as f:
            json.dump(context, f, indent=2)

    def get_active_agents(self) -> list:
        agents = []
        for f in self.context_dir.glob("*.json"):
            if f.name.startswith("broadcast_"):
                continue
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    agents.append(data)
            except Exception:
                pass
        return agents


class SubAgentTaskBoard:
    """Task board for sub-agent task queue and conflict detection."""

    def __init__(self, workspace_path: str):
        self.board_dir = Path(workspace_path) / ".sub_agent_tasks"
        self.board_dir.mkdir(parents=True, exist_ok=True)

    def enqueue_task(self, task_id: str, task_data: dict) -> dict:
        task_file = self.board_dir / f"{task_id}.json"
        task_data["task_id"] = task_id
        task_data["status"] = "queued"
        task_data["created_at"] = datetime.now().isoformat()
        with open(task_file, "w") as f:
            json.dump(task_data, f, indent=2)
        return task_data

    def claim_task(self, task_id: str, agent_id: str) -> Optional[dict]:
        task_file = self.board_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        with open(task_file, "r") as f:
            data = json.load(f)
        if data.get("status") != "queued":
            return None
        data["status"] = "claimed"
        data["claimed_by"] = agent_id
        data["claimed_at"] = datetime.now().isoformat()
        with open(task_file, "w") as f:
            json.dump(data, f, indent=2)
        return data

    def complete_task(self, task_id: str, result: dict = None) -> Optional[dict]:
        task_file = self.board_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        with open(task_file, "r") as f:
            data = json.load(f)
        data["status"] = "completed"
        data["result"] = result or {}
        data["completed_at"] = datetime.now().isoformat()
        with open(task_file, "w") as f:
            json.dump(data, f, indent=2)
        return data

    def fail_task(self, task_id: str, error: str) -> Optional[dict]:
        task_file = self.board_dir / f"{task_id}.json"
        if not task_file.exists():
            return None
        with open(task_file, "r") as f:
            data = json.load(f)
        data["status"] = "failed"
        data["error"] = error
        data["failed_at"] = datetime.now().isoformat()
        with open(task_file, "w") as f:
            json.dump(data, f, indent=2)
        return data

    def detect_conflicts(self, task_id: str) -> list:
        task_file = self.board_dir / f"{task_id}.json"
        if not task_file.exists():
            return []
        with open(task_file, "r") as f:
            task = json.load(f)
        conflicts = []
        task_files = set(task.get("touched_files", []))
        for f in self.board_dir.glob("*.json"):
            if f.name == f"{task_id}.json":
                continue
            try:
                with open(f, "r") as fp:
                    other = json.load(fp)
                if other.get("status") in ("claimed", "running"):
                    other_files = set(other.get("touched_files", []))
                    overlap = task_files & other_files
                    if overlap:
                        conflicts.append({
                            "task_id": other["task_id"],
                            "overlapping_files": list(overlap),
                        })
            except Exception:
                pass
        return conflicts
