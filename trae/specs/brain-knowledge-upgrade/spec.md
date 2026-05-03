# Brain 知识库全面升级 Spec

## Why
当前 Brain 知识库系统存在三大问题：(1) topics/ 目录有 200+ 个 `stepfun_*.json` 扁平文件，无分类、无索引、无语义搜索，查找效率极低；(2) Qoder 对话记录（4个 Quest 会话、16个子代理日志）和 TRAE 对话记录完全未导入知识库，大量有价值的任务上下文和代码修改历史被浪费；(3) knowledge_base 5 个分类目录中只有 2 个条目，知识库几乎为空，而 topics/ 有 200+ 条未结构化知识，需要迁移和整合。

## What Changes
- 新增 `Brain/topics/` 分类子目录结构，按领域/项目分类存储话题文件，替代当前扁平结构
- 新增 `Brain/importers/` 导入器模块：Qoder 对话导入器、TRAE 对话导入器、通用 JSONL 导入器
- 新增 `Brain/search/` 语义搜索引擎：基于 TF-IDF + 关键词的混合搜索，支持跨分类检索
- 新增 `Brain/indexer/` 自动索引器：扫描所有知识文件，生成倒排索引和标签索引
- 重构 `Brain/topics/_index.json`：从简单列表升级为分类树 + 标签云 + 统计信息
- 迁移现有 200+ `stepfun_*.json` 到分类子目录
- 新增 `Brain/tools/` CLI 工具集：知识查询、导入、统计、清理
- 新增 `Brain/integration/` 对接层：与 core/ai_adapter.py、core/knowledge_manager.py 集成

## Impact
- Affected specs: ai-platform-restructure (Brain 模块升级)
- Affected code: `storage/Brain/` 全目录、`core/knowledge_manager.py`、`core/ai_adapter.py`、`core/ai_new.py`
- Affected config: `storage/Brain/memory/config.json`、`ai_architecture.json`

## ADDED Requirements

### Requirement: 话题分类存储
系统 SHALL 将 `topics/` 目录从扁平结构升级为分类子目录结构：

```
topics/
├── _index.json           # 分类树 + 标签云 + 统计
├── ai_models/            # AI 模型相关话题
├── mcp_servers/          # MCP 服务器开发话题
├── game_dev/             # 游戏开发话题
├── system_ops/           # 系统运维话题
├── project_mgmt/         # 项目管理话题
├── coding_patterns/      # 代码模式话题
├── troubleshooting/      # 故障排查话题
└── uncategorized/        # 未分类话题（默认）
```

#### Scenario: 迁移现有话题
- **WHEN** 系统检测到 `topics/` 下有扁平的 `stepfun_*.json` 文件
- **THEN** 自动按话题内容中的 tags 字段分类到对应子目录
- **AND** 更新 `_index.json` 的分类映射

### Requirement: Qoder 对话导入器
系统 SHALL 提供 Qoder Quest 会话导入功能，将 Qoder 的 `.jsonl` 对话日志解析并导入知识库：

#### Scenario: 导入 Quest 会话
- **WHEN** 用户指定 Qoder 数据目录 `C:\Users\888\AppData\Roaming\Qoder\SharedClientCache\cli\projects\`
- **THEN** 系统扫描所有 `.session.execution.jsonl` 文件
- **AND** 提取用户消息、AI 回复、工具调用、文件修改记录
- **AND** 生成结构化知识条目存入 `knowledge/project_context/` 和 `knowledge/domain_knowledge/`
- **AND** 提取 Todo 列表和任务完成状态存入 `sessions/`

#### Scenario: 导入子代理日志
- **WHEN** Quest 会话目录下存在 `subagents/` 子目录
- **THEN** 解析每个 `agent-*.jsonl` 文件
- **AND** 提取子代理的任务描述、执行结果、发现的模式

### Requirement: TRAE 对话导入器
系统 SHALL 提供 TRAE IDE 对话记录导入功能：

#### Scenario: 导入 TRAE state.vscdb
- **WHEN** 用户指定 TRAE 数据目录
- **THEN** 从 `state.vscdb` SQLite 数据库提取聊天历史
- **AND** 解析键值对中的对话内容
- **AND** 导入为知识条目

### Requirement: 混合搜索引擎
系统 SHALL 提供跨分类的混合搜索能力：

#### Scenario: 关键词搜索
- **WHEN** 用户输入搜索关键词
- **THEN** 同时搜索 topics/、knowledge/、sessions/、patterns/ 四个数据源
- **AND** 按 TF-IDF 相关性 + importance 权重排序
- **AND** 返回合并后的结果列表

#### Scenario: 标签搜索
- **WHEN** 用户指定标签过滤条件
- **THEN** 从 `_index.json` 的标签索引中查找匹配条目
- **AND** 返回该标签下所有话题条目

### Requirement: 自动索引器
系统 SHALL 在每次知识写入后自动更新索引：

#### Scenario: 增量索引更新
- **WHEN** 新知识条目被保存到任意分类目录
- **THEN** 自动更新 `_index.json` 中的条目引用
- **AND** 更新标签云统计
- **AND** 更新分类计数

### Requirement: CLI 工具集
系统 SHALL 提供命令行工具管理知识库：

#### Scenario: 知识查询
- **WHEN** 运行 `python -m storage.Brain.tools query "MCP开发"`
- **THEN** 返回所有相关话题、知识条目、会话摘要

#### Scenario: 批量导入
- **WHEN** 运行 `python -m storage.Brain.tools import --source qoder --path <path>`
- **THEN** 执行导入并报告导入统计

#### Scenario: 知识统计
- **WHEN** 运行 `python -m storage.Brain.tools stats`
- **THEN** 输出各分类条目数、标签分布、存储大小、最近更新

### Requirement: AI 适配器集成
系统 SHALL 将 Brain 知识库与 AI 对话流程集成：

#### Scenario: 自动上下文注入
- **WHEN** 用户通过 `core/ai_new.py` 发起 AI 对话
- **THEN** 自动调用 `recall.py` 检测是否需要记忆召回
- **AND** 将召回结果注入对话上下文

## MODIFIED Requirements

### Requirement: Brain Memory Engine
原 `MemoryEngine` 类增加以下方法：
- `migrate_topics()`: 将扁平话题文件迁移到分类子目录
- `import_from_qoder(path)`: 从 Qoder 数据目录导入对话
- `import_from_trae(path)`: 从 TRAE 数据目录导入对话
- `search_all(keyword)`: 跨所有数据源的混合搜索
- `rebuild_index()`: 重建完整索引

### Requirement: Knowledge Manager
原 `KnowledgeSystem` 类增加以下方法：
- `sync_with_brain()`: 将 knowledge_manager 的知识与 Brain 同步
- `import_conversation(source, data)`: 从外部源导入对话数据

## REMOVED Requirements

### Requirement: 50MB 总大小限制
**Reason**: 知识库数据量增长需要更大存储空间，50MB 限制过于严格
**Migration**: 提升到 500MB，并增加按分类的大小配额管理
