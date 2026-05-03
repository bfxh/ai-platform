# 平台修复与 VCPToolBox 集成加固 Spec

## Why
本次深度分析发现 \python 平台存在 7 个已知 Bug（Python 版本不一致、scanner.py 环境变量未展开、GSTACK 空壳化、索引不同步、MCP 路径混用、health_check 导入错误、插件注册表扁平化），同时新增了 VCPToolBox + Claude Code 土豆版的桥接部署，存在进程管理脆弱、Bun 不在 PATH、管理面板双进程未文档化等问题。需要一次性修复所有已知问题并加固新部署的桥接链路。

## What Changes
- 修复 scanner.py 环境变量未展开问题（使用 os.path.expandvars）
- 统一 Python 版本引用为 3.12（与 config.toml 一致）
- 修复 health_check.bat 中 GStackCore 导入错误
- 同步 user/global/INDEX.md 与实际目录内容
- 修复 mcp-config.json 中旧路径引用（MCP_Core → storage/mcp）
- 为 .plugin_registry.json 添加优先级分类
- 创建 GSTACK 命令路由补全（从空壳升级为可执行命令）
- 创建 VCPToolBox 进程守护脚本（自动重启、健康检查）
- 将 Bun 加入系统 PATH（用户级环境变量）
- 创建一键启动脚本（start_clause.bat 已有，需加固）
- 更新 AGENTS.md 反映 VCPToolBox 桥接架构
- 更新 .trae/user_rules.md 删除保护规则（已完成，需验证）

## Impact
- Affected specs: ai-platform-restructure, gstack_integration
- Affected code:
  - adapter/software/scanner.py（环境变量修复）
  - adapter/INDEX.md（补充 ai/ 子目录）
  - scripts/health_check.bat（GStackCore 修复）
  - user/global/INDEX.md（同步索引）
  - storage/mcp/mcp-config.json（路径修复）
  - .plugin_registry.json（优先级分类）
  - gstack_core/gstack_core.py（命令路由补全）
  - AGENTS.md（更新架构说明）
- Affected config: .trae/config.toml, .env, config.env

## ADDED Requirements

### Requirement: VCPToolBox 进程守护
系统 SHALL 提供 VCPToolBox 进程守护机制，确保 API 服务（6005）和管理面板（6006）持续运行：

- 守护脚本每 30 秒检查一次端口 6005 和 6006
- 进程崩溃时自动重启（最多重试 3 次，间隔 10 秒）
- 重启失败时写入日志到 \python\logs\vcp_watchdog.log
- 守护脚本可通过 start_vcp_bridge.bat 自动启动

#### Scenario: VCPToolBox API 崩溃
- **WHEN** 端口 6005 无响应
- **THEN** 守护脚本自动重启 server.js，最多重试 3 次
- **AND** 重启成功后日志记录恢复时间

#### Scenario: VCPToolBox Admin 崩溃
- **WHEN** 端口 6006 无响应但 6005 正常
- **THEN** 仅重启 adminServer.js

#### Scenario: 连续崩溃
- **WHEN** 3 次重启均失败
- **THEN** 停止重试，写入告警日志，不弹窗打扰用户

### Requirement: Bun 环境变量持久化
系统 SHALL 将 Bun 加入用户级 PATH 环境变量，确保所有终端窗口都能直接使用 `bun` 命令：

- 路径：C:\Users\888\AppData\Roaming\npm
- 仅修改用户级 PATH（不修改系统级）
- 修改后立即生效（无需重启）

#### Scenario: 新终端窗口使用 Bun
- **WHEN** 用户打开新的 CMD/PowerShell 窗口
- **THEN** `bun --version` 能正常输出版本号

### Requirement: GSTACK 命令路由补全
GSTACK SHALL 从空壳升级为可执行命令路由，将 gstack 子命令映射到 core/ 层的实际实现：

- `gstack status` → 读取 ai_architecture.json 显示系统状态
- `gstack review` → 调用 scripts/review.py
- `gstack check` → 调用 scripts/deep_check.py
- `gstack fix` → 调用 scripts/fix/system_optimize.py
- `gstack pipeline` → 调用 core/pipeline_engine.py
- `gstack skill-doctor` → 调用 user/global/plugin/mcp-core/skills/skill_doctor/

#### Scenario: gstack review 执行
- **WHEN** 用户运行 `gstack review`
- **THEN** 实际执行 scripts/review.py 进行代码审查

#### Scenario: gstack 未知命令
- **WHEN** 用户运行 `gstack <未知命令>`
- **THEN** 显示帮助信息和可用命令列表

## MODIFIED Requirements

### Requirement: scanner.py 环境变量展开
adapter/software/scanner.py SHALL 使用 os.path.expandvars() 预处理路径中的环境变量占位符（%OLLAMA_DIR%、%USERPROFILE% 等），确保 Path.exists() 能正确检测。

原代码：
```python
SOFTWARE_CANDIDATES = {
    "ollama": ["%OLLAMA_DIR%/ollama.exe", ...],
}
```

修改后：
```python
import os
SOFTWARE_CANDIDATES = {
    "ollama": [os.path.expandvars("%OLLAMA_DIR%/ollama.exe"), ...],
}
```

### Requirement: Python 版本统一
所有配置文件和文档 SHALL 统一引用 Python 3.12（与 .trae/config.toml 一致）：

- AGENTS.md 运行时环境表：Python 3.10 → 3.12
- user/global/plugin.toml：python version = "3.10" → "3.12"
- adapter/INDEX.md：更新 Python 路径

### Requirement: 索引同步
user/global/INDEX.md SHALL 与实际目录内容同步，反映当前已有的 skill/plugin/model 条目：

当前实际内容：
- skill/: minecraft, code-analyzer, web-builder, mcp-skills
- plugin/: ollama-bridge, agents-md, mcp-core, gstack-core, full-checker
- models/: qwen2.5-coder:7b, deepseek-coder:6.7b

### Requirement: MCP 配置路径修复
storage/mcp/mcp-config.json 中 Skills 类服务的路径 SHALL 从旧路径 MCP_Core/ 更新为当前路径 storage/mcp/ 或 user/global/plugin/mcp-core/skills/。

### Requirement: health_check.bat 修复
scripts/health_check.bat 第 4 步 SHALL 修复 GStackCore 导入错误：
- 原代码：`from gstack_core import GStackCore`
- 修复为：`from gstack_core.gstack_core import cmd_status` 或直接调用 `node gstack_core/gstack_core.py status`

### Requirement: 插件注册表分类
.plugin_registry.json SHALL 为 77 个插件添加优先级分类：

| 类别 | 优先级 | 示例 |
|------|--------|------|
| 核心 | 10 | ai_toolkit, unified_workflow |
| 建模 | 5 | blender_mcp, ue_mcp, godot_mcp |
| 代码 | 5 | code_quality, github_dl |
| 工具 | 3 | desktop_automation, screen_eye |
| 游戏 | 1 | terraria_build_test |

## REMOVED Requirements
无
