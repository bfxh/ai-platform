# Tasks

- [x] Task 1: 设计能力单元描述文件规范
  - [x] 1.1 定义 skill.yaml schema
  - [x] 1.2 定义 mcp.json schema
  - [x] 1.3 定义 cli.yaml schema
  - [x] 1.4 定义 workflow.yaml schema
  - [x] 1.5 定义 agent.yaml schema
  - [x] 1.6 定义 plugin.toml schema
  - [x] 1.7 定义 model.yaml schema
  - [x] 1.8 编写规范文档到 specifications/ 目录

- [x] Task 2: 重构目录为三层架构
  - [x] 2.1 创建 storage/ 子目录
  - [x] 2.2 创建 user/ 双区
  - [x] 2.3 创建 projects/ 目录
  - [x] 2.4 迁移现有 MCP 服务到 storage/mcps/，补写 mcp.json
  - [x] 2.5 迁移现有 Skill 到 storage/skills/，补写 skill.yaml
  - [x] 2.6 迁移现有 CLI 工具到 storage/clis/，补写 cli.yaml
  - [x] 2.7 迁移 Ollama WS 桥接到 storage/plugins/ollama-bridge/，补写 plugin.toml
  - [x] 2.8 迁移 AGENTS.md MCP 到 storage/plugins/agents-md/，补写 plugin.toml
  - [x] 2.9 评估 scripts/ 下散装脚本（保留原位，新规范在 storage/ 注册）
  - [x] 2.10 更新 AGENTS.md 反映新目录结构

- [x] Task 3: 实现沙盒执行机制
  - [x] 3.1 创建 core/sandbox.py
  - [x] 3.2 实现删除拦截
  - [x] 3.3 实现超时监控
  - [x] 3.4 实现快照保存
  - [x] 3.5 快照文件名格式

- [x] Task 4: 实现 TRAE 调度中枢
  - [x] 4.1 创建 core/dispatcher.py
  - [x] 4.2 实现安装向导
  - [x] 4.3 实现连接配置
  - [x] 4.4 实现每日摘要
  - [x] 4.5 实现架构同步
  - [x] 4.6 注册为 MCP 服务

- [x] Task 5: 实现项目规范
  - [x] 5.1 创建项目模板
  - [x] 5.2 实现 Bug 自动记录
  - [x] 5.3 实现 Bug 手动提交
  - [x] 5.4 为现有项目补写规范文件

- [x] Task 6: Git 版本管理配置
  - [x] 6.1 更新 .gitignore
  - [x] 6.2 配置 Git LFS
  - [x] 6.3 实现路径存根规则
  - [x] 6.4 实现每日摘要 Git 提交

- [x] Task 7: 游戏测试 Plugin 示例
  - [x] 7.1 创建 projects/game_test/ 项目目录
  - [x] 7.2 编写 plugin.toml
  - [x] 7.3 编写 workflow.yaml
  - [x] 7.4 编写 README.md / INDEX.md / BUGS.md
  - [x] 7.5 端到端测试（Dispatcher 扫描验证）

# Task Dependencies
- Task 1 → Task 2
- Task 2 → Task 3
- Task 2 → Task 4
- Task 1 → Task 5
- Task 3 + Task 4 → Task 7
- Task 2 → Task 6
