#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GStackCore - 主控制器

协调各模块工作，提供统一的接口
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from github_client import GitHubClient, GitHubResponse


@dataclass
class Task:
    """任务"""
    id: str
    type: str
    params: Dict
    status: str = "pending"
    result: Any = None
    error: str = ""
    created_at: str = ""
    completed_at: str = ""


@dataclass
class GStackConfig:
    """GStack配置"""
    github_token: Optional[str] = None
    cache_dir: str = "/python/GitHub/cache"
    data_dir: str = "/python/GitHub/data"
    log_dir: str = "/python/GitHub/logs"
    max_retries: int = 3
    request_timeout: int = 30


class GStackCore:
    """
    GStack主控制器

    核心职责：
    - 初始化和管理各模块
    - 处理用户请求
    - 协调任务执行
    - 返回统一结果
    """

    def __init__(self, config: Optional[GStackConfig] = None):
        self.config = config or GStackConfig()

        # 初始化GitHub客户端
        self.github = GitHubClient(
            token=self.config.github_token,
            cache_dir=self.config.cache_dir
        )

        # 任务历史
        self.task_history: List[Task] = []
        self.task_counter = 0

        print("[INIT] GStackCore 初始化完成")

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        self.task_counter += 1
        return f"task_{int(time.time())}_{self.task_counter}"

    def _create_task(self, task_type: str, params: Dict) -> Task:
        """创建任务"""
        from datetime import datetime
        task = Task(
            id=self._generate_task_id(),
            type=task_type,
            params=params,
            status="pending",
            created_at=datetime.now().isoformat()
        )
        self.task_history.append(task)
        return task

    def process_natural_language(self, task_description: str) -> Dict:
        """
        处理自然语言任务

        参数：
        - task_description: 自然语言任务描述

        返回：
        - 处理结果
        """
        try:
            from smart_system import SmartSystem
            smart = SmartSystem()
            result = smart.process_task(task_description, self)
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"处理自然语言任务失败: {str(e)}"
            }

    def execute(self, task_type: str, params: Dict) -> Dict:
        """
        执行任务

        参数：
        - task_type: 任务类型
        - params: 任务参数

        返回：
        - 统一的结果格式
        """

        task = self._create_task(task_type, params)

        print(f"\n[TASK] 执行任务: {task_type}")
        print(f"   任务ID: {task.id}")
        print(f"   参数: {params}")

        try:
            # 根据任务类型执行
            if task_type == "get_user":
                result = self._handle_get_user(params)
            elif task_type == "get_repo":
                result = self._handle_get_repo(params)
            elif task_type == "list_repos":
                result = self._handle_list_repos(params)
            elif task_type == "search_repos":
                result = self._handle_search_repos(params)
            elif task_type == "analyze_repo":
                result = self._handle_analyze_repo(params)
            elif task_type == "compare_users":
                result = self._handle_compare_users(params)
            elif task_type == "batch_get":
                result = self._handle_batch_get(params)
            else:
                result = {
                    "success": False,
                    "error": f"未知任务类型: {task_type}"
                }

            # 更新任务状态
            task.status = "completed"
            task.result = result
            from datetime import datetime
            task.completed_at = datetime.now().isoformat()

            print(f"   结果: {'[OK] 成功' if result.get('success') else '[FAIL] 失败'}")
            if not result.get("success"):
                print(f"   错误: {result.get('error')}")

            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            from datetime import datetime
            task.completed_at = datetime.now().isoformat()

            print(f"   [ERROR] 异常: {str(e)}")

            return {
                "success": False,
                "error": str(e),
                "task_id": task.id
            }

    def _handle_get_user(self, params: Dict) -> Dict:
        """获取用户信息"""
        username = params.get("username")
        if not username:
            return {"success": False, "error": "缺少username参数"}

        result = self.github.get_user(username)
        if result.success:
            return {
                "success": True,
                "data": {
                    "username": result.data.get("login"),
                    "name": result.data.get("name"),
                    "bio": result.data.get("bio"),
                    "followers": result.data.get("followers"),
                    "following": result.data.get("following"),
                    "public_repos": result.data.get("public_repos"),
                    "public_gists": result.data.get("public_gists"),
                    "avatar_url": result.data.get("avatar_url"),
                    "html_url": result.data.get("html_url")
                }
            }
        return {"success": False, "error": result.error}

    def _handle_get_repo(self, params: Dict) -> Dict:
        """获取仓库信息"""
        owner = params.get("owner")
        repo = params.get("repo")
        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self.github.get_repo(owner, repo)
        if result.success:
            return {
                "success": True,
                "data": {
                    "name": result.data.get("name"),
                    "full_name": result.data.get("full_name"),
                    "description": result.data.get("description"),
                    "stars": result.data.get("stargazers_count"),
                    "forks": result.data.get("forks_count"),
                    "language": result.data.get("language"),
                    "open_issues": result.data.get("open_issues_count"),
                    "watchers": result.data.get("watchers_count"),
                    "subscribers_count": result.data.get("subscribers_count"),
                    "html_url": result.data.get("html_url")
                }
            }
        return {"success": False, "error": result.error}

    def _handle_list_repos(self, params: Dict) -> Dict:
        """列出用户仓库"""
        username = params.get("username")
        if not username:
            return {"success": False, "error": "缺少username参数"}

        limit = params.get("limit", 10)
        result = self.github.list_repos(username, {"per_page": limit})

        if result.success:
            repos = []
            for r in result.data:
                repos.append({
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count"),
                    "forks": r.get("forks_count"),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at")
                })

            return {
                "success": True,
                "data": repos,
                "count": len(repos)
            }
        return {"success": False, "error": result.error}

    def _handle_search_repos(self, params: Dict) -> Dict:
        """搜索仓库"""
        query = params.get("query")
        if not query:
            return {"success": False, "error": "缺少query参数"}

        limit = params.get("limit", 10)
        result = self.github.search_repos(query, {"per_page": limit, "sort": "stars", "order": "desc"})

        if result.success:
            repos = []
            for r in result.data.get("items", []):
                repos.append({
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count"),
                    "forks": r.get("forks_count"),
                    "language": r.get("language"),
                    "html_url": r.get("html_url")
                })

            return {
                "success": True,
                "data": repos,
                "total": result.data.get("total_count", 0),
                "count": len(repos)
            }
        return {"success": False, "error": result.error}

    def _handle_analyze_repo(self, params: Dict) -> Dict:
        """分析仓库"""
        owner = params.get("owner")
        repo = params.get("repo")
        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        # 获取仓库信息
        repo_result = self.github.get_repo(owner, repo)
        if not repo_result.success:
            return {"success": False, "error": repo_result.error}

        # 获取提交历史
        commits_result = self.github.list_commits(owner, repo, {"per_page": 30})
        if not commits_result.success:
            return {"success": False, "error": commits_result.error}

        # 获取Issues
        issues_result = self.github.get_issues(owner, repo, {"state": "all", "per_page": 30})
        if not issues_result.success:
            return {"success": False, "error": issues_result.error}

        # 获取PRs
        pulls_result = self.github.get_pulls(owner, repo, {"state": "all", "per_page": 30})
        if not pulls_result.success:
            return {"success": False, "error": pulls_result.error}

        # 计算统计数据
        open_issues = [i for i in issues_result.data if i.get("state") == "open"]
        closed_issues = [i for i in issues_result.data if i.get("state") == "closed"]
        open_pulls = [p for p in pulls_result.data if p.get("state") == "open"]
        merged_pulls = [p for p in pulls_result.data if p.get("merged_at")]

        return {
            "success": True,
            "data": {
                "repo": {
                    "name": repo_result.data.get("name"),
                    "full_name": repo_result.data.get("full_name"),
                    "description": repo_result.data.get("description"),
                    "stars": repo_result.data.get("stargazers_count"),
                    "forks": repo_result.data.get("forks_count"),
                    "language": repo_result.data.get("language"),
                    "created_at": repo_result.data.get("created_at"),
                    "pushed_at": repo_result.data.get("pushed_at"),
                    "license": repo_result.data.get("license", {}).get("name")
                },
                "stats": {
                    "total_commits_analyzed": len(commits_result.data),
                    "total_issues": len(issues_result.data),
                    "open_issues": len(open_issues),
                    "closed_issues": len(closed_issues),
                    "issue_close_rate": len(closed_issues) / len(issues_result.data) if issues_result.data else 0,
                    "total_pulls": len(pulls_result.data),
                    "open_pulls": len(open_pulls),
                    "merged_pulls": len(merged_pulls),
                    "merge_rate": len(merged_pulls) / len(pulls_result.data) if pulls_result.data else 0
                },
                "recent_commits": [
                    {
                        "sha": c.get("sha")[:7],
                        "message": c.get("commit", {}).get("message", "").split("\n")[0],
                        "author": c.get("commit", {}).get("author", {}).get("name"),
                        "date": c.get("commit", {}).get("author", {}).get("date")
                    }
                    for c in commits_result.data[:5]
                ]
            }
        }

    def _handle_compare_users(self, params: Dict) -> Dict:
        """比较用户"""
        users = params.get("users", [])
        if len(users) < 2:
            return {"success": False, "error": "至少需要2个用户进行比较"}

        user_data = []
        for username in users[:5]:  # 最多5个用户
            result = self.github.get_user(username)
            if result.success:
                user_data.append({
                    "username": result.data.get("login"),
                    "name": result.data.get("name"),
                    "followers": result.data.get("followers"),
                    "following": result.data.get("following"),
                    "public_repos": result.data.get("public_repos"),
                    "stars_received": result.data.get("followers", 0) * 10  # 估算
                })
            time.sleep(0.5)  # 避免API限制

        return {
            "success": True,
            "data": user_data,
            "count": len(user_data)
        }

    def _handle_batch_get(self, params: Dict) -> Dict:
        """批量获取"""
        items = params.get("items", [])
        item_type = params.get("type", "repo")

        if not items:
            return {"success": False, "error": "缺少items参数"}

        results = []
        for item in items[:20]:  # 最多20个
            if item_type == "repo":
                parts = item.split("/")
                if len(parts) == 2:
                    result = self.github.get_repo(parts[0], parts[1])
                    if result.success:
                        results.append({
                            "name": result.data.get("name"),
                            "full_name": result.data.get("full_name"),
                            "stars": result.data.get("stargazers_count"),
                            "success": True
                        })
                    else:
                        results.append({
                            "name": item,
                            "error": result.error,
                            "success": False
                        })
            elif item_type == "user":
                result = self.github.get_user(item)
                if result.success:
                    results.append({
                        "username": result.data.get("login"),
                        "followers": result.data.get("followers"),
                        "public_repos": result.data.get("public_repos"),
                        "success": True
                    })
                    time.sleep(0.5)
                else:
                    results.append({
                        "username": item,
                        "error": result.error,
                        "success": False
                    })

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "data": results,
            "total": len(results),
            "success_count": success_count,
            "failed_count": len(results) - success_count
        }

    def get_status(self) -> Dict:
        """获取系统状态"""
        rate_limit = self.github.get_rate_limit()

        return {
            "status": "running",
            "tasks_total": len(self.task_history),
            "tasks_completed": sum(1 for t in self.task_history if t.status == "completed"),
            "tasks_failed": sum(1 for t in self.task_history if t.status == "failed"),
            "rate_limit": rate_limit.data.get("resources", {}).get("core", {}) if rate_limit.success else None
        }

    def get_task_history(self, limit: int = 10) -> List[Dict]:
        """获取任务历史"""
        tasks = self.task_history[-limit:] if len(self.task_history) > limit else self.task_history

        return [
            {
                "id": t.id,
                "type": t.type,
                "status": t.status,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
                "error": t.error if t.status == "failed" else None
            }
            for t in reversed(tasks)
        ]


# 简单测试
if __name__ == "__main__":
    print("🧪 测试GStackCore")
    print("=" * 60)

    core = GStackCore()

    # 测试1: 获取用户
    print("\n📝 测试1: 获取用户信息")
    result = core.execute("get_user", {"username": "octocat"})
    print(f"  结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
    if result.get("success"):
        data = result.get("data")
        print(f"  用户名: {data.get('username')}")
        print(f"  名字: {data.get('name')}")
        print(f"  粉丝: {data.get('followers')}")

    # 测试2: 获取仓库
    print("\n📝 测试2: 获取仓库信息")
    result = core.execute("get_repo", {"owner": "microsoft", "repo": "vscode"})
    print(f"  结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
    if result.get("success"):
        data = result.get("data")
        print(f"  仓库名: {data.get('name')}")
        print(f"  Stars: {data.get('stars')}")

    # 测试3: 搜索仓库
    print("\n📝 测试3: 搜索仓库")
    result = core.execute("search_repos", {"query": "python web framework", "limit": 3})
    print(f"  结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
    if result.get("success"):
        print(f"  找到: {result.get('total')} 个仓库")
        for repo in result.get("data", [])[:3]:
            print(f"    - {repo.get('name')} (⭐ {repo.get('stars')})")

    # 测试4: 批量获取
    print("\n📝 测试4: 批量获取仓库")
    result = core.execute("batch_get", {
        "type": "repo",
        "items": ["microsoft/vscode", "google/chromium", "facebook/react"]
    })
    print(f"  结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
    if result.get("success"):
        print(f"  成功: {result.get('success_count')}/{result.get('total')}")

    # 测试5: 分析仓库
    print("\n📝 测试5: 分析仓库")
    result = core.execute("analyze_repo", {"owner": "microsoft", "repo": "vscode"})
    print(f"  结果: {'✅ 成功' if result.get('success') else '❌ 失败'}")
    if result.get("success"):
        data = result.get("data", {})
        stats = data.get("stats", {})
        print(f"  Stars: {data.get('repo', {}).get('stars')}")
        print(f"  总Issues: {stats.get('total_issues')}")
        print(f"  Issues关闭率: {stats.get('issue_close_rate', 0):.1%}")

    # 测试6: 系统状态
    print("\n📝 测试6: 系统状态")
    status = core.get_status()
    print(f"  状态: {status.get('status')}")
    print(f"  总任务: {status.get('tasks_total')}")
    rate_limit = status.get('rate_limit')
    if rate_limit:
        print(f"  API限制: {rate_limit.get('remaining', 'N/A')}/{rate_limit.get('limit', 'N/A')}")
    else:
        print(f"  API限制: 无法获取 (网络连接问题)")

    print("\n" + "=" * 60)
    print("✅ GStackCore测试完成!")
