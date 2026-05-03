# TRAE 通知灵动岛 Spec

## Why
用户希望在华为手机上运行 TRAE 通知和灵动岛功能，实时展示 TRAE IDE 事件状态（编译完成、AI回复、错误提醒等）。当前 DevEco Studio 3.1 太旧不支持官方实况窗 API，需要升级开发环境并基于 HarmonyOS NEXT API 12+ 的 `@kit.LiveViewKit` 实现真正的灵动岛体验。

## What Changes
- 升级 DevEco Studio 从 3.1 到 5.0+，支持 HarmonyOS NEXT SDK
- 创建 HarmonyOS NEXT 项目（API 12+，ArkTS 语言）
- 实现实况窗核心服务（LiveViewService），封装 `liveViewManager` 的启动/更新/停止生命周期
- 实现实况窗扩展能力（LiveViewExtension），处理系统级实况窗事件
- 实现主界面（Index），包含场景选择、自定义输入、灵动岛控制、进度展示、通知历史
- 配置 module.json5 声明实况窗扩展和通知权限
- 创建一键代码注入脚本，将代码注入到 DevEco Studio 创建的项目模板中

## Impact
- Affected specs: 无（新项目）
- Affected code: `D:\开发\harmony_liveview\code_v2\` 下所有文件、`\python\mcp.json` MCP配置

## ADDED Requirements

### Requirement: 实况窗核心服务
系统 SHALL 提供 LiveViewService 类，封装 HarmonyOS 实况窗 API 的完整生命周期管理。

#### Scenario: 启动实况窗
- **WHEN** 用户点击"启动灵动岛"按钮
- **THEN** 系统请求通知权限，调用 `liveViewManager.startLiveView()` 创建实况窗，在状态栏显示胶囊态、在锁屏/通知中心显示卡片态

#### Scenario: 更新实况窗进度
- **WHEN** 实况窗处于活跃状态且进度变化
- **THEN** 系统调用 `liveViewManager.updateLiveView()` 更新胶囊文字和卡片内容

#### Scenario: 停止实况窗
- **WHEN** 用户点击"结束灵动岛"或进度达到100%
- **THEN** 系统调用 `liveViewManager.stopLiveView()` 移除实况窗

#### Scenario: 实况窗启动失败降级
- **WHEN** 实况窗 API 调用失败（如设备不支持、权限不足）
- **THEN** 系统自动降级为普通通知发送

### Requirement: 普通通知服务
系统 SHALL 提供本地通知发送能力，作为实况窗的降级方案和独立功能。

#### Scenario: 发送普通通知
- **WHEN** 用户点击"发送通知"按钮
- **THEN** 系统通过 `notificationManager.publish()` 发送文本通知到通知栏

### Requirement: 通知权限管理
系统 SHALL 在首次使用通知/实况窗功能前请求通知授权。

#### Scenario: 权限已授予
- **WHEN** 用户已授权通知权限
- **THEN** 直接执行通知/实况窗操作

#### Scenario: 权限未授予
- **WHEN** 用户未授权通知权限
- **THEN** 系统尝试请求权限，若仍被拒绝则操作失败并记录日志

### Requirement: 多场景支持
系统 SHALL 支持7种实况窗场景类型：即时配送、打车出行、导航、航班、赛事比分、计时器、自定义。

#### Scenario: 选择场景
- **WHEN** 用户在场景选择器中点击某个场景
- **THEN** 该场景高亮选中，后续启动实况窗时使用该场景类型

### Requirement: 主界面交互
系统 SHALL 提供完整的主界面，包含场景选择、内容输入、操作控制、进度展示、历史记录。

#### Scenario: 自定义输入
- **WHEN** 用户在输入框中修改标题、内容、胶囊文字
- **THEN** 后续操作使用修改后的内容

#### Scenario: 进度自动模拟
- **WHEN** 实况窗启动后
- **THEN** 系统每3秒自动递增5%进度并更新实况窗，达到100%时自动停止

#### Scenario: 通知历史记录
- **WHEN** 执行任何通知/实况窗操作
- **THEN** 操作记录添加到历史列表顶部，支持单条删除和全部清除

### Requirement: 实况窗扩展能力
系统 SHALL 声明 LiveViewExtension 扩展，处理系统级实况窗生命周期回调。

#### Scenario: 系统创建实况窗
- **WHEN** 系统创建实况窗实例
- **THEN** LiveViewExtension.onLiveViewCreate() 被调用并记录日志

### Requirement: 一键代码注入脚本
系统 SHALL 提供 PowerShell 脚本，将预写好的代码文件自动注入到 DevEco Studio 创建的项目模板中。

#### Scenario: 注入代码
- **WHEN** 用户运行 inject_v2.ps1 并输入项目路径
- **THEN** 脚本自动备份原始文件，复制 LiveViewService/LiveViewExtension/Index/EntryAbility 到对应目录，替换 module.json5

### Requirement: DevEco MCP 配置
系统 SHALL 在 TRAE 的 mcp.json 中配置 DevEco MCP Toolbox，支持在 TRAE 中进行鸿蒙开发。

#### Scenario: MCP 工具可用
- **WHEN** TRAE 启动并加载 MCP 配置
- **THEN** deveco-mcp 服务可用，支持知识库检索、ArkTS检查、UI分析、构建运行

## MODIFIED Requirements

### Requirement: DevEco Studio 版本
DevEco Studio 版本 SHALL 为 5.0 Release 及以上，以支持 HarmonyOS NEXT SDK (API 12+) 和实况窗 API。当前安装的 3.1 版本需升级。

## REMOVED Requirements
无
