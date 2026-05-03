#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - TRAE 操控智能体

功能:
- 与 TRAE IDE 交互
- 调用 TRAE 的 MCP 工具
- 执行 \python 目录下的脚本和工具
- 管理 TRAE 工作流程

用法:
    from agent.trae_agent import TRAEAgent

    trae_agent = TRAEAgent()
    trae_agent.execute({"task_type": "trae_command", "command": "列出 \python 目录"})
"""

import random
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional

import sys
# 导入智能体基类
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.base import Agent, AgentType, get_agent_manager


class TRAEAgent(Agent):
    """TRAE 操控智能体"""

    name = "trae_controller"
    description = "TRAE 操控智能体 - 擅长与 TRAE IDE 交互和执行各种操作"
    version = "1.0.0"
    author = "MCP Core"
    agent_type = AgentType.SPECIALIZED
    skills = ["system_optimizer", "github_opensource"]
    abilities = {
        "trae_control": 95,
        "command_execution": 90,
        "file_management": 85,
        "workflow_management": 90,
        "speed": 80
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # TRAE 相关路径
        self.trae_config_dir = Path.home() / "AppData" / "Roaming" / "Trae CN" / "User"
        # 确保使用正确的绝对路径
        self.ai_dir = Path("/python").resolve()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        task_type = task.get("task_type")
        difficulty = task.get("difficulty", 1)

        # 模拟执行时间
        execution_time = random.uniform(3, 8) * (difficulty / 5)

        if task_type == "trae_command":
            # 执行 TRAE 相关命令
            command = task.get("command")
            if command:
                result = self._execute_trae_command(command)
                success = result.get("success", False)
                return {
                    "success": success,
                    "result": result.get("output", ""),
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }
            else:
                return {
                    "success": False,
                    "result": "缺少命令参数",
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }

        elif task_type == "run_script":
            # 运行 \python 目录下的脚本
            script_path = task.get("script_path")
            args = task.get("args", [])
            if script_path:
                result = self._run_script(script_path, args)
                success = result.get("success", False)
                return {
                    "success": success,
                    "result": result.get("output", ""),
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }
            else:
                return {
                    "success": False,
                    "result": "缺少脚本路径",
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }

        elif task_type == "file_operation":
            # 文件操作
            operation = task.get("operation")
            file_path = task.get("file_path")
            content = task.get("content")
            if operation and file_path:
                result = self._file_operation(operation, file_path, content)
                success = result.get("success", False)
                return {
                    "success": success,
                    "result": result.get("message", ""),
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }
            else:
                return {
                    "success": False,
                    "result": "缺少操作类型或文件路径",
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }

        elif task_type == "workflow_execution":
            # 执行工作流
            workflow_name = task.get("workflow_name")
            parameters = task.get("parameters", {})
            if workflow_name:
                result = self._execute_workflow(workflow_name, parameters)
                success = result.get("success", False)
                return {
                    "success": success,
                    "result": result.get("output", ""),
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }
            else:
                return {
                    "success": False,
                    "result": "缺少工作流名称",
                    "execution_time": execution_time,
                    "agent_type": self.agent_type.value
                }

        else:
            # 其他任务
            success = random.random() > 0.2  # 80% 的成功率
            result = f"{self.name} 尝试完成 {task_type} 任务，{'成功' if success else '失败'}"
            return {
                "success": success,
                "result": result,
                "execution_time": execution_time,
                "agent_type": self.agent_type.value
            }

    def _execute_trae_command(self, command: str) -> Dict[str, Any]:
        """执行 TRAE 相关命令"""
        try:
            self.logger.info(f"执行 TRAE 命令: {command}")

            # 这里可以根据命令类型执行不同的操作
            if "列出" in command and ("目录" in command or "文件夹" in command):
                # 列出目录
                try:
                    files = []
                    for item in self.ai_dir.iterdir():
                        if item.is_file():
                            files.append(f"[FILE] {item.name}")
                        else:
                            files.append(f"[DIR] {item.name}")
                    output = "\n".join(files[:50])  # 最多显示50个项目
                    return {"success": True, "output": output}
                except Exception as e:
                    self.logger.error(f"列出目录失败: {e}")
                    return {"success": False, "output": f"列出目录失败: {str(e)}"}

            elif "创建" in command and "文件" in command:
                # 创建文件
                if "测试" in command:
                    test_file = self.ai_dir / "test_trae_agent.txt"
                    test_file.write_text("TRAE 智能体测试文件\n创建时间: " + self._get_current_time())
                    return {"success": True, "output": f"成功创建测试文件: {test_file}"}

            elif "查看" in command and "配置" in command:
                # 查看 TRAE 配置
                mcp_config = self.trae_config_dir / "mcp.json"
                if mcp_config.exists():
                    content = mcp_config.read_text()
                    return {"success": True, "output": content[:1000] + "..." if len(content) > 1000 else content}
                else:
                    return {"success": False, "output": "TRAE 配置文件不存在"}

            else:
                # 默认处理
                return {"success": True, "output": f"执行命令: {command}"}

        except Exception as e:
            self.logger.error(f"执行 TRAE 命令失败: {e}")
            return {"success": False, "output": f"执行失败: {str(e)}"}

    def _run_script(self, script_path: str, args: list) -> Dict[str, Any]:
        """运行 /python 目录下的脚本"""
        try:
            # 构建完整路径
            if not script_path.startswith("D:\\") and not script_path.startswith("d:\\"):
                script_path = str(self.ai_dir / script_path)

            script_file = Path(script_path)
            if not script_file.exists():
                return {"success": False, "output": f"脚本不存在: {script_path}"}

            # 构建命令
            if script_file.suffix == ".py":
                cmd = ["python", str(script_file)] + args
            elif script_file.suffix == ".ps1":
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_file)] + args
            elif script_file.suffix == ".bat":
                cmd = ["cmd", "/c", str(script_file)] + args
            else:
                return {"success": False, "output": f"不支持的脚本类型: {script_file.suffix}"}

            self.logger.info(f"运行脚本: {' '.join(cmd)}")

            # 执行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.ai_dir)
            )

            output = result.stdout + (result.stderr if result.stderr else "")
            success = result.returncode == 0

            return {"success": success, "output": output[:2000] + "..." if len(output) > 2000 else output}

        except Exception as e:
            self.logger.error(f"运行脚本失败: {e}")
            return {"success": False, "output": f"运行失败: {str(e)}"}

    def _file_operation(self, operation: str, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """文件操作"""
        try:
            # 构建完整路径
            if not file_path.startswith("D:\\") and not file_path.startswith("d:\\"):
                file_path = str(self.ai_dir / file_path)

            file = Path(file_path)

            if operation == "read":
                # 读取文件
                if file.exists():
                    file_content = file.read_text()
                    return {"success": True, "message": file_content[:2000] + "..." if len(file_content) > 2000 else file_content}
                else:
                    return {"success": False, "message": f"文件不存在: {file_path}"}

            elif operation == "write":
                # 写入文件
                if content is not None:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.write_text(content)
                    return {"success": True, "message": f"成功写入文件: {file_path}"}
                else:
                    return {"success": False, "message": "缺少文件内容"}

            elif operation == "delete":
                # 删除文件
                if file.exists():
                    file.unlink()
                    return {"success": True, "message": f"成功删除文件: {file_path}"}
                else:
                    return {"success": False, "message": f"文件不存在: {file_path}"}

            elif operation == "copy":
                # 复制文件
                destination = content  # 假设 content 是目标路径
                if destination:
                    if not destination.startswith("D:\\") and not destination.startswith("d:\\"):
                        destination = str(self.ai_dir / destination)
                    dest_file = Path(destination)
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    dest_file.write_bytes(file.read_bytes())
                    return {"success": True, "message": f"成功复制文件到: {destination}"}
                else:
                    return {"success": False, "message": "缺少目标路径"}

            else:
                return {"success": False, "message": f"不支持的操作类型: {operation}"}

        except Exception as e:
            self.logger.error(f"文件操作失败: {e}")
            return {"success": False, "message": f"操作失败: {str(e)}"}

    def _execute_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        try:
            self.logger.info(f"执行工作流: {workflow_name}, 参数: {parameters}")

            # 工作流映射
            workflows = {
                "auto_transfer": {
                    "script": "auto_transfer.py",
                    "description": "自动文件传输"
                },
                "high_speed_transfer": {
                    "script": "high_speed_transfer.py",
                    "description": "高速文件传输"
                },
                "workflow_runner": {
                    "script": "workflow_runner.py",
                    "description": "工作流运行器"
                },
                "auto_receiver": {
                    "script": "auto_receiver.py",
                    "description": "传输接收端"
                }
            }

            if workflow_name in workflows:
                workflow = workflows[workflow_name]
                script_path = workflow["script"]
                # 运行工作流脚本
                result = self._run_script(script_path, [json.dumps(parameters)])
                return result
            else:
                return {"success": False, "output": f"工作流不存在: {workflow_name}"}

        except Exception as e:
            self.logger.error(f"执行工作流失败: {e}")
            return {"success": False, "output": f"执行失败: {str(e)}"}

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _enhance_abilities(self) -> None:
        """升级时增强能力"""
        # 增强 TRAE 控制能力
        self.abilities["trae_control"] = min(self.abilities["trae_control"] + 3, 100)
        # 增强命令执行能力
        self.abilities["command_execution"] = min(self.abilities["command_execution"] + 2, 100)
        # 增强文件管理能力
        self.abilities["file_management"] = min(self.abilities["file_management"] + 2, 100)
        # 增强工作流管理能力
        self.abilities["workflow_management"] = min(self.abilities["workflow_management"] + 3, 100)


def run_trae_agent_example():
    """运行 TRAE 智能体示例"""
    print("=" * 80)
    print("TRAE 智能体示例")
    print("=" * 80)

    # 获取智能体管理器
    manager = get_agent_manager()

    # 创建并注册 TRAE 智能体
    trae_agent = TRAEAgent()
    manager.register(trae_agent)

    # 列出所有智能体
    print("\n注册的智能体:")
    for info in manager.list_agents():
        print(f"  - {info.name}: {info.description} (等级: {info.level}, 类型: {info.agent_type.value})")
        print(f"    能力: {info.abilities}")
        print(f"    技能: {info.skills}")

    # 测试 TRAE 命令
    print("\n测试 TRAE 命令:")
    tasks = [
        {
            "task_type": "trae_command",
            "command": "列出 \python 目录"
        },
        {
            "task_type": "trae_command",
            "command": "创建测试文件"
        },
        {
            "task_type": "trae_command",
            "command": "查看 TRAE 配置"
        }
    ]

    for task in tasks:
        print(f"\n执行任务: {task['command']}")
        result = trae_agent.execute(task)
        print(f"  成功: {result['success']}")
        print(f"  结果: {result['result']}")

    # 测试运行脚本
    print("\n测试运行脚本:")
    script_task = {
        "task_type": "run_script",
        "script_path": "test_skills.py"
    }
    result = trae_agent.execute(script_task)
    print(f"执行脚本结果: {result['success']}")
    print(f"输出: {result['result'][:500]}...")

    # 测试文件操作
    print("\n测试文件操作:")
    file_task = {
        "task_type": "file_operation",
        "operation": "write",
        "file_path": "trae_agent_test.txt",
        "content": "这是 TRAE 智能体测试文件\n由 TRAE 智能体创建"
    }
    result = trae_agent.execute(file_task)
    print(f"写入文件结果: {result['success']}")
    print(f"消息: {result['result']}")

    # 测试工作流执行
    print("\n测试工作流执行:")
    workflow_task = {
        "task_type": "workflow_execution",
        "workflow_name": "auto_transfer",
        "parameters": {"source": "/python", "destination": "/python\backups"}
    }
    result = trae_agent.execute(workflow_task)
    print(f"执行工作流结果: {result['success']}")
    print(f"输出: {result['result'][:500]}...")

    # 关闭所有智能体
    manager.shutdown_all()
    print("\nTRAE 智能体示例完成")
    print("=" * 80)


if __name__ == "__main__":
    # 运行 TRAE 智能体示例
    run_trae_agent_example()
