#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 统一MCP Server

功能:
- MCP协议处理
- 工具注册与路由
- 请求/响应标准化
- WebSocket/HTTP支持

用法:
    python server.py                    # 启动服务器
    python server.py --port 8766        # 指定端口
    python server.py --call skill_name  # 直接调用技能
"""

import os
import sys
import json
import asyncio
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, Config
from event_bus import get_event_bus, EventBus
from skills.base import Skill, SkillRegistry, get_registry

# WorkflowEngine 延迟导入，避免启动时崩溃
try:
    from workflow.engine import WorkflowEngine
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False


class MCPServer:
    """MCP服务器"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.event_bus = get_event_bus()
        self.skill_registry = get_registry()
        self.workflow_engine = WorkflowEngine() if WORKFLOW_AVAILABLE else None
        
        self.host = self.config.get('server.host', 'localhost')
        self.port = self.config.get('server.port', 8766)
        self.max_connections = self.config.get('server.max_connections', 100)
        
        self._running = False
        self._skills_loaded = False
    
    def initialize(self) -> bool:
        """初始化服务器"""
        try:
            print(f"[MCP Server] 初始化中...")
            
            # 加载技能
            self._load_skills()
            
            # 启动事件总线
            self.event_bus.start()
            
            print(f"[MCP Server] 初始化完成")
            skills = self.skill_registry.list()
            print(f"  - 技能数量: {len(skills)}")
            if self.workflow_engine:
                print(f"  - 工作流数量: {len(self.workflow_engine.list_workflows())}")
            else:
                print(f"  - 工作流引擎: 不可用")
            
            return True
            
        except Exception as e:
            print(f"[MCP Server] 初始化失败: {e}")
            traceback.print_exc()
            return False
    
    def _load_skills(self):
        """加载技能"""
        if self._skills_loaded:
            return
        
        # 延迟导入核心技能，失败不影响整体
        skills_to_load = [
            ('network_transfer', 'NetworkTransferSkill'),
            ('exo_cluster', 'ExoClusterSkill'),
            ('notification', 'NotificationSkill'),
            ('system_config', 'SystemConfigSkill'),
            ('file_backup', 'FileBackupSkill')
        ]
        
        skills_config = self.config.get('skills', {})
        
        for skill_name, class_name in skills_to_load:
            try:
                module_path = f'skills.{skill_name}.skill'
                module = __import__(module_path, fromlist=[class_name])
                skill_class = getattr(module, class_name)
                
                if self.config.is_skill_enabled(skill_name):
                    self.skill_registry.register(skill_class)
                    print(f"[MCP Server] 注册技能: {skill_name}")
            except ImportError as e:
                print(f"[MCP Server] 跳过技能 {skill_name}: 模块不存在 - {e}")
            except Exception as e:
                print(f"[MCP Server] 跳过技能 {skill_name}: 初始化失败 - {e}")
        
        self._skills_loaded = True
        
        # 尝试加载所有已注册的技能
        print("[MCP Server] 尝试加载所有技能...")
        for skill_info in self.skill_registry.list():
            try:
                skill = self.skill_registry.get(skill_info['name'])
                if skill:
                    print(f"[MCP Server] 成功加载技能: {skill_info['name']}")
            except Exception as e:
                print(f"[MCP Server] 加载技能 {skill_info['name']} 失败: {e}")
    
    def call_skill(self, skill_name: str, params: Dict) -> Dict:
        """调用技能"""
        try:
            return self.skill_registry.execute(skill_name, params)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def run_workflow(self, workflow_name: str, context: Optional[Dict] = None) -> Dict:
        """运行工作流"""
        if self.workflow_engine is None:
            return {
                'success': False,
                'error': '工作流引擎不可用（workflow.engine 模块未安装）'
            }
        try:
            workflow = self.workflow_engine.load_workflow(workflow_name)
            if not workflow:
                return {
                    'success': False,
                    'error': f'工作流不存在: {workflow_name}'
                }
            
            return self.workflow_engine.execute(workflow, context)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def list_skills(self) -> List[Dict]:
        """列出所有技能"""
        return self.skill_registry.list()
    
    def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        if self.workflow_engine is None:
            return []
        return self.workflow_engine.list_workflows()
    
    def get_status(self) -> Dict:
        """获取服务器状态"""
        workflows_count = len(self.workflow_engine.list_workflows()) if self.workflow_engine else 0
        skills_count = len(self.skill_registry.list())
        return {
            'status': 'running' if self._running else 'stopped',
            'version': self.config.get('version', '2.0.0'),
            'skills': skills_count,
            'workflows': workflows_count,
            'host': self.host,
            'port': self.port
        }
    
    def shutdown(self):
        """关闭服务器"""
        self._running = False
        self.skill_registry.shutdown_all()
        if self.workflow_engine is not None:
            self.workflow_engine.shutdown()
        self.event_bus.stop()
        print("[MCP Server] 已关闭")


def main():
    parser = argparse.ArgumentParser(description='MCP Core Server')
    parser.add_argument('--port', type=int, default=8766, help='服务器端口')
    parser.add_argument('--host', type=str, default='localhost', help='服务器地址')
    parser.add_argument('--call', type=str, help='直接调用技能')
    parser.add_argument('--workflow', type=str, help='运行工作流')
    parser.add_argument('--list-skills', action='store_true', help='列出技能')
    parser.add_argument('--list-workflows', action='store_true', help='列出工作流')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--params', type=str, default='{}', help='调用参数(JSON)')
    
    args = parser.parse_args()
    
    # 创建服务器
    config = get_config()
    if args.port:
        config.set('server.port', args.port)
    if args.host:
        config.set('server.host', args.host)
    
    server = MCPServer(config)
    
    # 初始化
    if not server.initialize():
        sys.exit(1)
    
    # 处理命令
    if args.list_skills:
        print("\n可用技能:")
        for skill in server.list_skills():
            print(f"  - {skill['name']}: {skill['description']}")
            print(f"    版本: {skill['version']}, 作者: {skill['author']}")
            print(f"    已加载: {skill['is_loaded']}, 动作: {len(skill['actions'])}")
        print()
        return
    
    if args.list_workflows:
        print("\n可用工作流:")
        for wf in server.list_workflows():
            print(f"  - {wf['name']}: {wf['description']}")
            print(f"    步骤数: {wf['steps_count']}, 版本: {wf['version']}")
        print()
        return
    
    if args.status:
        status = server.get_status()
        print("\nMCP Server 状态:")
        print(f"  版本: {status['version']}")
        print(f"  状态: {status['status']}")
        print(f"  技能数: {status['skills']}")
        print(f"  工作流数: {status['workflows']}")
        print(f"  地址: {status['host']}:{status['port']}")
        print()
        return
    
    if args.call:
        try:
            params = json.loads(args.params)
        except:
            params = {}
        
        print(f"\n调用技能: {args.call}")
        print(f"参数: {params}")
        print("-" * 40)
        
        result = server.call_skill(args.call, params)
        
        print(f"\n结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        return
    
    if args.workflow:
        print(f"\n运行工作流: {args.workflow}")
        print("-" * 40)
        
        result = server.run_workflow(args.workflow)
        
        print(f"\n结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()
        return
    
    # 交互模式
    print("\n" + "=" * 50)
    print("MCP Core Server v2.0")
    print("=" * 50)
    print("\n可用命令:")
    print("  skills        - 列出技能")
    print("  workflows     - 列出工作流")
    print("  call <skill>  - 调用技能")
    print("  run <workflow> - 运行工作流")
    print("  status        - 查看状态")
    print("  quit          - 退出")
    print()
    
    try:
        while True:
            try:
                cmd = input("> ").strip()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                command = parts[0].lower()
                
                if command == 'quit' or command == 'exit':
                    break
                
                elif command == 'skills':
                    for skill in server.list_skills():
                        print(f"  {skill['name']}: {skill['description']}")
                
                elif command == 'workflows':
                    for wf in server.list_workflows():
                        print(f"  {wf['name']}: {wf['description']}")
                
                elif command == 'status':
                    status = server.get_status()
                    print(f"  状态: {status['status']}")
                    print(f"  技能: {status['skills']}, 工作流: {status['workflows']}")
                
                elif command == 'call' and len(parts) >= 2:
                    skill_name = parts[1]
                    params = {}
                    if len(parts) >= 3:
                        try:
                            params = json.loads(' '.join(parts[2:]))
                        except:
                            pass
                    
                    result = server.call_skill(skill_name, params)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                
                elif command == 'run' and len(parts) >= 2:
                    workflow_name = parts[1]
                    result = server.run_workflow(workflow_name)
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                
                else:
                    print(f"未知命令: {command}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
    
    finally:
        server.shutdown()
        print("\n再见!")


if __name__ == '__main__':
    main()
