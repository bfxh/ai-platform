#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为技能添加错误处理装饰器
"""

import re
from pathlib import Path


def add_error_handler_decorator(file_path: Path) -> bool:
    """为技能文件添加错误处理装饰器"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 检查是否已经导入了 handle_errors
    if 'from skills.base import Skill, handle_errors' in content:
        print(f"  ✓ {file_path.name} 已有装饰器导入")
        return False
    
    # 检查是否导入了 Skill
    if 'from skills.base import Skill' not in content:
        print(f"  ✗ {file_path.name} 未找到 Skill 导入")
        return False
    
    # 1. 添加 handle_errors 到导入
    content = content.replace(
        'from skills.base import Skill',
        'from skills.base import Skill, handle_errors'
    )
    
    # 2. 为 execute 方法添加装饰器
    # 查找 execute 方法定义
    execute_pattern = r'(\s+)def execute\(self'
    
    def add_decorator(match):
        indent = match.group(1)
        # 检查上一行是否已经有装饰器
        lines_before = content[:match.start()].split('\n')
        if lines_before and lines_before[-1].strip().startswith('@'):
            return match.group(0)  # 已有装饰器，不添加
        
        return f'{indent}@handle_errors\n{match.group(0)}'
    
    content = re.sub(execute_pattern, add_decorator, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {file_path.name} 已添加装饰器")
        return True
    else:
        print(f"  - {file_path.name} 无需修改")
        return False


def main():
    """主函数"""
    skills_dir = Path('/python/MCP_Core/skills')
    
    print("=" * 60)
    print("开始为技能添加错误处理装饰器")
    print("=" * 60)
    
    # 找到所有 skill.py 文件
    skill_files = list(skills_dir.glob('*/skill.py'))
    
    print(f"\n找到 {len(skill_files)} 个技能文件\n")
    
    modified_count = 0
    
    for skill_file in sorted(skill_files):
        if add_error_handler_decorator(skill_file):
            modified_count += 1
    
    print("\n" + "=" * 60)
    print(f"完成！修改了 {modified_count} 个文件")
    print("=" * 60)


if __name__ == '__main__':
    main()
