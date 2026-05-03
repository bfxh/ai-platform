#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub项目搜索技能
用于自动搜索、过滤和管理GitHub项目
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill

class GitHubProjectSearchSkill(Skill):
    """GitHub项目搜索技能"""

    name = "github_project_search"
    description = "GitHub项目搜索 - 自动搜索、过滤和管理GitHub项目"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.github_token = self.config.get("github_token", "")
        self.search_results_dir = self.config.get("search_results_dir", "github_search_results")
        self.projects_dir = self.config.get("projects_dir", "github_projects")
        self.default_search_params = self.config.get("default_search_params", {
            "sort": "stars",
            "order": "desc",
            "per_page": 30
        })
        
        # 确保目录存在
        os.makedirs(self.search_results_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)

    def _make_github_request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送GitHub API请求"""
        import requests
        
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        url = f"https://api.github.com{endpoint}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json()
            }
        except Exception as e:
            self.logger.error(f"GitHub API请求失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def search_projects(self, query: str, **kwargs) -> Dict:
        """搜索GitHub项目"""
        self.logger.info(f"搜索GitHub项目: {query}")
        
        params = self.default_search_params.copy()
        params.update(kwargs)
        params["q"] = query
        
        result = self._make_github_request("/search/repositories", params)
        
        if result["success"]:
            # 保存搜索结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(
                self.search_results_dir,
                f"search_{timestamp}.json"
            )
            
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result["data"], f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"搜索结果已保存到: {result_file}")
            
            # 处理结果
            items = result["data"].get("items", [])
            processed_items = []
            
            for item in items:
                processed_items.append({
                    "name": item.get("name"),
                    "full_name": item.get("full_name"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "language": item.get("language"),
                    "url": item.get("html_url"),
                    "clone_url": item.get("clone_url"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at")
                })
            
            return {
                "success": True,
                "total_count": result["data"].get("total_count", 0),
                "items": processed_items,
                "result_file": result_file
            }
        
        return result

    def clone_project(self, repo_url: str, target_dir: str = None) -> Dict:
        """克隆GitHub项目"""
        self.logger.info(f"克隆项目: {repo_url}")
        
        if not target_dir:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            target_dir = os.path.join(self.projects_dir, repo_name)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        
        try:
            # 使用git命令克隆
            cmd = ["git", "clone", repo_url, target_dir]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                self.logger.info(f"项目克隆成功: {target_dir}")
                return {
                    "success": True,
                    "path": target_dir
                }
            else:
                self.logger.error(f"项目克隆失败: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            self.logger.error(f"克隆项目失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def batch_clone(self, repos: List[str]) -> Dict:
        """批量克隆项目"""
        self.logger.info(f"批量克隆 {len(repos)} 个项目")
        
        results = []
        for repo in repos:
            result = self.clone_project(repo)
            results.append({
                "repo": repo,
                "result": result
            })
        
        # 统计结果
        success_count = sum(1 for r in results if r["result"]["success"])
        
        return {
            "success": True,
            "total": len(repos),
            "success": success_count,
            "failed": len(repos) - success_count,
            "results": results
        }

    def filter_projects(self, projects: List[Dict], **filters) -> List[Dict]:
        """过滤项目"""
        filtered = []
        
        for project in projects:
            match = True
            
            # 按语言过滤
            if "language" in filters and filters["language"]:
                if project.get("language", "").lower() != filters["language"].lower():
                    match = False
            
            # 按最小星数过滤
            if "min_stars" in filters and filters["min_stars"]:
                if project.get("stars", 0) < filters["min_stars"]:
                    match = False
            
            # 按最小fork数过滤
            if "min_forks" in filters and filters["min_forks"]:
                if project.get("forks", 0) < filters["min_forks"]:
                    match = False
            
            # 按关键词过滤
            if "keyword" in filters and filters["keyword"]:
                description = project.get("description", "").lower()
                if filters["keyword"].lower() not in description:
                    match = False
            
            if match:
                filtered.append(project)
        
        return filtered

    def generate_report(self, projects: List[Dict], output_file: str = None) -> Dict:
        """生成项目报告"""
        self.logger.info(f"生成项目报告，共 {len(projects)} 个项目")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.search_results_dir,
                f"project_report_{timestamp}.md"
            )
        
        # 生成Markdown报告
        report_content = f"# GitHub项目报告\n\n"
        report_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_content += f"项目数量: {len(projects)}\n\n"
        
        # 按星数排序
        sorted_projects = sorted(projects, key=lambda x: x.get("stars", 0), reverse=True)
        
        for i, project in enumerate(sorted_projects, 1):
            report_content += f"## {i}. {project.get('name')}\n"
            report_content += f"- 完整名称: {project.get('full_name')}\n"
            report_content += f"- 描述: {project.get('description', '无')}\n"
            report_content += f"- 星数: {project.get('stars', 0)}\n"
            report_content += f"- Fork数: {project.get('forks', 0)}\n"
            report_content += f"- 语言: {project.get('language', '无')}\n"
            report_content += f"- URL: {project.get('url')}\n"
            report_content += f"- 克隆URL: {project.get('clone_url')}\n"
            report_content += f"- 创建时间: {project.get('created_at')}\n"
            report_content += f"- 更新时间: {project.get('updated_at')}\n\n"
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            self.logger.info(f"项目报告已生成: {output_file}")
            return {
                "success": True,
                "report_file": output_file
            }
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def execute(self, command: str, **kwargs) -> Any:
        """执行技能命令"""
        if command == "search":
            query = kwargs.get("query")
            if not query:
                return "错误: 缺少 query 参数"
            
            # 提取搜索参数
            search_params = {}
            for key in ["sort", "order", "per_page", "page"]:
                if key in kwargs:
                    search_params[key] = kwargs[key]
            
            return self.search_projects(query, **search_params)
        
        elif command == "clone":
            repo_url = kwargs.get("repo_url")
            if not repo_url:
                return "错误: 缺少 repo_url 参数"
            
            target_dir = kwargs.get("target_dir")
            return self.clone_project(repo_url, target_dir)
        
        elif command == "batch-clone":
            repos = kwargs.get("repos")
            if not repos or not isinstance(repos, list):
                return "错误: 缺少 repos 参数或格式不正确"
            
            return self.batch_clone(repos)
        
        elif command == "filter":
            projects = kwargs.get("projects")
            if not projects or not isinstance(projects, list):
                return "错误: 缺少 projects 参数或格式不正确"
            
            # 提取过滤参数
            filters = {}
            for key in ["language", "min_stars", "min_forks", "keyword"]:
                if key in kwargs:
                    filters[key] = kwargs[key]
            
            return self.filter_projects(projects, **filters)
        
        elif command == "generate-report":
            projects = kwargs.get("projects")
            if not projects or not isinstance(projects, list):
                return "错误: 缺少 projects 参数或格式不正确"
            
            output_file = kwargs.get("output_file")
            return self.generate_report(projects, output_file)
        
        else:
            return "无效的命令，请使用以下命令: search, clone, batch-clone, filter, generate-report"

    def get_info(self) -> Dict:
        """获取技能信息"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "commands": [
                {
                    "name": "search",
                    "description": "搜索GitHub项目",
                    "parameters": [
                        {
                            "name": "query",
                            "type": "string",
                            "required": True,
                            "description": "搜索查询"
                        },
                        {
                            "name": "sort",
                            "type": "string",
                            "required": False,
                            "description": "排序字段 (stars, forks, updated)"
                        },
                        {
                            "name": "order",
                            "type": "string",
                            "required": False,
                            "description": "排序顺序 (asc, desc)"
                        },
                        {
                            "name": "per_page",
                            "type": "integer",
                            "required": False,
                            "description": "每页结果数"
                        }
                    ]
                },
                {
                    "name": "clone",
                    "description": "克隆GitHub项目",
                    "parameters": [
                        {
                            "name": "repo_url",
                            "type": "string",
                            "required": True,
                            "description": "项目克隆URL"
                        },
                        {
                            "name": "target_dir",
                            "type": "string",
                            "required": False,
                            "description": "目标目录"
                        }
                    ]
                },
                {
                    "name": "batch-clone",
                    "description": "批量克隆GitHub项目",
                    "parameters": [
                        {
                            "name": "repos",
                            "type": "array",
                            "required": True,
                            "description": "项目克隆URL列表"
                        }
                    ]
                },
                {
                    "name": "filter",
                    "description": "过滤项目",
                    "parameters": [
                        {
                            "name": "projects",
                            "type": "array",
                            "required": True,
                            "description": "项目列表"
                        },
                        {
                            "name": "language",
                            "type": "string",
                            "required": False,
                            "description": "编程语言"
                        },
                        {
                            "name": "min_stars",
                            "type": "integer",
                            "required": False,
                            "description": "最小星数"
                        },
                        {
                            "name": "min_forks",
                            "type": "integer",
                            "required": False,
                            "description": "最小Fork数"
                        },
                        {
                            "name": "keyword",
                            "type": "string",
                            "required": False,
                            "description": "关键词"
                        }
                    ]
                },
                {
                    "name": "generate-report",
                    "description": "生成项目报告",
                    "parameters": [
                        {
                            "name": "projects",
                            "type": "array",
                            "required": True,
                            "description": "项目列表"
                        },
                        {
                            "name": "output_file",
                            "type": "string",
                            "required": False,
                            "description": "输出文件路径"
                        }
                    ]
                }
            ]
        }

# 测试代码
if __name__ == "__main__":
    skill = GitHubProjectSearchSkill()
    # 测试搜索
    result = skill.execute("search", query="python machine learning", sort="stars", per_page=10)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 如果搜索成功，测试过滤和报告
    if result.get("success") and result.get("items"):
        # 过滤项目
        filtered = skill.execute("filter", projects=result["items"], min_stars=10000)
        print("\n过滤后的项目:")
        print(json.dumps(filtered, indent=2, ensure_ascii=False))
        
        # 生成报告
        report = skill.execute("generate-report", projects=filtered)
        print("\n报告生成:")
        print(json.dumps(report, indent=2, ensure_ascii=False))