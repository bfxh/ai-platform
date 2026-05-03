#!/usr/bin/env python
"""Brain Memory Recaller - 记忆召回系统

实现:
- 触发式召回 (识别何时需要调取记忆)
- 关键词搜索 (session + knowledge)
- 语义相似度搜索 (基于tags和内容匹配)
- 上下文注入 (将相关记忆组装为prompt可用的上下文)
- 相关性排序
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# 延迟导入避免循环依赖
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from .engine import get_memory_engine
        _engine = get_memory_engine()
    return _engine


class MemoryRecaller:
    """记忆召回器 - 根据上下文自动调取相关记忆"""

    def __init__(self):
        self.engine = _get_engine()
        self._recall_config = self._load_recall_config()

    def _load_recall_config(self) -> dict:
        return self.engine.config.get("recall_strategy", {})

    # ─── 触发检测 ──────────────────────────────────────

    def should_recall(self, message: str) -> list:
        """检测消息是否触发记忆召回，返回触发的触发器列表"""
        triggered = []
        triggers = self._recall_config.get("triggers", [])

        # 检测回溯类关键词
        backtrack_keywords = [
            "上次", "之前", "以前", "像上次一样", "跟之前一样",
            "上次那个", "之前那个", "再", "继续", "接着",
            "像之前那样", "和上次一样", "还记得", "想起来",
        ]
        for kw in backtrack_keywords:
            if kw in message:
                triggered.append("session_backtrack")
                break

        # 检测错误解决请求
        error_keywords = ["报错", "出错", "error", "错误", "异常",
                          "bug", "坏了", "不行", "失败"]
        for kw in error_keywords:
            if kw in message:
                triggered.append("error_solutions")
                break

        # 检测新任务开始
        task_keywords = ["帮我", "写一个", "创建一个", "做一个",
                         "实现", "开发", "配置", "设置", "安装",
                         "开始", "新建", "建立"]
        for kw in task_keywords:
            if kw in message:
                triggered.append("task_context")
                break

        # 始终加载用户偏好
        triggered.append("user_profile")

        return triggered

    # ─── 召回主函数 ────────────────────────────────────

    def recall(self, message: str, max_results: int = 10) -> dict:
        """主召回函数 - 返回结构化的记忆上下文

        Returns:
            {
                "triggered_by": [...],
                "sessions": [...],
                "knowledge": [...],
                "patterns": [...],
                "user_profile": {...},
                "summary": "简要的上下文摘要"
            }
        """
        triggers = self.should_recall(message)
        result = {
            "triggered_by": triggers,
            "sessions": [],
            "knowledge": [],
            "patterns": [],
            "user_profile": {},
            "summary": "",
            "timestamp": datetime.now().isoformat(),
        }

        # 提取关键词用于搜索
        keywords = self._extract_keywords(message)

        # 会话回溯
        if "session_backtrack" in triggers:
            for kw in keywords[:3]:
                sessions = self.engine.search_sessions(kw, limit=5)
                for s in sessions:
                    if s not in result["sessions"]:
                        result["sessions"].append(s)

        # 错误方案
        if "error_solutions" in triggers:
            for kw in keywords[:3]:
                entries = self.engine.kb_search(kw, category="error_solutions", limit=5)
                for e in entries:
                    if e not in result["knowledge"]:
                        result["knowledge"].append(e)

        # 通用知识搜索
        if "task_context" in triggers:
            for kw in keywords[:2]:
                entries = self.engine.kb_search(kw, limit=5)
                for e in entries:
                    if e not in result["knowledge"]:
                        result["knowledge"].append(e)

        # 模式搜索
        for kw in keywords[:2]:
            patterns = self.engine.search_patterns(kw, limit=3)
            for p in patterns:
                if p not in result["patterns"]:
                    result["patterns"].append(p)

        # 用户画像
        if self.engine.user_profile:
            result["user_profile"] = {
                "preferences": self.engine.user_profile.get("preferences", {}),
                "project_context": self.engine.user_profile.get("project_context", {}),
            }

        # 生成简要摘要
        result["summary"] = self._generate_summary(result)
        self.engine._stats["recalls"] += 1
        return result

    # ─── 上下文格式化 ──────────────────────────────────

    def format_context(self, recall_result: dict) -> str:
        """将召回结果格式化为可注入prompt的上下文字符串"""
        parts = []

        if recall_result.get("user_profile"):
            profile = recall_result["user_profile"]
            parts.append("## 用户偏好与上下文")
            for k, v in profile.get("preferences", {}).items():
                if isinstance(v, list):
                    parts.append(f"- {k}: {', '.join(str(x) for x in v)}")
                elif v:
                    parts.append(f"- {k}: {v}")

        if recall_result.get("sessions"):
            parts.append("\n## 相关历史会话")
            for s in recall_result["sessions"][:5]:
                parts.append(f"- [{s.get('session_id','')}] {s.get('summary','')[:150]}")

        if recall_result.get("knowledge"):
            parts.append("\n## 相关知识")
            for e in recall_result["knowledge"][:8]:
                parts.append(f"- [{e.get('category','')}] {e.get('title','')}: {e.get('content','')[:200]}")

        if recall_result.get("patterns"):
            parts.append("\n## 可用模式")
            for p in recall_result["patterns"][:3]:
                parts.append(f"- {p.get('name','')}: {p.get('description','')}")

        return "\n".join(parts)

    # ─── 关键词提取 ────────────────────────────────────

    def _extract_keywords(self, text: str) -> list:
        """从文本中提取关键词"""
        # 提取中文关键词 (2-4个字的词组)
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)

        # 提取英文关键词
        english_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_.]{2,}', text)

        # 停用词过滤
        stopwords = {
            "帮我", "一个", "这个", "那个", "一下", "怎么", "什么",
            "有没有", "能不能", "可以不", "是不是", "的话", "可以",
            "然后", "就是", "还是", "或者", "以及", "并且",
            "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
            "to", "for", "of", "with", "this", "that", "it", "and", "or",
        }

        keywords = [w for w in chinese_words if w not in stopwords]
        keywords += [w.lower() for w in english_words if w.lower() not in stopwords]

        # 去重并限制数量
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        return unique[:10]

    def _generate_summary(self, result: dict) -> str:
        """生成召回结果摘要"""
        parts = []
        if result["sessions"]:
            parts.append(f"找到{len(result['sessions'])}个相关会话")
        if result["knowledge"]:
            parts.append(f"找到{len(result['knowledge'])}条相关知识")
        if result["patterns"]:
            parts.append(f"找到{len(result['patterns'])}个可用模式")
        return "; ".join(parts) if parts else "无相关记忆"


# ─── 便捷函数 ──────────────────────────────────────────
_recaller_instance: Optional[MemoryRecaller] = None


def get_recaller() -> MemoryRecaller:
    global _recaller_instance
    if _recaller_instance is None:
        _recaller_instance = MemoryRecaller()
    return _recaller_instance


def quick_recall(message: str) -> str:
    """快速召回并返回格式化的上下文字符串"""
    r = get_recaller()
    result = r.recall(message)
    return r.format_context(result)


# ─── CLI 测试 ───────────────────────────────────────────
if __name__ == "__main__":
    test_messages = [
        "帮我像上次一样配置MCP服务",
        "GSTACK编译报错了怎么修",
        "帮我写一个Python脚本来分析数据",
        "启动时出现timeout错误",
    ]
    recaller = get_recaller()
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"Query: {msg}")
        result = recaller.recall(msg)
        print(f"Triggers: {result['triggered_by']}")
        print(f"Summary: {result['summary']}")
        print(f"\nFormatted Context:")
        print(recaller.format_context(result)[:500])
