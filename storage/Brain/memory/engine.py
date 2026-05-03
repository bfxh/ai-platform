#!/usr/bin/env python
"""Brain Memory Engine - 核心记忆持久化引擎

实现:
- working_memory: 内存LRU缓存 (max 50条)
- session_memory: 会话摘要持久化 (最近100个会话)
- knowledge_base: 知识库管理 (5个分类)
- patterns: 模式库存储
- cleanup: 自动清理 (max 50MB)
- user_profile: 用户画像加载
"""

import json
import os
import shutil
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ─── 路径配置 ───────────────────────────────────────────
ROOT = Path(__file__).parent.parent  # storage/Brain/
MEMORY_DIR = ROOT / "memory"
SESSIONS_DIR = MEMORY_DIR / "sessions"
KNOWLEDGE_DIR = MEMORY_DIR / "knowledge"
PATTERNS_DIR = MEMORY_DIR / "patterns"
CONFIG_FILE = MEMORY_DIR / "config.json"
PROFILE_FILE = MEMORY_DIR / "user_profile.json"
PATTERNS_FILE = ROOT / "optimized_prompts" / "patterns.json"

# 知识库分类子目录
CATEGORY_DIRS = {
    "user_preferences": KNOWLEDGE_DIR / "user_preferences",
    "project_context": KNOWLEDGE_DIR / "project_context",
    "error_solutions": KNOWLEDGE_DIR / "error_solutions",
    "tool_usage_patterns": KNOWLEDGE_DIR / "tool_usage_patterns",
    "domain_knowledge": KNOWLEDGE_DIR / "domain_knowledge",
}

MAX_TOTAL_SIZE_MB = 500
MAX_SESSIONS = 100
MAX_WORKING_ITEMS = 50


class LRUCache(OrderedDict):
    """线程安全的LRU缓存"""
    def __init__(self, maxsize: int = 50):
        super().__init__()
        self.maxsize = maxsize
        self._lock = threading.Lock()

    def get(self, key: str, default=None):
        with self._lock:
            if key in self:
                self.move_to_end(key)
                return self[key]
            return default

    def put(self, key: str, value: Any):
        with self._lock:
            if key in self:
                self.move_to_end(key)
            self[key] = value
            if len(self) > self.maxsize:
                self.popitem(last=False)


class MemoryEngine:
    """大脑记忆引擎 - 管理所有记忆类型"""

    def __init__(self):
        self._ensure_dirs()
        self.working_memory = LRUCache(MAX_WORKING_ITEMS)
        self.user_profile = self._load_user_profile()
        self.config = self._load_config()
        self._stats = {"saves": 0, "loads": 0, "recalls": 0, "cleanups": 0}

    # ─── 初始化 ───────────────────────────────────────

    def _ensure_dirs(self):
        """确保所有目录存在"""
        for d in [SESSIONS_DIR, KNOWLEDGE_DIR, PATTERNS_DIR]:
            d.mkdir(parents=True, exist_ok=True)
        for d in CATEGORY_DIRS.values():
            d.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {}

    def _load_user_profile(self) -> dict:
        if PROFILE_FILE.exists():
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        return {}

    # ─── Working Memory (短时记忆) ─────────────────────

    def wm_set(self, key: str, value: Any):
        """写入工作记忆"""
        self.working_memory.put(key, value)

    def wm_get(self, key: str, default=None):
        """读取工作记忆"""
        return self.working_memory.get(key, default)

    def wm_clear(self):
        """清空工作记忆"""
        self.working_memory.clear()

    def wm_all(self) -> dict:
        """获取所有工作记忆"""
        return dict(self.working_memory)

    # ─── Session Memory (会话记忆) ─────────────────────

    def save_session(self, session_id: str, summary: str,
                     key_decisions: list = None,
                     user_prefs: dict = None,
                     lessons: list = None,
                     files_touched: list = None,
                     tools_used: list = None,
                     duration_minutes: int = 0) -> str:
        """保存会话摘要"""
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "key_decisions": key_decisions or [],
            "user_preferences": user_prefs or {},
            "lessons_learned": lessons or [],
            "files_touched": files_touched or [],
            "tools_used": tools_used or [],
            "duration_minutes": duration_minutes,
        }
        filepath = SESSIONS_DIR / f"{session_id}.json"
        filepath.write_text(
            json.dumps(session_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self._stats["saves"] += 1
        self._enforce_session_limit()
        self._enforce_size_limit()
        return str(filepath)

    def load_session(self, session_id: str) -> Optional[dict]:
        """加载指定会话"""
        filepath = SESSIONS_DIR / f"{session_id}.json"
        if filepath.exists():
            self._stats["loads"] += 1
            return json.loads(filepath.read_text(encoding="utf-8"))
        return None

    def list_sessions(self, limit: int = 20) -> list:
        """列出最近的会话"""
        files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        sessions = []
        for f in files[:limit]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id", f.stem),
                    "timestamp": data.get("timestamp", ""),
                    "summary": (data.get("summary", "") or "")[:200],
                    "duration_minutes": data.get("duration_minutes", 0),
                })
            except Exception:
                sessions.append({"session_id": f.stem, "error": "parse_failed"})
        return sessions

    def search_sessions(self, keyword: str, limit: int = 10) -> list:
        """关键词搜索会话"""
        keyword_lower = keyword.lower()
        results = []
        for f in sorted(SESSIONS_DIR.glob("*.json"),
                       key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                content = f.read_text(encoding="utf-8").lower()
                if keyword_lower in content:
                    data = json.loads(content)  # 复用已读取的内容，避免双读
                    score = content.count(keyword_lower)
                    results.append({
                        "session_id": f.stem,
                        "timestamp": data.get("timestamp", ""),
                        "summary": (data.get("summary", "") or "")[:300],
                        "relevance": min(score, 100),
                    })
            except Exception:
                continue
            if len(results) >= limit:
                break
        return results

    def _enforce_session_limit(self):
        """强制执行会话数量限制"""
        files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime
        )
        while len(files) > MAX_SESSIONS:
            files[0].unlink(missing_ok=True)
            files.pop(0)
            self._stats["cleanups"] += 1

    # ─── Knowledge Base (知识库) ───────────────────────

    def kb_save(self, category: str, entry_id: str, title: str,
                content: str, tags: list = None,
                importance: int = 5) -> str:
        """保存知识条目"""
        if category not in CATEGORY_DIRS:
            raise ValueError(f"未知分类: {category}. 有效分类: {list(CATEGORY_DIRS.keys())}")

        entry = {
            "id": entry_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "importance": importance,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "access_count": 0,
        }
        filepath = CATEGORY_DIRS[category] / f"{entry_id}.json"
        filepath.write_text(
            json.dumps(entry, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self._stats["saves"] += 1
        return str(filepath)

    def kb_load(self, category: str, entry_id: str) -> Optional[dict]:
        """加载知识条目"""
        filepath = CATEGORY_DIRS.get(category, KNOWLEDGE_DIR) / f"{entry_id}.json"
        if filepath.exists():
            entry = json.loads(filepath.read_text(encoding="utf-8"))
            entry["access_count"] = entry.get("access_count", 0) + 1
            entry["last_accessed"] = datetime.now().isoformat()
            filepath.write_text(
                json.dumps(entry, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            self._stats["loads"] += 1
            return entry
        return None

    def kb_search(self, keyword: str, category: str = None,
                  limit: int = 10) -> list:
        """搜索知识库"""
        keyword_lower = keyword.lower()
        results = []

        search_dirs = (
            [CATEGORY_DIRS[category]] if category and category in CATEGORY_DIRS
            else list(CATEGORY_DIRS.values())
        )

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for f in search_dir.glob("*.json"):
                try:
                    content = f.read_text(encoding="utf-8").lower()
                    if keyword_lower in content:
                        entry = json.loads(f.read_text(encoding="utf-8"))
                        score = content.count(keyword_lower) + entry.get("importance", 0)
                        results.append({
                            "id": entry.get("id", f.stem),
                            "category": search_dir.name,
                            "title": entry.get("title", ""),
                            "content": (entry.get("content", "") or "")[:300],
                            "tags": entry.get("tags", []),
                            "importance": entry.get("importance", 5),
                            "relevance": score,
                        })
                except Exception:
                    continue

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def kb_list_categories(self) -> list:
        """列出所有知识分类及条目数"""
        cats = []
        for cat_name, cat_dir in CATEGORY_DIRS.items():
            count = len(list(cat_dir.glob("*.json"))) if cat_dir.exists() else 0
            cats.append({"name": cat_name, "count": count})
        return cats

    def kb_list_recent(self, category: str = None, limit: int = 20) -> list:
        """列出最近修改的知识条目"""
        search_dirs = (
            [CATEGORY_DIRS[category]] if category
            else list(CATEGORY_DIRS.values())
        )
        all_files = []
        for d in search_dirs:
            if d.exists():
                all_files.extend(d.glob("*.json"))

        all_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        entries = []
        for f in all_files[:limit]:
            try:
                entry = json.loads(f.read_text(encoding="utf-8"))
                entries.append({
                    "id": entry.get("id", f.stem),
                    "category": f.parent.name,
                    "title": entry.get("title", ""),
                    "importance": entry.get("importance", 5),
                    "updated_at": entry.get("updated_at", ""),
                })
            except Exception:
                continue
        return entries

    # ─── Patterns (模式库) ─────────────────────────────

    def save_pattern(self, pattern_id: str, name: str,
                     description: str, template: str,
                     tags: list = None, domain: str = "general") -> str:
        """保存模式"""
        pattern = {
            "id": pattern_id,
            "name": name,
            "description": description,
            "template": template,
            "tags": tags or [],
            "domain": domain,
            "created_at": datetime.now().isoformat(),
            "use_count": 0,
            "success_rate": 1.0,
        }
        filepath = PATTERNS_DIR / f"{pattern_id}.json"
        filepath.write_text(
            json.dumps(pattern, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return str(filepath)

    def load_pattern(self, pattern_id: str) -> Optional[dict]:
        """加载模式"""
        filepath = PATTERNS_DIR / f"{pattern_id}.json"
        if filepath.exists():
            return json.loads(filepath.read_text(encoding="utf-8"))
        return None

    def search_patterns(self, keyword: str, domain: str = None,
                        limit: int = 10) -> list:
        """搜索模式"""
        keyword_lower = keyword.lower()
        results = []
        for f in PATTERNS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if domain and data.get("domain") != domain:
                    continue
                text = f"{data.get('name','')} {data.get('description','')} {' '.join(data.get('tags',[]))}".lower()
                if keyword_lower in text:
                    results.append({
                        "id": data["id"],
                        "name": data["name"],
                        "description": data["description"],
                        "tags": data.get("tags", []),
                        "domain": data.get("domain", "general"),
                        "use_count": data.get("use_count", 0),
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["use_count"], reverse=True)
        return results[:limit]

    def record_pattern_use(self, pattern_id: str, success: bool = True):
        """记录模式使用情况"""
        filepath = PATTERNS_DIR / f"{pattern_id}.json"
        if filepath.exists():
            data = json.loads(filepath.read_text(encoding="utf-8"))
            data["use_count"] = data.get("use_count", 0) + 1
            # 加权更新成功率 (新结果权重30%)
            old_rate = data.get("success_rate", 1.0)
            data["success_rate"] = old_rate * 0.7 + (1.0 if success else 0.0) * 0.3
            data["last_used"] = datetime.now().isoformat()
            filepath.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

    # ─── Cleanup ───────────────────────────────────────

    def _enforce_size_limit(self):
        """强制执行总大小限制"""
        total = self._calc_total_size()
        if total < MAX_TOTAL_SIZE_MB * 1024 * 1024:
            return

        # 清理旧会话
        session_files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime
        )
        while self._calc_total_size() > MAX_TOTAL_SIZE_MB * 1024 * 1024 * 0.8:
            if session_files:
                session_files[0].unlink(missing_ok=True)
                session_files.pop(0)
            else:
                break
        self._stats["cleanups"] += 1

    def _calc_total_size(self) -> int:
        """计算记忆系统总大小"""
        total = 0
        for d in [SESSIONS_DIR, KNOWLEDGE_DIR, PATTERNS_DIR]:
            if d.exists():
                for f in d.rglob("*.json"):
                    try:
                        total += f.stat().st_size
                    except OSError:
                        pass
        return total

    # ─── User Profile ──────────────────────────────────

    def update_profile(self, updates: dict):
        """更新用户画像"""
        self.user_profile.update(updates)
        self.user_profile["updated_at"] = datetime.now().isoformat()
        PROFILE_FILE.write_text(
            json.dumps(self.user_profile, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_preference(self, key: str, default=None):
        """获取用户偏好"""
        return self.user_profile.get("preferences", {}).get(key, default)

    # ─── 统计 ──────────────────────────────────────────

    def stats(self) -> dict:
        """获取引擎统计"""
        return {
            **self._stats,
            "working_memory_size": len(self.working_memory),
            "session_count": len(list(SESSIONS_DIR.glob("*.json"))),
            "knowledge_entries": sum(
                len(list(d.glob("*.json")))
                for d in CATEGORY_DIRS.values() if d.exists()
            ),
            "pattern_count": len(list(PATTERNS_DIR.glob("*.json"))),
            "total_size_mb": round(self._calc_total_size() / 1024 / 1024, 2),
        }

    def health_check(self) -> dict:
        """健康检查"""
        issues = []
        if len(self.working_memory) >= MAX_WORKING_ITEMS:
            issues.append("working_memory_full")
        if self._calc_total_size() > MAX_TOTAL_SIZE_MB * 1024 * 1024 * 0.9:
            issues.append("size_warning")

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "stats": self.stats(),
        }

    # ─── 知识库升级方法 ──────────────────────────────────────

    def migrate_topics(self) -> dict:
        """迁移话题文件到分类子目录"""
        from storage.Brain.tools.migrate_topics import migrate_topics
        return migrate_topics()

    def import_from_qoder(self, path: str = None) -> dict:
        """从 Qoder 导入对话记录"""
        from storage.Brain.importers.qoder_importer import QoderImporter
        importer = QoderImporter(path)
        return importer.import_all(self)

    def import_from_trae(self, path: str = None) -> dict:
        """从 TRAE 导入对话记录"""
        try:
            from storage.Brain.importers.trae_importer import TraeImporter
            importer = TraeImporter(path)
            return importer.import_all(self)
        except ImportError:
            return {"error": "TRAE importer not implemented yet"}

    def search_all(self, keyword: str, limit: int = 10) -> list:
        """跨所有数据源的混合搜索"""
        from storage.Brain.search.hybrid_search import HybridSearchEngine
        searcher = HybridSearchEngine()
        return searcher.search(keyword, source="all", limit=limit)

    def rebuild_index(self) -> dict:
        """重建知识库索引"""
        from storage.Brain.indexer.auto_indexer import AutoIndexer
        indexer = AutoIndexer()
        return indexer.rebuild_index()


# ─── 全局单例 ───────────────────────────────────────────
_engine_instance: Optional[MemoryEngine] = None
_engine_lock = threading.Lock()


def get_memory_engine() -> MemoryEngine:
    """获取MemoryEngine全局单例"""
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            if _engine_instance is None:
                _engine_instance = MemoryEngine()
    return _engine_instance


# ─── CLI 测试入口 ───────────────────────────────────────
if __name__ == "__main__":
    engine = get_memory_engine()
    print("=== Brain Memory Engine Status ===")
    print(json.dumps(engine.stats(), ensure_ascii=False, indent=2))
    print("\n=== Health Check ===")
    print(json.dumps(engine.health_check(), ensure_ascii=False, indent=2))
    print("\n=== Categories ===")
    print(json.dumps(engine.kb_list_categories(), ensure_ascii=False, indent=2))
