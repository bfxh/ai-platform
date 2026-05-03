# TRAE 通知 & 灵动岛 — 开发方向与实施计划

## 一、项目目标

**在华为手机上实现 TRAE 通知 + 灵动岛效果的应用**

具体来说：开发一个 HarmonyOS 应用，当 TRAE IDE 中有事件（如代码编译完成、AI回复完成、错误提醒等）时，通过手机通知和灵动岛实时展示状态。

---

## 二、当前环境现状

| 项目 | 状态 | 说明 |
|------|------|------|
| TRAE CN | ✅ 已安装 | `D:\rj\KF\BC\Trae CN\Trae CN.exe` |
| DevEco Studio | ⚠️ 3.1.0.501（旧版） | `D:\rj\KF\HUAWEI\DevEco Studio`，仅支持 HarmonyOS 4 / API 9 |
| ArkTS 插件 | ✅ 已安装 | nailyzero.vscode-naily-ets-1.3.9 |
| Swift 插件 | ✅ 已安装 | sswg.swift-lang-1.11.4 |
| SweetPad 插件 | ✅ 已安装 | sweetpad.sweetpad-0.1.82 |
| CodeLLDB 插件 | ✅ 已安装 | vadimcn.vscode-lldb-1.12.2 |
| DevEco MCP | ✅ 已配置 | @deveco-codegenie/mcp@0.1.8-fix4 |
| Node.js | ✅ v10.9.7 | 可用 |
| 华为手机 | 🔲 待连接 | 需开启开发者模式 |

---

## 三、核心问题：两条开发路线

### 路线A：当前 DevEco 3.1（HarmonyOS 4 / API 9）

- **能做什么**：普通通知、悬浮窗（模拟灵动岛效果）
- **不能做什么**：官方实况窗 API（`@kit.LiveViewKit`）、胶囊态/卡片态
- **优点**：无需升级，现在就能开发
- **缺点**：只是通知+悬浮窗，不是真正的灵动岛

### 路线B：升级 DevEco 5.0+（HarmonyOS NEXT / API 12+）

- **能做什么**：官方实况窗 API（胶囊态灵动岛 + 卡片态）、所有路线A功能
- **不能做什么**：需要升级DevEco Studio、需要HarmonyOS 5.0+手机
- **优点**：真正的华为灵动岛体验
- **缺点**：需要升级开发工具，需申请实况窗服务权益

### ⭐ 推荐方案：路线B（升级DevEco Studio 5.0+）

理由：
1. 你的需求是"灵动岛"，路线A只是模拟，体验差
2. 华为官方已发布实况窗 API，应该用官方方案
3. DevEco 3.1 太旧，很多新特性不支持
4. 升级后路线A的功能也全部兼容

---

## 四、开发方向定义

### 产品名称：TRAE 通知灵动岛

### 功能清单

#### P0 — 核心功能（必须实现）

| # | 功能 | 说明 |
|---|------|------|
| 1 | **本地通知** | 应用内发送文本通知到手机通知栏 |
| 2 | **实况窗-胶囊态** | 状态栏灵动岛显示精简信息（图标+文字） |
| 3 | **实况窗-卡片态** | 锁屏/通知中心显示详细信息（标题+内容+进度） |
| 4 | **实况窗生命周期** | 启动→更新进度→结束，完整流程 |
| 5 | **通知权限管理** | 请求通知授权，处理拒绝情况 |

#### P1 — 增强功能（优先实现）

| # | 功能 | 说明 |
|---|------|------|
| 6 | **多场景支持** | 即时配送、打车、导航、计时器、自定义 |
| 7 | **进度模拟** | 自动模拟进度更新（3秒/次），演示灵动岛动态效果 |
| 8 | **通知历史** | 本地记录通知发送历史，可查看和清除 |
| 9 | **自定义输入** | 用户可输入标题、内容、胶囊文字 |

#### P2 — 进阶功能（后续迭代）

| # | 功能 | 说明 |
|---|------|------|
| 10 | **Push Kit 远程推送** | 服务端推送实况窗更新（需AppGallery Connect） |
| 11 | **TRAE Webhook 集成** | TRAE 事件通过HTTP推送到手机 |
| 12 | **iOS 版本** | 用 Swift + Live Activity 实现苹果灵动岛 |

---

## 五、实施步骤（路线B）

### 阶段1：环境升级（必须先完成）

1. **下载安装 DevEco Studio 5.0+**
   - 访问 https://developer.huawei.com/consumer/cn/deveco-studio/
   - 登录华为开发者账号下载最新版
   - 卸载旧版 3.1，安装新版到 `D:\rj\KF\HUAWEI\DevEco Studio`
   - 安装后配置 HarmonyOS NEXT SDK (API 12+)

2. **更新 MCP 配置中的 DEVECO_PATH**
   - 修改 `\python\mcp.json` 中 deveco-mcp 的 DEVECO_PATH 为新路径

3. **华为手机准备**
   - 系统升级到 HarmonyOS 5.0+
   - 开启开发者模式：设置 → 关于手机 → 连点7次版本号
   - 开启USB调试：设置 → 系统和更新 → 开发人员选项
   - USB连接电脑

### 阶段2：项目创建（DevEco Studio 5.0+ 中操作）

4. **用 DevEco Studio 创建新项目**
   - File → New → Create Project
   - 选择 Empty Ability 模板
   - Project Name: `TraeLiveView`
   - Bundle Name: `com.trae.liveview`
   - Save Location: `D:\开发\TraeLiveView`
   - Compatible SDK: API 12

5. **注入灵动岛代码**
   - 将已写好的 LiveViewService.ets（官方实况窗API版）复制到项目
   - 将 Index.ets 主界面代码复制到项目
   - 更新 module.json5 添加实况窗扩展和通知权限

### 阶段3：核心代码开发

6. **LiveViewService.ets** — 实况窗核心服务
   - 使用 `@kit.LiveViewKit` 的 `liveViewManager`
   - 实现：startLiveView / updateLiveView / stopLiveView
   - 实现：sendLocalNotification（普通通知）
   - 实现：requestNotificationPermission（权限请求）

7. **LiveViewExtension.ets** — 实况窗扩展
   - 继承 LiveViewExtensionAbility
   - 处理实况窗生命周期事件

8. **Index.ets** — 主界面
   - 场景选择器（7种场景类型）
   - 自定义输入（标题/内容/胶囊文字）
   - 操作按钮（启动灵动岛/发送通知/更新进度/结束）
   - 进度显示（进度条+状态指示）
   - 通知历史列表

9. **module.json5** — 模块配置
   - 声明 LiveViewExtension 扩展
   - 添加通知权限
   - 添加网络权限

### 阶段4：编译运行与调试

10. **编译项目**
    - DevEco Studio → Build → Build Hap(s)/APP(s)
    - 修复编译错误

11. **部署到华为手机**
    - 连接手机 → 选择设备 → Run
    - 授权通知权限
    - 测试灵动岛效果

### 阶段5：AppGallery Connect 配置（实况窗上线必须）

12. **申请实况窗服务权益**
    - 登录 AppGallery Connect
    - 项目设置 → 开放能力管理 → 实况窗服务 → 申请
    - 填写场景类型和描述
    - 等待审批（5个工作日）

13. **白名单设备调试**
    - 推送服务 → 实况窗白名单设备管理
    - 添加测试设备 Push Token
    - 24小时生效

---

## 六、iOS 版本方向（P2，后续考虑）

- **开发工具**：TRAE + SweetPad + Swift 插件（已安装）
- **核心API**：ActivityKit + Live Activity
- **限制**：完整开发需要 Mac + Xcode，Windows 仅能编辑代码
- **灵动岛实现**：WidgetKit + ActivityKit 创建 Live Activity
- **暂时搁置**：优先完成华为版本，iOS 版本后续再规划

---

## 七、已完成的准备工作

以下工作已经完成，无需重复：

- ✅ TRAE 插件安装（ArkTS / Swift / SweetPad / CodeLLDB）
- ✅ DevEco MCP Toolbox 配置
- ✅ 核心代码文件已编写（LiveViewService.ets / Index.ets / EntryAbility.ets）
- ✅ 项目目录结构已创建（`D:\开发\harmony_liveview`）
- ✅ 自动化脚本已创建（create_project.ps1 / inject_code.ps1 / upgrade_deveco.ps1）

## 八、待用户操作的关键步骤

**阻塞项：DevEco Studio 3.1 太旧，必须升级到 5.0+**

用户需要：
1. 去华为开发者官网下载 DevEco Studio 5.0+
2. 卸载旧版，安装新版
3. 在新版中创建项目

这三步只能用户手动完成（需要登录华为账号下载），AI无法代替操作。
