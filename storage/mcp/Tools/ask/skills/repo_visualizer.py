#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仓库可视化技能
分析GitHub仓库结构
"""

import os
from pathlib import Path

def run(repo_path=None):
    """运行仓库可视化技能"""
    try:
        if not repo_path:
            repo_path = os.getcwd()
        
        repo_path = Path(repo_path)
        if not repo_path.exists():
            return {"success": False, "error": "仓库路径不存在"}
        
        print(f"仓库可视化 - {repo_path.name}")
        print("=" * 50)
        
        # 统计文件类型
        file_types = {}
        total_files = 0
        
        for file in repo_path.rglob("*.*"):
            if file.is_file():
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
                total_files += 1
        
        print(f"总文件数: {total_files}")
        print("文件类型分布:")
        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext}: {count}")
        
        # 查找主要文件
        main_files = []
        for pattern in ["README*", "setup.*", "requirements.*", "package.*", "Makefile"]:
            for file in repo_path.glob(pattern):
                main_files.append(file.name)
        
        if main_files:
            print("\n主要文件:")
            for file in main_files:
                print(f"  - {file}")
        
        return {"success": True, "data": {"total_files": total_files, "file_types": file_types}}
    except Exception as e:
        return {"success": False, "error": str(e)}
