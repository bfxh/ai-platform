#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 自动上传工作流

功能：
- 自动初始化Git仓库
- 自动配置GitHub远程
- 自动提交并推送代码
- 支持批量文件处理
- 智能冲突解决

用法：
    python github_workflow.py init <project_path> [repo_name]
    python github_workflow.py add <project_path> [files...]
    python github_workflow.py commit <project_path> "message"
    python github_workflow.py push <project_path>
    python github_workflow.py auto <project_path> [repo_name]
    python github_workflow.py status <project_path>

MCP调用：
    {"tool": "github_workflow", "action": "auto_upload", "params": {...}}
"""

import json
import sys
import os
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================
# 配置
# ============================================================
GITHUB_API = "https://api.github.com"
DEFAULT_BRANCH = "main"

# Git忽略模板
GITIGNORE_TEMPLATE = """
# Python
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

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

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
"""

# README模板
README_TEMPLATE = """# {project_name}

{description}

## 项目结构

```
{structure}
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 作者

{author}

## 许可证

MIT
"""

# ============================================================
# GitHub工作流类
# ============================================================
class GitHubWorkflow:
    """GitHub自动上传工作流"""
    
    def __init__(self):
        self.token = self._get_token()
        self.username = self._get_username()
    
    def _get_token(self) -> Optional[str]:
        """获取GitHub Token"""
        # 从环境变量获取
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        
        if not token:
            # 尝试从git配置获取
            try:
                result = subprocess.run(
                    ["git", "config", "--global", "github.token"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    token = result.stdout.strip()
            except:
                pass
        
        return token
    
    def _get_username(self) -> Optional[str]:
        """获取GitHub用户名"""
        # 从git配置获取
        try:
            result = subprocess.run(
                ["git", "config", "--global", "user.name"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        # 从环境变量获取
        return os.environ.get("GITHUB_USERNAME")
    
    def _run_git(self, cwd: Path, args: List[str]) -> Dict:
        """运行git命令"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_config(self) -> Dict:
        """检查Git配置"""
        configs = {}
        
        for key in ["user.name", "user.email", "github.token"]:
            result = subprocess.run(
                ["git", "config", "--global", key],
                capture_output=True,
                text=True
            )
            configs[key] = result.stdout.strip() if result.returncode == 0 else None
        
        missing = [k for k, v in configs.items() if not v]
        
        if missing:
            return {
                "success": False,
                "error": f"缺少Git配置: {', '.join(missing)}",
                "configs": configs,
                "setup_guide": """
请配置Git：
    git config --global user.name "Your Name"
    git config --global user.email "your@email.com"
    git config --global github.token "your_github_token"

或在环境变量中设置：
    GITHUB_TOKEN=your_token
"""
            }
        
        return {
            "success": True,
            "configs": configs
        }
    
    def init_repo(self, project_path: str, repo_name: Optional[str] = None) -> Dict:
        """初始化仓库"""
        path = Path(project_path).resolve()
        
        if not path.exists():
            return {"success": False, "error": f"路径不存在: {path}"}
        
        repo_name = repo_name or path.name
        
        # 检查是否已是git仓库
        git_dir = path / ".git"
        if git_dir.exists():
            return {"success": True, "message": "已是Git仓库", "path": str(path)}
        
        # 初始化git
        result = self._run_git(path, ["init"])
        if not result.get("success"):
            return result
        
        # 创建.gitignore
        gitignore_path = path / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(GITIGNORE_TEMPLATE)
        
        # 创建README.md
        readme_path = path / "README.md"
        if not readme_path.exists():
            # 生成项目结构
            structure = self._generate_structure(path)
            
            readme_content = README_TEMPLATE.format(
                project_name=repo_name,
                description=f"{repo_name} 项目",
                structure=structure,
                author=self.username or "Anonymous"
            )
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        
        # 配置远程仓库
        if self.token and self.username:
            remote_url = f"https://{self.token}@github.com/{self.username}/{repo_name}.git"
            self._run_git(path, ["remote", "add", "origin", remote_url])
        
        return {
            "success": True,
            "message": f"已初始化仓库: {repo_name}",
            "path": str(path),
            "repo_name": repo_name
        }
    
    def _generate_structure(self, path: Path, prefix: str = "") -> str:
        """生成目录结构"""
        lines = []
        
        try:
            items = sorted(path.iterdir())
        except:
            return ""
        
        # 过滤
        ignore_patterns = ['.git', '__pycache__', '.pyc', '.cache', 'node_modules']
        items = [i for i in items if not any(p in str(i) for p in ignore_patterns)]
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir() and not item.is_symlink():
                extension = "    " if is_last else "│   "
                sub_structure = self._generate_structure(item, prefix + extension)
                if sub_structure:
                    lines.append(sub_structure)
        
        return "\n".join(lines)
    
    def add_files(self, project_path: str, files: Optional[List[str]] = None) -> Dict:
        """添加文件到暂存区"""
        path = Path(project_path).resolve()
        
        if files:
            # 添加指定文件
            for file in files:
                result = self._run_git(path, ["add", file])
                if not result.get("success"):
                    return result
        else:
            # 添加所有文件
            result = self._run_git(path, ["add", "."])
            if not result.get("success"):
                return result
        
        # 检查状态
        result = self._run_git(path, ["status", "--short"])
        
        return {
            "success": True,
            "message": "文件已添加到暂存区",
            "status": result.get("stdout", "")
        }
    
    def commit(self, project_path: str, message: Optional[str] = None) -> Dict:
        """提交更改"""
        path = Path(project_path).resolve()
        
        # 检查是否有更改
        status = self._run_git(path, ["status", "--porcelain"])
        if not status.get("stdout", "").strip():
            return {"success": True, "message": "没有需要提交的更改"}
        
        # 生成提交信息
        if not message:
            message = f"Update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        result = self._run_git(path, ["commit", "-m", message])
        
        return {
            "success": result.get("success"),
            "message": result.get("stdout") if result.get("success") else result.get("stderr"),
            "commit_message": message
        }
    
    def push(self, project_path: str, branch: str = "main") -> Dict:
        """推送到远程"""
        path = Path(project_path).resolve()
        
        # 检查远程仓库
        remote = self._run_git(path, ["remote", "-v"])
        if not remote.get("stdout", "").strip():
            return {"success": False, "error": "没有配置远程仓库"}
        
        # 设置分支名
        current_branch = self._run_git(path, ["branch", "--show-current"])
        if current_branch.get("success"):
            branch = current_branch.get("stdout", "").strip() or branch
        
        # 推送
        result = self._run_git(path, ["push", "-u", "origin", branch])
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"已推送到 {branch} 分支",
                "branch": branch
            }
        
        # 尝试处理冲突
        if "rejected" in result.get("stderr", "").lower():
            # 先拉取
            pull_result = self._run_git(path, ["pull", "origin", branch, "--rebase"])
            if pull_result.get("success"):
                # 再次推送
                result = self._run_git(path, ["push", "origin", branch])
        
        return {
            "success": result.get("success"),
            "message": result.get("stdout") if result.get("success") else result.get("stderr")
        }
    
    def auto_upload(self, project_path: str, repo_name: Optional[str] = None) -> Dict:
        """自动上传完整流程"""
        path = Path(project_path).resolve()
        
        print(f"开始自动上传: {path}")
        
        # 1. 检查配置
        print("1. 检查Git配置...")
        config = self.check_config()
        if not config.get("success"):
            return config
        print("  ✓ Git配置正常")
        
        # 2. 初始化仓库
        print("2. 初始化仓库...")
        init = self.init_repo(str(path), repo_name)
        if not init.get("success"):
            return init
        print(f"  ✓ 仓库已初始化: {init.get('repo_name')}")
        
        # 3. 添加文件
        print("3. 添加文件...")
        add = self.add_files(str(path))
        if not add.get("success"):
            return add
        print(f"  ✓ 文件已添加")
        
        # 4. 提交
        print("4. 提交更改...")
        commit = self.commit(str(path), f"Auto commit at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if not commit.get("success"):
            return commit
        print(f"  ✓ 已提交: {commit.get('commit_message')}")
        
        # 5. 推送
        print("5. 推送到GitHub...")
        push = self.push(str(path))
        if not push.get("success"):
            return push
        print(f"  ✓ 已推送到 {push.get('branch')} 分支")
        
        return {
            "success": True,
            "message": "自动上传完成",
            "repo_name": init.get("repo_name"),
            "branch": push.get("branch"),
            "url": f"https://github.com/{self.username}/{init.get('repo_name')}"
        }
    
    def status(self, project_path: str) -> Dict:
        """查看仓库状态"""
        path = Path(project_path).resolve()
        
        # 检查是否是git仓库
        git_dir = path / ".git"
        if not git_dir.exists():
            return {"success": False, "error": "不是Git仓库"}
        
        # 获取状态
        status_result = self._run_git(path, ["status"])
        
        # 获取日志
        log_result = self._run_git(path, ["log", "--oneline", "-5"])
        
        # 获取分支
        branch_result = self._run_git(path, ["branch", "-v"])
        
        return {
            "success": True,
            "status": status_result.get("stdout", ""),
            "recent_commits": log_result.get("stdout", "").split("\n") if log_result.get("success") else [],
            "branches": branch_result.get("stdout", "").split("\n") if branch_result.get("success") else []
        }

# ============================================================
# MCP 接口
# ============================================================
class GitHubWorkflowMCP:
    """GitHub工作流MCP接口"""
    
    def __init__(self):
        self.workflow = GitHubWorkflow()
    
    def handle(self, request: Dict) -> Dict:
        """处理MCP请求"""
        action = request.get("action")
        params = request.get("params", {})
        
        handlers = {
            "check_config": self._handle_check_config,
            "init_repo": self._handle_init_repo,
            "add_files": self._handle_add_files,
            "commit": self._handle_commit,
            "push": self._handle_push,
            "auto_upload": self._handle_auto_upload,
            "status": self._handle_status,
        }
        
        if action in handlers:
            return handlers[action](params)
        
        return {"success": False, "error": f"未知操作: {action}"}
    
    def _handle_check_config(self, params: Dict) -> Dict:
        return self.workflow.check_config()
    
    def _handle_init_repo(self, params: Dict) -> Dict:
        return self.workflow.init_repo(
            params.get("project_path"),
            params.get("repo_name")
        )
    
    def _handle_add_files(self, params: Dict) -> Dict:
        return self.workflow.add_files(
            params.get("project_path"),
            params.get("files")
        )
    
    def _handle_commit(self, params: Dict) -> Dict:
        return self.workflow.commit(
            params.get("project_path"),
            params.get("message")
        )
    
    def _handle_push(self, params: Dict) -> Dict:
        return self.workflow.push(
            params.get("project_path"),
            params.get("branch", "main")
        )
    
    def _handle_auto_upload(self, params: Dict) -> Dict:
        return self.workflow.auto_upload(
            params.get("project_path"),
            params.get("repo_name")
        )
    
    def _handle_status(self, params: Dict) -> Dict:
        return self.workflow.status(params.get("project_path"))

# ============================================================
# 命令行接口
# ============================================================
def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    workflow = GitHubWorkflow()
    
    if cmd == "init":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py init <project_path> [repo_name]")
            return
        
        project_path = sys.argv[2]
        repo_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = workflow.init_repo(project_path, repo_name)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py add <project_path> [files...]")
            return
        
        project_path = sys.argv[2]
        files = sys.argv[3:] if len(sys.argv) > 3 else None
        
        result = workflow.add_files(project_path, files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "commit":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py commit <project_path> [message]")
            return
        
        project_path = sys.argv[2]
        message = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = workflow.commit(project_path, message)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "push":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py push <project_path> [branch]")
            return
        
        project_path = sys.argv[2]
        branch = sys.argv[3] if len(sys.argv) > 3 else "main"
        
        result = workflow.push(project_path, branch)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "auto":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py auto <project_path> [repo_name]")
            return
        
        project_path = sys.argv[2]
        repo_name = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = workflow.auto_upload(project_path, repo_name)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "status":
        if len(sys.argv) < 3:
            print("用法: python github_workflow.py status <project_path>")
            return
        
        project_path = sys.argv[2]
        
        result = workflow.status(project_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "mcp":
        # MCP服务器模式
        print("GitHub工作流MCP服务器已启动")
        print("等待MCP调用...")
        
        mcp = GitHubWorkflowMCP()
        
        import select
        
        while True:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    request = json.loads(line)
                    response = mcp.handle(request)
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
