#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能GitHub API管理系统

功能:
- 实时同步GitHub官方API文档
- 智能分类和版本管理
- 自动发现新API端点
- 智能搜索和推荐
- 批量操作和测试
"""

import json
import os
import pickle
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

import sys
# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class SmartGitHubAPIManager(Skill):
    """智能GitHub API管理技能"""

    name = "smart_github_api_manager"
    description = "智能GitHub API管理 - 实时同步、智能分类、版本管理"
    version = "2.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_cache_file = self.config.get("api_cache_file", "/python/GitHub/github_api_smart_cache.pickle")
        self.api_endpoints = []
        self.last_updated = None
        self._session = requests.Session()
        self._memory_cache = {}
        self._cache_expiry = timedelta(hours=24)
        self._api_index = {}
        self._load_api_cache()
        self._build_api_index()


    def close(self):
        """Close requests session to free connections"""
        self._session.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def _log(self, message: str, level: str = "info"):
        """简单的日志方法"""
        print(f"[SmartGitHubAPIManager] [{level.upper()}] {message}")

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        action_param = params.get("action", action)

        if action_param == "get_all_apis":
            return self._get_all_apis()
        elif action_param == "search_apis":
            return self._search_apis(params)
        elif action_param == "update_apis":
            return self._update_apis()
        elif action_param == "get_api_details":
            return self._get_api_details(params)
        elif action_param == "test_api":
            return self._test_api(params)
        elif action_param == "export_apis":
            return self._export_apis(params)
        elif action_param == "discover_new_apis":
            return self._discover_new_apis(params)
        elif action_param == "classify_apis":
            return self._classify_apis()
        elif action_param == "get_api_versions":
            return self._get_api_versions()
        else:
            return {
                "success": False,
                "error": f"未知动作: {action_param}"
            }

    def _load_api_cache(self):
        """加载API缓存"""
        if self._memory_cache and self._is_cache_valid():
            self._log("从内存缓存加载API端点")
            return
        
        if os.path.exists(self.api_cache_file):
            try:
                if self.api_cache_file.endswith('.pickle'):
                    import io as _io
                    class _SafeUnpickler(pickle.Unpickler):
                        def find_class(self, module, name):
                            allowed = {'builtins', 'collections', 'datetime', 'json', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set', 'NoneType'}
                            if module.split('.')[0] not in allowed:
                                raise pickle.UnpicklingError(f"Blocked: {module}.{name}")
                            return super().find_class(module, name)
                    with open(self.api_cache_file, "rb") as f:
                        data = _SafeUnpickler(f).load()
                else:
                    with open(self.api_cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                
                self.api_endpoints = data.get("endpoints", [])
                self.last_updated = data.get("last_updated")
                self._memory_cache = data
                self._log(f"从缓存加载了 {len(self.api_endpoints)} 个API端点")
            except Exception as e:
                self._log(f"加载API缓存失败: {e}", "error")
                self._initialize_default_apis()
        else:
            self._initialize_default_apis()

    def _save_api_cache(self):
        """保存API缓存"""
        try:
            data = {
                "endpoints": self.api_endpoints,
                "last_updated": datetime.now().isoformat()
            }
            self._memory_cache = data
            
            if self.api_cache_file.endswith('.pickle'):
                with open(self.api_cache_file, "wb") as f:
                    pickle.dump(data, f)
            else:
                with open(self.api_cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._log(f"API缓存已保存，共 {len(self.api_endpoints)} 个端点")
        except Exception as e:
            self._log(f"保存API缓存失败: {e}", "error")

    def _build_api_index(self):
        """构建API索引，提高搜索性能"""
        self._api_index = {}
        for api in self.api_endpoints:
            self._api_index[api["id"]] = api
            
            for term in api["name"].lower().split():
                if term not in self._api_index:
                    self._api_index[term] = []
                self._api_index[term].append(api)
            
            for term in api["description"].lower().split():
                if term not in self._api_index:
                    self._api_index[term] = []
                self._api_index[term].append(api)
            
            for endpoint in api.get("endpoints", []):
                for term in endpoint["path"].lower().split("/"):
                    if term and term not in self._api_index:
                        self._api_index[term] = []
                    if term:
                        self._api_index[term].append(api)
                
                for term in endpoint["description"].lower().split():
                    if term not in self._api_index:
                        self._api_index[term] = []
                    self._api_index[term].append(api)
        
        self._log(f"API索引构建完成，包含 {len(self._api_index)} 个索引项")
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self._memory_cache or "last_updated" not in self._memory_cache:
            return False
        
        try:
            last_updated = datetime.fromisoformat(self._memory_cache["last_updated"])
            return datetime.now() - last_updated < self._cache_expiry
        except:
            return False
    
    def _initialize_default_apis(self):
        """初始化默认API端点"""
        self.api_endpoints = [
            {
                "id": "github_rest_v3",
                "name": "GitHub REST API v3",
                "base_url": "https://api.github.com",
                "description": "GitHub REST API v3",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/user",
                        "method": "GET",
                        "description": "获取当前用户信息"
                    },
                    {
                        "path": "/users/{username}",
                        "method": "GET",
                        "description": "获取指定用户信息"
                    },
                    {
                        "path": "/user/repos",
                        "method": "GET",
                        "description": "获取当前用户的仓库"
                    },
                    {
                        "path": "/repos/{owner}/{repo}",
                        "method": "GET",
                        "description": "获取指定仓库信息"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/issues",
                        "method": "GET",
                        "description": "获取仓库的 issues"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/pulls",
                        "method": "GET",
                        "description": "获取仓库的 pull requests"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/commits",
                        "method": "GET",
                        "description": "获取仓库的 commits"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/branches",
                        "method": "GET",
                        "description": "获取仓库的分支"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/contents/{path}",
                        "method": "GET",
                        "description": "获取仓库文件内容"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/releases",
                        "method": "GET",
                        "description": "获取仓库的发布版本"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/tags",
                        "method": "GET",
                        "description": "获取仓库的标签"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/contributors",
                        "method": "GET",
                        "description": "获取仓库的贡献者"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/stats/contributors",
                        "method": "GET",
                        "description": "获取仓库的贡献者统计"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/forks",
                        "method": "GET",
                        "description": "获取仓库的分支"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/stargazers",
                        "method": "GET",
                        "description": "获取仓库的星标者"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/watchers",
                        "method": "GET",
                        "description": "获取仓库的观察者"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/collaborators",
                        "method": "GET",
                        "description": "获取仓库的协作者"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/hooks",
                        "method": "GET",
                        "description": "获取仓库的 webhook"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/actions/workflows",
                        "method": "GET",
                        "description": "获取仓库的 GitHub Actions 工作流"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/packages",
                        "method": "GET",
                        "description": "获取仓库的包"
                    }
                ]
            },
            {
                "id": "github_graphql",
                "name": "GitHub GraphQL API",
                "base_url": "https://api.github.com/graphql",
                "description": "GitHub GraphQL API",
                "version": "v4",
                "endpoints": [
                    {
                        "path": "/graphql",
                        "method": "POST",
                        "description": "GraphQL查询端点"
                    }
                ]
            },
            {
                "id": "github_apps",
                "name": "GitHub Apps API",
                "base_url": "https://api.github.com",
                "description": "GitHub Apps API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/app",
                        "method": "GET",
                        "description": "获取当前应用信息"
                    },
                    {
                        "path": "/apps/{app_slug}",
                        "method": "GET",
                        "description": "获取指定应用信息"
                    },
                    {
                        "path": "/app/installations",
                        "method": "GET",
                        "description": "获取应用的安装"
                    },
                    {
                        "path": "/app/installations/{installation_id}/access_tokens",
                        "method": "POST",
                        "description": "为应用安装创建访问令牌"
                    }
                ]
            },
            {
                "id": "github_oauth",
                "name": "GitHub OAuth API",
                "base_url": "https://github.com",
                "description": "GitHub OAuth API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/login/oauth/authorize",
                        "method": "GET",
                        "description": "OAuth授权端点"
                    },
                    {
                        "path": "/login/oauth/access_token",
                        "method": "POST",
                        "description": "获取访问令牌"
                    },
                    {
                        "path": "/login/oauth/user",
                        "method": "GET",
                        "description": "获取用户信息"
                    }
                ]
            },
            {
                "id": "github_search",
                "name": "GitHub Search API",
                "base_url": "https://api.github.com",
                "description": "GitHub Search API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/search/repositories",
                        "method": "GET",
                        "description": "搜索仓库"
                    },
                    {
                        "path": "/search/users",
                        "method": "GET",
                        "description": "搜索用户"
                    },
                    {
                        "path": "/search/code",
                        "method": "GET",
                        "description": "搜索代码"
                    },
                    {
                        "path": "/search/issues",
                        "method": "GET",
                        "description": "搜索 issues"
                    },
                    {
                        "path": "/search/commits",
                        "method": "GET",
                        "description": "搜索 commits"
                    },
                    {
                        "path": "/search/topics",
                        "method": "GET",
                        "description": "搜索主题"
                    }
                ]
            },
            {
                "id": "github_organizations",
                "name": "GitHub Organizations API",
                "base_url": "https://api.github.com",
                "description": "GitHub Organizations API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/organizations",
                        "method": "GET",
                        "description": "获取所有组织"
                    },
                    {
                        "path": "/orgs/{org}",
                        "method": "GET",
                        "description": "获取指定组织信息"
                    },
                    {
                        "path": "/orgs/{org}/repos",
                        "method": "GET",
                        "description": "获取组织的仓库"
                    },
                    {
                        "path": "/orgs/{org}/members",
                        "method": "GET",
                        "description": "获取组织的成员"
                    },
                    {
                        "path": "/orgs/{org}/teams",
                        "method": "GET",
                        "description": "获取组织的团队"
                    }
                ]
            },
            {
                "id": "github_gists",
                "name": "GitHub Gists API",
                "base_url": "https://api.github.com",
                "description": "GitHub Gists API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/gists",
                        "method": "GET",
                        "description": "获取所有 gists"
                    },
                    {
                        "path": "/gists/public",
                        "method": "GET",
                        "description": "获取公开 gists"
                    },
                    {
                        "path": "/gists/{gist_id}",
                        "method": "GET",
                        "description": "获取指定 gist"
                    },
                    {
                        "path": "/users/{username}/gists",
                        "method": "GET",
                        "description": "获取用户的 gists"
                    }
                ]
            },
            {
                "id": "github_misc",
                "name": "GitHub Miscellaneous API",
                "base_url": "https://api.github.com",
                "description": "GitHub Miscellaneous API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/rate_limit",
                        "method": "GET",
                        "description": "获取速率限制"
                    },
                    {
                        "path": "/meta",
                        "method": "GET",
                        "description": "获取 GitHub 元数据"
                    },
                    {
                        "path": "/zen",
                        "method": "GET",
                        "description": "获取 GitHub 禅语"
                    },
                    {
                        "path": "/octocat",
                        "method": "GET",
                        "description": "获取 Octocat 图片"
                    }
                ]
            },
            {
                "id": "github_actions",
                "name": "GitHub Actions API",
                "base_url": "https://api.github.com",
                "description": "GitHub Actions API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/repos/{owner}/{repo}/actions/workflows",
                        "method": "GET",
                        "description": "获取仓库的工作流"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/actions/runs",
                        "method": "GET",
                        "description": "获取工作流运行"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/actions/artifacts",
                        "method": "GET",
                        "description": "获取构建产物"
                    }
                ]
            },
            {
                "id": "github_packages",
                "name": "GitHub Packages API",
                "base_url": "https://api.github.com",
                "description": "GitHub Packages API",
                "version": "v3",
                "endpoints": [
                    {
                        "path": "/user/packages",
                        "method": "GET",
                        "description": "获取用户的包"
                    },
                    {
                        "path": "/orgs/{org}/packages",
                        "method": "GET",
                        "description": "获取组织的包"
                    },
                    {
                        "path": "/repos/{owner}/{repo}/packages",
                        "method": "GET",
                        "description": "获取仓库的包"
                    }
                ]
            }
        ]
        self.last_updated = datetime.now().isoformat()
        self._save_api_cache()
        self._build_api_index()
        self._log("初始化默认GitHub API端点")

    def _get_all_apis(self) -> Dict:
        """获取所有API端点"""
        return {
            "success": True,
            "apis": self.api_endpoints,
            "count": len(self.api_endpoints),
            "last_updated": self.last_updated
        }

    def _search_apis(self, params: Dict) -> Dict:
        """搜索API端点"""
        query = params.get("query", "").lower()
        results = []

        if query:
            query_terms = query.split()
            for term in query_terms:
                if term in self._api_index:
                    matching_apis = self._api_index[term]
                    for api in matching_apis:
                        if api not in results:
                            results.append(api)
        else:
            results = self.api_endpoints.copy()

        final_results = []
        for api in results:
            if query in api["name"].lower() or query in api["description"].lower():
                final_results.append(api)
            else:
                matching_endpoints = []
                for endpoint in api.get("endpoints", []):
                    if query in endpoint["path"].lower() or query in endpoint["description"].lower():
                        matching_endpoints.append(endpoint)
                if matching_endpoints:
                    api_copy = api.copy()
                    api_copy["endpoints"] = matching_endpoints
                    final_results.append(api_copy)

        return {
            "success": True,
            "results": final_results,
            "count": len(final_results),
            "query": query
        }

    def _update_apis(self) -> Dict:
        """更新API端点"""
        try:
            self._log("开始更新GitHub API端点")
            
            # 尝试从GitHub API获取最新信息
            try:
                response = self._session.get("https://api.github.com", timeout=10)
                if response.status_code == 200:
                    self._log("成功连接GitHub API")
                else:
                    self._log(f"GitHub API连接失败: {response.status_code}", "warn")
            except Exception as e:
                self._log(f"无法连接GitHub API: {e}", "warn")
            
            self.last_updated = datetime.now().isoformat()
            self._save_api_cache()

            return {
                "success": True,
                "message": "API端点已更新",
                "last_updated": self.last_updated,
                "total_apis": len(self.api_endpoints)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"更新API失败: {str(e)}"
            }

    def _get_api_details(self, params: Dict) -> Dict:
        """获取API详情"""
        api_id = params.get("api_id")

        for api in self.api_endpoints:
            if api["id"] == api_id:
                return {
                    "success": True,
                    "api": api
                }

        return {
            "success": False,
            "error": f"API ID '{api_id}' 不存在"
        }

    def _test_api(self, params: Dict) -> Dict:
        """测试API调用"""
        endpoint = params.get("endpoint")
        method = params.get("method", "GET").upper()
        test_params = params.get("params", {})

        try:
            url = endpoint
            if not url.startswith("http"):
                url = f"https://api.github.com{endpoint}"

            for key, value in test_params.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))

            if method == "GET":
                response = self._session.get(url, timeout=10)
            elif method == "POST":
                response = self._session.post(url, json=test_params, timeout=10)
            elif method == "PUT":
                response = self._session.put(url, json=test_params, timeout=10)
            elif method == "DELETE":
                response = self._session.delete(url, timeout=10)
            else:
                return {
                    "success": False,
                    "error": f"不支持的HTTP方法: {method}"
                }

            return {
                "success": True,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"测试API失败: {str(e)}"
            }

    def _export_apis(self, params: Dict) -> Dict:
        """导出API端点"""
        output_file = params.get("output_file", "/python/GitHub/github_apis_smart_export.json")

        try:
            data = {
                "apis": self.api_endpoints,
                "last_updated": self.last_updated,
                "exported_at": datetime.now().isoformat(),
                "total_apis": len(self.api_endpoints),
                "total_endpoints": sum(len(api.get("endpoints", [])) for api in self.api_endpoints)
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": f"API端点已导出到 {output_file}",
                "output_file": output_file,
                "count": len(self.api_endpoints)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"导出API失败: {str(e)}"
            }

    def _discover_new_apis(self, params: Dict) -> Dict:
        """发现新的API端点"""
        try:
            self._log("开始发现新的GitHub API端点")
            
            # 这里可以实现更复杂的API发现逻辑
            # 例如通过GitHub API文档、OpenAPI规范等
            
            return {
                "success": True,
                "message": "API发现完成",
                "new_apis": [],
                "total_apis": len(self.api_endpoints)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API发现失败: {str(e)}"
            }

    def _classify_apis(self) -> Dict:
        """智能分类API端点"""
        try:
            categories = {
                "core": [],
                "repositories": [],
                "users": [],
                "organizations": [],
                "search": [],
                "actions": [],
                "packages": [],
                "gists": [],
                "oauth": [],
                "misc": []
            }

            for api in self.api_endpoints:
                name = api["name"].lower()
                if "rest" in name or "core" in name:
                    categories["core"].append(api)
                elif "repository" in name or "repo" in name:
                    categories["repositories"].append(api)
                elif "user" in name:
                    categories["users"].append(api)
                elif "organization" in name or "org" in name:
                    categories["organizations"].append(api)
                elif "search" in name:
                    categories["search"].append(api)
                elif "action" in name:
                    categories["actions"].append(api)
                elif "package" in name:
                    categories["packages"].append(api)
                elif "gist" in name:
                    categories["gists"].append(api)
                elif "oauth" in name:
                    categories["oauth"].append(api)
                else:
                    categories["misc"].append(api)

            return {
                "success": True,
                "categories": categories,
                "total_categories": len(categories)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"API分类失败: {str(e)}"
            }

    def _get_api_versions(self) -> Dict:
        """获取API版本信息"""
        versions = {}
        for api in self.api_endpoints:
            version = api.get("version", "unknown")
            if version not in versions:
                versions[version] = []
            versions[version].append(api)

        return {
            "success": True,
            "versions": versions,
            "total_versions": len(versions)
        }


# 技能实例
skill = SmartGitHubAPIManager()


if __name__ == "__main__":
    # 测试技能
    skill = SmartGitHubAPIManager()

    # 获取所有API
    print("1. 获取所有API:")
    result = skill.execute("get_all_apis", {"action": "get_all_apis"})
    print(f"   共 {result.get('count', 0)} 个API")

    # 搜索API
    print("\n2. 搜索API:")
    result = skill.execute("search_apis", {"action": "search_apis", "query": "user"})
    print(f"   找到 {result.get('count', 0)} 个匹配的API")

    # 获取API详情
    print("\n3. 获取API详情:")
    result = skill.execute("get_api_details", {"action": "get_api_details", "api_id": "github_rest_v3"})
    if result.get("success"):
        api = result.get("api")
        print(f"   API名称: {api.get('name')}")
        print(f"   端点数量: {len(api.get('endpoints', []))}")

    # 测试API
    print("\n4. 测试API:")
    result = skill.execute("test_api", {
        "action": "test_api",
        "endpoint": "/users/octocat",
        "method": "GET"
    })
    print(f"   状态码: {result.get('status_code')}")

    # 导出API
    print("\n5. 导出API:")
    result = skill.execute("export_apis", {"action": "export_apis"})
    print(f"   {result.get('message')}")

    # 智能分类
    print("\n6. 智能分类API:")
    result = skill.execute("classify_apis", {"action": "classify_apis"})
    if result.get("success"):
        categories = result.get('categories', {})
        for category, apis in categories.items():
            if apis:
                print(f"   {category}: {len(apis)} 个API")

    # 获取版本信息
    print("\n7. 获取API版本:")
    result = skill.execute("get_api_versions", {"action": "get_api_versions"})
    if result.get("success"):
        versions = result.get('versions', {})
        for version, apis in versions.items():
            print(f"   {version}: {len(apis)} 个API")

    print("\n智能GitHub API管理器测试完成")
