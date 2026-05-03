#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender MCP - TRAE Skill

通过自然语言控制Blender
"""

import os
import sys
import json
import subprocess
import requests
from pathlib import Path


class BlenderMCPSkill:
    """Blender MCP Skill 主类"""

    def __init__(self, config=None):
        self.config = config or {}
        self.blender_mcp_dir = Path(self.config.get("blender_mcp_dir", "/python/MCP/JM/blender_mcp"))
        self.server_url = self.config.get("server_url", "http://localhost:8400")
        self.blender_path = self.config.get("blender_path", "C:\\Program Files\Blender Foundation\Blender 4.0\blender.exe")
        self.server_script = self.blender_mcp_dir / "src" / "server.py"

    def start(self):
        """启动Blender MCP服务"""
        try:
            # 检查服务是否已经运行
            if self.status():
                return {"success": True, "message": "Blender MCP服务已经运行"}

            # 检查Blender路径是否存在
            if not Path(self.blender_path).exists():
                return {"success": False, "error": f"Blender路径不存在: {self.blender_path}"}

            # 检查服务器脚本是否存在
            if not self.server_script.exists():
                return {"success": False, "error": f"服务器脚本不存在: {self.server_script}"}

            # 启动Blender MCP服务
            subprocess.Popen([
                self.blender_path,
                "--python", str(self.server_script)
            ], creationflags=subprocess.CREATE_NEW_CONSOLE)

            return {"success": True, "message": "Blender MCP服务已启动"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self):
        """停止Blender MCP服务"""
        try:
            # 发送停止请求
            response = requests.post(self.server_url, json={"command": "shutdown"}, timeout=5)
            return {"success": True, "message": "Blender MCP服务已停止"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def status(self):
        """检查Blender MCP服务状态"""
        try:
            response = requests.get(self.server_url, timeout=2)
            return response.status_code == 200
        except:
            return False

    def restart(self):
        """重启Blender MCP服务"""
        try:
            # 停止服务
            self.stop()
            # 启动服务
            return self.start()
        except Exception as e:
            return {"success": False, "error": str(e)}


def execute(command, **kwargs):
    """执行Blender MCP命令"""
    blender_skill = BlenderMCPSkill(kwargs.get("config", {}))
    
    if command == "start":
        return blender_skill.start()
    elif command == "stop":
        return blender_skill.stop()
    elif command == "status":
        return {
            "success": True,
            "data": {
                "status": "online" if blender_skill.status() else "offline"
            }
        }
    elif command == "restart":
        return blender_skill.restart()
    else:
        return {"success": False, "error": f"未知命令: {command}"}


if __name__ == "__main__":
    # 测试代码
    blender_skill = BlenderMCPSkill()
    print(f"Blender MCP status: {'online' if blender_skill.status() else 'offline'}")
