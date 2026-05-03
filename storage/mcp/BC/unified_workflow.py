#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联合工作流引擎 - 结合 Claude Code + 我们的 MCP 工具

功能：
- 定义联合工作流
- 自动编排 Claude Code 工具 + 我们的 MCP 工具
- 支持条件分支、循环、并行
- 工作流状态管理
- 结果汇总与报告

用法：
    python unified_workflow.py list                    # 列出工作流
    python unified_workflow.py run <name> [params]     # 运行工作流
    python unified_workflow.py status <id>             # 查看状态
    python unified_workflow.py create <name>           # 创建工作流
    python unified_workflow.py edit <name>             # 编辑工作流

MCP调用：
    {"tool": "unified_workflow", "action": "run", "params": {"name": "..."}}
"""

import json
import sys
import os
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, r"\python")
from core.secure_utils import safe_eval_expr, SecureEvalError

_workflow_logger = logging.getLogger("unified_workflow")

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
WORKFLOW_PATH = AI_PATH / "Workflows"
WORKFLOW_PATH.mkdir(parents=True, exist_ok=True)

# ============================================================
# 工作流定义
# ============================================================
@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    tool: str  # 工具名称
    action: str  # 动作
    params: Dict = field(default_factory=dict)  # 参数
    depends_on: List[str] = field(default_factory=list)  # 依赖步骤
    condition: Optional[str] = None  # 执行条件
    retry_count: int = 0  # 重试次数
    timeout: int = 60  # 超时时间
    
@dataclass
class Workflow:
    """工作流"""
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)

@dataclass
class WorkflowInstance:
    """工作流实例"""
    id: str
    workflow_name: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    step_results: Dict = field(default_factory=dict)
    current_step: Optional[str] = None
    error: Optional[str] = None

# ============================================================
# 预定义工作流
# ============================================================
BUILTIN_WORKFLOWS = {
    "code_analyze_and_fix": Workflow(
        name="code_analyze_and_fix",
        description="代码分析 + AI修复 + 自动应用",
        steps=[
            WorkflowStep(
                id="1",
                tool="claude_code_bridge",
                action="analyze",
                params={"file": "{{file}}"}
            ),
            WorkflowStep(
                id="2",
                tool="ai_software",
                action="generate",
                params={"prompt": "分析以下代码问题并提供修复建议:\n{{step_1.result.analysis}}"},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="claude_code_bridge",
                action="edit",
                params={
                    "file": "{{file}}",
                    "changes": "{{step_2.result.code}}"
                },
                depends_on=["2"]
            ),
            WorkflowStep(
                id="4",
                tool="github_auto_commit",
                action="auto",
                params={"path": "{{project_path}}", "message": "自动修复代码"},
                depends_on=["3"],
                condition="{{auto_commit}}"
            )
        ],
        tags=["code", "ai", "github"]
    ),
    
    "web_research_and_download": Workflow(
        name="web_research_and_download",
        description="网页研究 + 资源下载 + 自动整理",
        steps=[
            WorkflowStep(
                id="1",
                tool="claude_code_bridge",
                action="call_claude_tool",
                params={"tool": "web_search", "tool_params": {"query": "{{query}}"}}
            ),
            WorkflowStep(
                id="2",
                tool="claude_code_bridge",
                action="call_claude_tool",
                params={"tool": "web_fetch", "tool_params": {"url": "{{step_1.result.urls[0]}}"}},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="vision_pro",
                action="analyze",
                params={"content": "{{step_2.result.content}}"},
                depends_on=["2"]
            ),
            WorkflowStep(
                id="4",
                tool="aria2_mcp",
                action="download",
                params={
                    "url": "{{download_url}}",
                    "options": {"dir": "D:/Downloads/Research"}
                },
                depends_on=["3"],
                condition="{{download_url}}"
            ),
            WorkflowStep(
                id="5",
                tool="auto_translate",
                action="translate_text",
                params={"text": "{{step_2.result.summary}}", "target_lang": "zh"},
                depends_on=["2"]
            )
        ],
        tags=["web", "research", "download"]
    ),
    
    "software_setup_auto": Workflow(
        name="software_setup_auto",
        description="软件搜索 + 下载 + 自动安装 + 配置",
        steps=[
            WorkflowStep(
                id="1",
                tool="local_software",
                action="search",
                params={"keyword": "{{software_name}}"}
            ),
            WorkflowStep(
                id="2",
                tool="aria2_mcp",
                action="download",
                params={"url": "{{step_1.result.download_url}}"},
                depends_on=["1"],
                condition="{{step_1.result.found}} == false"
            ),
            WorkflowStep(
                id="3",
                tool="da",
                action="click",
                params={"target": "安装向导"},
                depends_on=["2"]
            ),
            WorkflowStep(
                id="4",
                tool="da",
                action="type",
                params={"text": "%SOFTWARE_DIR%/GJ/{{software_name}}"},
                depends_on=["3"]
            ),
            WorkflowStep(
                id="5",
                tool="da",
                action="click",
                params={"target": "安装"},
                depends_on=["4"]
            ),
            WorkflowStep(
                id="6",
                tool="local_software",
                action="add",
                params={"path": "%SOFTWARE_DIR%/GJ/{{software_name}}"},
                depends_on=["5"]
            )
        ],
        tags=["software", "install", "auto"]
    ),
    
    "game_asset_pipeline": Workflow(
        name="game_asset_pipeline",
        description="游戏资源提取 + 处理 + 导入引擎",
        steps=[
            WorkflowStep(
                id="1",
                tool="extract",
                action="extract",
                params={"source": "{{game_path}}", "type": "{{asset_type}}"}
            ),
            WorkflowStep(
                id="2",
                tool="claude_code_bridge",
                action="analyze",
                params={"file": "{{step_1.result.extracted_files[0]}}"},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="auto_translate",
                action="translate_file",
                params={"file": "{{step_1.result.extracted_files}}"},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="4",
                tool="ue_mcp",
                action="import",
                params={
                    "project": "{{ue_project}}",
                    "files": "{{step_1.result.extracted_files}}"
                },
                depends_on=["2", "3"],
                condition="{{engine}} == 'ue5'"
            ),
            WorkflowStep(
                id="4b",
                tool="unity_mcp",
                action="import",
                params={
                    "project": "{{unity_project}}",
                    "files": "{{step_1.result.extracted_files}}"
                },
                depends_on=["2", "3"],
                condition="{{engine}} == 'unity'"
            )
        ],
        tags=["game", "asset", "pipeline"]
    ),
    
    "github_project_setup": Workflow(
        name="github_project_setup",
        description="GitHub项目初始化 + 配置 + 首次提交",
        steps=[
            WorkflowStep(
                id="1",
                tool="github_auto_commit",
                action="init",
                params={"path": "{{project_path}}", "repo_name": "{{repo_name}}"}
            ),
            WorkflowStep(
                id="2",
                tool="claude_code_bridge",
                action="call_claude_tool",
                params={
                    "tool": "file_write",
                    "tool_params": {
                        "file": "{{project_path}}/README.md",
                        "content": "# {{repo_name}}\n\n{{description}}"
                    }
                },
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="claude_code_bridge",
                action="call_claude_tool",
                params={
                    "tool": "file_write",
                    "tool_params": {
                        "file": "{{project_path}}/.gitignore",
                        "content": "__pycache__/\n*.pyc\n.env\nnode_modules/"
                    }
                },
                depends_on=["1"]
            ),
            WorkflowStep(
                id="4",
                tool="github_auto_commit",
                action="auto",
                params={"path": "{{project_path}}", "message": "Initial commit"},
                depends_on=["2", "3"]
            ),
            WorkflowStep(
                id="5",
                tool="github_accelerator",
                action="auto",
                params={},
                depends_on=["4"]
            )
        ],
        tags=["github", "project", "setup"]
    ),
    
    "ai_content_creation": Workflow(
        name="ai_content_creation",
        description="AI生成内容 + 翻译 + 发布",
        steps=[
            WorkflowStep(
                id="1",
                tool="ai_software",
                action="generate",
                params={"prompt": "{{content_prompt}}", "type": "text"}
            ),
            WorkflowStep(
                id="2",
                tool="ai_software",
                action="generate",
                params={"prompt": "为以下内容生成配图: {{step_1.result.text}}", "type": "image"},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="auto_translate",
                action="translate_text",
                params={"text": "{{step_1.result.text}}", "target_lang": "{{target_lang}}"},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="4",
                tool="claude_code_bridge",
                action="call_claude_tool",
                params={
                    "tool": "file_write",
                    "tool_params": {
                        "file": "{{output_path}}/content.md",
                        "content": "{{step_3.result.translated}}"
                    }
                },
                depends_on=["3"]
            ),
            WorkflowStep(
                id="5",
                tool="github_auto_commit",
                action="auto",
                params={"path": "{{output_path}}", "message": "Add content"},
                depends_on=["4"],
                condition="{{auto_publish}}"
            )
        ],
        tags=["ai", "content", "creation"]
    ),
    
    "system_optimization": Workflow(
        name="system_optimization",
        description="系统监控 + 内存优化 + 缓存清理",
        steps=[
            WorkflowStep(
                id="1",
                tool="memory_monitor",
                action="status",
                params={}
            ),
            WorkflowStep(
                id="2",
                tool="lazy_service_manager",
                action="cleanup",
                params={},
                depends_on=["1"],
                condition="{{step_1.result.mcp_total_mb}} > 500"
            ),
            WorkflowStep(
                id="3",
                tool="hybrid_cache",
                action="cleanup",
                params={},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="4",
                tool="local_software",
                action="scan",
                params={},
                depends_on=["2", "3"]
            ),
            WorkflowStep(
                id="5",
                tool="github_accelerator",
                action="auto",
                params={},
                depends_on=["4"]
            )
        ],
        tags=["system", "optimization", "maintenance"]
    ),
    
    "browser_download_workflow": Workflow(
        name="browser_download_workflow",
        description="浏览器下载拦截 + Aria2下载 + 自动整理",
        steps=[
            WorkflowStep(
                id="1",
                tool="aria2_mcp",
                action="start",
                params={}
            ),
            WorkflowStep(
                id="2",
                tool="browser_download_interceptor",
                action="start",
                params={},
                depends_on=["1"]
            ),
            WorkflowStep(
                id="3",
                tool="browser_download_interceptor",
                action="intercept",
                params={
                    "url": "{{download_url}}",
                    "filename": "{{filename}}"
                },
                depends_on=["2"]
            ),
            WorkflowStep(
                id="4",
                tool="aria2_mcp",
                action="list",
                params={"status": "active"},
                depends_on=["3"]
            )
        ],
        tags=["browser", "download", "aria2"]
    )
}

# ============================================================
# 工作流引擎
# ============================================================
class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._load_workflows()
    
    def _load_workflows(self):
        """加载工作流"""
        # 加载内置工作流
        self.workflows.update(BUILTIN_WORKFLOWS)
        
        # 加载自定义工作流
        for workflow_file in WORKFLOW_PATH.glob("*.json"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    workflow = Workflow(
                        name=data["name"],
                        description=data["description"],
                        steps=[WorkflowStep(**step) for step in data["steps"]],
                        tags=data.get("tags", [])
                    )
                    self.workflows[workflow.name] = workflow
            except Exception as e:
                print(f"加载工作流失败 {workflow_file}: {e}")
    
    def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        return [
            {
                "name": w.name,
                "description": w.description,
                "steps_count": len(w.steps),
                "tags": w.tags,
                "created_at": w.created_at
            }
            for w in self.workflows.values()
        ]
    
    def get_workflow(self, name: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(name)
    
    def create_instance(self, workflow_name: str, params: Dict) -> WorkflowInstance:
        """创建工作流实例"""
        instance_id = str(uuid.uuid4())[:8]
        
        instance = WorkflowInstance(
            id=instance_id,
            workflow_name=workflow_name,
            started_at=datetime.now().isoformat(),
            status="running"
        )
        
        self.instances[instance_id] = instance
        
        # 异步执行
        self.executor.submit(self._execute_workflow, instance, params)
        
        return instance
    
    def _execute_workflow(self, instance: WorkflowInstance, params: Dict):
        """执行工作流"""
        workflow = self.workflows.get(instance.workflow_name)
        if not workflow:
            instance.status = "failed"
            instance.error = f"工作流不存在: {instance.workflow_name}"
            return
        
        try:
            # 构建执行图
            step_map = {step.id: step for step in workflow.steps}
            completed = set()
            
            while len(completed) < len(workflow.steps):
                # 找到可以执行的步骤
                ready_steps = [
                    step for step in workflow.steps
                    if step.id not in completed
                    and all(dep in completed for dep in step.depends_on)
                ]
                
                if not ready_steps:
                    break
                
                # 执行步骤
                for step in ready_steps:
                    instance.current_step = step.id
                    
                    # 检查条件
                    if step.condition and not self._eval_condition(step.condition, instance, params):
                        completed.add(step.id)
                        instance.step_results[step.id] = {"skipped": True}
                        continue
                    
                    # 执行步骤
                    result = self._execute_step(step, instance, params)
                    instance.step_results[step.id] = result
                    
                    if result.get("success"):
                        completed.add(step.id)
                    else:
                        # 重试
                        if step.retry_count > 0:
                            for _ in range(step.retry_count):
                                time.sleep(1)
                                result = self._execute_step(step, instance, params)
                                if result.get("success"):
                                    completed.add(step.id)
                                    break
                        
                        if step.id not in completed:
                            instance.status = "failed"
                            instance.error = f"步骤 {step.id} 失败: {result.get('error')}"
                            return
            
            instance.status = "completed"
            instance.completed_at = datetime.now().isoformat()
        
        except Exception as e:
            instance.status = "failed"
            instance.error = str(e)
    
    def _eval_condition(self, condition: str, instance: WorkflowInstance, params: Dict) -> bool:
        try:
            context = {
                **params,
                **{f"step_{k}": v for k, v in instance.step_results.items()}
            }

            for key, value in context.items():
                if isinstance(value, str):
                    condition = condition.replace(f"{{{{{key}}}}}", value)

            names = {
                "True": True, "False": False, "None": None,
            }
            for key, value in context.items():
                if isinstance(key, str) and key.isidentifier():
                    names[key] = value

            functions = {
                "len": len, "str": str, "int": int, "float": float,
                "bool": bool, "abs": abs, "min": min, "max": max,
                "sum": sum, "round": round,
            }

            result = safe_eval_expr(condition, names=names, functions=functions)
            return bool(result)
        except SecureEvalError as e:
            _workflow_logger.warning("SecureEvalError in condition '%s': %s — defaulting to True", condition, e)
            return True
        except Exception:
            return True
    
    def _execute_step(self, step: WorkflowStep, instance: WorkflowInstance, params: Dict) -> Dict:
        """执行单个步骤"""
        # 替换参数中的变量
        resolved_params = self._resolve_params(step.params, instance, params)
        
        # 调用工具
        try:
            from .claude_code_bridge import ClaudeCodeBridge
            bridge = ClaudeCodeBridge()
            
            if step.tool in ["claude_code_bridge"]:
                # 调用 Claude Code 桥接器
                if step.action == "call_our_tool":
                    return bridge.call_our_tool(
                        resolved_params.get("tool"),
                        resolved_params.get("tool_action", ""),
                        resolved_params.get("tool_params", {})
                    )
                elif step.action == "call_claude_tool":
                    return bridge.call_claude_code_tool(
                        resolved_params.get("tool"),
                        resolved_params.get("tool_params", {})
                    )
                else:
                    return bridge.call_our_tool(step.tool, step.action, resolved_params)
            else:
                # 调用我们的 MCP 工具
                return bridge.call_our_tool(step.tool, step.action, resolved_params)
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _resolve_params(self, params: Dict, instance: WorkflowInstance, global_params: Dict) -> Dict:
        """解析参数中的变量"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # 替换 {{variable}}
                for gkey, gvalue in global_params.items():
                    value = value.replace(f"{{{{{gkey}}}}}", str(gvalue))
                
                # 替换步骤结果 {{step_X.result.y}}
                for step_id, step_result in instance.step_results.items():
                    if isinstance(step_result, dict):
                        for rkey, rvalue in step_result.items():
                            placeholder = f"{{{{step_{step_id}.result.{rkey}}}}}"
                            if placeholder in value:
                                value = value.replace(placeholder, str(rvalue))
                
                resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict]:
        """获取实例状态"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        return {
            "id": instance.id,
            "workflow_name": instance.workflow_name,
            "status": instance.status,
            "started_at": instance.started_at,
            "completed_at": instance.completed_at,
            "current_step": instance.current_step,
            "step_results": instance.step_results,
            "error": instance.error
        }
    
    def save_workflow(self, workflow: Workflow):
        """保存工作流"""
        workflow_file = WORKFLOW_PATH / f"{workflow.name}.json"
        
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump({
                "name": workflow.name,
                "description": workflow.description,
                "steps": [asdict(step) for step in workflow.steps],
                "tags": workflow.tags,
                "created_at": workflow.created_at,
                "updated_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        self.workflows[workflow.name] = workflow

# ============================================================
# MCP 接口
# ============================================================
class MCPInterface:
    """MCP 接口"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
    
    def handle(self, request: Dict) -> Dict:
        """处理 MCP 请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        if action == "list":
            return {"success": True, "workflows": self.engine.list_workflows()}
        
        elif action == "get":
            name = params.get("name")
            workflow = self.engine.get_workflow(name)
            if workflow:
                return {
                    "success": True,
                    "workflow": {
                        "name": workflow.name,
                        "description": workflow.description,
                        "steps": [asdict(step) for step in workflow.steps],
                        "tags": workflow.tags
                    }
                }
            return {"success": False, "error": f"工作流不存在: {name}"}
        
        elif action == "run":
            name = params.get("name")
            workflow_params = params.get("params", {})
            
            instance = self.engine.create_instance(name, workflow_params)
            return {
                "success": True,
                "instance_id": instance.id,
                "status": instance.status,
                "message": f"工作流已启动，实例ID: {instance.id}"
            }
        
        elif action == "status":
            instance_id = params.get("instance_id")
            status = self.engine.get_instance_status(instance_id)
            if status:
                return {"success": True, **status}
            return {"success": False, "error": f"实例不存在: {instance_id}"}
        
        elif action == "create":
            workflow = Workflow(
                name=params.get("name"),
                description=params.get("description", ""),
                steps=[WorkflowStep(**step) for step in params.get("steps", [])],
                tags=params.get("tags", [])
            )
            self.engine.save_workflow(workflow)
            return {"success": True, "message": f"工作流 {workflow.name} 已创建"}
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    engine = WorkflowEngine()
    
    if cmd == "list":
        workflows = engine.list_workflows()
        
        print("可用工作流:")
        print("=" * 80)
        print(f"{'名称':<30} {'步骤':<8} {'标签':<20} {'描述':<30}")
        print("-" * 80)
        
        for w in workflows:
            name = w['name'][:28] if len(w['name']) > 28 else w['name']
            tags = ', '.join(w['tags'])[:18] if w['tags'] else '-'
            desc = w['description'][:28] if len(w['description']) > 28 else w['description']
            print(f"{name:<30} {w['steps_count']:<8} {tags:<20} {desc:<30}")
    
    elif cmd == "run":
        if len(sys.argv) < 3:
            print("用法: unified_workflow.py run <name> [key=value ...]")
            return
        
        name = sys.argv[2]
        params = {}
        
        for arg in sys.argv[3:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                params[key] = value
        
        instance = engine.create_instance(name, params)
        
        print(f"工作流已启动: {name}")
        print(f"实例ID: {instance.id}")
        print(f"状态: {instance.status}")
        print("\n使用以下命令查看状态:")
        print(f"  python unified_workflow.py status {instance.id}")
    
    elif cmd == "status":
        if len(sys.argv) < 3:
            print("用法: unified_workflow.py status <instance_id>")
            return
        
        instance_id = sys.argv[2]
        status = engine.get_instance_status(instance_id)
        
        if status:
            print(f"实例状态: {status['id']}")
            print("=" * 60)
            print(f"工作流: {status['workflow_name']}")
            print(f"状态: {status['status']}")
            print(f"开始时间: {status['started_at']}")
            print(f"完成时间: {status.get('completed_at', '-')}")
            print(f"当前步骤: {status.get('current_step', '-')}")
            
            if status.get('error'):
                print(f"错误: {status['error']}")
            
            print("\n步骤结果:")
            for step_id, result in status['step_results'].items():
                print(f"  步骤 {step_id}: {result}")
        else:
            print(f"实例不存在: {instance_id}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("联合工作流引擎 MCP 已启动")
        
        mcp = MCPInterface()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
