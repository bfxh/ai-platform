#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - GitHub项目集成模块

功能:
- 搜索GitHub上的智能体和竞争系统相关项目
- 分析项目质量和相关性
- 提供项目集成建议
- 自动或半自动集成项目

用法:
    from agent.github_integration import GitHubIntegrator

    integrator = GitHubIntegrator()
    # 搜索相关项目
    projects = integrator.search_projects("agent competition system")
    # 分析项目
    analysis = integrator.analyze_project("username/repository")
    # 集成项目
    result = integrator.integrate_project("username/repository")
"""

import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/github_integration.log"), logging.StreamHandler()],
)

# 确保日志目录存在
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)


class GitHubIntegrator:
    """GitHub项目集成器"""

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.api_url = "https://api.github.com"
        self.logger = logging.getLogger("GitHubIntegrator")
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        # 定义相关的搜索关键词
        self.search_keywords = [
            "agent competition",
            "multi-agent system",
            "agent fusion",
            "agent evolution",
            "reinforcement learning agent",
            "intelligent agent system"
        ]

    def search_projects(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索GitHub项目"""
        self.logger.info(f"搜索GitHub项目: {query}")
        
        # 构建搜索查询
        search_query = f"{query} stars:>100 fork:>10"
        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }

        try:
            response = requests.get(f"{self.api_url}/search/repositories", headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            projects = []
            for item in data.get("items", []):
                project = {
                    "name": item["name"],
                    "full_name": item["full_name"],
                    "description": item["description"],
                    "stars": item["stargazers_count"],
                    "forks": item["forks_count"],
                    "language": item["language"],
                    "html_url": item["html_url"],
                    "clone_url": item["clone_url"],
                    "updated_at": item["updated_at"]
                }
                projects.append(project)
            
            self.logger.info(f"找到 {len(projects)} 个相关项目")
            return projects
        except Exception as e:
            self.logger.error(f"搜索项目失败: {e}")
            return []

    def search_agent_projects(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索智能体相关项目"""
        all_projects = []
        seen_projects = set()

        for keyword in self.search_keywords:
            self.logger.info(f"使用关键词搜索: {keyword}")
            projects = self.search_projects(keyword, max_results=5)
            for project in projects:
                if project["full_name"] not in seen_projects:
                    seen_projects.add(project["full_name"])
                    all_projects.append(project)

        # 按星数排序
        all_projects.sort(key=lambda x: x["stars"], reverse=True)
        return all_projects[:max_results]

    def analyze_project(self, repo_full_name: str) -> Dict[str, Any]:
        """分析GitHub项目"""
        self.logger.info(f"分析项目: {repo_full_name}")

        try:
            # 获取项目信息
            response = requests.get(f"{self.api_url}/repos/{repo_full_name}", headers=self.headers, timeout=30)
            response.raise_for_status()
            repo_info = response.json()

            files_response = requests.get(f"{self.api_url}/repos/{repo_full_name}/contents", headers=self.headers, timeout=30)
            files_response.raise_for_status()
            files = files_response.json()

            # 分析项目结构
            analysis = {
                "name": repo_info["name"],
                "full_name": repo_info["full_name"],
                "description": repo_info["description"],
                "stars": repo_info["stargazers_count"],
                "forks": repo_info["forks_count"],
                "language": repo_info["language"],
                "updated_at": repo_info["updated_at"],
                "html_url": repo_info["html_url"],
                "clone_url": repo_info["clone_url"],
                "integration_score": 0,
                "integration_suggestions": [],
                "structure": self._analyze_structure(files)
            }

            # 计算集成分数
            analysis["integration_score"] = self._calculate_integration_score(analysis)

            # 生成集成建议
            analysis["integration_suggestions"] = self._generate_integration_suggestions(analysis)

            return analysis
        except Exception as e:
            self.logger.error(f"分析项目失败: {e}")
            return {"error": str(e)}

    def _analyze_structure(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析项目结构"""
        structure = {
            "has_agent_folder": False,
            "has_competition_logic": False,
            "has_fusion_mechanism": False,
            "has_requirements_file": False,
            "has_setup_file": False,
            "languages": {}
        }

        # 检查文件和目录
        for item in files:
            if item["type"] == "dir":
                if "agent" in item["name"].lower():
                    structure["has_agent_folder"] = True
                elif "competition" in item["name"].lower():
                    structure["has_competition_logic"] = True
                elif "fusion" in item["name"].lower():
                    structure["has_fusion_mechanism"] = True
            elif item["type"] == "file":
                if item["name"] == "requirements.txt":
                    structure["has_requirements_file"] = True
                elif item["name"] == "setup.py" or item["name"] == "setup.cfg":
                    structure["has_setup_file"] = True

        return structure

    def _calculate_integration_score(self, analysis: Dict[str, Any]) -> int:
        """计算集成分数"""
        score = 0

        # 基于星数和fork数
        score += min(analysis["stars"] // 100, 30)
        score += min(analysis["forks"] // 50, 20)

        # 基于项目结构
        structure = analysis.get("structure", {})
        if structure.get("has_agent_folder"):
            score += 10
        if structure.get("has_competition_logic"):
            score += 15
        if structure.get("has_fusion_mechanism"):
            score += 15
        if structure.get("has_requirements_file"):
            score += 5
        if structure.get("has_setup_file"):
            score += 5

        # 基于更新时间（最近更新的项目得分更高）
        updated_at = datetime.fromisoformat(analysis["updated_at"].replace("Z", ""))
        days_since_update = (datetime.now() - updated_at).days
        if days_since_update < 30:
            score += 10
        elif days_since_update < 90:
            score += 5

        return min(score, 100)

    def _generate_integration_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """生成集成建议"""
        suggestions = []
        structure = analysis.get("structure", {})

        if structure.get("has_agent_folder"):
            suggestions.append("将项目的智能体实现集成到 agent/ 目录")
        if structure.get("has_competition_logic"):
            suggestions.append("将项目的竞争逻辑集成到 agent/base.py 的竞争机制中")
        if structure.get("has_fusion_mechanism"):
            suggestions.append("将项目的融合机制集成到 agent/base.py 的融合功能中")
        if structure.get("has_requirements_file"):
            suggestions.append("合并项目的依赖到 requirements.txt")

        # 基于语言的建议
        if analysis.get("language") == "Python":
            suggestions.append("直接集成Python代码到现有系统")
        else:
            suggestions.append(f"考虑使用 {analysis.get('language')} 到 Python 的接口或包装器")

        return suggestions

    def integrate_project(self, repo_full_name: str, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """集成GitHub项目"""
        self.logger.info(f"集成项目: {repo_full_name}")

        if target_dir is None:
            # 默认集成到 agent/external/ 目录
            target_dir = str(Path(__file__).parent / "external")

        # 确保目标目录存在
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        try:
            # 克隆仓库
            repo_name = repo_full_name.split("/")[-1]
            clone_path = target_path / repo_name

            if clone_path.exists():
                self.logger.warning(f"项目已存在: {clone_path}")
                # 拉取最新代码
                subprocess.run(["git", "-C", str(clone_path), "pull"], check=True)
            else:
                # 克隆仓库
                clone_url = f"https://github.com/{repo_full_name}.git"
                subprocess.run(["git", "clone", clone_url, str(clone_path)], check=True)

            # 分析项目
            analysis = self.analyze_project(repo_full_name)

            # 生成集成报告
            integration_report = {
                "success": True,
                "repo_full_name": repo_full_name,
                "clone_path": str(clone_path),
                "analysis": analysis,
                "integration_steps": [],
                "timestamp": datetime.now().isoformat()
            }

            # 执行集成步骤
            integration_steps = self._execute_integration_steps(clone_path, analysis)
            integration_report["integration_steps"] = integration_steps

            self.logger.info(f"项目集成成功: {repo_full_name}")
            return integration_report
        except Exception as e:
            self.logger.error(f"集成项目失败: {e}")
            return {"success": False, "error": str(e)}

    def _execute_integration_steps(self, clone_path: Path, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行集成步骤"""
        steps = []

        # 步骤1: 检查依赖
        requirements_file = clone_path / "requirements.txt"
        if requirements_file.exists():
            steps.append({
                "step": "检查依赖",
                "status": "completed",
                "details": f"发现依赖文件: {requirements_file}"
            })
            # 可以在这里添加依赖安装逻辑
        else:
            steps.append({
                "step": "检查依赖",
                "status": "skipped",
                "details": "未找到依赖文件"
            })

        # 步骤2: 检查智能体相关代码
        agent_dir = clone_path
        for dir_name in ["agent", "agents", "agent_system"]:
            if (clone_path / dir_name).exists():
                agent_dir = clone_path / dir_name
                break

        if agent_dir != clone_path:
            steps.append({
                "step": "检查智能体代码",
                "status": "completed",
                "details": f"发现智能体目录: {agent_dir}"
            })
        else:
            steps.append({
                "step": "检查智能体代码",
                "status": "skipped",
                "details": "未找到智能体目录"
            })

        # 步骤3: 检查竞争逻辑
        competition_files = []
        for root, dirs, files in os.walk(clone_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text()
                        if "competition" in content.lower() or "compete" in content.lower():
                            competition_files.append(str(file_path.relative_to(clone_path)))
                    except Exception:
                        pass

        if competition_files:
            steps.append({
                "step": "检查竞争逻辑",
                "status": "completed",
                "details": f"发现竞争相关文件: {competition_files}"
            })
        else:
            steps.append({
                "step": "检查竞争逻辑",
                "status": "skipped",
                "details": "未找到竞争相关代码"
            })

        # 步骤4: 检查融合机制
        fusion_files = []
        for root, dirs, files in os.walk(clone_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    try:
                        content = file_path.read_text()
                        if "fusion" in content.lower() or "merge" in content.lower():
                            fusion_files.append(str(file_path.relative_to(clone_path)))
                    except Exception:
                        pass

        if fusion_files:
            steps.append({
                "step": "检查融合机制",
                "status": "completed",
                "details": f"发现融合相关文件: {fusion_files}"
            })
        else:
            steps.append({
                "step": "检查融合机制",
                "status": "skipped",
                "details": "未找到融合相关代码"
            })

        return steps

    def create_integration_report(self, projects: List[Dict[str, Any]]) -> str:
        """创建集成报告"""
        report = "# GitHub 项目集成报告\n\n"
        report += f"生成时间: {datetime.now().isoformat()}\n\n"
        report += f"共分析 {len(projects)} 个项目\n\n"

        for i, project in enumerate(projects, 1):
            report += f"## {i}. {project['name']}\n"
            report += f"- 仓库: [{project['full_name']}]({project['html_url']})\n"
            report += f"- 描述: {project['description'] or '无描述'}\n"
            report += f"- 星数: {project['stars']}\n"
            report += f"- Fork数: {project['forks']}\n"
            report += f"- 主要语言: {project['language']}\n"
            report += f"- 最后更新: {project['updated_at']}\n\n"

        return report


if __name__ == "__main__":
    # 测试GitHub集成器
    integrator = GitHubIntegrator()

    print("=" * 80)
    print("GitHub 项目集成测试")
    print("=" * 80)

    # 搜索智能体相关项目
    print("\n1. 搜索智能体相关项目...")
    projects = integrator.search_agent_projects(max_results=5)

    print(f"找到 {len(projects)} 个相关项目:")
    for i, project in enumerate(projects, 1):
        print(f"  {i}. {project['full_name']} (★{project['stars']}, 📁{project['forks']})")
        print(f"     {project['description']}")
        print(f"     {project['html_url']}")

    # 分析第一个项目
    if projects:
        print("\n2. 分析第一个项目...")
        analysis = integrator.analyze_project(projects[0]['full_name'])
        
        print(f"项目: {analysis['full_name']}")
        print(f"集成分数: {analysis['integration_score']}/100")
        print("集成建议:")
        for suggestion in analysis['integration_suggestions']:
            print(f"  - {suggestion}")

        # 集成项目
        print("\n3. 集成项目...")
        result = integrator.integrate_project(projects[0]['full_name'])
        
        if result['success']:
            print(f"集成成功！项目已克隆到: {result['clone_path']}")
            print("集成步骤:")
            for step in result['integration_steps']:
                print(f"  - {step['step']}: {step['status']}")
                if step['details']:
                    print(f"    {step['details']}")
        else:
            print(f"集成失败: {result['error']}")

    # 创建集成报告
    if projects:
        print("\n4. 创建集成报告...")
        report = integrator.create_integration_report(projects)
        report_path = Path("reports") / "github_integration_report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        print(f"集成报告已生成: {report_path}")

    print("\nGitHub 项目集成测试完成")
    print("=" * 80)
