#!/usr/bin/env python
"""Qoder Conversation Importer - 从 Qoder IDE 导入对话记录到 Brain 知识库"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# 延迟导入避免循环依赖
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from storage.Brain.memory.engine import get_memory_engine
        _engine = get_memory_engine()
    return _engine

class QoderImporter:
    """Qoder 对话导入器"""

    def __init__(self, qoder_data_dir: str = None):
        if qoder_data_dir:
            self.data_dir = Path(qoder_data_dir)
        else:
            self.data_dir = Path(r"C:\Users\888\AppData\Roaming\Qoder\SharedClientCache\cli\projects\d--rj")
        self.cli_dir = self.data_dir.parent.parent  # cli/
        self.specs_dir = self.cli_dir / "specs"
        self.todos_dir = self.cli_dir / "todos"
        self.quest_dir = self.cli_dir / "quest"

    def scan_sessions(self) -> list:
        """扫描所有会话文件"""
        sessions = []
        if self.data_dir.exists():
            for jsonl_file in self.data_dir.glob("*.session.execution.jsonl"):
                session_id = jsonl_file.stem.replace(".session.execution", "")
                sessions.append({
                    "id": session_id,
                    "jsonl_path": jsonl_file,
                    "metadata_path": self.data_dir / f"{jsonl_file.stem}-session.json",
                    "todos_path": self.todos_dir / f"{jsonl_file.stem}.json",
                    "spec_path": self.specs_dir / f"spec-{session_id[:14]}.md",
                    "subagents_dir": self.data_dir / jsonl_file.stem / "subagents",
                })
        return sessions

    def parse_session(self, jsonl_path: Path) -> dict:
        """解析单个 JSONL 会话文件"""
        result = {
            "user_messages": [],
            "assistant_responses": [],
            "tool_calls": [],
            "files_modified": [],
            "summary": "",
        }

        if not jsonl_path.exists():
            return result

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        msg_type = entry.get("type")
                        message = entry.get("message", {})
                        content = message.get("content", [])

                        if msg_type == "user":
                            for item in content:
                                if item.get("type") == "text":
                                    result["user_messages"].append(item["text"])

                        elif msg_type == "assistant":
                            response = []
                            for item in content:
                                if item.get("type") == "text":
                                    response.append(item["text"])
                                elif item.get("type") == "thinking":
                                    response.append(f"【思考】{item['thinking']}")
                                elif item.get("type") == "tool_use":
                                    tool_name = item.get("name")
                                    tool_input = item.get("input", {})
                                    result["tool_calls"].append({
                                        "name": tool_name,
                                        "input": tool_input,
                                        "result": None,
                                    })
                            if response:
                                result["assistant_responses"].append("\n".join(response))

                        elif msg_type == "tool_result":
                            if result["tool_calls"]:
                                last_call = result["tool_calls"][-1]
                                for item in content:
                                    if item.get("type") == "text":
                                        last_call["result"] = item["text"]
                                        # 从工具结果中提取修改的文件
                                        file_pattern = r"(?:创建|修改|写入|生成)\s*(.+?\.(?:py|json|md|txt|yaml|yml))"
                                        matches = re.findall(file_pattern, item["text"])
                                        result["files_modified"].extend(matches)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error parsing {jsonl_path}: {e}")

        # 生成摘要
        if result["user_messages"]:
            result["summary"] = f"用户请求: {result['user_messages'][0][:100]}..."

        return result

    def parse_metadata(self, metadata_path: Path) -> dict:
        """解析会话元数据"""
        if not metadata_path.exists():
            return {}
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def parse_todos(self, todos_path: Path) -> list:
        """解析 Todo 列表"""
        if not todos_path.exists():
            return []
        try:
            with open(todos_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("todos", [])
        except Exception:
            return []

    def import_session(self, session_data: dict, engine = None) -> dict:
        """导入单个会话到 Brain"""
        if engine is None:
            engine = _get_engine()

        session_id = session_data["id"]
        parsed = self.parse_session(session_data["jsonl_path"])
        metadata = self.parse_metadata(session_data["metadata_path"])
        todos = self.parse_todos(session_data["todos_path"])

        # 保存会话摘要
        summary = f"""{parsed['summary']}
工具调用: {metadata.get('modelCallCount', 0)} 次模型调用, {metadata.get('toolCallCount', 0)} 次工具调用
修改文件: {', '.join(parsed['files_modified'])[:100]}"""

        session_info = engine.save_session(
            session_id=session_id,
            summary=summary,
            key_decisions=[],
            user_prefs={},
            lessons=[],
            files_touched=parsed["files_modified"],
            tools_used=[tc["name"] for tc in parsed["tool_calls"]],
            duration_minutes=0
        )

        # 提取知识
        if parsed["tool_calls"]:
            for tc in parsed["tool_calls"]:
                if tc["result"] and len(tc["result"]) > 50:
                    tool_result = tc["result"][:1000]
                    entry_id = f"tool_{session_id}_{tc['name'][:20]}"
                    engine.kb_save(
                        category="project_context",
                        entry_id=entry_id,
                        title=f"{tc['name']} 执行结果",
                        content=tool_result,
                        tags=["tool", tc["name"], "automation"],
                        importance=5
                    )

        # 提取 Todo 作为知识
        if todos:
            todo_text = "\n".join(f"- [{t.get('status', ' ')}] {t.get('content', '')}" for t in todos)
            engine.kb_save(
                category="project_context",
                entry_id=f"todos_{session_id}",
                title=f"会话任务列表",
                content=todo_text,
                tags=["task", "todo", "project"],
                importance=6
            )

        return {"session_id": session_id, "imported": True, "todos_count": len(todos)}

    def import_all(self, engine = None) -> dict:
        """导入所有会话"""
        if engine is None:
            engine = _get_engine()

        sessions = self.scan_sessions()
        results = []
        stats = {
            "total_sessions": len(sessions),
            "imported": 0,
            "failed": 0,
            "total_todos": 0,
        }

        for session_data in sessions:
            try:
                result = self.import_session(session_data, engine)
                results.append(result)
                stats["imported"] += 1
                stats["total_todos"] += result.get("todos_count", 0)
            except Exception as e:
                print(f"Failed to import {session_data['id']}: {e}")
                stats["failed"] += 1

        return stats

# ─── CLI 测试入口 ───────────────────────────────────────────
if __name__ == "__main__":
    importer = QoderImporter()
    sessions = importer.scan_sessions()
    print(f"找到 {len(sessions)} 个会话")

    if sessions:
        print("\n=== 开始导入 ===")
        stats = importer.import_all()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        
        print("\n=== 第一个会话内容预览 ===")
        parsed = importer.parse_session(sessions[0]["jsonl_path"])
        print(f"用户消息: {len(parsed['user_messages'])} 条")
        print(f"助手回复: {len(parsed['assistant_responses'])} 条")
        print(f"工具调用: {len(parsed['tool_calls'])} 次")
        print(f"修改文件: {parsed['files_modified']}")
