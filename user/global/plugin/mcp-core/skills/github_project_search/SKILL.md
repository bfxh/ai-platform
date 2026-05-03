# GitHub项目搜索技能

## 功能介绍

GitHub项目搜索技能是一个专门用于自动搜索、过滤和管理GitHub项目的工具，能够帮助开发者快速发现和获取优质的开源项目。

## 核心功能

- **项目搜索**：使用GitHub API搜索项目，支持各种搜索参数
- **项目克隆**：自动克隆GitHub项目到本地
- **批量操作**：支持批量克隆多个项目
- **项目过滤**：根据语言、星数、Fork数等条件过滤项目
- **报告生成**：生成详细的项目报告
- **结果保存**：自动保存搜索结果和报告

## 安装方法

1. 确保 MCP Core 已安装并运行
2. 将技能目录复制到 `MCP_Core/skills/` 目录下
3. 重启 MCP Core 服务

## 使用方法

### 命令行使用

```bash
# 搜索GitHub项目
python -m MCP_Core.cli skill github_project_search search --query "python machine learning" --sort "stars" --per_page 10

# 克隆项目
python -m MCP_Core.cli skill github_project_search clone --repo_url "https://github.com/username/repository.git"

# 批量克隆项目
python -m MCP_Core.cli skill github_project_search batch-clone --repos '["https://github.com/username/repo1.git", "https://github.com/username/repo2.git"]'

# 过滤项目
python -m MCP_Core.cli skill github_project_search filter --projects '{"items": [...]}' --language "python" --min_stars 1000

# 生成项目报告
python -m MCP_Core.cli skill github_project_search generate-report --projects '{"items": [...]}'
```

### 编程接口

```python
from MCP_Core.skills.github_project_search import GitHubProjectSearchSkill

# 初始化技能
skill = GitHubProjectSearchSkill()

# 搜索项目
result = skill.execute("search", query="python machine learning", sort="stars", per_page=10)
print(result)

# 克隆项目
result = skill.execute("clone", repo_url="https://github.com/username/repository.git")
print(result)

# 批量克隆项目
result = skill.execute("batch-clone", repos=["https://github.com/username/repo1.git", "https://github.com/username/repo2.git"])
print(result)

# 过滤项目
filtered = skill.execute("filter", projects=search_result["items"], language="python", min_stars=1000)
print(filtered)

# 生成报告
report = skill.execute("generate-report", projects=filtered)
print(report)
```

## 配置说明

### 配置文件

技能会使用以下默认配置：

- **github_token**：GitHub API令牌（可选，用于增加API速率限制）
- **search_results_dir**：搜索结果保存目录
- **projects_dir**：项目克隆目录
- **default_search_params**：默认搜索参数

### 环境变量

可以通过环境变量设置GitHub令牌：

```bash
set GITHUB_TOKEN=your_github_token
```

## 搜索参数

### 主要搜索参数

- **query**：搜索查询字符串，支持GitHub搜索语法
- **sort**：排序字段（stars, forks, updated）
- **order**：排序顺序（asc, desc）
- **per_page**：每页结果数（1-100）
- **page**：页码

### GitHub搜索语法

GitHub搜索支持以下语法：

- `language:python`：按语言过滤
- `stars:>1000`：按星数过滤
- `forks:>100`：按Fork数过滤
- `created:>2023-01-01`：按创建时间过滤
- `updated:>2023-01-01`：按更新时间过滤
- `topic:machine-learning`：按主题过滤

## 示例场景

### 场景 1：搜索机器学习项目

```bash
python -m MCP_Core.cli skill github_project_search search --query "machine learning language:python stars:>10000" --sort "stars" --per_page 10
```

### 场景 2：克隆热门项目

```bash
python -m MCP_Core.cli skill github_project_search clone --repo_url "https://github.com/scikit-learn/scikit-learn.git"
```

### 场景 3：批量克隆多个项目

```bash
python -m MCP_Core.cli skill github_project_search batch-clone --repos '["https://github.com/scikit-learn/scikit-learn.git", "https://github.com/tensorflow/tensorflow.git", "https://github.com/pytorch/pytorch.git"]'
```

### 场景 4：过滤并生成报告

```bash
# 先搜索
python -m MCP_Core.cli skill github_project_search search --query "python web framework" --sort "stars" --per_page 20

# 然后过滤并生成报告
python -m MCP_Core.cli skill github_project_search filter --projects '{"items": [...]}' --language "python" --min_stars 5000
python -m MCP_Core.cli skill github_project_search generate-report --projects '{"items": [...]}'
```

## 注意事项

1. **API速率限制**：GitHub API有速率限制，未认证用户每小时只能请求60次，认证用户每小时可以请求5000次
2. **网络连接**：需要稳定的网络连接来访问GitHub API
3. **Git安装**：克隆项目需要系统安装Git
4. **存储空间**：克隆大型项目需要足够的存储空间
5. **权限**：需要对目标目录有写入权限

## 故障排除

### API速率限制
- 错误信息：`API rate limit exceeded`
- 解决方法：配置GitHub令牌或等待速率限制重置

### Git未安装
- 错误信息：`git: command not found`
- 解决方法：安装Git并添加到系统PATH

### 网络连接失败
- 错误信息：`ConnectionError: HTTPSConnectionPool`
- 解决方法：检查网络连接或使用代理

### 权限不足
- 错误信息：`PermissionError: [Errno 13] Permission denied`
- 解决方法：确保对目标目录有写入权限

## 扩展建议

1. **多线程克隆**：支持并行克隆多个项目，提高速度
2. **项目分析**：添加项目结构和依赖分析功能
3. **自动更新**：定期更新已克隆的项目
4. **集成CI**：与持续集成系统集成
5. **项目推荐**：基于历史搜索和克隆记录推荐项目

## 版本历史

- **v1.0.0**：初始版本，支持基本的搜索、克隆、过滤和报告功能

## 贡献指南

欢迎提交 Issue 和 Pull Request，帮助改进这个技能。

## 许可证

MIT License