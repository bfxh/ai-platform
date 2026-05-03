#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub仓库同步技能

功能:
- 克隆仓库
- 拉取最新代码
- 推送代码
- 同步分支
- 同步标签
- 同步问题
- 同步PR
- 备份仓库
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubRepoSync(Skill):
    """GitHub仓库同步技能"""

    name = "github_repo_sync"
    description = "GitHub仓库同步 - 克隆、拉取、推送、同步分支和标签，备份仓库"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.owner = self.config.get("owner", "")
        self.repo = self.config.get("repo", "")
        self.token = self.config.get("token", os.getenv("GITHUB_TOKEN", ""))
        self.api_base = "https://api.github.com"
        self.local_repos_dir = self.config.get("local_repos_dir", "/python/GitHub/repos")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubRepoSync/1.0",
            "Authorization": f"token {self.token}" if self.token else ""
        })
        self._ensure_local_repos_dir()


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _ensure_local_repos_dir(self):
        """确保本地仓库目录存在"""
        Path(self.local_repos_dir).mkdir(parents=True, exist_ok=True)

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        if action == "clone_repo":
            return self._clone_repo(params)
        elif action == "pull_repo":
            return self._pull_repo(params)
        elif action == "push_repo":
            return self._push_repo(params)
        elif action == "sync_branches":
            return self._sync_branches(params)
        elif action == "sync_tags":
            return self._sync_tags(params)
        elif action == "sync_issues":
            return self._sync_issues(params)
        elif action == "sync_pulls":
            return self._sync_pulls(params)
        elif action == "backup_repo":
            return self._backup_repo(params)
        elif action == "list_local_repos":
            return self._list_local_repos(params)
        elif action == "get_repo_info":
            return self._get_repo_info(params)
        elif action == "create_local_backup":
            return self._create_local_backup(params)
        else:
            return {"success": False, "error": f"未知动作: {action}"}

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.api_base}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PATCH":
                response = self.session.patch(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                return {"success": False, "error": f"不支持的方法: {method}"}

            if response.status_code in [200, 201, 204]:
                return {"success": True, "data": response.json() if response.content else {}}
            else:
                return {"success": False, "error": f"API错误: {response.status_code}", "details": response.text}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _run_git_command(self, command: List[str], cwd: str = None) -> Dict:
        """运行git命令"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _clone_repo(self, params: Dict) -> Dict:
        """克隆仓库"""
        repo_url = params.get("repo_url")
        branch = params.get("branch", "main")

        if not repo_url:
            return {"success": False, "error": "缺少repo_url参数"}

        local_path = params.get("local_path", os.path.join(self.local_repos_dir, repo_url.split("/")[-1].replace(".git", "")))

        git_url = repo_url
        if self.token and "github.com" in git_url:
            git_url = git_url.replace("https://", f"https://{self.token}@")

        result = self._run_git_command(["git", "clone", "-b", branch, git_url, local_path])

        if result.get("success"):
            return {
                "success": True,
                "message": f"仓库已克隆到: {local_path}",
                "local_path": local_path
            }

        return result

    def _pull_repo(self, params: Dict) -> Dict:
        """拉取最新代码"""
        local_path = params.get("local_path")
        branch = params.get("branch", "main")

        if not local_path:
            return {"success": False, "error": "缺少local_path参数"}

        os.chdir(local_path)

        result = self._run_git_command(["git", "fetch", "--all"], cwd=local_path)
        if not result.get("success"):
            return result

        result = self._run_git_command(["git", "pull", "origin", branch], cwd=local_path)

        if result.get("success"):
            return {
                "success": True,
                "message": f"已拉取最新代码到: {local_path}",
                "output": result.get("stdout", "")
            }

        return result

    def _push_repo(self, params: Dict) -> Dict:
        """推送代码"""
        local_path = params.get("local_path")
        branch = params.get("branch", "main")
        commit_message = params.get("commit_message", "Update")

        if not local_path:
            return {"success": False, "error": "缺少local_path参数"}

        result = self._run_git_command(["git", "add", "."], cwd=local_path)
        if not result.get("success"):
            return result

        result = self._run_git_command(["git", "commit", "-m", commit_message], cwd=local_path)
        if not result.get("success"):
            return result

        result = self._run_git_command(["git", "push", "origin", branch], cwd=local_path)

        if result.get("success"):
            return {
                "success": True,
                "message": f"已推送代码到: {branch}",
                "output": result.get("stdout", "")
            }

        return result

    def _sync_branches(self, params: Dict) -> Dict:
        """同步分支"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        local_path = params.get("local_path")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/branches", None)

        if not result.get("success"):
            return result

        branches = result["data"]
        synced_branches = []

        if local_path:
            os.chdir(local_path)
            for branch in branches:
                branch_name = branch.get("name")
                result = self._run_git_command(["git", "fetch", "origin", f"refs/heads/{branch_name}:refs/remotes/origin/{branch_name}"], cwd=local_path)
                if result.get("success"):
                    synced_branches.append(branch_name)

        return {
            "success": True,
            "synced_branches": synced_branches,
            "total_branches": len(branches)
        }

    def _sync_tags(self, params: Dict) -> Dict:
        """同步标签"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        local_path = params.get("local_path")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/tags", None)

        if not result.get("success"):
            return result

        tags = result["data"]
        synced_tags = []

        if local_path:
            os.chdir(local_path)
            for tag in tags:
                tag_name = tag.get("name")
                result = self._run_git_command(["git", "fetch", "origin", f"refs/tags/{tag_name}:refs/tags/{tag_name}"], cwd=local_path)
                if result.get("success"):
                    synced_tags.append(tag_name)

        return {
            "success": True,
            "synced_tags": synced_tags,
            "total_tags": len(tags)
        }

    def _sync_issues(self, params: Dict) -> Dict:
        """同步问题"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        state = params.get("state", "open")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/issues?state={state}&per_page=100", None)

        if not result.get("success"):
            return result

        issues = result["data"]
        backup_file = os.path.join(self.local_repos_dir, f"{repo}_issues_{state}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "synced_issues": len(issues),
            "backup_file": backup_file
        }

    def _sync_pulls(self, params: Dict) -> Dict:
        """同步PR"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        state = params.get("state", "open")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/pulls?state={state}&per_page=100", None)

        if not result.get("success"):
            return result

        pulls = result["data"]
        backup_file = os.path.join(self.local_repos_dir, f"{repo}_pulls_{state}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(pulls, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "synced_pulls": len(pulls),
            "backup_file": backup_file
        }

    def _backup_repo(self, params: Dict) -> Dict:
        """备份仓库"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        backup_file = os.path.join(self.local_repos_dir, f"{repo}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz")

        result = self._run_git_command([
            "git", "clone", "--mirror",
            f"https://github.com/{owner}/{repo}.git",
            backup_file.replace(".tar.gz", ".git")
        ])

        if result.get("success"):
            return {
                "success": True,
                "message": f"仓库已备份到: {backup_file}",
                "backup_path": backup_file
            }

        return result

    def _list_local_repos(self, params: Dict) -> Dict:
        """列出本地仓库"""
        repos = []
        for item in os.listdir(self.local_repos_dir):
            item_path = os.path.join(self.local_repos_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, ".git")):
                repos.append({
                    "name": item,
                    "path": item_path,
                    "size": sum(os.path.getsize(os.path.join(dirpath, filename))
                                for dirpath, _, filenames in os.walk(item_path)
                                for filename in filenames)
                })

        return {
            "success": True,
            "repos": repos,
            "total": len(repos)
        }

    def _get_repo_info(self, params: Dict) -> Dict:
        """获取仓库信息"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        return self._make_request("GET", f"/repos/{owner}/{repo}", None)

    def _create_local_backup(self, params: Dict) -> Dict:
        """创建本地备份"""
        repo_name = params.get("repo_name")

        if not repo_name:
            return {"success": False, "error": "缺少repo_name参数"}

        repo_path = os.path.join(self.local_repos_dir, repo_name)

        if not os.path.exists(os.path.join(repo_path, ".git")):
            return {"success": False, "error": f"本地仓库不存在: {repo_path}"}

        backup_file = os.path.join(self.local_repos_dir, f"{repo_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz")

        result = self._run_git_command(["git", "archive", "-o", backup_file, "HEAD"], cwd=repo_path)

        if result.get("success"):
            return {
                "success": True,
                "message": f"本地备份已创建: {backup_file}",
                "backup_path": backup_file
            }

        return result


skill = GitHubRepoSync()
