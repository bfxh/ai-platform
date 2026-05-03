#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D盘全盘索引与快速查询系统 v2.0
==============================

以 %DEV_DIR% 为核心开发目录

功能:
1. 深度扫描D盘所有项目并建立索引
2. 支持按类型/关键词/路径查询
3. %DEV_DIR% 优先索引，递归到子项目
4. 生成结构化的索引数据库

使用方式:
    python disk_scanner.py scan        # 扫描并生成索引
    python disk_scanner.py query <关键词>  # 查询
    python disk_scanner.py list        # 列出所有项目
    python disk_scanner.py stats       # 显示统计信息
    python disk_scanner.py export      # 导出JSON
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import fnmatch

TOOLS_DIR = Path(__file__).parent
DB_PATH = TOOLS_DIR / "disk_index.db"
CONFIG_PATH = TOOLS_DIR / "disk_indexer_config.json"

PRIMARY_DEV_PATH = "%DEV_DIR%"

SCAN_PATHS = [
    (PRIMARY_DEV_PATH, "开发项目", True),
    ("/python", "AI开发环境", False),
    ("D:\\DEV\\工具\\GitHub", "GitHub克隆项目", False),
    ("%SOFTWARE_DIR%\\KF", "游戏Mod开发", False),
    ("%SOFTWARE_DIR%\\GJ", "工具项目", False),
    ("D:\\vcp\\VCPToolBox-main", "VCP工具箱", False),
    ("D:\\项目文件夹", "杂项项目", False),
    ("D:\\GJ BZM", "工具合集", False),
]

PROJECT_MARKERS = {
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "package.json": "Node.js",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "requirements.txt": "Python",
    "project.godot": "Godot",
    "pom.xml": "Java",
    "build.gradle": "Java/Gradle",
    "CMakeLists.txt": "C/C++",
    "Makefile": "C/C++",
}

PROJECT_MARKER_EXTENSIONS = {
    ".sln": "C#/.NET",
    ".csproj": "C#",
}

EXCLUDE_DIRS = {
    "node_modules", "__pycache__", ".git", "bin", "obj",
    "venv", ".venv", ".gradle", "build", "dist", "target",
    ".idea", ".vscode", "venv37", ".tox", ".eggs",
    ".pytest_cache", ".mypy_cache", ".next", ".nuxt",
    ".turbo", "coverage", ".cache", "Packages",
}

EXCLUDE_EXTENSIONS = {
    ".exe", ".dll", ".so", ".jar", ".zip", ".7z", ".rar",
    ".pak", ".blob", ".cache", ".pyc", ".pyo", ".o", ".obj",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".avi", ".mkv", ".flac",
    ".ttf", ".otf", ".woff", ".woff2",
}

DEV_CATEGORY_MAP = {
    "泰拉科技": "泰拉科技",
    "泰拉瑞亚": "泰拉瑞亚Mod",
    "星际战甲": "星际战甲",
    "我的": "个人项目",
}


class DiskIndexer:
    def __init__(self):
        self.db_path = DB_PATH
        self.config = self._load_config()
        self._init_database()

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _init_database(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                category TEXT,
                tech_stack TEXT,
                description TEXT,
                size_bytes INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                last_modified TEXT,
                indexed_at TEXT,
                is_dev_project INTEGER DEFAULT 0,
                parent_project TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_path TEXT,
                scan_time TEXT,
                items_found INTEGER,
                status TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_tech ON projects(tech_stack)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_dev ON projects(is_dev_project)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_parent ON projects(parent_project)")

        conn.commit()
        conn.close()

    def get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def scan_directory(self, path: str, category: str = None, deep: bool = False, parent: str = None) -> List[Dict]:
        projects = []
        path_obj = Path(path)

        if not path_obj.exists():
            print(f"[WARN] 路径不存在: {path}")
            return projects

        print(f"[SCAN] {'[DEEP] ' if deep else ''}{path}")

        for item in path_obj.iterdir():
            if not item.is_dir():
                continue
            if self._should_exclude_dir(item.name):
                continue

            project_info = self._analyze_project(item, category, parent=parent)
            if project_info:
                projects.append(project_info)

            if deep:
                sub_projects = self._deep_scan(item, category, parent=item.name)
                projects.extend(sub_projects)

        return projects

    def _deep_scan(self, path: Path, category: str = None, parent: str = None, depth: int = 0) -> List[Dict]:
        if depth > 3:
            return []

        projects = []
        try:
            for item in path.iterdir():
                if not item.is_dir():
                    continue
                if self._should_exclude_dir(item.name):
                    continue

                if self._is_project_root(item):
                    project_info = self._analyze_project(item, category, parent=parent)
                    if project_info:
                        projects.append(project_info)
                else:
                    sub = self._deep_scan(item, category, parent=parent, depth=depth + 1)
                    projects.extend(sub)
        except PermissionError:
            pass

        return projects

    def _should_exclude_dir(self, name: str) -> bool:
        for pattern in EXCLUDE_DIRS:
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                return True
        if name.startswith('.') and name not in {'.github', '.vscode'}:
            return True
        return False

    def _is_project_root(self, path: Path) -> bool:
        try:
            files = list(path.iterdir())
        except Exception:
            return False

        file_names = {f.name for f in files if f.is_file()}
        file_suffixes = {f.suffix.lower() for f in files if f.is_file()}

        for marker in PROJECT_MARKERS:
            if marker in file_names:
                return True

        for ext in PROJECT_MARKER_EXTENSIONS:
            if ext in file_suffixes:
                return True

        if any(f.suffix == ".gd" for f in files if f.is_file()):
            gd_count = sum(1 for f in files if f.is_file() and f.suffix == ".gd")
            if gd_count >= 2:
                return True

        if any(f.suffix == ".py" for f in files if f.is_file()):
            py_count = sum(1 for f in files if f.is_file() and f.suffix == ".py")
            if py_count >= 3:
                return True

        if any(f.suffix == ".cs" for f in files if f.is_file()):
            cs_count = sum(1 for f in files if f.is_file() and f.suffix == ".cs")
            if cs_count >= 3:
                return True

        return False

    def _analyze_project(self, path: Path, category: str = None, parent: str = None) -> Optional[Dict]:
        tech_stack = self._detect_tech_stack(path)
        if not tech_stack:
            return None

        size, file_count = self._calculate_size_and_files(path)
        is_dev = str(path).startswith(PRIMARY_DEV_PATH)

        if not category and is_dev:
            category = self._guess_dev_category(path)

        if not category:
            category = self._guess_category(path.name, tech_stack)

        project = {
            "name": path.name,
            "path": str(path),
            "category": category or "其他",
            "tech_stack": tech_stack,
            "description": self._generate_description(path, tech_stack),
            "size_bytes": size,
            "file_count": file_count,
            "last_modified": self._get_last_modified(path),
            "is_dev_project": 1 if is_dev else 0,
            "parent_project": parent,
        }

        return project

    def _detect_tech_stack(self, path: Path) -> Optional[str]:
        try:
            files = list(path.iterdir())
        except Exception:
            return None

        file_names = {f.name for f in files if f.is_file()}
        file_suffixes = {f.suffix.lower() for f in files if f.is_file()}

        for marker, tech in PROJECT_MARKERS.items():
            if marker in file_names:
                return tech

        for ext, tech in PROJECT_MARKER_EXTENSIONS.items():
            if ext in file_suffixes:
                return tech

        has_gd = any(f.suffix == ".gd" for f in files if f.is_file())
        has_rs = any(f.suffix == ".rs" for f in files if f.is_file())
        has_cs = any(f.suffix == ".cs" for f in files if f.is_file())
        has_py = any(f.suffix == ".py" for f in files if f.is_file())

        stacks = []
        if has_gd:
            stacks.append("GDScript")
        if has_rs:
            stacks.append("Rust")
        if has_cs:
            stacks.append("C#")
        if has_py:
            stacks.append("Python")

        if stacks:
            return "+".join(stacks)

        return None

    def _guess_dev_category(self, path: Path) -> Optional[str]:
        path_str = str(path)
        for key, cat in DEV_CATEGORY_MAP.items():
            if key in path_str:
                return cat
        return "开发项目"

    def _guess_category(self, name: str, tech: str) -> str:
        name_lower = name.lower()

        if "ai" in name_lower or "mcp" in name_lower or "gstack" in name_lower:
            return "AI系统"
        if "godot" in name_lower:
            return "Godot"
        if "unreal" in name_lower or "ue" in name_lower:
            return "UnrealEngine"
        if "unity" in name_lower:
            return "Unity"
        if "terr" in name_lower or "tmod" in name_lower:
            return "游戏Mod"
        if "bevy" in name_lower:
            return "Bevy"
        if "vcp" in name_lower or "toolbox" in name_lower:
            return "工具"
        if "rust" in name_lower or tech == "Rust":
            return "Rust"
        if "warframe" in name_lower:
            return "星际战甲"

        return "其他"

    def _calculate_size_and_files(self, path: Path) -> Tuple[int, int]:
        total_size = 0
        file_count = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        if item.suffix.lower() not in EXCLUDE_EXTENSIONS:
                            total_size += item.stat().st_size
                            file_count += 1
                    except Exception:
                        pass
        except Exception:
            pass
        return total_size, file_count

    def _get_last_modified(self, path: Path) -> str:
        try:
            return datetime.fromtimestamp(path.stat().st_mtime).isoformat()
        except Exception:
            return ""

    def _generate_description(self, path: Path, tech: str) -> str:
        for rmf in ["README.md", "readme.md", "README.txt", "README"]:
            readme = path / rmf
            if readme.exists():
                try:
                    with open(readme, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [f.readline().strip() for _ in range(5)]
                        desc = " ".join([l for l in lines if l and not l.startswith("#")])
                        if desc:
                            return desc[:200]
                except Exception:
                    pass
        return f"{tech}项目"

    def save_project(self, project: Dict) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO projects
            (name, path, category, tech_stack, description, size_bytes, file_count,
             last_modified, indexed_at, is_dev_project, parent_project)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project["name"],
            project["path"],
            project.get("category"),
            project.get("tech_stack"),
            project.get("description"),
            project.get("size_bytes", 0),
            project.get("file_count", 0),
            project.get("last_modified"),
            datetime.now().isoformat(),
            project.get("is_dev_project", 0),
            project.get("parent_project"),
        ))

        conn.commit()
        pid = cursor.lastrowid
        conn.close()
        return pid

    def full_scan(self) -> Dict:
        print("=" * 60)
        print("D盘全盘索引扫描 v2.0")
        print(f"核心开发目录: {PRIMARY_DEV_PATH}")
        print("=" * 60)

        total_projects = 0
        scan_results = []

        for scan_path, category, deep in SCAN_PATHS:
            projects = self.scan_directory(scan_path, category, deep=deep)
            for proj in projects:
                self.save_project(proj)
                total_projects += 1
                dev_flag = "★" if proj.get("is_dev_project") else " "
                print(f"  [{dev_flag}] {proj['name']} ({proj['tech_stack']}) [{proj['category']}]")

            scan_results.append({
                "path": scan_path,
                "category": category,
                "found": len(projects),
                "deep": deep
            })

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_history (scan_path, scan_time, items_found, status)
            VALUES (?, ?, ?, ?)
        """, ("ALL", datetime.now().isoformat(), total_projects, "completed"))
        conn.commit()
        conn.close()

        print("=" * 60)
        print(f"扫描完成! 共索引 {total_projects} 个项目")
        print(f"其中 %DEV_DIR% 项目: ★ 标记")
        print("=" * 60)

        return {
            "scan_time": datetime.now().isoformat(),
            "total_projects": total_projects,
            "results": scan_results
        }

    def query(self, keyword: str = None, category: str = None, tech: str = None,
              dev_only: bool = False, parent: str = None, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()

        sql = """SELECT id, name, path, category, tech_stack, description,
                        size_bytes, file_count, is_dev_project, parent_project
                 FROM projects WHERE 1=1"""
        params = []

        if keyword:
            sql += " AND (name LIKE ? OR path LIKE ? OR description LIKE ?)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if category:
            sql += " AND category = ?"
            params.append(category)

        if tech:
            sql += " AND tech_stack LIKE ?"
            params.append(f"%{tech}%")

        if dev_only:
            sql += " AND is_dev_project = 1"

        if parent:
            sql += " AND parent_project = ?"
            params.append(parent)

        sql += " ORDER BY is_dev_project DESC, size_bytes DESC LIMIT ?"
        params.append(int(limit))

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "name": row[1],
                "path": row[2],
                "category": row[3],
                "tech_stack": row[4],
                "description": row[5],
                "size_mb": round(row[6] / 1024 / 1024, 2) if row[6] else 0,
                "files": row[7],
                "is_dev": bool(row[8]),
                "parent": row[9],
            })

        conn.close()
        return results

    def list_all(self, limit: int = 200) -> List[Dict]:
        return self.query(limit=limit)

    def get_stats(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM projects")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE is_dev_project = 1")
        dev_total = cursor.fetchone()[0]

        cursor.execute("SELECT category, COUNT(*) FROM projects GROUP BY category ORDER BY COUNT(*) DESC")
        categories = dict(cursor.fetchall())

        cursor.execute("SELECT tech_stack, COUNT(*) FROM projects GROUP BY tech_stack ORDER BY COUNT(*) DESC")
        tech_stacks = dict(cursor.fetchall())

        cursor.execute("SELECT SUM(size_bytes) FROM projects")
        total_size = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(file_count) FROM projects")
        total_files = cursor.fetchone()[0] or 0

        cursor.execute("SELECT parent_project, COUNT(*) FROM projects WHERE parent_project IS NOT NULL GROUP BY parent_project ORDER BY COUNT(*) DESC")
        parents = dict(cursor.fetchall())

        conn.close()

        return {
            "total_projects": total,
            "dev_projects": dev_total,
            "total_size_gb": round(total_size / 1024 / 1024 / 1024, 2),
            "total_files": total_files,
            "categories": categories,
            "tech_stacks": tech_stacks,
            "parent_projects": parents,
        }

    def export_to_json(self, output_path: str = None) -> str:
        if output_path is None:
            output_path = TOOLS_DIR / "disk_index.json"

        projects = self.query(limit=10000)
        stats = self.get_stats()

        data = {
            "generated_at": datetime.now().isoformat(),
            "primary_dev_path": PRIMARY_DEV_PATH,
            "stats": stats,
            "projects": projects
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(output_path)


def format_results(results: List[Dict]) -> str:
    if not results:
        return "未找到匹配的项目\n"

    lines = []
    lines.append("=" * 90)
    lines.append(f"找到 {len(results)} 个项目:")
    lines.append("=" * 90)

    for i, proj in enumerate(results, 1):
        dev_flag = "★" if proj.get("is_dev") else " "
        parent_str = f" (父: {proj['parent']})" if proj.get("parent") else ""
        lines.append(f"\n{i}. [{dev_flag}] {proj['name']}{parent_str}")
        lines.append(f"   路径: {proj['path']}")
        lines.append(f"   分类: {proj['category']} | 技术: {proj['tech_stack']}")
        lines.append(f"   大小: {proj['size_mb']} MB | 文件: {proj['files']}")
        if proj.get("description"):
            lines.append(f"   描述: {proj['description'][:80]}")

    lines.append("\n" + "=" * 90)
    lines.append("★ = %DEV_DIR% 项目")
    return "\n".join(lines)


def main():
    import sys

    indexer = DiskIndexer()

    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  scan     - 执行全盘扫描")
        print("  query    - 查询项目 (用法: query <关键词>)")
        print("  list     - 列出所有项目")
        print("  stats    - 显示统计信息")
        print("  export   - 导出JSON")
        print("  dev      - 只列出%DEV_DIR%项目")
        return

    cmd = sys.argv[1].lower()

    if cmd == "scan":
        indexer.full_scan()

    elif cmd == "query":
        keyword = sys.argv[2] if len(sys.argv) > 2 else None
        category = None
        tech = None
        dev_only = False

        for i, arg in enumerate(sys.argv):
            if arg == "-c" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
            if arg == "-t" and i + 1 < len(sys.argv):
                tech = sys.argv[i + 1]
            if arg == "-d" or arg == "--dev":
                dev_only = True

        results = indexer.query(keyword=keyword, category=category, tech=tech, dev_only=dev_only)
        print(format_results(results))

    elif cmd == "list":
        results = indexer.list_all()
        print(format_results(results))

    elif cmd == "dev":
        results = indexer.query(dev_only=True, limit=200)
        print(format_results(results))

    elif cmd == "stats":
        stats = indexer.get_stats()
        print("=" * 60)
        print("D盘项目统计 v2.0")
        print("=" * 60)
        print(f"总项目数: {stats['total_projects']}")
        print(f"%DEV_DIR% 项目: {stats['dev_projects']}")
        print(f"总大小: {stats['total_size_gb']} GB")
        print(f"总文件数: {stats['total_files']}")
        print("\n按分类:")
        for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
        print("\n按技术栈:")
        for tech, count in sorted(stats['tech_stacks'].items(), key=lambda x: -x[1]):
            print(f"  {tech}: {count}")
        if stats.get('parent_projects'):
            print("\n按父项目:")
            for p, count in sorted(stats['parent_projects'].items(), key=lambda x: -x[1]):
                print(f"  {p}: {count} 个子项目")

    elif cmd == "export":
        path = indexer.export_to_json()
        print(f"已导出到: {path}")

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
