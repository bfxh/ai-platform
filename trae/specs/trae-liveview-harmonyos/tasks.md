# Tasks

- [ ] Task 1: 升级 DevEco Studio 到 5.0+（阻塞项，需用户手动下载）
  - [ ] SubTask 1.1: 下载 DevEco Studio 5.0+ 安装包（需登录华为开发者账号）
  - [ ] SubTask 1.2: 卸载旧版 DevEco Studio 3.1
  - [ ] SubTask 1.3: 安装新版 DevEco Studio 到 D:\rj\KF\HUAWEI\DevEco Studio
  - [ ] SubTask 1.4: 配置 HarmonyOS NEXT SDK (API 12+)

- [ ] Task 2: 更新 TRAE MCP 配置
  - [ ] SubTask 2.1: 修改 \python\mcp.json 中 deveco-mcp 的 DEVECO_PATH 为新安装路径

- [ ] Task 3: 在 DevEco Studio 中创建 HarmonyOS NEXT 项目
  - [ ] SubTask 3.1: 创建 Empty Ability 项目，Bundle Name: com.trae.liveview，保存到 D:\开发\TraeLiveView
  - [ ] SubTask 3.2: 确认项目可同步和编译

- [ ] Task 4: 注入灵动岛代码到项目
  - [ ] SubTask 4.1: 运行 inject_v2.ps1 脚本，输入项目路径
  - [ ] SubTask 4.2: 验证所有文件已正确复制到对应目录

- [x] Task 5: 验证实况窗核心服务代码 (code_v2预验证通过)
  - [x] SubTask 5.1: 确认 LiveViewService.ets 使用 @kit.LiveViewKit 的 liveViewManager
  - [x] SubTask 5.2: 确认 startLiveView/updateLiveView/stopLiveView 生命周期完整
  - [x] SubTask 5.3: 确认 sendLocalNotification 降级通知功能存在
  - [x] SubTask 5.4: 确认 requestNotificationPermission 权限请求逻辑

- [x] Task 6: 验证实况窗扩展代码 (code_v2预验证通过)
  - [x] SubTask 6.1: 确认 LiveViewExtension.ets 继承 LiveViewExtensionAbility
  - [x] SubTask 6.2: 确认 onLiveViewCreate/onLiveViewDestroy/onLiveViewEvent 回调已实现

- [x] Task 7: 验证主界面代码 (code_v2预验证通过)
  - [x] SubTask 7.1: 确认 Index.ets 包含7种场景选择器
  - [x] SubTask 7.2: 确认自定义输入（标题/内容/胶囊标题/胶囊内容）
  - [x] SubTask 7.3: 确认4个操作按钮（启动灵动岛/发送通知/更新进度/结束）
  - [x] SubTask 7.4: 确认进度条和状态指示
  - [x] SubTask 7.5: 确认通知历史列表（添加/删除/清除）
  - [x] SubTask 7.6: 确认进度自动模拟（3秒/次，5%递增）

- [x] Task 8: 验证模块配置 (code_v2预验证通过)
  - [x] SubTask 8.1: 确认 module.json5 声明 LiveViewExtension 扩展（type: liveView）
  - [x] SubTask 8.2: 确认 module.json5 包含通知权限 ohos.permission.NOTIFICATION_CONTROLLER
  - [x] SubTask 8.3: 确认 module.json5 包含网络权限 ohos.permission.INTERNET

- [x] Task 9: Web版通知+灵动岛已实现并上线
  - [x] SubTask 9.1: 在 TRAE Agent Hub 中添加通知标签页
  - [x] SubTask 9.2: 实现 Web Notification API 通知功能
  - [x] SubTask 9.3: 实现灵动岛UI组件（胶囊态+卡片态+进度条）
  - [x] SubTask 9.4: 实现场景选择器（自定义/配送/打车/导航/计时）
  - [x] SubTask 9.5: 实现通知历史记录（添加/删除/清除）
  - [x] SubTask 9.6: 实现进度自动模拟（3秒/次，5%递增）
  - [x] SubTask 9.7: 服务器启动成功，HTTP 200 OK

- [ ] Task 10: 部署到华为手机测试
  - [ ] SubTask 10.1: 华为手机浏览器访问 http://192.168.1.6:8765
  - [ ] SubTask 10.2: 添加到主屏幕（PWA安装）
  - [ ] SubTask 10.3: 授权通知权限
  - [ ] SubTask 10.4: 测试启动灵动岛、更新进度、结束灵动岛完整流程
  - [ ] SubTask 10.5: 测试普通通知发送
  - [ ] SubTask 10.6: 测试实况窗启动失败时的降级通知

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 3]
- [Task 10] depends on [Task 9]
