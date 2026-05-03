#!/usr/bin/env python3
"""
上下文管理机制
分析→压缩→清理，以便在大模型上下文有限的情况下处理多个项目
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

try:
    import tiktoken
except ImportError:
    tiktoken = None

import os

_BASE = Path(os.environ.get("AI_BASE_DIR", Path(__file__).resolve().parent.parent))
CONTEXT_FILE = str(_BASE / "user/context.json")
COMPRESSED_CONTEXT_FILE = str(_BASE / "user/compressed_context.json")


class ContextManager:
    def __init__(self, context_file=CONTEXT_FILE, compressed_file=COMPRESSED_CONTEXT_FILE, shared_context_aware=True):
        self.context_file = Path(context_file)
        self.compressed_file = Path(compressed_file)
        self.context_file.parent.mkdir(parents=True, exist_ok=True)
        self.context = self.load()

        # 共享上下文感知：加载其他 Agent 的状态
        self._shared_snapshot = None
        if shared_context_aware:
            self._load_shared_context()

    def load(self):
        if self.context_file.exists():
            try:
                with open(self.context_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "history": [],
            "projects": {},
            "last_clean": datetime.now().isoformat(),
        }

    def _load_shared_context(self):
        """从共享上下文中加载其他 Agent 的状态。"""
        try:
            from core.shared_context import get_shared_context

            ctx = get_shared_context(auto_start=False)
            if ctx:
                self._shared_snapshot = ctx.get_snapshot()
                if self._shared_snapshot:
                    other_agents = self._shared_snapshot.get("active_agents", [])
                    conflicts = self._shared_snapshot.get("cross_agent_conflicts", [])
                    if other_agents:
                        self.add_message(
                            "system",
                            f"[Shared Context] {len(other_agents)} other agents active. "
                            f"Recent context: {self._shared_snapshot.get('merged_context', '')[:200]}",
                        )
                    if conflicts:
                        self.add_message(
                            "system", f"[Conflict Warning] {len(conflicts)} file conflicts detected between agents"
                        )
        except ImportError:
            pass
        except Exception:
            pass

    def save(self):
        with open(self.context_file, "w", encoding="utf-8") as f:
            json.dump(self.context, f, ensure_ascii=False, indent=2)

    def add_message(self, role, content):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.context["history"].append(message)
        self.save()

    def get_context(self, max_tokens=4000, recent_first=True):
        history = self.context["history"]
        if recent_first:
            history = history[::-1]

        messages = []
        total_tokens = 0
        for msg in history:
            tokens = self.count_tokens(msg["content"])
            if total_tokens + tokens > max_tokens:
                break
            messages.append(msg)
            total_tokens += tokens

        if recent_first:
            messages = messages[::-1]
        return messages, total_tokens

    def count_tokens(self, text):
        """精确计算 token 数量（使用 tiktoken）"""
        if tiktoken:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                return len(encoding.encode(text))
            except Exception:
                pass
        # 简单估算：1 token ≈ 4 字符
        return len(text) // 4

    def analyze_context(self):
        analysis = {
            "total_messages": len(self.context["history"]),
            "total_tokens": sum(self.count_tokens(msg["content"]) for msg in self.context["history"]),
            "projects": list(self.context["projects"].keys()),
            "last_message": self.context["history"][-1] if self.context["history"] else None,
            "last_clean": self.context["last_clean"],
        }
        return analysis

    def compress_context(self, project_name=None):
        """压缩上下文，保留关键信息"""
        compressed = []
        for msg in self.context["history"]:
            content = msg["content"]
            # 压缩策略：
            # 1. 去除重复内容
            # 2. 保留代码块和关键指令
            # 3. 简化描述性文字

            # 保留代码块
            code_blocks = re.findall(r"```[\s\S]*?```", content)
            if code_blocks:
                compressed_content = "\n".join(code_blocks)
            else:
                # 保留关键指令和结果
                lines = content.split("\n")
                important_lines = []
                for line in lines:
                    line = line.strip()
                    if line and any(
                        keyword in line
                        for keyword in [
                            "任务",
                            "目标",
                            "要求",
                            "需要",
                            "必须",
                            "完成",
                            "成功",
                            "失败",
                            "修复",
                            "实现",
                            "添加",
                            "删除",
                            "修改",
                        ]
                    ):
                        important_lines.append(line)
                compressed_content = "\n".join(important_lines[:10])  # 最多保留10行

            if compressed_content:
                compressed_msg = msg.copy()
                compressed_msg["content"] = compressed_content
                compressed_msg["compressed"] = True
                compressed.append(compressed_msg)

        compressed_context = {
            "history": compressed,
            "projects": self.context["projects"],
            "compressed_at": datetime.now().isoformat(),
        }

        with open(self.compressed_file, "w", encoding="utf-8") as f:
            json.dump(compressed_context, f, ensure_ascii=False, indent=2)

        return compressed_context

    def clean_context(self, keep_recent=10):
        """清理上下文，只保留最近的消息"""
        if len(self.context["history"]) > keep_recent:
            self.context["history"] = self.context["history"][-keep_recent:]
        self.context["last_clean"] = datetime.now().isoformat()
        self.save()
        return len(self.context["history"])

    def add_project(self, project_name, info):
        self.context["projects"][project_name] = {
            **info,
            "added_at": datetime.now().isoformat(),
        }
        self.save()

    def switch_project(self, project_name):
        """切换项目，压缩当前上下文并清理"""
        # 压缩当前上下文
        self.compress_context(project_name)
        # 清理上下文，只保留最近的消息
        self.clean_context(keep_recent=5)
        # 添加项目信息到新上下文
        self.add_message("system", f"切换到项目: {project_name}")

        # 广播上下文到共享系统
        try:
            from core.shared_context import get_shared_context

            ctx = get_shared_context(auto_start=False)
            if ctx and ctx._started:
                ctx.broadcast_context(
                    summary=f"Switched to project: {project_name}",
                    key_files=[str(self.context_file)],
                    key_decisions=[f"Project switch: {project_name}"],
                )
        except ImportError:
            pass

        return "已切换到项目: " + project_name

    def get_projects(self):
        return self.context["projects"]


def main():
    manager = ContextManager()

    # 示例：添加测试消息
    manager.add_message("user", "帮我修复游戏测试的bug")
    manager.add_message("assistant", "好的，我将帮你修复游戏测试的bug。首先分析问题...")

    # 分析上下文
    analysis = manager.analyze_context()
    print("上下文分析:")
    print(f"总消息数: {analysis['total_messages']}")
    print(f"总令牌数: {analysis['total_tokens']}")
    print(f"项目: {analysis['projects']}")

    # 压缩上下文
    compressed = manager.compress_context()
    print(f"\n压缩后消息数: {len(compressed['history'])}")

    # 清理上下文
    kept = manager.clean_context(keep_recent=5)
    print(f"\n清理后保留消息数: {kept}")


if __name__ == "__main__":
    main()
