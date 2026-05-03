#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持久化知识库系统
解决 TRAE 每会话都忘事的问

功能
- 动录重信（路径决策配、偏好）
- 跨会话持久化
- 义搜（关词匹配）
- 动摘要生
-  SOUL.md / MEMORY.md 联动
"""

import json
import os
import re
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


#  知识库路径配 
KB_PATH = Path("/python/MCP_Core/data/knowledge_base.db")
MEMORY_MD = Path("{USERPROFILE}/.workbuddy/memory/MEMORY.md")
WORKBUDDY_MEM_DIR = Path("{USERPROFILE}/WorkBuddy/20260410084126/.workbuddy/memory")

KB_PATH.parent.mkdir(parents=True, exist_ok=True)
WORKBUDDY_MEM_DIR.mkdir(parents=True, exist_ok=True)


#  知识类型 
class KBCategory:
    PATH = "path"          # 文件/录路
    CONFIG = "config"      # 配置
    DECISION = "decision"  # 决策/选择
    PREFERENCE = "pref"    # 用户偏好
    PROJECT = "project"    # 项目信息
    SKILL = "skill"        # Skill 相关
    ERROR = "error"        # 错和解决方
    GENERAL = "general"    # 通用知识


class KnowledgeBase:
    """持久化知识库"""

    def __init__(self):
        self.db_path = KB_PATH
        self._init_db()
        self._sync_from_memory_md()

    def _init_db(self):
        """初化 SQLite 数据"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    source TEXT DEFAULT 'manual',
                    importance INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_category ON knowledge(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON knowledge(importance DESC)
            """)
            conn.commit()

    def _gen_id(self, title: str, category: str) -> str:
        """生成 ID"""
        raw = f"{category}:{title}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def add(
        self,
        title: str,
        content: str,
        category: str = KBCategory.GENERAL,
        tags: List[str] = None,
        source: str = "manual",
        importance: int = 5,
    ) -> str:
        """添加/更新知识条目"""
        if tags is None:
            tags = []
        
        now = datetime.now().isoformat()
        item_id = self._gen_id(title, category)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            existing = conn.execute(
                "SELECT id FROM knowledge WHERE id = ?", (item_id,)
            ).fetchone()
            
            if existing:
                # 更新
                conn.execute(
                    """UPDATE knowledge SET content=?, tags=?, updated_at=?, importance=?
                       WHERE id=?""",
                    (content, json.dumps(tags, ensure_ascii=False), now, importance, item_id),
                )
            else:
                # 新
                conn.execute(
                    """INSERT INTO knowledge 
                       (id, category, title, content, tags, source, importance, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (item_id, category, title, content,
                     json.dumps(tags, ensure_ascii=False), source, importance, now, now),
                )
            conn.commit()
        
        # 同到 MEMORY.md
        self._sync_important_to_memory_md(title, content, category, importance)
        
        return item_id

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """关键词搜索知识库"""
        keywords = query.lower().split()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT id, category, title, content, tags, importance, updated_at FROM knowledge ORDER BY importance DESC, access_count DESC"
            ).fetchall()
        
        scored = []
        for row in rows:
            item_id, cat, title, content, tags_str, imp, updated = row
            score = 0
            text = f"{title} {content}".lower()
            
            for kw in keywords:
                if kw in text:
                    score += 1
                    if kw in title.lower():
                        score += 2  # 标匹配权重更
            
            if score > 0:
                scored.append({
                    "id": item_id,
                    "category": cat,
                    "title": title,
                    "content": content[:200] + ("..." if len(content) > 200 else ""),
                    "tags": json.loads(tags_str) if tags_str else [],
                    "importance": imp,
                    "updated_at": updated,
                    "score": score,
                })
        
        scored.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)
        
        # 增加访问计数
        if scored:
            with sqlite3.connect(str(self.db_path)) as conn:
                for item in scored[:top_k]:
                    conn.execute(
                        "UPDATE knowledge SET access_count = access_count + 1 WHERE id = ?",
                        (item["id"],)
                    )
                conn.commit()
        
        return scored[:top_k]

    def get_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """按类获取知识"""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT id, title, content, tags, importance, updated_at 
                   FROM knowledge WHERE category=? ORDER BY importance DESC LIMIT ?""",
                (category, limit)
            ).fetchall()
        
        return [
            {
                "id": r[0],
                "title": r[1],
                "content": r[2],
                "tags": json.loads(r[3]) if r[3] else [],
                "importance": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ]

    def get_all_summary(self) -> str:
        """获取知识库摘要（ SOUL.md 注入"""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT category, title, content FROM knowledge 
                   WHERE importance >= 7 ORDER BY importance DESC LIMIT 50"""
            ).fetchall()
        
        if not rows:
            return "知识库暂无高优先级条"
        
        summary_lines = ["## 知识库摘要（高重要条）\n"]
        current_cat = None
        
        for cat, title, content in rows:
            if cat != current_cat:
                summary_lines.append(f"\n### {cat.upper()}")
                current_cat = cat
            short = content[:100].replace("\n", " ")
            summary_lines.append(f"- **{title}**: {short}")
        
        return "\n".join(summary_lines)

    def _sync_from_memory_md(self):
        """ MEMORY.md 同内容到数据库（动时"""
        if not MEMORY_MD.exists():
            return
        
        try:
            content = MEMORY_MD.read_text(encoding="utf-8")
            lines = content.split("\n")
            
            # 单解 MEMORY.md 的条
            current_section = "general"
            buffer_title = None
            buffer_lines = []
            
            for line in lines:
                if line.startswith("## "):
                    if buffer_title and buffer_lines:
                        self.add(
                            title=buffer_title,
                            content="\n".join(buffer_lines).strip(),
                            category=current_section,
                            source="memory_md",
                            importance=6,
                        )
                    current_section = line[3:].strip().lower().replace(" ", "_")
                    buffer_title = None
                    buffer_lines = []
                elif line.startswith("### "):
                    if buffer_title and buffer_lines:
                        self.add(
                            title=buffer_title,
                            content="\n".join(buffer_lines).strip(),
                            category=current_section,
                            source="memory_md",
                            importance=6,
                        )
                    buffer_title = line[4:].strip()
                    buffer_lines = []
                elif line.startswith("- ") or line.startswith("* "):
                    if not buffer_title:
                        buffer_title = line[2:50]
                    buffer_lines.append(line)
                else:
                    buffer_lines.append(line)
            
            # 保存后一
            if buffer_title and buffer_lines:
                self.add(
                    title=buffer_title,
                    content="\n".join(buffer_lines).strip(),
                    category=current_section,
                    source="memory_md",
                    importance=6,
                )
        except Exception as e:
            pass  # 不因为同步失败中

    def _sync_important_to_memory_md(
        self, title: str, content: str, category: str, importance: int
    ):
        """将重要知识同步到 MEMORY.md"""
        if importance < 7:
            return
        
        #  MEMORY.md 父目录存
        MEMORY_MD.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            existing = MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else ""
            
            # 查是否已存在
            if title in existing:
                return
            
            entry = f"\n### {title}\n- {content[:200]}\n- 来源: knowledge_base | 类别: {category}\n"
            
            if "## 动同" not in existing:
                entry = "\n## 动同步（知识库高优先级）\n" + entry
            
            with open(MEMORY_MD, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def auto_extract_and_store(self, text: str, source: str = "conversation") -> List[str]:
        """
        动从文本提取知识并存
        描路径配、决策等模式
        """
        stored_ids = []
        
        # 提取文件
        path_pattern = r'([A-Za-z]:\\[^"\'\s，;；]+|/home/[^"\'\s，;；]+)'
        paths = re.findall(path_pattern, text)
        for p in set(paths):
            if os.path.exists(p):
                title = f": {os.path.basename(p)}"
                item_id = self.add(
                    title=title,
                    content=f"完整: {p}",
                    category=KBCategory.PATH,
                    tags=["auto-extracted", "path"],
                    source=source,
                    importance=6,
                )
                stored_ids.append(item_id)
        
        # 提取 IP 地址（服务器/设）
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        ips = re.findall(ip_pattern, text)
        for ip in set(ips):
            if not ip.startswith("127.") and not ip.startswith("0."):
                item_id = self.add(
                    title=f"IP地址: {ip}",
                    content=f"发现于话，原: {text[:100]}",
                    category=KBCategory.CONFIG,
                    tags=["network", "ip"],
                    source=source,
                    importance=5,
                )
                stored_ids.append(item_id)
        
        # 提取「住」录」等明确指令
        remember_pattern = r'(?:记住|记录|记一下|save|remember)[:]\s*(.{5,100})'
        memories = re.findall(remember_pattern, text, re.IGNORECASE)
        for m in memories:
            item_id = self.add(
                title=f"记录: {m[:30]}",
                content=m,
                category=KBCategory.GENERAL,
                tags=["explicit-memory"],
                source=source,
                importance=8,
            )
            stored_ids.append(item_id)
        
        return stored_ids

    def delete(self, item_id: str) -> bool:
        """删除知识条目"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM knowledge WHERE id = ?", (item_id,))
            conn.commit()
        return True

    def stats(self) -> Dict:
        """获取知识库统"""
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            by_cat = conn.execute(
                "SELECT category, COUNT(*) FROM knowledge GROUP BY category"
            ).fetchall()
        
        return {
            "total": total,
            "by_category": dict(by_cat),
            "db_path": str(self.db_path),
        }


#  全局单例 
_kb_instance: Optional[KnowledgeBase] = None


def get_kb() -> KnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance


#  MCP Tool 接口 
def kb_add(title: str, content: str, category: str = "general", importance: int = 5) -> Dict:
    kb = get_kb()
    item_id = kb.add(title, content, category=category, importance=importance)
    return {"success": True, "id": item_id, "message": f"已录: {title}"}


def kb_search(query: str) -> Dict:
    kb = get_kb()
    results = kb.search(query)
    return {"success": True, "results": results, "count": len(results)}


def kb_stats() -> Dict:
    kb = get_kb()
    return {"success": True, **kb.stats()}


def kb_auto_extract(text: str) -> Dict:
    kb = get_kb()
    ids = kb.auto_extract_and_store(text)
    return {"success": True, "extracted_count": len(ids), "ids": ids}


def kb_summary() -> Dict:
    kb = get_kb()
    summary = kb.get_all_summary()
    return {"success": True, "summary": summary}


#  预置知识（初始化）─
def bootstrap_knowledge():
    """预置用户已知的重要知"""
    kb = get_kb()
    
    presets = [
        ("AI根目", "/python - 主配录，有AI相关文件都在这里", KBCategory.PATH, 9),
        ("MCP Core", "/python\\MCP_Core - MCP能和工作流核", KBCategory.PATH, 9),
        ("WorkBuddy Skills", "%USERPROFILE%\\.workbuddy\\skills - WorkBuddy能目录（数百", KBCategory.PATH, 9),
        ("mcp.json", "%USERPROFILE%\\.workbuddy\\mcp.json - MCP服务器配文件", KBCategory.PATH, 10),
        ("数据库路", "/python\\database.db - AI工作区SQLite数据", KBCategory.PATH, 8),
        ("StepFun API", "地址: http://127.0.0.1:3199/v1, 模型: step-1v, Token: stepfun-model-proxy", KBCategory.CONFIG, 9),
        ("Python", "系统Python: %USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python310\\python.exe", KBCategory.CONFIG, 8),
        ("工作区路", "%USERPROFILE%\\WorkBuddy\\20260410084126 - 当前TRAE工作", KBCategory.PATH, 8),
        ("VS Manager MCP", "已注: vs-manager 指向 /python/MCP/vs_mgr.py", KBCategory.CONFIG, 7),
        ("用户系统", "Windows 10/11 + PowerShell, 用户: 888", KBCategory.CONFIG, 7),
    ]
    
    count = 0
    for title, content, cat, imp in presets:
        kb.add(title, content, category=cat, importance=imp, source="bootstrap")
        count += 1
    
    return count


if __name__ == "__main__":
    print("=== 知识库初始化测试 ===\n")
    
    # 预置知识
    count = bootstrap_knowledge()
    print(f"预置知识条目: {count}")
    
    # 统
    kb = get_kb()
    stats = kb.stats()
    print(f"知识库统: {stats}")
    
    # 搜索测试
    print("\n搜索测试: 'MCP'")
    results = kb.search("MCP")
    for r in results[:3]:
        print(f"  [{r['category']}] {r['title']}: {r['content'][:80]}")
    
    # 动提取测
    print("\n动提取测:")
    text = "记住：我的项 D:\\Projects\\MyApp，服务器IP 192.168.1.100"
    ids = kb.auto_extract_and_store(text)
    print(f"  提取 {len(ids)} 条知")
    
    print("\n知识库摘:")
    print(kb.get_all_summary())
