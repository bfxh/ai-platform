# GitHub API测试工具

## 描述
高级GitHub API测试工具 - 批量测试、实时调试、性能测试、并发测试、速率限制测试

## 功能特性
- 🧪 **批量API测试** - 同时测试多个API端点
- 🔧 **实时调试** - 详细的请求和响应信息
- ⚡ **性能测试** - 测量响应时间和吞吐量
- 📊 **并发测试** - 模拟多用户并发访问
- 🚦 **速率限制测试** - 测试GitHub API速率限制
- 🔐 **认证测试** - 测试认证和授权
- 📋 **测试报告** - 生成详细的测试报告

## 安装
```bash
# 安装依赖
pip install requests

# 启动技能
python skill.py
```

## 可用动作

### 核心功能
- `test_api` - 测试单个API
- `batch_test` - 批量测试API
- `performance_test` - 性能测试
- `concurrent_test` - 并发测试
- `rate_limit_test` - 速率限制测试
- `auth_test` - 认证测试
- `get_test_history` - 获取测试历史
- `generate_report` - 生成测试报告

## 使用示例

### 1. 测试单个API
```python
result = skill.execute('test_api', {
    'endpoint': '/users/octocat',
    'method': 'GET'
})

if result['success']:
    test_result = result['test_result']
    print(f"状态码: {test_result['status_code']}")
    print(f"响应时间: {test_result['duration']:.3f} 秒")
    print(f"响应内容: {test_result['content'][:100]}...")
```

### 2. 批量测试
```python
# 测试指定端点
result = skill.execute('batch_test', {
    'endpoints': [
        {'endpoint': '/users/octocat', 'method': 'GET'},
        {'endpoint': '/repos/octocat/Hello-World', 'method': 'GET'},
        {'endpoint': '/rate_limit', 'method': 'GET'}
    ],
    'concurrency': 3
})

# 测试所有默认端点
result = skill.execute('batch_test', {
    'concurrency': 5
})

print(f"测试结果: {result['summary']['success']}/{result['summary']['total']} 成功")
print(f"总时间: {result['summary']['total_time']:.2f} 秒")
```

### 3. 性能测试
```python
result = skill.execute('performance_test', {
    'endpoint': '/users/octocat',
    'iterations': 100,
    'concurrency': 10
})

metrics = result['performance_metrics']
print(f"总请求: {metrics['total_requests']}")
print(f"成功请求: {metrics['success_requests']}")
print(f"平均响应时间: {metrics['average_response_time']:.3f} 秒")
print(f"最大响应时间: {metrics['max_response_time']:.3f} 秒")
print(f"QPS: {metrics['requests_per_second']:.2f}")
```

### 4. 并发测试
```python
result = skill.execute('concurrent_test', {
    'endpoint': '/users/octocat',
    'concurrent_users': 50,
    'duration': 60  # 60秒
})

metrics = result['concurrent_metrics']
print(f"并发用户: {metrics['concurrent_users']}")
print(f"总请求: {metrics['total_requests']}")
print(f"QPS: {metrics['requests_per_second']:.2f}")
print(f"错误率: {metrics['error_rate']:.2f}%")
```

### 5. 速率限制测试
```python
result = skill.execute('rate_limit_test', {
    'requests_per_minute': 60,
    'duration': 120  # 120秒
})

metrics = result['rate_limit_metrics']
print(f"总请求: {metrics['total_requests']}")
print(f"成功请求: {metrics['success_requests']}")
print(f"遇到速率限制: {metrics['rate_limit_encountered']}")
print(f"请求速率: {metrics['requests_per_minute']:.2f} RPM")
```

### 6. 认证测试
```python
result = skill.execute('auth_test', {
    'endpoint': '/user',
    'token': 'your_github_token_here'
})

for test in result['results']:
    print(f"{test['type']}: 状态码 {test['result']['status_code']}")
```

### 7. 生成测试报告
```python
result = skill.execute('generate_report', {
    'output_file': 'comprehensive_test_report.json'
})

print(f"报告生成成功: {result['report_file']}")
print(f"总测试数: {result['report']['summary']['total_tests']}")
print(f"总请求数: {result['report']['summary']['total_requests']}")
print(f"成功率: {result['report']['summary']['total_success']}/{result['report']['summary']['total_requests']}")
```

## 测试结果存储
所有测试结果都存储在 `/python/GitHub/test_results/` 目录中，包括：
- `batch_test_*.json` - 批量测试结果
- `performance_test_*.json` - 性能测试结果
- `concurrent_test_*.json` - 并发测试结果
- `rate_limit_test_*.json` - 速率限制测试结果
- `auth_test_*.json` - 认证测试结果
- `test_report_*.json` - 综合测试报告

## 配置

### 环境变量
- `GITHUB_API_TOKEN` - GitHub API令牌（可选）
- `GITHUB_API_TEST_RESULTS` - 测试结果存储目录

### 配置文件
```json
{
  "api_cache_file": "/python/GitHub/github_apis_smart_export.json",
  "test_results_dir": "/python/GitHub/test_results",
  "timeout": 30,
  "concurrency": 10
}
```

## 性能优化
- **并发测试** - 使用线程池提高测试效率
- **批量测试** - 支持并行测试多个API
- **缓存机制** - 缓存API数据减少重复请求
- **超时处理** - 自动处理超时和错误

## 安全建议
- 使用环境变量存储API令牌
- 避免在测试中使用真实的认证信息
- 合理设置测试速率，避免触发GitHub API速率限制
- 定期清理测试结果文件，避免占用过多磁盘空间

## 故障排除
- **API连接失败** - 检查网络连接和GitHub API状态
- **速率限制** - 减少测试频率，实现指数退避策略
- **认证错误** - 检查API令牌权限和有效性
- **性能测试失败** - 检查系统资源和网络状况

## 扩展建议
- 集成更多测试类型（如功能测试、回归测试）
- 添加测试计划和测试用例管理
- 实现持续集成和自动化测试
- 支持更多API版本和端点

## 版本历史
- **1.0.0** - 基础版本
  - 批量API测试
  - 性能测试
  - 并发测试
  - 速率限制测试
  - 认证测试
  - 测试报告生成

## 联系信息
- **作者**: MCP Core Team
- **版本**: 1.0.0
- **更新时间**: 2026-04-18

---

**GitHub API测试工具** - 让API测试变得简单高效！
