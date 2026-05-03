#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级工作流系统 - 复杂任务自动化
支持: 条件分支、循环、并行、错误处理、状态管理
"""

import asyncio
import json
import os
import re
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

sys.path.insert(0, r"\python\core")
sys.path.insert(0, r"\python\tools")
try:
    from ai_adapter import UnifiedAI
except ImportError:
    UnifiedAI = None
from ai_agent import Agent

try:
    from mcp_extended import MCPExtended
except ImportError:
    MCPExtended = None


class StepStatus(Enum):
    """步骤状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """步骤类型"""

    ACTION = "action"  # 执行动作
    CONDITION = "condition"  # 条件判断
    LOOP = "loop"  # 循环
    PARALLEL = "parallel"  # 并行
    WAIT = "wait"  # 等待
    AI = "ai"  # AI调用
    AGENT = "agent"  # Agent调用
    MCP = "mcp"  # MCP工具


@dataclass
class WorkflowStep:
    """工作流步骤"""

    id: str
    type: StepType
    name: str
    action: Callable = None
    params: Dict = field(default_factory=dict)
    condition: Callable = None
    on_success: str = None
    on_failure: str = None
    retry_count: int = 0
    retry_delay: int = 1
    timeout: int = 300

    # 运行时状态
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str = None
    start_time: datetime = None
    end_time: datetime = None
    execution_count: int = 0


@dataclass
class WorkflowContext:
    """工作流上下文"""

    variables: Dict = field(default_factory=dict)
    steps_results: Dict = field(default_factory=dict)
    current_step: str = None
    workflow_id: str = None
    start_time: datetime = None
    end_time: datetime = None

    def set(self, key: str, value: Any):
        """设置变量"""
        self.variables[key] = value

    def get(self, key: str, default=None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)

    def get_step_result(self, step_id: str) -> Any:
        """获取步骤结果"""
        return self.steps_results.get(step_id)


class Workflow:
    """
    高级工作流

    用法:
        # 创建工作流
        wf = Workflow("我的流程")

        # 添加步骤
        wf.add_step("step1", StepType.ACTION, action=func, params={"x": 1})
        wf.add_step("step2", StepType.CONDITION, condition=lambda ctx: ctx.get("x") > 0)
        wf.add_step("step3", StepType.AI, params={"prompt": "分析数据"})

        # 设置跳转
        wf.set_transition("step2", on_success="step3", on_failure="step_error")

        # 执行
        result = wf.run()
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: Dict[str, WorkflowStep] = {}
        self.transitions: Dict[str, Dict] = {}
        self.context = WorkflowContext()

        # 工具
        self.ai = UnifiedAI()
        self.agent = Agent()
        self.mcp = MCPExtended()

    def add_step(
        self,
        step_id: str,
        step_type: StepType,
        name: str = None,
        action: Callable = None,
        params: Dict = None,
        condition: Callable = None,
        **kwargs,
    ) -> "Workflow":
        """
        添加步骤

        Args:
            step_id: 步骤ID
            step_type: 步骤类型
            name: 步骤名称
            action: 执行函数
            params: 参数
            condition: 条件函数
        """
        step = WorkflowStep(
            id=step_id,
            type=step_type,
            name=name or step_id,
            action=action,
            params=params or {},
            condition=condition,
            **kwargs,
        )
        self.steps[step_id] = step
        return self

    def set_transition(self, step_id: str, on_success: str = None, on_failure: str = None):
        """设置步骤跳转"""
        self.transitions[step_id] = {"on_success": on_success, "on_failure": on_failure}

    def run(self, start_step: str = None, context_vars: Dict = None) -> Dict:
        """
        执行工作流

        Args:
            start_step: 起始步骤ID
            context_vars: 初始上下文变量

        Returns:
            执行结果
        """
        # 初始化上下文
        self.context.workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.context.start_time = datetime.now()
        if context_vars:
            self.context.variables.update(context_vars)

        # 确定起始步骤
        current_step = start_step or list(self.steps.keys())[0]

        print(f"🚀 启动工作流: {self.name}")
        print(f"   ID: {self.context.workflow_id}")
        print(f"   起始步骤: {current_step}")
        print("-" * 60)

        try:
            while current_step:
                if current_step not in self.steps:
                    print(f"❌ 步骤不存在: {current_step}")
                    break

                step = self.steps[current_step]
                self.context.current_step = current_step

                # 执行步骤
                success = self._execute_step(step)

                # 确定下一步
                if success:
                    next_step = self.transitions.get(current_step, {}).get("on_success")
                else:
                    next_step = self.transitions.get(current_step, {}).get("on_failure")

                if not next_step:
                    # 默认顺序执行
                    step_keys = list(self.steps.keys())
                    idx = step_keys.index(current_step)
                    if idx < len(step_keys) - 1:
                        next_step = step_keys[idx + 1]

                current_step = next_step

            self.context.end_time = datetime.now()
            print("-" * 60)
            print(f"✅ 工作流完成")

            return {
                "success": True,
                "context": self.context.variables,
                "steps_results": self.context.steps_results,
                "duration": self._get_duration(),
            }

        except Exception as e:
            self.context.end_time = datetime.now()
            print(f"❌ 工作流失败: {e}")
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "context": self.context.variables,
                "steps_results": self.context.steps_results,
                "duration": self._get_duration(),
            }

    def _execute_step(self, step: WorkflowStep) -> bool:
        """执行单个步骤"""
        print(f"\n▶️  执行步骤: {step.name} ({step.type.value})")

        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        step.execution_count += 1

        try:
            if step.type == StepType.ACTION:
                result = self._execute_action(step)
            elif step.type == StepType.CONDITION:
                result = self._execute_condition(step)
            elif step.type == StepType.AI:
                result = self._execute_ai(step)
            elif step.type == StepType.AGENT:
                result = self._execute_agent(step)
            elif step.type == StepType.MCP:
                result = self._execute_mcp(step)
            elif step.type == StepType.LOOP:
                result = self._execute_loop(step)
            elif step.type == StepType.PARALLEL:
                result = self._execute_parallel(step)
            elif step.type == StepType.WAIT:
                result = self._execute_wait(step)
            else:
                result = None

            step.result = result
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now()
            self.context.steps_results[step.id] = result

            duration = (step.end_time - step.start_time).total_seconds()
            print(f"   ✅ 完成 ({duration:.2f}s)")

            return True

        except Exception as e:
            step.error = str(e)
            step.status = StepStatus.FAILED
            step.end_time = datetime.now()

            print(f"   ❌ 失败: {e}")

            # 重试逻辑
            if step.execution_count <= step.retry_count:
                print(f"   🔄 重试 ({step.execution_count}/{step.retry_count})")
                import time

                time.sleep(step.retry_delay)
                return self._execute_step(step)

            return False

    def _execute_action(self, step: WorkflowStep) -> Any:
        """执行动作步骤"""
        if step.action:
            return step.action(self.context, **step.params)
        return None

    def _execute_condition(self, step: WorkflowStep) -> bool:
        """执行条件步骤"""
        if step.condition:
            return step.condition(self.context)
        return True

    def _execute_ai(self, step: WorkflowStep) -> str:
        """执行AI步骤"""
        prompt = step.params.get("prompt", "")
        provider = step.params.get("provider")
        model = step.params.get("model")

        # 替换变量
        prompt = self._replace_vars(prompt)

        return self.ai.chat(prompt, provider=provider, model=model)

    def _execute_agent(self, step: WorkflowStep) -> str:
        """执行Agent步骤"""
        task = step.params.get("task", "")
        provider = step.params.get("provider")

        # 替换变量
        task = self._replace_vars(task)

        return self.agent.run(task, provider=provider)

    def _execute_mcp(self, step: WorkflowStep) -> str:
        """执行MCP步骤"""
        tool = step.params.get("tool")
        action = step.params.get("action")
        args = step.params.get("args", [])
        kwargs = step.params.get("kwargs", {})

        # 替换变量
        args = [self._replace_vars(str(arg)) for arg in args]
        kwargs = {k: self._replace_vars(str(v)) for k, v in kwargs.items()}

        if tool == "file":
            return self.mcp.file(action, *args, **kwargs)
        elif tool == "code":
            return self.mcp.code(action, *args, **kwargs)
        elif tool == "data":
            return self.mcp.data(action, *args, **kwargs)
        elif tool == "network":
            return self.mcp.network(action, *args, **kwargs)
        elif tool == "system":
            return self.mcp.system(action, *args, **kwargs)

        return "[错误] 未知MCP工具"

    def _execute_loop(self, step: WorkflowStep) -> List:
        """执行循环步骤"""
        items = step.params.get("items", [])
        action = step.params.get("action")
        results = []

        for item in items:
            self.context.set("loop_item", item)
            if action:
                result = action(self.context, item)
                results.append(result)

        return results

    def _execute_parallel(self, step: WorkflowStep) -> List:
        """执行并行步骤"""
        actions = step.params.get("actions", [])
        results = []

        # 使用线程池并行执行
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=len(actions)) as executor:
            futures = [executor.submit(action, self.context) for action in actions]
            results = [f.result() for f in futures]

        return results

    def _execute_wait(self, step: WorkflowStep) -> None:
        """执行等待步骤"""
        seconds = step.params.get("seconds", 1)
        import time

        time.sleep(seconds)

    def _replace_vars(self, text: str) -> str:
        """替换文本中的变量"""
        pattern = r"\$\{(\w+)\}"

        def replace(match):
            var_name = match.group(1)
            return str(self.context.get(var_name, match.group(0)))

        return re.sub(pattern, replace, text)

    def _get_duration(self) -> float:
        """获取执行时长"""
        if self.context.start_time and self.context.end_time:
            return (self.context.end_time - self.context.start_time).total_seconds()
        return 0

    def export(self, path: str):
        """导出工作流定义"""
        data = {
            "name": self.name,
            "description": self.description,
            "steps": {
                step_id: {
                    "id": step.id,
                    "type": step.type.value,
                    "name": step.name,
                    "params": step.params,
                    "retry_count": step.retry_count,
                    "timeout": step.timeout,
                }
                for step_id, step in self.steps.items()
            },
            "transitions": self.transitions,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 工作流已导出: {path}")

    @classmethod
    def load(cls, path: str) -> "Workflow":
        """加载工作流定义"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        wf = cls(data["name"], data.get("description", ""))

        for step_id, step_data in data["steps"].items():
            wf.add_step(
                step_id=step_id,
                step_type=StepType(step_data["type"]),
                name=step_data["name"],
                params=step_data.get("params", {}),
                retry_count=step_data.get("retry_count", 0),
                timeout=step_data.get("timeout", 300),
            )

        for step_id, trans in data.get("transitions", {}).items():
            wf.set_transition(step_id, on_success=trans.get("on_success"), on_failure=trans.get("on_failure"))

        print(f"✅ 工作流已加载: {path}")
        return wf


# ============ 预定义工作流模板 ============


class WorkflowTemplates:
    """工作流模板"""

    @staticmethod
    def code_review_flow() -> Workflow:
        """代码审查工作流"""
        wf = Workflow("代码审查", "自动代码审查流程")

        wf.add_step("read_code", StepType.MCP, params={"tool": "file", "action": "read", "args": ["${file_path}"]})

        wf.add_step("analyze", StepType.AI, params={"prompt": "审查以下代码，找出潜在问题:\n${read_code}"})

        wf.add_step("check_style", StepType.MCP, params={"tool": "code", "action": "lint", "args": ["${file_path}"]})

        wf.add_step("generate_report", StepType.AI, params={"prompt": "基于分析结果生成审查报告"})

        return wf

    @staticmethod
    def project_setup_flow() -> Workflow:
        """项目初始化工作流"""
        wf = Workflow("项目初始化", "新项目初始化流程")

        wf.add_step(
            "create_structure", StepType.ACTION, action=lambda ctx: WorkflowTemplates._create_project_structure(ctx)
        )

        wf.add_step("init_git", StepType.MCP, params={"tool": "system", "action": "exec", "args": ["git init"]})

        wf.add_step("create_readme", StepType.AI, params={"prompt": "为项目 ${project_name} 生成README.md"})

        wf.add_step(
            "write_readme",
            StepType.MCP,
            params={"tool": "file", "action": "write", "kwargs": {"path": "README.md", "content": "${create_readme}"}},
        )

        return wf

    @staticmethod
    def _create_project_structure(ctx: WorkflowContext) -> str:
        """创建项目结构"""
        import os

        dirs = ["src", "tests", "docs", "config"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        return f"创建目录: {', '.join(dirs)}"


# ============ 便捷函数 ============


def create_workflow(name: str, description: str = "") -> Workflow:
    """创建工作流"""
    return Workflow(name, description)


def run_workflow(wf: Workflow, **kwargs) -> Dict:
    """运行工作流"""
    return wf.run(**kwargs)


def load_workflow(path: str) -> Workflow:
    """加载工作流"""
    return Workflow.load(path)


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("高级工作流系统测试")
    print("=" * 60)

    # 创建简单工作流
    wf = Workflow("测试流程")

    wf.add_step("step1", StepType.ACTION, action=lambda ctx: print("执行步骤1") or "结果1")

    wf.add_step("step2", StepType.AI, params={"prompt": "你好"})

    # 运行
    result = wf.run()
    print(f"\n最终结果: {result}")
