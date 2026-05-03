#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 统一工作流引擎（已修复资源泄漏）

功能:
- 工作流定义解析
- 步骤依赖管理
- 并行/顺序执行
- 状态持久化
- 错误重试
- 资源泄漏防护
"""

import json
import time
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import as_completed
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from event_bus import get_event_bus
from skills.base import get_registry
from resource_manager import ManagedThreadPoolExecutor, get_resource_tracker
from plugin_manager import get_plugin_manager


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    description: str
    skill: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None
    retry_count: int = 3
    timeout: int = 300
    parallel: bool = False
    target: str = "local"  # local/remote/both

    # 运行时状态
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_attempts: int = 0


@dataclass
class Workflow:
    """工作流"""
    name: str
    version: str
    description: str
    steps: List[WorkflowStep]
    config: Dict[str, Any] = field(default_factory=dict)

    # 运行时状态
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """工作流引擎（已修复资源泄漏）"""

    def __init__(self):
        self.config = get_config()
        self.event_bus = get_event_bus()
        self.skill_registry = get_registry()
        self.plugin_manager = get_plugin_manager()

        self.workflows_dir = Path(self.config.get('workflow.templates_dir', '/python/MCP_Core/workflow/templates'))
        self.state_dir = Path(self.config.get('workflow.state_dir', '/python/MCP_Core/.workflow_state'))
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.max_parallel = self.config.get('workflow.max_parallel_steps', 5)
        self.default_timeout = self.config.get('workflow.default_timeout', 600)
        self.auto_backup = self.config.get('workflow.auto_backup', True)

        self._current_workflow: Optional[Workflow] = None

        # 使用带资源管理的线程池
        self._executor = ManagedThreadPoolExecutor(max_workers=self.max_parallel, name='workflow_engine')
        self._lock = threading.RLock()

        # 注册到资源追踪器
        get_resource_tracker().track('workflow_engine', self, 'main_engine')

    def load_workflow(self, workflow_name: str) -> Optional[Workflow]:
        """加载工作流"""
        workflow_file = self.workflows_dir / f"{workflow_name}.json"

        if not workflow_file.exists():
            print(f"[WorkflowEngine] 工作流不存在: {workflow_name}")
            return None

        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 解析步骤
            steps = []
            for step_data in data.get('steps', []):
                step = WorkflowStep(
                    id=str(step_data.get('id', '')),
                    name=step_data.get('name', ''),
                    description=step_data.get('description', ''),
                    skill=step_data.get('skill', ''),
                    action=step_data.get('action', ''),
                    params=step_data.get('params', {}),
                    depends_on=step_data.get('depends_on', []),
                    condition=step_data.get('condition'),
                    retry_count=step_data.get('retry', 3),
                    timeout=step_data.get('timeout', self.default_timeout),
                    parallel=step_data.get('parallel', False),
                    target=step_data.get('target', 'local')
                )
                steps.append(step)

            workflow = Workflow(
                name=data.get('name', workflow_name),
                version=data.get('version', '1.0'),
                description=data.get('description', ''),
                steps=steps,
                config=data.get('config', {})
            )

            return workflow

        except Exception as e:
            print(f"[WorkflowEngine] 加载工作流失败: {e}")
            return None

    def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        workflows = []

        if self.workflows_dir.exists():
            for workflow_file in self.workflows_dir.glob('*.json'):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    workflows.append({
                        'name': data.get('name', workflow_file.stem),
                        'file': workflow_file.name,
                        'description': data.get('description', ''),
                        'version': data.get('version', '1.0'),
                        'steps_count': len(data.get('steps', []))
                    })
                except Exception:
                    pass

        return workflows

    def execute(self, workflow: Workflow, context: Optional[Dict] = None) -> Dict:
        """执行工作流"""
        with self._lock:
            self._current_workflow = workflow
            workflow.status = WorkflowStatus.RUNNING
            workflow.start_time = time.time()

            if context:
                workflow.context.update(context)

        # 发布工作流开始事件
        self.event_bus.publish('workflow_start', {
            'workflow': workflow.name,
            'steps_count': len(workflow.steps)
        }, source='workflow_engine')

        try:
            # 构建依赖图
            dependency_graph = self._build_dependency_graph(workflow.steps)

            # 执行步骤
            completed_steps = set()
            failed_steps = set()

            while len(completed_steps) + len(failed_steps) < len(workflow.steps):
                # 获取可执行的步骤
                ready_steps = self._get_ready_steps(
                    workflow.steps,
                    dependency_graph,
                    completed_steps,
                    failed_steps
                )

                if not ready_steps:
                    if failed_steps:
                        break
                    time.sleep(0.1)
                    continue

                # 分离并行和顺序步骤
                parallel_steps = [s for s in ready_steps if s.parallel]
                sequential_steps = [s for s in ready_steps if not s.parallel]

                # 执行并行步骤
                if parallel_steps:
                    self._execute_parallel_steps(parallel_steps, workflow)
                    for step in parallel_steps:
                        if step.status == StepStatus.COMPLETED:
                            completed_steps.add(step.id)
                        elif step.status == StepStatus.FAILED:
                            failed_steps.add(step.id)

                # 执行顺序步骤
                for step in sequential_steps:
                    self._execute_step(step, workflow)
                    if step.status == StepStatus.COMPLETED:
                        completed_steps.add(step.id)
                    elif step.status == StepStatus.FAILED:
                        failed_steps.add(step.id)
                        break

                # 保存状态
                self._save_state(workflow)

            # 完成
            workflow.end_time = time.time()

            if failed_steps:
                workflow.status = WorkflowStatus.FAILED
                result = {
                    'success': False,
                    'workflow': workflow.name,
                    'completed': len(completed_steps),
                    'failed': len(failed_steps),
                    'total': len(workflow.steps),
                    'duration': workflow.end_time - workflow.start_time
                }
            else:
                workflow.status = WorkflowStatus.COMPLETED
                result = {
                    'success': True,
                    'workflow': workflow.name,
                    'completed': len(completed_steps),
                    'total': len(workflow.steps),
                    'duration': workflow.end_time - workflow.start_time
                }

            # 发布工作流完成事件
            self.event_bus.publish('workflow_complete', result, source='workflow_engine')

            return result

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = time.time()

            error_result = {
                'success': False,
                'workflow': workflow.name,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

            self.event_bus.publish('workflow_error', error_result, source='workflow_engine')

            return error_result

    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {step.id: [] for step in steps}

        for step in steps:
            for dep_id in step.depends_on:
                if dep_id in graph:
                    graph[step.id].append(dep_id)

        return graph

    def _get_ready_steps(
        self,
        steps: List[WorkflowStep],
        dependency_graph: Dict[str, List[str]],
        completed_steps: set,
        failed_steps: set
    ) -> List[WorkflowStep]:
        """获取可执行的步骤"""
        ready = []

        for step in steps:
            if step.status != StepStatus.PENDING:
                continue

            # 检查依赖
            deps = dependency_graph.get(step.id, [])
            if all(dep in completed_steps for dep in deps):
                # 检查条件
                if step.condition:
                    if not self._evaluate_condition(step.condition, steps):
                        step.status = StepStatus.SKIPPED
                        continue
                ready.append(step)

        return ready

    def _evaluate_condition(self, condition: str, steps: List[WorkflowStep]) -> bool:
        """评估条件"""
        try:
            if '.' in condition:
                parts = condition.split('.')
                step_id = parts[0]
                attr = parts[1]

                for step in steps:
                    if step.id == step_id:
                        if attr == 'success':
                            return step.status == StepStatus.COMPLETED
                        elif attr == 'failed':
                            return step.status == StepStatus.FAILED

            return True
        except Exception:
            return True

    def _execute_step(self, step: WorkflowStep, workflow: Workflow):
        """执行单个步骤"""
        with self._lock:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()
            workflow.current_step = step.id

        # 发布步骤开始事件
        self.event_bus.publish('step_start', {
            'workflow': workflow.name,
            'step': step.id,
            'name': step.name
        }, source='workflow_engine')

        try:
            # 获取技能
            skill = self.skill_registry.get(step.skill)

            if not skill:
                raise Exception(f"技能不存在: {step.skill}")

            # 准备参数
            params = step.params.copy()
            params['action'] = step.action

            # 替换上下文变量
            params = self._substitute_context(params, workflow.context)

            # 执行（带重试）
            result = None
            for attempt in range(step.retry_count):
                try:
                    result = self.skill_registry.execute(step.skill, params)
                    if result.get('success'):
                        break
                    else:
                        step.retry_attempts += 1
                        if attempt < step.retry_count - 1:
                            time.sleep(1)
                except Exception:
                    step.retry_attempts += 1
                    if attempt == step.retry_count - 1:
                        raise
                    time.sleep(1)

            # 更新步骤状态
            step.end_time = time.time()
            step.result = result

            if result and result.get('success'):
                step.status = StepStatus.COMPLETED

                # 更新上下文
                if 'output' in result:
                    workflow.context[f"{step.id}_output"] = result['output']
            else:
                step.status = StepStatus.FAILED
                step.error = result.get('error', '未知错误') if result else '执行失败'

            # 发布步骤完成事件
            self.event_bus.publish('step_complete', {
                'workflow': workflow.name,
                'step': step.id,
                'status': step.status.value,
                'duration': step.end_time - step.start_time
            }, source='workflow_engine')

        except Exception as e:
            step.end_time = time.time()
            step.status = StepStatus.FAILED
            step.error = str(e)

            self.event_bus.publish('step_error', {
                'workflow': workflow.name,
                'step': step.id,
                'error': str(e)
            }, source='workflow_engine')

    def _execute_parallel_steps(self, steps: List[WorkflowStep], workflow: Workflow):
        """并行执行步骤"""
        futures = {}

        for step in steps:
            future = self._executor.submit(self._execute_step, step, workflow)
            futures[future] = step

        # 等待所有完成
        for future in as_completed(futures):
            step = futures[future]
            try:
                future.result()
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)

    def _substitute_context(self, params: Dict, context: Dict) -> Dict:
        """替换上下文变量"""
        result = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith('$'):
                var_name = value[1:]
                result[key] = context.get(var_name, value)
            elif isinstance(value, dict):
                result[key] = self._substitute_context(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._substitute_context({'v': v}, context)['v'] if isinstance(v, dict) else
                    context.get(v[1:], v) if isinstance(v, str) and v.startswith('$') else v
                    for v in value
                ]
            else:
                result[key] = value

        return result

    def _save_state(self, workflow: Workflow):
        """保存工作流状态"""
        try:
            state_file = self.state_dir / f"{workflow.name}_state.json"

            state = {
                'name': workflow.name,
                'status': workflow.status.value,
                'current_step': workflow.current_step,
                'start_time': workflow.start_time,
                'end_time': workflow.end_time,
                'context': workflow.context,
                'steps': [
                    {
                        'id': step.id,
                        'status': step.status.value,
                        'start_time': step.start_time,
                        'end_time': step.end_time,
                        'result': step.result,
                        'error': step.error,
                        'retry_attempts': step.retry_attempts
                    }
                    for step in workflow.steps
                ]
            }

            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"[WorkflowEngine] 保存状态失败: {e}")

    def load_state(self, workflow_name: str) -> Optional[Dict]:
        """加载工作流状态"""
        state_file = self.state_dir / f"{workflow_name}_state.json"

        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        return None

    def register_plugin(self, plugin_name: str, path: str, description: str = "",
                       version: str = "1.0", author: str = "", enabled: bool = True,
                       priority: int = 0):
        """注册插件到插件管理器"""
        return self.plugin_manager.register_plugin(plugin_name, path, description,
                                                   version, author, enabled, priority)

    def load_plugin(self, plugin_name: str):
        """加载插件"""
        return self.plugin_manager.load_plugin(plugin_name)

    def unload_plugin(self, plugin_name: str):
        """卸载插件"""
        return self.plugin_manager.unload_plugin(plugin_name)

    def toggle_plugin(self, plugin_name: str, enabled: bool):
        """切换插件启用状态"""
        return self.plugin_manager.toggle_plugin(plugin_name, enabled)

    def execute_plugin(self, plugin_name: str, action: str = 'run', params: Dict[str, Any] = None):
        """执行插件动作"""
        return self.plugin_manager.execute_plugin(plugin_name, action, params)

    def list_plugins(self):
        """列出所有插件"""
        return self.plugin_manager.list_plugins()

    def get_plugin_performance_report(self):
        """获取插件性能报告"""
        return self.plugin_manager.get_performance_report()

    def shutdown(self):
        """关闭引擎"""
        self._executor.shutdown(wait=True)
        get_resource_tracker().untrack('workflow_engine', self)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'executor_stats': self._executor.stats,
            'max_parallel': self.max_parallel,
            'workflows_available': len(self.list_workflows()),
            'plugin_performance': self.get_plugin_performance_report()
        }


if __name__ == '__main__':
    # 测试工作流引擎
    engine = WorkflowEngine()

    print("工作流引擎测试")
    print(f"工作流目录: {engine.workflows_dir}")

    # 列出工作流
    print("\n1. 工作流列表:")
    workflows = engine.list_workflows()
    for wf in workflows:
        print(f"   - {wf['name']}: {wf['description']} ({wf['steps_count']} steps)")

    # 测试插件管理
    print("\n2. 插件管理测试:")
    plugins = engine.list_plugins()
    print(f"   插件数量: {len(plugins)}")

    # 获取性能报告
    print("\n3. 性能报告:")
    stats = engine.get_stats()
    print(f"   线程池: {stats['executor_stats']['name']}")
    print(f"   最大并行数: {stats['max_parallel']}")
    print(f"   可用工作流: {stats['workflows_available']}")

    plugin_report = stats['plugin_performance']
    print("\n   插件性能:")
    print(f"     总插件数: {plugin_report['total_plugins']}")
    print(f"     已启用: {plugin_report['enabled_plugins']}")
    print(f"     已加载: {plugin_report['loaded_plugins']}")

    engine.shutdown()
    print("\n工作流引擎测试完成")
