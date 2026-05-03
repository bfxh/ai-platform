#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub数据分析可视化技能

功能:
- 仓库活动分析
- 贡献者分析
- Issue分析
- PR分析
- 代码频率分析
- 提交历史分析
- 数据可视化报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubDataAnalytics(Skill):
    """GitHub数据分析可视化技能"""

    name = "github_data_analytics"
    description = "GitHub数据分析可视化 - 仓库活动、贡献者、Issue、PR等数据分析与可视化"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.owner = self.config.get("owner", "")
        self.repo = self.config.get("repo", "")
        self.token = self.config.get("token", os.getenv("GITHUB_TOKEN", ""))
        self.api_base = "https://api.github.com"
        self.analysis_dir = self.config.get("analysis_dir", "/python/GitHub/analysis")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubDataAnalytics/1.0",
            "Authorization": f"token {self.token}" if self.token else ""
        })
        self._ensure_analysis_dir()


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _ensure_analysis_dir(self):
        """确保分析目录存在"""
        Path(self.analysis_dir).mkdir(parents=True, exist_ok=True)

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        if action == "analyze_repo_activity":
            return self._analyze_repo_activity(params)
        elif action == "analyze_contributors":
            return self._analyze_contributors(params)
        elif action == "analyze_issues":
            return self._analyze_issues(params)
        elif action == "analyze_pulls":
            return self._analyze_pulls(params)
        elif action == "analyze_code_frequency":
            return self._analyze_code_frequency(params)
        elif action == "analyze_commit_history":
            return self._analyze_commit_history(params)
        elif action == "generate_report":
            return self._generate_report(params)
        elif action == "generate_visualization":
            return self._generate_visualization(params)
        elif action == "analyze_trends":
            return self._analyze_trends(params)
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
            else:
                return {"success": False, "error": f"不支持的方法: {method}"}

            if response.status_code in [200, 201, 204]:
                return {"success": True, "data": response.json() if response.content else {}}
            else:
                return {"success": False, "error": f"API错误: {response.status_code}", "details": response.text}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_repo_activity(self, params: Dict) -> Dict:
        """分析仓库活动"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        days = params.get("days", 30)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/stats/commit_activity", None)

        if not result.get("success"):
            return result

        activity_data = result["data"]
        total_commits = sum(week.get("total", 0) for week in activity_data)
        daily_stats = {}

        for week in activity_data:
            days_data = week.get("days", [])
            for i, count in enumerate(days_data):
                date = datetime.fromtimestamp(week.get("timestamp", 0) + i * 86400).strftime("%Y-%m-%d")
                daily_stats[date] = daily_stats.get(date, 0) + count

        recent_activity = dict(list(daily_stats.items())[-days:])

        analysis = {
            "total_commits": total_commits,
            "daily_average": total_commits / days if days > 0 else 0,
            "most_active_day": max(daily_stats.items(), key=lambda x: x[1]) if daily_stats else None,
            "recent_activity": recent_activity,
            "analysis_period": f"{days} days"
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _analyze_contributors(self, params: Dict) -> Dict:
        """分析贡献者"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/contributors", None)

        if not result.get("success"):
            return result

        contributors = result["data"]

        analysis = {
            "total_contributors": len(contributors),
            "top_contributors": [
                {
                    "login": c.get("login"),
                    "contributions": c.get("contributions"),
                    "avatar_url": c.get("avatar_url")
                }
                for c in contributors[:10]
            ],
            "contribution_distribution": {
                "total": sum(c.get("contributions", 0) for c in contributors),
                "top_10_pct": sum(c.get("contributions", 0) for c in contributors[:10]) / max(1, sum(c.get("contributions", 0) for c in contributors)) * 100
            }
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _analyze_issues(self, params: Dict) -> Dict:
        """分析Issue"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        state = params.get("state", "all")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/issues?state={state}&per_page=100", None)

        if not result.get("success"):
            return result

        issues = result["data"]

        open_issues = [i for i in issues if i.get("state") == "open"]
        closed_issues = [i for i in issues if i.get("state") == "closed"]

        labels_count = {}
        for issue in issues:
            for label in issue.get("labels", []):
                label_name = label.get("name")
                labels_count[label_name] = labels_count.get(label_name, 0) + 1

        analysis = {
            "total_issues": len(issues),
            "open_issues": len(open_issues),
            "closed_issues": len(closed_issues),
            "close_rate": len(closed_issues) / len(issues) if issues else 0,
            "top_labels": sorted(labels_count.items(), key=lambda x: x[1], reverse=True)[:10],
            "average_time_to_close": self._calculate_avg_time_to_close(closed_issues)
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _calculate_avg_time_to_close(self, closed_issues: List[Dict]) -> float:
        """计算平均关闭时间"""
        total_time = 0
        count = 0

        for issue in closed_issues:
            created_at = issue.get("created_at")
            closed_at = issue.get("closed_at")
            if created_at and closed_at:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                closed = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                total_time += (closed - created).total_seconds()
                count += 1

        return total_time / count / 3600 if count > 0 else 0

    def _analyze_pulls(self, params: Dict) -> Dict:
        """分析PR"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        state = params.get("state", "all")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/pulls?state={state}&per_page=100", None)

        if not result.get("success"):
            return result

        pulls = result["data"]

        open_pulls = [p for p in pulls if p.get("state") == "open"]
        closed_pulls = [p for p in pulls if p.get("state") == "closed"]
        merged_pulls = [p for p in pulls if p.get("merged_at")]

        analysis = {
            "total_pulls": len(pulls),
            "open_pulls": len(open_pulls),
            "closed_pulls": len(closed_pulls),
            "merged_pulls": len(merged_pulls),
            "merge_rate": len(merged_pulls) / len(closed_pulls) if closed_pulls else 0,
            "average_time_to_merge": self._calculate_avg_time_to_merge(merged_pulls),
            "draft_pulls": len([p for p in pulls if p.get("draft", False)])
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _calculate_avg_time_to_merge(self, merged_pulls: List[Dict]) -> float:
        """计算平均合并时间"""
        total_time = 0
        count = 0

        for pr in merged_pulls:
            created_at = pr.get("created_at")
            merged_at = pr.get("merged_at")
            if created_at and merged_at:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                merged = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                total_time += (merged - created).total_seconds()
                count += 1

        return total_time / count / 3600 if count > 0 else 0

    def _analyze_code_frequency(self, params: Dict) -> Dict:
        """分析代码频率"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        result = self._make_request("GET", f"/repos/{owner}/{repo}/stats/code_frequency", None)

        if not result.get("success"):
            return result

        code_data = result["data"]
        weekly_stats = []

        for week_data in code_data:
            week = {
                "timestamp": week_data.get("week"),
                "additions": week_data.get("additions", 0),
                "deletions": week_data.get("deletions", 0),
                "date": datetime.fromtimestamp(week_data.get("week", 0)).strftime("%Y-%m-%d") if week_data.get("week") else None
            }
            weekly_stats.append(week)

        total_additions = sum(w.get("additions", 0) for w in weekly_stats)
        total_deletions = sum(w.get("deletions", 0) for w in weekly_stats)

        analysis = {
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "net_changes": total_additions - total_deletions,
            "weekly_stats": weekly_stats[-10:]
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _analyze_commit_history(self, params: Dict) -> Dict:
        """分析提交历史"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        sha = params.get("sha", "")
        path = params.get("path", "")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        endpoint = f"/repos/{owner}/{repo}/commits"
        if sha:
            endpoint += f"/{sha}"
        if path:
            endpoint += f"?path={path}"

        result = self._make_request("GET", endpoint, None)

        if not result.get("success"):
            return result

        commits = result["data"]

        analysis = {
            "total_commits": len(commits),
            "recent_commits": [
                {
                    "sha": c.get("sha"),
                    "message": c.get("commit", {}).get("message", "").split("\n")[0],
                    "author": c.get("commit", {}).get("author", {}).get("name"),
                    "date": c.get("commit", {}).get("author", {}).get("date"),
                    "url": c.get("html_url")
                }
                for c in commits[:20]
            ]
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _generate_report(self, params: Dict) -> Dict:
        """生成分析报告"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        report = {
            "title": f"GitHub仓库分析报告 - {owner}/{repo}",
            "generated_at": datetime.now().isoformat(),
            "sections": []
        }

        activity_analysis = self._analyze_repo_activity({"owner": owner, "repo": repo, "days": 30})
        if activity_analysis.get("success"):
            report["sections"].append({
                "title": "仓库活动分析",
                "data": activity_analysis.get("analysis")
            })

        contributors_analysis = self._analyze_contributors({"owner": owner, "repo": repo})
        if contributors_analysis.get("success"):
            report["sections"].append({
                "title": "贡献者分析",
                "data": contributors_analysis.get("analysis")
            })

        issues_analysis = self._analyze_issues({"owner": owner, "repo": repo})
        if issues_analysis.get("success"):
            report["sections"].append({
                "title": "Issue分析",
                "data": issues_analysis.get("analysis")
            })

        pulls_analysis = self._analyze_pulls({"owner": owner, "repo": repo})
        if pulls_analysis.get("success"):
            report["sections"].append({
                "title": "PR分析",
                "data": pulls_analysis.get("analysis")
            })

        report_file = Path(self.analysis_dir) / f"{repo}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "report": report,
            "report_file": str(report_file)
        }

    def _generate_visualization(self, params: Dict) -> Dict:
        """生成可视化数据"""
        viz_type = params.get("viz_type", "activity")
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        viz_data = {
            "type": viz_type,
            "owner": owner,
            "repo": repo,
            "generated_at": datetime.now().isoformat(),
            "data": {}
        }

        if viz_type == "activity":
            activity = self._analyze_repo_activity({"owner": owner, "repo": repo})
            if activity.get("success"):
                viz_data["data"] = activity.get("analysis", {}).get("recent_activity", {})

        elif viz_type == "contributors":
            contributors = self._analyze_contributors({"owner": owner, "repo": repo})
            if contributors.get("success"):
                viz_data["data"] = contributors.get("analysis", {}).get("top_contributors", [])

        elif viz_type == "issues":
            issues = self._analyze_issues({"owner": owner, "repo": repo})
            if issues.get("success"):
                analysis = issues.get("analysis", {})
                viz_data["data"] = {
                    "labels": ["Open", "Closed"],
                    "values": [analysis.get("open_issues", 0), analysis.get("closed_issues", 0)]
                }

        elif viz_type == "pulls":
            pulls = self._analyze_pulls({"owner": owner, "repo": repo})
            if pulls.get("success"):
                analysis = pulls.get("analysis", {})
                viz_data["data"] = {
                    "labels": ["Open", "Closed", "Merged"],
                    "values": [analysis.get("open_pulls", 0), analysis.get("closed_pulls", 0), analysis.get("merged_pulls", 0)]
                }

        return {
            "success": True,
            "visualization": viz_data
        }

    def _analyze_trends(self, params: Dict) -> Dict:
        """分析趋势"""
        owner = params.get("owner", self.owner)
        repo = params.get("repo", self.repo)
        metric = params.get("metric", "commits")

        if not owner or not repo:
            return {"success": False, "error": "缺少owner或repo参数"}

        if metric == "commits":
            result = self._make_request("GET", f"/repos/{owner}/{repo}/stats/commit_activity", None)
        elif metric == "code_frequency":
            result = self._make_request("GET", f"/repos/{owner}/{repo}/stats/code_frequency", None)
        elif metric == "contributors":
            result = self._make_request("GET", f"/repos/{owner}/{repo}/stats/contributors", None)
        else:
            return {"success": False, "error": f"不支持的指标: {metric}"}

        if not result.get("success"):
            return result

        trend_data = result["data"]

        analysis = {
            "metric": metric,
            "data_points": len(trend_data),
            "trend": self._calculate_trend(trend_data),
            "data": trend_data[-30:] if len(trend_data) > 30 else trend_data
        }

        return {
            "success": True,
            "analysis": analysis
        }

    def _calculate_trend(self, data: List[Dict]) -> str:
        """计算趋势"""
        if len(data) < 2:
            return "insufficient_data"

        values = []
        for item in data:
            if isinstance(item, dict):
                if "total" in item:
                    values.append(item["total"])
                elif "additions" in item:
                    values.append(item["additions"])

        if len(values) < 2:
            return "insufficient_data"

        recent_avg = sum(values[-7:]) / len(values[-7:]) if len(values) >= 7 else sum(values) / len(values)
        older_avg = sum(values[:-7]) / len(values[:-7]) if len(values) > 7 else sum(values) / len(values)

        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


skill = GitHubDataAnalytics()
