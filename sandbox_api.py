"""
FastAPI sandbox API server.
Provides REST endpoints for container lifecycle management.
Runs on port 8081 by default.
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.sandbox_service import DockerSandboxManager, ContainerConfig, SmartTimeoutHandler

app = FastAPI(title="Multica Sandbox API", version="1.0.0")
sandbox = DockerSandboxManager()
timeout_handler = SmartTimeoutHandler(sandbox)


class CreateContainerRequest(BaseModel):
    name: str
    image: str = "python:3.12-slim"
    cpu_limit: float = 1.0
    memory_limit_mb: int = 512
    gpu_enabled: bool = False
    env: dict = {}
    mounts: list = []


class ExecRequest(BaseModel):
    command: list
    timeout: int = 300


@app.post("/containers")
async def create_container(req: CreateContainerRequest):
    config = ContainerConfig(
        image=req.image,
        cpu_limit=req.cpu_limit,
        memory_limit_mb=req.memory_limit_mb,
        gpu_enabled=req.gpu_enabled,
        env=req.env,
        mounts=req.mounts,
    )
    status = sandbox.create_container(req.name, config)
    if status.error:
        raise HTTPException(status_code=500, detail=status.error)
    return status.__dict__


@app.get("/containers/{container_id}/status")
async def get_container_status(container_id: str):
    status = sandbox.get_container_status(container_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Container not found")
    return status.__dict__


@app.post("/containers/{container_id}/start")
async def start_container(container_id: str):
    ok = sandbox.start_container(container_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to start container")
    started, error = timeout_handler.wait_for_container_start(container_id)
    if not started:
        raise HTTPException(status_code=408, detail=error)
    return {"status": "running", "container_id": container_id}


@app.post("/containers/{container_id}/stop")
async def stop_container(container_id: str, timeout: int = 10):
    sandbox.stop_container(container_id, timeout)
    return {"status": "stopped", "container_id": container_id}


@app.post("/containers/{container_id}/exec")
async def exec_in_container(container_id: str, req: ExecRequest):
    exit_code, stdout, stderr = sandbox.exec_command(
        container_id, req.command, req.timeout
    )
    return {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}


@app.delete("/containers/{container_id}")
async def delete_container(container_id: str):
    ok = sandbox.cleanup_container(container_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete container")
    return {"status": "deleted", "container_id": container_id}


@app.get("/containers")
async def list_containers(name_filter: Optional[str] = None):
    containers = sandbox.list_containers(name_filter)
    return [c.__dict__ for c in containers if c is not None]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
