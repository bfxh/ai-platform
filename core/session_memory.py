#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话记忆系统 — 上下文延续 + 会话持久化

功能:
- 会话创建/加载/列表
- 消息历史记录（用户输入 + agent 输出）
- 任务执行结果追踪
- 最近会话快速检索
- 自动过期清理

存储: JSON 文件（`storage/sessions/`），零外部依赖

用法:
    from core.session_memory import SessionMemory

    mem = SessionMemory()
    sid = mem.create_session(agent="trae_control")
    mem.add_message(sid, role="user", content="创建 React 组件")
    mem.add_result(sid, success=True, summary="组件已创建")
    ctx = mem.get_context(sid)  # 获取完整会话上下文
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List


class SessionMemory:
    """轻量级会话记忆管理器"""

    MAX_SESSIONS_IN_MEMORY = 20       # 内存中最多保留的会话数
    MAX_SESSION_AGE_DAYS = 30         # 超过此天数自动归档
    MAX_CONTEXT_MESSAGES = 50         # 注入上下文的最大消息数
    SESSION_DIR_NAME = "sessions"
    ARCHIVE_DIR_NAME = "sessions_archive"

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.environ.get(
                "AI_BASE_DIR",
                str(Path(__file__).resolve().parent.parent)
            )
        self.base_dir = Path(base_dir)
        self.session_dir = self.base_dir / "storage" / self.SESSION_DIR_NAME
        self.archive_dir = self.base_dir / "storage" / self.ARCHIVE_DIR_NAME
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self._cache: Dict[str, dict] = {}
        self._access_order: List[str] = []

    # ================================================================
    # 会话生命周期
    # ================================================================

    def create_session(self, agent: str = "orchestrator",
                       task: str = "", metadata: dict = None) -> str:
        """创建新会话

        Returns:
            session_id (8 字符 hex)
        """
        import uuid
        sid = uuid.uuid4().hex[:8]
        now = datetime.now().isoformat()

        session = {
            "session_id": sid,
            "created_at": now,
            "updated_at": now,
            "agent": agent,
            "task": task[:200],
            "status": "active",
            "messages": [],
            "results": [],
            "metadata": metadata or {},
            "message_count": 0,
            "result_count": 0,
        }

        self._save_session(sid, session)
        self._cache_put(sid, session)
        return sid

    def load_session(self, session_id: str) -> Optional[dict]:
        """加载会话"""
        # 先查缓存
        if session_id in self._cache:
            self._touch(session_id)
            return self._cache[session_id]

        # 从文件加载
        data = self._read_session_file(session_id)
        if data:
            self._cache_put(session_id, data)
            return data
        return None

    def list_sessions(self, limit: int = 20, agent: str = None) -> List[dict]:
        """列出最近的会话"""
        sessions = []
        for f in sorted(self.session_dir.glob("*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if agent and data.get("agent") != agent:
                    continue
                sessions.append({
                    "session_id": data["session_id"],
                    "created_at": data.get("created_at", ""),
                    "updated_at": data.get("updated_at", ""),
                    "agent": data.get("agent", ""),
                    "task": data.get("task", "")[:100],
                    "status": data.get("status", "unknown"),
                    "message_count": data.get("message_count", 0),
                    "result_count": data.get("result_count", 0),
                })
            except Exception:
                continue
            if len(sessions) >= limit:
                break
        return sessions

    def close_session(self, session_id: str):
        """关闭会话（标记为完成）"""
        session = self.load_session(session_id)
        if session:
            session["status"] = "completed"
            session["updated_at"] = datetime.now().isoformat()
            self._save_session(session_id, session)

    # ================================================================
    # 消息管理
    # ================================================================

    def add_message(self, session_id: str, role: str, content: str,
                    metadata: dict = None):
        """添加消息到会话

        Args:
            session_id: 会话 ID
            role:       'user' | 'agent' | 'system' | 'tool'
            content:    消息内容
        """
        session = self.load_session(session_id)
        if not session:
            return

        msg = {
            "role": role,
            "content": content[:8000],  # 单条消息最多 8KB
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        session["messages"].append(msg)
        session["message_count"] = len(session["messages"])
        session["updated_at"] = datetime.now().isoformat()

        # 限制消息数量（保留最近 N 条）
        if len(session["messages"]) > self.MAX_CONTEXT_MESSAGES * 2:
            session["messages"] = session["messages"][-self.MAX_CONTEXT_MESSAGES:]

        self._save_session(session_id, session)

    def add_result(self, session_id: str, success: bool, summary: str,
                   detail: dict = None):
        """添加任务执行结果"""
        session = self.load_session(session_id)
        if not session:
            return

        result = {
            "success": success,
            "summary": summary[:1000],
            "detail": detail or {},
            "timestamp": datetime.now().isoformat(),
        }
        session["results"].append(result)
        session["result_count"] = len(session["results"])
        session["updated_at"] = datetime.now().isoformat()

        self._save_session(session_id, session)

    # ================================================================
    # 上下文检索
    # ================================================================

    def get_context(self, session_id: str,
                    max_messages: int = None,
                    include_results: bool = True) -> dict:
        """获取会话上下文（用于注入 agent prompt）

        Returns:
            {"session_id": ..., "agent": ..., "task": ...,
             "recent_messages": [...], "recent_results": [...],
             "summary": str}
        """
        session = self.load_session(session_id)
        if not session:
            return {"session_id": session_id, "available": False}

        max_msgs = max_messages or self.MAX_CONTEXT_MESSAGES
        messages = session.get("messages", [])[-max_msgs:]
        results = session.get("results", [])[-10:] if include_results else []

        # 生成摘要
        total_msgs = session.get("message_count", 0)
        total_results = session.get("result_count", 0)
        success_count = sum(1 for r in session.get("results", []) if r.get("success"))

        summary = (
            f"会话 {session_id}: "
            f"代理={session.get('agent', '?')}, "
            f"消息={total_msgs}条, "
            f"任务={total_results}次 (成功{success_count})"
        )

        return {
            "session_id": session_id,
            "agent": session.get("agent", ""),
            "task": session.get("task", ""),
            "status": session.get("status", ""),
            "created_at": session.get("created_at", ""),
            "available": True,
            "summary": summary,
            "total_messages": total_msgs,
            "total_results": total_results,
            "success_count": success_count,
            "recent_messages": [
                {"role": m["role"], "content": m["content"][:500]}
                for m in messages
            ],
            "recent_results": [
                {"success": r["success"], "summary": r["summary"][:200]}
                for r in results
            ],
        }

    def get_formatted_context(self, session_id: str) -> str:
        """获取格式化的上下文字符串（可直接注入 system prompt）"""
        ctx = self.get_context(session_id)
        if not ctx.get("available"):
            return ""

        lines = [f"## 会话上下文 ({session_id})"]
        lines.append(f"代理: {ctx['agent']}")
        lines.append(f"任务: {ctx['task'][:100]}")
        lines.append(f"状态: {ctx['status']}")

        if ctx["recent_messages"]:
            lines.append("\n### 最近消息")
            for m in ctx["recent_messages"][-10:]:
                role_label = {"user": "用户", "agent": "代理",
                              "system": "系统", "tool": "工具"}.get(m["role"], m["role"])
                lines.append(f"- [{role_label}] {m['content'][:200]}")

        if ctx["recent_results"]:
            lines.append("\n### 最近结果")
            for r in ctx["recent_results"][-5:]:
                status = "成功" if r["success"] else "失败"
                lines.append(f"- [{status}] {r['summary'][:200]}")

        return "\n".join(lines)

    # ================================================================
    # 会话间检索
    # ================================================================

    def find_related_sessions(self, keyword: str, limit: int = 5) -> List[dict]:
        """在所有会话中搜索相关关键词"""
        results = []
        keyword_lower = keyword.lower()

        for f in self.session_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                task = data.get("task", "").lower()
                if keyword_lower in task:
                    results.append({
                        "session_id": data["session_id"],
                        "task": data.get("task", "")[:150],
                        "agent": data.get("agent", ""),
                        "updated_at": data.get("updated_at", ""),
                        "score": 1.0 if keyword_lower == task else 0.5,
                    })
            except Exception:
                continue

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    # ================================================================
    # 维护
    # ================================================================

    def cleanup_old_sessions(self, max_age_days: int = None):
        """清理过期会话（移到归档目录）"""
        max_age = max_age_days or self.MAX_SESSION_AGE_DAYS
        cutoff = datetime.now() - timedelta(days=max_age)
        count = 0

        for f in self.session_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    archive_path = self.archive_dir / f.name
                    f.rename(archive_path)
                    # 从缓存移除
                    sid = f.stem
                    if sid in self._cache:
                        del self._cache[sid]
                    count += 1
            except Exception:
                continue

        return count

    def get_stats(self) -> dict:
        """获取存储统计"""
        sessions = list(self.session_dir.glob("*.json"))
        archives = list(self.archive_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in sessions + archives)

        return {
            "active_sessions": len(sessions),
            "archived_sessions": len(archives),
            "cached_sessions": len(self._cache),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    # ================================================================
    # 内部方法
    # ================================================================

    def _save_session(self, session_id: str, data: dict):
        """保存会话到文件"""
        filepath = self.session_dir / f"{session_id}.json"
        try:
            filepath.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[SessionMemory] 保存失败 ({session_id}): {e}")

    def _read_session_file(self, session_id: str) -> Optional[dict]:
        """从文件读取会话"""
        filepath = self.session_dir / f"{session_id}.json"
        if not filepath.exists():
            return None
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _cache_put(self, session_id: str, data: dict):
        """放入缓存（LRU 淘汰）"""
        if session_id in self._cache:
            self._access_order.remove(session_id)
        self._cache[session_id] = data
        self._access_order.append(session_id)

        # 淘汰最旧的
        while len(self._cache) > self.MAX_SESSIONS_IN_MEMORY:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

    def _touch(self, session_id: str):
        """标记最近访问"""
        if session_id in self._access_order:
            self._access_order.remove(session_id)
        self._access_order.append(session_id)


# ============================================================
# 模块级便捷函数
# ============================================================

_memory_instance = None


def get_memory() -> SessionMemory:
    """获取全局会话记忆实例"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = SessionMemory()
    return _memory_instance


# ============================================================
# 自测试
# ============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("Session Memory — 自测试")
    print("=" * 55)

    mem = SessionMemory()

    # 1. 创建会话
    print("\n[1] 创建会话...")
    sid = mem.create_session(agent="trae_control",
                             task="创建 React 登录组件")
    print(f"  session_id: {sid}")

    # 2. 添加消息
    print("\n[2] 添加消息...")
    mem.add_message(sid, "user", "请创建一个 React 登录组件")
    mem.add_message(sid, "agent", "正在分析需求，准备创建组件...")
    print(f"  已添加 2 条消息")

    # 3. 添加结果
    print("\n[3] 添加结果...")
    mem.add_result(sid, True, "Login 组件已创建: src/components/Login.tsx")
    mem.add_result(sid, False, "CSS 样式写入失败: IDE 未响应")
    print(f"  已添加 2 条结果")

    # 4. 获取上下文
    print("\n[4] 获取上下文...")
    ctx = mem.get_context(sid)
    print(f"  摘要: {ctx['summary']}")
    print(f"  消息数: {ctx['total_messages']}")
    print(f"  结果数: {ctx['total_results']}")

    # 5. 格式化上下文
    print("\n[5] 格式化上下文:")
    formatted = mem.get_formatted_context(sid)
    print(formatted[:500])

    # 6. 列表
    print("\n[6] 会话列表...")
    sessions = mem.list_sessions(limit=5)
    for s in sessions:
        print(f"  [{s['session_id']}] {s['agent']}: {s['task'][:50]}")

    # 7. 统计
    print("\n[7] 存储统计...")
    stats = mem.get_stats()
    print(f"  活跃: {stats['active_sessions']}, "
          f"缓存: {stats['cached_sessions']}, "
          f"大小: {stats['total_size_mb']} MB")

    print("\n" + "=" * 55)
    print("测试完成")
