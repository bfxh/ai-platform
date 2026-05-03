#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件库扫描器 - 扫描 D:\rj 和 F:\rj，建立完整软件清单并写入知识库
功能：
- 递归扫描所有目录，找到 .exe 和主要项目
- 识别软件类型（AI工具/IDE/游戏/系统工具）
- 自动写入知识库（SQLite + MEMORY.md）
- 生成软件清单报告
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 路径
RJ_DIRS = [Path("D:/rj"), Path("F:/rj")]
KB_PATH = Path("/python/MCP_Core/data/knowledge_base.db")
REPORT_PATH = Path("/python/MCP_Core/data/software_inventory.json")
KB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 软件类型映射
CATEGORY_MAP = {
    "AI": ["AI", "QClaw", "StepFun", "WorkBuddy", "Gemma", "Claude", "DeepSeek", "Ollama"],
    "IDE": ["VS Code", "VS", "DevEco", "PyCharm", "IntelliJ", "VSCode", "Trae", "Sublime", "Atom"],
    "GameEngine": ["Godot", "Unity", "UE_", "Unreal", "Godot_v"],
    "3DTool": ["blender", "Blender"],
    "Browser": ["browser", "LLQ", "chrome", "firefox", "edge"],
    "DevTool": ["Git", "npm", "node", "Rust", "cargo", "python"],
    "Utility": ["7-Zip", "DiskGenius", "Everything", "Umi-OCR", "UniGetUI", "HandBrake", "IDM", "VoiceXiaoai"],
    "Game": ["ATLauncher", "Steam", "KF", "Netch"],
}

def get_category(name: str) -> str:
    for cat, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw.lower() in name.lower():
                return cat
    return "Other"

def get_exe_files(directory: Path, max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
    """递归查找 exe 文件"""
    results = []
    if current_depth > max_depth or not directory.exists():
        return results
    
    try:
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() == ".exe":
                # 过滤安装包
                size = item.stat().st_size
                if size < 100_000:  # 小于100KB跳过
                    continue
                results.append({
                    "name": item.stem,
                    "full_name": item.name,
                    "path": str(item),
                    "size_mb": round(size / 1024 / 1024, 2),
                    "category": get_category(item.stem),
                    "parent": item.parent.name,
                })
            elif item.is_dir() and not item.name.startswith("."):
                if item.name not in ["node_modules", "__pycache__", ".git", "venv", "Lib", "Include"]:
                    results.extend(get_exe_files(item, max_depth, current_depth + 1))
    except PermissionError:
        pass
    return results

def get_project_dirs(directory: Path, max_depth: int = 3, current_depth: int = 0) -> List[Dict]:
    """查找项目目录（有 README 或特定文件的）"""
    results = []
    if current_depth > max_depth or not directory.exists():
        return results
    
    try:
        has_readme = any(directory.glob("README*")) or any(directory.glob("*.md"))
        has_code = any(directory.glob("*.py")) or any(directory.glob("*.js")) or any(directory.glob("*.ts")) or any(directory.glob("*.cpp"))
        
        if (has_readme or has_code) and current_depth >= 1:
            results.append({
                "name": directory.name,
                "path": str(directory),
                "has_readme": has_readme,
                "has_code": has_code,
                "category": get_category(directory.name),
                "parent": directory.parent.name,
                "depth": current_depth,
            })
        
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                if item.name not in ["node_modules", "__pycache__", ".git", "venv", "Lib", "Include", "Scripts"]:
                    results.extend(get_project_dirs(item, max_depth, current_depth + 1))
    except PermissionError:
        pass
    return results

def scan_all() -> Dict:
    """扫描所有软件库"""
    all_exes = []
    all_projects = []
    
    for rj_dir in RJ_DIRS:
        if rj_dir.exists():
            print(f"扫描: {rj_dir}")
            exes = get_exe_files(rj_dir)
            projects = get_project_dirs(rj_dir)
            all_exes.extend(exes)
            all_projects.extend(projects)
            print(f"  找到 {len(exes)} 个程序, {len(projects)} 个项目目录")
    
    # 去重（按路径）
    seen_exe_paths = set()
    unique_exes = []
    for e in all_exes:
        if e["path"] not in seen_exe_paths:
            seen_exe_paths.add(e["path"])
            unique_exes.append(e)
    
    seen_proj_paths = set()
    unique_projects = []
    for p in all_projects:
        if p["path"] not in seen_proj_paths:
            seen_proj_paths.add(p["path"])
            unique_projects.append(p)
    
    return {
        "scan_time": datetime.now().isoformat(),
        "exe_count": len(unique_exes),
        "project_count": len(unique_projects),
        "executables": unique_exes,
        "projects": unique_projects,
    }

def write_to_knowledge_base(data: Dict):
    """将软件清单写入 SQLite 知识库"""
    conn = sqlite3.connect(str(KB_PATH))
    
    # 确保表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS software_inventory (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            category TEXT,
            size_mb REAL,
            type TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sw_category ON software_inventory(category)")
    conn.commit()
    
    now = datetime.now().isoformat()
    
    # 写入 exe
    for exe in data["executables"]:
        sw_id = hashlib.md5(exe["path"].encode()).hexdigest()[:12]
        conn.execute("""
            INSERT OR REPLACE INTO software_inventory 
            (id, name, path, category, size_mb, type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sw_id, exe["name"], exe["path"], exe["category"], 
              exe.get("size_mb"), "executable", now))
    
    # 写入项目
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_inventory (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            category TEXT,
            has_readme INTEGER,
            has_code INTEGER,
            updated_at TEXT NOT NULL
        )
    """)
    
    for proj in data["projects"]:
        pid = hashlib.md5(proj["path"].encode()).hexdigest()[:12]
        conn.execute("""
            INSERT OR REPLACE INTO project_inventory 
            (id, name, path, category, has_readme, has_code, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pid, proj["name"], proj["path"], proj["category"],
              int(proj["has_readme"]), int(proj["has_code"]), now))
    
    conn.commit()
    conn.close()

def kb_add_software(knowledge_base_module, data: Dict):
    """将软件信息写入知识库（通过 knowledge_base.py）"""
    if knowledge_base_module is None:
        return
    
    # 写入高价值软件
    high_value = [
        ("AI工具-QClaw", f"%SOFTWARE_DIR%\\AI\\QClaw\\QClaw.exe (195MB) - AI客户端"),
        ("AI工具-StepFun", f"%SOFTWARE_DIR%\\AI\\StepFun\\StepFun.exe (196MB) - StepFun客户端"),
        ("AI工具-WorkBuddy", f"%SOFTWARE_DIR%\\AI\\WorkBuddy\\WorkBuddy.exe (182MB) - AI工作助手"),
        ("IDE-Trae CN", f"%SOFTWARE_DIR%\\KF\\BC\\Trae CN\\Trae CN.exe - 集成开发环境（含AI）"),
        ("IDE-VS Code", f"%SOFTWARE_DIR%\\KF\\BC\\VS Code\\Microsoft VS Code\\Code.exe"),
        ("IDE-Visual Studio", f"%SOFTWARE_DIR%\\KF\\BC\\VS - Microsoft Visual Studio"),
        ("IDE-DevEco Studio", f"%SOFTWARE_DIR%\\KF\\DevEcoStudio - 鸿蒙应用开发IDE"),
        ("浏览器-browser-use", f"%SOFTWARE_DIR%\\LLQ\\browser-use-main - AI浏览器自动化框架"),
        ("浏览器-browser-main", f"%SOFTWARE_DIR%\\LLQ\\browser-main - 自定义浏览器项目"),
        ("游戏引擎-Godot", f"%SOFTWARE_DIR%\\KF\\JM\\Godot_v4.6.1-stable_win64.exe - Godot 4游戏引擎"),
        ("游戏引擎-Unity", f"%SOFTWARE_DIR%\\KF\\JM\\Unity\\Editor - Unity 2021/2022编辑器"),
        ("游戏引擎-UE5.6", f"%SOFTWARE_DIR%\\KF\\JM\\UE_5.6\\Engine - Unreal Engine 5.6"),
        ("3D工具-Blender", f"%SOFTWARE_DIR%\\KF\\JM\\blender\\blender.exe - Blender 3D建模"),
        ("工具-Everything", f"%SOFTWARE_DIR%\\GJ\\Everything\\Everything.exe - 极速文件搜索"),
        ("工具-7-Zip", f"%SOFTWARE_DIR%\\GJ\\7-Zip\\7zFM.exe - 压缩工具"),
        ("工具-Umi-OCR", f"%SOFTWARE_DIR%\\GJ\\Umi-OCR_Paddle_v2.1.5 - PaddleOCR文字识别"),
        ("工具-UniGetUI", f"%SOFTWARE_DIR%\\GJ\\UniGetUI.x64\\UniGetUI.exe - 软件包管理器"),
        ("版本控制-Git", f"%GIT_DIR% - Git for Windows"),
        ("逆向工具-Ghidra", f"%SOFTWARE_DIR%\\KF\\FBY\\Ghidra - NSA逆向工具"),
        ("逆向工具-dnSpy", f"%SOFTWARE_DIR%\\KF\\FBY\\dnSpy - .NET逆向工具"),
        ("逆向工具-JADX", f"%SOFTWARE_DIR%\\KF\\FBY\\jadx - Android APK反编译器"),
    ]
    
    count = 0
    for title, content in high_value:
        try:
            knowledge_base_module.kb_add(title, content, category="software", importance=8)
            count += 1
        except Exception:
            pass
    
    return count

def generate_report(data: Dict) -> str:
    """生成软件清单报告"""
    lines = [
        "# 软件库扫描报告",
        f"扫描时间: {data['scan_time']}",
        f"总计: {data['exe_count']} 个程序, {data['project_count']} 个项目\n",
    ]
    
    # 按类型分组
    by_category = {}
    for exe in data["executables"]:
        cat = exe["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(exe)
    
    for cat, items in sorted(by_category.items()):
        lines.append(f"## {cat} ({len(items)}个)")
        for item in items[:20]:  # 最多显示20个
            size_str = f"{item['size_mb']}MB" if item.get("size_mb") else "?"
            lines.append(f"- `{item['name']}` - {item['path']} ({size_str})")
        if len(items) > 20:
            lines.append(f"  ... 还有 {len(items)-20} 个")
        lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("=== 软件库全面扫描 ===\n")
    
    # 扫描
    data = scan_all()
    
    # 保存 JSON
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n清单已保存: {REPORT_PATH}")
    
    # 写入知识库
    write_to_knowledge_base(data)
    print(f"已写入知识库: {KB_PATH}")
    
    # 写入高价值软件到知识库
    try:
        import sys
        sys.path.insert(0, "/python/MCP_Core")
        import knowledge_base
        count = kb_add_software(knowledge_base, data)
        print(f"知识库高价值软件: {count} 条")
    except Exception as e:
        print(f"知识库写入: {e}")
    
    # 生成报告
    report = generate_report(data)
    report_path = Path("/python/MCP_Core/data/software_inventory_report.md")
    report_path.write_text(report, encoding="utf-8")
    print(f"\n报告已保存: {report_path}")
    print(report)
