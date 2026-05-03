#!/usr/bin/env python3
"""
Claude Code 运作模式 - 复刻核心机制
基于逆向工程分析实现
"""

import asyncio
import hashlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional

# 添加工具路径
sys.path.insert(0, r"\python\tools")
sys.path.insert(0, r"\python\core")


class AgentState(Enum):
    """Agent状态"""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class Message:
    """消息结构 - 复刻h2A消息队列"""

    id: str
    type: str  # user, assistant, tool, system
    content: str
    metadata: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolCall:
    """工具调用 - 复刻Claude Code工具系统"""

    id: str
    name: str
    params: Dict
    result: Any = None
    status: str = "pending"  # pending, running, success, error


class ContextManager:
    """
    上下文管理器 - 复刻wU2消息压缩器
    92%阈值自动压缩算法
    """

    def __init__(self, max_tokens: int = 8000, compress_threshold: float = 0.92):
        self.max_tokens = max_tokens
        self.compress_threshold = compress_threshold
        self.messages: List[Message] = []
        self.summary: str = ""
        self.token_count = 0

    def add_message(self, message: Message) -> bool:
        """添加消息，自动压缩"""
        self.messages.append(message)
        self.token_count = self._estimate_tokens()

        # 检查是否需要压缩
        if self.token_count / self.max_tokens > self.compress_threshold:
            self._compress()
            return True
        return False

    def _estimate_tokens(self) -> int:
        """估算token数"""
        total = 0
        for msg in self.messages:
            # 中文1.5 token/字，英文1.3 token/词
            cn = len([c for c in msg.content if "\u4e00" <= c <= "\u9fff"])
            en = len(msg.content.split())
            total += int(cn * 1.5 + en * 1.3)
        return total

    def _compress(self):
        """压缩上下文 - 保留关键信息"""
        # 保留系统消息和最近消息
        system_msgs = [m for m in self.messages if m.type == "system"]
        recent_msgs = self.messages[-5:] if len(self.messages) > 5 else self.messages

        # 生成摘要
        old_msgs = self.messages[:-5] if len(self.messages) > 5 else []
        if old_msgs:
            self.summary = self._generate_summary(old_msgs)

        # 重建消息列表
        self.messages = (
            system_msgs
            + [
                Message(
                    id="summary", type="system", content=f"[历史摘要] {self.summary}", metadata={"compressed": True}
                )
            ]
            + recent_msgs
        )

        self.token_count = self._estimate_tokens()

    def _generate_summary(self, messages: List[Message]) -> str:
        """生成消息摘要"""
        # 简化实现：提取关键信息
        key_points = []
        for msg in messages:
            if msg.type == "user":
                key_points.append(f"用户请求: {msg.content[:50]}...")
            elif msg.type == "assistant" and "tool" in msg.metadata:
                key_points.append(f"执行工具: {msg.metadata['tool']}")
        return "; ".join(key_points[-3:])  # 保留最近3个关键点

    def get_context(self) -> List[Dict]:
        """获取当前上下文"""
        return [m.to_dict() for m in self.messages]

    def clear(self):
        """清空上下文"""
        self.messages = []
        self.summary = ""
        self.token_count = 0


class ToolRegistry:
    """
    工具注册表 - 复刻Claude Code工具系统
    """

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认工具"""
        # 文件工具
        self.register("read_file", self._read_file)
        self.register("write_file", self._write_file)
        self.register("list_dir", self._list_dir)

        # 代码工具
        self.register("search_code", self._search_code)
        self.register("run_command", self._run_command)

        # 分析工具
        self.register("analyze_code", self._analyze_code)

        # MCP工具
        self.register("use_mcp", self._use_mcp)

    def register(self, name: str, func: Callable):
        """注册工具"""
        self.tools[name] = func

    def call(self, name: str, params: Dict) -> Any:
        """调用工具"""
        if name not in self.tools:
            return {"error": f"未知工具: {name}"}

        try:
            return self.tools[name](**params)
        except Exception as e:
            return {"error": str(e)}

    # 工具实现
    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, path: str, content: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入: {path}"

    def _list_dir(self, path: str = ".") -> List[str]:
        return os.listdir(path)

    def _search_code(self, pattern: str, path: str = ".") -> List[str]:
        import re

        results = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if re.search(pattern, content):
                                results.append(filepath)
                    except:
                        pass
        return results

    _BLOCKED_CMDS = {'rm', 'del', 'format', 'rmdir', 'rd', 'erase', 'cipher', 'diskpart',
                     'net', 'netsh', 'reg', 'regedit', 'wscript', 'cscript', 'mshta',
                     'certutil', 'bitsadmin', 'ftp', 'shutdown', 'taskkill', 'powershell', 'cmd'}

    def _run_command(self, command: str) -> str:
        import subprocess
        import os

        first_token = command.split()[0].lower() if command.split() else ""
        base_name = os.path.basename(first_token)
        name, _ = os.path.splitext(base_name)
        if name in self._BLOCKED_CMDS:
            return f"[错误] 危险命令已被阻止: {name}"

        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return result.stdout or result.stderr

    def _analyze_code(self, code: str) -> Dict:
        # 简化实现
        return {"lines": len(code.split("\n")), "functions": code.count("def "), "classes": code.count("class ")}

    def _use_mcp(self, server: str, tool: str, params: Dict) -> Any:
        """使用MCP工具"""
        # 调用MCP
        return {"server": server, "tool": tool, "params": params}


class SubAgent:
    """
    子Agent - 复刻SubAgent并发执行
    """

    def __init__(self, name: str, parent: "ClaudeAgent"):
        self.name = name
        self.parent = parent
        self.context = ContextManager()
        self.state = AgentState.IDLE
        self.result: Any = None

    async def run(self, task: str) -> Any:
        """运行子任务"""
        self.state = AgentState.THINKING

        # 使用父Agent的AI能力
        result = self.parent._call_ai(task)

        self.result = result
        self.state = AgentState.IDLE
        return result


class ClaudeAgent:
    """
    Claude Code Agent - 核心实现
    复刻nO主循环引擎
    """

    def __init__(self, name: str = "Claude"):
        self.name = name
        self.state = AgentState.IDLE
        self.context = ContextManager()
        self.tools = ToolRegistry()
        self.message_queue: Queue = Queue()
        self.subagents: List[SubAgent] = []
        self.running = False

        # 从stepfun_client导入
        try:
            from stepfun_client import StepFunClient

            self.ai_client = StepFunClient()
        except ImportError:
            StepFunClient = None
            self.ai_client = None

    def _call_ai(self, prompt: str, context: List[Dict] = None) -> str:
        """调用AI"""
        if self.ai_client:
            try:
                return self.ai_client.chat(prompt)
            except Exception as e:
                return f"[AI错误] {e}"
        return f"[AI模拟] {prompt[:50]}..."

    async def _process_message(self, message: Message):
        """处理消息 - 核心循环"""
        self.state = AgentState.THINKING

        # 添加到上下文
        compressed = self.context.add_message(message)
        if compressed:
            print("[系统] 上下文已自动压缩")

        # 分析意图
        intent = self._analyze_intent(message.content)

        # 执行
        if intent["type"] == "tool":
            self.state = AgentState.EXECUTING
            result = self._execute_tool(intent["tool"], intent["params"])

            # 添加结果到上下文
            self.context.add_message(
                Message(
                    id=f"tool_{int(time.time())}", type="tool", content=str(result), metadata={"tool": intent["tool"]}
                )
            )

            # 生成回复
            response = self._call_ai(f"工具执行结果: {result}", self.context.get_context())
        else:
            # 直接回复
            response = self._call_ai(message.content, self.context.get_context())

        # 添加回复到上下文
        self.context.add_message(Message(id=f"assistant_{int(time.time())}", type="assistant", content=response))

        self.state = AgentState.IDLE
        return response

    def _analyze_intent(self, content: str) -> Dict:
        """分析用户意图"""
        # 简单规则匹配
        if content.startswith("/"):
            # 命令
            parts = content[1:].split()
            return {"type": "tool", "tool": parts[0], "params": {"args": parts[1:]}}

        # 检查是否需要工具
        tool_keywords = {
            "读文件": ("read_file", {"path": self._extract_path(content)}),
            "写文件": ("write_file", {"path": self._extract_path(content), "content": ""}),
            "列目录": ("list_dir", {"path": "."}),
            "搜索": ("search_code", {"pattern": content}),
        }

        for keyword, (tool, params) in tool_keywords.items():
            if keyword in content:
                return {"type": "tool", "tool": tool, "params": params}

        return {"type": "chat"}

    def _extract_path(self, content: str) -> str:
        """提取路径"""
        import re

        match = re.search(r"[\w\\/:\.]+\.\w+", content)
        return match.group(0) if match else "."

    def _execute_tool(self, name: str, params: Dict) -> Any:
        """执行工具"""
        print(f"[工具] {name}({params})")
        return self.tools.call(name, params)

    async def run(self):
        """主循环 - nO引擎"""
        self.running = True
        print(f"[{self.name}] Agent已启动")

        while self.running:
            try:
                # 从队列获取消息
                message = self.message_queue.get(timeout=0.1)

                # 处理消息
                response = await self._process_message(message)
                print(f"\n[{self.name}] {response}\n")

            except Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"[错误] {e}")
                self.state = AgentState.ERROR

    def send(self, content: str):
        """发送消息到Agent"""
        message = Message(id=f"msg_{int(time.time())}", type="user", content=content)
        self.message_queue.put(message)

    def stop(self):
        """停止Agent"""
        self.running = False

    def create_subagent(self, name: str) -> SubAgent:
        """创建子Agent"""
        sub = SubAgent(name, self)
        self.subagents.append(sub)
        return sub


# 全局Agent实例
_agent: Optional[ClaudeAgent] = None


def get_agent() -> ClaudeAgent:
    """获取全局Agent"""
    global _agent
    if _agent is None:
        _agent = ClaudeAgent()
    return _agent


# 便捷函数
def ask(prompt: str) -> str:
    """向Agent提问"""
    agent = get_agent()

    # 直接调用AI
    if agent.ai_client:
        try:
            return agent.ai_client.chat(prompt)
        except Exception as e:
            return f"[错误] {e}"

    return "[错误] AI客户端未初始化"


def chat():
    """进入对话模式"""
    agent = get_agent()

    print(f"\n[{agent.name}] 对话模式 (输入 'exit' 退出)")
    print("-" * 50)

    # 启动Agent
    import threading

    def run_agent():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agent.run())

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

    # 交互循环
    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() == "exit":
                agent.stop()
                print("👋 再见!")
                break

            if user_input:
                agent.send(user_input)
                time.sleep(1)  # 等待处理

                # 显示回复
                if agent.context.messages:
                    last = agent.context.messages[-1]
                    if last.type == "assistant":
                        print(f"\n{agent.name}: {last.content}")

        except KeyboardInterrupt:
            agent.stop()
            print("\n👋 再见!")
            break


if __name__ == "__main__":
    # 测试
    print(ask("你好"))
    # chat()
