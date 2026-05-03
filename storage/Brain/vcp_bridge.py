#!/usr/bin/env python3
"""
VCP TagMemo Bridge — 将 VCPToolBox 的高级语义记忆系统桥接到 AI 平台

VCP 的 TagMemo "Wave" 算法相比当前 Brain 系统的优势：
  - EPA 嵌入投影分析 → 理解查询的"语义世界"
  - ResidualPyramid 多层分解 → 90% 能量解释率
  - SpikePropagation 脉冲传播 → 跨概念关联发现
  - 向量索引 → O(log n) 语义搜索 vs 当前的关键词 O(n)

工作模式:
  1. 优先尝试连接 VCPToolBox (localhost:6005)
  2. VCP 不可用时自动降级到本地 Brain 记忆系统
  3. 异步批量同步：本地 bug 记忆 ↔ VCP 知识库

用法:
  bridge = VCPBridge()
  results = bridge.semantic_search("如何修复 TensorFlow 导入错误")
  bugs = bridge.search_similar_bugs("NullPointerException")
  context = bridge.recall_for_task("写一个 Minecraft 模组", files=["src/main.py"])
"""

import hashlib
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# ─── 路径配置 ───────────────────────────────────────────
ROOT = Path(__file__).parent  # storage/Brain/
VCP_BASE_URL = os.environ.get("VCP_URL", "http://127.0.0.1:6005")
VCP_API_KEY = os.environ.get("VCP_Key", "")
VCP_TIMEOUT = 10  # 连接超时（秒）
SYNC_BATCH_SIZE = 50

_KB_MANAGER_AVAILABLE = False


def _check_vcp_available() -> bool:
    """检查 VCPToolBox 是否在线。"""
    try:
        req = urllib.request.Request(
            f"{VCP_BASE_URL}/api/status",
            headers={"Authorization": f"Bearer {VCP_API_KEY}"},
        )
        with urllib.request.urlopen(req, timeout=VCP_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


class VCPBridge:
    """
    VCP 记忆桥 — 提供语义级别的记忆搜索与召回

    与本地 Brain 的差异:
      - search_similar(): Brain 用关键词计数，VCP 用向量余弦相似度
      - recall_for_task(): Brain 用触发词匹配，VCP 用语义理解
      - 反模式提取: Brain 手动规则，VCP 自动聚类发现
    """

    def __init__(self, brain_engine=None):
        self._vcp_available = _check_vcp_available()
        self._brain_engine = brain_engine
        self._sync_dir = ROOT / "vcp_sync"
        self._sync_dir.mkdir(parents=True, exist_ok=True)
        self._sync_state = self._load_sync_state()

    @property
    def vcp_available(self) -> bool:
        return self._vcp_available

    # ─── 语义搜索 ──────────────────────────────────────

    def semantic_search(self, query: str, limit: int = 10,
                        use_vcp: bool = True) -> list:
        """
        语义搜索 — 理解查询含义而非简单关键词匹配。

        VCP 模式: 使用 TagMemo EPA+ResidualPyramid 分解
        Fallback: 使用本地 Brain 的关键词搜索
        """
        if use_vcp and self._vcp_available:
            return self._vcp_semantic_search(query, limit)
        return self._brain_keyword_search(query, limit)

    def _vcp_semantic_search(self, query: str, limit: int) -> list:
        """通过 VCPToolBox 的 KnowledgeBaseManager 进行语义搜索。"""
        try:
            payload = json.dumps({
                "action": "query_semantic",
                "query": query,
                "limit": limit,
                "include_antipatterns": True,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{VCP_BASE_URL}/api/knowledge/query",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {VCP_API_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=VCP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("results", [])
        except Exception as e:
            print(f"[VCP Bridge] 语义搜索失败，降级到本地: {e}")
            self._vcp_available = False
            return self._brain_keyword_search(query, limit)

    def _brain_keyword_search(self, query: str, limit: int) -> list:
        """本地 Brain 关键词搜索（VCP 不可用时的 fallback）。"""
        if self._brain_engine is None:
            from .memory.engine import get_memory_engine
            self._brain_engine = get_memory_engine()

        sessions = self._brain_engine.search_sessions(query, limit=limit)
        return [{
            "source": "brain",
            "type": "session",
            "score": s.get("relevance", 0),
            "content": s.get("summary", ""),
            "id": s.get("session_id", ""),
            "timestamp": s.get("timestamp", ""),
        } for s in sessions]

    # ─── Bug 搜索（增强版）──────────────────────────────

    def search_similar_bugs(self, error_message: str, error_type: str = "",
                            files: list = None, limit: int = 10) -> list:
        """
        搜索类似 Bug — 比本地 bug_memory 更智能。

        VCP 模式: 使用向量相似度 + 反模式匹配
        Fallback: 本地 bug_memory 关键词索引
        """
        query = f"{error_type} {error_message}"
        if files:
            query += " " + " ".join(files)

        if self._vcp_available:
            return self._vcp_bug_search(query, error_type, limit)

        # Fallback to local
        from .memory.bug_memory import BugMemoryEngine
        bug_engine = BugMemoryEngine()
        return bug_engine.search_similar(query, limit=limit)

    def _vcp_bug_search(self, query: str, error_type: str, limit: int) -> list:
        """通过 VCP 搜索相关 bug（向量相似度 + 反模式）。"""
        try:
            payload = json.dumps({
                "action": "search_bugs",
                "query": query,
                "error_type": error_type,
                "limit": limit,
                "include_antipatterns": True,
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{VCP_BASE_URL}/api/bugs/search",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {VCP_API_KEY}",
                },
            )
            with urllib.request.urlopen(req, timeout=VCP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("bugs", [])
                antipatterns = data.get("antipatterns", [])
                return results + antipatterns
        except Exception as e:
            self._vcp_available = False
            from .memory.bug_memory import BugMemoryEngine
            return BugMemoryEngine().search_similar(query, limit=limit)

    # ─── 任务上下文召回 ─────────────────────────────────

    def recall_for_task(self, task_description: str,
                        files_involved: list = None) -> dict:
        """
        任务前召回相关上下文 — 自动注入经验。

        Returns:
            {
                "relevant_sessions": [...],   # 相关历史会话
                "relevant_bugs": [...],       # 相关 bug 教训
                "antipatterns": [...],        # 反模式警告
                "semantic_context": "...",    # VCP 语义理解摘要
                "warnings": [...],            # 针对当前任务的警告
            }
        """
        result = {
            "relevant_sessions": [],
            "relevant_bugs": [],
            "antipatterns": [],
            "semantic_context": "",
            "warnings": [],
        }

        # 1. 语义搜索（VCP 优先）
        if self._vcp_available:
            semantic_results = self._vcp_semantic_search(
                task_description, limit=5
            )
            result["relevant_sessions"] = [
                r for r in semantic_results if r.get("type") == "session"
            ]
            result["antipatterns"] = [
                r for r in semantic_results if r.get("type") == "antipattern"
            ]
            # VCP 提供的语义摘要
            for r in semantic_results:
                if r.get("type") == "semantic_context":
                    result["semantic_context"] = r.get("content", "")
                    break

        # 2. Bug 搜索
        result["relevant_bugs"] = self.search_similar_bugs(
            task_description,
            files=files_involved,
            limit=10,
        )

        # 3. 本地 Brain fallback（补充）
        if self._brain_engine:
            sessions = self._brain_engine.search_sessions(
                task_description, limit=5
            )
            existing_ids = {s.get("id") for s in result["relevant_sessions"]}
            for s in sessions:
                if s.get("session_id") not in existing_ids:
                    result["relevant_sessions"].append({
                        "source": "brain",
                        "type": "session",
                        "score": s.get("relevance", 0),
                        "content": s.get("summary", ""),
                        "id": s.get("session_id", ""),
                    })

        # 4. 生成警告
        if result["relevant_bugs"]:
            result["warnings"].append(
                f"⚠️ 发现 {len(result['relevant_bugs'])} 个相关历史 bug，请避免重蹈覆辙"
            )
        if result["antipatterns"]:
            result["warnings"].append(
                f"🚫 发现 {len(result['antipatterns'])} 个反模式，请注意规避"
            )

        return result

    # ─── 同步 ──────────────────────────────────────────

    def sync_bugs_to_vcp(self, max_bugs: int = SYNC_BATCH_SIZE) -> int:
        """将本地 bug 记忆同步到 VCP 知识库。"""
        if not self._vcp_available:
            return 0

        from .memory.bug_memory import BugMemoryEngine
        bug_engine = BugMemoryEngine()

        synced = 0
        for bug_file in bug_engine._bugs_dir.glob("bug_*.json"):
            bug_id = bug_file.stem
            if bug_id in self._sync_state.get("synced_bugs", set()):
                continue

            try:
                bug = json.loads(bug_file.read_text(encoding="utf-8"))
                payload = json.dumps({
                    "action": "record_bug",
                    "bug": bug,
                }).encode("utf-8")
                req = urllib.request.Request(
                    f"{VCP_BASE_URL}/api/bugs/record",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {VCP_API_KEY}",
                    },
                )
                with urllib.request.urlopen(req, timeout=VCP_TIMEOUT):
                    self._sync_state.setdefault("synced_bugs", set()).add(bug_id)
                    synced += 1
            except Exception:
                continue

            if synced >= max_bugs:
                break

        if synced > 0:
            self._save_sync_state()
        return synced

    def _load_sync_state(self) -> dict:
        state_file = self._sync_dir / "sync_state.json"
        if state_file.exists():
            return json.loads(state_file.read_text(encoding="utf-8"))
        return {"synced_bugs": [], "last_sync": None}

    def _save_sync_state(self):
        self._sync_state["last_sync"] = datetime.now().isoformat()
        state_file = self._sync_dir / "sync_state.json"
        state_file.write_text(
            json.dumps(self._sync_state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_status(self) -> dict:
        """获取桥接状态。"""
        return {
            "vcp_available": self._vcp_available,
            "vcp_url": VCP_BASE_URL,
            "synced_bugs": len(self._sync_state.get("synced_bugs", [])),
            "last_sync": self._sync_state.get("last_sync"),
            "brain_engine": self._brain_engine is not None,
        }


# ─── 便捷函数 ───────────────────────────────────────────

_bridge_instance = None


def get_vcp_bridge() -> VCPBridge:
    """获取 VCP 桥接单例。"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = VCPBridge()
    return _bridge_instance


def semantic_recall(query: str, limit: int = 10) -> list:
    """快捷语义搜索。"""
    return get_vcp_bridge().semantic_search(query, limit)


def recall_bugs(error_message: str, error_type: str = "",
                files: list = None) -> list:
    """快捷 bug 搜索。"""
    return get_vcp_bridge().search_similar_bugs(
        error_message, error_type, files
    )


def recall_for_task(task: str, files: list = None) -> dict:
    """快捷任务上下文召回。"""
    return get_vcp_bridge().recall_for_task(task, files)


if __name__ == "__main__":
    bridge = get_vcp_bridge()
    print(f"VCP Bridge Status: {json.dumps(bridge.get_status(), indent=2, ensure_ascii=False)}")

    if bridge.vcp_available:
        print("\n[VCP] Testing semantic search...")
        results = bridge.semantic_search("Minecraft 模组开发常见错误", limit=3)
        for r in results:
            print(f"  [{r.get('type', '?')}] score={r.get('score', 0):.2f} {r.get('content', '')[:100]}")
    else:
        print("\n[VCP] Not available, using local Brain fallback")
        results = bridge.semantic_search("Python import error", limit=3)
        for r in results:
            print(f"  [brain] score={r.get('score', 0)} {r.get('content', '')[:100]}")
