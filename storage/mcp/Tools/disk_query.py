#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRAE快速查询脚本
================

用于在TRAE中快速查询D盘项目

使用方法:
    python disk_query.py <关键词>
    python disk_query.py --list          # 列出所有
    python disk_query.py --stats        # 显示统计
    python disk_query.py --category ai   # 按分类筛选
    python disk_query.py --tech rust     # 按技术筛选
    python disk_query.py --path godot    # 路径关键词

输出格式:
    - 简洁模式: 名称 | 路径 | 技术栈
    - 详细模式: 包含描述和大小
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "MCP" / "Tools" / "disk_index.db"

CATEGORIES = {
    "ai": "AI系统",
    "godot": "Godot",
    "ue": "UnrealEngine",
    "unity": "Unity",
    "mod": "游戏Mod",
    "rust": "Rust",
    "bevy": "Bevy",
    "tool": "工具",
    "other": "其他"
}

TECH_STACKS = {
    "python": "Python",
    "rust": "Rust",
    "go": "Go",
    "java": "Java",
    "cs": "C#",
    "cpp": "C++",
    "ts": "TypeScript",
    "js": "JavaScript",
    "godot": "Godot",
    "dotnet": "C#/.NET"
}


def get_db():
    if not Path(DB_PATH).exists():
        return None
    return sqlite3.connect(str(DB_PATH))


def query_projects(
    keyword: str = None,
    category: str = None,
    tech: str = None,
    path_kw: str = None,
    limit: int = 50,
    verbose: bool = False
) -> List[Dict]:
    """查询项目"""
    conn = get_db()
    if not conn:
        return []

    cursor = conn.cursor()

    sql = """
        SELECT id, name, path, category, tech_stack, description, size_bytes, file_count
        FROM projects WHERE 1=1
    """
    params = []

    if keyword:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        kw = f"%{keyword}%"
        params.extend([kw, kw])

    if category:
        cat_full = CATEGORIES.get(category.lower(), category)
        sql += " AND category = ?"
        params.append(cat_full)

    if tech:
        if tech.lower() in TECH_STACKS:
            tech_full = TECH_STACKS[tech.lower()]
        else:
            tech_full = tech
        sql += " AND tech_stack = ?"
        params.append(tech_full)

    if path_kw:
        sql += " AND path LIKE ?"
        params.append(f"%{path_kw}%")

    sql += " ORDER BY size_bytes DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        size_mb = round(row[6] / 1024 / 1024, 2) if row[6] else 0
        results.append({
            "id": row[0],
            "name": row[1],
            "path": row[2],
            "category": row[3],
            "tech_stack": row[4],
            "description": row[5] or "",
            "size_mb": size_mb,
            "files": row[7]
        })

    conn.close()
    return results


def get_stats():
    """获取统计"""
    conn = get_db()
    if not conn:
        return None

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM projects")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT category, COUNT(*) FROM projects GROUP BY category ORDER BY COUNT(*) DESC")
    categories = [{"name": c[0], "count": c[1]} for c in cursor.fetchall()]

    cursor.execute("SELECT tech_stack, COUNT(*) FROM projects GROUP BY tech_stack ORDER BY COUNT(*) DESC")
    techs = [{"name": t[0], "count": t[1]} for t in cursor.fetchall()]

    cursor.execute("SELECT SUM(size_bytes) FROM projects")
    total_size = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total": total,
        "total_gb": round(total_size / 1024 / 1024 / 1024, 2),
        "categories": categories,
        "tech_stacks": techs
    }


def print_results(results: List[Dict], verbose: bool = False):
    """打印结果"""
    if not results:
        print("未找到匹配的项目")
        return

    if verbose:
        print("\n" + "=" * 90)
        print(f"找到 {len(results)} 个项目:")
        print("=" * 90)

        for i, p in enumerate(results, 1):
            print(f"\n{i}. {p['name']}")
            print(f"   分类: {p['category']} | 技术: {p['tech_stack']}")
            print(f"   大小: {p['size_mb']} MB | 文件: {p['files']}")
            print(f"   路径: {p['path']}")
            if p['description']:
                desc = p['description'][:100].replace('\n', ' ')
                print(f"   描述: {desc}...")
    else:
        header = f"{'名称':<35} {'技术栈':<10} {'大小':>8} | 路径"
        print("\n" + header)
        print("-" * 120)

        for p in results:
            name = p['name'][:33] + ".." if len(p['name']) > 35 else p['name']
            tech = (p['tech_stack'] or "Unknown")[:10]
            size = f"{p['size_mb']:.1f}MB"
            path = p['path']
            print(f"{name:<35} {tech:<10} {size:>8} | {path}")


def print_stats(stats):
    """打印统计"""
    if not stats:
        print("索引数据库不存在，请先运行: python disk_scanner.py scan")
        return

    print("\n" + "=" * 60)
    print("📊 D盘项目统计")
    print("=" * 60)
    print(f"总项目数: {stats['total']}")
    print(f"总大小: {stats['total_gb']} GB")

    print("\n按分类:")
    for c in stats['categories'][:10]:
        print(f"  {c['name']:<20} {c['count']:>5} 个")

    print("\n按技术栈:")
    for t in stats['tech_stacks'][:10]:
        print(f"  {t['name']:<20} {t['count']:>5} 个")


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        print("\n快速查询示例:")
        print("  python disk_query.py godot           # 搜索godot")
        print("  python disk_query.py --list          # 列出所有")
        print("  python disk_query.py --stats         # 显示统计")
        print("  python disk_query.py -c ai           # AI系统分类")
        print("  python disk_query.py -t rust         # Rust技术")
        print("  python disk_query.py -v rust         # 详细模式")
        return

    keyword = None
    category = None
    tech = None
    path_kw = None
    verbose = "-v" in args or "--verbose" in args

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--list":
            results = query_projects(limit=100)
            print_results(results, verbose=True)
            return
        elif arg == "--stats":
            stats = get_stats()
            print_stats(stats)
            return
        elif arg in ["-c", "--category"] and i + 1 < len(args):
            category = args[i + 1]
            i += 2
            continue
        elif arg in ["-t", "--tech"] and i + 1 < len(args):
            tech = args[i + 1]
            i += 2
            continue
        elif arg in ["-p", "--path"] and i + 1 < len(args):
            path_kw = args[i + 1]
            i += 2
            continue
        elif not arg.startswith("-"):
            keyword = arg
        i += 1

    results = query_projects(
        keyword=keyword,
        category=category,
        tech=tech,
        path_kw=path_kw,
        verbose=verbose
    )

    if keyword:
        print(f"\n🔍 搜索关键词: {keyword}")
    if category:
        print(f"📁 分类: {category}")
    if tech:
        print(f"🛠️ 技术: {tech}")
    if path_kw:
        print(f"📂 路径含: {path_kw}")

    print_results(results, verbose=verbose)


if __name__ == "__main__":
    main()
