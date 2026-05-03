#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 命令行工具 (CLI)

功能:
- 技能管理
- 工作流执行
- 系统监控
- 配置管理

用法:
    mcp skill list              # 列出技能
    mcp skill call <name>       # 调用技能
    mcp workflow run <name>     # 运行工作流
    mcp server start            # 启动服务
    mcp status                  # 查看状态
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent))

from server import MCPServer
from logger import get_logger


class MCPCLI:
    """MCP命令行接口"""
    
    def __init__(self):
        self.server: Optional[MCPServer] = None
        self.logger = get_logger("mcp.cli")
    
    def init_server(self):
        """初始化服务器"""
        if self.server is None:
            self.server = MCPServer()
            if not self.server.initialize():
                print("[错误] 服务器初始化失败")
                sys.exit(1)
    
    def skill_list(self, verbose: bool = False):
        """列出技能"""
        self.init_server()
        skills = self.server.list_skills()
        
        if not skills:
            print("暂无技能")
            return
        
        print(f"\n共有 {len(skills)} 个技能:\n")
        print(f"{'名称':<20} {'版本':<10} {'状态':<10} {'描述'}")
        print("-" * 70)
        
        for skill in skills:
            status = "✓" if skill.get('status') == 'ready' else "✗"
            print(f"{skill['name']:<20} {skill['version']:<10} {status:<10} {skill['description'][:30]}")
            
            if verbose and skill.get('parameters'):
                print(f"  参数:")
                for param_name, param_info in skill['parameters'].items():
                    req = "必填" if param_info.get('required') else "可选"
                    print(f"    - {param_name} ({req}): {param_info.get('description', '')}")
                print()
    
    def skill_call(self, name: str, params: str = "{}", output_json: bool = False):
        """调用技能"""
        self.init_server()
        
        try:
            params_dict = json.loads(params)
        except json.JSONDecodeError:
            print(f"[错误] 参数格式错误，必须是有效的 JSON")
            return
        
        print(f"调用技能: {name}")
        print(f"参数: {params_dict}")
        print("-" * 50)
        
        result = self.server.call_skill(name, params_dict)
        
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get('success'):
                print(f"✓ 执行成功")
                if 'result' in result:
                    print(f"结果: {result['result']}")
            else:
                print(f"✗ 执行失败")
                print(f"错误: {result.get('error', '未知错误')}")
    
    def skill_info(self, name: str):
        """查看技能详情"""
        self.init_server()
        
        skill = self.server.skill_registry.get(name)
        if not skill:
            print(f"[错误] 技能不存在: {name}")
            return
        
        info = skill.info
        
        print(f"\n技能详情: {info.name}")
        print("=" * 50)
        print(f"描述: {info.description}")
        print(f"版本: {info.version}")
        print(f"作者: {info.author}")
        print(f"状态: {info.status.value}")
        
        if info.dependencies:
            print(f"\n依赖: {', '.join(info.dependencies)}")
        
        if info.parameters:
            print(f"\n参数:")
            for param_name, param_info in info.parameters.items():
                print(f"  {param_name}:")
                print(f"    类型: {param_info.get('type', 'unknown')}")
                print(f"    必需: {'是' if param_info.get('required') else '否'}")
                print(f"    描述: {param_info.get('description', '')}")
                if 'default' in param_info:
                    print(f"    默认值: {param_info['default']}")
                if 'enum' in param_info:
                    print(f"    可选值: {', '.join(map(str, param_info['enum']))}")
    
    def workflow_list(self):
        """列出工作流"""
        self.init_server()
        workflows = self.server.list_workflows()
        
        if not workflows:
            print("暂无工作流")
            return
        
        print(f"\n共有 {len(workflows)} 个工作流:\n")
        print(f"{'名称':<25} {'版本':<8} {'步骤':<6} {'描述'}")
        print("-" * 70)
        
        for wf in workflows:
            print(f"{wf['name']:<25} {wf['version']:<8} {wf['steps_count']:<6} {wf['description'][:30]}")
    
    def workflow_run(self, name: str, context: str = "{}", verbose: bool = False):
        """运行工作流"""
        self.init_server()
        
        try:
            context_dict = json.loads(context)
        except json.JSONDecodeError:
            print(f"[错误] 上下文格式错误，必须是有效的 JSON")
            return
        
        print(f"运行工作流: {name}")
        if context_dict:
            print(f"上下文: {context_dict}")
        print("-" * 50)
        
        result = self.server.run_workflow(name, context_dict)
        
        if verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result.get('success'):
                print(f"✓ 工作流执行成功")
                print(f"完成步骤: {result.get('completed_steps', 0)}/{result.get('total_steps', 0)}")
            else:
                print(f"✗ 工作流执行失败")
                print(f"错误: {result.get('error', '未知错误')}")
                if result.get('failed_step'):
                    print(f"失败步骤: {result['failed_step']}")
    
    def workflow_show(self, name: str):
        """显示工作流详情"""
        self.init_server()
        
        from workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        workflow = engine.load_workflow(name)
        
        if not workflow:
            print(f"[错误] 工作流不存在: {name}")
            return
        
        print(f"\n工作流: {workflow.name}")
        print("=" * 50)
        print(f"描述: {workflow.description}")
        print(f"版本: {workflow.version}")
        print(f"步骤数: {len(workflow.steps)}")
        
        print(f"\n步骤列表:")
        for i, step in enumerate(workflow.steps, 1):
            deps = f" (依赖: {', '.join(step.depends_on)})" if step.depends_on else ""
            print(f"  {i}. {step.name} [{step.skill}.{step.action}]{deps}")
    
    def server_start(self, host: str = "localhost", port: int = 8766, daemon: bool = False):
        """启动服务器"""
        print(f"启动 MCP Server...")
        print(f"地址: {host}:{port}")
        
        self.init_server()
        
        if daemon:
            print("以守护模式运行")
            # 这里可以实现守护进程逻辑
        
        print("\n服务器已启动，按 Ctrl+C 停止")
        print("可用命令:")
        print("  skills     - 列出技能")
        print("  workflows  - 列出工作流")
        print("  status     - 查看状态")
        print("  quit       - 退出")
        print()
        
        try:
            while True:
                try:
                    cmd = input("> ").strip()
                    
                    if cmd == 'quit' or cmd == 'exit':
                        break
                    elif cmd == 'skills':
                        self.skill_list()
                    elif cmd == 'workflows':
                        self.workflow_list()
                    elif cmd == 'status':
                        self.status()
                    elif cmd:
                        print(f"未知命令: {cmd}")
                except KeyboardInterrupt:
                    break
        finally:
            self.server.shutdown()
            print("\n服务器已停止")
    
    def status(self):
        """查看系统状态"""
        self.init_server()
        status = self.server.get_status()
        
        print("\nMCP Core 系统状态")
        print("=" * 50)
        print(f"版本: {status['version']}")
        print(f"状态: {status['status']}")
        print(f"技能数: {status['skills']}")
        print(f"工作流数: {status['workflows']}")
        print(f"监听地址: {status['host']}:{status['port']}")
    
    def config_show(self):
        """显示配置"""
        from config import get_config
        config = get_config()
        
        print("\n当前配置:")
        print("=" * 50)
        print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))
    
    def config_set(self, key: str, value: str):
        """设置配置"""
        from config import get_config
        config = get_config()
        
        # 尝试解析值
        try:
            parsed_value = json.loads(value)
        except:
            parsed_value = value
        
        config.set(key, parsed_value)
        config.save()
        
        print(f"设置 {key} = {parsed_value}")
        print("配置已保存")


def main():
    """主函数"""
    cli = MCPCLI()
    
    parser = argparse.ArgumentParser(
        description='MCP Core 命令行工具',
        prog='mcp'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # skill 命令
    skill_parser = subparsers.add_parser('skill', help='技能管理')
    skill_subparsers = skill_parser.add_subparsers(dest='skill_command')
    
    # skill list
    skill_list_parser = skill_subparsers.add_parser('list', help='列出技能')
    skill_list_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    # skill call
    skill_call_parser = skill_subparsers.add_parser('call', help='调用技能')
    skill_call_parser.add_argument('name', help='技能名称')
    skill_call_parser.add_argument('-p', '--params', default='{}', help='参数(JSON格式)')
    skill_call_parser.add_argument('-j', '--json', action='store_true', help='JSON格式输出')
    
    # skill info
    skill_info_parser = skill_subparsers.add_parser('info', help='查看技能详情')
    skill_info_parser.add_argument('name', help='技能名称')
    
    # workflow 命令
    workflow_parser = subparsers.add_parser('workflow', help='工作流管理')
    workflow_subparsers = workflow_parser.add_subparsers(dest='workflow_command')
    
    # workflow list
    workflow_subparsers.add_parser('list', help='列出工作流')
    
    # workflow run
    workflow_run_parser = workflow_subparsers.add_parser('run', help='运行工作流')
    workflow_run_parser.add_argument('name', help='工作流名称')
    workflow_run_parser.add_argument('-c', '--context', default='{}', help='上下文(JSON格式)')
    workflow_run_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    # workflow show
    workflow_show_parser = workflow_subparsers.add_parser('show', help='显示工作流详情')
    workflow_show_parser.add_argument('name', help='工作流名称')
    
    # server 命令
    server_parser = subparsers.add_parser('server', help='服务器管理')
    server_subparsers = server_parser.add_subparsers(dest='server_command')
    
    # server start
    server_start_parser = server_subparsers.add_parser('start', help='启动服务器')
    server_start_parser.add_argument('--host', default='localhost', help='主机地址')
    server_start_parser.add_argument('--port', type=int, default=8766, help='端口')
    server_start_parser.add_argument('-d', '--daemon', action='store_true', help='守护模式')
    
    # status 命令
    subparsers.add_parser('status', help='查看系统状态')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_command')
    
    # config show
    config_subparsers.add_parser('show', help='显示配置')
    
    # config set
    config_set_parser = config_subparsers.add_parser('set', help='设置配置')
    config_set_parser.add_argument('key', help='配置键')
    config_set_parser.add_argument('value', help='配置值')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'skill':
        if args.skill_command == 'list':
            cli.skill_list(args.verbose)
        elif args.skill_command == 'call':
            cli.skill_call(args.name, args.params, args.json)
        elif args.skill_command == 'info':
            cli.skill_info(args.name)
        else:
            skill_parser.print_help()
    
    elif args.command == 'workflow':
        if args.workflow_command == 'list':
            cli.workflow_list()
        elif args.workflow_command == 'run':
            cli.workflow_run(args.name, args.context, args.verbose)
        elif args.workflow_command == 'show':
            cli.workflow_show(args.name)
        else:
            workflow_parser.print_help()
    
    elif args.command == 'server':
        if args.server_command == 'start':
            cli.server_start(args.host, args.port, args.daemon)
        else:
            server_parser.print_help()
    
    elif args.command == 'status':
        cli.status()
    
    elif args.command == 'config':
        if args.config_command == 'show':
            cli.config_show()
        elif args.config_command == 'set':
            cli.config_set(args.key, args.value)
        else:
            config_parser.print_help()


if __name__ == '__main__':
    main()
