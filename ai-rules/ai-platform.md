# \python 平台开发规范

## 架构约束
- 四层架构不可越界：用户层 → 核心层 → 适配层 → 存储层
- 修改 `ai_architecture.json` 前必须先备份（加时间戳）
- 新增 MCP 必须按分类存放：JM（建模）/ BC（代码）/ Tools（工具）
- 新增能力单元需注册到 `core/dispatcher.py`

## Brain 记忆系统
- `storage/Brain/` 是跨会话记忆引擎
- 每次任务前后调用 `brain.pre_task()` / `brain.post_task()`
- 失败时自动记录到 `bug_memory`
- 任务前必须召回历史相关 bug

## TRAE Pipeline
- 所有新项目必须通过五阶段管道：分析 → 安全审计 → 逆向工程 → 深度分析 → 开发
- 使用 `core/pipeline_engine.py -p <project_path>` 启动

## 能力单元优先级
1. Skill → `user/global/skill/`
2. MCP → `storage/mcp/` (JM → BC → Tools)
3. CLL → `storage/cll/`
4. Workflow → `*.yaml`
5. Agent → `agent.yaml`
6. Plugin → `user/global/plugin/`

## 关键路径
- Git: `D:/rj/KF/Git/cmd/git.exe`
- Ollama: `D:/rj/Ollama/ollama.exe`
- Python: `C:/Users/888/AppData/Local/Programs/Python/Python312/python.exe`
- TRAE config: `/python/.trae/config.toml`
