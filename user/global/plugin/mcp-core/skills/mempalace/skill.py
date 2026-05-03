#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - MemPalace AI记忆系统技能

功能:
- AI记忆宫殿管理
- 长期记忆存储和检索
- AAAK压缩格式支持
- 时间有效性知识图谱
- 冲突检测
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

import sys
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("警告: chromadb未安装，部分功能将不可用")

# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill, handle_errors


class MemPalaceSkill(Skill):
    """MemPalace AI记忆系统技能"""

    name = "mempalace"
    description = "AI记忆宫殿系统 - 基于古希腊记忆术的长期记忆管理"
    version = "1.0.0"
    author = "Milla Jovovich & Ben Sigman"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.db_path = self.config.get("db_path", "mempalace.db")
        self.chroma_path = self.config.get("chroma_path", "chroma_data")
        self.conn = None
        self.chroma_client = None
        self.collection = None

    def initialize(self):
        """初始化技能"""
        super().initialize()
        self._init_database()

        if CHROMA_AVAILABLE:
            self._init_chromadb()

        self.logger.info(f"MemPalace记忆系统已初始化")
        return True

    def shutdown(self):
        """关闭技能"""
        if self.conn:
            self.conn.close()

        if self.chroma_client:
            self.chroma_client.reset()

        self.logger.info("MemPalace记忆系统已关闭")

    def _init_database(self):
        """初始化SQLite数据库"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 创建表结构
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wing_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wing_id) REFERENCES wings(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wing_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wing_id) REFERENCES wings(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS closets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                summary TEXT,
                aaak_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drawers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                closet_id INTEGER NOT NULL,
                original_text TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (closet_id) REFERENCES closets(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tunnels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id1 INTEGER NOT NULL,
                room_id2 INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id1) REFERENCES rooms(id),
                FOREIGN KEY (room_id2) REFERENCES rooms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valid_until TIMESTAMP,
                confidence REAL DEFAULT 1.0
            )
        """)

        self.conn.commit()

    def _init_chromadb(self):
        """初始化ChromaDB向量数据库"""
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="memories",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"ChromaDB初始化失败: {e}")
            self.chroma_client = None

    def get_parameters(self) -> Dict:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "description": "执行的动作",
                "enum": [
                    "create_wing",
                    "create_room",
                    "store_memory",
                    "retrieve_memory",
                    "search",
                    "add_knowledge",
                    "query_knowledge",
                    "detect_conflicts",
                    "get_stats",
                    "export_data",
                    "import_data"
                ]
            },
            "wing_name": {
                "type": "string",
                "required": False,
                "description": "侧厅名称"
            },
            "wing_type": {
                "type": "string",
                "required": False,
                "description": "侧厅类型 (project/person/topic)"
            },
            "room_name": {
                "type": "string",
                "required": False,
                "description": "房间名称"
            },
            "memory_text": {
                "type": "string",
                "required": False,
                "description": "记忆文本"
            },
            "metadata": {
                "type": "object",
                "required": False,
                "description": "元数据"
            },
            "query": {
                "type": "string",
                "required": False,
                "description": "搜索查询"
            },
            "limit": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "结果数量限制"
            },
            "subject": {
                "type": "string",
                "required": False,
                "description": "知识三元组主体"
            },
            "predicate": {
                "type": "string",
                "required": False,
                "description": "知识三元组谓词"
            },
            "object": {
                "type": "string",
                "required": False,
                "description": "知识三元组客体"
            }
        }

    def validate_params(self, params: Dict) -> tuple[bool, Optional[str]]:
        """验证参数"""
        if "action" not in params:
            return False, "缺少必需参数: action"

        action = params["action"]

        if action == "create_wing":
            if "wing_name" not in params:
                return False, "创建侧厅需要 wing_name 参数"
            if "wing_type" not in params:
                return False, "创建侧厅需要 wing_type 参数"

        elif action == "create_room":
            if "wing_name" not in params:
                return False, "创建房间需要 wing_name 参数"
            if "room_name" not in params:
                return False, "创建房间需要 room_name 参数"

        elif action == "store_memory":
            if "wing_name" not in params:
                return False, "存储记忆需要 wing_name 参数"
            if "room_name" not in params:
                return False, "存储记忆需要 room_name 参数"
            if "memory_text" not in params:
                return False, "存储记忆需要 memory_text 参数"

        elif action == "add_knowledge":
            required = ["subject", "predicate", "object"]
            for req in required:
                if req not in params:
                    return False, f"添加知识需要 {req} 参数"

        return True, None

    @handle_errors
    def execute(self, params: Dict) -> Dict:
        """执行技能"""
        action = params.get("action")

        if action == "create_wing":
            return self._create_wing(params)
        elif action == "create_room":
            return self._create_room(params)
        elif action == "store_memory":
            return self._store_memory(params)
        elif action == "retrieve_memory":
            return self._retrieve_memory(params)
        elif action == "search":
            return self._search(params)
        elif action == "add_knowledge":
            return self._add_knowledge(params)
        elif action == "query_knowledge":
            return self._query_knowledge(params)
        elif action == "detect_conflicts":
            return self._detect_conflicts(params)
        elif action == "get_stats":
            return self._get_stats()
        elif action == "export_data":
            return self._export_data(params)
        elif action == "import_data":
            return self._import_data(params)
        else:
            return {
                "success": False,
                "error": f"未知动作: {action}"
            }

    def _create_wing(self, params: Dict) -> Dict:
        """创建侧厅"""
        wing_name = params["wing_name"]
        wing_type = params.get("wing_type", "project")

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO wings (name, type) VALUES (?, ?)",
                (wing_name, wing_type)
            )
            self.conn.commit()

            return {
                "success": True,
                "message": f"侧厅 '{wing_name}' 创建成功",
                "wing_id": cursor.lastrowid
            }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "error": f"侧厅 '{wing_name}' 已存在"
            }

    def _create_room(self, params: Dict) -> Dict:
        """创建房间"""
        wing_name = params["wing_name"]
        room_name = params["room_name"]

        cursor = self.conn.cursor()

        # 查找侧厅ID
        cursor.execute("SELECT id FROM wings WHERE name = ?", (wing_name,))
        wing = cursor.fetchone()

        if not wing:
            return {
                "success": False,
                "error": f"侧厅 '{wing_name}' 不存在"
            }

        try:
            cursor.execute(
                "INSERT INTO rooms (wing_id, name) VALUES (?, ?)",
                (wing[0], room_name)
            )
            self.conn.commit()

            return {
                "success": True,
                "message": f"房间 '{room_name}' 在侧厅 '{wing_name}' 中创建成功",
                "room_id": cursor.lastrowid
            }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "error": f"房间 '{room_name}' 已存在"
            }

    def _store_memory(self, params: Dict) -> Dict:
        """存储记忆"""
        wing_name = params["wing_name"]
        room_name = params["room_name"]
        memory_text = params["memory_text"]
        metadata = params.get("metadata", {})

        cursor = self.conn.cursor()

        # 查找房间ID
        cursor.execute("""
            SELECT r.id FROM rooms r
            JOIN wings w ON r.wing_id = w.id
            WHERE w.name = ? AND r.name = ?
        """, (wing_name, room_name))

        room = cursor.fetchone()

        if not room:
            return {
                "success": False,
                "error": f"房间 '{room_name}' 在侧厅 '{wing_name}' 中不存在"
            }

        room_id = room[0]

        # 生成AAAK压缩数据
        aaak_data = self._compress_to_aaak(memory_text)

        # 创建衣柜
        cursor.execute(
            "INSERT INTO closets (room_id, summary, aaak_data) VALUES (?, ?, ?)",
            (room_id, memory_text[:200], aaak_data)
        )
        closet_id = cursor.lastrowid

        # 创建抽屉（存储原文）
        cursor.execute(
            "INSERT INTO drawers (closet_id, original_text, metadata) VALUES (?, ?, ?)",
            (closet_id, memory_text, json.dumps(metadata))
        )
        drawer_id = cursor.lastrowid

        # 如果ChromaDB可用，添加向量索引
        if self.collection:
            try:
                self.collection.add(
                    documents=[memory_text],
                    metadatas=[{
                        "wing": wing_name,
                        "room": room_name,
                        "drawer_id": drawer_id,
                        **metadata
                    }],
                    ids=[f"mem_{drawer_id}"]
                )
            except Exception as e:
                print(f"向量索引失败: {e}")

        self.conn.commit()

        return {
            "success": True,
            "message": "记忆存储成功",
            "drawer_id": drawer_id,
            "aaak_size": len(aaak_data),
            "compression_ratio": len(aaak_data) / len(memory_text) if memory_text else 0
        }

    def _retrieve_memory(self, params: Dict) -> Dict:
        """检索记忆"""
        wing_name = params.get("wing_name")
        room_name = params.get("room_name")
        limit = params.get("limit", 10)

        cursor = self.conn.cursor()

        if wing_name and room_name:
            # 从特定房间检索
            cursor.execute("""
                SELECT d.id, d.original_text, d.metadata, d.created_at
                FROM drawers d
                JOIN closets c ON d.closet_id = c.id
                JOIN rooms r ON c.room_id = r.id
                JOIN wings w ON r.wing_id = w.id
                WHERE w.name = ? AND r.name = ?
                ORDER BY d.created_at DESC
                LIMIT ?
            """, (wing_name, room_name, limit))
        elif wing_name:
            # 从侧厅检索
            cursor.execute("""
                SELECT d.id, d.original_text, d.metadata, d.created_at
                FROM drawers d
                JOIN closets c ON d.closet_id = c.id
                JOIN rooms r ON c.room_id = r.id
                JOIN wings w ON r.wing_id = w.id
                WHERE w.name = ?
                ORDER BY d.created_at DESC
                LIMIT ?
            """, (wing_name, limit))
        else:
            # 全局检索
            cursor.execute("""
                SELECT d.id, d.original_text, d.metadata, d.created_at
                FROM drawers d
                ORDER BY d.created_at DESC
                LIMIT ?
            """, (limit,))

        memories = []
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "text": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })

        return {
            "success": True,
            "memories": memories,
            "count": len(memories)
        }

    def _search(self, params: Dict) -> Dict:
        """搜索记忆"""
        query = params.get("query", "")
        limit = params.get("limit", 10)

        if not query:
            return {
                "success": False,
                "error": "搜索查询不能为空"
            }

        # 如果ChromaDB可用，使用向量搜索
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )

                memories = []
                if results["ids"] and results["ids"][0]:
                    for i, doc_id in enumerate(results["ids"][0]):
                        memories.append({
                            "id": doc_id,
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i] if "distances" in results else None
                        })

                return {
                    "success": True,
                    "memories": memories,
                    "count": len(memories),
                    "search_type": "vector"
                }
            except Exception as e:
                print(f"向量搜索失败: {e}")

        # 降级到文本搜索
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.id, d.original_text, d.metadata, d.created_at
            FROM drawers d
            WHERE d.original_text LIKE ?
            ORDER BY d.created_at DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        memories = []
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "text": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })

        return {
            "success": True,
            "memories": memories,
            "count": len(memories),
            "search_type": "text"
        }

    def _add_knowledge(self, params: Dict) -> Dict:
        """添加知识三元组"""
        subject = params["subject"]
        predicate = params["predicate"]
        object = params["object"]
        valid_until = params.get("valid_until")
        confidence = params.get("confidence", 1.0)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_graph (subject, predicate, object, valid_until, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (subject, predicate, object, valid_until, confidence))

        self.conn.commit()

        return {
            "success": True,
            "message": "知识添加成功",
            "knowledge_id": cursor.lastrowid
        }

    def _query_knowledge(self, params: Dict) -> Dict:
        """查询知识图谱"""
        subject = params.get("subject")
        predicate = params.get("predicate")
        object = params.get("object")

        cursor = self.conn.cursor()

        conditions = []
        values = []

        if subject:
            conditions.append("subject = ?")
            values.append(subject)
        if predicate:
            conditions.append("predicate = ?")
            values.append(predicate)
        if object:
            conditions.append("object = ?")
            values.append(object)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(f"""
            SELECT id, subject, predicate, object, valid_from, valid_until, confidence
            FROM knowledge_graph
            WHERE {where_clause}
            AND (valid_until IS NULL OR valid_until > datetime('now'))
            ORDER BY confidence DESC
        """, values)

        knowledge = []
        for row in cursor.fetchall():
            knowledge.append({
                "id": row[0],
                "subject": row[1],
                "predicate": row[2],
                "object": row[3],
                "valid_from": row[4],
                "valid_until": row[5],
                "confidence": row[6]
            })

        return {
            "success": True,
            "knowledge": knowledge,
            "count": len(knowledge)
        }

    def _detect_conflicts(self, params: Dict) -> Dict:
        """检测知识冲突"""
        cursor = self.conn.cursor()

        # 查找可能冲突的知识
        cursor.execute("""
            SELECT k1.id as id1, k1.subject, k1.predicate, k1.object,
                   k2.id as id2, k2.subject as subject2, k2.predicate as predicate2, k2.object as object2
            FROM knowledge_graph k1
            JOIN knowledge_graph k2 ON k1.subject = k2.subject AND k1.predicate = k2.predicate
            WHERE k1.object != k2.object
            AND (k1.valid_until IS NULL OR k1.valid_until > datetime('now'))
            AND (k2.valid_until IS NULL OR k2.valid_until > datetime('now'))
        """)

        conflicts = []
        for row in cursor.fetchall():
            conflicts.append({
                "id1": row[0],
                "statement1": f"{row[1]} {row[2]} {row[3]}",
                "id2": row[4],
                "statement2": f"{row[5]} {row[6]} {row[7]}",
                "type": "contradiction"
            })

        return {
            "success": True,
            "conflicts": conflicts,
            "count": len(conflicts)
        }

    def _get_stats(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()

        stats = {}

        # 侧厅统计
        cursor.execute("SELECT COUNT(*) FROM wings")
        stats["wings_count"] = cursor.fetchone()[0]

        # 房间统计
        cursor.execute("SELECT COUNT(*) FROM rooms")
        stats["rooms_count"] = cursor.fetchone()[0]

        # 记忆统计
        cursor.execute("SELECT COUNT(*) FROM drawers")
        stats["memories_count"] = cursor.fetchone()[0]

        # 知识三元组统计
        cursor.execute("SELECT COUNT(*) FROM knowledge_graph")
        stats["knowledge_count"] = cursor.fetchone()[0]

        # 数据库大小
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        stats["db_size_bytes"] = db_size
        stats["db_size_mb"] = db_size / (1024 * 1024)

        # ChromaDB统计
        if self.collection:
            try:
                stats["vector_count"] = self.collection.count()
            except:
                stats["vector_count"] = 0

        return {
            "success": True,
            "stats": stats
        }

    def _export_data(self, params: Dict) -> Dict:
        """导出数据"""
        output_file = params.get("output_file", "mempalace_export.json")

        cursor = self.conn.cursor()

        # 导出所有数据
        export_data = {
            "wings": [],
            "rooms": [],
            "memories": [],
            "knowledge": [],
            "exported_at": datetime.now().isoformat()
        }

        cursor.execute("SELECT * FROM wings")
        export_data["wings"] = [
            {"id": row[0], "name": row[1], "type": row[2], "created_at": row[3]}
            for row in cursor.fetchall()
        ]

        cursor.execute("SELECT * FROM rooms")
        export_data["rooms"] = [
            {"id": row[0], "wing_id": row[1], "name": row[2], "created_at": row[3]}
            for row in cursor.fetchall()
        ]

        cursor.execute("SELECT * FROM drawers")
        export_data["memories"] = [
            {
                "id": row[0],
                "closet_id": row[1],
                "text": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "created_at": row[4]
            }
            for row in cursor.fetchall()
        ]

        cursor.execute("SELECT * FROM knowledge_graph")
        export_data["knowledge"] = [
            {
                "id": row[0],
                "subject": row[1],
                "predicate": row[2],
                "object": row[3],
                "valid_from": row[4],
                "valid_until": row[5],
                "confidence": row[6]
            }
            for row in cursor.fetchall()
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "message": f"数据已导出到 {output_file}",
            "output_file": output_file
        }

    def _import_data(self, params: Dict) -> Dict:
        """导入数据"""
        input_file = params.get("input_file")

        if not input_file or not os.path.exists(input_file):
            return {
                "success": False,
                "error": f"文件不存在: {input_file}"
            }

        with open(input_file, "r", encoding="utf-8") as f:
            import_data = json.load(f)

        cursor = self.conn.cursor()

        # 导入侧厅
        for wing in import_data.get("wings", []):
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO wings (name, type) VALUES (?, ?)",
                    (wing["name"], wing["type"])
                )
            except Exception as e:
                print(f"导入侧厅失败: {e}")

        # 导入房间
        for room in import_data.get("rooms", []):
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO rooms (wing_id, name) VALUES (?, ?)",
                    (room["wing_id"], room["name"])
                )
            except Exception as e:
                print(f"导入房间失败: {e}")

        # 导入知识
        for knowledge in import_data.get("knowledge", []):
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO knowledge_graph (subject, predicate, object, valid_from, valid_until, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        knowledge["subject"],
                        knowledge["predicate"],
                        knowledge["object"],
                        knowledge.get("valid_from"),
                        knowledge.get("valid_until"),
                        knowledge.get("confidence", 1.0)
                    )
                )
            except Exception as e:
                print(f"导入知识失败: {e}")

        self.conn.commit()

        return {
            "success": True,
            "message": f"数据已从 {input_file} 导入",
            "imported_wings": len(import_data.get("wings", [])),
            "imported_rooms": len(import_data.get("rooms", [])),
            "imported_knowledge": len(import_data.get("knowledge", []))
        }

    def _compress_to_aaak(self, text: str) -> str:
        """将文本压缩为AAAK格式"""
        # 简化的AAAK压缩实现
        # 实际实现会更复杂，这里只是示例

        if not text:
            return ""

        # 移除冗余词
        stop_words = {"的", "了", "和", "是", "在", "有", "我", "都", "个", "与", "the", "a", "an", "is", "are"}
        words = text.split()
        filtered_words = [w for w in words if w.lower() not in stop_words]

        # 使用哈希作为压缩表示
        compressed = "AAAK:" + hashlib.md5(" ".join(filtered_words).encode()).hexdigest()

        return compressed


# 技能实例
skill = MemPalaceSkill()


if __name__ == "__main__":
    # 测试技能
    skill.initialize()

    # 创建侧厅
    print("1. 创建侧厅:")
    result = skill.execute({
        "action": "create_wing",
        "wing_name": "AI开发",
        "wing_type": "project"
    })
    print(f"   {result}")

    # 创建房间
    print("\n2. 创建房间:")
    result = skill.execute({
        "action": "create_room",
        "wing_name": "AI开发",
        "room_name": "架构设计"
    })
    print(f"   {result}")

    # 存储记忆
    print("\n3. 存储记忆:")
    result = skill.execute({
        "action": "store_memory",
        "wing_name": "AI开发",
        "room_name": "架构设计",
        "memory_text": "我们决定使用微服务架构来提高系统的可扩展性",
        "metadata": {"topic": "architecture", "importance": "high"}
    })
    print(f"   {result}")

    # 检索记忆
    print("\n4. 检索记忆:")
    result = skill.execute({
        "action": "retrieve_memory",
        "wing_name": "AI开发",
        "room_name": "架构设计",
        "limit": 5
    })
    print(f"   找到 {result.get('count', 0)} 条记忆")

    # 添加知识
    print("\n5. 添加知识:")
    result = skill.execute({
        "action": "add_knowledge",
        "subject": "MemPalace",
        "predicate": "使用",
        "object": "记忆宫殿术"
    })
    print(f"   {result}")

    # 获取统计
    print("\n6. 获取统计:")
    result = skill.execute({"action": "get_stats"})
    print(f"   {result}")

    skill.shutdown()
    print("\nMemPalace技能测试完成")
