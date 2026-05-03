#!/usr/bin/env python
"""Brain Auto Indexer - 自动索引构建器

实现:
- 全量索引重建 (扫描所有数据源)
- 单条目增量更新 (add/update/remove)
- 标签云自动生成
- 分类计数统计
- v2.0 索引格式 (兼容旧格式)
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

BRAIN_ROOT = Path(__file__).parent.parent
TOPICS_DIR = BRAIN_ROOT / "topics"
KNOWLEDGE_DIR = BRAIN_ROOT / "memory" / "knowledge"
SESSIONS_DIR = BRAIN_ROOT / "memory" / "sessions"
PATTERNS_DIR = BRAIN_ROOT / "memory" / "patterns"
INDEX_FILE = TOPICS_DIR / "_index.json"

CATEGORY_DIRS = {
    "user_preferences": KNOWLEDGE_DIR / "user_preferences",
    "project_context": KNOWLEDGE_DIR / "project_context",
    "error_solutions": KNOWLEDGE_DIR / "error_solutions",
    "tool_usage_patterns": KNOWLEDGE_DIR / "tool_usage_patterns",
    "domain_knowledge": KNOWLEDGE_DIR / "domain_knowledge",
}

TOPIC_CATEGORY_META = {
    "ai_models": {"description": "AI模型相关话题"},
    "mcp_servers": {"description": "MCP服务器开发话题"},
    "game_dev": {"description": "游戏开发话题"},
    "system_ops": {"description": "系统运维话题"},
    "project_mgmt": {"description": "项目管理话题"},
    "coding_patterns": {"description": "代码模式话题"},
    "troubleshooting": {"description": "故障排查话题"},
    "uncategorized": {"description": "未分类话题"},
}

KNOWLEDGE_CATEGORY_META = {
    "user_preferences": {"description": "用户偏好"},
    "project_context": {"description": "项目上下文"},
    "error_solutions": {"description": "错误解决方案"},
    "tool_usage_patterns": {"description": "工具使用模式"},
    "domain_knowledge": {"description": "领域知识"},
}


class AutoIndexer:
    """自动索引器 - 构建和维护 Brain 知识库索引"""

    def __init__(self):
        self._index = self._load_index()

    def _load_index(self) -> dict:
        if INDEX_FILE.exists():
            try:
                data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return self._migrate_v1_to_v2(data)
                if isinstance(data, dict) and data.get("version") != "2.0":
                    return self._migrate_v1_to_v2(data.get("entries", []))
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return self._empty_index()

    def _empty_index(self) -> dict:
        categories = {}
        for cat, meta in TOPIC_CATEGORY_META.items():
            categories[cat] = {"count": 0, "description": meta["description"]}

        knowledge_categories = {}
        for cat, meta in KNOWLEDGE_CATEGORY_META.items():
            knowledge_categories[cat] = {"count": 0, "description": meta["description"]}

        return {
            "version": "2.0",
            "updated_at": "",
            "categories": categories,
            "knowledge_categories": knowledge_categories,
            "tag_cloud": {},
            "total_topics": 0,
            "total_knowledge": 0,
            "total_sessions": 0,
            "total_patterns": 0,
            "entries": [],
        }

    def _migrate_v1_to_v2(self, v1_entries: list) -> dict:
        idx = self._empty_index()
        for entry in v1_entries:
            if isinstance(entry, dict):
                cat = entry.get("category", "uncategorized")
                if cat not in idx["categories"]:
                    cat = "uncategorized"
                idx["entries"].append({
                    "id": entry.get("id", ""),
                    "title": entry.get("title", ""),
                    "tags": entry.get("tags", []),
                    "category": cat,
                    "file": entry.get("file", ""),
                    "score": entry.get("score", entry.get("importance", 5)),
                    "date": entry.get("date", ""),
                })
        idx["total_topics"] = len(idx["entries"])
        self._recompute_stats(idx)
        return idx

    def update_entry(self, category: str, entry_data: dict):
        """添加或更新单条索引条目"""
        entry_id = entry_data.get("id", "")
        if not entry_id:
            return

        for i, existing in enumerate(self._index["entries"]):
            if existing.get("id") == entry_id:
                self._index["entries"][i] = {
                    "id": entry_id,
                    "title": entry_data.get("title", existing.get("title", "")),
                    "tags": entry_data.get("tags", existing.get("tags", [])),
                    "category": category,
                    "file": entry_data.get("file", existing.get("file", "")),
                    "score": entry_data.get("score", entry_data.get("importance", existing.get("score", 5))),
                    "date": entry_data.get("date", existing.get("date", "")),
                }
                self._recompute_stats(self._index)
                self.save()
                return

        new_entry = {
            "id": entry_id,
            "title": entry_data.get("title", ""),
            "tags": entry_data.get("tags", []),
            "category": category,
            "file": entry_data.get("file", ""),
            "score": entry_data.get("score", entry_data.get("importance", 5)),
            "date": entry_data.get("date", datetime.now().isoformat()),
        }
        self._index["entries"].append(new_entry)
        self._recompute_stats(self._index)
        self.save()

    def remove_entry(self, entry_id: str):
        """从索引中移除条目"""
        before = len(self._index["entries"])
        self._index["entries"] = [
            e for e in self._index["entries"] if e.get("id") != entry_id
        ]
        if len(self._index["entries"]) < before:
            self._recompute_stats(self._index)
            self.save()

    def rebuild_index(self) -> dict:
        """全量重建索引 - 扫描所有数据源并重新生成"""
        idx = self._empty_index()
        idx["updated_at"] = datetime.now().isoformat()

        topic_entries = []
        topic_files = list(TOPICS_DIR.glob("*.json"))
        for cat_dir_name in TOPIC_CATEGORY_META:
            cat_dir = TOPICS_DIR / cat_dir_name
            if cat_dir.exists() and cat_dir.is_dir():
                topic_files.extend(cat_dir.glob("*.json"))

        seen = set()
        for f in topic_files:
            if f.name == "_index.json" or f.stem in seen:
                continue
            seen.add(f.stem)

            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                category = "uncategorized"
                if f.parent != TOPICS_DIR and f.parent.name in TOPIC_CATEGORY_META:
                    category = f.parent.name

                topic_entries.append({
                    "id": data.get("id", f.stem),
                    "title": data.get("title", ""),
                    "tags": data.get("tags", []),
                    "category": category,
                    "file": f.name if f.parent == TOPICS_DIR else f"{category}/{f.name}",
                    "score": data.get("score", 5),
                    "date": data.get("date", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

        idx["entries"] = topic_entries
        idx["total_topics"] = len(topic_entries)

        knowledge_total = 0
        for cat_name, cat_dir in CATEGORY_DIRS.items():
            count = 0
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.json")))
            idx["knowledge_categories"][cat_name]["count"] = count
            knowledge_total += count
        idx["total_knowledge"] = knowledge_total

        idx["total_sessions"] = (
            len(list(SESSIONS_DIR.glob("*.json"))) if SESSIONS_DIR.exists() else 0
        )
        idx["total_patterns"] = (
            len(list(PATTERNS_DIR.glob("*.json"))) if PATTERNS_DIR.exists() else 0
        )

        self._recompute_stats(idx)
        self._index = idx
        self.save()
        return self.get_stats()

    def get_stats(self) -> dict:
        """返回当前索引统计信息"""
        idx = self._index
        return {
            "version": idx.get("version", "2.0"),
            "updated_at": idx.get("updated_at", ""),
            "total_topics": idx.get("total_topics", 0),
            "total_knowledge": idx.get("total_knowledge", 0),
            "total_sessions": idx.get("total_sessions", 0),
            "total_patterns": idx.get("total_patterns", 0),
            "categories": idx.get("categories", {}),
            "knowledge_categories": idx.get("knowledge_categories", {}),
            "tag_cloud_top10": dict(
                Counter(idx.get("tag_cloud", {})).most_common(10)
            ),
            "entries_count": len(idx.get("entries", [])),
        }

    def save(self):
        """将索引写入 _index.json"""
        self._index["updated_at"] = datetime.now().isoformat()
        TOPICS_DIR.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _recompute_stats(self, idx: dict):
        """重新计算分类计数和标签云"""
        cat_counts = Counter()
        tag_counts = Counter()

        for entry in idx.get("entries", []):
            cat = entry.get("category", "uncategorized")
            cat_counts[cat] += 1
            for tag in entry.get("tags", []):
                tag_counts[tag] += 1

        for cat_name in TOPIC_CATEGORY_META:
            if cat_name in idx.get("categories", {}):
                idx["categories"][cat_name]["count"] = cat_counts.get(cat_name, 0)

        idx["tag_cloud"] = dict(tag_counts)
        idx["total_topics"] = len(idx.get("entries", []))


_indexer_instance: Optional[AutoIndexer] = None


def get_indexer() -> AutoIndexer:
    global _indexer_instance
    if _indexer_instance is None:
        _indexer_instance = AutoIndexer()
    return _indexer_instance


if __name__ == "__main__":
    indexer = get_indexer()

    print("=== Auto Indexer - Rebuilding Index ===\n")
    stats = indexer.rebuild_index()

    print(f"Version: {stats['version']}")
    print(f"Updated: {stats['updated_at']}")
    print(f"Total Topics: {stats['total_topics']}")
    print(f"Total Knowledge: {stats['total_knowledge']}")
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"Total Patterns: {stats['total_patterns']}")
    print(f"\nCategories:")
    for cat, info in stats["categories"].items():
        print(f"  {cat}: {info['count']} - {info['description']}")
    print(f"\nKnowledge Categories:")
    for cat, info in stats["knowledge_categories"].items():
        print(f"  {cat}: {info['count']}")
    print(f"\nTop Tags:")
    for tag, count in stats["tag_cloud_top10"].items():
        print(f"  {tag}: {count}")
