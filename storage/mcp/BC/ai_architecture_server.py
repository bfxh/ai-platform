#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Architecture Manager - MCP Server
/python\MCP\BC\ai_architecture_server.py

提供 tools:
- check_architecture
- backup_ai
- cleanup_files
- update_github

可被 TRAE 直接调用，通过 stdio 与 MCP 协议通信。
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# 确保核心模块在路径中
sys.path.insert(0, "/python/scripts")
from arch_core import ArchitectureManager


# =============================================================================
# 日志配置（输出到文件，避免污染 stdout）
# =============================================================================
LOG_FILE = Path("/python/logs/mcp_architecture_server.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("mcp_arch")


# =============================================================================
# MCP 协议基础
# =============================================================================
class MCPServer:
    """MCP Stdio 服务器基类"""

    def __init__(self):
        self.manager = ArchitectureManager()
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用工具列表"""
        return [
            {
                "name": "check_architecture",
                "description": "检查 /python 架构完整性，验证关键目录和文件是否存在",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "backup_ai",
                "description": "备份 /python 关键目录和文件到备份目录",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "备份名称（可选，默认自动生成）",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "cleanup_files",
                "description": "清理 /python 中的临时文件、旧日志和过期备份",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dry_run": {
                            "type": "boolean",
                            "description": "仅模拟，不实际删除文件",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "update_github",
                "description": "更新 /python\GitHub 目录下的 git 仓库（执行 git pull）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repos": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "指定要更新的仓库名称列表（可选，默认全部）",
                        },
                    },
                    "required": [],
                },
            },
        ]

    def _send(self, msg: Dict[str, Any]) -> None:
        """发送 JSON-RPC 消息到 stdout"""
        data = json.dumps(msg, ensure_ascii=False)
        sys.stdout.write(data + "\n")
        sys.stdout.flush()

    def _recv(self) -> Optional[Dict[str, Any]]:
        """从 stdin 接收 JSON-RPC 消息"""
        try:
            line = sys.stdin.readline()
            if not line:
                return None
            return json.loads(line)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误: {e}")
            return None

    def _make_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        """构造成功响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    def _make_error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """构造错误响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }

    # -------------------------------------------------------------------------
    # 工具实现
    # -------------------------------------------------------------------------
    def tool_check_architecture(self, params: Dict) -> Dict[str, Any]:
        """执行架构检查"""
        logger.info("tool: check_architecture")
        result = self.manager.check_architecture()
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.to_json(indent=2),
                }
            ],
            "isError": not result.success,
        }

    def tool_backup_ai(self, params: Dict) -> Dict[str, Any]:
        """执行备份"""
        name = params.get("name")
        logger.info(f"tool: backup_ai (name={name})")
        result = self.manager.backup_ai(backup_name=name)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.to_json(indent=2),
                }
            ],
            "isError": not result.success,
        }

    def tool_cleanup_files(self, params: Dict) -> Dict[str, Any]:
        """执行清理"""
        dry_run = params.get("dry_run", False)
        logger.info(f"tool: cleanup_files (dry_run={dry_run})")
        result = self.manager.cleanup_files(dry_run=dry_run)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.to_json(indent=2),
                }
            ],
            "isError": not result.success,
        }

    def tool_update_github(self, params: Dict) -> Dict[str, Any]:
        """执行 GitHub 更新"""
        repos = params.get("repos")
        logger.info(f"tool: update_github (repos={repos})")
        result = self.manager.update_github(repos=repos)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result.to_json(indent=2),
                }
            ],
            "isError": not result.success,
        }

    # -------------------------------------------------------------------------
    # 主循环
    # -------------------------------------------------------------------------
    def run(self) -> None:
        """运行 MCP 服务器主循环"""
        logger.info("MCP Architecture Server 启动")

        while True:
            request = self._recv()
            if request is None:
                break

            request_id = request.get("id")
            method = request.get("method", "")
            params = request.get("params", {})

            logger.info(f"收到请求: method={method}, id={request_id}")

            # 初始化握手
            if method == "initialize":
                self._send(self._make_response(request_id, {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "ai-architecture-server",
                        "version": "1.0.0",
                    },
                }))
                continue

            # 工具列表
            if method == "tools/list":
                self._send(self._make_response(request_id, {"tools": self.tools}))
                continue

            # 工具调用
            if method == "tools/call":
                tool_name = params.get("name", "")
                tool_params = params.get("arguments", {})

                try:
                    if tool_name == "check_architecture":
                        result = self.tool_check_architecture(tool_params)
                    elif tool_name == "backup_ai":
                        result = self.tool_backup_ai(tool_params)
                    elif tool_name == "cleanup_files":
                        result = self.tool_cleanup_files(tool_params)
                    elif tool_name == "update_github":
                        result = self.tool_update_github(tool_params)
                    else:
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        {"error": f"未知工具: {tool_name}"},
                                        ensure_ascii=False,
                                    ),
                                }
                            ],
                            "isError": True,
                        }

                    self._send(self._make_response(request_id, result))

                except Exception as e:
                    logger.exception(f"工具执行失败: {tool_name}")
                    self._send(self._make_error(request_id, -32603, str(e)))
                continue

            # 其他方法返回空结果
            self._send(self._make_response(request_id, {}))

        logger.info("MCP Architecture Server 停止")


# =============================================================================
# 入口
# =============================================================================
def main():
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
