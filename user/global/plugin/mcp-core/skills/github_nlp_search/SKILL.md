# GitHub API自然语言搜索与推荐系统

## 描述
智能GitHub API自然语言搜索与推荐系统 - 理解自然语言查询，智能推荐API，生成多语言示例代码

## 功能特性
- 🎯 **自然语言理解** - 理解用户的自然语言查询
- 🤖 **智能推荐** - 基于上下文和历史使用模式推荐API
- 💻 **多语言代码生成** - 支持Python、JavaScript、Bash等语言
- 📊 **上下文感知** - 基于用户上下文提供相关推荐
- 📈 **历史分析** - 分析用户使用历史，提供个性化推荐

## 安装
```bash
# 安装依赖
pip install requests

# 启动技能
python skill.py
```

## 可用动作

### 核心功能
- `natural_language_search` - 自然语言搜索API
- `recommend_apis` - 智能推荐API
- `generate_code` - 生成示例代码
- `get_search_history` - 获取搜索历史
- `clear_history` - 清除搜索历史

## 使用示例

### 1. 自然语言搜索
```python
# 中文查询
result = skill.execute('natural_language_search', {
    'query': '获取用户信息'
})

# 英文查询
result = skill.execute('natural_language_search', {
    'query': 'get repository information'
})

# 复杂查询
result = skill.execute('natural_language_search', {
    'query': '搜索Python仓库并按星标排序'
})
```

### 2. 智能推荐
```python
# 基于上下文推荐
result = skill.execute('recommend_apis', {
    'context': '我需要获取仓库的issues和pull requests'
})

# 基于历史推荐
result = skill.execute('recommend_apis', {
    'user_history': [
        {'query': '获取用户信息', 'timestamp': '2026-04-18T10:00:00'},
        {'query': '获取仓库信息', 'timestamp': '2026-04-18T10:30:00'}
    ]
})
```

### 3. 生成示例代码
```python
# 生成Python代码
result = skill.execute('generate_code', {
    'endpoint': '/users/octocat',
    'method': 'GET',
    'language': 'python'
})

# 生成JavaScript代码
result = skill.execute('generate_code', {
    'endpoint': '/repos/octocat/Hello-World',
    'method': 'GET',
    'language': 'javascript'
})

# 生成Bash代码
result = skill.execute('generate_code', {
    'endpoint': '/search/repositories',
    'method': 'GET',
    'language': 'bash',
    'params': {'q': 'python', 'sort': 'stars'}
})
```

## 支持的查询类型

### 用户相关
- "获取用户信息"
- "获取指定用户信息"
- "user info"
- "get user profile"

### 仓库相关
- "获取仓库信息"
- "获取仓库的issues"
- "获取仓库的pull requests"
- "获取仓库的commits"
- "获取仓库的分支"
- "repo information"
- "get repository details"

### 搜索相关
- "搜索仓库"
- "搜索用户"
- "搜索代码"
- "search repositories"
- "search users"

### 其他
- "获取速率限制"
- "获取元数据"
- "获取代码片段"
- "获取组织信息"

## 支持的编程语言
- **Python** - requests库
- **JavaScript** - node-fetch
- **Bash** - curl命令

## 配置

### 环境变量
- `GITHUB_API_TOKEN` - GitHub API令牌（可选）
- `GITHUB_NLP_CACHE` - API缓存文件路径
- `GITHUB_NLP_HISTORY` - 搜索历史文件路径

### 配置文件
```json
{
  "api_cache_file": "/python/GitHub/github_apis_smart_export.json",
  "history_file": "/python/GitHub/search_history.json"
}
```

## 性能优化
- **意图识别** - 基于模式匹配的快速意图识别
- **缓存机制** - 缓存API数据和搜索结果
- **批处理** - 支持批量API推荐
- **异步处理** - 支持异步代码生成

## 安全建议
- 使用环境变量存储API令牌
- 避免在生成的代码中硬编码敏感信息
- 定期清理搜索历史
- 使用HTTPS进行API调用

## 故障排除
- **搜索无结果** - 尝试使用更具体的查询
- **推荐不准确** - 提供更多上下文信息
- **代码生成失败** - 检查API端点和参数格式
- **历史记录错误** - 删除历史文件重新生成

## 扩展建议
- 集成自然语言处理库（如spaCy、NLTK）
- 添加更多编程语言支持
- 实现API使用分析和优化建议
- 支持API文档自动生成

## 版本历史
- **1.0.0** - 基础版本
  - 自然语言搜索功能
  - 智能推荐系统
  - 多语言代码生成
  - 搜索历史管理

## 联系信息
- **作者**: MCP Core Team
- **版本**: 1.0.0
- **更新时间**: 2026-04-18

---

**GitHub API自然语言搜索与推荐系统** - 让GitHub API使用变得简单智能！
