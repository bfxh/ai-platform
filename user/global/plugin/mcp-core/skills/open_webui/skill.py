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


class OpenWebUI(Skill):
    name = "open_webui"
    description = "Open WebUI - AI 聊天界面，支� Ollama/OpenAI 兼� API"
    version = "2.0.0"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_base = os.getenv("WEBUI_API_BASE", "http://localhost:3000/api/v1")
        self.api_key = os.getenv("WEBUI_API_KEY", "")
        self.webui_path = Path(os.getenv("WEBUI_PATH", "/python/downloads/all_skills/open-webui"))
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
            r = requests.get(f"{self.api_base}/configs", headers=self._headers(), timeout=3)
            return r.status_code in (200, 401)
        except:
            return False

    def execute(self, action: str, params: Dict) -> Dict:
        actions = {
            "start_webui": self._start_webui,
            "stop_webui": self._stop_webui,
            "check_status": self._check_status,
            "create_chat": self._create_chat,
            "send_message": self._send_message,
            "list_chats": self._list_chats,
            "list_models": self._list_models,
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
            "webui_path_exists": self.webui_path.exists()
        }

    def _start_webui(self, params: Dict) -> Dict:
        if self._is_server_running():
            return {"success": True, "message": "Open WebUI 已在运�"}

        port = params.get("port", "3000")

        try:
            self.process = subprocess.Popen(
                ["%USERPROFILE%/miniconda3/python.exe", "-m", "open_webui", "--port", port],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(5)
            return {"success": True, "message": f"Open WebUI �动中: http://localhost:{port}"}
        except FileNotFoundError:
            return {"success": False, "error": "open-webui �安�", "hint": "pip install open-webui"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _stop_webui(self, params: Dict = None) -> Dict:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            return {"success": True, "message": "Open WebUI 已停�"}
        return {"success": True, "message": "Open WebUI �运�"}

    def _list_models(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Open WebUI 服务�运�"}
        try:
            r = requests.get(f"{self.api_base}/models", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "models": r.json().get("data", [])}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_chat(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Open WebUI 服务�运�"}

        title = params.get("title", "新聊�")
        model = params.get("model", "gpt-4")

        try:
            r = requests.post(
                f"{self.api_base}/chats/new",
                headers=self._headers(),
                json={"chat": {"title": title, "models": [model]}},
                timeout=10
            )
            if r.status_code in (200, 201):
                data = r.json()
                return {"success": True, "chat_id": data.get("id"), "title": title, "model": model}
            return {"success": False, "error": f"API 返回 {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _send_message(self, params: Dict) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Open WebUI 服务�运�"}

        chat_id = params.get("chat_id")
        message = params.get("message")
        model = params.get("model", "gpt-4")

        if not message:
            return {"success": False, "error": "缺少消息内�"}

        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            if chat_id:
                payload["chat_id"] = chat_id

            r = requests.post(
                f"{self.api_base}/chats/completions",
                headers=self._headers(),
                json=payload,
                timeout=60
            )
            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                answer = choices[0]["message"]["content"] if choices else ""
                return {"success": True, "chat_id": chat_id, "response": answer, "model": model}
            return {"success": False, "error": f"API 返回 {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_chats(self, params: Dict = None) -> Dict:
        if not requests or not self._is_server_running():
            return {"success": False, "error": "Open WebUI 服务�运�"}
        try:
            r = requests.get(f"{self.api_base}/chats", headers=self._headers(), timeout=10)
            if r.status_code == 200:
                return {"success": True, "chats": r.json()}
            return {"success": False, "error": f"API 返回 {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    skill = OpenWebUI()
    print("Open WebUI �� v2.0")
