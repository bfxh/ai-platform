# GitHub API管理器 (github_api_manager)

## 描述

GitHub API管理技能，用于获取、管理和测试GitHub所有API端点。

## 功能

### 1. API管理
- 获取所有GitHub API端点
- 搜索API端点
- 更新API信息
- 导出API文档

### 2. API测试
- 测试API调用
- 支持GET、POST、PUT、DELETE方法
- 详细的响应信息

### 3. 缓存管理
- 本地缓存API信息
- 自动更新时间戳
- 持久化存储

## 支持的API

### GitHub REST API v3
- `/user` - 获取当前用户信息
- `/users/{username}` - 获取指定用户信息
- `/user/repos` - 获取当前用户的仓库
- `/repos/{owner}/{repo}` - 获取指定仓库信息
- `/repos/{owner}/{repo}/issues` - 获取仓库的 issues
- `/repos/{owner}/{repo}/pulls` - 获取仓库的 pull requests
- `/repos/{owner}/{repo}/commits` - 获取仓库的 commits
- `/repos/{owner}/{repo}/branches` - 获取仓库的分支

### GitHub GraphQL API
- `/graphql` - GraphQL查询端点

### GitHub Apps API
- `/app` - 获取当前应用信息
- `/apps/{app_slug}` - 获取指定应用信息

### GitHub OAuth API
- `/login/oauth/authorize` - OAuth授权端点
- `/login/oauth/access_token` - 获取访问令牌

## 用法

### MCP 调用

```json
{
  "skill": "github_api_manager",
  "action": "get_all_apis"
}
```

```json
{
  "skill": "github_api_manager",
  "action": "search_apis",
  "params": {
    "query": "user"
  }
}
```

```json
{
  "skill": "github_api_manager",
  "action": "test_api",
  "params": {
    "endpoint": "/users/octocat",
    "method": "GET"
  }
}
```

## 动作列表

| 动作 | 描述 | 必需参数 |
|------|------|----------|
| get_all_apis | 获取所有API端点 | 无 |
| search_apis | 搜索API端点 | query |
| update_apis | 更新API端点 | 无 |
| get_api_details | 获取API详情 | api_id |
| test_api | 测试API调用 | endpoint, method |
| export_apis | 导出API端点 | output_file (可选) |

## 配置选项

| 参数 | 默认值 | 描述 |
|------|--------|------|
| api_cache_file | github_api_cache.json | API缓存文件路径 |

## 依赖

- Python 3.8+
- requests

## 输出

- 操作成功/失败状态
- API端点列表
- 搜索结果
- API测试结果
- 导出状态

## 使用场景

1. **API文档管理**: 集中管理GitHub所有API端点
2. **开发辅助**: 快速查找和测试GitHub API
3. **集成测试**: 验证API调用的正确性
4. **自动化脚本**: 基于GitHub API的自动化工作流

## 注意事项

- 测试API时可能会受到GitHub API速率限制
- 某些API需要身份验证，测试时可能会返回401错误
- 缓存文件会自动创建在当前目录
- 建议定期更新API信息以保持最新
