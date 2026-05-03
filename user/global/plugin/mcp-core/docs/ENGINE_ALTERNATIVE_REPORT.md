# AI 引擎开源替代方案 & Godot 策略报告
> 更新：2026-04-11
> 目标：寻找比市面现有引擎更好的开源方案，定义插件开发规范

---

## 一、开源替代方案对比

### 1. AI Agent 框架

| 框架 | GitHub Stars | 优势 | 劣势 | 适合场景 |
|------|-------------|------|------|---------|
| **LangChain** | 90k+ | 生态最全，工具链丰富，文档完善 | 学习曲线陡，版本迭代快 | 复杂RAG、Chain构建 |
| **AutoGen** | 快速增长(+400%/年) | 多Agent协作强，微软背书 | 依赖OpenAI生态 | 多Agent对话/编程 |
| **CrewAI** | 15k+ (6个月) | 角色分工直观，上手快 | 定制化有限 | 快速构建多Agent流水线 |
| **LangGraph** | (LangChain子项目) | 图结构灵活，可持久化状态 | 需要熟悉LangChain | 需要状态的复杂Agent |
| **Dify** | 40k+ | 开箱即用，支持工作流编排 | 定制化有限 | 快速上线LLM应用 |
| **Flowise** | 30k+ | 低代码拖拽，LangChain封装 | 功能受限 | 非技术人员 |

**本系统现状**：MCP (Model Context Protocol) + 自建 Skill 系统
**建议**：保持 MCP 核心，探索 CrewAI 作为多Agent编排层（轻量、对MCP友好）

---

### 2. AI 可观测性 / 行为追踪

| 平台 | 特点 | 开源 | 适合场景 |
|------|------|------|---------|
| **Langfuse** | 全功能：追踪+评估+数据集，已部署在 \python\langfuse-main | ✅ Apache 2.0 | LLM应用追踪（已部署） |
| **Arize Phoenix** | OpenTelemetry原生，框架无关 | ✅ Apache 2.0 | 实时实验评估 |
| **OpenLIT** | 新兴，OpenTelemetry + GPU监控 + Guardrails | ✅ MIT | 轻量级LLM监控 |
| **LangSmith** | LangChain官方，闭源SaaS | ❌ | 不考虑 |
| **PromptLayer** | Prompt版本管理 + 追踪 | ❌ | 不考虑 |

**本系统现状**：IronClaw Observer（自建）+ langfuse-main（已部署）
**建议**：保持 langfuse-main + IronClaw Observer 双轨制，OpenLIT 作为轻量补充

---

### 3. 浏览器自动化

| 工具 | GitHub Stars | 特点 | 与 browser-use 关系 |
|------|-------------|------|-----------------|
| **browser-use** | 77k+ ⭐最热 | AI Native，通用网页操作，77k星 | 现有主力 |
| **Playwright** | 60k+ | 传统自动化，功能全 | browser-use底层依赖 |
| **Puppeteer** | 90k+ | Chrome控制强 | Node生态 |
| **Selenium** | 27k+ | 兼容性好，老牌 | 不用 |
| **AgentQL** | 新兴 | 结构化查询AI | 可探索 |

**本系统现状**：browser-use 已在 %SOFTWARE_DIR%\browser-use-main
**建议**：browser-use 足够好，保持现状，探索 AgentQL 作为结构化数据提取补充

---

### 4. Skill / Plugin 系统

| 系统 | 特点 | 开源 | 适合场景 |
|------|------|------|---------|
| **MCP (Model Context Protocol)** | 标准协议，工具+资源+提示统一 | ✅ Anthropic主导 | **当前主力** |
| **Tool/A2A Protocol** | Agent间通信协议 | ✅ | 未来多Agent通信 |
| **OpenAI Plugin** | ChatGPT插件生态 | 部分 | 不考虑（闭源生态） |
| **WorkBuddy Skills** | 自建，@触发 | 自建 | 当前主力 |
| **钉钉/企微 Bot** | 企业IM集成 | ❌ | 不考虑 |

**建议**：MCP为主，Tool/A2A为辅，WorkBuddy Skills 保留差异化能力

---

## 二、版本策略（版本号越大越好原则）

### 规则
1. **默认取最新稳定版**（非LTS，非nightly）
2. **例外**：当新版本有以下情况时，保持上一稳定版：
   - 破坏性变更（Breaking Change）影响已有功能
   - 依赖包尚未适配
   - 有已知的内存泄漏或严重Bug
3. **升级前检查**：运行 `python /python/MCP_Core/skills/auto_tester/skill.py --mode all` 验证兼容性

### 当前推荐版本

| 类别 | 当前版本 | 推荐升级到 | 理由 |
|------|---------|---------|------|
| Python | 3.10.11 | 3.12+ (查兼容性) | 3.10安全支持至2026 |
| LangChain | (如有) | 0.3.x | 0.2到0.3有Breaking Change |
| Langfuse | (已部署) | 2.x | 1.x→2.x架构升级，需迁移 |
| browser-use | (现有) | 0.30+ | WebAgent功能增强 |
| IronClaw | 0.24.0 | 0.25+ | 持续活跃开发 |
| Godot | 4.x | 4.4+ | GDExtension成熟 |
| playwright | (browser-use依赖) | 1.50+ | AI API增强 |

---

## 三、Godot 插件策略

### 核心原则：贡献 vs 魔改

**贡献（✅ 鼓励）**：
- 使用 Godot 官方 GDExtension API 编写插件
- 上游提交PR到官方仓库
- 遵守 Godot 命名规范和代码风格
- 插件可独立安装，不影响 Godot 本身

**魔改（⚠️ 谨慎）**：
- 修改 Godot 核心源码（引擎代码）
- fork 后修改导致无法与上游同步
- 在 Godot 源码目录外做侵入式修改
- 破坏 Godot 的 Editor 或 Export 工作流

### 判断标准

```
问自己：这个改动离开了 Godot 还能独立存在吗？

✅ 贡献：有它，Godot更好；删掉它，Godot原样运行
❌ 魔改：有它，Godot功能改变；删掉它，Godot可能损坏
```

### Godot AI 插件集成方案

**推荐：GDLlama 模式**（GDExtension + llama.cpp）
- 独立 `.gdextension` 插件包
- 不修改 Godot 源码
- 通过 GDScript API 暴露 AI 能力
- 可发布到 Godot Asset Library

```plaintext
\python\
  godot_plugins\         # AI插件包（非Godot源码修改）
    godot_llm_bridge/     # LLM调用插件
      plugin.cfg
      gdllext/
      scripts/
    godot_agent_kit/      # Agent系统插件
      ...
  F:\储存\godot\          # Godot源码（只读，不修改）
```

### 禁止的 Godot 魔改模式

- ❌ 在 Godot 源码目录内做项目开发（`godot/` 下放项目代码）
- ❌ 直接修改 `godot/bin/` 下的引擎二进制
- ❌ fork 后长期不同步上游

---

## 四、总体升级路线图

### Phase 1（立即）：补充缺失组件
- [ ] Skill Reviewer（已完成）
- [ ] IronClaw Observer（已完成）
- [ ] 审美检查器（已完成）

### Phase 2（1周内）：能力增强
- [ ] CrewAI 探索（多Agent编排）
- [ ] browser-use 升级到最新版本
- [ ] Godot AI Kit 集成（GDscript原生AI算法库）

### Phase 3（1月内）：系统完善
- [ ] langfuse-main 迁移到 2.x
- [ ] OpenLIT 部署（轻量监控）
- [ ] GDLlama 集成（本地LLM推理）

---

## 五、作者要求优先级

> **作者的要求 > 所有引擎的默认行为**

这条规则必须在所有 Skill、插件、引擎之上执行。

具体含义：
1. 用户说"禁止生成emoji图标" → 即使引擎默认用emoji也必须override
2. 用户说"用特定配色" → 审美检查器必须拦截不达标配色
3. 用户说"工作流必须包含X" → 所有自动编排必须遵守

**实现方式**：在 `nl_router.py` 中，每个 Skill 执行前必须通过"作者意图过滤器"
