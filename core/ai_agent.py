#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Agent系统 - 集成learn-claude-code的Agent架构
基于: https://github.com/shareAI-lab/learn-claude-code

核心架构:
1. Agent Loop - 模型与工具的核心循环
2. Tool System - 可扩展的工具系统
3. Subagent - 子Agent隔离上下文
4. Task System - 任务管理
5. Context Management - 上下文压缩
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))
# tools dir may not exist, use core dir as fallback
_tools_dir = _BASE_DIR.parent / "tools"
if _tools_dir.exists() and str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

try:
    from ai_adapter import ChatRequest, Message, UnifiedAI
except ImportError:
    UnifiedAI = None
# [FIXED] 原导入: from ai_config import get_config
try:
    from ai_config import get_config
except ImportError:
    get_config = None

try:
    from core.secure_utils import safe_exec_command, CommandNotAllowedError
except ImportError:
    safe_exec_command = None
    CommandNotAllowedError = PermissionError


@dataclass
class Tool:
    """工具定义"""

    name: str
    description: str
    parameters: Dict
    handler: Callable = None


@dataclass
class ToolCall:
    """工具调用"""

    name: str
    arguments: Dict
    id: str = ""


@dataclass
class AgentContext:
    """Agent上下文"""

    messages: List[Message] = field(default_factory=list)
    tools: List[Tool] = field(default_factory=list)
    max_iterations: int = 50
    current_iteration: int = 0
    workspace: Path = field(default_factory=lambda: Path.cwd())


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """注册内置工具"""
        # Bash工具
        self.register(
            Tool(
                name="bash",
                description="运行shell命令",
                parameters={
                    "type": "object",
                    "properties": {"command": {"type": "string", "description": "要执行的命令"}},
                    "required": ["command"],
                },
                handler=self._run_bash,
            )
        )

        # 文件读取
        self.register(
            Tool(
                name="read",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "文件路径"}},
                    "required": ["path"],
                },
                handler=self._run_read,
            )
        )

        # 文件写入
        self.register(
            Tool(
                name="write",
                description="写入文件",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "content": {"type": "string", "description": "文件内容"},
                    },
                    "required": ["path", "content"],
                },
                handler=self._run_write,
            )
        )

        # 文件编辑
        self.register(
            Tool(
                name="edit",
                description="编辑文件（查找替换）",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "文件路径"},
                        "old_string": {"type": "string", "description": "要替换的内容"},
                        "new_string": {"type": "string", "description": "新内容"},
                    },
                    "required": ["path", "old_string", "new_string"],
                },
                handler=self._run_edit,
            )
        )

        # 列出目录
        self.register(
            Tool(
                name="list",
                description="列出目录内容",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "目录路径", "default": "."}},
                    "required": [],
                },
                handler=self._run_list,
            )
        )

        # 搜索文件
        self.register(
            Tool(
                name="search",
                description="搜索文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "搜索模式"},
                        "path": {"type": "string", "description": "搜索路径", "default": "."},
                    },
                    "required": ["pattern"],
                },
                handler=self._run_search,
            )
        )

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """列出所有工具"""
        return list(self.tools.values())

    def to_openai_format(self) -> List[Dict]:
        """转换为OpenAI工具格式"""
        return [
            {
                "type": "function",
                "function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters},
            }
            for tool in self.tools.values()
        ]

    # -- 工具实现 --

    def _safe_path(self, path: str, workspace: Path) -> Path:
        """安全检查路径"""
        p = (workspace / path).resolve()
        if not str(p).startswith(str(workspace)):
            raise ValueError(f"路径越界: {path}")
        return p

    def _run_bash(self, command: str, workspace: Path) -> str:
        """运行bash命令"""
        try:
            if safe_exec_command is not None:
                result = safe_exec_command(command, cwd=str(workspace), timeout=120)
                output = (result.stdout + result.stderr).strip()
            else:
                result = subprocess.run(command, shell=False, cwd=workspace, capture_output=True, text=True, timeout=120)
                output = (result.stdout + result.stderr).strip()
            return output[:50000] if output else "(无输出)"
        except CommandNotAllowedError as e:
            return f"[错误] 命令被阻止: {e}"
        except subprocess.TimeoutExpired:
            return "[错误] 命令超时"
        except Exception as e:
            return f"[错误] {e}"

    def _run_read(self, path: str, workspace: Path) -> str:
        """读取文件"""
        try:
            file_path = self._safe_path(path, workspace)
            if not file_path.exists():
                return f"[错误] 文件不存在: {path}"
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content[:100000]  # 限制大小
        except Exception as e:
            return f"[错误] {e}"

    def _run_write(self, path: str, content: str, workspace: Path) -> str:
        """写入文件"""
        try:
            file_path = self._safe_path(path, workspace)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[成功] 已写入: {path}"
        except Exception as e:
            return f"[错误] {e}"

    def _run_edit(self, path: str, old_string: str, new_string: str, workspace: Path) -> str:
        """编辑文件"""
        try:
            file_path = self._safe_path(path, workspace)
            if not file_path.exists():
                return f"[错误] 文件不存在: {path}"

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if old_string not in content:
                return f"[错误] 未找到要替换的内容"

            new_content = content.replace(old_string, new_string, 1)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"[成功] 已编辑: {path}"
        except Exception as e:
            return f"[错误] {e}"

    def _run_list(self, path: str = ".", workspace: Path = None) -> str:
        """列出目录"""
        try:
            dir_path = self._safe_path(path, workspace or Path.cwd())
            if not dir_path.exists():
                return f"[错误] 目录不存在: {path}"

            items = []
            for item in dir_path.iterdir():
                item_type = "📁" if item.is_dir() else "📄"
                items.append(f"{item_type} {item.name}")

            return "\n".join(items) if items else "(空目录)"
        except Exception as e:
            return f"[错误] {e}"

    def _run_search(self, pattern: str, path: str = ".", workspace: Path = None) -> str:
        """搜索文件"""
        try:
            search_path = self._safe_path(path, workspace or Path.cwd())
            matches = []

            for root, dirs, files in os.walk(search_path):
                # 跳过隐藏目录和node_modules等
                dirs[:] = [
                    d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "venv"]
                ]

                for file in files:
                    if file.startswith("."):
                        continue
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            if pattern in content:
                                lines = content.split("\n")
                                for i, line in enumerate(lines, 1):
                                    if pattern in line:
                                        matches.append(f"{file_path}:{i}: {line.strip()}")
                                        if len(matches) >= 20:  # 限制结果数
                                            break
                    except Exception:
                        pass

                    if len(matches) >= 20:
                        break

                if len(matches) >= 20:
                    break

            return "\n".join(matches) if matches else "(未找到匹配)"
        except Exception as e:
            return f"[错误] {e}"


class Agent:
    """
    AI Agent - 核心Agent类

    核心循环:
        while stop_reason == "tool_use":
            response = LLM(messages, tools)
            execute tools
            append results

    用法:
        agent = Agent()
        result = agent.run("帮我创建一个Python项目")
    """

    def __init__(self, provider: str = None, model: str = None, workspace: str = None, system_prompt: str = None):
        """
        初始化Agent

        Args:
            provider: AI提供商
            model: 模型名称
            workspace: 工作目录
            system_prompt: 系统提示词
        """
        self.ai = UnifiedAI(provider=provider, model=model)
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.tool_registry = ToolRegistry()
        self.context = AgentContext(workspace=self.workspace)

        self.system_prompt = system_prompt or f"""你是一个编程Agent，工作目录是 {self.workspace}。
使用工具来完成任务。行动，不要解释。

可用工具:
- bash: 运行shell命令
- read: 读取文件
- write: 写入文件
- edit: 编辑文件
- list: 列出目录
- search: 搜索文件

规则:
1. 一次只调用一个工具
2. 等待工具结果后再进行下一步
3. 任务完成后直接输出结果，不要额外解释
"""

        self._setup_context()

    def _setup_context(self):
        """设置初始上下文"""
        self.context.messages = [Message(role="system", content=self.system_prompt)]
        self.context.tools = self.tool_registry.list_tools()

    def run(self, task: str, max_iterations: int = 50) -> str:
        """
        运行Agent完成任务

        Args:
            task: 任务描述
            max_iterations: 最大迭代次数

        Returns:
            最终结果
        """
        print(f"🤖 Agent开始任务: {task[:50]}...")
        print(f"   工作目录: {self.workspace}")
        print(f"   模型: {self.ai.provider}/{self.ai.model}")
        print("-" * 60)

        # 添加用户任务
        self.context.messages.append(Message(role="user", content=task))
        self.context.max_iterations = max_iterations

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            self.context.current_iteration = iteration

            # 调用AI
            try:
                response = self._call_ai()
            except Exception as e:
                print(f"❌ AI调用失败: {e}")
                return f"[错误] {e}"

            # 检查是否需要使用工具
            tool_calls = self._parse_tool_calls(response)

            if not tool_calls:
                # 没有工具调用，任务完成
                print(f"✅ 任务完成 ({iteration} 轮)")
                return response

            # 执行工具
            for tool_call in tool_calls:
                print(f"🔧 执行工具: {tool_call.name}")
                result = self._execute_tool(tool_call)

                # 添加工具结果到上下文
                self.context.messages.append(Message(role="assistant", content=response))
                self.context.messages.append(Message(role="user", content=f"[工具结果] {tool_call.name}: {result}"))

        print(f"⚠️ 达到最大迭代次数 ({max_iterations})")
        return "[错误] 任务超时"

    def _call_ai(self) -> str:
        """调用AI"""
        # 构建提示词（简化版，实际应该使用工具调用API）
        tools_desc = "\n".join([f"{tool.name}: {tool.description}" for tool in self.context.tools])

        messages_text = "\n".join([f"{msg.role}: {msg.content}" for msg in self.context.messages])

        prompt = f"""{messages_text}

可用工具:
{tools_desc}

如果需要使用工具，请按以下格式回复:
TOOL: <工具名>
ARGS: <JSON格式的参数>

如果不需要工具，直接回复结果。
"""

        return self.ai.chat(prompt, keep_history=False)

    def _parse_tool_calls(self, response: str) -> List[ToolCall]:
        """解析工具调用"""
        tool_calls = []

        # 解析 TOOL: 和 ARGS: 格式
        tool_match = re.search(r"TOOL:\s*(\w+)", response)
        args_match = re.search(r"ARGS:\s*(\{[^}]+\})", response)

        if tool_match:
            tool_name = tool_match.group(1)
            args = {}
            if args_match:
                try:
                    args = json.loads(args_match.group(1))
                except Exception:
                    pass

            tool_calls.append(ToolCall(name=tool_name, arguments=args))

        return tool_calls

    def _execute_tool(self, tool_call: ToolCall) -> str:
        """执行工具"""
        tool = self.tool_registry.get(tool_call.name)
        if not tool:
            return f"[错误] 未知工具: {tool_call.name}"

        if not tool.handler:
            return f"[错误] 工具未实现: {tool_call.name}"

        try:
            return tool.handler(workspace=self.workspace, **tool_call.arguments)
        except Exception as e:
            return f"[错误] 工具执行失败: {e}"

    def add_tool(self, tool: Tool):
        """添加自定义工具"""
        self.tool_registry.register(tool)
        self.context.tools = self.tool_registry.list_tools()


class Subagent:
    """
    子Agent - 用于隔离上下文

    用法:
        sub = Subagent(parent_agent)
        result = sub.run("完成子任务")
    """

    def __init__(self, parent: Agent, task_description: str = ""):
        self.parent = parent
        self.task_description = task_description
        self.agent = Agent(
            provider=parent.ai.provider,
            model=parent.ai.model,
            workspace=parent.workspace,
            system_prompt=f"你是一个子Agent。{task_description}\n完成任务后，总结你的发现。",
        )

    def run(self, task: str) -> str:
        """运行子任务"""
        print(f"📦 子Agent任务: {task[:50]}...")
        result = self.agent.run(task)
        print(f"📦 子Agent完成")
        return result


# ============ 便捷函数 ============


def run_agent(task: str, provider: str = None, **kwargs) -> str:
    """
    快速运行Agent

    示例:
        result = run_agent("创建一个Flask应用")
        result = run_agent("分析代码", provider="claude")
    """
    agent = Agent(provider=provider, **kwargs)
    return agent.run(task)


def create_agent(**kwargs) -> Agent:
    """创建Agent实例"""
    return Agent(**kwargs)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("AI Agent系统测试")
    print("=" * 60)

    # 测试Agent
    agent = Agent()

    # 测试工具
    print("\n测试工具:")
    registry = ToolRegistry()
    for tool in registry.list_tools():
        print(f"  - {tool.name}: {tool.description}")

    # 测试简单任务
    print("\n测试Agent:")
    result = agent.run("列出当前目录的文件")
    print(f"结果: {result}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
