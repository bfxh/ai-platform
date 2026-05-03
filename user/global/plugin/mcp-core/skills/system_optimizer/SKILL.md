# 系统优化技能

## 描述

自动清理和优化 \python 系统，包括备份清理、临时文件清理、日志统一、配置统一。

## 功能

### 1. 清理备份文件
- 自动删除超过 30 天的旧备份
- 保留最近 5 个备份
- 显示清理统计

### 2. 清理临时文件
- 删除超过 24 小时的临时文件
- 清理缓存和临时目录
- 显示释放空间

### 3. 统一日志管理
- 合并分散的日志文件
- 创建统一日志配置
- 设置日志轮转策略

### 4. 统一配置管理
- 合并多个 MCP 配置文件
- 创建主配置文件
- 更新配置引用

### 5. 依赖检查
- 检查备份相关依赖
- 检查临时文件依赖
- 检查日志依赖
- 检查配置依赖

## 用法

### 命令行
```bash
# 清理备份
python /python/MCP_Core/skills/system_optimizer/skill.py clean_backups

# 清理临时文件
python /python/MCP_Core/skills/system_optimizer/skill.py clean_temp

# 统一日志
python /python/MCP_Core/skills/system_optimizer/skill.py unify_logs

# 统一配置
python /python/MCP_Core/skills/system_optimizer/skill.py unify_config

# 检查依赖
python /python/MCP_Core/skills/system_optimizer/skill.py check_dependencies

# 完整优化
python /python/MCP_Core/skills/system_optimizer/skill.py full_optimize
```

### MCP 调用
```json
{
  "skill": "system_optimizer",
  "action": "full_optimize",
  "params": {}
}
```

## 配置

```json
{
  "max_backup_age_days": 30,
  "min_backup_keep_count": 5,
  "max_temp_age_hours": 24,
  "log_rotation_size": "10MB",
  "log_backup_count": 5
}
```

## 输出

- 清理的文件列表
- 释放的空间大小
- 更新的配置文件
- 优化报告

## 依赖

- Python 3.8+
- 标准库 (os, json, shutil, pathlib)

## 注意事项

- 清理前会检查依赖关系
- 重要文件不会被删除
- 操作会记录日志
- 生成详细的优化报告
