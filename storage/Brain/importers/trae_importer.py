#!/usr/bin/env python
"""TRAE Conversation Importer - 从 TRAE/Qoder IDE 的 state.vscdb 导入对话记录

增强: session_memory 会话记录 + file_protector 导入前自动备份
"""

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

_engine = None
_memory = None
_protector = None

def _get_engine():
    global _engine
    if _engine is None:
        from storage.Brain.memory.engine import get_memory_engine
        _engine = get_memory_engine()
    return _engine

def _get_memory():
    global _memory
    if _memory is None:
        try:
            from core.session_memory import get_memory as gm
            _memory = gm()
        except Exception:
            _memory = None
    return _memory

def _get_protector():
    global _protector
    if _protector is None:
        try:
            from core.file_protector import get_protector as gp
            _protector = gp()
        except Exception:
            _protector = None
    return _protector

class TraeImporter:
    """TRAE/Qoder 对话导入器（增强: file_protector + session_memory）"""

    def __init__(self, trae_data_dir: str = None):
        if trae_data_dir:
            self.data_dir = Path(trae_data_dir)
        else:
            self.data_dir = Path(r"C:\Users\888\AppData\Roaming\Qoder")
        self.vscdb_files = []
        self._memory = _get_memory()
        self._protector = _get_protector()
        self._session_id = None

    def _ensure_session(self, label: str = "TRAE 导入"):
        """确保有活跃的会话记忆"""
        if self._memory and not self._session_id:
            try:
                self._session_id = self._memory.create_session(
                    agent="trae_importer", task=label
                )
            except Exception:
                pass
        return self._session_id

    def _backup_vscdb(self, vscdb_path: Path):
        """导入前备份 vscdb 文件到 CC/1_raw"""
        if self._protector:
            try:
                rel_path = f"trae_vscdb/{vscdb_path.parent.name}_{vscdb_path.name}"
                self._protector.register(rel_path)
                content = vscdb_path.read_bytes()
                import base64
                self._protector.safe_write(rel_path, base64.b64encode(content).decode("ascii"))
            except Exception:
                pass

    def scan_vscdb_files(self) -> list:
        files = []
        global_storage = self.data_dir / "User" / "globalStorage"
        if global_storage.exists():
            for vscdb in global_storage.glob("state.vscdb"):
                files.append({"path": vscdb, "type": "global", "description": "全局存储"})
        workspace_storage = self.data_dir / "User" / "workspaceStorage"
        if workspace_storage.exists():
            for dir_name in os.listdir(workspace_storage):
                dir_path = workspace_storage / dir_name
                if dir_path.is_dir():
                    vscdb_path = dir_path / "state.vscdb"
                    if vscdb_path.exists():
                        files.append({"path": vscdb_path, "type": "workspace", "description": f"工作区 {dir_name[:16]}..."})
        self.vscdb_files = files
        return files

    def _decode_value(self, value) -> str:
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return str(value)

    def _extract_messages_from_data(self, data, depth=0) -> list:
        messages = []
        if depth > 5:
            return messages

        if isinstance(data, dict):
            # 直接有 role + content
            if "role" in data and "content" in data:
                messages.append({"role": data["role"], "content": data["content"]})
                return messages

            # 常见嵌套字段
            for key in ["messages", "conversation", "turns", "history", "data", "entries", "requests"]:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        messages.extend(self._extract_messages_from_data(item, depth + 1))

            # lingma chat history format
            if "question" in data or "answer" in data:
                q = data.get("question", "")
                a = data.get("answer", "")
                if q:
                    messages.append({"role": "user", "content": str(q)})
                if a:
                    messages.append({"role": "assistant", "content": str(a)})
                return messages

            # chat session format with sessionId + messages
            if "sessionId" in data:
                for key in ["messages", "conversation"]:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            messages.extend(self._extract_messages_from_data(item, depth + 1))

        elif isinstance(data, list):
            for item in data:
                messages.extend(self._extract_messages_from_data(item, depth + 1))

        return messages

    def extract_all_chat_data(self, vscdb_path: Path) -> list:
        chat_data = []
        try:
            conn = sqlite3.connect(str(vscdb_path))
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM ItemTable")
            rows = cursor.fetchall()

            for key, value in rows:
                key_lower = key.lower()
                if not any(kw in key_lower for kw in ["chat", "conversation", "ai", "message", "lingma", "aicoding"]):
                    continue

                value_str = self._decode_value(value)
                try:
                    parsed = json.loads(value_str)
                except (json.JSONDecodeError, ValueError):
                    if len(value_str) > 20:
                        chat_data.append({
                            "key": key,
                            "messages": [{"role": "raw", "content": value_str[:50000]}],
                            "size": len(value_str)
                        })
                    continue

                # 提取消息
                messages = self._extract_messages_from_data(parsed)

                # 如果没提取到消息，保存原始数据摘要
                if not messages and isinstance(parsed, (dict, list)):
                    # 尝试直接把整个数据当知识保存
                    summary = json.dumps(parsed, ensure_ascii=False)[:10000]
                    messages = [{"role": "metadata", "content": summary}]

                if messages:
                    chat_data.append({
                        "key": key,
                        "messages": messages,
                        "size": len(value_str)
                    })

            conn.close()
        except Exception as e:
            print(f"Error reading {vscdb_path}: {e}")

        return chat_data

    def import_chat(self, vscdb_path: Path, engine=None) -> dict:
        if engine is None:
            engine = _get_engine()

        # 导入前备份 vscdb
        self._backup_vscdb(vscdb_path)

        # 确保会话记录
        self._ensure_session(f"TRAE 导入: {vscdb_path.name}")

        chat_data = self.extract_all_chat_data(vscdb_path)

        if not chat_data:
            result = {"status": "no_data", "entries_found": 0, "entries_imported": 0}
            if self._memory and self._session_id:
                self._memory.add_result(self._session_id, True,
                    f"vscdb 无数据: {vscdb_path.name}", detail=result)
            return result

        total_messages = 0
        imported_keys = 0
        session_id = f"trae_{vscdb_path.parent.name[:16]}_{int(datetime.now().timestamp())}"

        for chat_entry in chat_data:
            key = chat_entry["key"]
            messages = chat_entry["messages"]
            total_messages += len(messages)

            # 保存每条消息为知识条目
            for i, msg in enumerate(messages[:30]):
                role = msg.get("role", "unknown")
                content = str(msg.get("content", ""))[:50000]
                if not content or content == "None":
                    continue

                category = "project_context" if role == "user" else "domain_knowledge"
                safe_key = re.sub(r'[^\w]', '_', key[:30])
                entry_id = f"{session_id}_{safe_key}_{i}"

                try:
                    engine.kb_save(
                        category=category,
                        entry_id=entry_id,
                        title=f"[{role}] {key[:40]}",
                        content=content,
                        tags=["trae", "conversation", role, key.split('.')[0]],
                        importance=5 if role == "assistant" else 4
                    )
                    imported_keys += 1
                except Exception as e:
                    print(f"Error saving entry {entry_id}: {e}")

        # 保存会话摘要
        user_msgs = sum(1 for cd in chat_data for m in cd["messages"] if m.get("role") == "user")
        asst_msgs = sum(1 for cd in chat_data for m in cd["messages"] if m.get("role") == "assistant")
        summary = f"TRAE/Qoder 对话记录: {len(chat_data)} 个会话, {user_msgs} 条用户消息, {asst_msgs} 条AI回复"

        try:
            engine.save_session(
                session_id=session_id,
                summary=summary,
                key_decisions=[],
                user_prefs={},
                lessons=[],
                files_touched=[],
                tools_used=["TRAE IDE"],
                duration_minutes=0
            )
        except Exception as e:
            print(f"Error saving session: {e}")

        result = {
            "status": "success",
            "session_id": session_id,
            "entries_found": len(chat_data),
            "entries_imported": imported_keys,
            "total_messages": total_messages
        }

        # 记录到 session_memory
        if self._memory and self._session_id:
            self._memory.add_result(self._session_id, True,
                summary, detail=result)

        return result

    def import_all(self, engine=None) -> dict:
        if engine is None:
            engine = _get_engine()

        self._ensure_session("TRAE 批量导入")

        self.scan_vscdb_files()
        stats = {"total_files": len(self.vscdb_files), "imported": 0, "failed": 0, "total_entries": 0, "total_messages": 0}

        for vscdb_info in self.vscdb_files:
            try:
                result = self.import_chat(vscdb_info["path"], engine)
                if result["status"] == "success":
                    stats["imported"] += 1
                    stats["total_entries"] += result.get("entries_imported", 0)
                    stats["total_messages"] += result.get("total_messages", 0)
                elif result["status"] == "no_data":
                    stats["failed"] += 1
            except Exception as e:
                print(f"Failed to import {vscdb_info['path']}: {e}")
                stats["failed"] += 1

        # 记录到 session_memory 并关闭
        if self._memory and self._session_id:
            summary = (f"TRAE 批量导入完成: {stats['imported']}/{stats['total_files']} 文件, "
                       f"{stats['total_entries']} 条目, {stats['total_messages']} 消息")
            self._memory.add_result(self._session_id, True, summary, detail=stats)
            try:
                self._memory.close_session(self._session_id)
            except Exception:
                pass
            self._session_id = None

        return stats


class TraeExporter:
    """CLAUDE → TRAE 数据导出器

    将 CLAUDE 的 evo 优化建议 / session 上下文 / skill 定义写回 TRAE 存储。
    桥接模式的关键组件——CLAUDE 产出 → TRAE 消费。
    """

    def __init__(self, trae_data_dir: str = None):
        if trae_data_dir:
            self.data_dir = Path(trae_data_dir)
        else:
            self.data_dir = Path(r"C:\Users\888\AppData\Roaming\Qoder")

    def _find_vscdb(self, target: str = "workspace") -> Optional[Path]:
        """查找 TRAE 的 state.vscdb 文件"""
        if target == "global":
            global_storage = self.data_dir / "User" / "globalStorage"
            if global_storage.exists():
                for vscdb in global_storage.glob("state.vscdb"):
                    return vscdb
        else:
            workspace_storage = self.data_dir / "User" / "workspaceStorage"
            if workspace_storage.exists():
                for dir_name in os.listdir(workspace_storage):
                    vscdb = workspace_storage / dir_name / "state.vscdb"
                    if vscdb.exists():
                        return vscdb
        return None

    def write_to_vscdb(self, key: str, value: dict) -> bool:
        """写入键值到 TRAE 的 SQLite 存储

        Args:
            key:   存储 key
            value: JSON 可序列化的值
        """
        vscdb = self._find_vscdb()
        if not vscdb:
            return False
        try:
            conn = sqlite3.connect(str(vscdb))
            cursor = conn.cursor()
            # 确保表存在
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS ItemTable (key TEXT PRIMARY KEY, value BLOB)"
            )
            cursor.execute(
                "INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False).encode("utf-8"))
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"write_to_vscdb error: {e}")
            return False

    def export_session_context(self, session_data: dict) -> bool:
        """导出 CLAUDE session 上下文到 TRAE 对话条目"""
        session_id = session_data.get("session_id", f"claude_{int(time.time())}")
        key = f"claude_session.{session_id}"

        value = {
            "source": "CLAUDE",
            "type": "session_context",
            "session_id": session_id,
            "agent": session_data.get("agent", "unknown"),
            "task": session_data.get("task", ""),
            "messages": session_data.get("messages", [])[-5:],
            "exported_at": datetime.now().isoformat(),
        }
        return self.write_to_vscdb(key, value)

    def export_evo_feedback(self, suggestions: List[dict]) -> dict:
        """导出 evo 优化建议到 TRAE

        Returns:
            {"exported": int, "keys": [...]}
        """
        exported = 0
        keys = []
        timestamp = int(time.time())

        for i, sug in enumerate(suggestions[:10]):
            key = f"claude_evo.suggestion.{timestamp}_{i}"
            value = {
                "source": "CLAUDE EvoEngine",
                "type": "optimization_suggestion",
                "agent": sug.get("agent", ""),
                "action": sug.get("action", ""),
                "suggestion": sug.get("suggestion", ""),
                "severity": sug.get("severity", "low"),
                "exported_at": datetime.now().isoformat(),
            }
            if self.write_to_vscdb(key, value):
                exported += 1
                keys.append(key)

        return {"exported": exported, "keys": keys}

    def export_skills_to_trae(self, skill_names: List[str]) -> dict:
        """导出 CLAUDE skill 定义到 TRAE"""
        exported = 0
        timestamp = int(time.time())

        for skill_name in skill_names[:20]:
            key = f"claude_skill.{skill_name}.{timestamp}"
            value = {
                "source": "CLAUDE Superpowers",
                "type": "skill_definition",
                "name": skill_name,
                "exported_at": datetime.now().isoformat(),
            }
            if self.write_to_vscdb(key, value):
                exported += 1

        return {"exported": exported}


if __name__ == "__main__":
    importer = TraeImporter()
    vscdb_files = importer.scan_vscdb_files()
    print(f"Found {len(vscdb_files)} vscdb files")
    for v in vscdb_files:
        print(f"  - {v['description']}: {v['path']}")
    if vscdb_files:
        print("\n=== Importing ===")
        stats = importer.import_all()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
