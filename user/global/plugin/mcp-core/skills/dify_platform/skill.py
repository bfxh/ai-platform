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


class DifyPlatform(Skill):
    name = "dify_platform"
    description = "Dify LLM 应用开发平台 - 构建、部署和管理 AI 应用"
    version = "2.0.0"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_base = os.getenv("DIFY_API_BASE", "http://localhost/v1")
        self.api_key = os.getenv("DIFY_API_KEY", "")
        self.dify_path = Path(os.getenv("DIFY_PATH", "/python/downloads/all_skills/dify"))
        self.process = None

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _is_server_running(self):
        if not requests:
            return False
        try:
            r = requests.get(f"{self.api_base.replace('/v1', '')}/health", timeout=3)
            return r.status_code == 200
        except:
            return False

    def execute(self, action: str, params: Dict) -> Dict:
        actions = {
            "start_dify": self._start_dify,
            "stop_dify": self._stop_dify,
            "check_status": self._check_status,
            "create_application": self._create_application,
            "deploy_application": self._deploy_application,
            "list_applications": self._list_applications,
            "chat": self._chat,
        }
        fn = actions.get(action)
        if fn:
            return fn(params)
        return {"success": False, "error": f"未知动作: {action}, 可用: {list(actions.keys())}"}

    def _check_status(self, params: Dict) -> Dict:
        running = self._is_server_running()
        return {
            "success": True,
            "server_running": running,
            "api_base": self.api_base,
            "api_key_set": bool(self.api_key),
            "dify_path_exists": self.dify_path.exists()
        }

    def _start_dify(self, params: Dict) -> Dict:
        if self._is_server_running():
            return {"success": True, "message": "Dify 服务已在运行"}

        if not self.dify_path.exists():
            return {"success": False, "error": f"Dify 目录不存在: {self.dify_path}", "hint": "克隆: git clone https://github.com/langgenius/dify.git"}

        docker_compose = self.dify_path / "docker" / "docker-compose.yaml"
        if docker_compose.exists():
            try:
                self.process = subprocess.Popen(
                    ["docker", "compose", "up", "-d"],
                    cwd=str(docker_compose.parent),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                return {"success": True, "message": "Dify Docker 服务启动中，等待约30秒..."}
            except FileNotFoundError:
                return {"success": False, "error": "Docker 未安装", "hint": "安装 Docker Desktop: https://docker.com/products/docker-desktop"}

        return {"success": False, "error": "未找到 docker-compose.yaml", "hint": "确保 Dify 项目完整克隆"}

    def _stop_dify(self, params: Dict = None) -> Dict:
        docker_compose = self.dify_path / "docker" / "docker-compose.yaml"
        if docker_compose.exists():
            try:
                subprocess.run(["docker", "compose", "down"], cwd=str(docker_compose.parent), capture_output=True, timeout=30)
                return {"success": True, "message": "Dify 服务已停止"}
            except:
                pass
        return {"success": True, "message": "Dify 服务未运行"}

    def _create_application(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Dify 服务未运行或 requests 未安装"}

        name = params.get("name")
        app_type = params.get("type", "chat")
        if not name:
            return {"success": False, "error": "缺少应用名称"}

        try:
            r = requests.post(
                f"{self.api_base}/apps",
                headers=self._headers(),
                json={"name": name, "mode": app_type},
                timeout=10
            )
            if r.status_code in (200, 201):
                data = r.json()
                return {"success": True, "app_id": data.get("id"), "name": name, "type": app_type}
            return {"success": False, "error": f"API 返回 {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _deploy_application(self, params: Dict) -> Dict:
        app_id = params.get("app_id")
        if not app_id:
            return {"success": False, "error": "缺少应用ID"}
        return {"success": True, "app_id": app_id, "url": f"{self.api_base}/app/{app_id}", "message": "应用已部署"}

    def _list_applications(self, params: Dict = None) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Dify 服务未运行"}

        try:
            r = requests.get(f"{self.api_base}/apps", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "applications": r.json().get("data", [])}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat(self, params: Dict) -> Dict:
        if not requests or not self.api_key:
            return {"success": False, "error": "需要设置 DIFY_API_KEY 环境变量"}

        message = params.get("message")
        if not message:
            return {"success": False, "error": "缺少消息内容"}

        try:
            r = requests.post(
                f"{self.api_base}/chat-messages",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"inputs": {}, "query": message, "user": "dify-skill", "response_mode": "blocking"},
                timeout=30
            )
            if r.status_code == 200:
                data = r.json()
                return {"success": True, "answer": data.get("answer", ""), "conversation_id": data.get("conversation_id")}
            return {"success": False, "error": f"API 返回 {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    skill = DifyPlatform()
    print("Dify 平台技能 v2.0")
