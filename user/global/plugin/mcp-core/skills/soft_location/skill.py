#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件位置管理 Skill
自动搜索并记录所有软件路径，回答用户"XX软件在哪"类问题
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

KB_PATH = Path("/python/MCP_Core/data/knowledge_base.db")

def search_software(name: str) -> Dict:
    """搜索软件位置"""
    results = []
    
    conn = sqlite3.connect(str(KB_PATH))
    
    # 搜索软件清单
    rows = conn.execute("""
        SELECT name, path, category, size_mb 
        FROM software_inventory 
        WHERE name LIKE ? OR path LIKE ?
        ORDER BY size_mb DESC
        LIMIT 10
    """, (f"%{name}%", f"%{name}%")).fetchall()
    
    for r in rows:
        results.append({
            "name": r[0],
            "path": r[1],
            "category": r[2],
            "size_mb": r[3],
        })
    
    # 搜索知识库
    kb_rows = conn.execute("""
        SELECT title, content 
        FROM knowledge 
        WHERE (title LIKE ? OR content LIKE ?) AND category = 'software'
        LIMIT 10
    """, (f"%{name}%", f"%{name}%")).fetchall()
    
    conn.close()
    
    return {
        "query": name,
        "found": len(results),
        "software": results,
        "kb_software": [{"title": r[0], "content": r[1]} for r in kb_rows],
    }

def search_project(name: str) -> Dict:
    """搜索项目目录"""
    conn = sqlite3.connect(str(KB_PATH))
    rows = conn.execute("""
        SELECT name, path, category 
        FROM project_inventory 
        WHERE name LIKE ? OR path LIKE ?
        LIMIT 10
    """, (f"%{name}%", f"%{name}%")).fetchall()
    conn.close()
    
    return {
        "query": name,
        "found": len(rows),
        "projects": [{"name": r[0], "path": r[1], "category": r[2]} for r in rows],
    }

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if not name:
        print("用法: python skill.py <软件名>")
        sys.exit(1)
    
    r = search_software(name)
    print(json.dumps(r, ensure_ascii=False, indent=2))
