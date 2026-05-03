#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI协作系统 - 多AI模型协同工作
支持: 独立运行、多模型协作、智能路由
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

sys.path.insert(0, r"\python\core")
sys.path.insert(0, r"\python\tools")
try:
    from ai_adapter import AIClientFactory, ChatRequest, Message, UnifiedAI
except ImportError:
    UnifiedAI = None
try:
    from ai_config import get_config
except ImportError:
    get_config = None


class CollaborationMode(Enum):
    """协作模式"""

    SINGLE = "single"  # 单一模型
    PARALLEL = "parallel"  # 并行执行（多个模型同时）
    SEQUENTIAL = "sequential"  # 串行执行（模型链）
    DEBATE = "debate"  # 辩论模式
    VOTE = "vote"  # 投票模式
    CASCADE = "cascade"  # 级联模式（一个模型的输出作为下一个的输入）
    SPECIALIST = "specialist"  # 专家模式（不同模型处理不同部分）


@dataclass
class AITask:
    """AI任务"""

    id: str
    prompt: str
    provider: str = None
    model: str = None
    context: Dict = field(default_factory=dict)
    priority: int = 0
    depends_on: List[str] = field(default_factory=list)
    result: str = ""
    status: str = "pending"  # pending, running, completed, failed
    execution_time: float = 0.0


@dataclass
class CollaborationResult:
    """协作结果"""

    final_output: str
    individual_results: Dict[str, str]
    execution_plan: Dict
    total_time: float
    consensus_score: float = 0.0


class AICollaborator:
    """
    AI协作器 - 协调多个AI模型共同工作

    用法:
        # 独立模式（单一模型）
        collab = AICollaborator()
        result = collab.run("写快速排序")

        # 并行模式（多个模型同时回答）
        collab = AICollaborator(mode="parallel", providers=["openai", "claude", "stepfun"])
        result = collab.run("分析这个代码")

        # 级联模式（模型链）
        collab = AICollaborator(mode="cascade")
        collab.add_step("openai", "生成代码")
        collab.add_step("claude", "审查代码")
        result = collab.run("写Python爬虫")

        # 专家模式（不同模型处理不同部分）
        collab = AICollaborator(mode="specialist")
        collab.assign("openai", "架构设计")
        collab.assign("claude", "代码实现")
        collab.assign("stepfun", "文档生成")
        result = collab.run("开发一个Web应用")
    """

    def __init__(self, mode: CollaborationMode = None, providers: List[str] = None):
        """
        初始化协作器

        Args:
            mode: 协作模式
            providers: 使用的AI提供商列表
        """
        self.mode = mode or CollaborationMode.SINGLE
        self.providers = providers or [get_config().default_provider]
        self.tasks: List[AITask] = []
        self.clients: Dict[str, UnifiedAI] = {}
        self._init_clients()

    def _init_clients(self):
        """初始化AI客户端"""
        for provider in self.providers:
            if provider not in self.clients:
                try:
                    self.clients[provider] = UnifiedAI(provider=provider)
                except Exception as e:
                    print(f"[警告] 无法初始化 {provider}: {e}")

    def add_provider(self, provider: str, model: str = None):
        """添加AI提供商"""
        if provider not in self.providers:
            self.providers.append(provider)
        if provider not in self.clients:
            self.clients[provider] = UnifiedAI(provider=provider, model=model)

    def remove_provider(self, provider: str):
        """移除AI提供商"""
        if provider in self.providers:
            self.providers.remove(provider)
        if provider in self.clients:
            del self.clients[provider]

    def run(self, prompt: str, **kwargs) -> Union[str, CollaborationResult]:
        """
        执行任务

        Args:
            prompt: 任务描述
            **kwargs: 额外参数

        Returns:
            单一模式下返回字符串，协作模式下返回CollaborationResult
        """
        start_time = time.time()

        if self.mode == CollaborationMode.SINGLE:
            return self._run_single(prompt, **kwargs)
        elif self.mode == CollaborationMode.PARALLEL:
            return self._run_parallel(prompt, **kwargs)
        elif self.mode == CollaborationMode.SEQUENTIAL:
            return self._run_sequential(prompt, **kwargs)
        elif self.mode == CollaborationMode.DEBATE:
            return self._run_debate(prompt, **kwargs)
        elif self.mode == CollaborationMode.VOTE:
            return self._run_vote(prompt, **kwargs)
        elif self.mode == CollaborationMode.CASCADE:
            return self._run_cascade(prompt, **kwargs)
        elif self.mode == CollaborationMode.SPECIALIST:
            return self._run_specialist(prompt, **kwargs)
        else:
            return self._run_single(prompt, **kwargs)

    def _run_single(self, prompt: str, provider: str = None, **kwargs) -> str:
        """单一模式"""
        provider = provider or self.providers[0]
        if provider not in self.clients:
            raise ValueError(f"未初始化的提供商: {provider}")

        return self.clients[provider].chat(prompt, **kwargs)

    def _run_parallel(self, prompt: str, **kwargs) -> CollaborationResult:
        """并行模式 - 多个模型同时回答"""
        results = {}
        start_time = time.time()

        print(f"🔄 并行模式: 使用 {len(self.providers)} 个模型")

        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = {}
            for provider in self.providers:
                if provider in self.clients:
                    future = executor.submit(self._execute_with_time, provider, prompt, **kwargs)
                    futures[future] = provider

            for future in as_completed(futures):
                provider = futures[future]
                try:
                    result, exec_time = future.result()
                    results[provider] = result
                    print(f"  ✅ {provider}: {exec_time:.2f}s")
                except Exception as e:
                    results[provider] = f"[错误] {e}"
                    print(f"  ❌ {provider}: {e}")

        # 综合结果
        total_time = time.time() - start_time
        final_output = self._synthesize_results(results, prompt)

        return CollaborationResult(
            final_output=final_output,
            individual_results=results,
            execution_plan={"mode": "parallel", "providers": self.providers},
            total_time=total_time,
        )

    def _run_sequential(self, prompt: str, steps: List[Dict] = None, **kwargs) -> CollaborationResult:
        """串行模式 - 模型链"""
        results = {}
        start_time = time.time()
        current_input = prompt

        steps = steps or [{"provider": p, "task": "process"} for p in self.providers]

        print(f"🔄 串行模式: {len(steps)} 个步骤")

        for i, step in enumerate(steps, 1):
            provider = step["provider"]
            task_desc = step.get("task", "process")

            print(f"  Step {i}/{len(steps)}: {provider} - {task_desc}")

            if provider not in self.clients:
                results[f"step_{i}"] = f"[错误] 未初始化: {provider}"
                continue

            try:
                step_start = time.time()
                result = self.clients[provider].chat(current_input, **kwargs)
                exec_time = time.time() - step_start

                results[f"step_{i}_{provider}"] = result
                current_input = result  # 输出作为下一步输入

                print(f"    ✅ 完成 ({exec_time:.2f}s)")
            except Exception as e:
                results[f"step_{i}"] = f"[错误] {e}"
                print(f"    ❌ 失败: {e}")

        total_time = time.time() - start_time

        return CollaborationResult(
            final_output=current_input,
            individual_results=results,
            execution_plan={"mode": "sequential", "steps": steps},
            total_time=total_time,
        )

    def _run_debate(self, prompt: str, rounds: int = 2, **kwargs) -> CollaborationResult:
        """辩论模式 - 多个模型互相讨论"""
        results = {}
        start_time = time.time()

        print(f"🔄 辩论模式: {len(self.providers)} 个模型, {rounds} 轮")

        # 第一轮：各自发表观点
        context = f"主题: {prompt}\n\n请发表你的观点。"
        round_results = {}

        for provider in self.providers:
            if provider in self.clients:
                result = self.clients[provider].chat(context, **kwargs)
                round_results[provider] = result
                results[f"round_1_{provider}"] = result

        # 后续轮次：互相评论
        for round_num in range(2, rounds + 1):
            print(f"  第 {round_num} 轮辩论...")
            new_results = {}

            for provider in self.providers:
                if provider not in self.clients:
                    continue

                # 构建辩论上下文
                debate_context = f"主题: {prompt}\n\n"
                debate_context += "其他模型的观点:\n"
                for other_provider, other_result in round_results.items():
                    if other_provider != provider:
                        debate_context += f"\n[{other_provider}]:\n{other_result[:500]}...\n"

                debate_context += f"\n请基于以上观点，给出你的反驳或补充。"

                result = self.clients[provider].chat(debate_context, **kwargs)
                new_results[provider] = result
                results[f"round_{round_num}_{provider}"] = result

            round_results = new_results

        # 综合结论
        final_context = f"主题: {prompt}\n\n基于以上辩论，请给出最终结论。"
        final_results = {}
        for provider in self.providers:
            if provider in self.clients:
                final_results[provider] = self.clients[provider].chat(final_context, **kwargs)

        # 选择最全面的结论
        final_output = self._select_best_result(final_results, prompt)

        total_time = time.time() - start_time

        return CollaborationResult(
            final_output=final_output,
            individual_results=results,
            execution_plan={"mode": "debate", "rounds": rounds, "providers": self.providers},
            total_time=total_time,
        )

    def _run_vote(self, prompt: str, **kwargs) -> CollaborationResult:
        """投票模式 - 多个模型投票选择最佳答案"""
        results = {}
        start_time = time.time()

        print(f"🔄 投票模式: {len(self.providers)} 个模型")

        # 第一步：各自生成答案
        answers = {}
        for provider in self.providers:
            if provider in self.clients:
                answer = self.clients[provider].chat(prompt, **kwargs)
                answers[provider] = answer
                results[f"answer_{provider}"] = answer

        # 第二步：互相评估
        votes = {p: 0 for p in answers.keys()}

        for voter in self.providers:
            if voter not in self.clients:
                continue

            vote_context = f"任务: {prompt}\n\n以下是各模型的答案:\n\n"
            for provider, answer in answers.items():
                vote_context += f"[{provider}]:\n{answer[:1000]}...\n\n"

            vote_context += "请评估以上答案，选择最好的一个，回复格式: 最佳: [提供商名称]"

            vote_result = self.clients[voter].chat(vote_context, **kwargs)

            # 解析投票
            for provider in answers.keys():
                if provider.lower() in vote_result.lower():
                    votes[provider] += 1
                    break

        # 选择得票最高的
        winner = max(votes, key=votes.get)
        final_output = answers[winner]

        print(f"  🏆 获胜者: {winner} ({votes[winner]} 票)")

        total_time = time.time() - start_time
        consensus = votes[winner] / len(self.providers) if self.providers else 0

        return CollaborationResult(
            final_output=final_output,
            individual_results={**results, "votes": votes},
            execution_plan={"mode": "vote", "providers": self.providers, "winner": winner},
            total_time=total_time,
            consensus_score=consensus,
        )

    def _run_cascade(self, prompt: str, stages: List[Dict] = None, **kwargs) -> CollaborationResult:
        """级联模式 - 一个模型的输出作为下一个的输入"""
        results = {}
        start_time = time.time()

        stages = stages or [
            {"provider": self.providers[0], "instruction": "生成初始方案"},
            {
                "provider": self.providers[1] if len(self.providers) > 1 else self.providers[0],
                "instruction": "优化和完善",
            },
            {
                "provider": self.providers[2] if len(self.providers) > 2 else self.providers[0],
                "instruction": "最终审查",
            },
        ]

        print(f"🔄 级联模式: {len(stages)} 个阶段")

        current_content = prompt
        for i, stage in enumerate(stages, 1):
            provider = stage["provider"]
            instruction = stage["instruction"]

            print(f"  阶段 {i}/{len(stages)}: {provider} - {instruction}")

            if provider not in self.clients:
                results[f"stage_{i}"] = f"[错误] 未初始化: {provider}"
                continue

            stage_prompt = f"{instruction}\n\n输入内容:\n{current_content}"

            try:
                result = self.clients[provider].chat(stage_prompt, **kwargs)
                results[f"stage_{i}_{provider}"] = result
                current_content = result
                print(f"    ✅ 完成")
            except Exception as e:
                results[f"stage_{i}"] = f"[错误] {e}"
                print(f"    ❌ 失败: {e}")

        total_time = time.time() - start_time

        return CollaborationResult(
            final_output=current_content,
            individual_results=results,
            execution_plan={"mode": "cascade", "stages": stages},
            total_time=total_time,
        )

    def _run_specialist(self, prompt: str, assignments: Dict[str, str] = None, **kwargs) -> CollaborationResult:
        """专家模式 - 不同模型处理不同部分"""
        results = {}
        start_time = time.time()

        # 默认分工
        if not assignments:
            assignments = self._auto_assign_tasks(prompt)

        print(f"🔄 专家模式: {len(assignments)} 个专家")

        # 并行执行各专家任务
        with ThreadPoolExecutor(max_workers=len(assignments)) as executor:
            futures = {}
            for provider, task in assignments.items():
                if provider in self.clients:
                    future = executor.submit(self._execute_specialist_task, provider, prompt, task, **kwargs)
                    futures[future] = provider

            for future in as_completed(futures):
                provider = futures[future]
                try:
                    result = future.result()
                    results[provider] = result
                    print(f"  ✅ {provider}: 完成")
                except Exception as e:
                    results[provider] = f"[错误] {e}"
                    print(f"  ❌ {provider}: {e}")

        # 综合所有专家的结果
        final_output = self._combine_specialist_results(results, prompt)

        total_time = time.time() - start_time

        return CollaborationResult(
            final_output=final_output,
            individual_results=results,
            execution_plan={"mode": "specialist", "assignments": assignments},
            total_time=total_time,
        )

    def _auto_assign_tasks(self, prompt: str) -> Dict[str, str]:
        """自动分配任务"""
        # 根据提示词内容自动判断需要的专家
        prompt_lower = prompt.lower()

        assignments = {}

        # 代码相关
        if any(kw in prompt_lower for kw in ["代码", "程序", "开发", "写", "实现", "python", "javascript"]):
            if "openai" in self.providers:
                assignments["openai"] = "代码生成和架构设计"
            if "claude" in self.providers:
                assignments["claude"] = "代码审查和优化"

        # 创意相关
        if any(kw in prompt_lower for kw in ["创意", "设计", "想法", "文案", "写作"]):
            if "claude" in self.providers:
                assignments["claude"] = "创意生成"
            if "gemini" in self.providers:
                assignments["gemini"] = "内容扩展"

        # 分析相关
        if any(kw in prompt_lower for kw in ["分析", "评估", "比较", "研究"]):
            if "openai" in self.providers:
                assignments["openai"] = "深度分析"
            if "deepseek" in self.providers:
                assignments["deepseek"] = "逻辑推理"

        # 中文内容
        if any(kw in prompt_lower for kw in ["中文", "翻译", "中文文档"]):
            if "qwen" in self.providers:
                assignments["qwen"] = "中文内容生成"
            if "stepfun" in self.providers:
                assignments["stepfun"] = "中文优化"

        # 如果没有匹配到，平均分配
        if not assignments:
            tasks = ["主要实现", "辅助优化", "质量检查"]
            for i, provider in enumerate(self.providers):
                if i < len(tasks):
                    assignments[provider] = tasks[i]

        return assignments

    def _execute_with_time(self, provider: str, prompt: str, **kwargs) -> Tuple[str, float]:
        """执行并记录时间"""
        start = time.time()
        result = self.clients[provider].chat(prompt, **kwargs)
        exec_time = time.time() - start
        return result, exec_time

    def _execute_specialist_task(self, provider: str, prompt: str, task: str, **kwargs) -> str:
        """执行专家任务"""
        specialist_prompt = f"你作为{task}专家，请处理以下任务:\n\n{prompt}"
        return self.clients[provider].chat(specialist_prompt, **kwargs)

    def _synthesize_results(self, results: Dict[str, str], original_prompt: str) -> str:
        """综合多个结果"""
        if len(results) == 1:
            return list(results.values())[0]

        # 使用第一个可用的模型来综合
        synthesizer = list(self.clients.keys())[0]

        synthesis_prompt = f"任务: {original_prompt}\n\n以下是多个AI模型的回答:\n\n"
        for provider, result in results.items():
            synthesis_prompt += f"[{provider}]:\n{result}\n\n"

        synthesis_prompt += "请综合以上回答，给出一个最全面、最准确的最终答案。"

        try:
            return self.clients[synthesizer].chat(synthesis_prompt)
        except:
            # 如果综合失败，返回最长的回答（通常最详细）
            return max(results.values(), key=len)

    def _select_best_result(self, results: Dict[str, str], prompt: str) -> str:
        """选择最佳结果"""
        if not results:
            return ""

        if len(results) == 1:
            return list(results.values())[0]

        # 启发式选择：选择最长的（通常更详细）
        # 或者可以选择第一个成功的
        return max(results.values(), key=len)

    def _combine_specialist_results(self, results: Dict[str, str], prompt: str) -> str:
        """组合专家结果"""
        if len(results) == 1:
            return list(results.values())[0]

        # 使用一个模型来组合
        composer = list(self.clients.keys())[0]

        combine_prompt = f"项目: {prompt}\n\n以下是各专家的工作成果:\n\n"
        for provider, result in results.items():
            combine_prompt += f"[{provider}]:\n{result}\n\n"

        combine_prompt += "请将以上各专家的工作整合成一个完整的、连贯的最终交付物。"

        try:
            return self.clients[composer].chat(combine_prompt)
        except:
            # 如果组合失败，简单拼接
            return "\n\n".join([f"=== {k} ===\n{v}" for k, v in results.items()])


class SmartRouter:
    """
    智能路由器 - 根据任务类型自动选择最佳模型或组合

    用法:
        router = SmartRouter()
        result = router.route("写Python代码")

        # 或获取推荐
        recommendation = router.recommend("翻译文档")
    """

    # 任务类型到最佳模型的映射
    TASK_MODEL_MAPPING = {
        "coding": {
            "primary": ["openai", "claude", "deepseek"],
            "secondary": ["stepfun", "qwen"],
            "mode": CollaborationMode.SPECIALIST,
        },
        "writing": {
            "primary": ["claude", "openai"],
            "secondary": ["gemini", "qwen"],
            "mode": CollaborationMode.PARALLEL,
        },
        "analysis": {
            "primary": ["openai", "claude"],
            "secondary": ["deepseek", "gemini"],
            "mode": CollaborationMode.DEBATE,
        },
        "translation": {
            "primary": ["qwen", "stepfun", "doubao"],
            "secondary": ["openai", "claude"],
            "mode": CollaborationMode.VOTE,
        },
        "creative": {
            "primary": ["claude", "gemini"],
            "secondary": ["openai", "qwen"],
            "mode": CollaborationMode.PARALLEL,
        },
        "math": {"primary": ["openai", "deepseek"], "secondary": ["claude", "gemini"], "mode": CollaborationMode.VOTE},
        "general": {"primary": ["stepfun", "openai"], "secondary": ["claude"], "mode": CollaborationMode.SINGLE},
    }

    def __init__(self):
        self.config = get_config()
        self.available_providers = self.config.get_available_providers()

    def detect_task_type(self, prompt: str) -> str:
        """检测任务类型"""
        prompt_lower = prompt.lower()

        # 代码相关
        if any(
            kw in prompt_lower
            for kw in [
                "代码",
                "程序",
                "编程",
                "写",
                "实现",
                "开发",
                "函数",
                "类",
                "python",
                "javascript",
                "java",
                "cpp",
                "c++",
                "go",
                "rust",
                "code",
                "program",
                "function",
                "class",
                "algorithm",
            ]
        ):
            return "coding"

        # 写作相关
        if any(
            kw in prompt_lower
            for kw in [
                "写",
                "文章",
                "写作",
                "文案",
                "内容",
                "故事",
                "邮件",
                "write",
                "essay",
                "article",
                "content",
                "story",
            ]
        ):
            return "writing"

        # 分析相关
        if any(
            kw in prompt_lower
            for kw in [
                "分析",
                "评估",
                "比较",
                "研究",
                "检查",
                "审查",
                "analyze",
                "analysis",
                "evaluate",
                "compare",
                "review",
            ]
        ):
            return "analysis"

        # 翻译相关
        if any(kw in prompt_lower for kw in ["翻译", "translate", "translation", "中英", "英中", "英文", "中文"]):
            return "translation"

        # 创意相关
        if any(
            kw in prompt_lower
            for kw in ["创意", "想法", "设计", "构思", "头脑风暴", "creative", "idea", "design", "brainstorm"]
        ):
            return "creative"

        # 数学相关
        if any(kw in prompt_lower for kw in ["数学", "计算", "求解", "方程", "math", "calculate", "solve"]):
            return "math"

        return "general"

    def recommend(self, prompt: str) -> Dict:
        """推荐最佳配置"""
        task_type = self.detect_task_type(prompt)
        mapping = self.TASK_MODEL_MAPPING.get(task_type, self.TASK_MODEL_MAPPING["general"])

        # 筛选可用的模型
        available_primary = [p for p in mapping["primary"] if p in self.available_providers]
        available_secondary = [p for p in mapping["secondary"] if p in self.available_providers]

        # 如果没有可用的，使用默认
        if not available_primary:
            available_primary = [self.config.default_provider]

        return {
            "task_type": task_type,
            "recommended_providers": available_primary + available_secondary,
            "primary": available_primary,
            "secondary": available_secondary,
            "recommended_mode": mapping["mode"],
            "confidence": "high" if len(available_primary) > 0 else "low",
        }

    def route(self, prompt: str, **kwargs) -> Union[str, CollaborationResult]:
        """智能路由任务"""
        recommendation = self.recommend(prompt)

        print(f"🎯 任务类型: {recommendation['task_type']}")
        print(f"🤖 推荐模型: {', '.join(recommendation['recommended_providers'])}")
        print(f"🔄 协作模式: {recommendation['recommended_mode'].value}")

        # 创建协作器
        collab = AICollaborator(
            mode=recommendation["recommended_mode"], providers=recommendation["recommended_providers"]
        )

        return collab.run(prompt, **kwargs)


# ============ 便捷函数 ============


def collaborate(prompt: str, providers: List[str] = None, mode: str = "parallel", **kwargs) -> CollaborationResult:
    """
    多模型协作

    Args:
        prompt: 任务描述
        providers: 使用的模型列表，如 ["openai", "claude", "stepfun"]
        mode: 协作模式 (single/parallel/sequential/debate/vote/cascade/specialist)
        **kwargs: 其他参数

    Returns:
        CollaborationResult

    示例:
        result = collaborate("写快速排序", ["openai", "claude"], "vote")
        print(result.final_output)
    """
    mode_enum = CollaborationMode(mode)
    collab = AICollaborator(mode=mode_enum, providers=providers)
    return collab.run(prompt, **kwargs)


def smart_route(prompt: str, **kwargs) -> Union[str, CollaborationResult]:
    """
    智能路由 - 自动选择最佳模型或组合

    示例:
        result = smart_route("写Python爬虫")
        # 自动检测为coding任务，可能使用openai+claude的专家模式
    """
    router = SmartRouter()
    return router.route(prompt, **kwargs)


def debate(prompt: str, providers: List[str] = None, rounds: int = 2, **kwargs) -> CollaborationResult:
    """
    辩论模式 - 多个模型讨论后给出结论

    示例:
        result = debate("AI是否会取代程序员", ["openai", "claude", "gemini"], rounds=3)
    """
    providers = providers or ["openai", "claude"]
    collab = AICollaborator(mode=CollaborationMode.DEBATE, providers=providers)
    return collab.run(prompt, rounds=rounds, **kwargs)


def vote(prompt: str, providers: List[str] = None, **kwargs) -> CollaborationResult:
    """
    投票模式 - 多个模型投票选择最佳答案

    示例:
        result = vote("哪个Python框架最好", ["openai", "claude", "deepseek"])
        print(f"获胜者: {result.execution_plan.get('winner')}")
    """
    providers = providers or ["openai", "claude", "stepfun"]
    collab = AICollaborator(mode=CollaborationMode.VOTE, providers=providers)
    return collab.run(prompt, **kwargs)


def cascade(prompt: str, stages: List[Dict], **kwargs) -> CollaborationResult:
    """
    级联模式 - 多阶段处理

    示例:
        stages = [
            {"provider": "openai", "instruction": "生成代码"},
            {"provider": "claude", "instruction": "审查和优化"},
            {"provider": "stepfun", "instruction": "生成中文文档"}
        ]
        result = cascade("写Web应用", stages)
    """
    providers = list(set([s["provider"] for s in stages]))
    collab = AICollaborator(mode=CollaborationMode.CASCADE, providers=providers)
    return collab.run(prompt, stages=stages, **kwargs)


def specialist(prompt: str, assignments: Dict[str, str] = None, **kwargs) -> CollaborationResult:
    """
    专家模式 - 不同模型处理不同部分

    示例:
        assignments = {
            "openai": "架构设计",
            "claude": "代码实现",
            "stepfun": "文档编写"
        }
        result = specialist("开发Web应用", assignments)
    """
    providers = list(assignments.keys()) if assignments else None
    collab = AICollaborator(mode=CollaborationMode.SPECIALIST, providers=providers)
    return collab.run(prompt, assignments=assignments, **kwargs)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("AI协作系统测试")
    print("=" * 60)

    # 测试智能路由
    print("\n1. 测试智能路由")
    print("-" * 60)

    test_prompts = ["写Python快速排序代码", "翻译这段英文到中文", "分析AI对未来工作的影响", "创意写作：未来的城市"]

    router = SmartRouter()
    for prompt in test_prompts:
        print(f"\n提示: {prompt}")
        rec = router.recommend(prompt)
        print(f"  类型: {rec['task_type']}")
        print(f"  推荐: {', '.join(rec['recommended_providers'])}")
        print(f"  模式: {rec['recommended_mode'].value}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
