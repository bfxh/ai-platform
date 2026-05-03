#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为技能添加类型注解
"""

import re
from pathlib import Path
from typing import List


def add_type_hints(file_path: Path) -> bool:
    """为技能文件添加类型注解"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 检查是否已经导入了 typing
    if 'from typing import' not in content:
        # 在文件开头添加 typing 导入
        import_pattern = r'(import sys\n)'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r'\1from typing import Dict, List, Optional, Any, Tuple\n',
                content,
                count=1
            )
    
    # 为 execute 方法添加返回类型注解
    content = re.sub(
        r'def execute\(self, params\):',
        r'def execute(self, params: Dict) -> Dict:',
        content
    )
    
    # 为 get_parameters 方法添加返回类型注解
    content = re.sub(
        r'def get_parameters\(self\):',
        r'def get_parameters(self) -> Dict:',
        content
    )
    
    # 为 __init__ 方法添加参数类型注解
    content = re.sub(
        r'def __init__\(self, config=None\):',
        r'def __init__(self, config: Optional[Dict] = None):',
        content
    )
    
    # 为 validate_params 方法添加类型注解
    content = re.sub(
        r'def validate_params\(self, params\):',
        r'def validate_params(self, params: Dict) -> Tuple[bool, Optional[str]]:',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ {file_path.name} 已添加类型注解")
        return True
    else:
        print(f"  - {file_path.name} 无需修改")
        return False


def main():
    """主函数"""
    skills_dir = Path('/python/MCP_Core/skills')
    
    print("=" * 60)
    print("开始为技能添加类型注解")
    print("=" * 60)
    
    # 找到所有 skill.py 文件
    skill_files = list(skills_dir.glob('*/skill.py'))
    
    print(f"\n找到 {len(skill_files)} 个技能文件\n")
    
    modified_count = 0
    
    for skill_file in sorted(skill_files):
        if add_type_hints(skill_file):
            modified_count += 1
    
    print("\n" + "=" * 60)
    print(f"完成！修改了 {modified_count} 个文件")
    print("=" * 60)


if __name__ == '__main__':
    main()
