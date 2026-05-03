#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 项目管理自动化

功能：
- 批量管理多个项目
- 项目依赖分析
- 自动同步子模块
- 批量更新
- 项目健康检查
- 自动发布 Release
- 项目模板生成

用法：
    python github_project_manager.py list                    # 列出所有项目
    python github_project_manager.py add <path> [name]       # 添加项目
    python github_project_manager.py remove <name>           # 移除项目
    python github_project_manager.py sync                    # 同步所有项目
    python github_project_manager.py status                  # 查看所有项目状态
    python github_project_manager.py bulk-commit             # 批量提交所有项目
    python github_project_manager.py release <name> <version> # 发布 Release
    python github_project_manager.py template <name>         # 生成项目模板
    python github_project_manager.py health                  # 项目健康检查

MCP调用：
    {"tool": "github_project_manager", "action": "sync"}
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
CONFIG_PATH = AI_PATH / "MCP_Skills"
PROJECTS_FILE = CONFIG_PATH / "github_projects.json"

# ============================================================
# 数据结构
# ============================================================
@dataclass
class Project:
    """项目信息"""
    name: str
    path: str
    repo_url: Optional[str] = None
    auto_sync: bool = True
    auto_commit: bool = True
    last_sync: Optional[str] = None
    last_commit: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

# ============================================================
# 项目管理器
# ============================================================
class GitHubProjectManager:
    """GitHub 项目管理器"""
    
    def __init__(self):
        self.projects = self._load_projects()
    
    def _load_projects(self) -> Dict[str, Dict]:
        """加载项目列表"""
        if PROJECTS_FILE.exists():
            try:
                with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_projects(self):
        """保存项目列表"""
        PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.projects, f, ensure_ascii=False, indent=2)
    
    def add_project(self, path: Path, name: Optional[str] = None) -> Dict:
        """添加项目"""
        project_name = name or path.name
        
        # 检查项目是否存在
        if not path.exists():
            return {"success": False, "error": f"路径不存在: {path}"}
        
        # 获取 git 远程地址
        repo_url = None
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                repo_url = result.stdout.strip()
        except:
            pass
        
        # 添加项目
        self.projects[project_name] = asdict(Project(
            name=project_name,
            path=str(path),
            repo_url=repo_url
        ))
        
        self._save_projects()
        
        return {
            "success": True,
            "project": project_name,
            "path": str(path),
            "repo_url": repo_url
        }
    
    def remove_project(self, name: str) -> Dict:
        """移除项目"""
        if name not in self.projects:
            return {"success": False, "error": f"项目不存在: {name}"}
        
        del self.projects[name]
        self._save_projects()
        
        return {"success": True, "removed": name}
    
    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        return [
            {
                "name": name,
                "path": info["path"],
                "repo_url": info.get("repo_url"),
                "auto_sync": info.get("auto_sync", True),
                "last_sync": info.get("last_sync"),
                "last_commit": info.get("last_commit")
            }
            for name, info in self.projects.items()
        ]
    
    def sync_all(self) -> Dict:
        """同步所有项目"""
        results = []
        
        for name, info in self.projects.items():
            if not info.get("auto_sync", True):
                continue
            
            path = Path(info["path"])
            
            if not path.exists():
                results.append({"name": name, "success": False, "error": "路径不存在"})
                continue
            
            # 拉取更新
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=str(path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    self.projects[name]["last_sync"] = datetime.now().isoformat()
                    results.append({"name": name, "success": True, "output": result.stdout})
                else:
                    results.append({"name": name, "success": False, "error": result.stderr})
            
            except Exception as e:
                results.append({"name": name, "success": False, "error": str(e)})
        
        self._save_projects()
        
        return {
            "success": True,
            "synced": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results
        }
    
    def bulk_commit(self, message: Optional[str] = None) -> Dict:
        """批量提交所有项目"""
        results = []
        
        for name, info in self.projects.items():
            if not info.get("auto_commit", True):
                continue
            
            path = Path(info["path"])
            
            if not path.exists():
                results.append({"name": name, "success": False, "error": "路径不存在"})
                continue
            
            # 调用 github_auto_commit
            try:
                result = subprocess.run(
                    ["python", str(AI_PATH / "MCP" / "github_auto_commit.py"), "auto", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    self.projects[name]["last_commit"] = datetime.now().isoformat()
                    results.append({"name": name, "success": True})
                else:
                    results.append({"name": name, "success": False, "error": result.stderr})
            
            except Exception as e:
                results.append({"name": name, "success": False, "error": str(e)})
        
        self._save_projects()
        
        return {
            "success": True,
            "committed": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results
        }
    
    def health_check(self) -> Dict:
        """项目健康检查"""
        results = []
        
        for name, info in self.projects.items():
            path = Path(info["path"])
            
            health = {
                "name": name,
                "exists": path.exists(),
                "is_git_repo": (path / ".git").exists(),
                "has_remote": False,
                "uncommitted_changes": 0,
                "issues": []
            }
            
            if not path.exists():
                health["issues"].append("路径不存在")
                results.append(health)
                continue
            
            if not (path / ".git").exists():
                health["issues"].append("不是 Git 仓库")
                results.append(health)
                continue
            
            # 检查远程
            try:
                result = subprocess.run(
                    ["git", "remote", "-v"],
                    cwd=str(path),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                health["has_remote"] = "origin" in result.stdout
                
                if not health["has_remote"]:
                    health["issues"].append("未配置远程仓库")
            except:
                health["issues"].append("无法检查远程仓库")
            
            # 检查未提交变更
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=str(path),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                health["uncommitted_changes"] = len([l for l in result.stdout.strip().split('\n') if l])
                
                if health["uncommitted_changes"] > 0:
                    health["issues"].append(f"有 {health['uncommitted_changes']} 个未提交变更")
            except:
                pass
            
            results.append(health)
        
        return {
            "success": True,
            "total": len(results),
            "healthy": len([r for r in results if not r["issues"]]),
            "issues": len([r for r in results if r["issues"]]),
            "results": results
        }
    
    def generate_template(self, template_name: str, output_path: Path) -> Dict:
        """生成项目模板"""
        templates = {
            "python": {
                "files": {
                    "main.py": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()\n",
                    "requirements.txt": "",
                    "README.md": "# Project\n\nDescription\n",
                    ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n"
                }
            },
            "web": {
                "files": {
                    "index.html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Project</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>\n",
                    "style.css": "body {\n    font-family: Arial, sans-serif;\n}\n",
                    "script.js": "console.log('Hello, World!');\n",
                    "README.md": "# Web Project\n\nDescription\n"
                }
            },
            "mcp": {
                "files": {
                    "main.py": "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\"\"\"\nMCP Tool\n\"\"\"\n\nimport json\nimport sys\n\ndef main():\n    print('MCP Tool')\n\nif __name__ == '__main__':\n    main()\n",
                    "README.md": "# MCP Tool\n\nDescription\n",
                    ".gitignore": "__pycache__/\n*.pyc\n.env\n"
                }
            }
        }
        
        if template_name not in templates:
            return {"success": False, "error": f"未知模板: {template_name}"}
        
        template = templates[template_name]
        
        # 创建目录
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 创建文件
        for filename, content in template["files"].items():
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return {
            "success": True,
            "template": template_name,
            "path": str(output_path),
            "files": list(template["files"].keys())
        }

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    manager = GitHubProjectManager()
    
    if cmd == "list":
        projects = manager.list_projects()
        
        if not projects:
            print("没有管理的项目")
            return
        
        print(f"管理的项目 ({len(projects)} 个):")
        print("-" * 80)
        print(f"{'名称':<20} {'路径':<40} {'自动同步':<10}")
        print("-" * 80)
        
        for p in projects:
            path_display = p['path'][:40] + "..." if len(p['path']) > 40 else p['path']
            auto_sync = "是" if p.get('auto_sync', True) else "否"
            print(f"{p['name']:<20} {path_display:<40} {auto_sync:<10}")
    
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("用法: github_project_manager.py add <path> [name]")
            return
        
        path = Path(sys.argv[2])
        name = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = manager.add_project(path, name)
        
        if result.get("success"):
            print(f"✓ 项目已添加: {result['project']}")
            print(f"  路径: {result['path']}")
            if result['repo_url']:
                print(f"  仓库: {result['repo_url']}")
        else:
            print(f"✗ 添加失败: {result.get('error')}")
    
    elif cmd == "remove":
        if len(sys.argv) < 3:
            print("用法: github_project_manager.py remove <name>")
            return
        
        name = sys.argv[2]
        result = manager.remove_project(name)
        
        if result.get("success"):
            print(f"✓ 项目已移除: {result['removed']}")
        else:
            print(f"✗ 移除失败: {result.get('error')}")
    
    elif cmd == "sync":
        print("同步所有项目...")
        result = manager.sync_all()
        
        print(f"\n同步完成:")
        print(f"  成功: {result['synced']}")
        print(f"  失败: {result['failed']}")
    
    elif cmd == "bulk-commit":
        print("批量提交所有项目...")
        result = manager.bulk_commit()
        
        print(f"\n提交完成:")
        print(f"  成功: {result['committed']}")
        print(f"  失败: {result['failed']}")
    
    elif cmd == "health":
        print("项目健康检查...")
        result = manager.health_check()
        
        print(f"\n检查结果:")
        print(f"  总数: {result['total']}")
        print(f"  健康: {result['healthy']}")
        print(f"  有问题: {result['issues']}")
        
        print("\n详细报告:")
        for r in result['results']:
            status = "✓" if not r['issues'] else "✗"
            print(f"  {status} {r['name']}")
            for issue in r['issues']:
                print(f"      - {issue}")
    
    elif cmd == "template":
        if len(sys.argv) < 4:
            print("用法: github_project_manager.py template <name> <output_path>")
            return
        
        template_name = sys.argv[2]
        output_path = Path(sys.argv[3])
        
        result = manager.generate_template(template_name, output_path)
        
        if result.get("success"):
            print(f"✓ 模板已生成: {result['template']}")
            print(f"  路径: {result['path']}")
            print(f"  文件: {', '.join(result['files'])}")
        else:
            print(f"✗ 生成失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("GitHub 项目管理器 MCP 服务器已启动")
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    action = request.get("action")
                    params = request.get("params", {})
                    
                    if action == "list":
                        response = {"success": True, "projects": manager.list_projects()}
                    elif action == "add":
                        response = manager.add_project(Path(params["path"]), params.get("name"))
                    elif action == "remove":
                        response = manager.remove_project(params["name"])
                    elif action == "sync":
                        response = manager.sync_all()
                    elif action == "bulk_commit":
                        response = manager.bulk_commit(params.get("message"))
                    elif action == "health":
                        response = manager.health_check()
                    else:
                        response = {"success": False, "error": f"未知操作: {action}"}
                    
                    print(json.dumps(response, ensure_ascii=False))
                    sys.stdout.flush()
                
                except json.JSONDecodeError:
                    print(json.dumps({"success": False, "error": "无效的JSON"}))
                    sys.stdout.flush()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
