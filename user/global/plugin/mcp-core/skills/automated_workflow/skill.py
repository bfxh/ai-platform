#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化工作流技能
用于自动执行一系列任务，如搜索GitHub项目、克隆项目、运行测试等
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill

class AutomatedWorkflowSkill(Skill):
    """自动化工作流技能"""

    name = "automated_workflow"
    description = "自动化工作流 - 自动执行一系列任务，如搜索GitHub项目、克隆项目、运行测试等"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.workflows_dir = self.config.get("workflows_dir", "workflows")
        self.logs_dir = self.config.get("logs_dir", "workflow_logs")
        self.default_workflow = self.config.get("default_workflow", "github_project_search")
        
        # 确保目录存在
        os.makedirs(self.workflows_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def _load_workflow(self, workflow_name: str) -> Optional[Dict]:
        """加载工作流配置"""
        workflow_file = os.path.join(self.workflows_dir, f"{workflow_name}.json")
        
        if not os.path.exists(workflow_file):
            self.logger.error(f"工作流文件不存在: {workflow_file}")
            return None
        
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                workflow = json.load(f)
            return workflow
        except Exception as e:
            self.logger.error(f"加载工作流失败: {e}")
            return None

    def _save_workflow(self, workflow_name: str, workflow: Dict) -> bool:
        """保存工作流配置"""
        workflow_file = os.path.join(self.workflows_dir, f"{workflow_name}.json")
        
        try:
            with open(workflow_file, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            self.logger.info(f"工作流已保存: {workflow_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存工作流失败: {e}")
            return False

    def _execute_step(self, step: Dict, context: Dict) -> Dict:
        """执行单个工作流步骤"""
        step_name = step.get("name", "unknown")
        step_type = step.get("type", "shell")
        
        self.logger.info(f"执行步骤: {step_name} ({step_type})")
        
        try:
            if step_type == "shell":
                # 执行shell命令
                command = step.get("command")
                if not command:
                    return {"success": False, "error": "缺少command参数"}
                
                # 替换上下文变量
                for key, value in context.items():
                    command = command.replace(f"${{{key}}}", str(value))
                
                # 执行命令
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                output = result.stdout + result.stderr
                success = result.returncode == 0
                
                return {
                    "success": success,
                    "output": output,
                    "returncode": result.returncode
                }
            
            elif step_type == "skill":
                # 执行技能命令
                skill_name = step.get("skill")
                skill_command = step.get("command")
                skill_params = step.get("params", {})
                
                if not skill_name or not skill_command:
                    return {"success": False, "error": "缺少skill或command参数"}
                
                # 替换上下文变量
                for key, value in context.items():
                    for param_name, param_value in skill_params.items():
                        if isinstance(param_value, str):
                            skill_params[param_name] = param_value.replace(f"${{{key}}}", str(value))
                
                # 导入并执行技能
                try:
                    # 动态导入技能
                    skill_module = __import__(f"skills.{skill_name}", fromlist=["get_skill"])
                    skill_class = skill_module.get_skill()
                    skill_instance = skill_class()
                    
                    # 执行技能命令
                    result = skill_instance.execute(skill_command, **skill_params)
                    
                    # 检查结果
                    if isinstance(result, dict) and result.get("success", True):
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": str(result)}
                except Exception as e:
                    return {"success": False, "error": f"执行技能失败: {e}"}
            
            elif step_type == "python":
                # 执行Python代码
                code = step.get("code")
                if not code:
                    return {"success": False, "error": "缺少code参数"}
                
                # 替换上下文变量
                for key, value in context.items():
                    code = code.replace(f"${{{key}}}", str(value))
                
                # 执行代码
                local_vars = {"context": context, "logger": self.logger}
                try:
                    exec(code, globals(), local_vars)
                    return {"success": True, "result": local_vars.get("result")}
                except Exception as e:
                    return {"success": False, "error": f"执行Python代码失败: {e}"}
            
            else:
                return {"success": False, "error": f"未知的步骤类型: {step_type}"}
                
        except Exception as e:
            self.logger.error(f"执行步骤失败: {e}")
            return {"success": False, "error": str(e)}

    def _execute_workflow(self, workflow: Dict, context: Dict = None) -> Dict:
        """执行工作流"""
        workflow_name = workflow.get("name", "unnamed")
        steps = workflow.get("steps", [])
        
        self.logger.info(f"开始执行工作流: {workflow_name}")
        
        # 初始化上下文
        if context is None:
            context = {}
        
        # 添加默认上下文
        context["workflow_name"] = workflow_name
        context["timestamp"] = datetime.now().isoformat()
        context["workflows_dir"] = self.workflows_dir
        context["logs_dir"] = self.logs_dir
        
        # 执行步骤
        results = []
        success = True
        
        for i, step in enumerate(steps):
            step_name = step.get("name", f"step_{i}")
            self.logger.info(f"执行第 {i+1} 步: {step_name}")
            
            # 执行步骤
            result = self._execute_step(step, context)
            results.append({
                "step": step_name,
                "result": result
            })
            
            # 检查结果
            if not result.get("success", False):
                self.logger.error(f"步骤 {step_name} 失败: {result.get('error')}")
                success = False
                
                # 检查是否继续执行
                if step.get("continue_on_error", False):
                    self.logger.info("继续执行后续步骤")
                else:
                    break
            
            # 更新上下文
            if "result" in result:
                context[f"step_{i}_result"] = result["result"]
            
            # 步骤间延迟
            if step.get("delay", 0) > 0:
                delay = step.get("delay")
                self.logger.info(f"延迟 {delay} 秒")
                time.sleep(delay)
        
        # 生成工作流报告
        report = {
            "workflow_name": workflow_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "steps": results,
            "context": context
        }
        
        # 保存日志
        log_file = os.path.join(
            self.logs_dir,
            f"workflow_{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"工作流日志已保存: {log_file}")
        except Exception as e:
            self.logger.error(f"保存工作流日志失败: {e}")
        
        return report

    def create_workflow(self, name: str, steps: List[Dict], description: str = "") -> Dict:
        """创建工作流"""
        workflow = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        
        if self._save_workflow(name, workflow):
            return {
                "success": True,
                "message": f"工作流 {name} 创建成功"
            }
        else:
            return {
                "success": False,
                "error": "创建工作流失败"
            }

    def list_workflows(self) -> Dict:
        """列出所有工作流"""
        workflows = []
        
        for file in os.listdir(self.workflows_dir):
            if file.endswith(".json"):
                workflow_name = file.replace(".json", "")
                workflow_file = os.path.join(self.workflows_dir, file)
                
                try:
                    with open(workflow_file, "r", encoding="utf-8") as f:
                        workflow = json.load(f)
                    workflows.append({
                        "name": workflow_name,
                        "description": workflow.get("description", ""),
                        "steps": len(workflow.get("steps", [])),
                        "created_at": workflow.get("created_at", "")
                    })
                except Exception as e:
                    self.logger.error(f"读取工作流文件失败: {e}")
        
        return {
            "success": True,
            "workflows": workflows
        }

    def execute(self, command: str, **kwargs) -> Any:
        """执行技能命令"""
        if command == "run":
            workflow_name = kwargs.get("workflow") or self.default_workflow
            context = kwargs.get("context", {})
            
            # 加载工作流
            workflow = self._load_workflow(workflow_name)
            if not workflow:
                return "错误: 工作流不存在"
            
            # 执行工作流
            return self._execute_workflow(workflow, context)
        
        elif command == "create":
            name = kwargs.get("name")
            steps = kwargs.get("steps")
            description = kwargs.get("description", "")
            
            if not name or not steps:
                return "错误: 缺少 name 或 steps 参数"
            
            return self.create_workflow(name, steps, description)
        
        elif command == "list":
            return self.list_workflows()
        
        elif command == "create-github-search-workflow":
            # 创建GitHub项目搜索工作流
            workflow_name = kwargs.get("name", "github_search")
            query = kwargs.get("query", "python machine learning")
            sort = kwargs.get("sort", "stars")
            per_page = kwargs.get("per_page", 10)
            min_stars = kwargs.get("min_stars", 1000)
            
            # 构建工作流步骤
            steps = [
                {
                    "name": "搜索GitHub项目",
                    "type": "skill",
                    "skill": "github_project_search",
                    "command": "search",
                    "params": {
                        "query": query,
                        "sort": sort,
                        "per_page": per_page
                    }
                },
                {
                    "name": "过滤项目",
                    "type": "skill",
                    "skill": "github_project_search",
                    "command": "filter",
                    "params": {
                        "projects": "${step_0_result.items}",
                        "min_stars": min_stars
                    }
                },
                {
                    "name": "生成项目报告",
                    "type": "skill",
                    "skill": "github_project_search",
                    "command": "generate-report",
                    "params": {
                        "projects": "${step_1_result}"
                    }
                }
            ]
            
            return self.create_workflow(
                workflow_name,
                steps,
                f"GitHub项目搜索工作流: {query}"
            )
        
        else:
            return "无效的命令，请使用以下命令: run, create, list, create-github-search-workflow"

    def get_info(self) -> Dict:
        """获取技能信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "commands": [
                {
                    "name": "run",
                    "description": "执行工作流",
                    "parameters": [
                        {
                            "name": "workflow",
                            "type": "string",
                            "required": false,
                            "description": "工作流名称"
                        },
                        {
                            "name": "context",
                            "type": "object",
                            "required": false,
                            "description": "工作流上下文"
                        }
                    ]
                },
                {
                    "name": "create",
                    "description": "创建工作流",
                    "parameters": [
                        {
                            "name": "name",
                            "type": "string",
                            "required": true,
                            "description": "工作流名称"
                        },
                        {
                            "name": "steps",
                            "type": "array",
                            "required": true,
                            "description": "工作流步骤"
                        },
                        {
                            "name": "description",
                            "type": "string",
                            "required": false,
                            "description": "工作流描述"
                        }
                    ]
                },
                {
                    "name": "list",
                    "description": "列出所有工作流"
                },
                {
                    "name": "create-github-search-workflow",
                    "description": "创建GitHub项目搜索工作流",
                    "parameters": [
                        {
                            "name": "name",
                            "type": "string",
                            "required": false,
                            "description": "工作流名称"
                        },
                        {
                            "name": "query",
                            "type": "string",
                            "required": false,
                            "description": "搜索查询"
                        },
                        {
                            "name": "sort",
                            "type": "string",
                            "required": false,
                            "description": "排序字段"
                        },
                        {
                            "name": "per_page",
                            "type": "integer",
                            "required": false,
                            "description": "每页结果数"
                        },
                        {
                            "name": "min_stars",
                            "type": "integer",
                            "required": false,
                            "description": "最小星数"
                        }
                    ]
                }
            ]
        }

# 测试代码
if __name__ == "__main__":
    skill = AutomatedWorkflowSkill()
    
    # 创建GitHub搜索工作流
    result = skill.execute("create-github-search-workflow", 
                         name="ml_projects",
                         query="python machine learning",
                         sort="stars",
                         per_page=10,
                         min_stars=10000)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 运行工作流
    if result.get("success"):
        result = skill.execute("run", workflow="ml_projects")
        print(json.dumps(result, indent=2, ensure_ascii=False))