#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 数据库集成模块

功能:
- 智能体数据持久化
- 竞争和进化历史存储
- 大模型使用记录
- 智能体性能分析

用法:
    from agent.database_integration import DatabaseManager

    db_manager = DatabaseManager()
    # 初始化数据库
    db_manager.initialize()
    # 保存智能体信息
    db_manager.save_agent(agent_info)
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any

# 确保日志目录存在
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(str(log_dir / "database_integration.log")), logging.StreamHandler()],
)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: Optional[str] = None):
        # 使用绝对路径
        base_dir = Path(__file__).parent.parent
        self.db_path = db_path or str(base_dir / "data" / "agent_database.db")
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.logger = logging.getLogger("DatabaseManager")

    def initialize(self) -> bool:
        """初始化数据库"""
        try:
            # 确保数据目录存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # 连接数据库
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            # 创建表
            self._create_tables()

            self.logger.info(f"数据库初始化成功: {self.db_path}")
            return True
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            return False

    def _create_tables(self):
        """创建数据库表"""
        # 智能体表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            version TEXT,
            agent_type TEXT,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            abilities TEXT,
            skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 竞争历史表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rounds INTEGER,
            results TEXT
        )
        ''')

        # 进化历史表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS evolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner TEXT,
            loser TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            task TEXT
        )
        ''')

        # 大模型表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            path TEXT,
            size REAL,
            type TEXT,
            extension TEXT,
            last_modified TIMESTAMP,
            used_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 智能体训练表
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS training (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT,
            training_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN
        )
        ''')

        # 提交更改
        self.conn.commit()

    def save_agent(self, agent_info: Dict[str, Any]) -> bool:
        """保存智能体信息"""
        try:
            # 检查智能体是否存在
            self.cursor.execute("SELECT id FROM agents WHERE name = ?", (agent_info["name"],))
            existing = self.cursor.fetchone()

            if existing:
                # 更新智能体信息
                self.cursor.execute('''
                UPDATE agents SET
                    description = ?,
                    version = ?,
                    agent_type = ?,
                    level = ?,
                    experience = ?,
                    wins = ?,
                    losses = ?,
                    abilities = ?,
                    skills = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
                ''', (
                    agent_info.get("description", ""),
                    agent_info.get("version", "1.0.0"),
                    agent_info.get("agent_type", "general"),
                    agent_info.get("level", 1),
                    agent_info.get("experience", 0),
                    agent_info.get("wins", 0),
                    agent_info.get("losses", 0),
                    json.dumps(agent_info.get("abilities", {})),
                    json.dumps(agent_info.get("skills", [])),
                    agent_info["name"]
                ))
            else:
                # 插入新智能体
                self.cursor.execute('''
                INSERT INTO agents (
                    name, description, version, agent_type, level, experience, wins, losses, abilities, skills
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_info["name"],
                    agent_info.get("description", ""),
                    agent_info.get("version", "1.0.0"),
                    agent_info.get("agent_type", "general"),
                    agent_info.get("level", 1),
                    agent_info.get("experience", 0),
                    agent_info.get("wins", 0),
                    agent_info.get("losses", 0),
                    json.dumps(agent_info.get("abilities", {})),
                    json.dumps(agent_info.get("skills", []))
                ))

            self.conn.commit()
            self.logger.info(f"智能体信息保存成功: {agent_info['name']}")
            return True
        except Exception as e:
            self.logger.error(f"保存智能体信息失败: {e}")
            return False

    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """获取智能体信息"""
        try:
            self.cursor.execute("SELECT * FROM agents WHERE name = ?", (agent_name,))
            row = self.cursor.fetchone()

            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "version": row[3],
                    "agent_type": row[4],
                    "level": row[5],
                    "experience": row[6],
                    "wins": row[7],
                    "losses": row[8],
                    "abilities": json.loads(row[9]) if row[9] else {},
                    "skills": json.loads(row[10]) if row[10] else [],
                    "created_at": row[11],
                    "updated_at": row[12]
                }
            return None
        except Exception as e:
            self.logger.error(f"获取智能体信息失败: {e}")
            return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有智能体"""
        try:
            self.cursor.execute("SELECT * FROM agents ORDER BY level DESC, experience DESC")
            rows = self.cursor.fetchall()

            agents = []
            for row in rows:
                agents.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "version": row[3],
                    "agent_type": row[4],
                    "level": row[5],
                    "experience": row[6],
                    "wins": row[7],
                    "losses": row[8],
                    "abilities": json.loads(row[9]) if row[9] else {},
                    "skills": json.loads(row[10]) if row[10] else [],
                    "created_at": row[11],
                    "updated_at": row[12]
                })

            return agents
        except Exception as e:
            self.logger.error(f"列出智能体失败: {e}")
            return []

    def save_competition(self, rounds: int, results: Dict[str, Any]) -> bool:
        """保存竞争记录"""
        try:
            self.cursor.execute('''
            INSERT INTO competitions (rounds, results)
            VALUES (?, ?)
            ''', (rounds, json.dumps(results)))

            self.conn.commit()
            self.logger.info(f"竞争记录保存成功，共 {rounds} 轮")
            return True
        except Exception as e:
            self.logger.error(f"保存竞争记录失败: {e}")
            return False

    def save_evolution(self, winner: str, loser: str, task: Dict[str, Any]) -> bool:
        """保存进化记录"""
        try:
            self.cursor.execute('''
            INSERT INTO evolution (winner, loser, task)
            VALUES (?, ?, ?)
            ''', (winner, loser, json.dumps(task)))

            self.conn.commit()
            self.logger.info(f"进化记录保存成功: {winner} 融合了 {loser}")
            return True
        except Exception as e:
            self.logger.error(f"保存进化记录失败: {e}")
            return False

    def save_model(self, model_info: Dict[str, Any]) -> bool:
        """保存大模型信息"""
        try:
            # 检查模型是否存在
            self.cursor.execute("SELECT id FROM models WHERE name = ?", (model_info["name"],))
            existing = self.cursor.fetchone()

            if existing:
                # 更新模型信息
                self.cursor.execute('''
                UPDATE models SET
                    path = ?,
                    size = ?,
                    type = ?,
                    extension = ?,
                    last_modified = ?
                WHERE name = ?
                ''', (
                    model_info.get("path"),
                    model_info.get("size"),
                    model_info.get("type"),
                    model_info.get("extension"),
                    model_info.get("last_modified"),
                    model_info["name"]
                ))
            else:
                # 插入新模型
                self.cursor.execute('''
                INSERT INTO models (
                    name, path, size, type, extension, last_modified
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    model_info["name"],
                    model_info.get("path"),
                    model_info.get("size"),
                    model_info.get("type"),
                    model_info.get("extension"),
                    model_info.get("last_modified")
                ))

            self.conn.commit()
            self.logger.info(f"大模型信息保存成功: {model_info['name']}")
            return True
        except Exception as e:
            self.logger.error(f"保存大模型信息失败: {e}")
            return False

    def increment_model_usage(self, model_name: str) -> bool:
        """增加模型使用次数"""
        try:
            self.cursor.execute(
                "UPDATE models SET used_count = used_count + 1 WHERE name = ?",
                (model_name,)
            )
            self.conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"增加模型使用次数失败: {e}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有大模型"""
        try:
            self.cursor.execute("SELECT * FROM models ORDER BY used_count DESC")
            rows = self.cursor.fetchall()

            models = []
            for row in rows:
                models.append({
                    "id": row[0],
                    "name": row[1],
                    "path": row[2],
                    "size": row[3],
                    "type": row[4],
                    "extension": row[5],
                    "last_modified": row[6],
                    "used_count": row[7],
                    "created_at": row[8]
                })

            return models
        except Exception as e:
            self.logger.error(f"列出大模型失败: {e}")
            return []

    def save_training(self, agent_name: str, training_data: List[Dict[str, Any]], success: bool) -> bool:
        """保存训练记录"""
        try:
            self.cursor.execute('''
            INSERT INTO training (agent_name, training_data, success)
            VALUES (?, ?, ?)
            ''', (agent_name, json.dumps(training_data), success))

            self.conn.commit()
            self.logger.info(f"训练记录保存成功: {agent_name}")
            return True
        except Exception as e:
            self.logger.error(f"保存训练记录失败: {e}")
            return False

    def get_agent_history(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体历史记录"""
        try:
            # 获取智能体信息
            agent = self.get_agent(agent_name)

            # 获取训练记录
            self.cursor.execute(
                "SELECT * FROM training WHERE agent_name = ? ORDER BY timestamp DESC",
                (agent_name,)
            )
            training_rows = self.cursor.fetchall()

            training_history = []
            for row in training_rows:
                training_history.append({
                    "id": row[0],
                    "training_data": json.loads(row[2]) if row[2] else [],
                    "timestamp": row[3],
                    "success": row[4]
                })

            # 获取进化记录（作为获胜者）
            self.cursor.execute(
                "SELECT * FROM evolution WHERE winner = ? ORDER BY timestamp DESC",
                (agent_name,)
            )
            evolution_rows = self.cursor.fetchall()

            evolution_history = []
            for row in evolution_rows:
                evolution_history.append({
                    "id": row[0],
                    "loser": row[2],
                    "timestamp": row[3],
                    "task": json.loads(row[4]) if row[4] else {}
                })

            return {
                "agent": agent,
                "training_history": training_history,
                "evolution_history": evolution_history
            }
        except Exception as e:
            self.logger.error(f"获取智能体历史记录失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager_instance = None


def get_database_manager() -> DatabaseManager:
    """获取全局数据库管理器"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
        _db_manager_instance.initialize()
    return _db_manager_instance


if __name__ == "__main__":
    # 测试数据库管理器
    db_manager = DatabaseManager()
    db_manager.initialize()

    print("=" * 80)
    print("数据库集成测试")
    print("=" * 80)

    # 测试保存智能体
    print("\n1. 保存智能体信息...")
    agent_info = {
        "name": "test_agent",
        "description": "测试智能体",
        "version": "1.0.0",
        "agent_type": "general",
        "level": 2,
        "experience": 1500,
        "wins": 5,
        "losses": 2,
        "abilities": {"intelligence": 85, "speed": 75},
        "skills": ["github_opensource", "system_optimizer"]
    }
    db_manager.save_agent(agent_info)

    # 测试获取智能体
    print("\n2. 获取智能体信息...")
    agent = db_manager.get_agent("test_agent")
    if agent:
        print(f"智能体: {agent['name']}")
        print(f"等级: {agent['level']}")
        print(f"经验值: {agent['experience']}")
        print(f"能力: {agent['abilities']}")

    # 测试列出智能体
    print("\n3. 列出所有智能体...")
    agents = db_manager.list_agents()
    print(f"共 {len(agents)} 个智能体:")
    for agent in agents:
        print(f"  - {agent['name']} (等级: {agent['level']})")

    # 测试保存竞争记录
    print("\n4. 保存竞争记录...")
    competition_results = {
        "rankings": [
            {"name": "test_agent", "win_rate": 71.43, "level": 2},
            {"name": "other_agent", "win_rate": 28.57, "level": 1}
        ]
    }
    db_manager.save_competition(3, competition_results)

    # 测试保存进化记录
    print("\n5. 保存进化记录...")
    task = {"task_type": "data_analysis", "difficulty": 5}
    db_manager.save_evolution("test_agent", "other_agent", task)

    # 测试保存大模型
    print("\n6. 保存大模型信息...")
    model_info = {
        "name": "llama-2-7b-chat.Q4_K_M",
        "path": "C:\\Users\\User\\Models\\llama-2-7b-chat.Q4_K_M.gguf",
        "size": 3500.0,
        "type": "llama",
        "extension": ".gguf",
        "last_modified": "2024-01-01 00:00:00"
    }
    db_manager.save_model(model_info)

    # 测试列出大模型
    print("\n7. 列出所有大模型...")
    models = db_manager.list_models()
    print(f"共 {len(models)} 个大模型:")
    for model in models:
        print(f"  - {model['name']} ({model['type']}, {model['size']:.2f} MB)")

    # 测试获取智能体历史
    print("\n8. 获取智能体历史记录...")
    history = db_manager.get_agent_history("test_agent")
    print(f"智能体: {history.get('agent', {}).get('name')}")
    print(f"训练记录: {len(history.get('training_history', []))}")
    print(f"进化记录: {len(history.get('evolution_history', []))}")

    # 关闭数据库连接
    db_manager.close()

    print("\n数据库集成测试完成")
    print("=" * 80)
