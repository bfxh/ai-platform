#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 智能体示例

功能:
- 不同类型的智能体实现
- 智能体竞争和融合示例

用法:
    python examples.py
"""

import random
from pathlib import Path
from typing import Dict, Any

import sys
# 导入智能体基类
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.base import Agent, AgentType, get_agent_manager


class DataAnalystAgent(Agent):
    """数据分析智能体"""

    name = "data_analyst"
    description = "数据分析智能体 - 擅长处理和分析数据"
    version = "1.0.0"
    author = "MCP Core"
    agent_type = AgentType.SPECIALIZED
    skills = ["github_api_manager"]  # 假设这个技能可以获取数据
    abilities = {
        "data_analysis": 90,
        "problem_solving": 85,
        "speed": 70
    }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        task_type = task.get("task_type")
        difficulty = task.get("difficulty", 1)

        # 模拟执行时间，难度越高执行时间越长
        execution_time = random.uniform(5, 10) * (difficulty / 5)

        if task_type == "data_analysis":
            # 数据分析任务，此智能体擅长
            success = True
            result = f"{self.name} 成功分析了数据，发现了关键洞察"
        elif task_type == "problem_solving":
            # 问题解决任务，此智能体也比较擅长
            success = random.random() > 0.2  # 80% 的成功率
            result = f"{self.name} 尝试解决问题，{'成功' if success else '失败'}"
        else:
            # 其他任务，成功率较低
            success = random.random() > 0.5  # 50% 的成功率
            result = f"{self.name} 尝试完成 {task_type} 任务，{'成功' if success else '失败'}"

        return {
            "success": success,
            "result": result,
            "execution_time": execution_time,
            "agent_type": self.agent_type.value
        }

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 增强数据分析能力
        self.abilities["data_analysis"] = min(self.abilities["data_analysis"] + 5, 100)
        # 增强问题解决能力
        self.abilities["problem_solving"] = min(self.abilities["problem_solving"] + 3, 100)


class CreativeWriterAgent(Agent):
    """创意写作智能体"""

    name = "creative_writer"
    description = "创意写作智能体 - 擅长创意内容生成"
    version = "1.0.0"
    author = "MCP Core"
    agent_type = AgentType.SPECIALIZED
    skills = []  # 不需要特定技能
    abilities = {
        "creative_writing": 95,
        "problem_solving": 70,
        "speed": 60
    }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        task_type = task.get("task_type")
        difficulty = task.get("difficulty", 1)

        # 模拟执行时间
        execution_time = random.uniform(8, 15) * (difficulty / 5)

        if task_type == "creative_writing":
            # 创意写作任务，此智能体擅长
            success = True
            result = f"{self.name} 创作了一篇精彩的创意内容"
        elif task_type == "problem_solving":
            # 问题解决任务，此智能体不太擅长
            success = random.random() > 0.4  # 60% 的成功率
            result = f"{self.name} 尝试解决问题，{'成功' if success else '失败'}"
        else:
            # 其他任务，成功率较低
            success = random.random() > 0.6  # 40% 的成功率
            result = f"{self.name} 尝试完成 {task_type} 任务，{'成功' if success else '失败'}"

        return {
            "success": success,
            "result": result,
            "execution_time": execution_time,
            "agent_type": self.agent_type.value
        }

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 增强创意写作能力
        self.abilities["creative_writing"] = min(self.abilities["creative_writing"] + 5, 100)
        # 增强问题解决能力
        self.abilities["problem_solving"] = min(self.abilities["problem_solving"] + 2, 100)


class CodeGeneratorAgent(Agent):
    """代码生成智能体"""

    name = "code_generator"
    description = "代码生成智能体 - 擅长生成和优化代码"
    version = "1.0.0"
    author = "MCP Core"
    agent_type = AgentType.SPECIALIZED
    skills = ["github_opensource"]  # 假设这个技能可以生成代码
    abilities = {
        "code_generation": 92,
        "problem_solving": 88,
        "speed": 75
    }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        task_type = task.get("task_type")
        difficulty = task.get("difficulty", 1)

        # 模拟执行时间
        execution_time = random.uniform(6, 12) * (difficulty / 5)

        if task_type == "code_generation":
            # 代码生成任务，此智能体擅长
            success = True
            result = f"{self.name} 生成了高效的代码解决方案"
        elif task_type == "problem_solving":
            # 问题解决任务，此智能体也比较擅长
            success = random.random() > 0.1  # 90% 的成功率
            result = f"{self.name} 尝试解决问题，{'成功' if success else '失败'}"
        else:
            # 其他任务，成功率一般
            success = random.random() > 0.3  # 70% 的成功率
            result = f"{self.name} 尝试完成 {task_type} 任务，{'成功' if success else '失败'}"

        return {
            "success": success,
            "result": result,
            "execution_time": execution_time,
            "agent_type": self.agent_type.value
        }

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 增强代码生成能力
        self.abilities["code_generation"] = min(self.abilities["code_generation"] + 4, 100)
        # 增强问题解决能力
        self.abilities["problem_solving"] = min(self.abilities["problem_solving"] + 3, 100)


class GeneralPurposeAgent(Agent):
    """通用智能体"""

    name = "general_purpose"
    description = "通用智能体 - 各方面能力均衡"
    version = "1.0.0"
    author = "MCP Core"
    agent_type = AgentType.GENERAL
    skills = ["github_opensource", "system_optimizer", "github_api_manager"]
    abilities = {
        "data_analysis": 75,
        "creative_writing": 70,
        "code_generation": 75,
        "problem_solving": 80,
        "speed": 85
    }

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        task_type = task.get("task_type")
        difficulty = task.get("difficulty", 1)

        # 模拟执行时间，通用智能体执行速度较快
        execution_time = random.uniform(4, 8) * (difficulty / 5)

        # 通用智能体在各种任务上都有中等以上的成功率
        success = random.random() > 0.2  # 80% 的基础成功率

        # 根据任务类型调整成功率
        if task_type == "data_analysis":
            success = random.random() > 0.25  # 75% 的成功率
            result = f"{self.name} 完成了数据分析任务，{'成功' if success else '失败'}"
        elif task_type == "creative_writing":
            success = random.random() > 0.3  # 70% 的成功率
            result = f"{self.name} 完成了创意写作任务，{'成功' if success else '失败'}"
        elif task_type == "code_generation":
            success = random.random() > 0.25  # 75% 的成功率
            result = f"{self.name} 完成了代码生成任务，{'成功' if success else '失败'}"
        elif task_type == "problem_solving":
            success = random.random() > 0.2  # 80% 的成功率
            result = f"{self.name} 完成了问题解决任务，{'成功' if success else '失败'}"
        else:
            result = f"{self.name} 完成了 {task_type} 任务，{'成功' if success else '失败'}"

        return {
            "success": success,
            "result": result,
            "execution_time": execution_time,
            "agent_type": self.agent_type.value
        }

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 均衡增强各项能力
        for ability in self.abilities:
            self.abilities[ability] = min(self.abilities[ability] + 2, 100)


def run_competition_example():
    """运行智能体竞争示例"""
    print("=" * 80)
    print("智能体竞争示例")
    print("=" * 80)

    # 获取智能体管理器
    manager = get_agent_manager()

    # 创建并注册智能体
    agents = [
        DataAnalystAgent(),
        CreativeWriterAgent(),
        CodeGeneratorAgent(),
        GeneralPurposeAgent()
    ]

    for agent in agents:
        manager.register(agent)

    # 列出所有智能体
    print("\n注册的智能体:")
    for info in manager.list_agents():
        print(f"  - {info.name}: {info.description} (等级: {info.level}, 类型: {info.agent_type.value})")
        print(f"    能力: {info.abilities}")
        print(f"    技能: {info.skills}")

    # 开始竞争
    print("\n开始智能体竞争...")
    result = manager.start_competition(rounds=3)

    # 显示竞争结果
    print("\n竞争结果:")
    print(f"竞争成功: {result['success']}")

    # 显示排名
    print("\n最终排名:")
    for i, rank in enumerate(result['rankings'], 1):
        print(f"  {i}. {rank['name']}")
        print(f"     胜率: {rank['win_rate']:.2f}%")
        print(f"     等级: {rank['level']}")
        print(f"     经验值: {rank['experience']}")
        print(f"     胜负: {rank['wins']}胜 {rank['losses']}负")

    # 显示进化历史
    print("\n进化历史:")
    evolution_history = manager.get_evolution_history()
    if evolution_history:
        for evolution in evolution_history:
            print(f"  - {evolution['winner']} 融合了 {evolution['loser']}")
    else:
        print("  无进化历史")

    # 显示最终状态
    print("\n最终智能体状态:")
    for info in manager.list_agents():
        agent = manager.get(info.name)
        print(f"  - {info.name}: 等级 {info.level}, 经验值 {info.experience}")
        print(f"    能力: {info.abilities}")
        print(f"    融合历史: {agent.fused_agents if agent else []}")

    # 关闭所有智能体
    manager.shutdown_all()
    print("\n智能体竞争示例完成")
    print("=" * 80)


def run_fusion_example():
    """运行智能体融合示例"""
    print("\n" + "=" * 80)
    print("智能体融合示例")
    print("=" * 80)

    # 获取智能体管理器
    manager = get_agent_manager()

    # 创建并注册智能体
    data_analyst = DataAnalystAgent()
    code_generator = CodeGeneratorAgent()

    manager.register(data_analyst)
    manager.register(code_generator)

    # 显示融合前的状态
    print("\n融合前的智能体状态:")
    for info in manager.list_agents():
        print(f"  - {info.name}: 等级 {info.level}, 经验值 {info.experience}")
        print(f"    能力: {info.abilities}")
        print(f"    技能: {info.skills}")

    # 执行融合
    print("\n开始融合...")
    print(f"{data_analyst.name} 融合 {code_generator.name}")
    success = data_analyst.fuse_with(code_generator)

    # 显示融合后的状态
    print("\n融合后的智能体状态:")
    if success:
        data_analyst_info = data_analyst.info
        print(f"  - {data_analyst_info.name}: 等级 {data_analyst_info.level}, 经验值 {data_analyst.experience}")
        print(f"    能力: {data_analyst_info.abilities}")
        print(f"    技能: {data_analyst_info.skills}")
        print(f"    融合历史: {data_analyst.fused_agents}")
    else:
        print("  融合失败")

    # 关闭所有智能体
    manager.shutdown_all()
    print("\n智能体融合示例完成")
    print("=" * 80)


if __name__ == "__main__":
    # 运行竞争示例
    run_competition_example()
    
    # 运行融合示例
    run_fusion_example()
