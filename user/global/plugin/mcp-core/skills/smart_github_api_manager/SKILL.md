# 智能GitHub API管理器

## 描述
智能GitHub API管理系统 - 实时同步、智能分类、版本管理、批量操作

## 功能特性
- 📡 **实时同步** - 自动从GitHub官方获取最新API文档
- 🤖 **智能分类** - 基于功能自动分类API端点
- 📋 **版本管理** - 支持多个API版本的管理
- 🔍 **智能搜索** - 支持自然语言查询和智能推荐
- 🧪 **批量测试** - 内置测试环境，支持实时调试
- 📊 **数据分析** - 提供API使用分析和优化建议

## 安装
```bash
# 安装依赖
pip install requests

# 启动技能
python skill.py
```

## 可用动作

### 核心功能
- `get_all_apis` - 获取所有GitHub API端点
- `search_apis` - 搜索API端点（支持自然语言）
- `update_apis` - 更新API端点信息
- `get_api_details` - 获取API详情
- `test_api` - 测试API调用
- `export_apis` - 导出API端点

### 智能功能
- `discover_new_apis` - 发现新的API端点
- `classify_apis` - 智能分类API端点
- `get_api_versions` - 获取API版本信息

## 使用示例

### 1. 获取所有API
```python
result = skill.execute('get_all_apis', {})
print(f"共 {result['count']} 个API")
```

### 2. 搜索API
```python
# 自然语言搜索
result = skill.execute('search_apis', {'query': '获取用户信息'})

# 关键词搜索
result = skill.execute('search_apis', {'query': 'repo issues'})
```

### 3. 测试API
```python
result = skill.execute('test_api', {
    'endpoint': '/users/octocat',
    'method': 'GET'
})
print(f"状态码: {result['status_code']}")
```

### 4. 智能分类
```python
result = skill.execute('classify_apis', {})
categories = result['categories']
for category, apis in categories.items():
    print(f"{category}: {len(apis)} 个API")
```

### 5. 导出API
```python
result = skill.execute('export_apis', {
    'output_file': 'github_apis_complete.json'
})
print(result['message'])
```

## 配置

### 环境变量
- `GITHUB_API_TOKEN` - GitHub API令牌（可选）
- `GITHUB_API_CACHE` - 缓存文件路径

### 配置文件
```json
{
  "api_cache_file": "/python/GitHub/github_api_smart_cache.pickle",
  "cache_expiry": 24,
  "timeout": 30
}
```

## 支持的API类别
- **核心API** - GitHub REST API v3、GraphQL API
- **仓库管理** - 仓库、issues、pull requests、commits
- **用户管理** - 用户信息、个人资料
- **组织管理** - 组织、团队、成员
- **搜索功能** - 仓库搜索、用户搜索、代码搜索
- **Actions** - CI/CD工作流管理
- **Packages** - 包管理
- **Gists** - 代码片段管理
- **OAuth** - 认证授权
- **杂项** - 速率限制、元数据

## 版本历史
- **2.0.0** - 智能GitHub API管理器
  - 新增智能分类功能
  - 新增API发现功能
  - 新增版本管理功能
  - 优化搜索和推荐系统

- **1.0.0** - 基础GitHub API管理器
  - 基础API管理功能
  - 基本搜索和测试功能

## 性能优化
- 内存缓存 - 减少文件I/O操作
- 索引系统 - 提高搜索性能
- 批量操作 - 支持并行API调用
- 智能缓存 - 根据使用频率自动调整

## 安全建议
- 使用环境变量存储API令牌
- 避免在代码中硬编码敏感信息
- 定期更新API缓存
- 使用HTTPS进行API调用

## 故障排除
- **API连接失败** - 检查网络连接和GitHub API状态
- **速率限制** - 实现指数退避策略
- **缓存问题** - 删除缓存文件重新生成
- **认证错误** - 检查API令牌权限

## 扩展建议
- 集成GitHub Webhooks
- 添加API使用分析
- 支持更多API版本
- 实现API监控和告警

## 联系信息
- **作者**: MCP Core Team
- **版本**: 2.0.0
- **更新时间**: 2026-04-18

---

**智能GitHub API管理器** - 让GitHub API管理变得简单智能！
