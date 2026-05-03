# 自动化工作流技能

## 功能介绍

自动化工作流技能是一个专门用于自动执行一系列任务的工具，能够帮助开发者构建和执行复杂的自动化流程，如搜索GitHub项目、克隆项目、运行测试等。

## 核心功能

- **工作流管理**：创建、列出和执行工作流
- **多步骤执行**：支持执行多个连续的任务步骤
- **多种步骤类型**：支持shell命令、技能调用和Python代码执行
- **上下文传递**：在步骤之间传递数据和结果
- **日志记录**：自动记录工作流执行过程和结果
- **GitHub集成**：与GitHub项目搜索技能集成，实现自动化的项目发现和管理

## 安装方法

1. 确保 MCP Core 已安装并运行
2. 将技能目录复制到 `MCP_Core/skills/` 目录下
3. 重启 MCP Core 服务

## 使用方法

### 命令行使用

```bash
# 列出所有工作流
python -m MCP_Core.cli skill automated_workflow list

# 创建GitHub项目搜索工作流
python -m MCP_Core.cli skill automated_workflow create-github-search-workflow --name "ml_projects" --query "python machine learning" --sort "stars" --per_page 10 --min_stars 10000

# 运行工作流
python -m MCP_Core.cli skill automated_workflow run --workflow "ml_projects"

# 创建自定义工作流
python -m MCP_Core.cli skill automated_workflow create --name "custom_workflow" --steps '[{"name": "Step 1", "type": "shell", "command": "echo Hello World"}, {"name": "Step 2", "type": "python", "code": "result = \"Python result\""}]' --description "自定义工作流"
```

### 编程接口

```python
from MCP_Core.skills.automated_workflow import AutomatedWorkflowSkill

# 初始化技能
skill = AutomatedWorkflowSkill()

# 创建GitHub搜索工作流
result = skill.execute("create-github-search-workflow", 
                     name="ml_projects",
                     query="python machine learning",
                     sort="stars",
                     per_page=10,
                     min_stars=10000)
print(result)

# 运行工作流
result = skill.execute("run", workflow="ml_projects")
print(result)

# 列出工作流
result = skill.execute("list")
print(result)

# 创建自定义工作流
steps = [
    {
        "name": "Step 1",
        "type": "shell",
        "command": "echo Hello World"
    },
    {
        "name": "Step 2",
        "type": "python",
        "code": "result = \"Python result\""
    }
]
result = skill.execute("create", name="custom_workflow", steps=steps, description="自定义工作流")
print(result)
```

## 工作流配置

### 工作流结构

工作流是一个JSON文件，包含以下字段：

- **name**：工作流名称
- **description**：工作流描述
- **steps**：工作流步骤列表
- **created_at**：创建时间

### 步骤类型

#### 1. Shell步骤

执行shell命令：

```json
{
  "name": "执行shell命令",
  "type": "shell",
  "command": "echo Hello World",
  "continue_on_error": false,
  "delay": 0
}
```

#### 2. 技能步骤

执行其他技能的命令：

```json
{
  "name": "执行技能",
  "type": "skill",
  "skill": "github_project_search",
  "command": "search",
  "params": {
    "query": "python machine learning",
    "sort": "stars"
  },
  "continue_on_error": false,
  "delay": 0
}
```

#### 3. Python步骤

执行Python代码：

```json
{
  "name": "执行Python代码",
  "type": "python",
  "code": "result = \"Python result\"\nlogger.info('Python代码执行完成')",
  "continue_on_error": false,
  "delay": 0
}
```

## 上下文变量

工作流执行过程中，步骤之间可以通过上下文变量传递数据：

- **${workflow_name}**：工作流名称
- **${timestamp}**：执行时间戳
- **${workflows_dir}**：工作流目录
- **${logs_dir}**：日志目录
- **${step_0_result}**：第0步的结果
- **${step_1_result}**：第1步的结果
- **...**：其他步骤的结果

## 示例工作流

### GitHub项目搜索工作流

```json
{
  "name": "github_search",
  "description": "GitHub项目搜索工作流",
  "steps": [
    {
      "name": "搜索GitHub项目",
      "type": "skill",
      "skill": "github_project_search",
      "command": "search",
      "params": {
        "query": "python machine learning",
        "sort": "stars",
        "per_page": 10
      }
    },
    {
      "name": "过滤项目",
      "type": "skill",
      "skill": "github_project_search",
      "command": "filter",
      "params": {
        "projects": "${step_0_result.items}",
        "min_stars": 1000
      }
    },
    {
      "name": "生成项目报告",
      "type": "skill",
      "skill": "github_project_search",
      "command": "generate-report",
      "params": {
        "projects": "${step_1_result}"
      }
    }
  ],
  "created_at": "2026-04-09T12:00:00Z"
}
```

### 项目克隆和测试工作流

```json
{
  "name": "project_test",
  "description": "项目克隆和测试工作流",
  "steps": [
    {
      "name": "克隆项目",
      "type": "skill",
      "skill": "github_project_search",
      "command": "clone",
      "params": {
        "repo_url": "https://github.com/username/repository.git"
      }
    },
    {
      "name": "安装依赖",
      "type": "shell",
      "command": "cd ${step_0_result.path} && pip install -r requirements.txt"
    },
    {
      "name": "运行测试",
      "type": "shell",
      "command": "cd ${step_0_result.path} && python -m pytest"
    }
  ],
  "created_at": "2026-04-09T12:00:00Z"
}
```

## 注意事项

1. **权限要求**：需要对工作流目录和日志目录有写入权限
2. **网络连接**：执行GitHub相关步骤需要网络连接
3. **依赖安装**：执行某些步骤可能需要安装相应的依赖
4. **错误处理**：工作流执行过程中出现错误会停止执行，除非设置了 `continue_on_error: true`
5. **执行时间**：复杂的工作流可能需要较长的执行时间

## 故障排除

### 工作流文件不存在
- 错误信息：`工作流文件不存在`
- 解决方法：确保工作流名称正确，或者先创建工作流

### 步骤执行失败
- 错误信息：`步骤执行失败`
- 解决方法：查看工作流日志，了解具体的错误原因

### 上下文变量未找到
- 错误信息：`上下文变量未找到`
- 解决方法：确保前一步骤执行成功，并且变量名称正确

### 技能未找到
- 错误信息：`执行技能失败: No module named 'MCP_Core.skills.xxx'`
- 解决方法：确保相应的技能已安装

## 扩展建议

1. **定时执行**：添加定时执行工作流的功能
2. **并行执行**：支持并行执行多个步骤，提高效率
3. **条件执行**：根据条件决定是否执行某些步骤
4. **错误处理**：添加更复杂的错误处理逻辑
5. **通知系统**：工作流执行完成后发送通知

## 版本历史

- **v1.0.0**：初始版本，支持基本的工作流创建和执行功能

## 贡献指南

欢迎提交 Issue 和 Pull Request，帮助改进这个技能。

## 许可证

MIT License