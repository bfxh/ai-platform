#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 智能体系统主入口

功能:
- 启动智能体竞争系统
- 集成GitHub项目
- 管理智能体生命周期

用法:
    python main.py --competition  # 运行智能体竞争
    python main.py --github  # 搜索和集成GitHub项目
    python main.py --help  # 显示帮助信息
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import sys
# 导入智能体相关模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.base import get_agent_manager, AgentType
from agent.examples import DataAnalystAgent, CreativeWriterAgent, CodeGeneratorAgent, GeneralPurposeAgent
from agent.trae_agent import TRAEAgent
from agent.github_integration import GitHubIntegrator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/agent_main.log"), logging.StreamHandler()],
)

# 确保日志目录存在
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)


class AgentSystem:
    """智能体系统"""

    def __init__(self):
        self.logger = logging.getLogger("AgentSystem")
        self.agent_manager = get_agent_manager()
        self.github_integrator = GitHubIntegrator()

    def run_competition(self, rounds: int = 5):
        """运行智能体竞争"""
        self.logger.info(f"启动智能体竞争，共 {rounds} 轮")

        # 注册内置智能体
        self._register_agents()

        # 列出所有智能体
        self._list_agents()

        # 开始竞争
        result = self.agent_manager.start_competition(rounds=rounds)

        # 显示竞争结果
        self._display_competition_results(result)

        # 关闭所有智能体
        self.agent_manager.shutdown_all()

    def search_github_projects(self, max_results: int = 10):
        """搜索GitHub项目"""
        self.logger.info(f"搜索GitHub智能体相关项目，最多 {max_results} 个")

        # 搜索项目
        projects = self.github_integrator.search_agent_projects(max_results=max_results)

        # 显示搜索结果
        self._display_github_projects(projects)

        # 创建集成报告
        report = self.github_integrator.create_integration_report(projects)
        report_path = Path("reports") / "github_projects_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        self.logger.info(f"集成报告已生成: {report_path}")

        return projects

    def discover_models(self):
        """发现本地大模型"""
        self.logger.info("发现本地大模型")

        # 注册智能体
        self._register_agents()

        # 发现模型
        models = self.agent_manager.discover_models()

        # 显示模型信息
        self.logger.info(f"发现 {len(models)} 个本地大模型:")
        for i, model in enumerate(models, 1):
            self.logger.info(f"  {i}. {model['name']} ({model['type']}, {model['size']:.2f} MB)")
            self.logger.info(f"     路径: {model['path']}")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def load_model(self, agent_name: str, model_name: str):
        """为智能体加载大模型"""
        self.logger.info(f"为智能体 {agent_name} 加载模型 {model_name}")

        # 注册智能体
        self._register_agents()

        # 加载模型
        success = self.agent_manager.load_model(agent_name, model_name)

        if success:
            self.logger.info(f"模型加载成功")
        else:
            self.logger.error(f"模型加载失败")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def train_agent(self, agent_name: str):
        """训练智能体"""
        self.logger.info(f"训练智能体 {agent_name}")

        # 注册智能体
        self._register_agents()

        # 生成训练数据
        training_data = [
            {"task_type": "data_analysis", "result": "成功分析了数据集，发现了关键洞察"},
            {"task_type": "problem_solving", "result": "成功解决了复杂问题"},
            {"task_type": "creative_writing", "result": "生成了高质量的创意内容"},
            {"task_type": "code_generation", "result": "生成了高效的代码解决方案"}
        ]

        # 训练智能体
        success = self.agent_manager.train_agent(agent_name, training_data)

        if success:
            self.logger.info(f"智能体训练成功")
        else:
            self.logger.error(f"智能体训练失败")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def optimize_memory_all(self):
        """优化所有智能体的内存使用"""
        self.logger.info("优化所有智能体的内存使用")

        # 注册智能体
        self._register_agents()

        # 优化内存
        success = self.agent_manager.optimize_memory_all()

        if success:
            self.logger.info("内存优化成功")
        else:
            self.logger.error("内存优化失败")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def list_agents_from_db(self):
        """从数据库列出所有智能体"""
        self.logger.info("从数据库列出所有智能体")

        # 从数据库获取智能体列表
        agents = self.agent_manager.list_agents_from_db()

        # 显示智能体信息
        self.logger.info(f"数据库中共有 {len(agents)} 个智能体:")
        for i, agent in enumerate(agents, 1):
            self.logger.info(f"  {i}. {agent['name']}")
            self.logger.info(f"     等级: {agent['level']}, 经验值: {agent['experience']}")
            self.logger.info(f"     胜负: {agent['wins']}胜 {agent['losses']}负")
            self.logger.info(f"     能力: {agent['abilities']}")

    def list_models_from_db(self):
        """从数据库列出所有大模型"""
        self.logger.info("从数据库列出所有大模型")

        # 从数据库获取模型列表
        models = self.agent_manager.list_models_from_db()

        # 显示模型信息
        self.logger.info(f"数据库中共有 {len(models)} 个大模型:")
        for i, model in enumerate(models, 1):
            self.logger.info(f"  {i}. {model['name']}")
            self.logger.info(f"     类型: {model['type']}, 大小: {model['size']:.2f} MB")
            self.logger.info(f"     使用次数: {model['used_count']}")
            self.logger.info(f"     路径: {model['path']}")

    def get_agent_history(self, agent_name: str):
        """获取智能体历史记录"""
        self.logger.info(f"获取智能体 {agent_name} 的历史记录")

        # 从数据库获取智能体历史
        history = self.agent_manager.get_agent_history(agent_name)

        # 显示历史信息
        agent = history.get("agent")
        if agent:
            self.logger.info(f"智能体: {agent['name']}")
            self.logger.info(f"等级: {agent['level']}, 经验值: {agent['experience']}")
            self.logger.info(f"能力: {agent['abilities']}")

        training_history = history.get("training_history", [])
        self.logger.info(f"训练记录: {len(training_history)} 条")
        for i, training in enumerate(training_history[:3], 1):  # 只显示最近3条
            self.logger.info(f"  {i}. 时间: {training['timestamp']}, 成功: {training['success']}")

        evolution_history = history.get("evolution_history", [])
        self.logger.info(f"进化记录: {len(evolution_history)} 条")
        for i, evolution in enumerate(evolution_history[:3], 1):  # 只显示最近3条
            self.logger.info(f"  {i}. 时间: {evolution['timestamp']}, 融合: {evolution['loser']}")

    def start_tra_e_agent(self):
        """启动TRAE控制智能体"""
        self.logger.info("启动 TRAE 控制智能体")

        try:
            from agent.trae_control import get_tra_e_agent
            trae_agent = get_tra_e_agent()

            self.logger.info("TRAE 控制智能体启动成功")
            self.logger.info("可用命令:")
            self.logger.info("  --trae-task read_file:file_path - 读取文件")
            self.logger.info("  --trae-task write_file:file_path:content - 写入文件")
            self.logger.info("  --trae-task execute_command:command - 执行命令")
            self.logger.info("  --trae-task list_directory:path - 列出目录")
            self.logger.info("  --trae-task create_directory:path - 创建目录")
            self.logger.info("  --trae-task search_files:path:pattern - 搜索文件")
            self.logger.info("  --trae-task web_search:query - Web搜索")

        except Exception as e:
            self.logger.error(f"启动 TRAE 控制智能体失败: {e}")

    def execute_tra_e_task(self, task_type: str, params: str):
        """执行TRAE任务"""
        self.logger.info(f"执行 TRAE 任务: {task_type}")

        try:
            from agent.trae_control import get_tra_e_agent
            trae_agent = get_tra_e_agent()

            # 解析参数
            task_params = params.split(":")
            task = {"type": task_type}

            if task_type == "read_file":
                task["file_path"] = task_params[0]
            elif task_type == "write_file":
                task["file_path"] = task_params[0]
                task["content"] = ":".join(task_params[1:])
            elif task_type == "execute_command":
                task["command"] = ":".join(task_params)
            elif task_type == "list_directory":
                task["path"] = task_params[0]
            elif task_type == "create_directory":
                task["path"] = task_params[0]
            elif task_type == "search_files":
                task["path"] = task_params[0]
                task["pattern"] = task_params[1]
            elif task_type == "web_search":
                task["query"] = ":".join(task_params)
            else:
                self.logger.error(f"未知任务类型: {task_type}")
                return

            # 执行任务
            result = trae_agent.handle_task(task)

            # 显示结果
            if result["success"]:
                self.logger.info(f"任务执行成功: {task_type}")
                if "content" in result:
                    self.logger.info(f"内容: {result['content']}")
                elif "output" in result:
                    self.logger.info(f"输出: {result['output']}")
                elif "entries" in result:
                    self.logger.info(f"条目: {result['entries']}")
                elif "files" in result:
                    self.logger.info(f"文件: {result['files']}")
                elif "results" in result:
                    self.logger.info(f"结果: {result['results']}")
            else:
                self.logger.error(f"任务执行失败: {result['error']}")

        except Exception as e:
            self.logger.error(f"执行 TRAE 任务失败: {e}")

    def execute_trae_command(self, command: str):
        """执行 TRAE 命令"""
        self.logger.info(f"执行 TRAE 命令: {command}")

        # 注册智能体
        self._register_agents()

        # 获取 TRAE 智能体
        trae_agent = self.agent_manager.get("trae_controller")
        if trae_agent:
            # 执行命令
            result = trae_agent.execute({"task_type": "trae_command", "command": command})
            self.logger.info(f"命令执行结果: {'成功' if result['success'] else '失败'}")
            self.logger.info(f"结果: {result['result']}")
        else:
            self.logger.error("TRAE 智能体未找到")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def run_script(self, script_path: str):
        """运行脚本"""
        self.logger.info(f"运行脚本: {script_path}")

        # 注册智能体
        self._register_agents()

        # 获取 TRAE 智能体
        trae_agent = self.agent_manager.get("trae_controller")
        if trae_agent:
            # 执行脚本
            result = trae_agent.execute({"task_type": "run_script", "script_path": script_path})
            self.logger.info(f"脚本执行结果: {'成功' if result['success'] else '失败'}")
            self.logger.info(f"输出: {result['result']}")
        else:
            self.logger.error("TRAE 智能体未找到")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def file_operation(self, operation_str: str):
        """文件操作"""
        self.logger.info(f"文件操作: {operation_str}")

        # 解析操作参数
        parts = operation_str.split(":", 2)
        if len(parts) < 2:
            self.logger.error("文件操作格式错误，正确格式: operation:file_path:content")
            return

        operation = parts[0]
        file_path = parts[1]
        content = parts[2] if len(parts) > 2 else None

        # 注册智能体
        self._register_agents()

        # 获取 TRAE 智能体
        trae_agent = self.agent_manager.get("trae_controller")
        if trae_agent:
            # 执行文件操作
            result = trae_agent.execute({
                "task_type": "file_operation",
                "operation": operation,
                "file_path": file_path,
                "content": content
            })
            self.logger.info(f"文件操作结果: {'成功' if result['success'] else '失败'}")
            self.logger.info(f"消息: {result['result']}")
        else:
            self.logger.error("TRAE 智能体未找到")

        # 关闭智能体
        self.agent_manager.shutdown_all()

    def execute_workflow(self, workflow_str: str):
        """执行工作流"""
        self.logger.info(f"执行工作流: {workflow_str}")

        # 解析工作流参数
        parts = workflow_str.split(":", 1)
        if len(parts) < 1:
            self.logger.error("工作流格式错误，正确格式: workflow_name:parameters")
            return

        workflow_name = parts[0]
        parameters = parts[1] if len(parts) > 1 else "{}"

        try:
            import json
            parameters = json.loads(parameters) if parameters else {}
        except (json.JSONDecodeError, TypeError):
            parameters = {}

        # 注册智能体
        self._register_agents()

        # 获取 TRAE 智能体
        trae_agent = self.agent_manager.get("trae_controller")
        if trae_agent:
            # 执行工作流
            result = trae_agent.execute({
                "task_type": "workflow_execution",
                "workflow_name": workflow_name,
                "parameters": parameters
            })
            self.logger.info(f"工作流执行结果: {'成功' if result['success'] else '失败'}")
            self.logger.info(f"输出: {result['result']}")
        else:
            self.logger.error("TRAE 智能体未找到")

        # 关闭智能体
        self.agent_manager.shutdown_all()


    def integrate_github_projects(self, projects: List[Dict[str, Any]]):
        """集成GitHub项目"""
        self.logger.info(f"集成 {len(projects)} 个GitHub项目")

        for project in projects:
            self.logger.info(f"集成项目: {project['full_name']}")
            result = self.github_integrator.integrate_project(project['full_name'])

            if result['success']:
                self.logger.info(f"项目集成成功: {project['full_name']}")
                self.logger.info(f"克隆路径: {result['clone_path']}")
            else:
                self.logger.error(f"项目集成失败: {project['full_name']}, 错误: {result.get('error')}")

    def _register_agents(self):
        """注册智能体"""
        # 注册内置智能体
        agents = [
            DataAnalystAgent(),
            CreativeWriterAgent(),
            CodeGeneratorAgent(),
            GeneralPurposeAgent(),
            TRAEAgent()
        ]

        for agent in agents:
            self.agent_manager.register(agent)

        # 注册从GitHub集成的智能体（如果有）
        self._register_external_agents()

    def _register_external_agents(self):
        """注册外部智能体"""
        external_dir = Path(__file__).parent / "external"
        if external_dir.exists():
            for repo_dir in external_dir.iterdir():
                if repo_dir.is_dir():
                    # 尝试导入智能体
                    try:
                        sys.path.insert(0, str(repo_dir))
                        # 这里可以根据具体项目结构调整导入逻辑
                        # 例如：from some_module import SomeAgent
                        # self.agent_manager.register(SomeAgent())
                    except Exception as e:
                        self.logger.warning(f"无法导入外部智能体: {repo_dir}, 错误: {e}")

    def _list_agents(self):
        """列出所有智能体"""
        agents = self.agent_manager.list_agents()
        self.logger.info(f"注册了 {len(agents)} 个智能体:")
        for agent in agents:
            self.logger.info(f"  - {agent.name}: {agent.description} (等级: {agent.level}, 类型: {agent.agent_type.value})")

    def _display_competition_results(self, result: Dict[str, Any]):
        """显示竞争结果"""
        if result.get("success"):
            self.logger.info("智能体竞争结果:")
            self.logger.info("排名:")
            for i, rank in enumerate(result['rankings'], 1):
                self.logger.info(f"  {i}. {rank['name']} - 胜率: {rank['win_rate']:.2f}%, 等级: {rank['level']}")

            # 显示进化历史
            evolution_history = self.agent_manager.get_evolution_history()
            if evolution_history:
                self.logger.info("进化历史:")
                for evolution in evolution_history:
                    self.logger.info(f"  - {evolution['winner']} 融合了 {evolution['loser']}")
        else:
            self.logger.error(f"竞争失败: {result.get('error')}")

    def _display_github_projects(self, projects: List[Dict[str, Any]]):
        """显示GitHub项目"""
        self.logger.info(f"找到 {len(projects)} 个智能体相关项目:")
        for i, project in enumerate(projects, 1):
            self.logger.info(f"  {i}. {project['full_name']} (★{project['stars']}, 📁{project['forks']})")
            self.logger.info(f"     描述: {project['description']}")
            self.logger.info(f"     URL: {project['html_url']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Core 智能体系统")
    parser.add_argument("--competition", action="store_true", help="运行智能体竞争")
    parser.add_argument("--github", action="store_true", help="搜索和集成GitHub项目")
    parser.add_argument("--models", action="store_true", help="发现本地大模型")
    parser.add_argument("--load-model", type=str, help="为智能体加载大模型，格式: agent_name:model_name")
    parser.add_argument("--train", type=str, help="训练智能体，格式: agent_name")
    parser.add_argument("--optimize-memory", action="store_true", help="优化所有智能体的内存使用")
    parser.add_argument("--db-agents", action="store_true", help="从数据库列出所有智能体")
    parser.add_argument("--db-models", action="store_true", help="从数据库列出所有大模型")
    parser.add_argument("--agent-history", type=str, help="获取智能体历史记录，格式: agent_name")
    parser.add_argument("--trae", action="store_true", help="启动TRAE控制智能体")
    parser.add_argument("--trae-task", type=str, help="执行TRAE任务，格式: type:params")
    parser.add_argument("--trae-command", type=str, help="执行 TRAE 命令，格式: command")
    parser.add_argument("--run-script", type=str, help="运行脚本，格式: script_path")
    parser.add_argument("--file-operation", type=str, help="文件操作，格式: operation:file_path:content")
    parser.add_argument("--workflow", type=str, help="执行工作流，格式: workflow_name:parameters")
    parser.add_argument("--rounds", type=int, default=5, help="竞争轮数")
    parser.add_argument("--max-results", type=int, default=10, help="GitHub搜索结果数量")
    parser.add_argument("--integrate", action="store_true", help="集成搜索到的GitHub项目")

    args = parser.parse_args()

    system = AgentSystem()

    if args.competition:
        # 运行智能体竞争
        system.run_competition(rounds=args.rounds)
    elif args.github:
        # 搜索GitHub项目
        projects = system.search_github_projects(max_results=args.max_results)
        if args.integrate and projects:
            # 集成前3个项目
            system.integrate_github_projects(projects[:3])
    elif args.models:
        # 发现本地大模型
        system.discover_models()
    elif args.load_model:
        # 为智能体加载大模型
        agent_name, model_name = args.load_model.split(":")
        system.load_model(agent_name, model_name)
    elif args.train:
        # 训练智能体
        system.train_agent(args.train)
    elif args.optimize_memory:
        # 优化内存使用
        system.optimize_memory_all()
    elif args.db_agents:
        # 从数据库列出所有智能体
        system.list_agents_from_db()
    elif args.db_models:
        # 从数据库列出所有大模型
        system.list_models_from_db()
    elif args.agent_history:
        # 获取智能体历史记录
        system.get_agent_history(args.agent_history)
    elif args.trae:
        # 启动TRAE控制智能体
        system.start_tra_e_agent()
    elif args.trae_task:
        # 执行TRAE任务
        task_type, params = args.trae_task.split(":", 1)
        system.execute_tra_e_task(task_type, params)
    elif args.trae_command:
        # 执行 TRAE 命令
        system.execute_trae_command(args.trae_command)
    elif args.run_script:
        # 运行脚本
        system.run_script(args.run_script)
    elif args.file_operation:
        # 文件操作
        system.file_operation(args.file_operation)
    elif args.workflow:
        # 执行工作流
        system.execute_workflow(args.workflow)
    else:
        # 显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()
