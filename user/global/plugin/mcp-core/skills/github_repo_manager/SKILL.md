# GitHub 仓库管理器 (github_repo_manager)

## 描述

GitHub仓库管理器，支持仓库克隆、批量下载、分析和同步。

## 功能

### 1. 仓库克隆
- 单仓库克隆
- 浅克隆支持 (--depth)
- 自动目录组织 (owner/repo)

### 2. 批量克隆
- 从文件读取仓库列表
- 批量处理
- 成功/失败统计

### 3. 仓库分析
- 文件类型统计
- 编程语言分布
- 仓库大小计算
- Git状态检查

### 4. 仓库同步
- 自动拉取更新
- 分支检测
- 冲突处理

## 用法

### 命令行

```bash
# 克隆单个仓库
python /python/MCP_Core/skills/github_repo_manager/skill.py clone https://github.com/user/repo.git

# 克隆到指定目录
python /python/MCP_Core/skills/github_repo_manager/skill.py clone <url> D:/custom/path

# 批量克隆
python /python/MCP_Core/skills/github_repo_manager/skill.py batch repos.txt

# 分析仓库
python /python/MCP_Core/skills/github_repo_manager/skill.py analyze /python/GitHub/owner/repo

# 同步仓库
python /python/MCP_Core/skills/github_repo_manager/skill.py sync /python/GitHub/owner/repo

# 列出所有仓库
python /python/MCP_Core/skills/github_repo_manager/skill.py list

# 创建批量克隆模板
python /python/MCP_Core/skills/github_repo_manager/skill.py create_batch
```

### MCP 调用

```json
{
  "skill": "github_repo_manager",
  "action": "clone_repository",
  "params": {
    "repo_url": "https://github.com/user/repo.git",
    "depth": 1
  }
}
```

## 批量克隆文件格式

```text
# GitHub 仓库批量克隆列表
# 每行一个仓库URL
# 以 # 开头的行会被忽略

# AI/ML 相关
https://github.com/microsoft/DeepSpeed
https://github.com/huggingface/transformers

# 工具类
https://github.com/yt-dlp/yt-dlp
```

## 目录结构

```
/python/GitHub/
├── repos/                  # 克隆的仓库
│   ├── owner1/
│   │   └── repo1/
│   └── owner2/
│       └── repo2/
├── backups/                # 仓库备份
└── repos_to_clone.txt      # 批量克隆列表
```

## 分析输出

```
路径: /python/GitHub/owner/repo
Git仓库: 是
总大小: 15.23 MB

文件类型:
  .py        45 个文件
  .md        12 个文件
  .json       8 个文件

编程语言:
  Python        45 个文件
  Markdown      12 个文件
  JSON           8 个文件
```

## 配置

### 配置文件
```json
{
  "default_clone_depth": 1,
  "auto_pull": true,
  "backup_enabled": true,
  "backup_dir": "/python/GitHub/backups"
}
```

### 环境变量
```bash
# Windows
set GITHUB_TOKEN=your_token
```

## 依赖

- Python 3.8+
- Git
- 标准库 (os, json, subprocess, pathlib, urllib)
