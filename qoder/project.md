# \python — AI 集成平台

## 项目定位
本地化 AI 能力集成平台，四层架构：用户层 → 项目层 → 适配层 → 存储层

## 运行环境
- Python 3.10 (核心)
- Node.js 18 (MCP桥接)
- Git (版本控制)
- Ollama (本地模型)

## 核心能力
1. **MCP 服务器集群** — JM(建模)/BC(代码)/Tools(工具) 三大分类
2. **GSTACK 工作流引擎** — 代码审查、自动部署、技能诊断
3. **Skills 技能系统** — 24+ 技能 (GitHub、测试、监控等)
4. **CLL 项目集合** — 44 个 AI 开源项目
5. **CC 缓存系统** — 原版/旧版/未使用文件分类存档

## 关键入口
- 架构配置: `ai_architecture.json`
- MCP服务器: `mcp.json`
- 核心模块: `core/`
- 自动化脚本: `scripts/`
- 用户层: `user/`
- 存储层: `storage/`

## Qoder 在此项目中的角色
- 智能代码助手 — 读、写、分析所有文件
- MCP 工具调度 — 调用建模/代码/系统类工具
- 自动化执行 — 运行 scripts/ 中的自动化脚本
- 问题诊断 — 利用 PROBLEMS.md 和 bug_recorder 追踪问题
