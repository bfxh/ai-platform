# AI 架构管理器 - 自动化任务清单

## [ ] Task 1: 每日启动检查
- **触发**: 每次对话开始时
- **操作**:
  1. 调用 `mcp_trae-gstack_gstack` 检查 GSTACK
  2. 验证 ai_architecture.json 版本 (v4.2)
  3. 检查核心配置文件存在性
- **输出**: 检查报告

## [ ] Task 2: MCP 文件分类检查
- **触发**: 用户提到 MCP 或文件分类时
- **操作**:
  1. 扫描 JM/BC/Tools 目录文件数
  2. 对比 ai_architecture.json 配置
  3. 报告差异

## [ ] Task 3: CC 缓存整理
- **触发**: 用户提到整理、清理或 CC 时
- **操作**:
  1. 扫描 \python 根目录散落文件
  2. 按类型移动到 CC/1_Raw, CC/2_Old, CC/3_Unused
  3. 更新 INDEX.md

## [ ] Task 4: Skills 系统维护
- **触发**: 用户提到 Skills 或技能时
- **操作**:
  1. 检查 MCP_Core/skills 目录
  2. 验证 available_skills 列表
  3. 运行 skill_doctor 自检

## [ ] Task 5: GitHub 项目更新
- **触发**: 用户提到更新或 GitHub 时
- **操作**:
  1. 运行 daily_github_update.py
  2. 检查 44 个 CLL_Projects 更新
  3. 生成更新报告

## [ ] Task 6: 备份执行
- **触发**: 用户提到备份时
- **操作**:
  1. 运行 daily_backup.py
  2. 备份到 %BACKUP_DIR%\backup\
  3. 清理旧备份 (保留7天)

## [ ] Task 7: 配置修复
- **触发**: 发现配置问题时
- **操作**:
  1. 备份当前配置到 CC/2_Old
  2. 修复配置项
  3. 验证修复结果
