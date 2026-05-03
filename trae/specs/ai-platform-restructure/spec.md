# 本地 AI 能力集成平台 Spec

## Why
\python 当前是一个松散的脚本集合，能力单元（Skill/MCP/CLI/Workflow/Agent/Plugin/模型）没有统一接入规范，缺乏沙盒保护、超时回收、项目级规范和自动化调度。需要重构为一个形态无关、完全本地、沙盒隔离的集成平台，以 TRAE 为调度中枢。

## What Changes
- **BREAKING** 重构目录为三层架构：用户层（个人数据区 + 运行保障区）、项目层、存储层，取消通用层
- 新增能力单元接入规范：7 种形态（Skill/MCP/CLI/Workflow/Agent/Plugin/模型）统一描述文件 + 标准入入口
- 新增沙盒执行机制：所有能力默认沙盒运行，禁止未授权删除，超时 10 分钟自动保存到 trash
- 新增 TRAE 调度中枢：安装向导、连接配置、每日摘要、任务监控、架构同步
- 新增项目规范：每个项目必须含 README.md / INDEX.md / BUGS.md / plugin.toml
- 新增垃圾堆机制：超时快照保存到 storage/trash/，含日志、变量摘要、文件差异
- 新增每日摘要：storage/daily/YYYY-MM-DD.json 自动生成
- Git 管理扩展：纳入 trash 快照（LFS）、每日摘要、软件路径存根；排除模型本体、密钥、缓存
- 命名规则：去掉所有"完整""统一""智能"等修饰词，名字就是名字

## Impact
- Affected specs: trae-unlimited-optimization（旧 spec，需归档）
- Affected code: \python 全目录结构、AGENTS.md、.trae/config.toml、所有 MCP/Skill 注册逻辑
- Affected config: TRAE product.json、mcp.json、resource_registry.json

## ADDED Requirements

### Requirement: 能力单元接入规范
平台 SHALL 为 7 种能力形态提供统一接入规范，每种形态必须提供描述文件和标准入口：

| 形态 | 描述文件 | 入口 |
|------|---------|------|
| Skill | skill.yaml | 入口脚本（.py/.js/.sh） |
| MCP | mcp.json | 启动命令 + 环境变量 |
| CLI | cli.yaml | 可执行路径 + 参数模板 |
| Workflow | workflow.yaml | DAG 定义文件 |
| Agent | agent.yaml | 循环 + 工具调用权限 |
| Plugin | plugin.toml | 独立目录，可内含上述形态 |
| Model | model.yaml | 路径 + 推理脚本 |

#### Scenario: 注册新 Skill
- **WHEN** 用户在 storage/skills/ 下放置 skill.yaml + 入口脚本
- **THEN** TRAE 自动扫描并注册到调度表，无需手动配置

#### Scenario: Plugin 整合多形态
- **WHEN** 一个 Plugin 目录包含 CLI 启动游戏 + Skill 执行操作 + MCP 验证状态
- **THEN** TRAE 按 plugin.toml 编排执行顺序，形成闭环

### Requirement: 三层架构
平台 SHALL 采用三层架构，取消通用层：

```
用户层 (User)
  ├── 个人数据区：项目配置、笔记、密钥（用户完全自主）
  └── 运行保障区：临时密钥、缓存、状态恢复（平台自动维护）

项目层 (Project)
  └── 每个项目的入口插件、工作流、教程、Bug 记录、索引

存储层 (Storage)
  ├── skills/ mcps/ clis/ workflows/ agents/ plugins/
  ├── daily/    每日摘要 JSON
  └── trash/    超时垃圾堆快照
```

#### Scenario: 用户数据隔离
- **WHEN** 项目 A 的运行出错
- **THEN** 不影响用户个人数据区和其他项目

#### Scenario: 运行保障区自动清理
- **WHEN** 平台检测到缓存超过阈值
- **THEN** 自动清理运行保障区，不触碰个人数据区

### Requirement: 沙盒执行机制
平台 SHALL 为所有能力执行创建沙盒环境：

- 默认禁止删除操作，除非显式授权
- 单次任务超过 10 分钟，自动挂起并保存现场到 trash/
- 快照包含：运行日志、内存变量摘要、文件系统差异清单
- 快照文件名格式：YYYY-MM-DD_HHMMSS_taskid.snapshot

#### Scenario: 任务超时
- **WHEN** 一个 Skill 执行超过 10 分钟
- **THEN** TRAE 挂起任务，打包快照到 storage/trash/，通知用户

#### Scenario: 未授权删除
- **WHEN** 自动化任务尝试删除文件但未获授权
- **THEN** 沙盒拦截操作，记录到日志，不执行删除

### Requirement: TRAE 调度中枢
TRAE SHALL 作为平台自动化中枢，提供：

1. **安装向导**：读取用户配置，初始化 Git 仓库，写入 .trae/config.toml
2. **连接配置**：扫描本地工具路径，生成相对路径映射，更新存储层描述文件
3. **每日摘要**：可视化日历视图，一键提交 storage/daily/YYYY-MM-DD.json
4. **任务监控**：为每个能力执行创建沙盒，监控耗时，超时则挂起→保存→通知
5. **架构同步**：目录结构或规范变更时，自动更新调度逻辑

#### Scenario: 每日摘要生成
- **WHEN** 每日 23:59 或用户手动触发
- **THEN** 生成 storage/daily/YYYY-MM-DD.json，包含当日执行的任务、结果、异常

#### Scenario: 架构变更同步
- **WHEN** 存储层新增一种能力形态目录
- **THEN** TRAE 自动更新扫描逻辑和调度表

### Requirement: 项目规范
每个项目 SHALL 必须包含：

| 文件 | 说明 |
|------|------|
| README.md | 教程：安装、配置、使用 |
| INDEX.md | 索引：所有 Skill/MCP/CLI/Workflow 列表与跳转 |
| BUGS.md | Bug 记录：玩家/AI 发现的 Bug 汇总 |
| plugin.toml | 插件入口描述 |

#### Scenario: Bug 自动记录
- **WHEN** AI 自动化测试遇到异常
- **THEN** 自动追加到 BUGS.md，带时间戳、日志摘要、复现步骤

#### Scenario: 玩家上报 Bug
- **WHEN** 玩家通过界面或文件提交 Bug
- **THEN** 追加到 BUGS.md，格式与 AI 自动记录一致

### Requirement: Git 版本管理
平台 SHALL 管理 Git 版本：

**纳入版本库**：插件代码、能力配置、项目教程/索引/Bug 清单、软件路径存根、每日摘要
**不纳入版本库**：模型文件、安装包、用户密钥/token、运行时缓存、大型二进制数据（用 LFS 或路径存根）
**trash 快照**：推荐 Git LFS，保留最小可诊断信息

#### Scenario: 模型文件管理
- **WHEN** 存储层引用一个本地模型
- **THEN** Git 只记录 model.yaml 中的路径，不跟踪模型本体

### Requirement: 命名规则
平台 SHALL 遵循命名规则：

- 禁止使用"完整""统一""智能""自动"等修饰词作为名称前缀/后缀
- 名字就是名字：skill 不是"智能技能"，plugin 不是"统一插件"
- 目录名、文件名、配置键名一律简洁

#### Scenario: 目录命名
- **WHEN** 创建新能力目录
- **THEN** 使用 skills/ 而非 smart_skills/，使用 trash/ 而非 auto_recovery_trash/

## MODIFIED Requirements

### Requirement: 取消通用层
原 \python 架构中存在模糊的"通用层"概念，现明确取消。原因：

1. 个人密钥/偏好被意外注入到项目逻辑中
2. 项目错误污染用户环境
3. 备份与恢复粒度变粗

改为用户层双区：个人数据区（用户完全自主）+ 运行保障区（平台自动维护），严格分离关注点。

## REMOVED Requirements

### Requirement: 旧 resource_registry.json 中心化注册
**Reason**: 改为各能力单元自带描述文件，平台自动扫描发现，无需中心化注册表
**Migration**: 现有 resource_registry.json 中的条目迁移到对应 storage/ 子目录的描述文件中

### Requirement: 旧 scripts/ 散装脚本
**Reason**: 散装脚本没有接入规范，无法被调度。统一迁移为 Skill 或 CLI 形态
**Migration**: 逐个评估 scripts/ 下的脚本，有价值的转为 Skill（加 skill.yaml），无价值的归档到 trash/
