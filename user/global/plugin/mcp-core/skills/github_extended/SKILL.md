# GitHub扩展功能系统

## 描述
GitHub扩展功能系统 - 速率限制管理、批量操作、数据处理、分析工具、智能调度、错误处理、数据可视化

## 功能特性
- 🚦 **速率限制管理** - 监控和优化GitHub API速率限制
- 📦 **批量操作** - 并发执行多个API操作
- 🛠️ **数据处理** - 转换、过滤、聚合和规范化数据
- 📊 **分析工具** - 分析API使用、性能、错误和趋势
- 🤖 **智能调度** - 基于速率限制和优先级的智能调度
- 🔧 **错误处理** - 针对不同错误类型的处理策略
- 🎨 **数据可视化** - 生成API使用、性能和错误的可视化数据

## 安装
```bash
# 安装依赖
pip install requests

# 启动技能
python skill.py
```

## 可用动作

### 核心功能
- `rate_limit_management` - 速率限制管理
- `batch_operation` - 批量操作
- `data_processing` - 数据处理
- `analysis` - 分析工具
- `intelligent_scheduling` - 智能调度
- `error_handling` - 错误处理
- `data_visualization` - 数据可视化

## 使用示例

### 1. 速率限制管理
```python
# 检查速率限制
result = skill.execute('rate_limit_management', {
    'action': 'check'
})

if result['success']:
    rate_limit = result['rate_limit']
    core = rate_limit['resources']['core']
    print(f"核心API剩余: {core['remaining']}/{core['limit']}")
    print(f"重置时间: {core['reset']}")

# 优化速率限制使用
result = skill.execute('rate_limit_management', {
    'action': 'optimize'
})

print("优化建议:", result['optimization']['recommendations'])
```

### 2. 批量操作
```python
result = skill.execute('batch_operation', {
    'operations': [
        {'endpoint': '/users/octocat', 'method': 'GET'},
        {'endpoint': '/repos/octocat/Hello-World', 'method': 'GET'},
        {'endpoint': '/rate_limit', 'method': 'GET'}
    ],
    'concurrency': 3,
    'rate_limit_safe': True
})

print(f"批量操作结果: {result['summary']['success']}/{result['summary']['total']} 成功")
print(f"总时间: {result['summary']['total_time']:.2f} 秒")
print(f"结果文件: {result['result_file']}")
```

### 3. 数据处理
```python
# 转换数据
test_data = [
    {"name": "John", "age": 30, "city": "New York"},
    {"name": "Jane", "age": 25, "city": "London"}
]

result = skill.execute('data_processing', {
    'action': 'transform',
    'data': test_data,
    'transform_rules': {"name": "full_name", "age": "years_old"},
    'output_file': 'transformed_data.json'
})

print("处理后的数据:", result['processed_data'])

# 过滤数据
result = skill.execute('data_processing', {
    'action': 'filter',
    'data': test_data,
    'filter_rules': {"age": {"$gt": 25}}
})

print("过滤后的数据:", result['processed_data'])

# 聚合数据
result = skill.execute('data_processing', {
    'action': 'aggregate',
    'data': test_data,
    'aggregate_rules': {"city": "city"}
})

print("聚合后的数据:", result['processed_data'])
```

### 4. 分析工具
```python
analysis_data = [
    {
        "operation": {"endpoint": "/users/octocat", "method": "GET"},
        "result": {"status_code": 200, "duration": 0.5},
        "success": True,
        "timestamp": "2026-04-18T10:00:00"
    },
    {
        "operation": {"endpoint": "/repos/octocat/Hello-World", "method": "GET"},
        "result": {"status_code": 200, "duration": 0.3},
        "success": True,
        "timestamp": "2026-04-18T10:01:00"
    }
]

# API使用分析
result = skill.execute('analysis', {
    'analysis_type': 'api_usage',
    'data': analysis_data
})

print("API使用分析:", result['analysis_result'])

# 性能分析
result = skill.execute('analysis', {
    'analysis_type': 'performance',
    'data': analysis_data
})

print("性能分析:", result['analysis_result'])

# 错误分析
result = skill.execute('analysis', {
    'analysis_type': 'error_analysis',
    'data': analysis_data
})

print("错误分析:", result['analysis_result'])

# 趋势分析
result = skill.execute('analysis', {
    'analysis_type': 'trends',
    'data': analysis_data
})

print("趋势分析:", result['analysis_result'])
```

### 5. 智能调度
```python
result = skill.execute('intelligent_scheduling', {
    'operations': [
        {'endpoint': '/users/octocat', 'method': 'GET', 'priority': 1},
        {'endpoint': '/repos/octocat/Hello-World', 'method': 'GET', 'priority': 2},
        {'endpoint': '/rate_limit', 'method': 'GET', 'priority': 3}
    ],
    'strategy': 'priority'
})

print("调度结果:", result['scheduled_operations'])
```

### 6. 错误处理
```python
# 速率限制错误处理
result = skill.execute('error_handling', {
    'error_type': 'rate_limit'
})

print("速率限制错误处理策略:", result['error_handling'])

# 认证错误处理
result = skill.execute('error_handling', {
    'error_type': 'authentication'
})

print("认证错误处理策略:", result['error_handling'])

# 网络错误处理
result = skill.execute('error_handling', {
    'error_type': 'network'
})

print("网络错误处理策略:", result['error_handling'])
```

### 7. 数据可视化
```python
# API使用可视化
result = skill.execute('data_visualization', {
    'visualization_type': 'api_usage',
    'data': analysis_data,
    'output_file': 'api_usage_visualization.json'
})

print("API使用可视化文件:", result['output_file'])

# 性能可视化
result = skill.execute('data_visualization', {
    'visualization_type': 'performance',
    'data': analysis_data,
    'output_file': 'performance_visualization.json'
})

print("性能可视化文件:", result['output_file'])

# 错误分析可视化
result = skill.execute('data_visualization', {
    'visualization_type': 'error_analysis',
    'data': analysis_data,
    'output_file': 'error_analysis_visualization.json'
})

print("错误分析可视化文件:", result['output_file'])

# 趋势可视化
result = skill.execute('data_visualization', {
    'visualization_type': 'trends',
    'data': analysis_data,
    'output_file': 'trends_visualization.json'
})

print("趋势可视化文件:", result['output_file'])
```

## 数据存储
所有数据和分析结果都存储在以下目录中：
- `/python/GitHub/data/` - 原始和处理后的数据
- `/python/GitHub/analysis/` - 分析报告和可视化数据
- `/python/GitHub/rate_limit.json` - 速率限制信息

## 配置

### 环境变量
- `GITHUB_API_TOKEN` - GitHub API令牌（可选）
- `GITHUB_DATA_DIR` - 数据存储目录
- `GITHUB_ANALYSIS_DIR` - 分析结果目录

### 配置文件
```json
{
  "api_cache_file": "/python/GitHub/github_apis_smart_export.json",
  "data_dir": "/python/GitHub/data",
  "analysis_dir": "/python/GitHub/analysis",
  "rate_limit_file": "/python/GitHub/rate_limit.json",
  "concurrency": 10,
  "timeout": 30
}
```

## 性能优化
- **并发执行** - 使用线程池提高批量操作效率
- **速率限制感知** - 智能调整请求频率
- **数据缓存** - 减少重复API调用
- **批处理** - 合并多个请求减少API调用次数

## 安全建议
- 使用环境变量存储API令牌
- 合理设置并发数，避免触发GitHub API速率限制
- 定期清理数据文件，避免占用过多磁盘空间
- 实现指数退避策略处理API错误

## 故障排除
- **速率限制错误** - 减少请求频率，使用速率限制管理功能
- **认证错误** - 检查API令牌有效性
- **网络错误** - 检查网络连接，实现重试机制
- **数据处理错误** - 检查输入数据格式

## 扩展建议
- 集成更多数据处理算法
- 添加机器学习模型进行预测分析
- 实现实时监控和告警
- 支持更多可视化类型

## 版本历史
- **1.0.0** - 基础版本
  - 速率限制管理
  - 批量操作
  - 数据处理
  - 分析工具
  - 智能调度
  - 错误处理
  - 数据可视化

## 联系信息
- **作者**: MCP Core Team
- **版本**: 1.0.0
- **更新时间**: 2026-04-18

---

**GitHub扩展功能系统** - 让GitHub API使用更加智能高效！
