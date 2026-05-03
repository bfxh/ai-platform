#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Quality MCP - 代码质量分析工具

纯Python实现，零依赖，直接分析代码文件。

用法：
    python code_quality.py scan <path>              # 扫描代码
    python code_quality.py review <file>             # 审查单个文件
    python code_quality.py complexity <file>         # 复杂度分析
    python code_quality.py duplicates <path>         # 重复代码检测
    python code_quality.py dead <path>               # 死代码检测
    python code_quality.py deps <path>               # 依赖分析
    python code_quality.py metrics <path>            # 代码指标
    python code_quality.py report <path>             # 完整报告
    python code_quality.py fix <file>                # 自动修复简单问题
    python code_quality.py diff <file1> <file2>      # 代码对比
"""

import ast
import sys
import os
import re
import json
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

LANG_EXT = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
    '.java': 'java', '.cs': 'csharp', '.cpp': 'cpp', '.c': 'c',
    '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php',
}


# ============================================================
# 1. 代码扫描
# ============================================================
def scan_path(path):
    """扫描代码目录，输出整体指标"""
    path = Path(path)
    
    stats = {
        "files": 0, "total_lines": 0, "code_lines": 0,
        "blank_lines": 0, "comment_lines": 0,
        "functions": 0, "classes": 0,
        "max_line_length": 0, "avg_line_length": 0,
        "long_functions": [], "long_files": [],
        "by_language": {},
    }
    
    all_lengths = []
    
    files = []
    if path.is_file():
        files = [path]
    else:
        for ext in LANG_EXT:
            for f in path.rglob(f"*{ext}"):
                # 跳过废弃目录
                if '_deprecated' in str(f) or '__pycache__' in str(f):
                    continue
                files.append(f)
    
    for f in files:
        ext = f.suffix.lower()
        lang = LANG_EXT.get(ext, "unknown")
        
        try:
            lines = f.read_text(encoding='utf-8', errors='ignore').split('\n')
        except:
            continue
        
        stats["files"] += 1
        stats["total_lines"] += len(lines)
        
        lang_stats = stats["by_language"].setdefault(lang, {"files": 0, "lines": 0})
        lang_stats["files"] += 1
        lang_stats["lines"] += len(lines)
        
        code = 0
        blank = 0
        comment = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            all_lengths.append(len(line))
            
            if len(line) > stats["max_line_length"]:
                stats["max_line_length"] = len(line)
            
            if not stripped:
                blank += 1
            elif stripped.startswith('#') or stripped.startswith('//'):
                comment += 1
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                in_block_comment = not in_block_comment
                comment += 1
            elif stripped.startswith('/*'):
                in_block_comment = True
                comment += 1
            elif stripped.endswith('*/'):
                in_block_comment = False
                comment += 1
            elif in_block_comment:
                comment += 1
            else:
                code += 1
        
        stats["code_lines"] += code
        stats["blank_lines"] += blank
        stats["comment_lines"] += comment
        
        # Python特定分析
        if ext == '.py':
            try:
                tree = ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                        stats["functions"] += 1
                        func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                        if func_lines > 50:
                            stats["long_functions"].append({
                                "file": str(f), "name": node.name,
                                "lines": func_lines, "line": node.lineno
                            })
                    elif isinstance(node, ast.ClassDef):
                        stats["classes"] += 1
            except:
                pass
        
        if len(lines) > 500:
            stats["long_files"].append({"file": str(f), "lines": len(lines)})
    
    stats["avg_line_length"] = sum(all_lengths) // max(len(all_lengths), 1)
    
    # 输出
    print(f"代码扫描: {path}")
    print(f"{'='*50}")
    print(f"  文件数: {stats['files']}")
    print(f"  总行数: {stats['total_lines']}")
    print(f"  代码行: {stats['code_lines']}")
    print(f"  注释行: {stats['comment_lines']}")
    print(f"  空白行: {stats['blank_lines']}")
    print(f"  注释率: {stats['comment_lines']*100//max(stats['code_lines'],1)}%")
    print(f"  函数数: {stats['functions']}")
    print(f"  类数:   {stats['classes']}")
    print(f"  最长行: {stats['max_line_length']} 字符")
    print(f"  平均行长: {stats['avg_line_length']} 字符")
    
    if stats["by_language"]:
        print(f"\n  语言分布:")
        for lang, info in sorted(stats["by_language"].items(), key=lambda x: x[1]["lines"], reverse=True):
            print(f"    {lang:15s} {info['files']:4d} 文件  {info['lines']:6d} 行")
    
    if stats["long_functions"]:
        print(f"\n  过长函数 (>50行): {len(stats['long_functions'])} 个")
        for lf in stats["long_functions"][:10]:
            print(f"    {lf['name']:30s} {lf['lines']:4d}行  {lf['file']}:{lf['line']}")
    
    if stats["long_files"]:
        print(f"\n  过长文件 (>500行): {len(stats['long_files'])} 个")
        for lf in stats["long_files"][:10]:
            print(f"    {lf['lines']:5d}行  {lf['file']}")
    
    return stats


# ============================================================
# 2. 复杂度分析（Python）
# ============================================================
def analyze_complexity(filepath):
    """分析Python文件的圈复杂度"""
    code = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"语法错误: {e}")
        return
    
    print(f"复杂度分析: {filepath}")
    print(f"{'='*50}")
    
    results = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1  # 基础复杂度
            
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.IfExp)):
                    complexity += 1
                elif isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(child, (ast.And, ast.Or)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
                elif isinstance(child, ast.comprehension):
                    complexity += 1
            
            lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
            
            # 嵌套深度
            max_depth = _calc_nesting_depth(node)
            
            level = "OK" if complexity <= 5 else "WARN" if complexity <= 10 else "HIGH" if complexity <= 20 else "CRITICAL"
            
            results.append({
                "name": node.name, "line": node.lineno,
                "complexity": complexity, "lines": lines,
                "depth": max_depth, "level": level
            })
    
    results.sort(key=lambda x: x["complexity"], reverse=True)
    
    for r in results:
        marker = "✓" if r["level"] == "OK" else "⚠" if r["level"] == "WARN" else "✗"
        print(f"  {marker} {r['name']:35s} CC={r['complexity']:2d}  {r['lines']:3d}行  深度={r['depth']}  [{r['level']}]")
    
    avg_cc = sum(r["complexity"] for r in results) / max(len(results), 1)
    high = sum(1 for r in results if r["complexity"] > 10)
    print(f"\n  平均复杂度: {avg_cc:.1f}")
    print(f"  高复杂度函数: {high}/{len(results)}")
    
    return results


def _calc_nesting_depth(node, depth=0):
    """计算最大嵌套深度"""
    max_d = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)):
            d = _calc_nesting_depth(child, depth + 1)
            max_d = max(max_d, d)
        else:
            d = _calc_nesting_depth(child, depth)
            max_d = max(max_d, d)
    return max_d


# ============================================================
# 3. 重复代码检测
# ============================================================
def detect_duplicates(path, min_lines=5):
    """检测重复代码块"""
    path = Path(path)
    
    # 收集所有代码块
    blocks = {}  # hash → [(file, start_line, lines)]
    
    files = list(path.rglob("*.py")) if path.is_dir() else [path]
    
    for f in files:
        try:
            lines = f.read_text(encoding='utf-8', errors='ignore').split('\n')
        except:
            continue
        
        # 滑动窗口
        for i in range(len(lines) - min_lines + 1):
            block = '\n'.join(line.strip() for line in lines[i:i+min_lines] if line.strip())
            if len(block) < 50:  # 太短的跳过
                continue
            
            h = hashlib.md5(block.encode()).hexdigest()
            if h not in blocks:
                blocks[h] = []
            blocks[h].append({"file": str(f), "line": i+1, "preview": block[:100]})
    
    # 找重复
    duplicates = [(h, locs) for h, locs in blocks.items() if len(locs) > 1]
    duplicates.sort(key=lambda x: len(x[1]), reverse=True)
    
    print(f"重复代码检测: {path}")
    print(f"{'='*50}")
    
    if duplicates:
        print(f"  发现 {len(duplicates)} 组重复代码:")
        for h, locs in duplicates[:20]:
            print(f"\n  [{len(locs)}处重复]")
            for loc in locs[:5]:
                print(f"    {loc['file']}:{loc['line']}")
            print(f"    预览: {locs[0]['preview'][:80]}...")
    else:
        print("  未发现重复代码")
    
    return duplicates


# ============================================================
# 4. 依赖分析（Python）
# ============================================================
def analyze_deps(path):
    """分析Python文件的导入依赖"""
    path = Path(path)
    files = list(path.rglob("*.py")) if path.is_dir() else [path]
    
    imports = defaultdict(set)  # file → {imported_modules}
    all_modules = set()
    
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
        except:
            continue
        
        fname = str(f.relative_to(path) if path.is_dir() else f.name)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[fname].add(alias.name)
                    all_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports[fname].add(node.module)
                    all_modules.add(node.module)
    
    print(f"依赖分析: {path}")
    print(f"{'='*50}")
    
    # 标准库 vs 第三方 vs 本地
    stdlib = {'os', 'sys', 'json', 'time', 'datetime', 'pathlib', 're', 'math',
              'collections', 'functools', 'itertools', 'typing', 'abc', 'enum',
              'hashlib', 'struct', 'socket', 'threading', 'subprocess', 'shutil',
              'logging', 'unittest', 'io', 'copy', 'random', 'string', 'textwrap',
              'argparse', 'configparser', 'csv', 'sqlite3', 'http', 'urllib',
              'ssl', 'ctypes', 'ast', 'inspect', 'traceback', 'signal', 'uuid'}
    
    third_party = set()
    local = set()
    
    for mod in all_modules:
        root = mod.split('.')[0]
        if root in stdlib:
            pass
        elif any(root in str(f) for f in files):
            local.add(mod)
        else:
            third_party.add(mod)
    
    print(f"  标准库: {len(stdlib & all_modules)} 个")
    if third_party:
        print(f"  第三方: {', '.join(sorted(third_party))}")
    if local:
        print(f"  本地: {', '.join(sorted(local))}")
    
    # 依赖最多的文件
    dep_counts = [(f, len(deps)) for f, deps in imports.items()]
    dep_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  依赖最多的文件:")
    for f, count in dep_counts[:10]:
        print(f"    {count:3d} 个导入  {f}")
    
    return imports


# ============================================================
# 5. 代码指标汇总
# ============================================================
def full_report(path):
    """生成完整质量报告"""
    path = Path(path)
    
    print(f"{'='*60}")
    print(f"代码质量报告: {path}")
    print(f"{'='*60}")
    
    # 扫描
    print(f"\n{'─'*60}")
    print("1. 代码概览")
    print(f"{'─'*60}")
    stats = scan_path(path)
    
    # 复杂度
    if path.is_file() and path.suffix == '.py':
        print(f"\n{'─'*60}")
        print("2. 复杂度分析")
        print(f"{'─'*60}")
        analyze_complexity(str(path))
    
    # 依赖
    print(f"\n{'─'*60}")
    print("3. 依赖分析")
    print(f"{'─'*60}")
    analyze_deps(path)
    
    # 重复
    print(f"\n{'─'*60}")
    print("4. 重复代码")
    print(f"{'─'*60}")
    detect_duplicates(path)
    
    # 评分
    print(f"\n{'─'*60}")
    print("5. 质量评分")
    print(f"{'─'*60}")
    
    score = 10
    deductions = []
    
    if stats.get("long_functions"):
        d = min(len(stats["long_functions"]) * 0.5, 3)
        score -= d
        deductions.append(f"过长函数({len(stats['long_functions'])}个): -{d:.1f}")
    
    if stats.get("long_files"):
        d = min(len(stats["long_files"]) * 0.5, 2)
        score -= d
        deductions.append(f"过长文件({len(stats['long_files'])}个): -{d:.1f}")
    
    comment_rate = stats["comment_lines"] * 100 // max(stats["code_lines"], 1)
    if comment_rate < 5:
        score -= 1
        deductions.append(f"注释率过低({comment_rate}%): -1.0")
    
    if stats["max_line_length"] > 120:
        score -= 0.5
        deductions.append(f"最长行过长({stats['max_line_length']}字符): -0.5")
    
    score = max(score, 1)
    
    for d in deductions:
        print(f"  {d}")
    
    level = "优秀" if score >= 8 else "良好" if score >= 6 else "一般" if score >= 4 else "需改进"
    print(f"\n  总分: {score:.1f}/10 [{level}]")


# ============================================================
# CLI
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""Code Quality MCP - 代码质量分析

用法: python code_quality.py <action> [args...]

  scan <path>           扫描代码(行数/函数/类/语言)
  complexity <file>     复杂度分析(Python)
  duplicates <path>     重复代码检测
  deps <path>           依赖分析
  report <path>         完整质量报告""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "scan":
        scan_path(args[0] if args else ".")
    elif action == "complexity":
        analyze_complexity(args[0] if args else "")
    elif action == "duplicates":
        detect_duplicates(args[0] if args else ".")
    elif action == "deps":
        analyze_deps(args[0] if args else ".")
    elif action == "report":
        full_report(args[0] if args else ".")
    elif action == "review":
        # 单文件审查 = 复杂度 + 扫描
        if args:
            scan_path(args[0])
            if args[0].endswith('.py'):
                analyze_complexity(args[0])
    else:
        print(f"未知: {action}")


if __name__ == '__main__':
    main()
