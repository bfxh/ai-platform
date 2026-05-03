#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - 技能安装器

功能:
- 自动创建技能目录结构
- 生成技能模板代码
- 自动注册技能
- 更新配置文件

用法:
    python skill_installer.py create <skill_name> [--description "描述"]
    python skill_installer.py list
    python skill_installer.py register <skill_name>
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# MCP Core 路径
MCP_CORE_PATH = Path("/python/MCP_Core")
SKILLS_PATH = MCP_CORE_PATH / "skills"
SERVER_FILE = MCP_CORE_PATH / "server.py"
CONFIG_FILE = MCP_CORE_PATH / "config.py"


SKILL_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{skill_class} - {description}

功能:
- 功能1
- 功能2

用法:
    skill.execute({{'action': 'action1'}})
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base import Skill
from event_bus import get_event_bus


class {skill_class}(Skill):
    """{description}"""
    
    name = "{skill_name}"
    description = "{description}"
    version = "1.0.0"
    author = "MCP Core"
    config_prefix = "{skill_name}"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.event_bus = get_event_bus()
    
    def get_parameters(self):
        """定义技能参数"""
        return {{
            'action': {{
                'type': 'string',
                'required': True,
                'enum': ['action1', 'action2'],
                'description': '操作类型'
            }},
            'param1': {{
                'type': 'string',
                'required': False,
                'default': 'default',
                'description': '参数1'
            }}
        }}
    
    def execute(self, params):
        """执行技能"""
        action = params.get('action')
        
        if action == 'action1':
            return self._do_action1(params)
        elif action == 'action2':
            return self._do_action2(params)
        else:
            return {{'success': False, 'error': f'未知操作: {{action}}'}}
    
    def _do_action1(self, params):
        """执行操作1"""
        try:
            self.event_bus.publish('{skill_name}_action1_started', {{}}, source=self.name)
            return {{'success': True, 'result': 'action1 completed'}}
        except Exception as e:
            return {{'success': False, 'error': str(e)}}
    
    def _do_action2(self, params):
        """执行操作2"""
        try:
            return {{'success': True, 'result': 'action2 completed'}}
        except Exception as e:
            return {{'success': False, 'error': str(e)}}


if __name__ == '__main__':
    skill = {skill_class}()
    print(f"技能: {{skill.name}}")
    print(f"描述: {{skill.description}}")
    print(f"版本: {{skill.version}}")
'''


INIT_TEMPLATE = '''"""{skill_class} - {description}"""

from .skill import {skill_class}

__all__ = ['{skill_class}']
'''


WORKFLOW_TEMPLATE = '''{{
  "name": "{workflow_name}",
  "version": "1.0",
  "description": "{description}",
  "steps": [
    {{
      "id": "step1",
      "name": "步骤1",
      "description": "第一步",
      "skill": "{skill_name}",
      "action": "action1",
      "params": {{}}
    }},
    {{
      "id": "step2",
      "name": "步骤2",
      "description": "第二步",
      "skill": "{skill_name}",
      "action": "action2",
      "params": {{}},
      "depends_on": ["step1"]
    }}
  ],
  "config": {{
    "timeout": 300
  }}
}}'''


class SkillInstaller:
    """技能安装器"""
    
    def __init__(self):
        self.skills_path = SKILLS_PATH
        self.server_file = SERVER_FILE
        self.config_file = CONFIG_FILE
    
    def create_skill(self, skill_name: str, description: str = "") -> bool:
        """创建新技能"""
        # 转换技能名称为有效格式
        skill_name = skill_name.lower().replace(' ', '_').replace('-', '_')
        skill_class = ''.join(word.capitalize() for word in skill_name.split('_')) + 'Skill'
        
        if not description:
            description = f"{skill_name} 技能"
        
        # 创建目录
        skill_dir = self.skills_path / skill_name
        if skill_dir.exists():
            print(f"[错误] 技能 '{skill_name}' 已存在")
            return False
        
        try:
            skill_dir.mkdir(parents=True)
            
            # 创建 __init__.py
            init_file = skill_dir / "__init__.py"
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(INIT_TEMPLATE.format(
                    skill_class=skill_class,
                    description=description
                ))
            
            # 创建 skill.py
            skill_file = skill_dir / "skill.py"
            with open(skill_file, 'w', encoding='utf-8') as f:
                f.write(SKILL_TEMPLATE.format(
                    skill_name=skill_name,
                    skill_class=skill_class,
                    description=description
                ))
            
            print(f"[成功] 技能 '{skill_name}' 创建完成")
            print(f"  目录: {skill_dir}")
            print(f"  文件: {skill_file}")
            print(f"\n下一步:")
            print(f"  1. 编辑 {skill_file}")
            print(f"  2. 运行: python skill_installer.py register {skill_name}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 创建技能失败: {e}")
            return False
    
    def register_skill(self, skill_name: str) -> bool:
        """注册技能到server.py"""
        skill_name = skill_name.lower().replace(' ', '_').replace('-', '_')
        skill_class = ''.join(word.capitalize() for word in skill_name.split('_')) + 'Skill'
        
        skill_dir = self.skills_path / skill_name
        if not skill_dir.exists():
            print(f"[错误] 技能 '{skill_name}' 不存在，请先创建")
            return False
        
        try:
            # 读取 server.py
            with open(self.server_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已注册
            if f"from skills.{skill_name}.skill import {skill_class}" in content:
                print(f"[警告] 技能 '{skill_name}' 已在 server.py 中注册")
                return True
            
            # 添加导入语句
            import_line = f"    from skills.{skill_name}.skill import {skill_class}\n"
            
            # 找到最后一个导入语句的位置
            import_marker = "# 注册已有技能..."
            if import_marker in content:
                content = content.replace(
                    import_marker,
                    f"{import_line}    {import_marker}"
                )
            
            # 添加注册代码
            register_code = f"""        # 注册 {skill_name} 技能
        if self.config.is_skill_enabled('{skill_name}'):
            skill = {skill_class}(skills_config.get('{skill_name}'))
            self.skill_registry.register(skill)
        
"""
            
            register_marker = "self._skills_loaded = True"
            if register_marker in content:
                content = content.replace(
                    register_marker,
                    f"{register_code}        {register_marker}"
                )
            
            # 写回文件
            with open(self.server_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新配置
            self._add_config(skill_name)
            
            print(f"[成功] 技能 '{skill_name}' 已注册到 server.py")
            print(f"[成功] 配置已添加到 config.py")
            print(f"\n现在可以测试:")
            print(f"  python server.py --call {skill_name} --params {{\"action\":\"action1\"}}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 注册技能失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_config(self, skill_name: str) -> bool:
        """添加配置到config.py"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已存在
            if f"'{skill_name}':" in content and "'skills':" in content:
                return True
            
            # 添加配置
            config_code = f"""        '{skill_name}': {{
            'enabled': True
        }},
"""
            
            # 找到 skills 配置的位置
            marker = "'skills': {"
            if marker in content:
                content = content.replace(
                    marker,
                    f"{marker}\n            # {skill_name} 技能配置\n{config_code}"
                )
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"[警告] 添加配置失败: {e}")
            return False
    
    def list_skills(self):
        """列出所有技能"""
        print("\n已创建的技能:")
        print("-" * 50)
        
        count = 0
        for item in self.skills_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                skill_file = item / "skill.py"
                init_file = item / "__init__.py"
                
                status = []
                if skill_file.exists():
                    status.append("✓ skill.py")
                if init_file.exists():
                    status.append("✓ __init__.py")
                
                # 检查是否已注册
                with open(self.server_file, 'r', encoding='utf-8') as f:
                    server_content = f.read()
                
                registered = f"from skills.{item.name}.skill import" in server_content
                
                print(f"  {item.name}")
                print(f"    路径: {item}")
                print(f"    文件: {', '.join(status) if status else '✗ 无'}")
                print(f"    注册: {'✓ 已注册' if registered else '✗ 未注册'}")
                print()
                count += 1
        
        print(f"总计: {count} 个技能")
    
    def create_workflow(self, workflow_name: str, skill_name: str = "", description: str = "") -> bool:
        """创建工作流"""
        workflow_name = workflow_name.lower().replace(' ', '_').replace('-', '_')
        
        if not description:
            description = f"{workflow_name} 工作流"
        
        if not skill_name:
            skill_name = "network_transfer"  # 默认技能
        
        workflow_file = MCP_CORE_PATH / "workflow" / "templates" / f"{workflow_name}.json"
        
        if workflow_file.exists():
            print(f"[错误] 工作流 '{workflow_name}' 已存在")
            return False
        
        try:
            with open(workflow_file, 'w', encoding='utf-8') as f:
                f.write(WORKFLOW_TEMPLATE.format(
                    workflow_name=workflow_name,
                    description=description,
                    skill_name=skill_name
                ))
            
            print(f"[成功] 工作流 '{workflow_name}' 创建完成")
            print(f"  文件: {workflow_file}")
            print(f"\n运行:")
            print(f"  python server.py --workflow {workflow_name}")
            
            return True
            
        except Exception as e:
            print(f"[错误] 创建工作流失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='MCP Core 技能安装器')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # create 命令
    create_parser = subparsers.add_parser('create', help='创建新技能')
    create_parser.add_argument('skill_name', help='技能名称')
    create_parser.add_argument('--description', '-d', default='', help='技能描述')
    
    # register 命令
    register_parser = subparsers.add_parser('register', help='注册技能到server.py')
    register_parser.add_argument('skill_name', help='技能名称')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有技能')
    
    # workflow 命令
    workflow_parser = subparsers.add_parser('workflow', help='创建工作流')
    workflow_parser.add_argument('workflow_name', help='工作流名称')
    workflow_parser.add_argument('--skill', '-s', default='', help='关联的技能')
    workflow_parser.add_argument('--description', '-d', default='', help='工作流描述')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    installer = SkillInstaller()
    
    if args.command == 'create':
        installer.create_skill(args.skill_name, args.description)
    
    elif args.command == 'register':
        installer.register_skill(args.skill_name)
    
    elif args.command == 'list':
        installer.list_skills()
    
    elif args.command == 'workflow':
        installer.create_workflow(args.workflow_name, args.skill, args.description)


if __name__ == '__main__':
    main()
