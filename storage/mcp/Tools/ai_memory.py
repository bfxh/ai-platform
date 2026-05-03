#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 记忆系统 - 记录和分类用户需求

功能：
- 记录用户的所有要求和偏好
- 自动分类和标签
- 基因记忆（核心偏好）
- 上下文记忆（会话历史）
- 项目记忆（项目特定要求）
- 技能记忆（技能使用偏好）
- 工作流记忆（工作流偏好）
- 支持搜索和检索
- 自动同步到 GitHub

用法：
    python ai_memory.py add <category> <content> [tags]     # 添加记忆
    python ai_memory.py get <category> [query]              # 获取记忆
    python ai_memory.py search <query>                      # 搜索记忆
    python ai_memory.py list [category]                     # 列出记忆
    python ai_memory.py update <id> <content>               # 更新记忆
    python ai_memory.py delete <id>                         # 删除记忆
    python ai_memory.py sync                                # 同步到 GitHub
    python ai_memory.py genes                               # 显示基因记忆
    python ai_memory.py context                             # 显示上下文

MCP调用：
    {"tool": "ai_memory", "action": "add", "params": {...}}
"""

import json
import sys
import os
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"
MEMORY_PATH = AI_PATH / "Memory"
MEMORY_PATH.mkdir(parents=True, exist_ok=True)

# 记忆数据库
MEMORY_DB = MEMORY_PATH / "ai_memory.db"

# 记忆分类
MEMORY_CATEGORIES = {
    "genes": "基因记忆 - 核心偏好和原则",
    "context": "上下文记忆 - 会话历史",
    "projects": "项目记忆 - 项目特定要求",
    "skills": "技能记忆 - 技能使用偏好",
    "workflows": "工作流记忆 - 工作流偏好",
    "tools": "工具记忆 - 工具配置偏好",
    "coding": "编码记忆 - 代码风格偏好",
    "ui": "UI记忆 - 界面偏好",
    "game_dev": "游戏开发记忆 - 游戏开发偏好",
    "github": "GitHub记忆 - GitHub相关偏好",
    "mcp": "MCP记忆 - MCP配置偏好",
    "general": "一般记忆 - 其他要求",
}

# 优先级
PRIORITIES = {
    "critical": 5,  # 关键 - 必须遵守
    "high": 4,      # 高 - 重要
    "medium": 3,    # 中 - 一般
    "low": 2,       # 低 - 可选
    "optional": 1,  # 可选 - 参考
}

# ============================================================
# 记忆项
# ============================================================
@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    category: str
    content: str
    tags: List[str]
    priority: str
    created_at: str
    updated_at: str
    access_count: int
    last_accessed: Optional[str]
    context: Optional[str]
    related_ids: List[str]

# ============================================================
# AI 记忆系统
# ============================================================
class AIMemory:
    """AI 记忆系统"""
    
    def __init__(self):
        self.db = self._init_db()
        self._load_genes()
    
    def _init_db(self) -> sqlite3.Connection:
        """初始化数据库"""
        MEMORY_PATH.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(MEMORY_DB))
        
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT,
                content TEXT,
                tags TEXT,
                priority TEXT,
                created_at TEXT,
                updated_at TEXT,
                access_count INTEGER,
                last_accessed TEXT,
                context TEXT,
                related_ids TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
        ''')
        
        conn.commit()
        return conn
    
    def _load_genes(self):
        """加载基因记忆"""
        # 核心基因记忆 - 用户的基础偏好
        self.genes = {
            "language": "中文",
            "code_style": "简洁、注释清晰",
            "file_encoding": "UTF-8",
            "path_style": "绝对路径",
            "backup_policy": "自动备份重要文件",
            "mcp_mode": "懒加载、内存优化",
            "github_sync": "自动同步",
            "game_engine": "Godot优先",
            "ai_service": "阶跃AI优先",
        }
    
    def _generate_id(self, content: str) -> str:
        """生成记忆 ID"""
        hash_obj = hashlib.md5(content.encode())
        return hash_obj.hexdigest()[:12]
    
    def add_memory(self, category: str, content: str, 
                   tags: List[str] = None, priority: str = "medium",
                   context: str = None, related_ids: List[str] = None) -> Dict:
        """添加记忆"""
        try:
            if category not in MEMORY_CATEGORIES:
                return {"success": False, "error": f"未知分类: {category}"}
            
            memory_id = self._generate_id(content)
            now = datetime.now().isoformat()
            
            cursor = self.db.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO memories 
                (id, category, content, tags, priority, created_at, updated_at, 
                 access_count, last_accessed, context, related_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_id,
                category,
                content,
                json.dumps(tags or [], ensure_ascii=False),
                priority,
                now,
                now,
                0,
                None,
                context,
                json.dumps(related_ids or [], ensure_ascii=False)
            ))
            
            self.db.commit()
            
            return {
                "success": True,
                "id": memory_id,
                "category": category,
                "message": f"记忆已添加到 [{MEMORY_CATEGORIES[category]}]"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memory(self, category: str = None, query: str = None, 
                   limit: int = 10) -> Dict:
        """获取记忆"""
        try:
            cursor = self.db.cursor()
            
            if category and query:
                cursor.execute('''
                    SELECT * FROM memories 
                    WHERE category = ? AND content LIKE ?
                    ORDER BY access_count DESC, updated_at DESC
                    LIMIT ?
                ''', (category, f'%{query}%', limit))
            elif category:
                cursor.execute('''
                    SELECT * FROM memories 
                    WHERE category = ?
                    ORDER BY access_count DESC, updated_at DESC
                    LIMIT ?
                ''', (category, limit))
            elif query:
                cursor.execute('''
                    SELECT * FROM memories 
                    WHERE content LIKE ?
                    ORDER BY access_count DESC, updated_at DESC
                    LIMIT ?
                ''', (f'%{query}%', limit))
            else:
                cursor.execute('''
                    SELECT * FROM memories 
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memories.append({
                    "id": row[0],
                    "category": row[1],
                    "content": row[2],
                    "tags": json.loads(row[3]),
                    "priority": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "access_count": row[7],
                })
                
                # 更新访问计数
                cursor.execute('''
                    UPDATE memories 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), row[0]))
            
            self.db.commit()
            
            return {
                "success": True,
                "count": len(memories),
                "memories": memories
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_memory(self, query: str, categories: List[str] = None) -> Dict:
        """搜索记忆"""
        try:
            cursor = self.db.cursor()
            
            if categories:
                placeholders = ','.join(['?' for _ in categories])
                sql = f'''
                    SELECT * FROM memories 
                    WHERE category IN ({placeholders}) AND (content LIKE ? OR tags LIKE ?)
                    ORDER BY priority DESC, access_count DESC
                '''
                cursor.execute(sql, (*categories, f'%{query}%', f'%{query}%'))
            else:
                cursor.execute('''
                    SELECT * FROM memories 
                    WHERE content LIKE ? OR tags LIKE ?
                    ORDER BY priority DESC, access_count DESC
                ''', (f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memories.append({
                    "id": row[0],
                    "category": row[1],
                    "content": row[2],
                    "tags": json.loads(row[3]),
                    "priority": row[4],
                    "updated_at": row[6],
                })
            
            return {
                "success": True,
                "query": query,
                "count": len(memories),
                "memories": memories
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_categories(self) -> Dict:
        """列出所有分类"""
        return {
            "success": True,
            "categories": [
                {"id": k, "name": v}
                for k, v in MEMORY_CATEGORIES.items()
            ]
        }
    
    def get_genes(self) -> Dict:
        """获取基因记忆"""
        return {
            "success": True,
            "genes": self.genes,
            "description": "基因记忆是用户的核心偏好，必须始终遵守"
        }
    
    def update_gene(self, key: str, value: str) -> Dict:
        """更新基因记忆"""
        self.genes[key] = value
        
        # 同时保存到数据库
        return self.add_memory(
            category="genes",
            content=f"{key}: {value}",
            tags=["gene", key],
            priority="critical"
        )
    
    def get_context(self, session_id: str = None) -> Dict:
        """获取上下文记忆"""
        # 获取最近的上下文记忆
        result = self.get_memory(category="context", limit=20)
        
        return {
            "success": True,
            "session_id": session_id,
            "recent_context": result.get("memories", []),
            "genes": self.genes
        }
    
    def add_context(self, content: str, session_id: str = None) -> Dict:
        """添加上下文记忆"""
        return self.add_memory(
            category="context",
            content=content,
            tags=["context", session_id] if session_id else ["context"],
            priority="medium",
            context=session_id
        )
    
    def update_memory(self, memory_id: str, content: str) -> Dict:
        """更新记忆"""
        try:
            cursor = self.db.cursor()
            cursor.execute('''
                UPDATE memories 
                SET content = ?, updated_at = ?
                WHERE id = ?
            ''', (content, datetime.now().isoformat(), memory_id))
            
            self.db.commit()
            
            return {
                "success": True,
                "id": memory_id,
                "message": "记忆已更新"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_memory(self, memory_id: str) -> Dict:
        """删除记忆"""
        try:
            cursor = self.db.cursor()
            cursor.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
            self.db.commit()
            
            return {
                "success": True,
                "id": memory_id,
                "message": "记忆已删除"
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def export_to_json(self, category: str = None) -> Dict:
        """导出记忆到 JSON"""
        try:
            result = self.get_memory(category=category, limit=1000)
            
            if not result.get("success"):
                return result
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "genes": self.genes,
                "memories": result["memories"]
            }
            
            export_file = MEMORY_PATH / f"memory_export_{datetime.now().strftime('%Y%m%d')}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "file": str(export_file),
                "count": len(result["memories"])
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_to_github(self) -> Dict:
        """同步到 GitHub"""
        try:
            # 导出记忆
            export_result = self.export_to_json()
            if not export_result.get("success"):
                return export_result
            
            # 使用 github_auto_commit 提交
            import subprocess
            result = subprocess.run(
                ["python", str(MCP_PATH / "github_auto_commit.py"), "auto", str(MEMORY_PATH)],
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "message": "记忆已同步到 GitHub",
                "export_file": export_result["file"]
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_relevant_memories(self, context: str, limit: int = 5) -> Dict:
        """获取相关记忆（基于上下文）"""
        # 提取关键词
        keywords = self._extract_keywords(context)
        
        all_memories = []
        for keyword in keywords:
            result = self.search_memory(keyword)
            if result.get("success"):
                all_memories.extend(result["memories"])
        
        # 去重并排序
        seen = set()
        unique_memories = []
        for m in all_memories:
            if m["id"] not in seen:
                seen.add(m["id"])
                unique_memories.append(m)
        
        # 按优先级排序
        unique_memories.sort(key=lambda x: PRIORITIES.get(x["priority"], 0), reverse=True)
        
        return {
            "success": True,
            "keywords": keywords,
            "memories": unique_memories[:limit]
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []
        
        # 游戏开发相关
        if any(word in text for word in ["游戏", "godot", "unity", "ue5"]):
            keywords.extend(["game_dev", "godot", "unity"])
        
        # MCP 相关
        if any(word in text for word in ["mcp", "技能", "工具"]):
            keywords.extend(["mcp", "skills", "tools"])
        
        # GitHub 相关
        if any(word in text for word in ["github", "git", "提交"]):
            keywords.extend(["github", "git"])
        
        # 代码相关
        if any(word in text for word in ["代码", "编程", "python"]):
            keywords.extend(["coding", "python"])
        
        # 工作流相关
        if any(word in text for word in ["工作流", "workflow", "自动化"]):
            keywords.extend(["workflows", "automation"])
        
        return keywords if keywords else ["general"]

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.memory = AIMemory()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "add":
            return self.memory.add_memory(
                category=params.get("category"),
                content=params.get("content"),
                tags=params.get("tags"),
                priority=params.get("priority", "medium"),
                context=params.get("context"),
                related_ids=params.get("related_ids")
            )
        
        elif action == "get":
            return self.memory.get_memory(
                category=params.get("category"),
                query=params.get("query"),
                limit=params.get("limit", 10)
            )
        
        elif action == "search":
            return self.memory.search_memory(
                query=params.get("query"),
                categories=params.get("categories")
            )
        
        elif action == "list_categories":
            return self.memory.list_categories()
        
        elif action == "genes":
            return self.memory.get_genes()
        
        elif action == "update_gene":
            return self.memory.update_gene(
                key=params.get("key"),
                value=params.get("value")
            )
        
        elif action == "context":
            return self.memory.get_context(
                session_id=params.get("session_id")
            )
        
        elif action == "add_context":
            return self.memory.add_context(
                content=params.get("content"),
                session_id=params.get("session_id")
            )
        
        elif action == "update":
            return self.memory.update_memory(
                memory_id=params.get("id"),
                content=params.get("content")
            )
        
        elif action == "delete":
            return self.memory.delete_memory(
                memory_id=params.get("id")
            )
        
        elif action == "export":
            return self.memory.export_to_json(
                category=params.get("category")
            )
        
        elif action == "sync":
            return self.memory.sync_to_github()
        
        elif action == "relevant":
            return self.memory.get_relevant_memories(
                context=params.get("context"),
                limit=params.get("limit", 5)
            )
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    memory = AIMemory()
    
    if cmd == "add":
        if len(sys.argv) < 4:
            print("用法: ai_memory.py add <category> <content> [tags]")
            print("分类:", ", ".join(MEMORY_CATEGORIES.keys()))
            return
        
        category = sys.argv[2]
        content = sys.argv[3]
        tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        
        result = memory.add_memory(category, content, tags)
        
        if result.get("success"):
            print(f"✓ {result['message']}")
            print(f"  ID: {result['id']}")
        else:
            print(f"✗ {result.get('error')}")
    
    elif cmd == "get":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        query = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = memory.get_memory(category, query)
        
        if result.get("success"):
            print(f"找到 {result['count']} 条记忆:")
            for m in result["memories"]:
                print(f"\n[{m['category']}] {m['id']}")
                print(f"  {m['content'][:100]}...")
                print(f"  优先级: {m['priority']}, 访问: {m['access_count']}")
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("用法: ai_memory.py search <query>")
            return
        
        query = sys.argv[2]
        result = memory.search_memory(query)
        
        if result.get("success"):
            print(f"搜索 '{query}' 找到 {result['count']} 条记忆:")
            for m in result["memories"]:
                print(f"\n[{m['category']}] {m['content'][:80]}...")
    
    elif cmd == "list":
        result = memory.list_categories()
        
        if result.get("success"):
            print("记忆分类:")
            for cat in result["categories"]:
                print(f"  {cat['id']:<15} - {cat['name']}")
    
    elif cmd == "genes":
        result = memory.get_genes()
        
        if result.get("success"):
            print("基因记忆（核心偏好）:")
            print("=" * 60)
            for key, value in result["genes"].items():
                print(f"  {key}: {value}")
    
    elif cmd == "context":
        result = memory.get_context()
        
        if result.get("success"):
            print("当前上下文:")
            print("=" * 60)
            print("基因:", result["genes"])
            print("\n近期记忆:")
            for m in result["recent_context"]:
                print(f"  - {m['content'][:60]}...")
    
    elif cmd == "sync":
        print("同步到 GitHub...")
        result = memory.sync_to_github()
        
        if result.get("success"):
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("AI 记忆系统 MCP 已启动")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
