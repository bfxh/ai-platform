#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多AI工具联动系统
Multi-AI Toolkit Linkage System

功能:
- AI工具链式调用
- 多模型协作
- 任务分发
- 结果融合

用法:
    python ai_toolkit_linkage.py chain <task_config>
    python ai_toolkit_linkage.py parallel <task_config>
    python ai_toolkit_linkage.py route <task> <tools>
"""

import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill, handle_errors

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AI_ROOT = Path(os.environ.get("AI_ROOT", "/python"))


@dataclass
class LinkageTask:
    """联动任务"""

    task_id: str
    task_type: str  # chain, parallel, route
    steps: List[Dict]
    input_data: Any
    output_format: str = "json"
    metadata: Dict = field(default_factory=dict)


@dataclass
class LinkageResult:
    """联动结果"""

    task_id: str
    success: bool
    results: List[Dict]
    execution_time: float
    errors: List[str] = field(default_factory=list)


class AIToolkitLinkage(Skill):
    """AI工具联动系统"""

    # 技能元数据
    name = "ai_toolkit_linkage"
    description = "多AI工具联动系统 - 链式调用、多模型协作、任务分发、结果融合"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "ai_toolkit_linkage"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.results = []
        self.tool_adapters = {}
        self._load_adapters()

    def _load_adapters(self):
        """加载工具适配器"""
        adapter_path = AI_ROOT / "MCP_Core" / "adapters" / "unified_adapter.py"
        if adapter_path.exists():
            print(f"加载适配器: {adapter_path}")

    def chain_execute(self, task_config: Dict) -> LinkageResult:
        """
        链式执行 - 一个工具的输出作为下一个工具的输入

        示例配置:
        {
            "steps": [
                {"tool": "openai", "action": "summarize", "prompt": "总结以下内容"},
                {"tool": "anthropic", "action": "analyze", "prompt": "分析总结结果"},
                {"tool": "openai", "action": "generate", "prompt": "基于分析生成报告"}
            ]
        }
        """
        print("\n" + "=" * 60)
        print("链式执行模式")
        print("=" * 60 + "\n")

        start_time = datetime.now()
        task_id = task_config.get("task_id", f"chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        steps = task_config.get("steps", [])
        input_data = task_config.get("input", "")

        results = []
        current_data = input_data
        errors = []

        for i, step in enumerate(steps, 1):
            tool = step.get("tool")
            action = step.get("action")

            print(f"\n步骤 {i}/{len(steps)}: {tool} -> {action}")
            current_str = str(current_data)
            print(
                f"  输入: {current_str[:100]}..."
                if len(current_str) > 100
                else f"  输入: {current_str}"
            )

            try:
                # 模拟执行（实际应调用真实API）
                result = self._execute_tool(tool, action, current_data, step.get("params", {}))
                results.append(
                    {
                        "step": i,
                        "tool": tool,
                        "action": action,
                        "input": current_data,
                        "output": result,
                        "status": "success",
                    }
                )
                current_data = result
                result_str = str(result)
                print(
                    f"  输出: {result_str[:100]}..."
                    if len(result_str) > 100
                    else f"  输出: {result_str}"
                )

            except Exception as e:
                error_msg = f"步骤 {i} 失败: {e}"
                errors.append(error_msg)
                print(f"  错误: {error_msg}")
                results.append(
                    {"step": i, "tool": tool, "action": action, "status": "error", "error": str(e)}
                )
                break

        execution_time = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 60)
        print(
            f"链式执行完成: {len([r for r in results if r.get('status') == 'success'])} 成功, {len(errors)} 失败"
        )
        print(f"执行时间: {execution_time:.2f} 秒")
        print("=" * 60 + "\n")

        return LinkageResult(
            task_id=task_id,
            success=len(errors) == 0,
            results=results,
            execution_time=execution_time,
            errors=errors,
        )

    def parallel_execute(self, task_config: Dict) -> LinkageResult:
        """
        并行执行 - 多个工具同时处理同一任务

        示例配置:
        {
            "input": "任务描述",
            "tools": ["openai", "anthropic", "google"],
            "merge_strategy": "best"  # best, concat, vote
        }
        """
        print("\n" + "=" * 60)
        print("并行执行模式")
        print("=" * 60 + "\n")

        start_time = datetime.now()
        task_id = task_config.get("task_id", f"parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        input_data = task_config.get("input", "")
        tools = task_config.get("tools", [])
        merge_strategy = task_config.get("merge_strategy", "concat")

        print(f"输入: {input_data}")
        print(f"工具: {', '.join(tools)}")
        print(f"合并策略: {merge_strategy}\n")

        results = []
        errors = []

        # 空工具列表保护
        if not tools:
            print("警告: 工具列表为空，跳过并行执行")
            return LinkageResult(
                task_id=task_id,
                success=False,
                results=[],
                execution_time=0.0,
                errors=["工具列表为空"],
            )

        # 并行执行
        with ThreadPoolExecutor(max_workers=len(tools)) as executor:
            futures = {
                executor.submit(self._execute_tool, tool, "process", input_data, {}): tool
                for tool in tools
            }

            for future in as_completed(futures):
                tool = futures[future]
                try:
                    result = future.result(timeout=30)
                    results.append({"tool": tool, "output": result, "status": "success"})
                    print(f"  {tool}: 完成")
                except Exception as e:
                    errors.append(f"{tool}: {e}")
                    results.append({"tool": tool, "status": "error", "error": str(e)})
                    print(f"  {tool}: 错误 - {e}")

        # 合并结果
        merged_result = self._merge_results(results, merge_strategy)

        execution_time = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 60)
        print(
            f"并行执行完成: {len([r for r in results if r.get('status') == 'success'])} 成功, {len(errors)} 失败"
        )
        print(f"执行时间: {execution_time:.2f} 秒")
        print("=" * 60 + "\n")

        return LinkageResult(
            task_id=task_id,
            success=len(errors) == 0,
            results=results + [{"merged": merged_result}],
            execution_time=execution_time,
            errors=errors,
        )

    def route_execute(self, task_description: str, available_tools: List[str]) -> LinkageResult:
        """
        智能路由 - 根据任务选择最佳工具

        Args:
            task_description: 任务描述
            available_tools: 可用工具列表
        """
        print("\n" + "=" * 60)
        print("智能路由模式")
        print("=" * 60 + "\n")

        start_time = datetime.now()
        task_id = f"route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"任务: {task_description}")
        print(f"可用工具: {', '.join(available_tools)}\n")

        # 路由决策逻辑
        selected_tool = self._select_best_tool(task_description, available_tools)
        print(f"选择工具: {selected_tool}\n")

        try:
            result = self._execute_tool(selected_tool, "process", task_description, {})
            results = [{"tool": selected_tool, "output": result, "status": "success"}]
            errors = []
            success = True
        except Exception as e:
            results = [{"tool": selected_tool, "status": "error", "error": str(e)}]
            errors = [str(e)]
            success = False

        execution_time = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 60)
        print(f"路由执行完成: {'成功' if success else '失败'}")
        print(f"执行时间: {execution_time:.2f} 秒")
        print("=" * 60 + "\n")

        return LinkageResult(
            task_id=task_id,
            success=success,
            results=results,
            execution_time=execution_time,
            errors=errors,
        )

    def _execute_tool(self, tool: str, action: str, data: Any, params: Dict) -> Any:
        """执行工具"""
        # 这里应该调用真实的AI工具API
        # 目前返回模拟结果
        return f"[{tool}] 处理结果: {action} 完成"

    def _select_best_tool(self, task: str, tools: List[str]) -> str:
        """选择最佳工具"""
        # 简单的关键词匹配
        task_lower = task.lower()

        if "代码" in task_lower or "code" in task_lower:
            return "openai" if "openai" in tools else tools[0]
        elif "分析" in task_lower or "analyze" in task_lower:
            return "anthropic" if "anthropic" in tools else tools[0]
        elif "本地" in task_lower or "local" in task_lower:
            return "ollama" if "ollama" in tools else tools[0]
        else:
            return tools[0] if tools else "openai"

    def _merge_results(self, results: List[Dict], strategy: str) -> str:
        """合并多个结果"""
        successful_results = [r["output"] for r in results if r.get("status") == "success"]

        if strategy == "concat":
            return "\n\n---\n\n".join(successful_results)
        elif strategy == "best":
            # 选择最长的结果作为最佳结果
            return max(successful_results, key=len) if successful_results else ""
        elif strategy == "vote":
            # 简单的投票机制
            return successful_results[0] if successful_results else ""
        else:
            return "\n".join(successful_results)

    def create_workflow_template(self, template_type: str) -> Dict:
        """创建工作流模板"""
        templates = {
            "content_creation": {
                "name": "内容创作工作流",
                "type": "chain",
                "steps": [
                    {"tool": "openai", "action": "generate_outline", "description": "生成大纲"},
                    {"tool": "anthropic", "action": "expand_content", "description": "扩展内容"},
                    {"tool": "openai", "action": "polish", "description": "润色"},
                ],
            },
            "code_review": {
                "name": "代码审查工作流",
                "type": "parallel",
                "tools": ["openai", "anthropic"],
                "merge_strategy": "concat",
            },
            "research": {
                "name": "研究分析工作流",
                "type": "chain",
                "steps": [
                    {"tool": "google", "action": "search_summarize", "description": "搜索总结"},
                    {"tool": "anthropic", "action": "deep_analysis", "description": "深度分析"},
                    {"tool": "openai", "action": "generate_report", "description": "生成报告"},
                ],
            },
        }

        return templates.get(template_type, {})

    def get_parameters(self) -> Dict:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "enum": ["chain", "parallel", "route", "template"],
                "description": "操作类型",
            },
            "task_config": {"type": "object", "required": False, "description": "任务配置"},
            "task_description": {"type": "string", "required": False, "description": "任务描述"},
            "available_tools": {"type": "array", "required": False, "description": "可用工具列表"},
            "template_type": {"type": "string", "required": False, "description": "模板类型"},
        }

    @handle_errors
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        action = params.get("action")

        if action == "chain":
            task_config = params.get("task_config", {})
            result = self.chain_execute(task_config)
            return {
                "success": result.success,
                "result": {
                    "task_id": result.task_id,
                    "results": result.results,
                    "execution_time": result.execution_time,
                    "errors": result.errors,
                },
            }
        elif action == "parallel":
            task_config = params.get("task_config", {})
            result = self.parallel_execute(task_config)
            return {
                "success": result.success,
                "result": {
                    "task_id": result.task_id,
                    "results": result.results,
                    "execution_time": result.execution_time,
                    "errors": result.errors,
                },
            }
        elif action == "route":
            task_description = params.get("task_description", "")
            available_tools = params.get("available_tools", [])
            result = self.route_execute(task_description, available_tools)
            return {
                "success": result.success,
                "result": {
                    "task_id": result.task_id,
                    "results": result.results,
                    "execution_time": result.execution_time,
                    "errors": result.errors,
                },
            }
        elif action == "template":
            template_type = params.get("template_type", "content_creation")
            template = self.create_workflow_template(template_type)
            return {"success": True, "result": template}
        else:
            return {"success": False, "error": "无效的操作"}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_toolkit_linkage.py <命令>")
        print("命令:")
        print("  chain <config_file>     链式执行")
        print("  parallel <config_file>  并行执行")
        print("  route <task> <tools>    智能路由")
        print("  template <type>         创建模板")
        return

    linkage = AIToolkitLinkage()
    command = sys.argv[1]

    if command == "chain" and len(sys.argv) >= 3:
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            config = json.load(f)
        result = linkage.chain_execute(config)
        print(json.dumps(result.__dict__, indent=2, ensure_ascii=False, default=str))

    elif command == "parallel" and len(sys.argv) >= 3:
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            config = json.load(f)
        result = linkage.parallel_execute(config)
        print(json.dumps(result.__dict__, indent=2, ensure_ascii=False, default=str))

    elif command == "route" and len(sys.argv) >= 4:
        task = sys.argv[2]
        tools = sys.argv[3].split(",")
        result = linkage.route_execute(task, tools)
        print(json.dumps(result.__dict__, indent=2, ensure_ascii=False, default=str))

    elif command == "template" and len(sys.argv) >= 3:
        template = linkage.create_workflow_template(sys.argv[2])
        print(json.dumps(template, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令或参数不足: {command}")


if __name__ == "__main__":
    main()
