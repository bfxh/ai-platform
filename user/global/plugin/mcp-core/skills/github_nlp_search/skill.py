#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能GitHub API自然语言搜索与推荐系统

功能:
- 自然语言查询理解
- 智能API推荐
- 多语言示例代码生成
- 上下文感知推荐
- 历史使用分析
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import sys
# 导入技能基类
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill


class GitHubNLPSearch(Skill):
    """GitHub API自然语言搜索与推荐技能"""

    name = "github_nlp_search"
    description = "GitHub API自然语言搜索与推荐 - 理解自然语言查询，智能推荐API，生成示例代码"
    version = "1.0.0"
    author = "MCP Core Team"

    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.api_cache_file = self.config.get("api_cache_file", "/python/GitHub/github_apis_smart_export.json")
        self.history_file = self.config.get("history_file", "/python/GitHub/search_history.json")
        self.api_endpoints = []
        self.search_history = []
        self._load_api_data()
        self._load_search_history()

    def _log(self, message: str, level: str = "info"):
        """简单的日志方法"""
        print(f"[GitHubNLPSearch] [{level.upper()}] {message}")

    def execute(self, action: str, params: Dict) -> Dict:
        """执行技能"""
        action_param = params.get("action", action)

        if action_param == "natural_language_search":
            return self._natural_language_search(params)
        elif action_param == "recommend_apis":
            return self._recommend_apis(params)
        elif action_param == "generate_code":
            return self._generate_code(params)
        elif action_param == "get_search_history":
            return self._get_search_history()
        elif action_param == "clear_history":
            return self._clear_history()
        else:
            return {
                "success": False,
                "error": f"未知动作: {action_param}"
            }

    def _load_api_data(self):
        """加载API数据"""
        try:
            if os.path.exists(self.api_cache_file):
                with open(self.api_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.api_endpoints = data.get("apis", [])
                self._log(f"加载了 {len(self.api_endpoints)} 个API端点")
            else:
                self._log("API缓存文件不存在，使用默认数据", "warn")
                self._load_default_apis()
        except Exception as e:
            self._log(f"加载API数据失败: {e}", "error")
            self._load_default_apis()

    def _load_default_apis(self):
        """加载默认API数据"""
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
            }
        ]

    def _load_search_history(self):
        """加载搜索历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.search_history = json.load(f)
                self._log(f"加载了 {len(self.search_history)} 条搜索历史")
            else:
                self._log("搜索历史文件不存在，创建新的", "info")
                self.search_history = []
        except Exception as e:
            self._log(f"加载搜索历史失败: {e}", "error")
            self.search_history = []

    def _save_search_history(self):
        """保存搜索历史"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.search_history, f, ensure_ascii=False, indent=2)
            self._log(f"保存了 {len(self.search_history)} 条搜索历史")
        except Exception as e:
            self._log(f"保存搜索历史失败: {e}", "error")

    def _natural_language_search(self, params: Dict) -> Dict:
        """自然语言搜索API"""
        query = params.get("query", "").lower()
        if not query:
            return {
                "success": False,
                "error": "缺少查询参数"
            }

        # 记录搜索历史
        self.search_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat()
        })
        # 只保留最近100条历史
        self.search_history = self.search_history[-100:]
        self._save_search_history()

        # 意图识别
        intent = self._identify_intent(query)
        
        # 搜索相关API
        results = self._search_relevant_apis(query, intent)

        return {
            "success": True,
            "query": query,
            "intent": intent,
            "results": results,
            "count": len(results)
        }

    def _identify_intent(self, query: str) -> str:
        """识别用户意图"""
        intent_patterns = {
            "get_user_info": ["用户信息", "获取用户", "user info", "get user"],
            "get_repo_info": ["仓库信息", "获取仓库", "repo info", "get repo"],
            "get_issues": ["issues", "问题", "bug"],
            "get_pulls": ["pull request", "pr", "合并请求"],
            "get_commits": ["commits", "提交", "commit"],
            "get_branches": ["分支", "branches"],
            "search_repos": ["搜索仓库", "search repo"],
            "search_users": ["搜索用户", "search user"],
            "search_code": ["搜索代码", "search code"],
            "get_rate_limit": ["速率限制", "rate limit"],
            "get_metadata": ["元数据", "metadata"],
            "get_gists": ["gist", "代码片段"],
            "get_organizations": ["组织", "organization"]
        }

        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern.lower() in query:
                    return intent

        return "general_search"

    def _search_relevant_apis(self, query: str, intent: str) -> List[Dict]:
        """搜索相关的API"""
        results = []

        for api in self.api_endpoints:
            for endpoint in api.get("endpoints", []):
                # 匹配描述
                if query in endpoint["description"].lower():
                    results.append({
                        "api_id": api["id"],
                        "api_name": api["name"],
                        "endpoint": endpoint["path"],
                        "method": endpoint["method"],
                        "description": endpoint["description"],
                        "relevance": 1.0
                    })
                # 匹配路径
                elif any(term in endpoint["path"].lower() for term in query.split()):
                    results.append({
                        "api_id": api["id"],
                        "api_name": api["name"],
                        "endpoint": endpoint["path"],
                        "method": endpoint["method"],
                        "description": endpoint["description"],
                        "relevance": 0.8
                    })

        # 根据意图增强相关性
        intent_mappings = {
            "get_user_info": ["/user", "/users/"],
            "get_repo_info": ["/repos/"],
            "get_issues": ["/issues"],
            "get_pulls": ["/pulls"],
            "get_commits": ["/commits"],
            "get_branches": ["/branches"],
            "search_repos": ["/search/repositories"],
            "search_users": ["/search/users"],
            "search_code": ["/search/code"],
            "get_rate_limit": ["/rate_limit"],
            "get_metadata": ["/meta"],
            "get_gists": ["/gists"],
            "get_organizations": ["/orgs/", "/organizations"]
        }

        if intent in intent_mappings:
            for result in results:
                for pattern in intent_mappings[intent]:
                    if pattern in result["endpoint"]:
                        result["relevance"] = min(result["relevance"] + 0.3, 1.0)

        # 按相关性排序
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return results[:10]  # 只返回前10个结果

    def _recommend_apis(self, params: Dict) -> Dict:
        """智能推荐API"""
        context = params.get("context", "")
        user_history = params.get("user_history", [])

        # 分析历史使用模式
        recommended = []

        # 基于历史使用推荐
        if user_history:
            # 分析最常用的API类别
            category_counts = {}
            for history_item in user_history:
                query = history_item.get("query", "").lower()
                intent = self._identify_intent(query)
                category_counts[intent] = category_counts.get(intent, 0) + 1

            # 按使用频率排序
            popular_intents = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]

            for intent, _ in popular_intents:
                intent_results = self._search_relevant_apis("", intent)
                recommended.extend(intent_results[:2])

        # 基于上下文推荐
        if context:
            context_results = self._search_relevant_apis(context, "general_search")
            recommended.extend(context_results[:3])

        # 去重
        seen = set()
        unique_recommended = []
        for api in recommended:
            key = f"{api['endpoint']}_{api['method']}"
            if key not in seen:
                seen.add(key)
                unique_recommended.append(api)

        return {
            "success": True,
            "recommended": unique_recommended[:5],
            "count": len(unique_recommended[:5])
        }

    def _generate_code(self, params: Dict) -> Dict:
        """生成示例代码"""
        endpoint = params.get("endpoint")
        method = params.get("method", "GET")
        language = params.get("language", "python")
        params = params.get("params", {})

        if not endpoint:
            return {
                "success": False,
                "error": "缺少endpoint参数"
            }

        code_templates = {
            "python": {
                "GET": """import requests

# GitHub API endpoint
url = "{url}"

# Headers (optional)
headers = {{
    "Accept": "application/vnd.github.v3+json"
}}

# Parameters
params = {params}

# Make request
response = requests.get(url, headers=headers, params=params)

# Handle response
if response.status_code == 200:
    data = response.json()
    print("Success:", data)
else:
    print(f"Error: {{response.status_code}}", response.text)
""",
                "POST": """import requests

# GitHub API endpoint
url = "{url}"

# Headers
headers = {{
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}}

# Data
payload = {params}

# Make request
response = requests.post(url, headers=headers, json=payload)

# Handle response
if response.status_code in [200, 201]:
    data = response.json()
    print("Success:", data)
else:
    print(f"Error: {{response.status_code}}", response.text)
"""
            },
            "javascript": {
                "GET": """const fetch = require('node-fetch');

// GitHub API endpoint
const url = "{url}";

// Headers
const headers = {
  "Accept": "application/vnd.github.v3+json"
};

// Parameters
const params = new URLSearchParams({params});
const fullUrl = `${url}?${params}`;

// Make request
fetch(fullUrl, {
  method: 'GET',
  headers: headers
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
""",
                "POST": """const fetch = require('node-fetch');

// GitHub API endpoint
const url = "{url}";

// Headers
const headers = {
  "Accept": "application/vnd.github.v3+json",
  "Content-Type": "application/json"
};

// Data
const payload = {params};

// Make request
fetch(url, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => console.log('Success:', data))
.catch(error => console.error('Error:', error));
"""
            },
            "bash": {
                "GET": """#!/bin/bash

# GitHub API endpoint
URL="{url}"

# Parameters
PARAMS="{params_query}"

# Make request
curl -X GET "$URL?$PARAMS" \
  -H "Accept: application/vnd.github.v3+json"
""",
                "POST": """#!/bin/bash

# GitHub API endpoint
URL="{url}"

# Data
DATA='{params_json}'

# Make request
curl -X POST "$URL" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  -d "$DATA"
"""
            },
            "python3": {
                "GET": """import requests

# GitHub API endpoint
url = "{url}"

# Headers (optional)
headers = {{
    "Accept": "application/vnd.github.v3+json"
}}

# Parameters
params = {params}

# Make request
response = requests.get(url, headers=headers, params=params)

# Handle response
if response.status_code == 200:
    data = response.json()
    print("Success:", data)
else:
    print(f"Error: {response.status_code}", response.text)
"""
            }
        }

        # 构建URL
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"https://api.github.com{endpoint}"

        # 替换路径参数
        for key, value in params.items():
            if f"{{{key}}}" in url:
                url = url.replace(f"{{{key}}}", str(value))

        # 生成代码
        if language in code_templates:
            if method in code_templates[language]:
                template = code_templates[language][method]
                
                # 处理参数
                if language == "bash":
                    if method == "GET":
                        params_query = "&" .join([f"{k}={v}" for k, v in params.items()])
                        code = template.replace("{url}", url).replace("{params_query}", params_query)
                    else:
                        import json
                        params_json = json.dumps(params)
                        code = template.replace("{url}", url).replace("{params_json}", params_json)
                else:
                    import json
                    params_str = json.dumps(params, indent=2)
                    # 使用字符串替换避免大括号冲突
                    code = template.replace("{url}", url).replace("{params}", params_str)
            else:
                return {
                    "success": False,
                    "error": f"不支持的HTTP方法: {method}"
                }
        else:
            return {
                "success": False,
                "error": f"不支持的编程语言: {language}"
            }

        return {
            "success": True,
            "endpoint": endpoint,
            "method": method,
            "language": language,
            "code": code
        }

    def _get_search_history(self) -> Dict:
        """获取搜索历史"""
        return {
            "success": True,
            "history": self.search_history,
            "count": len(self.search_history)
        }

    def _clear_history(self) -> Dict:
        """清除搜索历史"""
        self.search_history = []
        self._save_search_history()
        return {
            "success": True,
            "message": "搜索历史已清除"
        }


# 技能实例
skill = GitHubNLPSearch()


if __name__ == "__main__":
    # 测试技能
    skill = GitHubNLPSearch()

    # 自然语言搜索
    print("1. 自然语言搜索:")
    result = skill.execute("natural_language_search", {
        "action": "natural_language_search",
        "query": "获取用户信息"
    })
    print(f"   找到 {result.get('count', 0)} 个匹配的API")
    for api in result.get('results', [])[:3]:
        print(f"   - {api['endpoint']} ({api['method']}): {api['description']}")

    # 智能推荐
    print("\n2. 智能推荐:")
    result = skill.execute("recommend_apis", {
        "action": "recommend_apis",
        "context": "我需要获取仓库信息"
    })
    print(f"   推荐 {result.get('count', 0)} 个API")
    for api in result.get('recommended', [])[:3]:
        print(f"   - {api['endpoint']} ({api['method']}): {api['description']}")

    # 生成代码
    print("\n3. 生成Python代码:")
    result = skill.execute("generate_code", {
        "action": "generate_code",
        "endpoint": "/users/octocat",
        "method": "GET",
        "language": "python",
        "params": {}
    })
    if result.get("success"):
        print("   生成的代码:")
        print(result.get("code"))

    # 生成JavaScript代码
    print("\n4. 生成JavaScript代码:")
    result = skill.execute("generate_code", {
        "action": "generate_code",
        "endpoint": "/repos/octocat/Hello-World",
        "method": "GET",
        "language": "javascript",
        "params": {}
    })
    if result.get("success"):
        print("   生成的代码:")
        print(result.get("code"))

    # 生成Bash代码
    print("\n5. 生成Bash代码:")
    result = skill.execute("generate_code", {
        "action": "generate_code",
        "endpoint": "/search/repositories",
        "method": "GET",
        "language": "bash",
        "params": {"q": "python", "sort": "stars"}
    })
    if result.get("success"):
        print("   生成的代码:")
        print(result.get("code"))

    print("\nGitHub API自然语言搜索与推荐系统测试完成")
