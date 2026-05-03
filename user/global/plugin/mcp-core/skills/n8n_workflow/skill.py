#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill

try:
    import requests
except ImportError:
    requests = None


class N8nWorkflow(Skill):
    name = "n8n_workflow"
    description = "n8n 工作流自动化 - 400+ 集成的工作流引擎"
    version = "2.0.0"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_base = os.getenv("N8N_API_BASE", "http://localhost:5678/api/v1")
        self.api_key = os.getenv("N8N_API_KEY", "")
        self.n8n_path = Path(os.getenv("N8N_PATH", "/python/downloads/all_skills/n8n"))
        self.process = None

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    def _is_server_running(self):
        if not requests:
            return False
        try:
            r = requests.get(f"{self.api_base}/workflows", headers=self._headers(), timeout=3)
            return r.status_code in (200, 401)
        except:
            return False

    def execute(self, action: str, params: Dict) -> Dict:
        actions = {
            "start_n8n": self._start_n8n,
            "stop_n8n": self._stop_n8n,
            "check_status": self._check_status,
            "create_workflow": self._create_workflow,
            "execute_workflow": self._execute_workflow,
            "list_workflows": self._list_workflows,
            "get_workflow": self._get_workflow,
        }
        fn = actions.get(action)
        if fn:
            return fn(params)
        return {"success": False, "error": f"�知动�: {action}, ��: {list(actions.keys())}"}

    def _check_status(self, params: Dict) -> Dict:
        running = self._is_server_running()
        return {
            "success": True,
            "server_running": running,
            "api_base": self.api_base,
            "api_key_set": bool(self.api_key),
            "n8n_path_exists": self.n8n_path.exists()
        }

    def _start_n8n(self, params: Dict) -> Dict:
        if self._is_server_running():
            return {"success": True, "message": "n8n 已在运�"}

        port = params.get("port", "5678")

        try:
            env = os.environ.copy()
            env["N8N_PORT"] = port
            if self.api_key:
                env["N8N_API_KEY"] = self.api_key

            self.process = subprocess.Popen(
                ["%USERPROFILE%/miniconda3/python.exe", "-m", "n8n", "start"],
                env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(8)
            return {"success": True, "message": f"n8n �动中: http://localhost:{port}"}
        except FileNotFoundError:
            return {"success": False, "error": "n8n �安�", "hint": "npm install -g n8n"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_n8n(self, params: Dict = None) -> Dict:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            return {"success": True, "message": "n8n 已停�"}
        return {"success": True, "message": "n8n �运�"}

    def _create_workflow(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "n8n 服务�运�"}

        name = params.get("name")
        nodes = params.get("nodes", [])
        connections = params.get("connections", {})

        if not name:
            return {"success": False, "error": "缺少工作流名�"}

        try:
            payload = {
                "name": name,
                "nodes": nodes if nodes else [{"parameters": {}, "name": "Start", "type": "n8n-nodes-base.manualTrigger", "position": [250, 300]}],
                "connections": connections,
                "active": False
            }
            r = requests.post(f"{self.api_base}/workflows", headers=self._headers(), json=payload, timeout=10)
            if r.status_code in (200, 201):
                data = r.json()
                return {"success": True, "workflow_id": data.get("id"), "name": name}
            return {"success": False, "error": f"API 返回 {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_workflow(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "n8n 服务�运�"}

        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {"success": False, "error": "缺少工作流ID"}

        try:
            r = requests.post(f"{self.api_base}/workflows/{workflow_id}/activate", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "workflow_id": workflow_id, "status": "activated"}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_workflows(self, params: Dict = None) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "n8n 服务�运�"}
        try:
            r = requests.get(f"{self.api_base}/workflows", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "workflows": r.json().get("data", [])}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_workflow(self, params: Dict) -> Dict:
        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {"success": False, "error": "缺少工作流ID"}
        if not requests or not self._is_server_running():
            return {"success": False, "error": "n8n 服务�运�"}
        try:
            r = requests.get(f"{self.api_base}/workflows/{workflow_id}", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "workflow": r.json()}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    skill = N8nWorkflow()
    print("n8n 工作流技� v2.0")
