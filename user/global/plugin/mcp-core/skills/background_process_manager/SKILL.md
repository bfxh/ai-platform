# 后台进程管理技能

## 功能介绍

后台进程管理技能是一个专门用于识别和关闭不需要的后台程序的工具，特别针对那些不在任务栏显示的程序（如WPC）。该技能可以帮助用户优化系统性能，减少不必要的资源占用。

## 核心功能

- **自动清理**：识别并关闭目标列表中的后台进程
- **进程列表**：显示当前运行的所有进程及其状态
- **智能识别**：区分需要保留的编程软件和需要关闭的后台程序
- **可配置**：支持自定义排除列表和目标列表
- **详细日志**：记录所有操作，便于后续分析

## 安装方法

1. 确保MCP Core已安装并运行
2. 将技能目录复制到 `MCP_Core/skills/` 目录下
3. 重启MCP Core服务

## 使用方法

### 命令行使用

```bash
# 清理后台进程
python -m MCP_Core.cli skill background_process_manager clean

# 列出当前运行的进程
python -m MCP_Core.cli skill background_process_manager list

# 显示当前配置
python -m MCP_Core.cli skill background_process_manager config

# 添加进程到排除列表
python -m MCP_Core.cli skill background_process_manager add-excluded --process "code.exe"

# 添加进程到目标列表
python -m MCP_Core.cli skill background_process_manager add-target --process "WPC.exe"

# 从排除列表中移除进程
python -m MCP_Core.cli skill background_process_manager remove-excluded --process "code.exe"

# 从目标列表中移除进程
python -m MCP_Core.cli skill background_process_manager remove-target --process "WPC.exe"
```

### 直接运行脚本

```bash
# 清理后台进程
python background_process_manager.py clean

# 列出当前运行的进程
python background_process_manager.py list

# 显示当前配置
python background_process_manager.py config
```

## 配置说明

### 配置文件

技能会在首次运行时生成 `background_process_config.json` 配置文件，包含以下内容：

- **excluded_processes**：不会被关闭的进程列表
- **target_processes**：会被关闭的进程列表
- **log_file**：日志文件路径

### 默认排除列表

- **编程相关**：code.exe, visualstudio.exe, devenv.exe, blender.exe, godot.exe, python.exe等
- **系统关键**：explorer.exe, svchost.exe, winlogon.exe, csrss.exe等
- **安全软件**：antimalware.exe, defender.exe
- **常用工具**：chrome.exe, firefox.exe, edge.exe, notepad.exe

### 默认目标列表

- **WPC相关**：WPC.exe, WPCService.exe
- **Adobe相关**：Adobe CEF Helper.exe, Adobe Desktop Service.exe
- **娱乐软件**：Spotify.exe, Steam.exe, Discord.exe
- **云存储**：OneDrive.exe, Dropbox.exe, GoogleDrive.exe
- **通信工具**：Teams.exe, Skype.exe, Zoom.exe
- **媒体软件**：iTunes.exe, QuickTimePlayer.exe
- **游戏启动器**：Origin.exe, EpicGamesLauncher.exe, UbisoftConnect.exe

## 注意事项

1. **谨慎使用**：该技能会强制终止进程，请确保目标列表中的进程确实可以安全关闭
2. **编程软件**：默认不会关闭编程相关软件，如VS Code、Visual Studio、Blender、Godot等
3. **系统进程**：默认不会关闭系统关键进程，确保系统稳定运行
4. **权限要求**：某些进程可能需要管理员权限才能关闭
5. **日志记录**：所有操作都会记录到 `background_process_log.txt` 文件中

## 扩展建议

1. **定时清理**：可以设置定时任务，定期运行清理功能
2. **自定义规则**：根据个人使用习惯，调整排除列表和目标列表
3. **性能监控**：结合性能监控工具，分析清理前后的系统性能变化
4. **批量操作**：支持批量添加/移除进程到配置列表

## 故障排除

### 进程无法关闭
- 检查是否有足够的权限
- 确认进程不是系统关键进程
- 尝试以管理员身份运行

### 配置文件丢失
- 技能会自动生成默认配置文件
- 可以手动创建配置文件，参考默认配置格式

### 日志文件过大
- 定期清理日志文件
- 修改配置中的日志文件路径到其他位置

## 示例场景

### 场景1：开发前清理
在开始编程前，运行清理命令关闭不必要的后台进程，确保系统资源集中在开发工具上。

### 场景2：游戏前优化
在启动游戏前，关闭所有可能影响游戏性能的后台进程，如聊天软件、云存储同步等。

### 场景3：系统维护
定期运行清理命令，保持系统清爽，减少资源占用。

## 版本历史

- **v1.0.0**：初始版本，包含基本的进程管理功能

## 贡献指南

欢迎提交Issue和Pull Request，帮助改进这个技能。

## 许可证

MIT License