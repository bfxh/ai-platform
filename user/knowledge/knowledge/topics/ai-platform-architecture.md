---
title: \python 本地化 AI 能力集成平台架构分析
date: 2026-04-29
source: 代码分析
tags: [architecture, ai-platform, dispatcher, pipeline, mcp, knowledge-system]
---

# \python 本地化 AI 能力集成平台 — 完整架构

## 一、项目概述

本地化 AI 能力集成平台，核心理念：**所有能力本机执行，数据不出本机**。四层架构：用户层、项目层、适配层、存储层。

## 二、四层架构

```
用户层 (user/)     → 声明+配置+交互入口
项目层 (projects/) → 各项目框架内部层
适配层 (adapter/)  → OS差异适配 + 软件路径发现 + 10个AI提供商统一接入
存储层 (storage/)  → 能力实现+模型数据+跨Agent共享+分类缓存
```

核心层 `core/` 横跨四层，作为调度和桥接枢纽。

## 三、系统启动流程

1. TRAE IDE 打开 \python 工作区
2. 加载 .trae/config.toml（Python/Ollama/Git/Node 绝对路径）
3. 加载 .trae/project_rules.md → 指向 ai-plugin/rules/
4. 加载 .trae/user_rules.md → "自动智能工作"交互模式
5. ai-plugin 按 plugin.yaml autoload 顺序加载规则
6. Dispatcher.scan() 递归搜索7种签名文件注册能力单元
7. Ollama 本地模型服务启动（localhost:11434）
8. SharedContext 初始化（storage/shared_context/）

## 四、核心模块（core/ 23个文件）

### 4.1 入口与调度

| 模块 | 核心类/函数 | 职责 |
|------|------------|------|
| ai.py | AI类 + ask/write_code等快捷函数 | 统一入口，新旧接口兼容 |
| dispatcher.py | Dispatcher + SandboxManager | 能力单元扫描/注册/调度，7种签名文件 |
| router.py | SmartRouter + do/code/review | 本地/云端智能路由，SIMPLE→Ollama, COMPLEX→云端 |

### 4.2 工作流与管道

| 模块 | 核心类/函数 | 职责 |
|------|------------|------|
| workflow.py | WorkflowEngine + wf.go() | 极简工作流，一句话定义并执行 |
| workflow_engine.py | run_workflow() | YAML工作流引擎，按节点图执行skill/mcp/cli |
| pipeline_engine.py | Pipeline + Phase + GateReport | 五阶段强制管道（分析→安全→逆向→深度→开发） |

### 4.3 AI适配与Agent

| 模块 | 核心类/函数 | 职责 |
|------|------------|------|
| ai_adapter.py | UnifiedAI + AIClientFactory + 10个Client | 10个AI提供商统一接口（策略+工厂+门面模式） |
| ai_agent.py | Agent + ToolRegistry + Subagent | Agent Loop（调用AI→解析工具→执行→循环） |
| ai_config.py | AIConfig + get_config() | 4级优先级配置：运行时>环境变量>配置文件>默认值 |

### 4.4 上下文与协调

| 模块 | 核心类/函数 | 职责 |
|------|------------|------|
| context_manager.py | ContextManager | 分析→压缩→清理三步工作流 |
| shared_context.py | SharedContextManager + 6个子模块 | 跨Agent文件系统级协调 |
| knowledge_manager.py | KnowledgeSystem | 摄取→消化→输出→巡检四步工作流 |
| model_info_manager.py | ModelInfoManager | 12个预设模型信息管理 |

### 4.5 工具与安全

| 模块 | 核心类/函数 | 职责 |
|------|------------|------|
| mcp_lite.py | MCPLite + 6个工具 | 轻量MCP（file/code/search/browser/db/design） |
| mcp_extended.py | MCPExtended + 5个工具集 | 增强MCP（File/Code/Data/Network/System） |
| sandbox.py | SandboxManager + DeleteInterceptor | 沙盒隔离+删除拦截+超时监控 |
| optimizer.py | TokenOptimizer | 5步优化流水线，减少50%+ token |

## 五、能力单元优先级

```
Skill → MCP → CLL → Workflow → Agent → Plugin
```

Dispatcher 严格按此顺序查找能力单元。

## 六、MCP 服务体系

mcp-config.json 定义 38 个 MCP 服务：
- JM (建模): 8个 — blender_mcp, ue_mcp, unity_mcp, godot_mcp 等
- BC (代码): 12个 — code_quality, github_dl, dev_mgr 等
- Tools (工具): 13个 — screen_eye, net_pro, aria2_mcp 等
- Skills: 10个 — system_optimizer, auto_tester, skill_doctor 等

## 七、ai-plugin 能力包系统

单一配置源（/python/ai-plugin/），所有 AI Agent 的行为管理中心：
- plugin.yaml: 元数据 + 强制规则清单 + 集成对接
- rules/: workflow.md(最高优先级), coding-style.md, security.md
- skills/: code-review.md, architecture-design.md
- templates/: bugfix.md, new-feature.md
- scripts/install.sh: 同步到 .trae/ 和 .qoder/

核心设计：修改一处，install.sh 分发到所有 AI 工具。

## 八、规范体系（7种能力单元）

```
Plugin ─┬─ includes → Skill (最小可执行单元)
        ├─ includes → MCP (外部协议服务)
        ├─ includes → CLI (命令行工具)
        ├─ includes → Workflow (DAG编排)
        ├─ includes → Agent (自主决策循环)
        ├─ includes → Model (本地模型描述)
        └─ dependencies → Plugin
```

## 九、关键发现

| 问题 | 严重度 |
|------|--------|
| GSTACK 空壳化（仅90行路由壳） | 高 |
| Python 版本不一致（config.toml=312, scanner=310） | 中 |
| scanner.py 环境变量未展开 | 中 |
| 索引与实际不一致 | 中 |
| MCP 配置路径混用 | 中 |
| 插件注册表扁平化（77个全部priority:0） | 低 |
