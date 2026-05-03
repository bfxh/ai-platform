"""Tests for sandbox_service.py"""
import pytest
import os
import sys

# Ensure the python directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.sandbox_service import (
    DockerSandboxManager,
    SmartTimeoutHandler,
    ContainerConfig,
    ContainerStatus,
)


class TestDockerSandboxManager:
    def test_init(self):
        manager = DockerSandboxManager()
        assert manager is not None

    def test_container_status_dataclass(self):
        status = ContainerStatus(
            container_id="abc123",
            name="test-container",
            image="python:3.12",
            status="running",
        )
        assert status.container_id == "abc123"
        assert status.status == "running"

    def test_container_config_defaults(self):
        config = ContainerConfig()
        assert config.image == "python:3.12-slim"
        assert config.cpu_limit == 1.0
        assert config.memory_limit_mb == 512
        assert config.gpu_enabled is False

    def test_get_container_status_nonexistent(self):
        manager = DockerSandboxManager()
        status = manager.get_container_status("nonexistent123")
        assert status is None


class TestSmartTimeoutHandler:
    def test_init(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)
        assert handler._default_start_timeout == 20

    def test_save_restore_checkpoint(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)

        task_id = "test-task-001"
        state = {"step": 3, "progress": 0.5}

        handler.save_checkpoint(task_id, state)
        restored = handler.restore_checkpoint(task_id)

        assert restored is not None
        assert restored["step"] == 3
        assert restored["progress"] == 0.5

    def test_has_checkpoint(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)

        handler.save_checkpoint("task-1", {"data": "test"})
        assert handler.has_checkpoint("task-1") is True
        assert handler.has_checkpoint("nonexistent") is False

    def test_clear_checkpoint(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)

        handler.save_checkpoint("task-1", {"data": "test"})
        handler.clear_checkpoint("task-1")
        assert handler.has_checkpoint("task-1") is False

    def test_reroute_task(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)

        result = handler.reroute_task("task-1", "container_path", "process_path")
        assert result is True

    def test_wait_for_container_start_nonexistent(self):
        manager = DockerSandboxManager()
        handler = SmartTimeoutHandler(manager)

        started, error = handler.wait_for_container_start(
            "nonexistent", timeout=1
        )
        assert started is False
        assert error is not None
        assert "failed to start" in error
