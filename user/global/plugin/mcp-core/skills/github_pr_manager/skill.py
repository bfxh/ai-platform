#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub PR管理技能

功能:
- 创建PR
- 更新PR
- 合并PR
- 关闭PR
- 评论PR
- 审查PR
- PR搜索
- 批量操作
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubPRManager(Skill):
    """GitHub PR管理技能"""

    name = "github_pr_manager"
    description = "GitHub PR管理 - 创建、更新、合并、关闭PR，审查和评论管理"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.owner = self.config.get("owner", "")
        self.repo = self.config.get("repo", "")
        self.token = self.config.get("token", os.getenv("GITHUB_TOKEN", ""))
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubPRManager/1.0",
            "Authorization": f"token {self.token}" if self.token else ""
        })


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        if action == "create_pr":
            return self._create_pr(params)
        elif action == "update_pr":
            return self._update_pr(params)
        elif action == "merge_pr":
            return self._merge_pr(params)
        elif action == "close_pr":
            return self._close_pr(params)
        elif action == "comment_pr":
            return self._comment_pr(params)
        elif action == "review_pr":
            return self._review_pr(params)
        elif action == "search_prs":
            return self._search_prs(params)
        elif action == "batch_operation":
            return self._batch_operation(params)
        elif action == "get_pr":
            return self._get_pr(params)
        elif action == "list_prs":
            return self._list_prs(params)
        elif action == "get_pr_files":
            return self._get_pr_files(params)
        elif action == "get_pr_commits":
            return self._get_pr_commits(params)
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
            elif method == "PUT":
                response = self.session.put(url, json=data)
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

    def _create_pr(self, params: Dict) -> Dict:
        """创建PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        title = params.get("title")
        head = params.get("head")
        base = params.get("base", "main")
        body = params.get("body", "")
        draft = params.get("draft", False)
        maintainer_can_modify = params.get("maintainer_can_modify", True)

        if not title or not head:
            return {"success": False, "error": "缺少title或head参数"}

        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
            "maintainer_can_modify": maintainer_can_modify
        }

        return self._make_request("POST", f"/repos/{self.owner}/{self.repo}/pulls", data)

    def _update_pr(self, params: Dict) -> Dict:
        """更新PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        data = {}
        if "title" in params:
            data["title"] = params["title"]
        if "body" in params:
            data["body"] = params["body"]
        if "state" in params:
            data["state"] = params["state"]
        if "base" in params:
            data["base"] = params["base"]

        return self._make_request("PATCH", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}", data)

    def _merge_pr(self, params: Dict) -> Dict:
        """合并PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        merge_method = params.get("merge_method", "merge")
        commit_title = params.get("commit_title", "")
        commit_message = params.get("commit_message", "")

        data = {
            "merge_method": merge_method
        }
        if commit_title:
            data["commit_title"] = commit_title
        if commit_message:
            data["commit_message"] = commit_message

        return self._make_request("PUT", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/merge", data)

    def _close_pr(self, params: Dict) -> Dict:
        """关闭PR"""
        params["state"] = "closed"
        return self._update_pr(params)

    def _comment_pr(self, params: Dict) -> Dict:
        """评论PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        body = params.get("body", "")

        if not pr_number or not body:
            return {"success": False, "error": "缺少pr_number或body参数"}

        data = {"body": body}
        return self._make_request("POST", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/comments", data)

    def _review_pr(self, params: Dict) -> Dict:
        """审查PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        event = params.get("event", "COMMENT")
        body = params.get("body", "")
        comments = params.get("comments", [])

        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        data = {
            "event": event,
            "body": body
        }
        if comments:
            data["comments"] = comments

        return self._make_request("POST", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/reviews", data)

    def _search_prs(self, params: Dict) -> Dict:
        """搜索PR"""
        state = params.get("state", "open")
        base = params.get("base", "")
        sort = params.get("sort", "created")
        direction = params.get("direction", "desc")

        query_parts = [f"repo:{self.owner}/{self.repo}"]

        if state:
            query_parts.append(f"is:pr state:{state}")
        if base:
            query_parts.append(f"base:{base}")

        query = "+".join(query_parts)

        result = self._make_request("GET", f"/search/issues?q={query}&sort={sort}&direction={direction}&type=pr", None)

        if result.get("success"):
            return {
                "success": True,
                "total_count": result["data"].get("total_count", 0),
                "pull_requests": result["data"].get("items", [])
            }

        return result

    def _batch_operation(self, params: Dict) -> Dict:
        """批量操作"""
        operations = params.get("operations", [])

        if not operations:
            return {"success": False, "error": "缺少operations参数"}

        results = []
        for op in operations:
            action = op.get("action")
            op_params = {k: v for k, v in op.items() if k != "action"}
            result = self.execute(action, op_params)
            results.append({
                "operation": op,
                "result": result,
                "success": result.get("success", False)
            })

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "success": True,
            "results": results,
            "summary": {
                "total": len(operations),
                "success": success_count,
                "failure": len(operations) - success_count
            }
        }

    def _get_pr(self, params: Dict) -> Dict:
        """获取单个PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        return self._make_request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}", None)

    def _list_prs(self, params: Dict) -> Dict:
        """列出PR"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        state = params.get("state", "open")
        sort = params.get("sort", "created")
        direction = params.get("direction", "desc")
        per_page = params.get("per_page", 100)
        page = params.get("page", 1)

        url = f"/repos/{self.owner}/{self.repo}/pulls?state={state}&sort={sort}&direction={direction}&per_page={per_page}&page={page}"

        return self._make_request("GET", url, None)

    def _get_pr_files(self, params: Dict) -> Dict:
        """获取PR修改的文件"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        return self._make_request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files", None)

    def _get_pr_commits(self, params: Dict) -> Dict:
        """获取PR的提交"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        pr_number = params.get("pr_number")
        if not pr_number:
            return {"success": False, "error": "缺少pr_number参数"}

        return self._make_request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{pr_number}/commits", None)


skill = GitHubPRManager()
