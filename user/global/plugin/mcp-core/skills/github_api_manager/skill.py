#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Core - GitHub API管理技能

功能:
- 获取和管理GitHub所有API端点
- 提供API文档和使用方法
- 支持API调用测试
- 自动更新API信息
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


class GitHubAPIManager(Skill):
    """GitHub API管理技能"""

    name = "github_api_manager"
    description = "GitHub API管理 - 获取和管理GitHub所有API端点"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_cache_file = self.config.get("api_cache_file", "github_api_cache.pickle")  # 使用pickle格式提高性能
        self.api_endpoints = []
        self.last_updated = None
        self._session = requests.Session()  # 使用会话对象复用连接
        self._memory_cache = {}  # 内存缓存，减少文件读取
        self._cache_expiry = timedelta(hours=24)  # 缓存过期时间
        self._api_index = {}  # API索引，提高搜索性能
        self._load_api_cache()
        self._build_api_index()  # 构建API索引


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
        print(f"[GitHubAPIManager] [{level.upper()}] {message}")

    def get_parameters(self) -> Dict:
        """获取参数定义"""
        return {
            "action": {
                "type": "string",
                "required": True,
                "description": "执行的动作",
                "enum": [
                    "get_all_apis",
                    "search_apis",
                    "update_apis",
                    "get_api_details",
                    "test_api",
                    "export_apis"
                ]
            },
            "query": {
                "type": "string",
                "required": False,
                "description": "API搜索查询"
            },
            "api_id": {
                "type": "string",
                "required": False,
                "description": "API ID"
            },
            "endpoint": {
                "type": "string",
                "required": False,
                "description": "API端点"
            },
            "method": {
                "type": "string",
                "required": False,
                "description": "HTTP方法"
            },
            "params": {
                "type": "object",
                "required": False,
                "description": "API参数"
            },
            "output_file": {
                "type": "string",
                "required": False,
                "description": "导出文件路径"
            }
        }

    def validate_params(self, params: Dict) -> tuple[bool, Optional[str]]:
        """验证参数"""
        if "action" not in params:
            return False, "缺少必需参数: action"

        action = params["action"]

        if action == "search_apis" and "query" not in params:
            return False, "搜索API需要 query 参数"

        if action == "get_api_details" and "api_id" not in params:
            return False, "获取API详情需要 api_id 参数"

        if action == "test_api":
            if "endpoint" not in params:
                return False, "测试API需要 endpoint 参数"
            if "method" not in params:
                return False, "测试API需要 method 参数"

        return True, None

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
        else:
            return {
                "success": False,
                "error": f"未知动作: {action_param}"
            }

    def _load_api_cache(self):
        """加载API缓存"""
        # 检查内存缓存是否有效
        if self._memory_cache and self._is_cache_valid():
            self._log("从内存缓存加载API端点")
            return
        
        if os.path.exists(self.api_cache_file):
            try:
                # 尝试使用pickle格式加载
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
                    # 兼容旧的JSON格式
                    with open(self.api_cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                
                self.api_endpoints = data.get("endpoints", [])
                self.last_updated = data.get("last_updated")
                # 更新内存缓存
                self._memory_cache = data
                self._log(f"从缓存加载了 {len(self.api_endpoints)} 个API端点")
            except Exception as e:
                self._log(f"加载API缓存失败: {e}", "error")
        else:
            # 初始化默认API端点
            self._initialize_default_apis()

    def _save_api_cache(self):
        """保存API缓存"""
        try:
            data = {
                "endpoints": self.api_endpoints,
                "last_updated": datetime.now().isoformat()
            }
            # 更新内存缓存
            self._memory_cache = data
            
            # 使用pickle格式保存，提高性能
            if self.api_cache_file.endswith('.pickle'):
                with open(self.api_cache_file, "wb") as f:
                    pickle.dump(data, f)
            else:
                # 兼容旧的JSON格式
                with open(self.api_cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._log(f"API缓存已保存，共 {len(self.api_endpoints)} 个端点")
        except Exception as e:
            self._log(f"保存API缓存失败: {e}", "error")

    def _build_api_index(self):
        """构建API索引，提高搜索性能"""
        self._api_index = {}
        for api in self.api_endpoints:
            # 索引API ID
            self._api_index[api["id"]] = api
            
            # 索引API名称和描述
            for term in api["name"].lower().split():
                if term not in self._api_index:
                    self._api_index[term] = []
                self._api_index[term].append(api)
            
            for term in api["description"].lower().split():
                if term not in self._api_index:
                    self._api_index[term] = []
                self._api_index[term].append(api)
            
            # 索引端点路径和描述
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
        # GitHub REST API v4 (GraphQL) 和 v3 主要端点
        self.api_endpoints = [
            {
                "id": "github_rest_v3",
                "name": "GitHub REST API v3",
                "base_url": "https://api.github.com",
                "description": "GitHub REST API v3",
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
                    }
                ]
            },
            {
                "id": "github_graphql",
                "name": "GitHub GraphQL API",
                "base_url": "https://api.github.com/graphql",
                "description": "GitHub GraphQL API",
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
                    }
                ]
            },
            {
                "id": "github_oauth",
                "name": "GitHub OAuth API",
                "base_url": "https://github.com",
                "description": "GitHub OAuth API",
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
                    }
                ]
            }
        ]
        self.last_updated = datetime.now().isoformat()
        self._save_api_cache()
        self._build_api_index()  # 构建API索引
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
        results = []  # 使用列表存储结果

        # 使用索引进行快速搜索
        if query:
            query_terms = query.split()
            for term in query_terms:
                if term in self._api_index:
                    matching_apis = self._api_index[term]
                    for api in matching_apis:
                        if api not in results:  # 避免重复
                            results.append(api)
        else:
            # 如果查询为空，返回所有API
            results = self.api_endpoints.copy()

        # 进一步过滤，确保匹配度
        final_results = []
        for api in results:
            if query in api["name"].lower() or query in api["description"].lower():
                final_results.append(api)
            else:
                # 搜索端点路径和描述
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
        # 这里可以添加从GitHub官方文档或API获取最新端点的逻辑
        # 目前只是更新时间戳
        self.last_updated = datetime.now().isoformat()
        self._save_api_cache()

        return {
            "success": True,
            "message": "API端点已更新",
            "last_updated": self.last_updated,
            "total_apis": len(self.api_endpoints)
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
            # 构建完整URL
            url = endpoint
            if not url.startswith("http"):
                # 假设是相对路径，使用GitHub API基础URL
                url = f"https://api.github.com{endpoint}"

            # 替换路径参数
            for key, value in test_params.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))

            # 发送请求（使用会话对象提高性能）
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
        output_file = params.get("output_file", "github_apis.json")

        try:
            data = {
                "apis": self.api_endpoints,
                "last_updated": self.last_updated,
                "exported_at": datetime.now().isoformat()
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


# 技能实例
skill = GitHubAPIManager()


if __name__ == "__main__":
    # 测试技能
    skill = GitHubAPIManager()

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
    result = skill.execute("export_apis", {"action": "export_apis", "output_file": "github_apis_export.json"})
    print(f"   {result.get('message')}")

    print("\nGitHub API管理器测试完成")
