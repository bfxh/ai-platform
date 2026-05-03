#!/usr/bin/env python
"""Bug Memory Engine — 错误学习与防复发系统

核心使命:
  任何 AI 犯过的错，永久记录，下次遇到同类任务自动警告，杜绝重犯。

功能:
  1. record_bug()      — 记录 bug（上下文 + 错误 + 修复方案）
  2. search_similar()   — 搜索历史上类似 bug
  3. recall_for_task()  — 任务前自动召回相关 bug 教训
  4. check_recurrence() — 检查当前操作是否会触发已知 bug
  5. get_antipatterns() — 提取"永远不要这样做"的反模式

数据存储:
  storage/Brain/memory/bugs/  — JSON 文件，按日期组织
  storage/Brain/memory/antipatterns.json — 提炼的反模式
"""

import json
import hashlib
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict


class BugMemoryEngine:
    """Bug 记忆引擎 — 让 AI 从错误中学习。"""

    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "bugs"
        self._bugs_dir = Path(data_dir)
        self._bugs_dir.mkdir(parents=True, exist_ok=True)
        self._antipatterns_file = self._bugs_dir.parent / "antipatterns.json"
        self._lock = threading.Lock()
        self._index = self._build_index()
        self._dup_cache = {}  # md5_hash -> bug_dict 缓存，避免 O(n²) 遍历

    # ─── 索引 ──────────────────────────────────────────

    def _build_index(self) -> dict:
        """构建 bug 关键词索引，加速搜索。"""
        index = defaultdict(list)
        for bug_file in self._bugs_dir.glob("bug_*.json"):
            try:
                bug = json.loads(bug_file.read_text(encoding="utf-8"))
                bug_id = bug.get("bug_id", bug_file.stem)
                keywords = self._extract_keywords(bug)
                for kw in keywords:
                    index[kw].append(bug_id)
            except (json.JSONDecodeError, OSError):
                continue
        return dict(index)

    def _extract_keywords(self, bug: dict) -> list:
        """从 bug 记录中提取关键词。"""
        text = " ".join([
            bug.get("task_description", ""),
            bug.get("error_message", ""),
            bug.get("error_type", ""),
            " ".join(bug.get("files_involved", [])),
            " ".join(bug.get("tags", [])),
        ]).lower()

        # 提取有意义的词（长度 > 2）
        words = set()
        for word in text.replace(".", " ").replace("/", " ").replace("\\", " ").split():
            word = word.strip("()[]{},:;\"'")
            if len(word) > 2:
                words.add(word)

        # 添加文件名中的关键词
        for f in bug.get("files_involved", []):
            name = Path(f).stem.lower()
            for part in name.replace("_", " ").replace("-", " ").split():
                if len(part) > 1:
                    words.add(part)

        return list(words)

    # ─── 记录 ──────────────────────────────────────────

    def record_bug(self, error_message: str, task_description: str = "",
                   error_type: str = "unknown", fix_description: str = "",
                   files_involved: list = None, agent_id: str = "unknown",
                   severity: str = "medium", tags: list = None) -> str:
        """记录一个 bug。

        Args:
            error_message: 错误信息
            task_description: 当时在做什么任务
            error_type: 错误类型 (import, syntax, config, logic, permission, network, etc.)
            fix_description: 如何修复的
            files_involved: 涉及的文件
            agent_id: 哪个 AI 犯的
            severity: 严重程度 (low, medium, high, critical)
            tags: 标签

        Returns:
            bug_id
        """
        now = datetime.now()
        bug_id = f"bug_{now.strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(error_message.encode()).hexdigest()[:8]}"

        bug = {
            "bug_id": bug_id,
            "timestamp": now.isoformat(),
            "agent_id": agent_id,
            "task_description": task_description[:500],
            "error_message": error_message[:1000],
            "error_type": error_type,
            "fix_description": fix_description[:1000],
            "files_involved": files_involved or [],
            "severity": severity,
            "tags": tags or [],
            "recurrence_count": 0,
            "last_seen": now.isoformat(),
        }

        # 检查是否是已知 bug 的复发
        existing = self._find_duplicate(error_message, error_type)
        if existing:
            bug["recurrence_count"] = existing.get("recurrence_count", 0) + 1
            bug["first_seen"] = existing.get("timestamp", bug["timestamp"])
            bug["bug_id"] = existing["bug_id"]  # 复用原有 ID
            # 更新原文件
            bug_file = self._bugs_dir / f"{existing['bug_id']}.json"
        else:
            bug["first_seen"] = bug["timestamp"]
            bug_file = self._bugs_dir / f"{bug_id}.json"

        with self._lock:
            bug_file.write_text(json.dumps(bug, ensure_ascii=False, indent=2), encoding="utf-8")
            # 更新索引
            keywords = self._extract_keywords(bug)
            for kw in keywords:
                if kw not in self._index:
                    self._index[kw] = []
                if bug["bug_id"] not in self._index[kw]:
                    self._index[kw].append(bug["bug_id"])

            # 如果复发次数 >= 3，提取为反模式
            if bug["recurrence_count"] >= 3:
                self._extract_antipattern(bug)

        return bug["bug_id"]

    def _find_duplicate(self, error_message: str, error_type: str) -> Optional[dict]:
        """查找是否有高度相似的已有 bug。使用缓存避免每次遍历所有文件。"""
        key = hashlib.md5(f"{error_type}:{error_message[:200]}".encode()).hexdigest()[:12]
        
        # 先查缓存
        if key in self._dup_cache:
            return self._dup_cache[key]
        
        # 缓存未命中才遍历文件（同时构建缓存）
        for bug_file in self._bugs_dir.glob("bug_*.json"):
            try:
                bug = json.loads(bug_file.read_text(encoding="utf-8"))
                existing_key = hashlib.md5(
                    f"{bug.get('error_type', '')}:{bug.get('error_message', '')[:200]}".encode()
                ).hexdigest()[:12]
                self._dup_cache[existing_key] = bug  # 构建缓存
                if existing_key == key:
                    return bug
            except (json.JSONDecodeError, OSError):
                continue
        return None

    # ─── 搜索与召回 ────────────────────────────────────

    def search_similar(self, query: str, limit: int = 10) -> list:
        """搜索与 query 相关的历史 bug。

        Args:
            query: 搜索词（任务描述、错误信息等）
            limit: 返回数量上限

        Returns:
            相关 bug 列表，按相关性排序
        """
        query_words = set()
        for word in query.lower().replace(".", " ").replace("/", " ").split():
            word = word.strip("()[]{},:;\"'")
            if len(word) > 2:
                query_words.add(word)

        # 通过索引查找候选
        scores = defaultdict(int)
        for word in query_words:
            for bug_id in self._index.get(word, []):
                scores[bug_id] += 1

        # 排序并取 top N
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        # 加载完整 bug 记录
        results = []
        for bug_id, score in ranked:
            bug_file = self._bugs_dir / f"{bug_id}.json"
            if bug_file.exists():
                try:
                    bug = json.loads(bug_file.read_text(encoding="utf-8"))
                    bug["relevance_score"] = score
                    results.append(bug)
                except (json.JSONDecodeError, OSError):
                    continue

        return results

    def recall_for_task(self, task_description: str, files_involved: list = None) -> dict:
        """任务执行前召回相关历史教训。

        这是最重要的方法 — 在每个任务前调用，
        自动注入相关 bug 经验，防止重蹈覆辙。

        Returns:
            {
                "relevant_bugs": [...],       # 相关 bug 列表
                "antipatterns": [...],        # 相关反模式
                "warnings": [...],            # 针对当前任务的警告
                "summary": "简明教训总结"
            }
        """
        # 搜索相关 bug
        query_parts = [task_description]
        if files_involved:
            query_parts.extend(files_involved)
        query = " ".join(query_parts)

        relevant_bugs = self.search_similar(query, limit=10)

        # 加载反模式
        antipatterns = self.get_antipatterns()

        # 匹配反模式
        relevant_antipatterns = []
        for ap in antipatterns:
            ap_text = ap.get("pattern", "") + " " + " ".join(ap.get("tags", []))
            if any(word in ap_text.lower() for word in query.lower().split() if len(word) > 3):
                relevant_antipatterns.append(ap)

        # 生成警告
        warnings = []
        for bug in relevant_bugs[:5]:
            if bug.get("severity") in ("high", "critical"):
                warnings.append(
                    f"[!] [{bug['error_type']}] {bug['error_message'][:150]}. "
                    f"修复: {bug.get('fix_description', '未知')[:100]}"
                )
            if bug.get("recurrence_count", 0) >= 2:
                warnings.append(
                    f"[!!] 重复犯过的错（{bug['recurrence_count']}次）: "
                    f"{bug['error_message'][:150]}"
                )

        # 生成摘要
        summary_parts = []
        if relevant_bugs:
            bug_types = set(b.get("error_type", "unknown") for b in relevant_bugs)
            summary_parts.append(f"发现 {len(relevant_bugs)} 个相关历史 bug（类型: {', '.join(bug_types)}）")
        if relevant_antipatterns:
            summary_parts.append(f"匹配 {len(relevant_antipatterns)} 个反模式")
        if warnings:
            summary_parts.append(f"{len(warnings)} 个高危警告")
        if not summary_parts:
            summary_parts.append("未发现相关历史 bug，但请保持警惕")

        return {
            "relevant_bugs": relevant_bugs,
            "antipatterns": relevant_antipatterns,
            "warnings": warnings,
            "summary": "。".join(summary_parts),
        }

    def check_recurrence(self, error_message: str) -> Optional[dict]:
        """检查某个错误是否以前犯过。

        Returns:
            如果犯过，返回历史 bug 记录；否则返回 None
        """
        existing = self._find_duplicate(error_message, "any")
        if existing and existing.get("recurrence_count", 0) > 0:
            return {
                "previous_occurrences": existing["recurrence_count"],
                "first_seen": existing.get("first_seen", ""),
                "last_seen": existing.get("last_seen", ""),
                "fix": existing.get("fix_description", ""),
                "bug_id": existing["bug_id"],
            }
        return None

    # ─── 反模式 ────────────────────────────────────────

    def _extract_antipattern(self, bug: dict):
        """从复发 >= 3 次的 bug 中提取反模式。"""
        antipatterns = self.get_antipatterns()

        ap = {
            "id": f"ap_{bug['bug_id']}",
            "pattern": bug["error_message"][:300],
            "description": f"复发 {bug['recurrence_count']} 次的错误: {bug['error_message'][:200]}",
            "fix": bug.get("fix_description", "")[:300],
            "error_type": bug.get("error_type", "unknown"),
            "severity": bug.get("severity", "medium"),
            "first_seen": bug.get("first_seen", ""),
            "last_seen": bug.get("last_seen", ""),
            "recurrence_count": bug["recurrence_count"],
            "tags": bug.get("tags", []),
        }

        # 去重
        existing_ids = {a.get("id", "") for a in antipatterns}
        if ap["id"] not in existing_ids:
            antipatterns.append(ap)
            self._antipatterns_file.write_text(
                json.dumps(antipatterns, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def get_antipatterns(self) -> list:
        """获取所有反模式。"""
        if not self._antipatterns_file.exists():
            return []
        try:
            return json.loads(self._antipatterns_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    # ─── 统计 ──────────────────────────────────────────

    def stats(self) -> dict:
        """获取 bug 记忆统计。"""
        bugs = list(self._bugs_dir.glob("bug_*.json"))
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        total_recurrences = 0

        for bf in bugs:
            try:
                bug = json.loads(bf.read_text(encoding="utf-8"))
                by_type[bug.get("error_type", "unknown")] += 1
                by_severity[bug.get("severity", "medium")] += 1
                total_recurrences += bug.get("recurrence_count", 0)
            except (json.JSONDecodeError, OSError):
                continue

        return {
            "total_bugs": len(bugs),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "total_recurrences": total_recurrences,
            "antipatterns": len(self.get_antipatterns()),
        }


# ─── 全局单例 ───────────────────────────────────────────
_bug_memory_instance: Optional[BugMemoryEngine] = None
_instance_lock = threading.Lock()


def get_bug_memory() -> BugMemoryEngine:
    """获取 Bug 记忆引擎单例。"""
    global _bug_memory_instance
    if _bug_memory_instance is None:
        with _instance_lock:
            if _bug_memory_instance is None:
                _bug_memory_instance = BugMemoryEngine()
    return _bug_memory_instance


# ─── CLI 测试 ──────────────────────────────────────────
if __name__ == "__main__":
    bm = get_bug_memory()

    # 模拟记录 bug
    bug_id1 = bm.record_bug(
        error_message="ModuleNotFoundError: No module named 'filelock'",
        task_description="初始化共享上下文系统",
        error_type="import",
        fix_description="pip install filelock",
        files_involved=["core/shared_context.py"],
        agent_id="Qoder",
        tags=["import", "dependency", "shared_context"],
    )
    print(f"Recorded: {bug_id1}")

    # 模拟搜索
    results = bm.search_similar("filelock import error shared context")
    print(f"\nSearch results: {len(results)}")
    for r in results:
        print(f"  [{r['error_type']}] {r['error_message'][:80]} (recurrence: {r['recurrence_count']})")

    # 模拟任务前召回
    recall = bm.recall_for_task("初始化 shared context", files_involved=["core/shared_context.py"])
    print(f"\nRecall summary: {recall['summary']}")
    for w in recall["warnings"]:
        print(f"  {w}")

    print(f"\nStats: {json.dumps(bm.stats(), ensure_ascii=False, indent=2)}")
