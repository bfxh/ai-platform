# PROBLEMS.md - 已知问题记录

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
