#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GStack GitHub客户端

核心要求：
- 稳定可靠，网络错误自动重试
- 完善的错误处理
- API速率限制处理
- 清晰的返回值
"""

import os
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class GitHubResponse:
    """GitHub API响应"""
    success: bool
    data: Any = None
    error: str = ""
    status_code: int = 0
    cached: bool = False


class GitHubClient:
    """
    GitHub API客户端

    特点：
    - 自动重试（指数退避）
    - 速率限制处理
    - 缓存机制
    - 完善的错误信息
    """

    def __init__(self, token: Optional[str] = None, cache_dir: str = "/python/GitHub/cache"):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.api_base = "https://api.github.com"
        self.cache_dir = cache_dir
        self.session = requests.Session()

        # 设置请求头
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GStackClient/1.0"
        })

        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"

        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _get_cache_path(self, endpoint: str, params: Dict = None) -> str:
        """获取缓存文件路径"""
        import hashlib
        import json

        # 处理参数中的列表
        def sanitize_params(p):
            if isinstance(p, dict):
                return {k: sanitize_params(v) for k, v in p.items()}
            elif isinstance(p, list):
                return tuple(sanitize_params(item) for item in p)
            else:
                return p

        sanitized_params = sanitize_params(params)
        key = endpoint + (json.dumps(sanitized_params) if sanitized_params else "")
        cache_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _get_from_cache(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """从缓存读取"""
        cache_path = self._get_cache_path(endpoint, params)
        if os.path.exists(cache_path):
            try:
                # 检查缓存是否过期（1小时）
                file_mtime = os.path.getmtime(cache_path)
                if time.time() - file_mtime < 3600:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                pass
        return None

    def _save_to_cache(self, endpoint: str, params: Dict, data: Any):
        """保存到缓存"""
        cache_path = self._get_cache_path(endpoint, params)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        max_retries: int = 3,
        use_cache: bool = True
    ) -> GitHubResponse:
        """
        发送API请求

        参数：
        - method: GET, POST, PATCH, DELETE
        - endpoint: API端点（如 /users/octocat）
        - params: URL参数
        - data: 请求体数据
        - max_retries: 最大重试次数
        - use_cache: 是否使用缓存
        """

        url = f"{self.api_base}{endpoint}"

        # 检查缓存（仅GET请求）
        if method == "GET" and use_cache:
            cached_data = self._get_from_cache(endpoint, params)
            if cached_data:
                return GitHubResponse(
                    success=True,
                    data=cached_data,
                    cached=True
                )

        # 重试循环
        for attempt in range(max_retries):
            try:
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=30)
                elif method == "POST":
                    response = self.session.post(url, json=data, timeout=30)
                elif method == "PATCH":
                    response = self.session.patch(url, json=data, timeout=30)
                elif method == "PUT":
                    response = self.session.put(url, json=data, timeout=30)
                elif method == "DELETE":
                    response = self.session.delete(url, timeout=30)
                else:
                    return GitHubResponse(
                        success=False,
                        error=f"不支持的HTTP方法: {method}"
                    )

                # 成功
                if response.status_code in [200, 201]:
                    result_data = response.json() if response.content else {}

                    # 保存缓存
                    if method == "GET" and use_cache:
                        self._save_to_cache(endpoint, params, result_data)

                    return GitHubResponse(
                        success=True,
                        data=result_data,
                        status_code=response.status_code
                    )

                # 速率限制
                if response.status_code == 403:
                    rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                    rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))

                    if rate_limit_remaining == 0:
                        # 等待速率限制重置
                        wait_time = max(rate_limit_reset - time.time(), 0) + 5
                        if wait_time < 3600:  # 最多等1小时
                            time.sleep(min(wait_time, 60))
                            continue
                    else:
                        # 指数退避
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(wait_time)
                        continue

                # 404 未找到
                if response.status_code == 404:
                    return GitHubResponse(
                        success=False,
                        error=f"资源未找到: {endpoint}",
                        status_code=404
                    )

                # 其他错误
                error_msg = f"API错误: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except Exception:
                    error_msg = response.text[:200] if response.text else error_msg

                return GitHubResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code
                )

            # 网络错误
            except requests.exceptions.Timeout:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                return GitHubResponse(
                    success=False,
                    error="请求超时"
                )

            except requests.exceptions.ConnectionError as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                return GitHubResponse(
                    success=False,
                    error=f"连接错误: {str(e)}"
                )

            except Exception as e:
                return GitHubResponse(
                    success=False,
                    error=f"未知错误: {str(e)}"
                )

        # 达到最大重试次数
        return GitHubResponse(
            success=False,
            error=f"达到最大重试次数 ({max_retries})"
        )

    # ========== 公共API方法 ==========

    def get_user(self, username: str) -> GitHubResponse:
        """获取用户信息"""
        return self._make_request("GET", f"/users/{username}")

    def get_repo(self, owner: str, repo: str) -> GitHubResponse:
        """获取仓库信息"""
        return self._make_request("GET", f"/repos/{owner}/{repo}")

    def list_repos(self, username: str, params: Dict = None) -> GitHubResponse:
        """列出用户的仓库"""
        if params is None:
            params = {"per_page": 30, "sort": "updated"}
        return self._make_request("GET", f"/users/{username}/repos", params)

    def search_repos(self, query: str, params: Dict = None) -> GitHubResponse:
        """搜索仓库"""
        if params is None:
            params = {"per_page": 30, "sort": "stars"}
        return self._make_request("GET", "/search/repositories", {"q": query, **params})

    def get_rate_limit(self) -> GitHubResponse:
        """获取速率限制状态"""
        return self._make_request("GET", "/rate_limit", use_cache=False)

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = None) -> GitHubResponse:
        """获取文件内容"""
        params = {}
        if ref:
            params["ref"] = ref
        return self._make_request("GET", f"/repos/{owner}/{repo}/contents/{path}", params)

    def list_commits(self, owner: str, repo: str, params: Dict = None) -> GitHubResponse:
        """列出提交"""
        if params is None:
            params = {"per_page": 30}
        return self._make_request("GET", f"/repos/{owner}/{repo}/commits", params)

    def get_issues(self, owner: str, repo: str, params: Dict = None) -> GitHubResponse:
        """获取Issues"""
        if params is None:
            params = {"state": "open", "per_page": 30}
        return self._make_request("GET", f"/repos/{owner}/{repo}/issues", params)

    def create_issue(self, owner: str, repo: str, title: str, body: str = "") -> GitHubResponse:
        """创建Issue"""
        data = {"title": title, "body": body}
        return self._make_request("POST", f"/repos/{owner}/{repo}/issues", data=data)

    def get_pulls(self, owner: str, repo: str, params: Dict = None) -> GitHubResponse:
        """获取PRs"""
        if params is None:
            params = {"state": "open", "per_page": 30}
        return self._make_request("GET", f"/repos/{owner}/{repo}/pulls", params)

    def get_workflows(self, owner: str, repo: str) -> GitHubResponse:
        """获取工作流"""
        return self._make_request("GET", f"/repos/{owner}/{repo}/actions/workflows")

    def list_branches(self, owner: str, repo: str) -> GitHubResponse:
        """列出分支"""
        return self._make_request("GET", f"/repos/{owner}/{repo}/branches")


# 简单测试
if __name__ == "__main__":
    print("🧪 测试GitHubClient")
    print("=" * 60)

    client = GitHubClient()

    # 测试1: 获取用户信息
    print("\n📝 测试1: 获取用户信息")
    result = client.get_user("octocat")
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        print(f"  用户名: {result.data.get('login')}")
        print(f"  名字: {result.data.get('name')}")
    else:
        print(f"  错误: {result.error}")

    # 测试2: 获取仓库信息
    print("\n📝 测试2: 获取仓库信息")
    result = client.get_repo("microsoft", "vscode")
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        print(f"  仓库名: {result.data.get('name')}")
        print(f"  Stars: {result.data.get('stargazers_count')}")
        print(f"  缓存: {'是' if result.cached else '否'}")
    else:
        print(f"  错误: {result.error}")

    # 测试3: 搜索仓库
    print("\n📝 测试3: 搜索仓库")
    result = client.search_repos("python web framework", {"per_page": 5})
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        print(f"  找到: {result.data.get('total_count')} 个仓库")
        for i, repo in enumerate(result.data.get('items', [])[:3], 1):
            print(f"    {i}. {repo.get('full_name')} (⭐ {repo.get('stargazers_count')})")
    else:
        print(f"  错误: {result.error}")

    # 测试4: 速率限制
    print("\n📝 测试4: 获取速率限制")
    result = client.get_rate_limit()
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        core = result.data.get('resources', {}).get('core', {})
        print(f"  Core API: {core.get('remaining')}/{core.get('limit')}")
    else:
        print(f"  错误: {result.error}")

    # 测试5: 列出仓库
    print("\n📝 测试5: 列出仓库")
    result = client.list_repos("microsoft", {"per_page": 5})
    print(f"  结果: {'✅ 成功' if result.success else '❌ 失败'}")
    if result.success:
        print(f"  找到: {len(result.data)} 个仓库")
        for i, repo in enumerate(result.data[:3], 1):
            print(f"    {i}. {repo.get('name')} (⭐ {repo.get('stargazers_count')})")
    else:
        print(f"  错误: {result.error}")

    print("\n" + "=" * 60)
    print("✅ GitHubClient测试完成!")
