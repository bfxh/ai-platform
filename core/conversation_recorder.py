#!/usr/bin/env python3
"""
/python 自动对话和任务记录系统
自动保存对话历史和任务记录
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ConversationRecorder:
    """对话记录器"""

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.environ.get("AI_BASE_DIR", str(Path(__file__).resolve().parent.parent))
        self.base_path = base_path
        self.conversations_path = os.path.join(base_path, "conversations")
        self.tasks_path = os.path.join(base_path, "tasks")

        # 确保目录存在
        self._ensure_directories()

        # 当前会话
        self.current_session = None
        self.session_id = None

    def _ensure_directories(self):
        """确保目录存在"""
        Path(self.conversations_path).mkdir(parents=True, exist_ok=True)
        Path(self.tasks_path).mkdir(parents=True, exist_ok=True)

        # 创建子目录
        Path(os.path.join(self.conversations_path, "daily")).mkdir(exist_ok=True)
        Path(os.path.join(self.tasks_path, datetime.now().strftime("%Y-%m"))).mkdir(parents=True, exist_ok=True)

    def start_session(self, session_name: Optional[str] = None) -> str:
        """开始新会话"""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            self.session_id = f"{self.session_id}_{session_name}"

        self.current_session = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "tasks": [],
        }

        return self.session_id

    def add_message(self, role: str, content: str):
        """添加消息"""
        if not self.current_session:
            self.start_session()

        self.current_session["messages"].append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

    def add_task(self, task: str, status: str = "pending"):
        """添加任务"""
        if not self.current_session:
            self.start_session()

        self.current_session["tasks"].append({"task": task, "status": status, "created_at": datetime.now().isoformat()})

    def end_session(self):
        """结束会话并保存"""
        if not self.current_session:
            return

        self.current_session["end_time"] = datetime.now().isoformat()

        # 保存对话历史
        self._save_conversation()

        # 保存任务记录
        self._save_tasks()

        self.current_session = None

    def _save_conversation(self):
        """保存对话历史"""
        if not self.current_session:
            return

        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"{self.conversations_path}\\daily\\{date}.json"

        # 读取已有数据
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except:
                existing_data = []

        # 添加新会话
        existing_data.append(self.current_session)

        # 保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def _save_tasks(self):
        """保存任务记录"""
        if not self.current_session or not self.current_session["tasks"]:
            return

        month = datetime.now().strftime("%Y-%m")
        filename = f"{self.tasks_path}\\{month}.json"

        # 读取已有数据
        existing_data = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except:
                existing_data = []

        # 添加新任务
        for task in self.current_session["tasks"]:
            existing_data.append(task)

        # 保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

    def get_conversation_history(self, date: Optional[str] = None) -> List[Dict]:
        """获取对话历史"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        filename = f"{self.conversations_path}\\daily\\{date}.json"

        if not os.path.exists(filename):
            return []

        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def get_tasks(self, month: Optional[str] = None) -> List[Dict]:
        """获取任务记录"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")

        filename = f"{self.tasks_path}\\{month}.json"

        if not os.path.exists(filename):
            return []

        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def search_conversations(self, keyword: str) -> List[Dict]:
        """搜索对话"""
        results = []
        daily_path = os.path.join(self.conversations_path, "daily")

        if not os.path.exists(daily_path):
            return results

        for filename in os.listdir(daily_path):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(daily_path, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    sessions = json.load(f)

                for session in sessions:
                    for message in session.get("messages", []):
                        if keyword.lower() in message.get("content", "").lower():
                            results.append(
                                {
                                    "session_id": session.get("session_id"),
                                    "date": filename.replace(".json", ""),
                                    "message": message,
                                }
                            )
                            break
            except:
                continue

        return results


def main():
    """测试函数"""
    recorder = ConversationRecorder()

    print("=" * 60)
    print("自动对话和任务记录系统测试")
    print("=" * 60)
    print()

    # 开始会话
    session_id = recorder.start_session("测试会话")
    print(f"[INFO] 会话已开始: {session_id}")
    print()

    # 添加消息
    recorder.add_message("user", "帮我写一个Python代码")
    recorder.add_message("assistant", "好的，我来帮你写一个Python代码。")
    recorder.add_message("user", "谢谢")
    print("[INFO] 已添加消息")
    print()

    # 添加任务
    recorder.add_task("写一个Python代码")
    recorder.add_task("测试代码")
    print("[INFO] 已添加任务")
    print()

    # 结束会话
    recorder.end_session()
    print("[INFO] 会话已结束并保存")
    print()

    # 获取历史
    history = recorder.get_conversation_history()
    print(f"[INFO] 获取到 {len(history)} 个历史会话")
    print()

    # 获取任务
    tasks = recorder.get_tasks()
    print(f"[INFO] 获取到 {len(tasks)} 个任务")
    print()


if __name__ == "__main__":
    main()
