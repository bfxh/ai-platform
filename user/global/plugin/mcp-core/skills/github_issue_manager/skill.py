#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Issue管理技能

功能:
- 创建Issue
- 更新Issue
- 关闭/打开Issue
- 评论Issue
- 标签管理
- 里程碑管理
- Issue搜索
- 批量操作
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubIssueManager(Skill):
    """GitHub Issue管理技能"""

    name = "github_issue_manager"
    description = "GitHub Issue管理 - 创建、更新、关闭、评论Issue，标签和里程碑管理"
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
            "User-Agent": "GitHubIssueManager/1.0",
            "Authorization": f"token {self.token}" if self.token else ""
        })
        self.issue_cache_file = "/python/GitHub/issue_cache.json"
        self.issue_cache = []
        self._load_cache()


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _load_cache(self):
        """加载Issue缓存"""
        if os.path.exists(self.issue_cache_file):
            try:
                with open(self.issue_cache_file, "r", encoding="utf-8") as f:
                    self.issue_cache = json.load(f)
            except:
                self.issue_cache = []

    def _save_cache(self):
        """保存Issue缓存"""
        with open(self.issue_cache_file, "w", encoding="utf-8") as f:
            json.dump(self.issue_cache, f, ensure_ascii=False, indent=2)

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        if action == "create_issue":
            return self._create_issue(params)
        elif action == "update_issue":
            return self._update_issue(params)
        elif action == "close_issue":
            return self._close_issue(params)
        elif action == "open_issue":
            return self._open_issue(params)
        elif action == "comment_issue":
            return self._comment_issue(params)
        elif action == "add_labels":
            return self._add_labels(params)
        elif action == "remove_labels":
            return self._remove_labels(params)
        elif action == "add_milestone":
            return self._add_milestone(params)
        elif action == "search_issues":
            return self._search_issues(params)
        elif action == "batch_operation":
            return self._batch_operation(params)
        elif action == "get_issue":
            return self._get_issue(params)
        elif action == "list_issues":
            return self._list_issues(params)
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

    def _create_issue(self, params: Dict) -> Dict:
        """创建Issue"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        title = params.get("title")
        body = params.get("body", "")
        labels = params.get("labels", [])
        assignees = params.get("assignees", [])
        milestone = params.get("milestone")

        if not title:
            return {"success": False, "error": "缺少title参数"}

        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone

        result = self._make_request("POST", f"/repos/{self.owner}/{self.repo}/issues", data)

        if result.get("success"):
            issue = result["data"]
            self.issue_cache.append(issue)
            self._save_cache()

        return result

    def _update_issue(self, params: Dict) -> Dict:
        """更新Issue"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        if not issue_number:
            return {"success": False, "error": "缺少issue_number参数"}

        data = {}
        if "title" in params:
            data["title"] = params["title"]
        if "body" in params:
            data["body"] = params["body"]
        if "state" in params:
            data["state"] = params["state"]
        if "labels" in params:
            data["labels"] = params["labels"]
        if "assignees" in params:
            data["assignees"] = params["assignees"]

        result = self._make_request("PATCH", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", data)

        if result.get("success"):
            for i, issue in enumerate(self.issue_cache):
                if issue.get("number") == issue_number:
                    self.issue_cache[i].update(result["data"])
                    break
            self._save_cache()

        return result

    def _close_issue(self, params: Dict) -> Dict:
        """关闭Issue"""
        params["state"] = "closed"
        return self._update_issue(params)

    def _open_issue(self, params: Dict) -> Dict:
        """打开Issue"""
        params["state"] = "open"
        return self._update_issue(params)

    def _comment_issue(self, params: Dict) -> Dict:
        """评论Issue"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        body = params.get("body", "")

        if not issue_number or not body:
            return {"success": False, "error": "缺少issue_number或body参数"}

        data = {"body": body}
        return self._make_request("POST", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments", data)

    def _add_labels(self, params: Dict) -> Dict:
        """添加标签"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        labels = params.get("labels", [])

        if not issue_number or not labels:
            return {"success": False, "error": "缺少issue_number或labels参数"}

        data = labels
        return self._make_request("POST", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/labels", data)

    def _remove_labels(self, params: Dict) -> Dict:
        """移除标签"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        label = params.get("label")

        if not issue_number or not label:
            return {"success": False, "error": "缺少issue_number或label参数"}

        return self._make_request("DELETE", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}/labels/{label}")

    def _add_milestone(self, params: Dict) -> Dict:
        """添加里程碑"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        milestone_number = params.get("milestone_number")

        if not issue_number or not milestone_number:
            return {"success": False, "error": "缺少issue_number或milestone_number参数"}

        data = {"milestone": milestone_number}
        return self._make_request("PATCH", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", data)

    def _search_issues(self, params: Dict) -> Dict:
        """搜索Issue"""
        state = params.get("state", "open")
        labels = params.get("labels", [])
        assignee = params.get("assignee", "")
        milestone = params.get("milestone", "")
        sort = params.get("sort", "created")
        direction = params.get("direction", "desc")

        query_parts = [f"repo:{self.owner}/{self.repo}"]

        if state:
            query_parts.append(f"state:{state}")
        if labels:
            for label in labels:
                query_parts.append(f"label:{label}")
        if assignee:
            query_parts.append(f"assignee:{assignee}")
        if milestone:
            query_parts.append(f"milestone:{milestone}")

        query = "+".join(query_parts)

        result = self._make_request("GET", f"/search/issues?q={query}&sort={sort}&direction={direction}", None)

        if result.get("success"):
            return {
                "success": True,
                "total_count": result["data"].get("total_count", 0),
                "issues": result["data"].get("items", [])
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

    def _get_issue(self, params: Dict) -> Dict:
        """获取单个Issue"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        issue_number = params.get("issue_number")
        if not issue_number:
            return {"success": False, "error": "缺少issue_number参数"}

        return self._make_request("GET", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", None)

    def _list_issues(self, params: Dict) -> Dict:
        """列出Issue"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        state = params.get("state", "open")
        labels = params.get("labels", "")
        sort = params.get("sort", "created")
        direction = params.get("direction", "desc")
        per_page = params.get("per_page", 100)
        page = params.get("page", 1)

        url = f"/repos/{self.owner}/{self.repo}/issues?state={state}&sort={sort}&direction={direction}&per_page={per_page}&page={page}"

        if labels:
            url += f"&labels={labels}"

        return self._make_request("GET", url, None)


skill = GitHubIssueManager()
