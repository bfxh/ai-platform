#!/usr/bin/env python
"""Brain Hybrid Search Engine - TF-IDF混合搜索引擎

实现:
- TF-IDF 语义评分 (替代简单关键词计数)
- 多数据源联合搜索 (topics/knowledge/sessions/patterns)
- 标签过滤 + 关键词搜索混合
- 重要性加权排序 (TF-IDF * 0.7 + importance * 0.3)
- 中英文混合分词
- 向后兼容旧扁平结构和新的分类子目录结构
"""

import json
import math
import re
from collections import Counter, defaultdict
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

TOPIC_CATEGORIES = [
    "ai_models", "mcp_servers", "game_dev", "system_ops",
    "project_mgmt", "coding_patterns", "troubleshooting", "uncategorized",
]


class HybridSearchEngine:
    """TF-IDF混合搜索引擎 - 跨数据源智能搜索"""

    def __init__(self):
        self._index = self._load_index()
        self._doc_count = 0
        self._df_cache = defaultdict(int)
        self._build_df_cache()

    def _load_index(self) -> dict:
        if INDEX_FILE.exists():
            try:
                return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"version": "2.0", "entries": [], "tag_cloud": {}, "categories": {}, "knowledge_categories": {}}

    def _build_df_cache(self):
        self._doc_count = 0
        self._df_cache = defaultdict(int)
        for entry in self._index.get("entries", []):
            self._doc_count += 1
            text = f"{entry.get('title', '')} {' '.join(entry.get('tags', []))}"
            tokens = set(self._tokenize(text))
            for token in tokens:
                self._df_cache[token] += 1

    def search(self, keyword: str, source: str = "all", limit: int = 10,
               tags: list = None) -> list:
        """主搜索方法

        Args:
            keyword: 搜索关键词
            source: 数据源 "all"/"topics"/"knowledge"/"sessions"/"patterns"
            limit: 返回结果数量上限
            tags: 标签过滤列表 (先按标签过滤再搜索)

        Returns:
            排序后的搜索结果列表
        """
        results = []

        if source in ("all", "topics"):
            results.extend(self._scan_topics(keyword, tags))
        if source in ("all", "knowledge"):
            results.extend(self._scan_knowledge(keyword))
        if source in ("all", "sessions"):
            results.extend(self._scan_sessions(keyword))
        if source in ("all", "patterns"):
            results.extend(self._scan_patterns(keyword))

        for r in results:
            doc_text = f"{r.get('title', '')} {r.get('content_preview', '')}"
            tfidf = self._tfidf_score(keyword, doc_text)
            importance = r.get("importance", 5)
            importance_normalized = min(importance / 10.0, 1.0)
            r["relevance"] = round(tfidf * 0.7 + importance_normalized * 0.3, 4)

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def search_by_tags(self, tags: list, limit: int = 20) -> list:
        """基于标签搜索, 使用 _index.json 加速"""
        if not tags:
            return []

        tag_set = set(t.lower() for t in tags)
        results = []

        for entry in self._index.get("entries", []):
            entry_tags = set(t.lower() for t in entry.get("tags", []))
            overlap = tag_set & entry_tags
            if overlap:
                results.append({
                    "source": "topics",
                    "id": entry.get("id", ""),
                    "title": entry.get("title", ""),
                    "content_preview": "",
                    "tags": entry.get("tags", []),
                    "importance": entry.get("score", 5),
                    "relevance": round(len(overlap) / len(tag_set), 4),
                    "category": entry.get("category", "uncategorized"),
                    "file_path": str(TOPICS_DIR / entry.get("file", "")),
                })

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def _tfidf_score(self, keyword: str, document: str) -> float:
        """计算 TF-IDF 分数"""
        doc_tokens = self._tokenize(document)
        if not doc_tokens:
            return 0.0

        kw_tokens = self._tokenize(keyword)
        if not kw_tokens:
            return 0.0

        token_counts = Counter(doc_tokens)
        total_tokens = len(doc_tokens)

        score = 0.0
        for kw_token in kw_tokens:
            tf = token_counts.get(kw_token, 0) / total_tokens if total_tokens > 0 else 0
            df = self._df_cache.get(kw_token, 0)
            idf = math.log((self._doc_count + 1) / (df + 1)) + 1 if self._doc_count > 0 else 1.0
            score += tf * idf

        return min(score, 1.0)

    def _tokenize(self, text: str) -> list:
        """中英文混合分词

        - 中文字符逐字拆分 + 双字组合
        - 英文按单词拆分
        - 统一小写
        """
        if not text:
            return []

        tokens = []

        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        for ch in chinese_chars:
            tokens.append(ch)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i + 1])

        english_words = re.findall(r'[a-zA-Z][a-zA-Z0-9_]*', text)
        for w in english_words:
            tokens.append(w.lower())

        return tokens

    def _scan_topics(self, keyword: str, tags: list = None) -> list:
        """搜索 topics, 兼容旧扁平结构和新的分类子目录"""
        results = []
        keyword_lower = keyword.lower()
        tag_set = set(t.lower() for t in tags) if tags else None

        topic_files = list(TOPICS_DIR.glob("*.json"))
        for cat_dir_name in TOPIC_CATEGORIES:
            cat_dir = TOPICS_DIR / cat_dir_name
            if cat_dir.exists() and cat_dir.is_dir():
                topic_files.extend(cat_dir.glob("*.json"))

        seen = set()
        for f in topic_files:
            if f.name == "_index.json" or f.stem in seen:
                continue
            seen.add(f.stem)

            try:
                raw = f.read_text(encoding="utf-8")
                if keyword_lower not in raw.lower():
                    continue

                data = json.loads(raw)
                entry_tags = data.get("tags", [])

                if tag_set:
                    entry_tag_lower = set(t.lower() for t in entry_tags)
                    if not (tag_set & entry_tag_lower):
                        continue

                category = "uncategorized"
                if f.parent != TOPICS_DIR:
                    category = f.parent.name

                content_text = data.get("summary", "") or data.get("content", "")
                if not content_text and data.get("results"):
                    content_text = " ".join(
                        str(r) for r in data["results"][:3]
                    ) if isinstance(data["results"], list) else str(data["results"])

                results.append({
                    "source": "topics",
                    "id": data.get("id", f.stem),
                    "title": data.get("title", ""),
                    "content_preview": content_text[:300],
                    "tags": entry_tags,
                    "importance": data.get("score", 5),
                    "relevance": 0.0,
                    "category": category,
                    "file_path": str(f),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return results

    def _scan_knowledge(self, keyword: str, category: str = None) -> list:
        """搜索知识库"""
        results = []
        keyword_lower = keyword.lower()

        search_dirs = (
            [CATEGORY_DIRS[category]] if category and category in CATEGORY_DIRS
            else list(CATEGORY_DIRS.values())
        )

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for f in search_dir.glob("*.json"):
                try:
                    raw = f.read_text(encoding="utf-8")
                    if keyword_lower not in raw.lower():
                        continue

                    data = json.loads(raw)
                    results.append({
                        "source": "knowledge",
                        "id": data.get("id", f.stem),
                        "title": data.get("title", ""),
                        "content_preview": (data.get("content", "") or "")[:300],
                        "tags": data.get("tags", []),
                        "importance": data.get("importance", 5),
                        "relevance": 0.0,
                        "category": search_dir.name,
                        "file_path": str(f),
                    })
                except (json.JSONDecodeError, OSError):
                    continue

        return results

    def _scan_sessions(self, keyword: str) -> list:
        """搜索会话记录"""
        results = []
        keyword_lower = keyword.lower()

        if not SESSIONS_DIR.exists():
            return results

        for f in sorted(SESSIONS_DIR.glob("*.json"),
                        key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                raw = f.read_text(encoding="utf-8")
                if keyword_lower not in raw.lower():
                    continue

                data = json.loads(raw)
                summary = data.get("summary", "") or ""
                lessons = data.get("lessons_learned", [])
                lessons_text = " ".join(str(l) for l in lessons) if lessons else ""

                results.append({
                    "source": "sessions",
                    "id": data.get("session_id", f.stem),
                    "title": f"Session: {summary[:80]}",
                    "content_preview": (summary + " " + lessons_text)[:300],
                    "tags": [],
                    "importance": 5,
                    "relevance": 0.0,
                    "category": "sessions",
                    "file_path": str(f),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return results

    def _scan_patterns(self, keyword: str) -> list:
        """搜索模式库"""
        results = []
        keyword_lower = keyword.lower()

        if not PATTERNS_DIR.exists():
            return results

        for f in PATTERNS_DIR.glob("*.json"):
            try:
                raw = f.read_text(encoding="utf-8")
                if keyword_lower not in raw.lower():
                    continue

                data = json.loads(raw)
                results.append({
                    "source": "patterns",
                    "id": data.get("id", f.stem),
                    "title": data.get("name", ""),
                    "content_preview": (data.get("description", "") or "")[:300],
                    "tags": data.get("tags", []),
                    "importance": min(data.get("use_count", 0), 10),
                    "relevance": 0.0,
                    "category": data.get("domain", "general"),
                    "file_path": str(f),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return results


_engine_instance: Optional[HybridSearchEngine] = None


def get_search_engine() -> HybridSearchEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = HybridSearchEngine()
    return _engine_instance


if __name__ == "__main__":
    engine = get_search_engine()

    print("=== Hybrid Search Engine Test ===\n")

    queries = ["MCP", "Brain", "游戏开发", "error", "IronClaw"]
    for q in queries:
        print(f"\n--- Query: {q} ---")
        results = engine.search(q, limit=5)
        for r in results:
            print(f"  [{r['source']}] {r['title'][:60]} | rel={r['relevance']:.3f} | cat={r['category']}")

    print("\n\n--- Tag Search: ['MCP', '开发'] ---")
    tag_results = engine.search_by_tags(["MCP", "开发"], limit=5)
    for r in tag_results:
        print(f"  [{r['source']}] {r['title'][:60]} | rel={r['relevance']:.3f} | tags={r['tags']}")
