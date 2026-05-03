# TRAE IDE — AI 能力包集成规则

本文件由 `/python/ai-plugin/plugin.yaml` 集中管理。
修改 TRAE 行为请编辑 ai-plugin 对应文件，通过 `install.sh` 同步。

---

## [!!] 第一步 — 启动后立即执行

**在做任何事情之前，按顺序完成以下两步:**

### 1. 读取系统记忆文件
```
打开并完整阅读: /python/WARNINGS.md
```

这个文件只有 5 个小节，2 分钟内能读完。它告诉你:
- 软件在哪里（真实路径，不是默认路径）
- 以前犯过什么错误（不要重犯）
- 环境是否正常

**不读这个文件 = 盲人摸象。你会猜错路径、重复已知错误。**

### 2. 运行环境检查
```bash
py /python/intervention/pre_session_check.py
```

确认所有关键路径和环境变量都存在。

---

## 🧠 自动加载 — 资源清单

TRAE 启动时自动加载以下资源（由 ai-plugin 管理）:

### 能力包核心规则
- `/python/ai-plugin/rules/workflow.md` — 任务执行工作流
- `/python/ai-plugin/rules/communication.md` — 沟通规范
- `/python/ai-plugin/rules/coding-style.md` — 代码规范
- `/python/ai-plugin/rules/security.md` — 安全规则

### 强制初始化
- 🔴 **Brain 记忆系统** (`/python/storage/Brain/`) — 每次任务前必须初始化
- 🔴 **Bug 记忆引擎** (`/python/storage/Brain/memory/bug_memory.py`) — 自动学习错误
- 🔴 **跨 Agent 共享上下文** (`/python/core/shared_context.py`) — 多 AI 协调

### 可用能力单元
- Skill: `/python/user/global/skill/` — 用户技能
- MCP: `/python/storage/mcp/` — JM (3D建模/Blender), BC (代码/GitHub), Tools (系统/自动化)
- CLL: `/python/storage/cll/` — 44 个开源 LLM 项目
- Plugin: `/python/user/global/plugin/` — 插件系统

---

## 🧠 Bug 学习系统（防智障机制）

### 核心规则
- 🔴 每个错误必须记录 — 失败时自动调用 `brain.bug_memory.record_bug()`
- 🔴 每个任务前必须召回 — `brain.pre_task()` 自动搜索历史相关 bug
- 🔴 复发 3 次自动标记为反模式 — 永久警告所有 Agent
- 🔴 错误分类自动识别 — import / syntax / logic / permission / network / encoding

### 使用方式
```python
# 任务前 — 自动注入历史教训
pre = brain.pre_task("修改 shared_context.py", expected_files=["core/shared_context.py"])
if pre["bug_warnings"]:
    for w in pre["bug_warnings"]:
        print(f"[!] {w}")

# 任务后 — 失败自动记录
brain.post_task(success=False, result=str(error), instruction="修改 shared_context.py")
```

---

## 🎯 工作原则

1. **自动工作** — 不需要用户手动启动 MCP 服务器
2. **智能理解** — 自动理解用户需求，不依赖明确指令
3. **能力优先** — 优先使用已有的 Skill/MCP/CLL/Plugin
4. **不重复造轮子** — 先搜索现有实现
5. **保持简洁** — 避免无意义回复和技术术语堆砌

---

## 🛡️ 保护规则

- 架构文件修改前必须备份
- MCP 文件必须按分类存放 (JM/BC/Tools)
- CC 缓存文件定期清理
- 以上规则继承自 `/python/ai-plugin/rules/security.md`

---

## 📁 目录参考

| 层 | 路径 | 说明 |
|----|------|------|
| 用户层 | `/python/user/` | 配置、插件、技能、对话历史 |
| 存储层 | `/python/storage/` | Brain、MCP、CLL、CC |
| 核心层 | `/python/core/` | dispatch、pipeline、shared_context |
| 适配层 | `/python/adapter/` | 外部工具集成 |
| 能力包 | `/python/ai-plugin/` | 集中化 AI 行为管理 |
