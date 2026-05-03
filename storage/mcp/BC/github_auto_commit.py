#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 自动化提交工作流 - 增强版

功能：
1. 自动检测项目变更
2. 智能生成提交信息
3. 自动提交并推送
4. 支持定时自动提交
5. 支持多项目管理
6. 变更摘要生成
7. 自动创建PR（可选）
8. 备份管理
9. 版本标签管理

用法：
    python github_auto_commit.py watch <project_path>    # 监控项目变更
    python github_auto_commit.py auto <project_path>     # 立即自动提交
    python github_auto_commit.py schedule <project_path> # 定时自动提交
    python github_auto_commit.py status <project_path>   # 查看项目状态
    python github_auto_commit.py log <project_path>      # 查看提交历史
    python github_auto_commit.py backup <project_path>   # 创建备份
    python github_auto_commit.py tag <project_path> <tag_name>  # 创建标签
    python github_auto_commit.py sync <project_path>     # 同步远程变更
    python github_auto_commit.py clean <project_path>    # 清理未跟踪文件
    python github_auto_commit.py init <project_path>     # 初始化项目

MCP调用：
    {"tool": "github_auto_commit", "action": "auto_commit", "params": {...}}
"""

import json
import sys
import os
import subprocess
import time
import hashlib
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
AI_PATH = Path("/python")
MCP_PATH = AI_PATH / "MCP"
CONFIG_PATH = AI_PATH / "MCP_Skills"
LOG_PATH = AI_PATH / "logs"

# 配置文件
CONFIG_FILE = CONFIG_PATH / "github_auto_commit.json"
STATE_FILE = CONFIG_PATH / "github_auto_commit_state.json"

# 默认配置
DEFAULT_CONFIG = {
    "auto_commit": {
        "enabled": True,
        "interval_minutes": 30,  # 每30分钟检查一次
        "min_changes": 1,        # 至少1个变更才提交
        "auto_push": True,
        "generate_message": True,
        "include_diff_summary": True
    },
    "commit_message": {
        "template": "{type}: {summary}",
        "types": {
            "feat": "新功能",
            "fix": "修复",
            "docs": "文档",
            "style": "格式",
            "refactor": "重构",
            "perf": "性能优化",
            "test": "测试",
            "chore": "构建/工具"
        }
    },
    "watch": {
        "file_patterns": ["*.py", "*.js", "*.html", "*.css", "*.md", "*.json", "*.yaml", "*.yml"],
        "ignore_patterns": ["__pycache__", "*.pyc", ".git", "node_modules", "venv", ".env"],
        "max_file_size_mb": 10
    },
    "backup": {
        "enabled": True,
        "max_backups": 10,
        "backup_dir": str(AI_PATH / "backups")
    }
}

# ============================================================
# 数据结构
# ============================================================
@dataclass
class ProjectConfig:
    """项目配置"""
    path: str
    repo_name: Optional[str] = None
    auto_commit: bool = True
    commit_interval: int = 30
    last_commit: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ChangeInfo:
    """变更信息"""
    files_added: List[str]
    files_modified: List[str]
    files_deleted: List[str]
    total_changes: int
    summary: str

# ============================================================
# GitHub 自动化提交管理器
# ============================================================
class GitHubAutoCommit:
    """GitHub 自动化提交管理器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.state = self._load_state()
        self.projects = self.state.get("projects", {})
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except:
                pass
        return DEFAULT_CONFIG
    
    def _save_config(self):
        """保存配置"""
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _load_state(self) -> Dict:
        """加载状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"projects": {}, "last_run": None}
    
    def _save_state(self):
        """保存状态"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "projects": self.projects,
                "last_run": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def _run_git(self, project_path: Path, args: List[str], check: bool = True) -> Tuple[int, str, str]:
        """运行 git 命令"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if check and result.returncode != 0:
                return result.returncode, result.stdout, result.stderr
            
            return result.returncode, result.stdout, result.stderr
        
        except Exception as e:
            return -1, "", str(e)
    
    def _get_git_status(self, project_path: Path) -> Dict:
        """获取 git 状态"""
        # 获取状态
        code, stdout, stderr = self._run_git(project_path, ["status", "--porcelain"], check=False)
        
        if code != 0:
            return {"error": stderr}
        
        added = []
        modified = []
        deleted = []
        untracked = []
        
        for line in stdout.strip().split('\n'):
            if not line:
                continue
            
            status = line[:2]
            file_path = line[3:].strip()
            
            if status.startswith('A') or status.endswith('A'):
                added.append(file_path)
            elif status.startswith('M') or status.endswith('M'):
                modified.append(file_path)
            elif status.startswith('D') or status.endswith('D'):
                deleted.append(file_path)
            elif status == '??':
                untracked.append(file_path)
        
        return {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "untracked": untracked,
            "total": len(added) + len(modified) + len(deleted) + len(untracked)
        }
    
    def _generate_commit_message(self, changes: Dict, project_path: Path) -> str:
        """智能生成提交信息"""
        if not self.config["commit_message"]["generate_message"]:
            return f"Auto commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 分析变更类型
        types_count = defaultdict(int)
        
        all_files = changes.get("added", []) + changes.get("modified", []) + changes.get("deleted", [])
        
        for file in all_files:
            ext = Path(file).suffix.lower()
            
            if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']:
                types_count["feat"] += 1
            elif ext in ['.md', '.txt', '.rst']:
                types_count["docs"] += 1
            elif ext in ['.css', '.scss', '.less', '.html']:
                types_count["style"] += 1
            elif 'test' in file.lower():
                types_count["test"] += 1
            elif ext in ['.json', '.yaml', '.yml', '.toml']:
                types_count["chore"] += 1
            else:
                types_count["chore"] += 1
        
        # 确定主要类型
        main_type = max(types_count, key=types_count.get) if types_count else "chore"
        
        # 生成摘要
        summaries = []
        
        if changes.get("added"):
            summaries.append(f"添加 {len(changes['added'])} 个文件")
        
        if changes.get("modified"):
            summaries.append(f"修改 {len(changes['modified'])} 个文件")
        
        if changes.get("deleted"):
            summaries.append(f"删除 {len(changes['deleted'])} 个文件")
        
        summary = "，".join(summaries) if summaries else "自动提交"
        
        # 生成完整消息
        template = self.config["commit_message"]["template"]
        message = template.format(
            type=main_type,
            summary=summary,
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 添加详细变更（可选）
        if self.config["auto_commit"]["include_diff_summary"] and all_files:
            message += "\n\n变更详情:\n"
            for file in all_files[:10]:  # 最多显示10个文件
                message += f"- {file}\n"
            
            if len(all_files) > 10:
                message += f"... 还有 {len(all_files) - 10} 个文件\n"
        
        return message
    
    def init_project(self, project_path: Path, repo_name: Optional[str] = None) -> Dict:
        """初始化项目"""
        print(f"初始化项目: {project_path}")
        
        # 检查是否是 git 仓库
        git_dir = project_path / ".git"
        
        if not git_dir.exists():
            # 初始化 git 仓库
            code, stdout, stderr = self._run_git(project_path, ["init"])
            
            if code != 0:
                return {"success": False, "error": f"Git 初始化失败: {stderr}"}
            
            print("  ✓ Git 仓库已初始化")
            
            # 创建 .gitignore
            gitignore_path = project_path / ".gitignore"
            if not gitignore_path.exists():
                gitignore_content = self._generate_gitignore(project_path)
                with open(gitignore_path, 'w', encoding='utf-8') as f:
                    f.write(gitignore_content)
                print("  ✓ .gitignore 已创建")
            
            # 创建 README
            readme_path = project_path / "README.md"
            if not readme_path.exists():
                readme_content = self._generate_readme(project_path, repo_name)
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                print("  ✓ README.md 已创建")
        
        # 配置 GitHub 远程
        remote_result = self._setup_remote(project_path, repo_name)
        
        if not remote_result.get("success"):
            return remote_result
        
        # 添加到项目管理
        project_id = hashlib.md5(str(project_path).encode()).hexdigest()[:12]
        self.projects[project_id] = asdict(ProjectConfig(
            path=str(project_path),
            repo_name=repo_name
        ))
        
        self._save_state()
        
        return {
            "success": True,
            "project_id": project_id,
            "path": str(project_path),
            "repo_name": repo_name
        }
    
    def _generate_gitignore(self, project_path: Path) -> str:
        """生成 .gitignore"""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Logs
logs/
*.log

# Temp
temp/
tmp/
.cache/

# Large files
*.zip
*.tar.gz
*.rar
*.7z
*.exe
*.dll
*.pdb

# Database
*.db
*.sqlite
*.sqlite3

# Secrets
.env
.env.local
secrets.json
config.local.json
"""
    
    def _generate_readme(self, project_path: Path, repo_name: Optional[str]) -> str:
        """生成 README"""
        project_name = repo_name or project_path.name
        
        # 获取项目结构
        structure = []
        for item in project_path.iterdir():
            if item.name.startswith('.') or item.name.startswith('__'):
                continue
            
            if item.is_dir():
                structure.append(f"{item.name}/")
            else:
                structure.append(item.name)
        
        structure_str = "\n".join(f"  - {s}" for s in structure[:10])
        
        return f"""# {project_name}

{project_name} 项目

## 项目结构

```
{structure_str}
```

## 使用说明

请补充使用说明...

## 开发

请补充开发说明...

## 许可证

MIT
"""
    
    def _setup_remote(self, project_path: Path, repo_name: Optional[str]) -> Dict:
        """设置 GitHub 远程仓库"""
        # 获取 GitHub token
        token = os.environ.get("GITHUB_TOKEN")
        username = os.environ.get("GITHUB_USERNAME")
        
        if not token or not username:
            return {
                "success": False,
                "error": "未配置 GITHUB_TOKEN 或 GITHUB_USERNAME 环境变量"
            }
        
        # 检查远程仓库
        code, stdout, stderr = self._run_git(project_path, ["remote", "-v"], check=False)
        
        if "origin" in stdout:
            print("  ✓ 远程仓库已配置")
            return {"success": True}
        
        # 创建 GitHub 仓库
        repo_name = repo_name or project_path.name
        
        import urllib.request
        import ssl
        
        ctx = create_ssl_context()
        
        data = json.dumps({
            "name": repo_name,
            "private": False,
            "auto_init": False
        }).encode()
        
        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=data,
            headers={
                "Authorization": f"token {token}",
                "Content-Type": "application/json",
                "User-Agent": "GitHub-Auto-Commit"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                repo_data = json.loads(response.read().decode())
                repo_url = repo_data["clone_url"].replace("https://", f"https://{token}@")
                
                # 添加远程仓库
                code, stdout, stderr = self._run_git(project_path, ["remote", "add", "origin", repo_url])
                
                if code != 0:
                    return {"success": False, "error": f"添加远程仓库失败: {stderr}"}
                
                print(f"  ✓ GitHub 仓库已创建: {repo_data['html_url']}")
                return {"success": True, "repo_url": repo_data['html_url']}
        
        except Exception as e:
            return {"success": False, "error": f"创建 GitHub 仓库失败: {e}"}
    
    def auto_commit(self, project_path: Path, dry_run: bool = False) -> Dict:
        """自动提交"""
        print(f"自动提交项目: {project_path}")
        
        # 检查是否是 git 仓库
        git_dir = project_path / ".git"
        if not git_dir.exists():
            print("  项目未初始化，正在初始化...")
            init_result = self.init_project(project_path)
            if not init_result.get("success"):
                return init_result
        
        # 获取状态
        status = self._get_git_status(project_path)
        
        if "error" in status:
            return {"success": False, "error": status["error"]}
        
        total_changes = status.get("total", 0)
        
        if total_changes == 0:
            print("  没有变更需要提交")
            return {"success": True, "committed": False, "reason": "no_changes"}
        
        print(f"  发现 {total_changes} 个变更:")
        print(f"    - 新增: {len(status.get('added', []))}")
        print(f"    - 修改: {len(status.get('modified', []))}")
        print(f"    - 删除: {len(status.get('deleted', []))}")
        print(f"    - 未跟踪: {len(status.get('untracked', []))}")
        
        if dry_run:
            return {"success": True, "committed": False, "dry_run": True, "changes": status}
        
        # 添加所有变更
        if status.get("untracked"):
            self._run_git(project_path, ["add"] + status["untracked"])
            print(f"  ✓ 添加了 {len(status['untracked'])} 个新文件")
        
        if status.get("modified"):
            self._run_git(project_path, ["add"] + status["modified"])
            print(f"  ✓ 添加了 {len(status['modified'])} 个修改的文件")
        
        if status.get("deleted"):
            self._run_git(project_path, ["add", "-u"])
            print(f"  ✓ 标记了 {len(status['deleted'])} 个删除的文件")
        
        # 生成提交信息
        commit_message = self._generate_commit_message(status, project_path)
        
        # 提交
        code, stdout, stderr = self._run_git(project_path, ["commit", "-m", commit_message])
        
        if code != 0:
            return {"success": False, "error": f"提交失败: {stderr}"}
        
        print(f"  ✓ 已提交: {commit_message.split(chr(10))[0]}")
        
        # 推送
        if self.config["auto_commit"]["auto_push"]:
            code, stdout, stderr = self._run_git(project_path, ["push", "origin", "HEAD"])
            
            if code != 0:
                # 尝试设置上游分支
                code, stdout, stderr = self._run_git(project_path, ["push", "-u", "origin", "HEAD"])
            
            if code == 0:
                print("  ✓ 已推送到远程")
            else:
                print(f"  ⚠ 推送失败: {stderr}")
        
        # 更新项目状态
        project_id = hashlib.md5(str(project_path).encode()).hexdigest()[:12]
        if project_id in self.projects:
            self.projects[project_id]["last_commit"] = datetime.now().isoformat()
            self._save_state()
        
        return {
            "success": True,
            "committed": True,
            "changes": total_changes,
            "message": commit_message.split(chr(10))[0]
        }
    
    def watch_project(self, project_path: Path):
        """监控项目变更"""
        print(f"开始监控项目: {project_path}")
        print(f"检查间隔: {self.config['auto_commit']['interval_minutes']} 分钟")
        print("按 Ctrl+C 停止监控")
        print()
        
        try:
            while True:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查变更...")
                
                result = self.auto_commit(project_path)
                
                if result.get("committed"):
                    print(f"  ✓ 自动提交成功")
                elif result.get("reason") == "no_changes":
                    print(f"  - 无变更")
                else:
                    print(f"  ✗ {result.get('error', '未知错误')}")
                
                # 等待下一次检查
                interval = self.config["auto_commit"]["interval_minutes"] * 60
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    def get_status(self, project_path: Path) -> Dict:
        """获取项目状态"""
        git_dir = project_path / ".git"
        
        if not git_dir.exists():
            return {
                "initialized": False,
                "path": str(project_path)
            }
        
        # 获取 git 状态
        status = self._get_git_status(project_path)
        
        # 获取分支信息
        code, stdout, stderr = self._run_git(project_path, ["branch", "-v"], check=False)
        branch_info = stdout.strip()
        
        # 获取远程信息
        code, stdout, stderr = self._run_git(project_path, ["remote", "-v"], check=False)
        remote_info = stdout.strip()
        
        # 获取最近提交
        code, stdout, stderr = self._run_git(project_path, ["log", "-1", "--oneline"], check=False)
        last_commit = stdout.strip() if code == 0 else None
        
        project_id = hashlib.md5(str(project_path).encode()).hexdigest()[:12]
        project_config = self.projects.get(project_id, {})
        
        return {
            "initialized": True,
            "path": str(project_path),
            "branch": branch_info,
            "remote": remote_info,
            "last_commit": last_commit,
            "changes": status,
            "auto_commit_enabled": project_config.get("auto_commit", True),
            "last_auto_commit": project_config.get("last_commit")
        }
    
    def create_backup(self, project_path: Path) -> Dict:
        """创建备份"""
        if not self.config["backup"]["enabled"]:
            return {"success": False, "error": "备份功能未启用"}
        
        backup_dir = Path(self.config["backup"]["backup_dir"])
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = project_path.name
        backup_name = f"{project_name}_{timestamp}.zip"
        backup_path = backup_dir / backup_name
        
        try:
            # 创建 zip 备份
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in project_path.rglob("*"):
                    # 跳过 .git 目录
                    if ".git" in str(item.relative_to(project_path)):
                        continue
                    
                    if item.is_file():
                        zipf.write(item, item.relative_to(project_path))
            
            print(f"✓ 备份已创建: {backup_path}")
            
            # 清理旧备份
            self._cleanup_old_backups(project_name, backup_dir)
            
            return {
                "success": True,
                "backup_path": str(backup_path),
                "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _cleanup_old_backups(self, project_name: str, backup_dir: Path):
        """清理旧备份"""
        max_backups = self.config["backup"]["max_backups"]
        
        backups = sorted(
            backup_dir.glob(f"{project_name}_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[max_backups:]:
            old_backup.unlink()
            print(f"  已删除旧备份: {old_backup.name}")
    
    def create_tag(self, project_path: Path, tag_name: str, message: Optional[str] = None) -> Dict:
        """创建标签"""
        # 创建标签
        tag_message = message or f"Release {tag_name}"
        
        code, stdout, stderr = self._run_git(project_path, ["tag", "-a", tag_name, "-m", tag_message])
        
        if code != 0:
            return {"success": False, "error": f"创建标签失败: {stderr}"}
        
        # 推送标签
        code, stdout, stderr = self._run_git(project_path, ["push", "origin", tag_name])
        
        if code != 0:
            return {"success": False, "error": f"推送标签失败: {stderr}"}
        
        return {
            "success": True,
            "tag": tag_name,
            "message": tag_message
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
    auto_commit = GitHubAutoCommit()
    
    if cmd == "init":
        if len(sys.argv) < 3:
            print("用法: github_auto_commit.py init <project_path> [repo_name]")
            return
        
        project_path = Path(sys.argv[2])
        repo_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = auto_commit.init_project(project_path, repo_name)
        
        if result.get("success"):
            print(f"\n✓ 项目初始化成功")
            print(f"  项目ID: {result['project_id']}")
        else:
            print(f"\n✗ 初始化失败: {result.get('error')}")
    
    elif cmd == "auto":
        if len(sys.argv) < 3:
            print("用法: github_auto_commit.py auto <project_path>")
            return
        
        project_path = Path(sys.argv[2])
        dry_run = "--dry-run" in sys.argv
        
        result = auto_commit.auto_commit(project_path, dry_run)
        
        if result.get("success"):
            if result.get("committed"):
                print(f"\n✓ 提交成功")
                print(f"  变更数: {result['changes']}")
                print(f"  提交信息: {result['message']}")
            else:
                print(f"\n- {result.get('reason', '未提交')}")
        else:
            print(f"\n✗ 提交失败: {result.get('error')}")
    
    elif cmd == "watch":
        if len(sys.argv) < 3:
            print("用法: github_auto_commit.py watch <project_path>")
            return
        
        project_path = Path(sys.argv[2])
        auto_commit.watch_project(project_path)
    
    elif cmd == "status":
        if len(sys.argv) < 3:
            print("用法: github_auto_commit.py status <project_path>")
            return
        
        project_path = Path(sys.argv[2])
        status = auto_commit.get_status(project_path)
        
        print("项目状态:")
        print("-" * 40)
        print(f"路径: {status['path']}")
        print(f"已初始化: {'是' if status['initialized'] else '否'}")
        
        if status['initialized']:
            print(f"\n分支: {status['branch']}")
            print(f"\n远程仓库:\n{status['remote']}")
            print(f"\n最近提交: {status['last_commit']}")
            
            changes = status['changes']
            print(f"\n待提交变更: {changes.get('total', 0)} 个")
            if changes.get('total', 0) > 0:
                print(f"  - 新增: {len(changes.get('added', []))}")
                print(f"  - 修改: {len(changes.get('modified', []))}")
                print(f"  - 删除: {len(changes.get('deleted', []))}")
            
            print(f"\n自动提交: {'启用' if status['auto_commit_enabled'] else '禁用'}")
            if status['last_auto_commit']:
                print(f"上次自动提交: {status['last_auto_commit']}")
    
    elif cmd == "backup":
        if len(sys.argv) < 3:
            print("用法: github_auto_commit.py backup <project_path>")
            return
        
        project_path = Path(sys.argv[2])
        result = auto_commit.create_backup(project_path)
        
        if result.get("success"):
            print(f"✓ 备份创建成功")
            print(f"  路径: {result['backup_path']}")
            print(f"  大小: {result['size_mb']:.2f} MB")
        else:
            print(f"✗ 备份失败: {result.get('error')}")
    
    elif cmd == "tag":
        if len(sys.argv) < 4:
            print("用法: github_auto_commit.py tag <project_path> <tag_name> [message]")
            return
        
        project_path = Path(sys.argv[2])
        tag_name = sys.argv[3]
        message = sys.argv[4] if len(sys.argv) > 4 else None
        
        result = auto_commit.create_tag(project_path, tag_name, message)
        
        if result.get("success"):
            print(f"✓ 标签创建成功: {result['tag']}")
        else:
            print(f"✗ 标签创建失败: {result.get('error')}")
    
    elif cmd == "mcp":
        # MCP 服务器模式
        print("GitHub 自动提交 MCP 服务器已启动")
        print("支持操作: init, auto, status, backup, tag")
        
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
                    
                    project_path = Path(params.get("path", "."))
                    
                    if action == "init":
                        response = auto_commit.init_project(project_path, params.get("repo_name"))
                    elif action == "auto":
                        response = auto_commit.auto_commit(project_path, params.get("dry_run", False))
                    elif action == "status":
                        response = auto_commit.get_status(project_path)
                    elif action == "backup":
                        response = auto_commit.create_backup(project_path)
                    elif action == "tag":
                        response = auto_commit.create_tag(project_path, params.get("tag"), params.get("message"))
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
