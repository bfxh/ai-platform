#!/usr/bin/env python3
"""
极简工作流引擎 - 一句话定义，自动执行
减少90%的配置，保持100%功能
"""

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Workflow:
    """极简工作流定义"""

    name: str
    steps: List[str]  # 简化: 只用字符串列表
    auto: bool = True  # 自动执行


class WorkflowEngine:
    """工作流引擎 - 自动编排执行"""

    def __init__(self):
        self.skills = {}
        self.workflows = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认技能"""
        try:
            from router import analyze, code, design, do, review
        except ImportError:
            do = None

        self.skills = {
            "do": do,
            "code": code,
            "review": review,
            "design": design,
            "analyze": analyze,
            "search": lambda q: do(f"搜索: {q}"),
            "write": lambda t: do(f"写作: {t}"),
            "fix": lambda c: do(f"修复: {c}"),
            "test": lambda c: do(f"测试: {c}"),
            "doc": lambda c: do(f"文档: {c}"),
            "refactor": lambda c: do(f"重构: {c}"),
        }

    def register(self, name: str, func: Callable):
        """注册技能"""
        self.skills[name] = func

    def define(self, name: str, steps: List[str]):
        """
        定义工作流 - 一句话
        示例: define("dev", ["analyze", "code", "review", "test"])
        """
        self.workflows[name] = Workflow(name=name, steps=steps)
        return self

    def run(self, workflow_name: str, input_data: str) -> Dict[str, Any]:
        """
        执行工作流
        自动串联所有步骤
        """
        if workflow_name not in self.workflows:
            # 动态创建工作流
            return self._dynamic_run(workflow_name, input_data)

        workflow = self.workflows[workflow_name]
        results = {}
        context = input_data

        for step in workflow.steps:
            if step in self.skills:
                # 执行技能
                result = self.skills[step](context)
                results[step] = result
                context = result  # 传递上下文
            else:
                # 动态解释
                result = self.skills["do"](f"{step}: {context}")
                results[step] = result
                context = result

        return {"workflow": workflow_name, "input": input_data, "results": results, "output": context}

    def _dynamic_run(self, task_type: str, input_data: str) -> Dict:
        """动态执行 - 智能推断工作流"""
        # 根据任务类型自动选择工作流
        workflows_map = {
            "code": ["analyze", "code", "review"],
            "bug": ["analyze", "fix", "test"],
            "feature": ["analyze", "design", "code", "test"],
            "doc": ["analyze", "doc"],
            "review": ["review"],
            "test": ["analyze", "test"],
            "refactor": ["analyze", "refactor", "test"],
        }

        steps = workflows_map.get(task_type, ["do"])
        self.workflows[task_type] = Workflow(name=task_type, steps=steps)

        return self.run(task_type, input_data)

    def __call__(self, workflow_spec: str, input_data: str = "") -> Any:
        """
        极简调用 - 一句话执行
        示例: wf("code:写快速排序")
        """
        if ":" in workflow_spec:
            workflow_name, input_data = workflow_spec.split(":", 1)
        else:
            workflow_name = workflow_spec

        result = self.run(workflow_name, input_data)
        return result["output"]


# 全局引擎
wf = WorkflowEngine()

# 预定义常用工作流
wf.define("dev", ["analyze", "code", "review", "test"])
wf.define("fix", ["analyze", "fix", "test"])
wf.define("doc", ["analyze", "doc"])
wf.define("design", ["analyze", "design", "review"])


# 极简入口
def go(task: str) -> str:
    """
    极简入口 - 一句话完成所有
    示例: go("code:快速排序")
          go("fix:这个bug")
          go("doc:这个函数")
    """
    return wf(task)


# 快捷函数
def dev(feature: str) -> str:
    """完整开发流程"""
    return wf("dev", feature)


def fix(bug: str) -> str:
    """修复流程"""
    return wf("fix", bug)


def doc(code: str) -> str:
    """文档流程"""
    return wf("doc", code)


if __name__ == "__main__":
    # 测试
    print(go("code:写个快速排序"))
    print(go("review:检查这段代码"))
