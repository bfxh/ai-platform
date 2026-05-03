# AI Platform - AGENTS.md

## 项目概述
本地化 AI 能力集成平台，四层架构：用户层、项目层、适配层、存储层

## 项目目录结构（2026-04-26 整理后）

```
\python\
├── core/                  # AI 核心模块（dispatcher, workflow, mcp）
├── adapter/               # 平台适配层
├── storage/               # 存储层
│   ├── mcp/JM/           # 建模类 MCP (Blender, UE, Unity, Godot)
│   ├── mcp/BC/           # 代码类 MCP (GitHub, Search, Fix)
│   ├── mcp/Tools/        # 工具类 MCP (Download, Monitor, Config)
│   ├── cll/              # 44个 CLL 开源项目
│   ├── CC/               # 分类缓存 (1_Raw/2_Old/3_Unused)
│   ├── models/           # 模型信息与AI工具对比数据
│   └── Brain/            # AI 记忆系统
├── user/                  # 用户层 (config, plugins, skills, tasks)
│   ├── global/           # 全局能力（plugin/skill/prompt）
│   ├── knowledge/        # 复利知识系统（raw/knowledge/outputs/inspection）
│   └── context.json      # 上下文管理数据
├── projects/              # 项目层（minecraft/game_test/_template）
├── scripts/               # 自动化脚本
│   ├── build/            # 构建脚本
│   ├── launch/           # 启动脚本
│   ├── check/            # 检查/验证脚本
│   ├── fix/              # 修复脚本
│   ├── download/         # 下载脚本
│   ├── test/             # 测试脚本
│   ├── mod/              # Mod 管理
│   ├── powershell/       # PowerShell 脚本
│   └── *.bat             # 维护脚本
├── docs/                  # 文档和截图
├── downloads/             # 下载文件
├── logs/                  # 日志
├── .trae/                 # TRAE IDE 配置和技能
├── ai-plugin/             # 集中化 AI 能力包 (plugin.yaml + rules/skills/templates/scripts)
├── AGENTS.md              # AI 操作指南（本文件）
├── PROBLEMS.md            # 已知问题记录
├── ai_architecture.json   # 架构配置 v5.0
├── index.json             # 目录索引
├── requirements.txt       # Python 依赖
└── README.md              # 项目说明
```

### 运行时环境
| 工具 | 版本 | 路径 | 角色 |
|------|------|------|------|
| TRAE | 1.107 | - | 自动化调度/IDE |
| Ollama | 0.21 | %OLLAMA_DIR%/ollama.exe | 本地模型服务 |
| Python | 3.12 | %USERPROFILE%/AppData/Local/Programs/Python/Python312/python.exe | 运行时 |
| Node.js | 18 | node | 运行时 |
| Git | 2.x | %GIT_DIR%/cmd/git.exe | 版本控制 |
| Java | 17 | java | 运行时 (Minecraft) |
| Rust | 1.70+ | cargo | 编译器 |
| PowerShell | 7 | pwsh | 脚本引擎 |
| Bun | 1.3.13 | C:\Users\888\AppData\Roaming\npm\bun.cmd | Claude Code 运行时 |
| VCPToolBox | - | \python\downloads\VCPToolBox\VCPToolBox-main | API 桥接层 |

### 常用模型
| 模型 | 提供方 | 用途 |
|------|--------|------|
| qwen2.5-coder:7b | Ollama | 代码生成 |
| deepseek-coder:6.7b | Ollama | 深度代码 |

### 端口映射
| 端口 | 服务 | 说明 |
|------|------|------|
| 11434 | Ollama | 本地模型推理 |
| 6005 | VCPToolBox API | OpenAI 兼容 API 桥接 |
| 6006 | VCPToolBox Admin | 管理面板 Web UI |
| 11436 | WS Bridge | Ollama WebSocket 桥接 |

### MCP 服务
| 服务 | 入口 | 说明 |
|------|------|------|
| agents-md-discovery | user/global/plugin/agents-md/server.mjs | 项目上下文自动发现与注入 |
| ollama-ws-bridge | user/global/plugin/ollama-bridge/bridge.mjs | 本地 AI 对话桥接 |
| mcp-core-skills | user/global/plugin/mcp-core/server.py | 核心技能服务 |
| filesystem | storage/mcp/Tools/da.py | 文件系统访问 |
| vcp-toolbox | \python\downloads\VCPToolBox\VCPToolBox-main\server.js | API 桥接层（87个插件） |

### Skill 列表
| Skill | 位置 | 说明 |
|-------|------|------|
| minecraft-skill | user/global/skill/minecraft/ | Minecraft 自动化技能包 |
| code-analyzer | user/global/skill/code-analyzer/ | 代码分析 |
| web-builder | user/global/skill/web-builder/ | Web 构建 |
| software-scanner | user/global/plugin/mcp-core/skills/software_scanner/ | 本地软件扫描 |
| auto-tester | user/global/plugin/mcp-core/skills/auto_tester/ | 自动化测试 |
| network-bypass | user/global/plugin/mcp-core/skills/network_bypass/ | 网络限制突破 |
| skill-doctor | user/global/plugin/mcp-core/skills/skill_doctor/ | 技能健康诊断 |
| wechat-remote-control | user/global/plugin/full-checker/skills/wechat-remote-control/ | 微信远程控制PC |
| obsidian-knowledge | user/global/plugin/full-checker/skills/obsidian-knowledge/ | Obsidian知识库集成 |
| multi-device-workflow | user/global/plugin/full-checker/skills/multi-device-workflow/ | 多端协同工作流 |
| self-evolving-agent | user/global/plugin/full-checker/skills/self-evolving-agent/ | 自进化Agent(技能结晶) |
| mcp-second-brain | user/global/plugin/full-checker/skills/mcp-second-brain/ | MCP第二大脑(图数据库记忆) |
| web-content-reach | user/global/plugin/full-checker/skills/web-content-reach/ | 全网内容检索(B站/小红书/GitHub) |
| local-llm-engine | user/global/plugin/full-checker/skills/local-llm-engine/ | 本地LLM引擎(Ollama/LocalAI/Jan) |
| ragflow-knowledge | user/global/plugin/full-checker/skills/ragflow-knowledge/ | RAGFlow知识库(RAG文档问答) |
| n8n-workflow | user/global/plugin/full-checker/skills/n8n-workflow/ | n8n工作流自动化(181K Stars) |
| mcp-marketplace | user/global/plugin/full-checker/skills/mcp-marketplace/ | MCP市场(68+模块/400+服务器) |

### Claude Code 土豆版集成
| 项目 | 说明 |
|------|------|
| 位置 |  |
| 运行时 | Bun 1.3.13 |
| 模型 | qwen2.5-coder:7b (通过 VCPToolBox 桥接) |
| MCP 配置 | .mcp-config.json (18个本地MCP服务) |
| 启动 | \python\scripts\launch\start_clause.bat |
| 面板 | http://127.0.0.1:6006/AdminPanel/ (admin/vcp2026) |
| 守护 | \python\scripts\launch\vcp_watchdog.py |

### Plugin 列表
| Plugin | 位置 | 说明 |
|--------|------|------|
| mcp-core | user/global/plugin/mcp-core/ | MCP 核心技能系统 |
| gstack-core | user/global/plugin/gstack-core/ | GSTACK 自动化 DevOps |
| agents-md | user/global/plugin/agents-md/ | AGENTS.md 自动发现 |
| ollama-bridge | user/global/plugin/ollama-bridge/ | Ollama WS 桥接 |
| full-checker | user/global/plugin/full-checker/ | 全项目最终检查 |

## 架构
- 用户层 (user/): personal/ + global/ + config/
- 项目层 (projects/): 各项目框架内部层
- 适配层 (adapter/): OS + 软件适配
- 存储层 (storage/): 能力描述 + 模型 + 数据

## AI 能力包 (ai-plugin) — 所有 AI 的单一配置源

`/python/ai-plugin/` 是 TRAE、Qoder 及未来所有 AI Agent 的集中化行为管理中心。
所有 AI 启动时必须按顺序加载:

```
/python/ai-plugin/
├── plugin.yaml          # 能力包元数据 + 强制规则清单
├── rules/               # 行为规则 (所有 AI 必须遵守)
│   ├── workflow.md      # 任务执行工作流
│   ├── communication.md # 沟通规范
│   ├── coding-style.md  # 代码规范
│   └── security.md      # 安全规则
├── skills/              # 可复用技能模块 (YAML frontmatter, 兼容 TuriX-CUA)
├── templates/           # 任务模板 (new-feature / bugfix)
└── scripts/install.sh   # 安装/同步脚本
```

### 强制规则 (插件级)
- 每次任务前初始化 Brain 记忆系统 + 召回 Bug 历史
- 每次任务后记录结果 + 失败自动记录 Bug
- 遵循 `ai-plugin/rules/` 下所有规则文件
- 能力单元使用顺序: Skill -> MCP -> CLL -> Workflow -> Agent -> Plugin
- 修改架构文件前必须备份

### 同步机制
- `scripts/install.sh` 将 ai-plugin 内容链接到 `.trae/` 和 `.qoder/`
- 支持 Git 版本控制: 配置 `plugin.yaml` 中的 `repository.url`
- 修改能力包后运行 `install.sh` 即可同步所有 AI 工具

---

## 测试规则

### 游戏测试（必须以玩家视角执行）
1. **启动**：识别启动方式（直接/启动器/平台/脚本），处理启动器弹窗和更新
2. **主菜单**：等待加载稳定，识别菜单类型，导航到游戏入口
3. **进入游戏**：创建/加载世界，等待加载完成（日志+HUD+画面稳定）
4. **基础操控**：WASD移动（截图对比位移）、跳跃、视角旋转、交互
5. **玩法测试**：战斗/物品/建造/任务/模组功能，每步截图验证
6. **稳定性**：持续运行+内存监控+日志错误检查
7. **退出**：保存→退出→收集日志→生成报告

详细规则：`user/global/prompt/game_test_rules.md`

### 软件测试
1. 安装/部署 → 启动 → 核心功能 → 插件/扩展 → 稳定性 → 退出
详细规则：`user/global/prompt/software_test_rules.md`

### 插件/模组测试
1. 加载验证（日志+列表）→ 功能验证（物品/生物/机制）→ 兼容性 → 配置 → 卸载
详细规则：`user/global/prompt/plugin_mod_test_rules.md`

### 测试框架
- 通用框架：`core/game_test_framework.py`（GameTestFramework 类）
- Minecraft 测试：`projects/minecraft/test_minecraft_1204.py`
- 游戏探索技能：`projects/game_test/skills/explore.py`

## 规则
- 所有能力本机执行，数据不出本机
- 默认沙盒执行
- 超时 10 分钟自动存垃圾堆
- **TRAE Pipeline v6.0 强制规则（最高优先级）**:
  所有项目在开始任何开发工作之前，必须按顺序通过 TRAE 五阶段管道：
  1. **Phase 1 - 初步分析**: 架构扫描、语言检测、依赖映射、特性识别
  2. **Phase 2 - 安全审计**: 密钥检测、不安全代码模式、依赖漏洞
  3. **Phase 3 - 逆向工程**: 许可证检测、开源验证、二进制分析
  4. **Phase 4 - 深度分析**: 交叉前三个阶段结果、风险重评
  5. **Phase 5 - 开发实施**: 仅当前四阶段通过后才可执行
  - 每阶段必须生成 Gate Report 才能进入下一阶段
  - CRITICAL 安全发现或 Proprietary 许可证自动阻塞开发阶段
  - 使用 `python core/pipeline_engine.py -p <project_path>` 启动管道
- **能力单元优先级（问题解决顺序）**:
  当无法直接完成任务时，严格按以下顺序检查本地能力:
  1. **Skill** → `/python/user/global/skill/`
  2. **MCP** → `/python/storage/mcp/` (JM → BC → Tools)
  3. **CLL** → `/python/storage/cll/`
  4. **Workflow** → workflow.yaml 定义
  5. **Agent** → agent.yaml 定义
  6. **Plugin** → `/python/user/global/plugin/`
  如以上均无法满足，再检查当前操作软件的内置扩展
- **任务委托规则（防臃肿）**:
  以下基础任务应委托给其他AI聊天窗口处理:
  - 代码审核 / 代码质量检查(lint) / 基础建模设计
  - Skill/MCP/CLL/Workflow/Agent/Plugin 整理优化
  - 文档生成
  仅保留需要本地文件访问、工具执行或平台专有知识的任务在 \python 处理
- **质量原则**: 速度可以慢，但输出质量必须达到最高标准
- **GSTACK 审计先行**: 所有操作必须先通过 GSTACK 审计再执行
- **防臃肿**: 每5个任务后自动检查冗余组件，使用 `skill_doctor` 定期诊断
- 游戏测试必须以玩家视角执行，不得仅凭文件存在判定通过
- 每个测试阶段必须截图留证
- 发现 bug 必须记录到 `PROBLEMS.md`（位于 /python/PROBLEMS.md）
- 修改任何模块前，先查阅 PROBLEMS.md 避免重复已知问题
- **TRAE 聊天规则**：每次与用户开始新会话时，必须先询问用户使用的是哪个大模型，然后调用 `core/model_info_manager.py` 获取该模型的上下文长度、能力等信息，再根据模型能力制定工作计划
- **上下文管理**：当模型上下文有限时，使用 `core/context_manager.py` 进行分析→压缩→清理，以便处理多个项目
- **AI 对比分析**：使用 `core/ai_comparison_analyzer.py` 对比所有相关 AI 框架、插件、模型，提供多维度分析报告
- **复利知识系统**：使用 `core/knowledge_manager.py` 实现 Compound Engineering 四步工作流：摄取→消化→输出→巡检
- **跨 Agent 协调（Cross-Agent Coordination）**:
  所有 AI Agent (Qoder, TRAE 等) 通过文件系统级共享上下文进行通信:
  - **启动时**：调用 `core/shared_context.py` 注册自身 (`SharedContextManager.register_agent()`)
  - **任务开始**：调用 `broadcast_context()` 告知其他 Agent 当前工作任务
  - **文件修改前**：调用 `check_file_conflicts()` 检测是否有其他 Agent 正在处理同一文件
  - **文件修改后**：调用 `log_file_operation()` 记录文件变更（其他 Agent 可通过轮询发现）
  - **学到新知识**：调用 `push_knowledge()` 推送到共享知识队列
  - **定期同步**：调用 `poll_other_agent_changes()` 获取其他 Agent 的文件变更
  - **定期维护**：调用 `maintenance()` 清理死 Agent 和过期数据
  - 所有共享数据位于 `/python/storage/shared_context/`，纯 JSON/JSONL 格式
  - 如果 `shared_context.py` 模块不可用，系统自动退回单 Agent 模式
- MIT 协议

## 总检查规则 (Full-Checker)

### 触发条件
- **项目结束时**：任何项目完成或阶段完成后必须执行总查
- **手动触发**：用户明确要求执行总查
- **CI/CD集成**：作为发布流程的最后一环

### 执行方式
```
使用 full-checker plugin 进行项目总查：
1. project-final-check: 全面检查五大项（代码质量/测试/文档/安全/依赖）
2. qa-fullstack-testing: 针对需要完整测试流程的项目
3. cypress-qa-testing: 针对 Web 应用项目的 UI 测试

检查项目类型后自动匹配对应的 skill 进行验证。
```

### 项目级配置
- 支持为不同项目设置特定检查配置
- 自动检测项目类型（NodeJS/Python/Java/Rust/Go等）
- 根据项目类型选择适当的检查策略
