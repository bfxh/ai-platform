# Tasks

- [ ] Task 1: 创建话题分类子目录结构并迁移 200+ 扁平文件
  - [ ] 1.1 定义分类规则（按 tags 字段自动分类：ai_models, mcp_servers, game_dev, system_ops, project_mgmt, coding_patterns, troubleshooting, uncategorized）
  - [ ] 1.2 创建 `topics/ai_models/` 等 8 个分类子目录
  - [ ] 1.3 编写迁移脚本 `storage/Brain/tools/migrate_topics.py`，读取每个 `stepfun_*.json` 的 tags，移动到对应子目录
  - [ ] 1.4 执行迁移，验证文件数一致
  - [ ] 1.5 重构 `_index.json` 为分类树 + 标签云 + 统计信息格式

- [ ] Task 2: 创建 Qoder 对话导入器
  - [ ] 2.1 编写 `storage/Brain/importers/qoder_importer.py`，解析 `.session.execution.jsonl` 格式
  - [ ] 2.2 提取用户消息、AI 回复（thinking + text + tool_use）、工具调用结果
  - [ ] 2.3 提取 Todo 列表和任务完成状态，存入 `memory/sessions/`
  - [ ] 2.4 提取代码修改记录（文件路径 + diff），存入 `knowledge/project_context/`
  - [ ] 2.5 提取领域知识（架构决策、配置方案），存入 `knowledge/domain_knowledge/`
  - [ ] 2.6 解析子代理日志 `subagents/agent-*.jsonl`
  - [ ] 2.7 执行导入：导入 4 个 Quest 会话 + 16 个子代理日志

- [ ] Task 3: 创建 TRAE 对话导入器
  - [ ] 3.1 编写 `storage/Brain/importers/trae_importer.py`，解析 TRAE 对话格式
  - [ ] 3.2 从 `state.vscdb` SQLite 提取聊天历史键值对
  - [ ] 3.3 解析对话内容并导入为知识条目

- [ ] Task 4: 创建混合搜索引擎
  - [ ] 4.1 编写 `storage/Brain/search/hybrid_search.py`，实现 TF-IDF 关键词搜索
  - [ ] 4.2 实现跨 topics/、knowledge/、sessions/、patterns/ 四源搜索
  - [ ] 4.3 实现 importance 权重 + TF-IDF 相关性混合排序
  - [ ] 4.4 实现标签过滤搜索
  - [ ] 4.5 将搜索引擎集成到 `recall.py` 的 `recall()` 方法

- [ ] Task 5: 创建自动索引器
  - [ ] 5.1 编写 `storage/Brain/indexer/auto_indexer.py`
  - [ ] 5.2 实现增量索引：知识写入后自动更新 `_index.json`
  - [ ] 5.3 实现标签云统计更新
  - [ ] 5.4 实现 `rebuild_index()` 全量重建
  - [ ] 5.5 在 `MemoryEngine.kb_save()` 和 `save_session()` 中集成索引器

- [ ] Task 6: 创建 CLI 工具集
  - [ ] 6.1 编写 `storage/Brain/tools/__main__.py`，实现 `query`、`import`、`stats`、`clean` 子命令
  - [ ] 6.2 `query` 命令：调用混合搜索引擎，格式化输出结果
  - [ ] 6.3 `import` 命令：调用导入器，支持 `--source qoder/trae/jsonl` 参数
  - [ ] 6.4 `stats` 命令：输出各分类条目数、标签分布、存储大小
  - [ ] 6.5 `clean` 命令：清理过期/低价值条目

- [ ] Task 7: 集成到 AI 适配器
  - [ ] 7.1 修改 `core/ai_new.py`，在对话发起时自动调用 `recall.py`
  - [ ] 7.2 修改 `core/knowledge_manager.py`，添加 `sync_with_brain()` 和 `import_conversation()` 方法
  - [ ] 7.3 修改 `MemoryEngine`，增加 `migrate_topics()`、`import_from_qoder()`、`import_from_trae()`、`search_all()` 方法
  - [ ] 7.4 将 50MB 大小限制提升到 500MB

# Task Dependencies
- [Task 2] depends on [Task 1] (导入器需要分类目录结构)
- [Task 4] depends on [Task 1] (搜索引擎需要分类后的数据)
- [Task 5] depends on [Task 1] (索引器需要新的目录结构)
- [Task 6] depends on [Task 2, Task 4, Task 5] (CLI 工具调用导入器和搜索引擎)
- [Task 7] depends on [Task 4, Task 5] (适配器集成需要搜索引擎和索引器)
- [Task 1] can run independently (基础结构)
- [Task 3] can run in parallel with [Task 2] (TRAE 导入器与 Qoder 导入器独立)
