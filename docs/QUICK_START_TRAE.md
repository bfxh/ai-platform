# \python TRAE 快速入门 (3分钟版)

> **版本**: v1.0 | **更新**: 2026-04-23 | **目标**: 3分钟内理解 \python

---

## 什么是 \python

**\python 是一个 AI 操作系统**，包含：
- 50+ 目录 | 2000+ 文件
- 44 个开源 AI 项目 (CLL_Projects)
- 108 个 MCP 工具
- 29 个 Skills 技能
- GSTACK 工作流引擎

---

## 核心目录 (5秒记忆)

```
\python\
├── MCP/JM/           # 3D建模工具 (Blender, UE5, Unity, Godot)
├── MCP/BC/           # 代码工具 (GitHub, 搜索, 修复)
├── MCP/Tools/        # 系统工具 (下载, 监控, 配置)
├── MCP_Core/         # 核心系统 (skills, workflow, agent)
├── gstack_core/      # GSTACK 工作流引擎
├── CC/                # 分类缓存 (1_Raw/2_Old/3_Unused)
├── CLL_Projects/     # 44个开源AI项目
└── scripts/          # 自动化脚本
```

---

## 黄金法则 (必须遵守)

| 规则 | 说明 |
|------|------|
| **GSTACK 优先** | 所有操作优先使用 GSTACK 工作流 |
| **JM/BC/Tools 分类** | 新文件必须分类：建模→JM, 代码→BC, 其他→Tools |
| **CC 缓存规则** | 原始→1_Raw, 旧版→2_Old, 未用→3_Unused |
| **受保护文件** | AGENTS.md, index.json, .gstack_protected 修改前必须备份 |

---

## 常用命令 (直接运行)

```bash
# 代码审查
python gstack_core.py review file.py

# 启动服务器
python MCP_Core/server.py

# 执行备份
python scripts/daily_backup.py

# 检查系统状态
python scripts/deep_check.py
```

---

## 文件分类决策树

```
新文件属于...
├── Blender/3D/UE/Unity/Godot → MCP/JM/
├── 代码/GitHub/搜索/修复/验证 → MCP/BC/
└── 其他所有 → MCP/Tools/
```

---

## 快速查找

| 需要找... | 去这里 |
|-----------|--------|
| Blender MCP | `MCP/JM/blender_mcp.py` |
| GitHub 工具 | `MCP/BC/github_*.py` |
| 系统监控 | `MCP/Tools/system_monitor.py` |
| GSTACK 核心 | `gstack_core/gstack_core.py` |
| 技能基类 | `MCP_Core/skills/base.py` |
| 每日备份 | `scripts/daily_backup.py` |

---

## 错误处理

```python
# GSTACK 不可用时
1. 检查: from gstack_core import GStackCore
2. 失败则告知用户进入降级模式
3. 仅提供只读服务

# 文件分类错误
1. Blender相关 → 移至 MCP/JM/
2. GitHub相关 → 移至 MCP/BC/
3. 其他 → 移至 MCP/Tools/
```

---

## 下一步

- **完整指南**: [TRAE_COMPLETE_GUIDE.md](TRAE_COMPLETE_GUIDE.md)
- **架构文档**: [AGENTS.md](AGENTS.md)
- **诊断工具**: `python scripts/deep_check.py`

---

> 记住: **GSTACK 优先, JM/BC/Tools 分类, CC 缓存历史**
