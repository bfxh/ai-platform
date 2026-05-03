---
name: workflow
description: AI Agent 任务执行工作流 — 第一步不可跳过
priority: highest
version: "2.0"
---

# [!!] 任务执行工作流 — 强制流程

## 第零步 (任何任务前必做)

```
在执行任何操作之前，按顺序完成以下检查。
这一步不容跳过，跳过的后果是重复已知错误。
```

### [必须] 0.1 — 读取系统记忆

**打开并完整阅读 `/python/WARNINGS.md`**

这个文件包含：
- 软件的真实安装路径 (不要猜)
- 已知的环境问题
- 以前犯过的错误和修复方法
- 必须避免的反模式

如果你发现自己在猜一个路径或配置，先去 WARNINGS.md 确认。

### [必须] 0.2 — 运行环境检查

```bash
py /python/intervention/pre_session_check.py
```

这会检查所有关键路径、环境变量、基础设施是否正常。
如果报错，先修复再继续。

### [必须] 0.3 — 回忆相关历史

问自己：
- 我有没有处理过类似的任务？（查 WARNINGS.md 第3节）
- 有没有相关的反模式需要避免？（查 WARNINGS.md 第4节）
- 我要修改的文件过去出过什么问题？

---

## 第一步 — 理解任务

1. 完整阅读用户的问题
2. 不确定时先问，不要猜
3. 搜索相关代码 (`Glob`, `Grep`)，不要凭记忆猜文件路径

## 第二步 — 检查本地能力

按优先级检查：
1. **Skill** → `/python/user/global/skill/`
2. **MCP** → `/python/storage/mcp/` (JM → BC → Tools)
3. **CLL** → `/python/storage/cll/`
4. **Workflow** → `*.yaml`
5. **Agent** → `agent.yaml`
6. **Plugin** → `/python/user/global/plugin/`

## 第三步 — 执行

- 先读现有代码再改
- 修改架构文件前先备份
- 外部命令用绝对路径
- 中文输出避免 emoji

## 第四步 — 记录

任务完成后：
- 如果失败：记录到 `/python/WARNINGS.md` 第3节
- 如果成功但学到了新东西：更新 WARNINGS.md
- 告诉用户运行：`py /python/intervention/update_memory.py`

---

## 绝对禁止

- [!!] 跳过 WARNINGS.md 读取
- [!!] 凭记忆猜测软件路径
- [!!] 用系统 PATH 中的命令代替绝对路径
- [!!] 在未读代码的情况下提修改建议
- [!!] 修改架构文件不备份
