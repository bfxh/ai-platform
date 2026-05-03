# AI 集成平台 (AI Integration Platform)

高度模块化、可扩展的人工智能集成平台。统一多 AI 提供商接口，内置 MCP (Model Context Protocol) 工具系统、7 种能力单元体系、游戏测试框架，支持本地+云端混合 AI 架构。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

---

## 项目简介

AI 集成平台是一个生产级 AI 开发与自动化系统，核心定位是**统一多 AI 提供商的中枢调度层**，向上承接 IDE / CLI / Agent 等交互界面，向下兼容 OpenAI、Anthropic、Google Gemini、Ollama 本地模型、DeepSeek、通义千问等主流 AI 服务。

平台采用 **GSTACK 优先** 的执行策略，所有工作流在进入 AI 引擎前先经过 GSTACK 工作流引擎进行编排审计，确保操作可追踪、可回滚。




### 核心能力

| 能力 | 说明 |
|------|------|
| **多 AI 提供商** | 统一接口访问 stepfun / openai / anthropic / gemini / ollama / deepseek / qwen / doubao |
| **MCP 工具系统** | 108 个 MCP 工具 (建模类 JM / 代码类 BC / 工具类 Tools) |
| **7 种能力单元** | Skill、Plugin、Workflow、Agent、MCP、CLI、Model — 从原子脚本到自主 Agent 全覆盖 |
| **游戏测试框架** | 以玩家身份执行 Minecraft / Terraria 自动化测试，每阶段截图留证 |
| **AI 记忆系统** | 话题追踪、思维记录、提示优化、学习成长 (Compound Engineering) |
| **本地+云端混合** | 通过 Ollama 运行本地模型，结合云端 API 弹性扩展 |
| **三区隔离** | personal/ (私密) + runtime/ (临时) + global/ (共享) 三区环境隔离 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                   用户层 (user/)                     │
│  personal/  个人配置·密钥·笔记·任务                    │
│  global/    共享插件·技能·工作流·提示·RAG              │
│  config/    本地配置                                   │
├─────────────────────────────────────────────────────┤
│                   项目层 (projects/)                  │
│  minecraft/ · game_test/ · test/                      │
│  各项目独立的 MCP/CLI/Skill/Workflow 配置              │
├─────────────────────────────────────────────────────┤
│                   适配层 (adapter/)                    │
│  ai/        AI 提供商适配 (stepfun/openai/...)        │
│  os/        操作系统路径映射                           │
│  software/  本地软件扫描                               │
├─────────────────────────────────────────────────────┤
│                   存储层 (storage/)                    │
│  mcp/       MCP 工具仓库 (JM·BC·Tools)                │
│  cll/       CLL 开源 LLM 项目追踪 (44 项目)            │
│  CC/        分类缓存 (Raw·Old·Unused)                  │
│  Brain/     AI 记忆系统                                │
│  plugins/·skills/·workflows/·agents/                  │
├─────────────────────────────────────────────────────┤
│                横向贯穿层                              │
│  core/         AI 引擎 (调度·工作流·插件·上下文)        │
│  gstack_core/  GSTACK 工作流引擎                       │
│  scripts/      自动化脚本 (构建·启动·检查·修复)         │
│  specifications/  能力单元规范定义                      │
└─────────────────────────────────────────────────────┘
```

---

## 目录结构

```
\python\
├── core/                          # AI 核心引擎 (40+ Python 模块)
│   ├── ai_new.py                  # 统一 AI 入口 (AI 类)
│   ├── ai_adapter.py              # 多提供商适配器
│   ├── dispatcher.py              # 能力单元调度器 (沙箱执行)
│   ├── workflow_engine.py         # DAG 工作流执行引擎
│   ├── context_manager.py         # 上下文与 Token 管理
│   ├── knowledge_manager.py       # 知识系统 (Compound Engineering)
│   ├── game_test_framework.py     # 游戏测试框架
│   ├── model_info_manager.py      # LLM 模型能力追踪
│   └── plugin_system/             # 插件架构
│
├── adapter/                       # 平台适配层
│   ├── ai/                        # AI 提供商 SDK 封装
│   ├── os/                        # 操作路径映射
│   └── software/                  # 本地软件扫描
│
├── storage/                       # 存储层
│   ├── mcp/                       # MCP 工具仓库
│   │   ├── JM/                    # 建模类 (Blender/UE/Unity/Godot)
│   │   ├── BC/                    # 代码类 (GitHub/Search/Fix)
│   │   └── Tools/                 # 工具类 (Download/Monitor/Config)
│   ├── cll/                       # CLL 开源 LLM 项目 (44 项目)
│   ├── CC/                        # 分类缓存 (1_Raw/2_Old/3_Unused)
│   ├── Brain/                     # AI 记忆系统
│   ├── skills/·plugins/·workflows/·agents/
│   └── README.md
│
├── user/                          # 用户层 (三区隔离)
│   ├── personal/                  # 私密区 — 密钥·笔记·任务 (不入库)
│   ├── runtime/                   # 临时区 — 运行时文件 (不入库)
│   └── global/                    # 共享区 — 插件·技能·提示·RAG
│
├── scripts/                       # 自动化脚本 (34 个)
│   ├── build/                     # 构建脚本
│   ├── launch/                    # 启动脚本
│   ├── check/                     # 检查/验证脚本
│   ├── fix/                       # 修复脚本
│   ├── download/                  # 下载脚本
│   └── test/                      # 测试脚本
│
├── gstack_core/                   # GSTACK 工作流引擎
│   └── gstack_core.py             # 主入口
│
├── specifications/                # 7 种能力单元规范定义
│   ├── skill.yaml / mcp.json / cli.yaml
│   ├── workflow.yaml / agent.yaml / plugin.toml / model.yaml
│   └── README.md
│
├── mcp-servers/                   # MCP 服务器实现
│   ├── agents-md-discovery/       # 项目上下文自动发现 (Node.js)
│   └── ollama-ws-bridge/          # Ollama WebSocket 桥接 (Node.js)
│
├── projects/                      # 项目配置
│   ├── minecraft/                 # Minecraft 测试
│   └── game_test/                 # 游戏测试框架
│
├── MCP/                           # 架构映射 → storage/mcp/
├── MCP_Core/                      # 架构映射 → core/
├── CC/                            # 架构映射 → storage/CC/
├── CLL_Projects/                  # 架构映射 → storage/cll/
│
├── docs/                          # 文档与截图
├── .trae/                         # TRAE IDE 配置与技能
├── .qoder/                        # Qoder AI 集成配置
├── .github/                       # GitHub CI/CD 工作流
├── ai_architecture.json           # 架构配置 v5.0
├── mcp.json                       # MCP 服务器注册表
├── requirements.txt               # Python 依赖 (300+)
├── AGENTS.md                      # AI 操作指南
├── README.md                      # 本文件
└── LICENSE                        # MIT License
```

---

## 支持的 AI 提供商

| 提供商 | 标识符 | 说明 | 环境变量 |
|--------|--------|------|----------|
| 阶跃AI | `stepfun` | 默认提供商 | `STEPFUN_API_KEY` |
| OpenAI | `openai` | GPT 系列 | `OPENAI_API_KEY` |
| Anthropic | `claude` | Claude 系列 | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini` | Gemini 系列 | `GEMINI_API_KEY` |
| Ollama | `ollama` | 本地模型运行 | 无需 (本地服务) |
| DeepSeek | `deepseek` | DeepSeek 系列 | `DEEPSEEK_API_KEY` |
| 通义千问 | `qwen` | 阿里云 Qwen 系列 | `QWEN_API_KEY` |
| 豆包 | `doubao` | 字节跳动豆包 | `DOUBAO_API_KEY` |

默认提供商可通过环境变量 `AI_PROVIDER` 更改，或代码中指定 `AI(provider="openai")`。

---

## 快速开始

### 1. 环境要求

| 工具 | 最低版本 | 用途 |
|------|---------|------|
| Python | 3.10+ | AI 引擎运行 |
| Node.js | 18+ | MCP 服务器 |
| Git | 2.x+ | 版本控制 |
| Ollama | 0.21+ | 本地模型 (可选) |

### 2. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/bfxh/ai-platform.git \python
cd \python

# 安装 Python 依赖
pip install -r requirements.txt

# (可选) 安装 MCP 服务器依赖
cd user/global/plugin/agents-md && npm install
cd user/global/plugin/ollama-bridge && npm install
```

### 3. 配置环境变量

```powershell
# PowerShell
$env:STEPFUN_API_KEY = "your_stepfun_api_key"
$env:OPENAI_API_KEY = "your_openai_api_key"
# ... 按需配置其他提供商

# 或设置默认提供商
$env:AI_PROVIDER = "stepfun"
```

### 4. 基础使用

```python
from core.ai_new import AI, ask, chat, write_code

# 方式一：创建 AI 实例
ai = AI()                          # 默认提供商 (stepfun)
ai = AI(provider="openai")         # 指定 OpenAI
ai = AI(provider="claude", model="claude-3-opus")

result = ai("你好，介绍一下自己")    # 极简调用
result = ai.ask("什么是人工智能?")   # 提问 (不保持历史)
result = ai.chat("你好")            # 聊天 (保持历史)
code = ai.write_code("写快速排序")   # 代码生成
review = ai.review_code(code)       # 代码审查
fixed = ai.fix(code)                # 代码修复
ai.switch_provider("gemini")        # 运行时切换提供商

# 方式二：快捷函数
result = ask("什么是机器学习?", provider="stepfun")
code = write_code("写二分查找算法")
```

---

## 能力单元系统

平台定义了 **7 种能力单元**，从原子操作到自主 Agent 逐层组合：

| 形态 | 定义文件 | 格式 | 用途 |
|------|---------|------|------|
| **Skill** | `skill.yaml` | YAML | 最小可执行单元，封装脚本逻辑 |
| **MCP** | `mcp.json` | JSON | 外部协议服务，与 TRAE 兼容 |
| **CLI** | `cli.yaml` | YAML | 命令行工具封装 |
| **Workflow** | `workflow.yaml` | YAML | DAG 编排，串联多个能力单元 |
| **Agent** | `agent.yaml` | YAML | 自主决策循环，可调用工具 |
| **Plugin** | `plugin.toml` | TOML | 打包发布单元，组合多种能力 |
| **Model** | `model.yaml` | YAML | 本地模型文件描述 |

### 组合关系

```
Plugin ─┬─ includes ── Skill
        ├─ includes ── MCP
        ├─ includes ── CLI
        ├─ includes ── Workflow ── nodes ── Skill/MCP/CLI/Agent
        ├─ includes ── Agent ── tools ── Skill/MCP/CLI
        └─ dependencies ── Plugin
```

详细规范参见 [specifications/README.md](specifications/README.md)。

### 内置 Plugin

| Plugin | 位置 | 说明 |
|--------|------|------|
| mcp-core | `user/global/plugin/mcp-core/` | MCP 核心技能系统 |
| gstack-core | `user/global/plugin/gstack-core/` | GSTACK 自动化 DevOps |
| agents-md | `user/global/plugin/agents-md/` | AGENTS.md 自动发现注入 |
| ollama-bridge | `user/global/plugin/ollama-bridge/` | Ollama WebSocket 桥接 |
| full-checker | `user/global/plugin/full-checker/` | 项目最终全面检查 |

### 内置 Skill

| Skill | 位置 | 说明 |
|-------|------|------|
| minecraft-skill | `user/global/skill/minecraft/` | Minecraft 自动化 |
| code-analyzer | `user/global/skill/code-analyzer/` | 代码分析 |
| web-builder | `user/global/skill/web-builder/` | Web 构建 |
| unified-game | `user/global/skill/unified-game/` | 统一游戏测试 |
| terraria | `user/global/skill/terraria/` | Terraria 自动化 |

---

## MCP 系统

### 已注册的 MCP 服务器

| 服务 | 入口 | 说明 |
|------|------|------|
| filesystem | `storage/mcp/Tools/da.py` | 文件系统完整访问 |
| agents-md-discovery | `user/global/plugin/agents-md/server.mjs` | 项目上下文自动发现与注入 |
| ollama-ws-bridge | `user/global/plugin/ollama-bridge/bridge.mjs` | AI 对话 WebSocket 桥接 |
| mcp-core-skills | `user/global/plugin/mcp-core/server.py` | 核心技能服务 |
| deveco-mcp | MCP 配置 | 华为 DevEco 集成 |

配置方式：

```json
// mcp.json — MCP 服务器注册表
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["storage/mcp/Tools/da.py"],
      "description": "文件系统访问"
    }
  }
}
```

---

## GSTACK 工作流引擎

GSTACK 是平台的**核心编排引擎**，所有修改类操作必须通过 GSTACK 进行审计。

### CLI 命令

```bash
python gstack_core.py status            # 系统状态查看
python gstack_core.py review <file>     # 代码审查（带自动修复）
python gstack_core.py qa                # 测试+自动修复
python gstack_core.py qa_only           # 仅报告不修复
python gstack_core.py ship              # 自动化部署
python gstack_core.py investigate       # 根因分析
python gstack_core.py plan_ceo_review   # CEO 视角评审
python gstack_core.py plan_eng_review   # 工程架构评审
python gstack_core.py skill_doctor      # Skills 自检与回滚
python gstack_core.py cc_cleanup        # CC 缓存清理扫描
python gstack_core.py office_hours      # 产品风格验证
```

---

## 测试框架

### 游戏测试流程

平台内置 `core/game_test_framework.py`，提供标准化游戏测试流程：

```
启动游戏 → 主菜单 → 进入游戏 → 基础操控 → 玩法测试 → 稳定性 → 退出
```

测试规则要求**以玩家身份执行**，不得仅凭文件存在判定通过，每个阶段必须截图留证。

### 测试工具

| 工具 | 说明 |
|------|------|
| `core/game_test_framework.py` | 通用游戏测试框架 (GameTestFramework 类) |
| `projects/minecraft/` | Minecraft 专项测试 |
| `user/global/skill/unified-game/` | 统一游戏测试技能 |
| `cypress-qa-automation/` | Web 应用 Cypress UI 自动化测试 |

---

## 开发指南

### 添加新的 AI 提供商

```python
from adapter.ai import BaseAIClient, AIClientFactory, AIProvider

class MyAIClient(BaseAIClient):
    def _get_api_key_from_env(self) -> str:
        return os.getenv("MYAI_API_KEY", "")
    
    def _get_default_base_url(self) -> str:
        return "https://api.myai.com/v1"
    
    def _get_default_model(self) -> str:
        return "myai-1.0"
    
    def chat(self, request):
        # 实现聊天逻辑
        pass

# 注册提供商
AIClientFactory.register(AIProvider("myai"), MyAIClient)
```

### 创建自定义 Skill

在 `user/global/skill/` 下创建目录，编写 `skill.yaml` 和入口脚本：

```yaml
# skill.yaml
name: my-skill
entry: skill.py
description: 我的自定义技能
timeout: 600
permissions:
  network: true
  filesystem: ["./"]
tags: [custom]
```

### 创建自定义 Plugin

```toml
# plugin.toml
name = "my-plugin"
version = "1.0.0"
description = "我的自定义插件"

[includes]
skills = ["my-skill"]
mcps = ["my-mcp"]

[dependencies]
plugins = ["mcp-core"]
```

---

## 运行环境

| 工具 | 版本 | 路径 | 角色 |
|------|------|------|------|
| TRAE | 1.107 | - | 自动化 IDE |
| Ollama | 0.21 | `%OLLAMA_DIR%/ollama.exe` | 本地模型服务 |
| Python | 3.10 | `%USERPROFILE%/.../Python310/python.exe` | 运行时 |
| Node.js | 18 | `node` | 运行时 |
| Git | 2.x | `%GIT_DIR%/cmd/git.exe` | 版本控制 |
| Java | 17 | `java` | 运行时 (Minecraft) |
| Rust | 1.70+ | `cargo` | 编译 |
| PowerShell | 7 | `pwsh` | 脚本引擎 |

---

## 设计原则

- **数据本地化**：所有能力本机执行，数据不出设备
- **沙盒优先**：默认沙盒执行，超时 10 分钟自动清理
- **GSTACK 优先**：修改操作必须经 GSTACK 审计
- **三区隔离**：personal / runtime / global 严格隔离
- **游戏测试真实性**：必须实际运行游戏，不能仅凭文件判定
- **截图留证**：每个测试阶段截图保存
- **Bug 追踪**：发现问题记录到 `PROBLEMS.md`

---

## 贡献指南

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

本项目基于 MIT License 开源。详见 [LICENSE](LICENSE) 文件。

---

**注意**：本项目处于活跃开发阶段，接口可能发生变化。请参考最新文档和 `AGENTS.md`。
