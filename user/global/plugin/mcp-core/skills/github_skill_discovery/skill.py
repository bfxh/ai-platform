#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Skill自动发现和下载系统

功能:
- 搜索GitHub上的skill仓库
- 下载并解析skill项目
- 自动适配到GStack技能管理系统
- 创建skill市场和展示界面
- 定期更新skill列表
"""

import json
import os
import re
import time
import zipfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import requests

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.base import Skill


class GitHubSkillDiscovery(Skill):
    """GitHub Skill自动发现系统"""

    name = "github_skill_discovery"
    description = "GitHub Skill自动发现和下载系统 - 搜索、下载、适配GitHub上的skill项目"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.token = self.config.get("token", os.getenv("GITHUB_TOKEN", ""))
        self.api_base = "https://api.github.com"
        self.search_base = "https://api.github.com/search"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHubSkillDiscovery/1.0",
            "Authorization": f"token {self.token}" if self.token else ""
        })
        self.discovery_cache_file = "/python/GitHub/discovered_skills.json"
        self.skill_marketplace_file = "/python/GitHub/skill_marketplace.json"
        self.local_skills_dir = Path("/python/MCP_Core/skills")
        self.discovered_skills = []
        self.skill_marketplace = {"skills": [], "categories": {}, "last_updated": None}
        self._load_discovery_cache()
        self._load_skill_marketplace()


    def close(self):
        """Close requests session to free connections"""
        self.session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _load_discovery_cache(self):
        """加载发现缓存"""
        if os.path.exists(self.discovery_cache_file):
            try:
                with open(self.discovery_cache_file, "r", encoding="utf-8") as f:
                    self.discovered_skills = json.load(f)
            except:
                self.discovered_skills = []

    def _save_discovery_cache(self):
        """保存发现缓存"""
        with open(self.discovery_cache_file, "w", encoding="utf-8") as f:
            json.dump(self.discovered_skills, f, ensure_ascii=False, indent=2)

    def _load_skill_marketplace(self):
        """加载skill市场数据"""
        if os.path.exists(self.skill_marketplace_file):
            try:
                with open(self.skill_marketplace_file, "r", encoding="utf-8") as f:
                    self.skill_marketplace = json.load(f)
            except:
                self.skill_marketplace = {"skills": [], "categories": {}, "last_updated": None}
        else:
            self.skill_marketplace = {"skills": [], "categories": {}, "last_updated": None}

    def _save_skill_marketplace(self):
        """保存skill市场数据"""
        self.skill_marketplace["last_updated"] = datetime.now().isoformat()
        with open(self.skill_marketplace_file, "w", encoding="utf-8") as f:
            json.dump(self.skill_marketplace, f, ensure_ascii=False, indent=2)

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        if action == "search_skills":
            return self._search_skills(params)
        elif action == "discover_popular_skills":
            return self._discover_popular_skills(params)
        elif action == "discover_mcp_skills":
            return self._discover_mcp_skills(params)
        elif action == "download_skill":
            return self._download_skill(params)
        elif action == "download_and_install":
            return self._download_and_install(params)
        elif action == "install_from_url":
            return self._install_from_url(params)
        elif action == "get_marketplace":
            return self._get_marketplace(params)
        elif action == "update_marketplace":
            return self._update_marketplace(params)
        elif action == "get_skill_info":
            return self._get_skill_info(params)
        elif action == "search_marketplace":
            return self._search_marketplace(params)
        elif action == "get_categories":
            return self._get_categories(params)
        elif action == "recommend_skills":
            return self._recommend_skills(params)
        elif action == "get_downloaded_skills":
            return self._get_downloaded_skills(params)
        else:
            return {"success": False, "error": f"未知动作: {action}"}

    def _make_request(self, method: str, url: str, data: Dict = None) -> Dict:
        """发送API请求"""
        try:
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                return {"success": False, "error": f"不支持的方法: {method}"}

            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            elif response.status_code == 403:
                return {"success": False, "error": "速率限制已达到，请稍后再试"}
            elif response.status_code == 404:
                return {"success": False, "error": "资源未找到"}
            else:
                return {"success": False, "error": f"API错误: {response.status_code}", "details": response.text}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search_skills(self, params: Dict) -> Dict:
        """搜索GitHub上的skill仓库"""
        query = params.get("query", "MCP skill OR skill.py")
        language = params.get("language", "python")
        sort = params.get("sort", "stars")
        order = params.get("order", "desc")
        max_results = params.get("max_results", 30)

        search_query = f"{query} in:name,description,readme language:{language}"
        url = f"{self.search_base}/repositories?q={search_query}&sort={sort}&order={order}&per_page={min(max_results, 100)}"

        result = self._make_request("GET", url)

        if not result.get("success"):
            return result

        repos = result["data"].get("items", [])

        skills = []
        for repo in repos:
            skill_info = {
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo.get("html_url"),
                "clone_url": repo.get("clone_url"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
                "score": repo.get("score", 0)
            }
            skills.append(skill_info)

        self.discovered_skills = skills
        self._save_discovery_cache()

        return {
            "success": True,
            "skills": skills,
            "total_count": len(skills),
            "query": query
        }

    def _discover_popular_skills(self, params: Dict) -> Dict:
        """发现热门skill"""
        min_stars = params.get("min_stars", 10)
        max_results = params.get("max_results", 50)

        search_query = "MCP skill OR skill.py stars:>10"
        url = f"{self.search_base}/repositories?q={search_query}&sort=stars&order=desc&per_page={min(max_results, 100)}"

        result = self._make_request("GET", url)

        if not result.get("success"):
            return result

        repos = result["data"].get("items", [])

        popular_skills = []
        for repo in repos:
            if repo.get("stargazers_count", 0) >= min_stars:
                skill_info = {
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "url": repo.get("html_url"),
                    "clone_url": repo.get("clone_url"),
                    "updated_at": repo.get("updated_at"),
                    "topics": repo.get("topics", []),
                    "is_popular": True
                }
                popular_skills.append(skill_info)

        popular_skills.sort(key=lambda x: x["stars"], reverse=True)

        return {
            "success": True,
            "skills": popular_skills,
            "total_count": len(popular_skills),
            "min_stars": min_stars
        }

    def _discover_mcp_skills(self, params: Dict) -> Dict:
        """发现MCP官方skill"""
        organizations = params.get("organizations", [
            "modelcontextprotocol",
            "microsoft",
            "openai",
            "anthropic"
        ])

        all_skills = []

        for org in organizations:
            url = f"{self.api_base}/orgs/{org}/repos?type=public&sort=updated&per_page=50"
            result = self._make_request("GET", url)

            if result.get("success"):
                repos = result["data"]
                for repo in repos:
                    repo_name = repo.get("name", "") or ""
                    repo_desc = repo.get("description", "") or ""

                    if any(keyword in repo_name.lower() or keyword in repo_desc.lower()
                           for keyword in ["skill", "mcp", "tool", "plugin"]):
                        skill_info = {
                            "name": repo.get("name"),
                            "full_name": repo.get("full_name"),
                            "description": repo.get("description"),
                            "language": repo.get("language"),
                            "stars": repo.get("stargazers_count", 0),
                            "forks": repo.get("forks_count", 0),
                            "url": repo.get("html_url"),
                            "clone_url": repo.get("clone_url"),
                            "updated_at": repo.get("updated_at"),
                            "topics": repo.get("topics", []),
                            "organization": org
                        }
                        all_skills.append(skill_info)

            time.sleep(0.5)

        all_skills.sort(key=lambda x: x["stars"], reverse=True)

        return {
            "success": True,
            "skills": all_skills,
            "total_count": len(all_skills),
            "organizations": organizations
        }

    def _download_skill(self, params: Dict) -> Dict:
        """下载skill仓库"""
        repo_url = params.get("repo_url")
        repo_full_name = params.get("repo_full_name")

        if not repo_url and not repo_full_name:
            return {"success": False, "error": "缺少repo_url或repo_full_name参数"}

        if repo_full_name:
            download_url = f"{self.api_base}/repos/{repo_full_name}/zipball"
        else:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                repo_full_name = f"{path_parts[0]}/{path_parts[1]}"
                download_url = f"{self.api_base}/repos/{repo_full_name}/zipball"
            else:
                return {"success": False, "error": "无效的仓库URL"}

        result = self._make_request("GET", download_url)

        if not result.get("success"):
            return result

        zipball_url = result["data"].get("url") or download_url

        try:
            response = self.session.get(zipball_url, stream=True, timeout=60)
            if response.status_code == 200:
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, f"{repo_full_name.split('/')[-1]}.zip")

                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                extract_dir = os.path.join(temp_dir, "extracted")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                extracted_items = os.listdir(extract_dir)
                if extracted_items:
                    skill_source_dir = os.path.join(extract_dir, extracted_items[0])
                    return {
                        "success": True,
                        "zip_path": zip_path,
                        "extract_dir": extract_dir,
                        "skill_source_dir": skill_source_dir,
                        "repo_full_name": repo_full_name
                    }

                return {"success": False, "error": "解压失败"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _download_and_install(self, params: Dict) -> Dict:
        """下载并安装skill"""
        repo_full_name = params.get("repo_full_name")
        repo_url = params.get("repo_url")

        if not repo_full_name and not repo_url:
            return {"success": False, "error": "缺少repo_full_name或repo_url参数"}

        download_result = self._download_skill({
            "repo_full_name": repo_full_name,
            "repo_url": repo_url
        })

        if not download_result.get("success"):
            return download_result

        skill_source_dir = download_result.get("skill_source_dir")

        skill_files = self._find_skill_files(skill_source_dir)

        if not skill_files:
            return {
                "success": False,
                "error": "未找到skill文件",
                "hint": "请确保仓库包含skill.py或类似的skill文件"
            }

        skill_dest_dir = self.local_skills_dir / repo_full_name.split("/")[-1]
        skill_dest_dir.mkdir(parents=True, exist_ok=True)

        installed_files = []
        for skill_file in skill_files:
            dest_file = skill_dest_dir / Path(skill_file).name
            try:
                import shutil
                shutil.copy2(skill_file, dest_file)
                installed_files.append(str(dest_file))
            except Exception as e:
                return {"success": False, "error": f"复制文件失败: {str(e)}"}

        readme_content = self._find_and_copy_readme(skill_source_dir, skill_dest_dir)

        skill_info = {
            "name": repo_full_name.split("/")[-1],
            "full_name": repo_full_name,
            "installed_at": datetime.now().isoformat(),
            "installed_files": installed_files,
            "skill_dir": str(skill_dest_dir)
        }

        marketplace_entry = self._create_marketplace_entry(skill_info)
        self.skill_marketplace["skills"].append(marketplace_entry)
        self._save_skill_marketplace()

        return {
            "success": True,
            "message": f"成功安装skill: {repo_full_name}",
            "skill_info": skill_info,
            "installed_files": installed_files
        }

    def _install_from_url(self, params: Dict) -> Dict:
        """从URL安装skill"""
        url = params.get("url")

        if not url:
            return {"success": False, "error": "缺少url参数"}

        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 2:
            repo_full_name = f"{path_parts[0]}/{path_parts[1]}"
        else:
            return {"success": False, "error": "无效的URL格式"}

        return self._download_and_install({
            "repo_full_name": repo_full_name
        })

    def _find_skill_files(self, directory: str) -> List[str]:
        """查找skill文件"""
        skill_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith("skill.py") or file == "skill.py" or "skill" in file.lower():
                    skill_files.append(os.path.join(root, file))
        return skill_files

    def _find_and_copy_readme(self, source_dir: str, dest_dir: Path) -> Optional[str]:
        """查找并复制README文件"""
        readme_names = ["README.md", "README.txt", "README", "readme.md"]
        for name in readme_names:
            readme_path = os.path.join(source_dir, name)
            if os.path.exists(readme_path):
                try:
                    import shutil
                    shutil.copy2(readme_path, dest_dir / "README.md")
                    return str(dest_dir / "README.md")
                except:
                    pass
        return None

    def _create_marketplace_entry(self, skill_info: Dict) -> Dict:
        """创建skill市场条目"""
        return {
            "name": skill_info.get("name"),
            "full_name": skill_info.get("full_name"),
            "installed_at": skill_info.get("installed_at"),
            "installed_files": skill_info.get("installed_files"),
            "skill_dir": skill_info.get("skill_dir"),
            "status": "installed",
            "rating": 0,
            "downloads": 0,
            "description": skill_info.get("description", "")
        }

    def _get_marketplace(self, params: Dict) -> Dict:
        """获取skill市场"""
        category = params.get("category")
        sort_by = params.get("sort_by", "installed_at")
        order = params.get("order", "desc")

        skills = self.skill_marketplace.get("skills", [])

        if category:
            skills = [s for s in skills if s.get("category") == category]

        if sort_by == "stars":
            skills.sort(key=lambda x: x.get("stars", 0), reverse=(order == "desc"))
        elif sort_by == "rating":
            skills.sort(key=lambda x: x.get("rating", 0), reverse=(order == "desc"))
        elif sort_by == "downloads":
            skills.sort(key=lambda x: x.get("downloads", 0), reverse=(order == "desc"))
        else:
            skills.sort(key=lambda x: x.get("installed_at", ""), reverse=(order == "desc"))

        return {
            "success": True,
            "skills": skills,
            "total_count": len(skills),
            "categories": self.skill_marketplace.get("categories", {}),
            "last_updated": self.skill_marketplace.get("last_updated")
        }

    def _update_marketplace(self, params: Dict) -> Dict:
        """更新skill市场"""
        discover_result = self._discover_popular_skills({"min_stars": 5, "max_results": 100})

        if discover_result.get("success"):
            popular_skills = discover_result.get("skills", [])

            self.skill_marketplace["skills"] = popular_skills

            categories = {}
            for skill in popular_skills:
                topics = skill.get("topics", [])
                for topic in topics:
                    if topic not in categories:
                        categories[topic] = []
                    categories[topic].append(skill.get("name"))

            self.skill_marketplace["categories"] = categories
            self._save_skill_marketplace()

            return {
                "success": True,
                "total_skills": len(popular_skills),
                "total_categories": len(categories),
                "message": "Skill市场更新成功"
            }

        return discover_result

    def _get_skill_info(self, params: Dict) -> Dict:
        """获取skill详细信息"""
        name = params.get("name")

        for skill in self.skill_marketplace.get("skills", []):
            if skill.get("name") == name or skill.get("full_name") == name:
                return {
                    "success": True,
                    "skill": skill
                }

        return {
            "success": False,
            "error": f"未找到skill: {name}"
        }

    def _search_marketplace(self, params: Dict) -> Dict:
        """搜索skill市场"""
        query = params.get("query", "").lower()
        category = params.get("category")

        skills = self.skill_marketplace.get("skills", [])

        results = []
        for skill in skills:
            if query:
                if (query in skill.get("name", "").lower() or
                    query in skill.get("description", "").lower() or
                    query in skill.get("full_name", "").lower()):
                    results.append(skill)
            elif category:
                if category in skill.get("topics", []):
                    results.append(skill)

        return {
            "success": True,
            "skills": results,
            "total_count": len(results),
            "query": query
        }

    def _get_categories(self, params: Dict) -> Dict:
        """获取skill分类"""
        return {
            "success": True,
            "categories": self.skill_marketplace.get("categories", {}),
            "total_categories": len(self.skill_marketplace.get("categories", {}))
        }

    def _recommend_skills(self, params: Dict) -> Dict:
        """推荐skill"""
        based_on = params.get("based_on", [])
        max_recommendations = params.get("max_recommendations", 5)

        recommended = []

        for skill in self.skill_marketplace.get("skills", []):
            if skill.get("name") not in based_on:
                topics = skill.get("topics", [])
                score = len([t for t in topics if t in based_on])

                if score > 0:
                    recommended.append({
                        "skill": skill,
                        "relevance_score": score
                    })

        recommended.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "success": True,
            "recommendations": [r["skill"] for r in recommended[:max_recommendations]],
            "total": len(recommended)
        }

    def _get_downloaded_skills(self, params: Dict) -> Dict:
        """获取已下载的skills"""
        downloaded = []

        if self.local_skills_dir.exists():
            for skill_dir in self.local_skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_files = list(skill_dir.glob("*skill*.py"))
                    if skill_files:
                        downloaded.append({
                            "name": skill_dir.name,
                            "path": str(skill_dir),
                            "files": [str(f) for f in skill_dir.glob("*.py")],
                            "has_readme": (skill_dir / "README.md").exists()
                        })

        return {
            "success": True,
            "skills": downloaded,
            "total_count": len(downloaded)
        }


skill = GitHubSkillDiscovery()
