# Tasks

- [x] Task 1: 修复 scanner.py 环境变量展开
  - [x] 1.1 在 scanner.py 顶部添加 `import os`
  - [x] 1.2 为 SOFTWARE_CANDIDATES 中所有路径添加 os.path.expandvars() 预处理
  - [x] 1.3 在 scan_installed_software() 中对路径也做 expandvars
  - [x] 1.4 验证：运行 scanner.py 确认 Ollama 路径能被正确检测

- [x] Task 2: 统一 Python 版本引用
  - [x] 2.1 修改 AGENTS.md 运行时环境表：Python 3.10 → 3.12，更新路径
  - [x] 2.2 修改 user/global/plugin.toml：python version = "3.10" → "3.12"
  - [x] 2.3 修改 adapter/INDEX.md：更新 Python 路径为 Python312
  - [x] 2.4 验证：grep 全项目确认无遗漏的 Python310 引用

- [x] Task 3: 修复 health_check.bat
  - [x] 3.1 将 `from gstack_core import GStackCore` 改为正确的导入方式
  - [x] 3.2 或改用 `python -c "from gstack_core.gstack_core import cmd_status; cmd_status()"` 调用
  - [x] 3.3 验证：运行 health_check.bat 第 4 步不报错

- [x] Task 4: 同步 user/global/INDEX.md
  - [x] 4.1 扫描 user/global/skill/ 目录实际内容
  - [x] 4.2 扫描 user/global/plugin/ 目录实际内容
  - [x] 4.3 重写 INDEX.md 反映实际条目
  - [x] 4.4 验证：INDEX.md 中每个条目对应的目录确实存在

- [x] Task 5: 修复 mcp-config.json 旧路径
  - [x] 5.1 搜索 mcp-config.json 中所有 `MCP_Core` 路径引用
  - [x] 5.2 替换为正确的当前路径（storage/mcp/ 或 user/global/plugin/mcp-core/skills/）
  - [x] 5.3 验证：替换后的路径指向实际存在的文件

- [x] Task 6: 插件注册表优先级分类
  - [x] 6.1 为 .plugin_registry.json 中 77 个插件按类别分配优先级
  - [x] 6.2 核心=10, 建模=5, 代码=5, 工具=3, 游戏=1
  - [x] 6.3 验证：JSON 格式正确，优先级字段非零

- [x] Task 7: GSTACK 命令路由补全
  - [x] 7.1 在 gstack_core.py 中添加命令到实际实现的映射
  - [x] 7.2 实现 `gstack review` → scripts/review.py
  - [x] 7.3 实现 `gstack check` → scripts/deep_check.py
  - [x] 7.4 实现 `gstack fix` → scripts/fix/system_optimize.py
  - [x] 7.5 实现 `gstack pipeline` → core/pipeline_engine.py
  - [x] 7.6 实现 `gstack skill-doctor` → skill_doctor 目录
  - [x] 7.7 未知命令显示帮助信息
  - [x] 7.8 验证：运行 `gstack status` 和 `gstack review --help` 不报错

- [x] Task 8: VCPToolBox 进程守护脚本
  - [x] 8.1 创建 scripts/launch/vcp_watchdog.py（每 30 秒检查端口 6005/6006）
  - [x] 8.2 实现自动重启逻辑（最多 3 次，间隔 10 秒）
  - [x] 8.3 实现日志写入 \python\logs\vcp_watchdog.log
  - [x] 8.4 更新 start_vcp_bridge.bat 集成守护脚本
  - [x] 8.5 验证：手动杀掉 VCPToolBox 进程后，守护脚本自动重启

- [x] Task 9: Bun 加入系统 PATH
  - [x] 9.1 创建脚本将 C:\Users\888\AppData\Roaming\npm 添加到用户级 PATH
  - [x] 9.2 使用 setx 或注册表方式持久化
  - [x] 9.3 验证：新 CMD 窗口中 `bun --version` 正常输出

- [x] Task 10: 更新 AGENTS.md
  - [x] 10.1 添加 VCPToolBox 桥接架构说明
  - [x] 10.2 添加 Claude Code 土豆版集成说明
  - [x] 10.3 更新端口映射表（11434/6005/6006）
  - [x] 10.4 更新 MCP 服务表（添加 VCPToolBox 条目）
  - [x] 10.5 验证：AGENTS.md 内容与实际系统一致

# Task Dependencies
- Task 2 → Task 4（版本统一后再同步索引）
- Task 8 → Task 9（守护脚本依赖 Bun 在 PATH 中）
- Task 7 独立（GSTACK 命令路由）
- Task 1, 3, 5, 6 独立（各自修复不同 Bug）
- Task 10 依赖 Task 1-9 全部完成
