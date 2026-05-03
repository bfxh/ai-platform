#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions工作流管理技能

功能:
- 列出工作流
- 获取工作流详情
- 触发工作流
- 取消工作流运行
- 查看工作流运行历史
- 获取工作流运行日志
- 管理工作流文件
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


class GitHubActionsManager(Skill):
    """GitHub Actions工作流管理技能"""

    name = "github_actions_manager"
    description = "GitHub Actions工作流管理 - 列出、触发、取消工作流，查看运行历史和日志"
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
            "User-Agent": "GitHubActionsManager/1.0",
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
        if action == "list_workflows":
            return self._list_workflows(params)
        elif action == "get_workflow":
            return self._get_workflow(params)
        elif action == "get_workflow_runs":
            return self._get_workflow_runs(params)
        elif action == "trigger_workflow":
            return self._trigger_workflow(params)
        elif action == "cancel_workflow_run":
            return self._cancel_workflow_run(params)
        elif action == "get_workflow_run":
            return self._get_workflow_run(params)
        elif action == "get_workflow_run_jobs":
            return self._get_workflow_run_jobs(params)
        elif action == "get_workflow_run_logs":
            return self._get_workflow_run_logs(params)
        elif action == "rerun_workflow":
            return self._rerun_workflow(params)
        elif action == "list_repository_dispatch":
            return self._list_repository_dispatch(params)
        elif action == "create_dispatch":
            return self._create_dispatch(params)
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

    def _list_workflows(self, params: Dict) -> Dict:
        """列出所有工作流"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        per_page = params.get("per_page", 30)
        page = params.get("page", 1)

        url = f"/repos/{self.owner}/{self.repo}/actions/workflows?per_page={per_page}&page={page}"

        return self._make_request("GET", url, None)

    def _get_workflow(self, params: Dict) -> Dict:
        """获取工作流详情"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        workflow_id = params.get("workflow_id")
        if not workflow_id:
            return {"success": False, "error": "缺少workflow_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}"

        return self._make_request("GET", url, None)

    def _get_workflow_runs(self, params: Dict) -> Dict:
        """获取工作流运行历史"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        workflow_id = params.get("workflow_id")
        status = params.get("status", "")
        branch = params.get("branch", "")
        actor = params.get("actor", "")
        per_page = params.get("per_page", 30)
        page = params.get("page", 1)

        if workflow_id:
            url = f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/runs"
        else:
            url = f"/repos/{self.owner}/{self.repo}/actions/runs"

        query_params = f"per_page={per_page}&page={page}"
        if status:
            query_params += f"&status={status}"
        if branch:
            query_params += f"&branch={branch}"
        if actor:
            query_params += f"&actor={actor}"

        url = f"{url}?{query_params}"

        return self._make_request("GET", url, None)

    def _trigger_workflow(self, params: Dict) -> Dict:
        """触发工作流"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        workflow_id = params.get("workflow_id")
        ref = params.get("ref")
        inputs = params.get("inputs", {})

        if not workflow_id or not ref:
            return {"success": False, "error": "缺少workflow_id或ref参数"}

        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs

        url = f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/dispatches"

        return self._make_request("POST", url, data)

    def _cancel_workflow_run(self, params: Dict) -> Dict:
        """取消工作流运行"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        run_id = params.get("run_id")
        if not run_id:
            return {"success": False, "error": "缺少run_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/cancel"

        return self._make_request("POST", url, None)

    def _get_workflow_run(self, params: Dict) -> Dict:
        """获取工作流运行详情"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        run_id = params.get("run_id")
        if not run_id:
            return {"success": False, "error": "缺少run_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"

        return self._make_request("GET", url, None)

    def _get_workflow_run_jobs(self, params: Dict) -> Dict:
        """获取工作流运行的作业"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        run_id = params.get("run_id")
        if not run_id:
            return {"success": False, "error": "缺少run_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/jobs"

        return self._make_request("GET", url, None)

    def _get_workflow_run_logs(self, params: Dict) -> Dict:
        """获取工作流运行日志"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        run_id = params.get("run_id")
        if not run_id:
            return {"success": False, "error": "缺少run_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/logs"

        response = self.session.get(f"{self.api_base}{url}", stream=True)

        if response.status_code == 200:
            log_content = response.content
            return {
                "success": True,
                "data": {
                    "logs": log_content.decode("utf-8", errors="ignore"),
                    "size": len(log_content)
                }
            }
        else:
            return {"success": False, "error": f"获取日志失败: {response.status_code}"}

    def _rerun_workflow(self, params: Dict) -> Dict:
        """重新运行工作流"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        run_id = params.get("run_id")
        if not run_id:
            return {"success": False, "error": "缺少run_id参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/rerun"

        return self._make_request("POST", url, None)

    def _list_repository_dispatch(self, params: Dict) -> Dict:
        """列出仓库的外部事件"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        url = f"/repos/{self.owner}/{self.repo}/actions(repository_dispatch"

        return self._make_request("GET", url, None)

    def _create_dispatch(self, params: Dict) -> Dict:
        """创建外部事件"""
        if not self.owner or not self.repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        event_type = params.get("event_type")
        client_payload = params.get("client_payload", {})

        if not event_type:
            return {"success": False, "error": "缺少event_type参数"}

        data = {
            "event_type": event_type,
            "client_payload": client_payload
        }

        url = f"/repos/{self.owner}/{self.repo}/dispatches"

        return self._make_request("POST", url, data)


skill = GitHubActionsManager()
