# PROBLEMS.md - 已知问题记录

## AI 平台问题

### T-003 ✅ fixed
**问题**: 无法处理弹窗（模组冲突/崩溃/JVM错误/许可协议）
**修复**: game_test_framework.py 新增 detect_popups() 自动检测处理弹窗

### T-004 ✅ fixed
**问题**: 模组测试阶段 (mod_test) 有声明无实现
**修复**: test_minecraft_1204.py 新增 test_mods() 函数

### T-005 ✅ fixed
**问题**: 日志关键字 "Saving chunks" 无法判断加载完成
**修复**: game_test_framework.py 改用多个加载标志 + 画面稳定双重判断

### T-006 ✅ fixed
**问题**: launch_1204.py 只启动进程，不等待游戏窗口
**修复**: launch_1204.py 新增 wait_for_window() 等待 Minecraft 窗口出现

### W-002 ✅ fixed
**问题**: game_state_mcp 无法作为真正的 MCP 服务被调用
**修复**: game_state_mcp.py 实现 stdio 服务器模式

### A-001 ✅ fixed
**问题**: Dispatcher 注册名冲突
**修复**: dispatcher.py 双注册: 项目名/单元名 + raw名

### A-002 ✅ fixed
**问题**: dispatch 不支持 mcp/workflow
**修复**: dispatcher.py 新增 _dispatch_mcp/_dispatch_workflow/_dispatch_cli

### S-001 ✅ fixed
**问题**: game_test external_path 错误
**修复**: game_test/plugin.toml 改为 /python/projects/game_test

### S-002 ✅ fixed
**问题**: minecraft external_path 错误
**修复**: minecraft/plugin.toml 改为 /python

## TerraTech 项目问题

## 已解决问题

### 1. 游戏启动后退出并再次启动 (已解决)
- **日期**: 2026-04-26
- **描述**: 游戏启动后约60-76秒退出，然后EOS启动器重新启动游戏，导致模组被卸载重载
- **根本原因**:
  1. 旧版GameStartupPatcher阻止了`EnterSetupStateAsync`和`HandleEnterSetupState`等关键初始化方法，导致游戏初始化流程断裂
  2. 旧版GameSafetyPatcher阻止了`UpdateModSession`和`ProcessLoadingMod`，导致模组无法正常加载
  3. 游戏通过`Application.Quit()`退出进程，EOS启动器检测到退出后重新启动
  4. `Application.Quit`的Harmony补丁因方法重载歧义而失败
- **解决方案**:
  1. 重写GameStartupPatcher，只阻止重启和错误处理方法，不阻止正常初始化流程
  2. 移除对`UpdateModSession`和`ProcessLoadingMod`的阻止
  3. 添加`Application.Quit()`和`Application.Quit(int)`的Hook，阻止游戏意外退出
  4. 修改EOSBootstrapper.ini设置`NoOperation=1`
  5. 使用`new System.Type[0]`和`new System.Type[] { typeof(int) }`明确指定方法签名
- **验证**: 自动化测试显示游戏稳定运行120秒+，exit_count=0，pids_seen=1

### 2. Harmony补丁方法重载歧义 (已解决)
- **日期**: 2026-04-26
- **描述**: `Application.Quit`有两个重载，Harmony无法自动匹配导致补丁失败
- **错误信息**: `Ambiguous match for HarmonyMethod`
- **解决方案**: 将两个重载分别放在不同的HarmonyPatch类中，使用明确的类型数组指定方法签名
