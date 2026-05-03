#!/usr/bin/env python3
"""
智能路由系统 - 本地/云端自动选择
自动优化token使用，一句话完成任务
"""

import hashlib
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional


class ComputeType(Enum):
    LOCAL = "local"  # 本地计算
    CLOUD = "cloud"  # 云端API
    HYBRID = "hybrid"  # 混合模式


class TaskComplexity(Enum):
    SIMPLE = 1  # 简单任务 (<100 tokens)
    NORMAL = 2  # 常规任务 (100-1000 tokens)
    COMPLEX = 3  # 复杂任务 (>1000 tokens)


@dataclass
class Task:
    """任务定义"""

    prompt: str
    context: Optional[str] = None
    files: Optional[List[str]] = None
    priority: str = "normal"  # low/normal/high


@dataclass
class RouteResult:
    """路由结果"""

    compute_type: ComputeType
    model: str
    max_tokens: int
    temperature: float
    use_cache: bool
    estimated_cost: float


class SmartRouter:
    """智能路由器 - 自动选择最优执行路径"""

    def __init__(self):
        self.cache = {}
        self.local_models = self._init_local_models()
        self.cloud_models = {
            "step-1-8k": {"cost": 0.001, "speed": "fast"},
            "step-1-32k": {"cost": 0.003, "speed": "normal"},
            "claude-3.5": {"cost": 0.005, "speed": "normal"},
        }

    def _init_local_models(self) -> Dict:
        """初始化本地模型"""
        return {
            "ollama": {"available": False, "path": None},
            "llamacpp": {"available": False, "path": None},
        }

    def analyze_complexity(self, task: Task) -> TaskComplexity:
        """分析任务复杂度"""
        text = task.prompt + (task.context or "")
        length = len(text)

        # 简单规则
        if length < 100 and not task.files:
            return TaskComplexity.SIMPLE
        elif length < 1000:
            return TaskComplexity.NORMAL
        else:
            return TaskComplexity.COMPLEX

    def route(self, task: Task) -> RouteResult:
        """智能路由 - 自动选择最优方案"""
        complexity = self.analyze_complexity(task)

        # 检查缓存
        cache_key = self._get_cache_key(task)
        if cache_key in self.cache:
            return RouteResult(
                compute_type=ComputeType.LOCAL,
                model="cache",
                max_tokens=0,
                temperature=0,
                use_cache=True,
                estimated_cost=0,
            )

        # 路由决策
        if complexity == TaskComplexity.SIMPLE:
            # 简单任务优先本地
            if self._has_local_model():
                return self._local_route(task)
            else:
                return self._cloud_route(task, "step-1-8k")

        elif complexity == TaskComplexity.NORMAL:
            # 常规任务用云端小模型
            return self._cloud_route(task, "step-1-8k")

        else:  # COMPLEX
            # 复杂任务用云端大模型
            return self._cloud_route(task, "step-1-32k")

    def _has_local_model(self) -> bool:
        """检查是否有可用本地模型"""
        return any(m["available"] for m in self.local_models.values())

    def _local_route(self, task: Task) -> RouteResult:
        """本地路由"""
        return RouteResult(
            compute_type=ComputeType.LOCAL,
            model="ollama-7b",
            max_tokens=512,
            temperature=0.7,
            use_cache=False,
            estimated_cost=0,
        )

    def _cloud_route(self, task: Task, model: str) -> RouteResult:
        """云端路由 - 自动优化token"""
        # 智能截断上下文
        optimized_prompt = self._optimize_prompt(task.prompt, task.context)

        # 估算token
        est_tokens = len(optimized_prompt) // 4 + 500  # 粗略估算

        return RouteResult(
            compute_type=ComputeType.CLOUD,
            model=model,
            max_tokens=min(est_tokens, 4000),
            temperature=0.7 if task.priority == "normal" else 0.5,
            use_cache=False,
            estimated_cost=self.cloud_models.get(model, {}).get("cost", 0.001) * est_tokens / 1000,
        )

    def _optimize_prompt(self, prompt: str, context: Optional[str]) -> str:
        """优化prompt减少token"""
        # 1. 去除多余空格
        text = " ".join((prompt + " " + (context or "")).split())

        # 2. 截断过长内容
        if len(text) > 8000:
            text = text[:4000] + "\n...[内容截断]...\n" + text[-2000:]

        return text

    def _get_cache_key(self, task: Task) -> str:
        """生成缓存key"""
        content = task.prompt + str(task.context)
        return hashlib.sha256(content.encode()).hexdigest()

    def execute(self, task: Task, handler: Callable) -> str:
        """执行任务"""
        route = self.route(task)

        if route.use_cache:
            return self.cache[self._get_cache_key(task)]

        result = handler(task, route)

        # 缓存结果
        if route.compute_type == ComputeType.CLOUD:
            self.cache[self._get_cache_key(task)] = result

        return result


# 全局路由器
router = SmartRouter()


def do(prompt: str, **kwargs) -> str:
    """
    一句话执行任务
    自动路由到最优方案
    """
    task = Task(prompt=prompt, **kwargs)
    route = router.route(task)

    # 根据路由执行
    if route.compute_type == ComputeType.LOCAL:
        return _execute_local(task, route)
    else:
        return _execute_cloud(task, route)


def _execute_local(task: Task, route: RouteResult) -> str:
    """本地执行"""
    # 简化实现
    return f"[本地执行] {task.prompt[:50]}..."


def _execute_cloud(task: Task, route: RouteResult) -> str:
    """云端执行"""
    import sys

    sys.path.insert(0, r"\python\tools")
    try:
        from stepfun_client import StepFunClient
    except ImportError:
        StepFunClient = None

    client = StepFunClient()
    return client.chat(task.prompt, model=route.model, max_tokens=route.max_tokens, temperature=route.temperature)


# 快捷函数
def code(prompt: str) -> str:
    """写代码 - 一句话"""
    return do(f"写代码: {prompt}", priority="high")


def review(prompt: str) -> str:
    """代码审查 - 一句话"""
    return do(f"审查代码: {prompt}")


def design(prompt: str) -> str:
    """设计 - 一句话"""
    return do(f"设计: {prompt}")


def analyze(prompt: str) -> str:
    """分析 - 一句话"""
    return do(f"分析: {prompt}")


if __name__ == "__main__":
    # 测试
    print(do("你好"))
    print(code("快速排序"))
