#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 智能体基类与竞争管理器

功能:
- 智能体基类定义
- 智能体竞争机制
- 智能体融合与进化
- 智能体管理

用法:
    from agent.base import Agent, AgentManager

    class MyAgent(Agent):
        name = "my_agent"

        def execute(self, task):
            return {"success": True, "result": "完成任务"}

    # 创建管理器
    manager = AgentManager()
    manager.register(MyAgent())

    # 开始竞争
    manager.start_competition()
"""

import json
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import sys
# 导入技能系统
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.base import Skill, get_registry
from config_manager import get_config_manager
# 导入大模型集成
from agent.llm_integration import LLMIntegrator, LLMAgentEnhancer
# 导入数据库集成
from agent.database_integration import get_database_manager

# 确保日志目录存在
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(str(log_dir / "agent.log")), logging.StreamHandler()],
)


def handle_errors(func: Callable) -> Callable:
    """统一错误处理装饰器"""

    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        try:
            self.logger.info(f"执行方法: {func.__name__}")
            result = func(self, *args, **kwargs)
            # 确保返回值是字典格式
            if not isinstance(result, dict):
                return {"success": True, "result": result}
            self.logger.info(f"方法执行成功: {func.__name__}")
            return result
        except Exception as e:
            error_message = str(e)
            # 记录错误
            self._last_error = error_message
            self.status = AgentStatus.ERROR

            # 使用 logger 记录错误
            self.logger.error(f"方法执行失败: {func.__name__}, 错误: {error_message}")

            return {"success": False, "error": error_message}

    return wrapper


class AgentStatus(Enum):
    """智能体状态"""

    DISABLED = "disabled"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    EVOLVING = "evolving"


class AgentType(Enum):
    """智能体类型"""

    GENERAL = "general"
    SPECIALIZED = "specialized"
    HYBRID = "hybrid"


@dataclass
class AgentInfo:
    """智能体信息"""

    name: str
    description: str
    version: str
    author: str
    agent_type: AgentType = AgentType.GENERAL
    level: int = 1
    experience: int = 0
    skills: List[str] = field(default_factory=list)
    abilities: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.DISABLED
    last_error: Optional[str] = None


class Agent(ABC):
    """智能体基类"""

    # 智能体元数据（子类必须定义）
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    agent_type: AgentType = AgentType.GENERAL

    # 能力和技能
    abilities: Dict[str, Any] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or {}
        self.status: AgentStatus = AgentStatus.DISABLED
        self._initialized: bool = False
        self._last_error: Optional[str] = None
        self.level: int = 1
        self.experience: int = 0
        self.competition_wins: int = 0
        self.competition_losses: int = 0
        self.fused_agents: List[str] = []  # 融合过的智能体
        self.training_history: List[Dict[str, Any]] = []  # 训练历史
        # 初始化日志
        self.logger = logging.getLogger(self.name)
        # 初始化配置管理器
        self.config_manager = get_config_manager()
        # 初始化技能注册中心
        self.skill_registry = get_registry()
        # 初始化大模型集成
        self.llm_integrator = LLMIntegrator()
        self.llm_enhancer = LLMAgentEnhancer(self.llm_integrator)
        # 初始化数据库管理器
        self.db_manager = get_database_manager()
        # 加载智能体配置
        self._load_config()
        # 从数据库加载智能体状态
        self._load_from_database()

    @property
    def info(self) -> AgentInfo:
        """获取智能体信息"""
        return AgentInfo(
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            agent_type=self.agent_type,
            level=self.level,
            experience=self.experience,
            skills=self.skills,
            abilities=self.abilities,
            status=self.status,
            last_error=self._last_error,
        )

    def initialize(self) -> bool:
        """初始化智能体"""
        if self._initialized:
            return True

        try:
            if self._do_initialize():
                self.status = AgentStatus.READY
                self._initialized = True
                return True
            else:
                self.status = AgentStatus.ERROR
                return False
        except Exception as e:
            self._last_error = str(e)
            self.status = AgentStatus.ERROR
            return False

    def _do_initialize(self) -> bool:
        """实际初始化逻辑（子类可重写）"""
        # 加载技能
        for skill_name in self.skills:
            if not self.skill_registry.get(skill_name):
                self.logger.warning(f"技能 '{skill_name}' 未注册")
        return True

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务（子类必须实现）"""
        pass

    def train(self, training_data: List[Dict[str, Any]]) -> bool:
        """使用大模型训练智能体"""
        self.logger.info(f"{self.name} 开始训练")
        # 记录训练数据
        self.training_history.extend(training_data)
        # 使用大模型训练
        success = self.llm_enhancer.train_agent(self, training_data)
        if success:
            self.logger.info(f"{self.name} 训练成功")
            # 获得训练经验值
            self.gain_experience(len(training_data) * 50)
            # 保存训练记录到数据库
            self.db_manager.save_training(self.name, training_data, success)
        return success

    def discover_models(self) -> List[Dict[str, Any]]:
        """发现本地大模型"""
        return self.llm_integrator.discover_local_models()

    def load_model(self, model_name: str) -> bool:
        """加载大模型"""
        return self.llm_integrator.load_model(model_name)

    def optimize_memory(self) -> bool:
        """优化内存使用"""
        return self.llm_integrator.optimize_memory_usage()

    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证任务"""
        if "task_type" not in task:
            return False, "缺少必需参数: task_type"
        return True, None

    def shutdown(self) -> None:
        """关闭智能体"""
        # 保存状态到数据库
        self._save_to_database()
        # 优化内存使用
        self.optimize_memory()
        # 执行关闭逻辑
        self._do_shutdown()
        self.status = AgentStatus.DISABLED
        self._initialized = False

    def _do_shutdown(self) -> None:
        """实际关闭逻辑（子类可重写）"""
        pass

    def _load_config(self) -> None:
        """加载智能体配置"""
        config_name = self.name.lower().replace(" ", "_")
        agent_config = self.config_manager.load_config(config_name)
        if agent_config:
            self.config.update(agent_config)
            self.logger.info(f"加载智能体配置: {config_name}")

    def _load_from_database(self) -> None:
        """从数据库加载智能体状态"""
        agent_data = self.db_manager.get_agent(self.name)
        if agent_data:
            self.level = agent_data.get("level", 1)
            self.experience = agent_data.get("experience", 0)
            self.competition_wins = agent_data.get("wins", 0)
            self.competition_losses = agent_data.get("losses", 0)
            self.abilities = agent_data.get("abilities", {})
            self.skills = agent_data.get("skills", [])
            self.logger.info(f"从数据库加载智能体状态: {self.name}")

    def _save_to_database(self) -> None:
        """保存智能体状态到数据库"""
        agent_info = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "agent_type": self.agent_type.value,
            "level": self.level,
            "experience": self.experience,
            "wins": self.competition_wins,
            "losses": self.competition_losses,
            "abilities": self.abilities,
            "skills": self.skills
        }
        self.db_manager.save_agent(agent_info)

    def _save_evolution(self, loser: str, task: Dict[str, Any]) -> None:
        """保存进化记录到数据库"""
        self.db_manager.save_evolution(self.name, loser, task)

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        # 首先从本地配置中获取
        value = self.config.get(key, default)
        if value is not default:
            return value
        # 如果本地配置中没有，从配置管理器中获取
        config_name = self.name.lower().replace(" ", "_")
        return self.config_manager.get_config(config_name, key, default)

    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值"""
        config_name = self.name.lower().replace(" ", "_")
        success = self.config_manager.set_config(config_name, key, value)
        if success:
            # 更新本地配置
            self.config[key] = value
            self.logger.info(f"设置配置: {key} = {value}")
        return success

    def gain_experience(self, amount: int) -> None:
        """获得经验值"""
        self.experience += amount
        self.logger.info(f"{self.name} 获得 {amount} 经验值")
        # 检查是否升级
        self._check_level_up()
        # 保存到数据库
        self._save_to_database()

    def _check_level_up(self) -> bool:
        """检查是否升级"""
        # 简单的升级逻辑：每1000经验值升一级
        new_level = (self.experience // 1000) + 1
        if new_level > self.level:
            old_level = self.level
            self.level = new_level
            self.logger.info(f"{self.name} 升级了！从 {old_level} 级升到 {self.level} 级")
            # 升级时增强能力
            self._enhance_abilities()
            return True
        return False

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 使用大模型增强能力
        self.logger.info(f"{self.name} 升级时使用大模型增强能力")
        self.llm_enhancer.enhance_agent(self)
        # 子类可以重写此方法来定义具体的能力增强逻辑
        pass

    def fuse_with(self, other_agent: 'Agent') -> bool:
        """与其他智能体融合"""
        if self.status != AgentStatus.READY or other_agent.status != AgentStatus.READY:
            self.logger.error("智能体状态不正确，无法融合")
            return False

        try:
            self.status = AgentStatus.EVOLVING
            self.logger.info(f"{self.name} 开始与 {other_agent.name} 融合")

            # 融合技能
            for skill in other_agent.skills:
                if skill not in self.skills:
                    self.skills.append(skill)
                    self.logger.info(f"融合技能: {skill}")

            # 融合能力
            for ability, value in other_agent.abilities.items():
                if ability not in self.abilities:
                    self.abilities[ability] = value
                else:
                    # 能力值叠加
                    if isinstance(self.abilities[ability], (int, float)):
                        self.abilities[ability] = max(self.abilities[ability], value)
                    elif isinstance(self.abilities[ability], dict):
                        self.abilities[ability].update(value)
                self.logger.info(f"融合能力: {ability}")

            # 获得经验值
            self.gain_experience(other_agent.experience // 2)

            # 记录融合历史
            self.fused_agents.append(other_agent.name)

            # 使用大模型分析融合结果并优化
            self.logger.info(f"使用大模型分析融合结果")
            fusion_prompt = f"分析智能体 {self.name} 与 {other_agent.name} 的融合结果，提供优化建议以提高智能体性能。"
            result = self.llm_integrator.infer(fusion_prompt)
            if result.get("success"):
                self.logger.info(f"融合优化建议: {result['result']}")

            # 保存进化记录到数据库
            self._save_evolution(other_agent.name, {"task_type": "fusion"})

            self.status = AgentStatus.READY
            self.logger.info(f"{self.name} 与 {other_agent.name} 融合成功")
            return True
        except Exception as e:
            self._last_error = str(e)
            self.status = AgentStatus.ERROR
            self.logger.error(f"融合失败: {e}")
            return False


class AgentManager:
    """智能体管理器"""

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        self._agent_classes: Dict[str, Type[Agent]] = {}
        self._competitions: List[Dict[str, Any]] = []
        self._evolution_history: List[Dict[str, Any]] = []
        # 初始化数据库管理器
        from agent.database_integration import get_database_manager
        self.db_manager = get_database_manager()
        # 初始化日志
        self.logger = logging.getLogger("AgentManager")

    def register(self, agent: Agent) -> bool:
        """注册智能体"""
        if not agent.name:
            self.logger.error("智能体名称不能为空")
            return False

        if agent.name in self._agents:
            self.logger.warning(f"智能体 '{agent.name}' 已存在，将被覆盖")

        # 初始化智能体
        if agent.initialize():
            self._agents[agent.name] = agent
            self._agent_classes[agent.name] = agent.__class__
            self.logger.info(f"智能体 '{agent.name}' 注册成功")
            return True
        else:
            self.logger.error(f"智能体 '{agent.name}' 初始化失败")
            return False

    def unregister(self, agent_name: str) -> None:
        """注销智能体"""
        if agent_name in self._agents:
            self._agents[agent_name].shutdown()
            del self._agents[agent_name]
            del self._agent_classes[agent_name]
            self.logger.info(f"智能体 '{agent_name}' 已注销")

    def get(self, agent_name: str) -> Optional[Agent]:
        """获取智能体实例"""
        return self._agents.get(agent_name)

    def list_agents(self) -> List[AgentInfo]:
        """列出所有智能体"""
        return [agent.info for agent in self._agents.values()]

    def execute_task(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        agent = self._agents.get(agent_name)
        if not agent:
            return {"success": False, "error": f"智能体 '{agent_name}' 不存在"}

        # 验证任务
        valid, error = agent.validate_task(task)
        if not valid:
            return {"success": False, "error": error}

        # 执行任务
        try:
            agent.status = AgentStatus.RUNNING
            self.logger.info(f"执行任务: {task.get('task_type')} 由 {agent_name}")
            result = agent.execute(task)
            agent.status = AgentStatus.READY

            # 获得经验值
            if result.get("success", False):
                agent.gain_experience(100)

            self.logger.info(f"任务执行成功: {task.get('task_type')}")
            return result

        except Exception as e:
            error_message = str(e)
            agent._last_error = error_message
            agent.status = AgentStatus.ERROR

            self.logger.error(f"任务执行失败: {task.get('task_type')}, 错误: {error_message}")
            return {"success": False, "error": error_message}

    def start_competition(self, rounds: int = 5) -> Dict[str, Any]:
        """开始智能体竞争"""
        if len(self._agents) < 2:
            return {"success": False, "error": "至少需要两个智能体才能开始竞争"}

        self.logger.info(f"开始智能体竞争，共 {rounds} 轮")

        # 生成任务
        tasks = self._generate_tasks(rounds)
        competition_results = []

        # 两两竞争
        agent_names = list(self._agents.keys())
        for i in range(len(agent_names)):
            for j in range(i + 1, len(agent_names)):
                agent1_name = agent_names[i]
                agent2_name = agent_names[j]
                agent1 = self._agents[agent1_name]
                agent2 = self._agents[agent2_name]

                self.logger.info(f"{agent1_name} vs {agent2_name}")

                # 执行任务
                for task in tasks:
                    result1 = self.execute_task(agent1_name, task)
                    result2 = self.execute_task(agent2_name, task)

                    # 评估结果
                    winner = self._evaluate_winner(agent1, agent2, result1, result2, task)
                    if winner:
                        winner_agent = self._agents[winner]
                        loser_agent = agent1 if winner == agent2_name else agent2

                        # 获胜者获得经验值
                        winner_agent.gain_experience(200)
                        winner_agent.competition_wins += 1
                        loser_agent.competition_losses += 1

                        # 获胜者可以选择融合失败者
                        if random.random() > 0.5:  # 50% 的概率融合
                            self.logger.info(f"{winner} 选择融合 {loser_agent.name}")
                            if winner_agent.fuse_with(loser_agent):
                                evolution_record = {
                                    "winner": winner,
                                    "loser": loser_agent.name,
                                    "timestamp": datetime.now().isoformat(),
                                    "task": task
                                }
                                self._evolution_history.append(evolution_record)
                                # 保存进化记录到数据库
                                self.db_manager.save_evolution(winner, loser_agent.name, task)

                    # 记录竞争结果
                    competition_results.append({
                        "agent1": agent1_name,
                        "agent2": agent2_name,
                        "task": task,
                        "result1": result1,
                        "result2": result2,
                        "winner": winner
                    })

        # 记录竞争历史
        competition_record = {
            "timestamp": datetime.now().isoformat(),
            "rounds": rounds,
            "results": competition_results
        }
        self._competitions.append(competition_record)
        # 保存竞争记录到数据库
        self.db_manager.save_competition(rounds, competition_record)

        # 生成最终排名
        rankings = self._generate_rankings()

        self.logger.info("智能体竞争结束")
        return {
            "success": True,
            "rankings": rankings,
            "competition_results": competition_results
        }

    def _generate_tasks(self, count: int) -> List[Dict[str, Any]]:
        """生成任务"""
        tasks = []
        task_types = [
            "data_analysis",
            "problem_solving",
            "creative_writing",
            "code_generation",
            "decision_making"
        ]

        for i in range(count):
            task_type = random.choice(task_types)
            tasks.append({
                "task_type": task_type,
                "difficulty": random.randint(1, 10),
                "deadline": time.time() + 30,  # 30秒 deadline
                "id": f"task_{i+1}"
            })

        return tasks

    def _evaluate_winner(self, agent1: Agent, agent2: Agent, result1: Dict, result2: Dict, task: Dict) -> Optional[str]:
        """评估获胜者"""
        # 简单的评估逻辑：比较执行结果
        if not result1.get("success"):
            return agent2.name
        if not result2.get("success"):
            return agent1.name

        # 基于任务难度和执行结果评分
        score1 = self._calculate_score(result1, task)
        score2 = self._calculate_score(result2, task)

        if score1 > score2:
            return agent1.name
        elif score2 > score1:
            return agent2.name
        else:
            # 平局
            return None

    def _calculate_score(self, result: Dict, task: Dict) -> int:
        """计算得分"""
        score = 0
        if result.get("success"):
            # 基础分数
            score = 100
            # 根据任务难度调整
            score *= task.get("difficulty", 1) / 5
            # 根据执行时间调整（如果有）
            if "execution_time" in result:
                execution_time = result["execution_time"]
                if execution_time < 10:
                    score *= 1.5
                elif execution_time < 20:
                    score *= 1.2
        return int(score)

    def _generate_rankings(self) -> List[Dict[str, Any]]:
        """生成排名"""
        rankings = []
        for agent_name, agent in self._agents.items():
            rankings.append({
                "name": agent_name,
                "level": agent.level,
                "experience": agent.experience,
                "wins": agent.competition_wins,
                "losses": agent.competition_losses,
                "win_rate": agent.competition_wins / (agent.competition_wins + agent.competition_losses + 1) * 100
            })

        # 按胜率和等级排序
        rankings.sort(key=lambda x: (x["win_rate"], x["level"]), reverse=True)
        return rankings

    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """获取进化历史"""
        return self._evolution_history

    def get_competition_history(self) -> List[Dict[str, Any]]:
        """获取竞争历史"""
        return self._competitions

    def shutdown_all(self) -> None:
        """关闭所有智能体"""
        self.logger.info(f"开始关闭所有智能体，共 {len(self._agents)} 个")
        for agent in self._agents.values():
            try:
                # 优化内存使用
                agent.optimize_memory()
                agent.shutdown()
            except Exception as e:
                self.logger.error(f"关闭智能体 {agent.name} 失败: {e}")
        self._agents.clear()
        self._agent_classes.clear()
        self.logger.info("所有智能体已关闭")

    def get_agent_history(self, agent_name: str) -> Dict[str, Any]:
        """获取智能体历史记录"""
        return self.db_manager.get_agent_history(agent_name)

    def list_agents_from_db(self) -> List[Dict[str, Any]]:
        """从数据库列出所有智能体"""
        return self.db_manager.list_agents()

    def list_models_from_db(self) -> List[Dict[str, Any]]:
        """从数据库列出所有大模型"""
        return self.db_manager.list_models()

    def train_agent(self, agent_name: str, training_data: List[Dict[str, Any]]) -> bool:
        """训练智能体"""
        agent = self._agents.get(agent_name)
        if not agent:
            self.logger.error(f"智能体不存在: {agent_name}")
            return False

        self.logger.info(f"训练智能体: {agent_name}")
        return agent.train(training_data)

    def discover_models(self) -> List[Dict[str, Any]]:
        """发现所有本地大模型"""
        self.logger.info("发现本地大模型")
        models = []
        seen_models = set()

        for agent in self._agents.values():
            try:
                agent_models = agent.discover_models()
                for model in agent_models:
                    if model["name"] not in seen_models:
                        seen_models.add(model["name"])
                        models.append(model)
            except Exception as e:
                self.logger.error(f"智能体 {agent.name} 发现模型失败: {e}")

        return models

    def load_model(self, agent_name: str, model_name: str) -> bool:
        """为智能体加载大模型"""
        agent = self._agents.get(agent_name)
        if not agent:
            self.logger.error(f"智能体不存在: {agent_name}")
            return False

        self.logger.info(f"为智能体 {agent_name} 加载模型: {model_name}")
        return agent.load_model(model_name)

    def optimize_memory_all(self) -> bool:
        """优化所有智能体的内存使用"""
        self.logger.info("优化所有智能体的内存使用")
        success = True

        for agent in self._agents.values():
            try:
                if not agent.optimize_memory():
                    success = False
            except Exception as e:
                self.logger.error(f"优化智能体 {agent.name} 内存失败: {e}")
                success = False

        return success


# 全局管理器实例
_manager_instance = None


def get_agent_manager() -> AgentManager:
    """获取全局智能体管理器"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = AgentManager()
    return _manager_instance


if __name__ == "__main__":
    # 测试智能体基类
    class TestAgent1(Agent):
        name = "test_agent_1"
        description = "测试智能体 1"
        version = "1.0.0"
        agent_type = AgentType.GENERAL
        skills = ["github_opensource", "system_optimizer"]
        abilities = {"intelligence": 80, "speed": 70}

        def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
            task_type = task.get("task_type")
            return {
                "success": True,
                "result": f"{self.name} 完成了 {task_type} 任务",
                "execution_time": random.uniform(5, 15)
            }

    class TestAgent2(Agent):
        name = "test_agent_2"
        description = "测试智能体 2"
        version = "1.0.0"
        agent_type = AgentType.SPECIALIZED
        skills = ["github_api_manager"]
        abilities = {"intelligence": 90, "speed": 60}

        def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
            task_type = task.get("task_type")
            return {
                "success": True,
                "result": f"{self.name} 完成了 {task_type} 任务",
                "execution_time": random.uniform(8, 20)
            }

    # 测试管理器
    manager = AgentManager()
    agent1 = TestAgent1()
    agent2 = TestAgent2()

    if manager.register(agent1) and manager.register(agent2):
        print("\n智能体列表:")
        for info in manager.list_agents():
            print(f"  - {info.name}: {info.description} (等级: {info.level}, 状态: {info.status.value})")

        print("\n开始竞争:")
        result = manager.start_competition(rounds=2)
        print(f"竞争结果: {result['success']}")

        print("\n排名:")
        for i, rank in enumerate(result['rankings'], 1):
            print(f"  {i}. {rank['name']} - 胜率: {rank['win_rate']:.2f}%, 等级: {rank['level']}")

        print("\n进化历史:")
        for evolution in manager.get_evolution_history():
            print(f"  {evolution['winner']} 融合了 {evolution['loser']}")

    manager.shutdown_all()
    print("\n智能体基类测试完成")
