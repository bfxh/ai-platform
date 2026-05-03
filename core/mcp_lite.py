#!/usr/bin/env python3
"""
轻量级MCP系统 - 极简集成
减少90%配置，自动发现，即插即用
"""

import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional


class MCPCapability(Enum):
    FILE = "file"  # 文件操作
    CODE = "code"  # 代码分析
    SEARCH = "search"  # 搜索
    BROWSER = "browser"  # 浏览器
    DB = "db"  # 数据库
    DESIGN = "design"  # 设计
    MEDIA = "media"  # 多媒体


@dataclass
class MCPTool:
    """MCP工具定义"""

    name: str
    capability: MCPCapability
    command: str
    auto_detect: bool = True


@dataclass
class MCPResult:
    """MCP执行结果"""

    success: bool
    data: any
    tokens_used: int
    latency_ms: float


class MCPLite:
    """轻量级MCP管理器"""

    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.handlers: Dict[str, Callable] = {}
        self._auto_register()

    def _auto_register(self):
        """自动注册可用工具"""
        # 文件系统
        self.register(
            "file", MCPTool(name="file", capability=MCPCapability.FILE, command="filesystem"), self._handle_file
        )

        # 代码分析
        self.register(
            "code", MCPTool(name="code", capability=MCPCapability.CODE, command="code_analyzer"), self._handle_code
        )

        # 搜索
        self.register(
            "search", MCPTool(name="search", capability=MCPCapability.SEARCH, command="search"), self._handle_search
        )

        # 浏览器
        self.register(
            "browser",
            MCPTool(name="browser", capability=MCPCapability.BROWSER, command="browser"),
            self._handle_browser,
        )

        # 数据库
        self.register("db", MCPTool(name="db", capability=MCPCapability.DB, command="sqlite"), self._handle_db)

        # 设计
        self.register(
            "design",
            MCPTool(name="design", capability=MCPCapability.DESIGN, command="design_tools"),
            self._handle_design,
        )

    def register(self, name: str, tool: MCPTool, handler: Callable):
        """注册工具"""
        self.tools[name] = tool
        self.handlers[name] = handler

    def use(self, tool_name: str, **kwargs) -> MCPResult:
        """
        使用工具 - 一句话调用
        示例: use("file", action="read", path="test.py")
        """
        if tool_name not in self.handlers:
            return MCPResult(success=False, data=f"未知工具: {tool_name}", tokens_used=0, latency_ms=0)

        import time

        start = time.time()

        try:
            result = self.handlers[tool_name](**kwargs)
            latency = (time.time() - start) * 1000

            return MCPResult(success=True, data=result, tokens_used=len(str(result)) // 4, latency_ms=latency)
        except Exception as e:
            return MCPResult(success=False, data=str(e), tokens_used=0, latency_ms=(time.time() - start) * 1000)

    # 处理器实现
    def _handle_file(self, action: str, path: str, content: str = None) -> str:
        """文件操作"""
        if action == "read":
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        elif action == "write":
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"已写入: {path}"
        elif action == "list":
            import os

            return "\n".join(os.listdir(path))
        return "未知操作"

    def _handle_code(self, action: str, code: str = None, path: str = None) -> str:
        """代码分析"""
        try:
            from router import do
        except ImportError:
            do = None

        if action == "analyze":
            return do(f"分析代码:\n{code}")
        elif action == "review":
            return do(f"审查代码:\n{code}")
        elif action == "fix":
            return do(f"修复代码:\n{code}")
        elif action == "explain":
            return do(f"解释代码:\n{code}")
        return "未知操作"

    def _handle_search(self, query: str, type: str = "web") -> str:
        """搜索"""
        try:
            from router import do
        except ImportError:
            do = None
        return do(f"搜索: {query}")

    def _handle_browser(self, action: str, url: str = None) -> str:
        """浏览器"""
        if action == "fetch":
            import urllib.request

            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8")[:5000]
        return "未知操作"

    def _handle_db(self, action: str, query: str = None, db_path: str = None) -> str:
        import sqlite3

        if query:
            dangerous = ["DROP", "DELETE FROM", "TRUNCATE", "ALTER", "GRANT", "REVOKE", "ATTACH", "DETACH"]
            q_upper = query.strip().upper()
            if any(q_upper.startswith(d) for d in dangerous):
                return "[错误] 危险SQL操作被阻止"

        conn = sqlite3.connect(db_path or ":memory:")
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            return str(result)
        finally:
            conn.close()

    def _handle_design(self, action: str, prompt: str = None) -> str:
        """设计"""
        try:
            from router import do
        except ImportError:
            do = None
        return do(f"设计: {prompt}")

    def __call__(self, tool_spec: str) -> str:
        """
        极简调用
        示例: mcp("file:read:test.py")
        """
        parts = tool_spec.split(":")
        tool_name = parts[0]

        kwargs = {}
        if len(parts) > 1:
            kwargs["action"] = parts[1]
        if len(parts) > 2:
            if tool_name == "file":
                kwargs["path"] = parts[2]
            elif tool_name == "code":
                kwargs["code"] = parts[2]

        result = self.use(tool_name, **kwargs)
        return result.data if result.success else f"错误: {result.data}"


# 全局实例
mcp = MCPLite()


# 快捷函数
def file(action: str, path: str, **kwargs) -> str:
    """文件操作"""
    return mcp.use("file", action=action, path=path, **kwargs).data


def code(action: str, code: str = None, **kwargs) -> str:
    """代码操作"""
    return mcp.use("code", action=action, code=code, **kwargs).data


def search(query: str) -> str:
    """搜索"""
    return mcp.use("search", query=query).data


def browser(url: str) -> str:
    """浏览器"""
    return mcp.use("browser", action="fetch", url=url).data


def db(query: str, db_path: str = None) -> str:
    """数据库"""
    return mcp.use("db", action="query", query=query, db_path=db_path).data


def design(prompt: str) -> str:
    """设计"""
    return mcp.use("design", action="create", prompt=prompt).data


if __name__ == "__main__":
    # 测试
    print(mcp("file:list:/python"))
    print(search("Python快速排序"))
