# 系统优化技能

## 功能说明

系统优化技能是一个用于管理系统资源、清理冗余文件、统一配置和日志管理的自动化工具。它提供了以下核心功能：

- **清理备份文件**：删除旧的备份文件，保留指定数量的最新备份
- **清理临时文件**：删除过期的临时文件，释放磁盘空间
- **统一日志管理**：将分散的日志文件集中管理，创建统一的日志配置
- **统一配置管理**：合并分散的配置文件，创建主配置文件
- **依赖检查**：检查系统依赖关系，确保系统组件正常工作
- **完整优化**：执行所有优化操作，生成优化报告

## 参数定义

| 参数名 | 类型 | 必需 | 描述 | 枚举值 | 默认值 |
|-------|------|------|------|-------|-------|
| action | string | 是 | 要执行的操作 | clean_backups, clean_temp, unify_logs, unify_config, check_dependencies, full_optimize | - |
| max_age_days | integer | 否 | 备份文件保留最大天数 | - | 30 |
| keep_count | integer | 否 | 备份文件最少保留数量 | - | 5 |
| max_age_hours | integer | 否 | 临时文件保留最大小时数 | - | 24 |

## 目录结构

技能使用以下目录结构：

| 目录 | 描述 | 默认路径 |
|------|------|----------|
| BACKUPS_DIR | 备份文件目录 | /python/backups |
| TEMP_DIR | 临时文件目录 | /python/Temp |
| LOGS_DIR | 日志文件目录 | /python/Logs |
| CONFIG_DIR | 配置文件目录 | /python/Config |

## 环境变量

技能使用以下环境变量：

- **AI_ROOT**：AI 项目的根目录，默认为 "/python"

## 使用示例

### 1. 清理备份文件

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "clean_backups", "max_age_days": 30, "keep_count": 5})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "cleaned_files": ["/python\\backups\\old_backup_1", "/python\\backups\\old_backup_2"],
    "cleaned_size": 104857600,
    "errors": [],
    "warnings": [],
    "updated_configs": []
  }
}
```

### 2. 清理临时文件

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "clean_temp", "max_age_hours": 24})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "cleaned_files": ["/python\\Temp\\temp_file_1.txt", "/python\\Temp\\temp_dir_1"],
    "cleaned_size": 52428800,
    "errors": [],
    "warnings": [],
    "updated_configs": []
  }
}
```

### 3. 统一日志管理

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "unify_logs"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "cleaned_files": [],
    "cleaned_size": 0,
    "errors": [],
    "warnings": [],
    "updated_configs": ["/python\\Logs\\log_config.json"]
  }
}
```

### 4. 统一配置管理

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "unify_config"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "cleaned_files": [],
    "cleaned_size": 0,
    "errors": [],
    "warnings": [],
    "updated_configs": ["/python\\Config\\master_config.json"]
  }
}
```

### 5. 检查依赖关系

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "check_dependencies"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "backup_dependencies": ["/python\\GJ\\GJ\\auto_backup.py"],
    "temp_dependencies": ["/python\\auto_workflow.py"],
    "log_dependencies": ["/python\\MCP_Core\\logger.py"],
    "config_dependencies": ["/python\\MCP_Core\\config.py"]
  }
}
```

### 6. 完整优化

```python
from skills.system_optimizer.skill import SystemOptimizerSkill

skill = SystemOptimizerSkill()
result = skill.execute({"action": "full_optimize"})
print(result)
```

**输出**：
```json
{
  "success": true,
  "result": {
    "timestamp": "2024-01-01T12:00:00",
    "summary": {
      "cleaned_files_count": 10,
      "cleaned_size_mb": 150.5,
      "errors_count": 0,
      "warnings_count": 0,
      "updated_configs_count": 2
    },
    "details": {
      "cleaned_files": [...],
      "cleaned_size": 157800000,
      "errors": [],
      "warnings": [],
      "updated_configs": [...]
    }
  }
}
```

## 优化报告

完整优化操作会生成详细的优化报告，保存到以下位置：

```
/python/Logs/optimization_report_YYYYMMDD_HHMMSS.json
```

报告包含以下信息：

- **timestamp**：优化执行时间
- **summary**：优化摘要，包括清理的文件数量、释放的空间等
- **details**：详细的优化结果，包括清理的文件列表、错误和警告等

## 配置文件

### 1. 统一日志配置

技能会在 `/python/Logs` 目录下创建 `log_config.json` 文件，包含以下配置：

```json
{
  "version": "1.0",
  "unified_log_dir": "/python/Logs",
  "log_rotation": {"max_size": "10MB", "backup_count": 5},
  "log_levels": {"default": "INFO", "mcp_core": "DEBUG", "workflow": "INFO"},
  "log_files": {
    "system": "system.log",
    "mcp": "mcp.log",
    "workflow": "workflow.log",
    "error": "error.log"
  }
}
```

### 2. 主配置文件

技能会在 `/python/Config` 目录下创建 `master_config.json` 文件，合并所有发现的配置文件。

## 依赖检查

技能会检查以下依赖关系：

| 类别 | 依赖项 |
|------|--------|
| 备份依赖 | GJ/auto_backup.py, file_backup/skill.py |
| 临时文件依赖 | auto_workflow.py, cache.py |
| 日志依赖 | logger.py, server.py |
| 配置依赖 | config.py, config_manager.py, ai.py |

## 注意事项

1. **数据安全**：清理操作会删除文件，请确保重要数据已备份
2. **权限要求**：需要对目标目录有写入权限
3. **执行时间**：完整优化可能需要较长时间，特别是在首次执行时
4. **系统影响**：清理操作可能会暂时影响系统性能

## 故障排除

### 常见问题

1. **目录不存在**：技能会自动创建必要的目录结构
2. **权限不足**：确保对目标目录有写入权限
3. **文件被占用**：某些文件可能被其他进程占用，会在错误列表中显示

### 错误处理

技能包含错误处理机制，会捕获并记录执行过程中的错误，并在返回结果中包含错误信息。

## 版本历史

- **1.0.0**：初始版本，包含基本的系统优化功能

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个技能！
