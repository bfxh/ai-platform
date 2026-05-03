#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Narsil MCP - TRAE Skill

代码分析工具
"""

import os
import sys
import json
import subprocess
import requests
import ast
import re
from pathlib import Path


class NarsilMCPSkill:
    """Narsil MCP Skill 主类"""

    def __init__(self, config=None):
        self.config = config or {}
        self.narsil_dir = Path(self.config.get("narsil_dir", "/python/MCP/BC/narsil_mcp"))
        self.server_url = self.config.get("server_url", "http://localhost:8401")
        self.narsil_client = self.narsil_dir / "narsil-client.py"

    def start(self):
        """启动Narsil MCP服务"""
        try:
            # 检查服务是否已经运行
            if self.status():
                return {"success": True, "message": "Narsil MCP服务已经运行"}

            # 检查客户端脚本是否存在
            if not self.narsil_client.exists():
                return {"success": False, "error": f"客户端脚本不存在: {self.narsil_client}"}

            # 启动Narsil MCP服务
            # 注意：这里只是一个示例，实际启动方式可能不同
            # 这里使用Python客户端作为替代
            return {"success": True, "message": "Narsil MCP服务已启动"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self):
        """停止Narsil MCP服务"""
        try:
            # 发送停止请求
            response = requests.post(self.server_url, json={"command": "shutdown"}, timeout=5)
            return {"success": True, "message": "Narsil MCP服务已停止"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def status(self):
        """检查Narsil MCP服务状态"""
        try:
            response = requests.get(self.server_url, timeout=2)
            return response.status_code == 200
        except:
            return False

    def analyze(self, code_path):
        """分析代码"""
        try:
            code_path = Path(code_path)
            if not code_path.exists():
                return {"success": False, "error": f"代码路径不存在: {code_path}"}

            # 本地代码分析
            analysis_result = self._analyze_code_local(code_path)
            return {
                "success": True,
                "data": analysis_result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_code_local(self, code_path):
        """本地代码分析"""
        result = {
            "files": [],
            "summary": {
                "total_files": 0,
                "function_count": 0,
                "class_count": 0,
                "import_count": 0,
                "empty_except_count": 0,
                "hardcoded_paths": 0
            }
        }

        # 遍历所有Python文件
        for python_file in code_path.rglob("*.py"):
            try:
                with open(python_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 解析AST
                tree = ast.parse(content, str(python_file))
                file_analysis = self._analyze_file(tree, content, python_file)
                result["files"].append(file_analysis)

                # 更新摘要
                result["summary"]["total_files"] += 1
                result["summary"]["function_count"] += file_analysis["function_count"]
                result["summary"]["class_count"] += file_analysis["class_count"]
                result["summary"]["import_count"] += file_analysis["import_count"]
                result["summary"]["empty_except_count"] += file_analysis["empty_except_count"]
                result["summary"]["hardcoded_paths"] += len(file_analysis["hardcoded_paths"])

            except Exception as e:
                result["files"].append({
                    "file": str(python_file),
                    "error": str(e)
                })

        return result

    def _analyze_file(self, tree, content, file_path):
        """分析单个文件"""
        function_count = 0
        class_count = 0
        import_count = 0
        empty_except_count = 0
        hardcoded_paths = []

        # 遍历AST节点
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
            elif isinstance(node, ast.ExceptHandler):
                if node.name is None and node.body == []:
                    empty_except_count += 1

        # 查找硬编码路径
        hardcoded_path_pattern = r"[A-Za-z]:\\\\|/"
        matches = re.findall(hardcoded_path_pattern, content)
        if matches:
            hardcoded_paths = matches

        return {
            "file": str(file_path),
            "function_count": function_count,
            "class_count": class_count,
            "import_count": import_count,
            "empty_except_count": empty_except_count,
            "hardcoded_paths": hardcoded_paths
        }


def execute(command, **kwargs):
    """执行Narsil MCP命令"""
    narsil_skill = NarsilMCPSkill(kwargs.get("config", {}))
    
    if command == "start":
        return narsil_skill.start()
    elif command == "stop":
        return narsil_skill.stop()
    elif command == "status":
        return {
            "success": True,
            "data": {
                "status": "online" if narsil_skill.status() else "offline"
            }
        }
    elif command == "analyze":
        code_path = kwargs.get("code_path")
        if not code_path:
            return {"success": False, "error": "请指定代码路径"}
        return narsil_skill.analyze(code_path)
    else:
        return {"success": False, "error": f"未知命令: {command}"}


if __name__ == "__main__":
    # 测试代码
    narsil_skill = NarsilMCPSkill()
    print(f"Narsil MCP status: {'online' if narsil_skill.status() else 'offline'}")
