#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目文档自动生成系统
每个项目必须有对应的 .PROJECT.md 文档，跟随项目走

文档包含：
- 项目基本信息（名称、路径、技术栈）
- 架构设计（节点、数据流、依赖）
- 功能清单（所有功能点）
- 安装/构建指南
- 测试方法
- 已知的架构限制和注意事项
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# ─── 项目文档模板 ────────────────────────────────────────────────────────────
PROJECT_TEMPLATE = '''# {project_name} - 项目文档

> **生成时间**: {created_at}
> **项目路径**: {project_path}
> **最后更新**: {updated_at}

---

## 基本信息

| 字段 | 内容 |
|------|------|
| 项目名称 | {project_name} |
| 根目录 | {project_path} |
| 技术栈 | {tech_stack} |
| 语言 | {language} |
| 源码管理 | {vcs} |

---

## 架构设计

### 核心模块
{core_modules}

### 数据流
{data_flow}

### 依赖关系
{dependencies}

### 关键节点
{key_nodes}

---

## 功能清单

### 已实现功能
{implemented_features}

### 待实现功能（TODO）
{todo_features}

### 已知限制
{known_limitations}

---

## 安装与构建

### 环境要求
{requirements}

### 构建步骤
{build_steps}

### 配置说明
{config_notes}

---

## 测试方法

### 自动测试
{auto_tests}

### 手动验证步骤
{manual_tests}

---

## 维护记录

{history_records}

---

## 相关资源

- 源码: {project_path}
- 文档: {project_path}/README.md
- 配置: {config_location}

---

*本文档由 AI 系统自动生成，随项目同步更新*
'''

# ─── 架构节点类型 ────────────────────────────────────────────────────────────
NODE_TYPES = {
    "入口": "用户交互的起点（API/CLI/GUI）",
    "核心引擎": "业务逻辑处理中心",
    "存储": "数据持久化（DB/File/Memory）",
    "通信": "网络通信/API调用",
    "工具": "外部工具集成",
    "插件": "可扩展功能节点",
}

def analyze_directory_structure(root: Path, max_depth: int = 3) -> Dict:
    """分析目录结构，识别项目骨架"""
    structure = {
        "dirs": [],
        "code_files": [],
        "config_files": [],
        "doc_files": [],
    }
    
    if not root.exists():
        return structure
    
    def walk(path: Path, depth: int = 0):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                if item.name.startswith("."):
                    continue
                if item.is_dir():
                    structure["dirs"].append({"name": item.name, "path": str(item), "depth": depth})
                    walk(item, depth + 1)
                else:
                    ext = item.suffix.lower()
                    if ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".rs", ".go"]:
                        structure["code_files"].append(str(item))
                    elif ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".config"]:
                        structure["config_files"].append(str(item))
                    elif ext in [".md", ".txt", ".rst"]:
                        structure["doc_files"].append(str(item))
        except PermissionError:
            pass
    
    walk(root)
    return structure


def detect_language(structure: Dict) -> str:
    """识别主要编程语言"""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React/JSX",
        ".tsx": "React/TSX",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".rs": "Rust",
        ".go": "Go",
    }
    
    counts = {}
    for f in structure["code_files"]:
        ext = Path(f).suffix.lower()
        lang = ext_map.get(ext, ext)
        counts[lang] = counts.get(lang, 0) + 1
    
    if counts:
        return max(counts, key=counts.get)
    return "Unknown"


def detect_tech_stack(structure: Dict) -> List[str]:
    """识别技术栈"""
    stack = []
    all_files = [str(f) for f in structure["code_files"]] + [str(f) for f in structure["config_files"]]
    all_text = "\n".join(all_files).lower()
    
    indicators = {
        "Flask": "Flask",
        "FastAPI": "FastAPI",
        "Django": "Django",
        "React": "React",
        "Vue": "Vue.js",
        "Angular": "Angular",
        "Express": "Express.js",
        "Next.js": "Next.js",
        "Node.js": "Node.js",
        "Laravel": "Laravel",
        "Spring": "Spring Boot",
        "PyTorch": "PyTorch",
        "TensorFlow": "TensorFlow",
        "OpenCV": "OpenCV",
        "Pygame": "Pygame",
        "Godot": "Godot Engine",
        "Unity": "Unity",
        "Unreal": "Unreal Engine",
        "MCP": "MCP (Model Context Protocol)",
        "browser": "浏览器自动化",
    }
    
    for indicator, name in indicators.items():
        if indicator.lower() in all_text:
            stack.append(name)
    
    return stack or ["一般项目"]


def read_todos(structure: Dict) -> List[str]:
    """从代码文件中提取 TODO"""
    todos = []
    for f in structure["code_files"][:20]:  # 限制扫描文件数
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                for i, line in enumerate(fp, 1):
                    if "TODO" in line.upper() or "FIXME" in line.upper() or "XXX" in line.upper():
                        todos.append(f"{Path(f).name}:{i} - {line.strip()[:100]}")
        except Exception:
            pass
    return todos[:20]


def generate_project_doc(project_path: str) -> Dict:
    """生成项目文档"""
    root = Path(project_path)
    
    if not root.exists():
        return {"error": f"路径不存在: {project_path}"}
    
    structure = analyze_directory_structure(root)
    language = detect_language(structure)
    tech_stack = detect_tech_stack(structure)
    todos = read_todos(structure)
    
    # 识别核心目录
    core_dirs = [d["name"] for d in structure["dirs"] if d["depth"] == 1 
                 and d["name"] not in ["node_modules", "venv", "__pycache__", "Lib", "bin"]]
    
    # 核心模块描述
    core_modules_str = "\n".join([f"{i+1}. **{d}** - " for i, d in enumerate(core_dirs[:8])])
    
    # 生成文档
    doc_content = PROJECT_TEMPLATE.format(
        project_name=root.name,
        project_path=str(root),
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        tech_stack=", ".join(tech_stack),
        language=language,
        vcs="Git" if (root / ".git").exists() else "未知",
        core_modules=core_modules_str or "（从目录结构分析）",
        data_flow="（待补充：描述数据从输入到输出的完整路径）",
        dependencies="（待补充：外部依赖关系）",
        key_nodes="（待补充：关键处理节点）",
        implemented_features="（待补充）",
        todo_features="\n".join([f"- {t}" for t in todos]) if todos else "- （从代码中提取）",
        known_limitations="（待补充）",
        requirements="（待补充）",
        build_steps="（待补充）",
        config_notes="（待补充）",
        auto_tests="（待补充）",
        manual_tests="（待补充）",
        history_records="- 文档创建: " + datetime.now().strftime("%Y-%m-%d"),
        config_location=str(root / "config.json"),
    )
    
    return {
        "success": True,
        "project_name": root.name,
        "project_path": str(root),
        "language": language,
        "tech_stack": tech_stack,
        "structure": {
            "dirs": len(structure["dirs"]),
            "code_files": len(structure["code_files"]),
            "config_files": len(structure["config_files"]),
        },
        "document": doc_content,
    }


def save_project_doc(project_path: str, doc_content: str) -> str:
    """保存项目文档到项目目录"""
    root = Path(project_path)
    doc_path = root / ".PROJECT.md"
    doc_path.write_text(doc_content, encoding="utf-8")
    return str(doc_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python skill.py <项目路径>")
        print("示例: python skill.py /python/MCP_Core")
        sys.exit(1)
    
    project_path = sys.argv[1]
    print(f"分析项目: {project_path}\n")
    
    result = generate_project_doc(project_path)
    
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print(f"项目: {result['project_name']}")
        print(f"语言: {result['language']}")
        print(f"技术栈: {', '.join(result['tech_stack'])}")
        print(f"结构: {result['structure']['dirs']} 个目录, {result['structure']['code_files']} 个代码文件")
        
        doc_path = save_project_doc(project_path, result["document"])
        print(f"\n文档已生成: {doc_path}")
        
        # 同时保存到 MCP_Core data 目录
        out_path = Path("/python/MCP_Core/data/projects")
        out_path.mkdir(parents=True, exist_ok=True)
        safe_name = result["project_name"].replace("/", "_").replace("\\", "_")
        out_file = out_path / f"{safe_name}.md"
        out_file.write_text(result["document"], encoding="utf-8")
        print(f"副本保存: {out_file}")
