#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 异步技能基类

功能:
- 异步技能执行
- 并发执行支持
- 异步事件总线
- 性能优化
"""

import asyncio
import functools
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Coroutine, Union

from skills.base import Skill, handle_errors


class AsyncSkill(Skill):
    """异步技能基类"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._async_initialized = False
        self._lock = asyncio.Lock()

    @abstractmethod
    async def execute_async(self, params: Dict) -> Dict:
        """异步执行技能

        Args:
            params: 执行参数

        Returns:
            执行结果字典
        """
        pass

    def execute(self, params: Dict) -> Dict:
        """同步执行接口（自动转换为异步）"""
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 运行异步方法
            return loop.run_until_complete(self.execute_async(params))
        except Exception as e:
            return {"success": False, "error": f"异步执行失败: {str(e)}"}

    async def initialize_async(self) -> bool:
        """异步初始化"""
        async with self._lock:
            if not self._async_initialized:
                self._async_initialized = True
            return True


class AsyncSkillExecutor:
    """异步技能执行器"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results: Dict[str, Any] = {}
        self._execution_times: Dict[str, float] = {}

    async def execute_single(
        self, skill: AsyncSkill, params: Dict, task_id: str = None
    ) -> Dict:
        """执行单个技能"""
        task_id = task_id or f"task_{id(skill)}_{time.time()}"

        async with self.semaphore:
            start_time = time.time()
            try:
                result = await skill.execute_async(params)
                self.results[task_id] = result
                return result
            except Exception as e:
                error_result = {"success": False, "error": str(e)}
                self.results[task_id] = error_result
                return error_result
            finally:
                self._execution_times[task_id] = time.time() - start_time

    async def execute_batch(
        self, tasks: List[tuple], return_exceptions: bool = True
    ) -> List[Dict]:
        """批量执行技能

        Args:
            tasks: 任务列表，每个元素为 (skill, params, task_id)
            return_exceptions: 是否返回异常结果

        Returns:
            执行结果列表
        """
        coroutines = [
            self.execute_single(skill, params, task_id)
            for skill, params, task_id in tasks
        ]

        return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)

    async def execute_with_timeout(
        self, skill: AsyncSkill, params: Dict, timeout: float = 30.0
    ) -> Dict:
        """带超时的技能执行"""
        try:
            return await asyncio.wait_for(
                skill.execute_async(params), timeout=timeout
            )
        except asyncio.TimeoutError:
            return {"success": False, "error": f"执行超时（{timeout}秒）"}

    def get_execution_time(self, task_id: str) -> Optional[float]:
        """获取任务执行时间"""
        return self._execution_times.get(task_id)

    def get_all_execution_times(self) -> Dict[str, float]:
        """获取所有任务执行时间"""
        return self._execution_times.copy()


class AsyncEventBus:
    """异步事件总线"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: Any):
        """发布事件"""
        await self._event_queue.put((event_type, data))

    async def start(self):
        """启动事件处理"""
        self._running = True
        while self._running:
            try:
                event_type, data = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )

                # 分发事件
                if event_type in self._subscribers:
                    for callback in self._subscribers[event_type]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(data))
                            else:
                                callback(data)
                        except Exception as e:
                            print(f"事件处理错误: {e}")
            except asyncio.TimeoutError:
                continue

    def stop(self):
        """停止事件处理"""
        self._running = False


def async_handle_errors(func: Callable) -> Callable:
    """异步错误处理装饰器"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = f"执行错误: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "error": error_msg}

    return wrapper


# 示例异步技能
class AsyncExampleSkill(AsyncSkill):
    """示例异步技能"""

    name = "async_example"
    description = "示例异步技能"
    version = "1.0.0"

    async def execute_async(self, params: Dict) -> Dict:
        """异步执行"""
        await asyncio.sleep(0.1)  # 模拟异步操作
        return {"success": True, "data": "异步执行成功"}


# 全局异步执行器实例
_async_executor: Optional[AsyncSkillExecutor] = None


def get_async_executor(max_concurrent: int = 10) -> AsyncSkillExecutor:
    """获取异步执行器实例"""
    global _async_executor
    if _async_executor is None:
        _async_executor = AsyncSkillExecutor(max_concurrent=max_concurrent)
    return _async_executor


async def run_skills_concurrently(
    skills_with_params: List[tuple], max_concurrent: int = 10
) -> List[Dict]:
    """并发执行多个技能

    Args:
        skills_with_params: 技能列表，每个元素为 (skill, params)
        max_concurrent: 最大并发数

    Returns:
        执行结果列表
    """
    executor = get_async_executor(max_concurrent)

    # 添加任务ID
    tasks = [
        (skill, params, f"task_{i}")
        for i, (skill, params) in enumerate(skills_with_params)
    ]

    return await executor.execute_batch(tasks)


# 使用示例
if __name__ == "__main__":
    async def main():
        # 创建异步技能
        skill1 = AsyncExampleSkill()
        skill2 = AsyncExampleSkill()

        # 并发执行
        results = await run_skills_concurrently([
            (skill1, {"action": "test1"}),
            (skill2, {"action": "test2"}),
        ])

        print("执行结果:")
        for i, result in enumerate(results):
            print(f"  任务 {i}: {result}")

    # 运行示例
    asyncio.run(main())
