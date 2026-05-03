# F:\要搞的东西 - 完整资源索引

> 生成时间: 2026-04-25 | 本索引覆盖目录下所有有价值资源

---

## 目录总览

```
F:\要搞的东西\
├── 1. MuMu共享文件夹/        → APK应用包
├── 2. cube_connector/        → Godot 4.6 方块建造游戏
├── 3. exo_extract/           → exo 分布式AI集群框架 (Rust+Python)
├── 4. mcp/                   → MCP服务器集群 (20+服务)
├── 5. 网络工具集/             → 系统网络优化工具集
├── 6. 记录每天看心情/          → 日记/心情记录
├── 7. 阶跃AI/                → TerraTech模组开发 + 游戏资产提取
└── (根目录散落文件)            → 各类脚本、工具、文档
```

---

## 1. MuMu共享文件夹/

| 文件 | 类型 | 价值 |
|------|------|------|
| `Download/应用宝.apk` | Android APK | 应用宝应用市场安装包 |
| `Download/应用宝-1.apk` | Android APK | 应用宝安装包(另一版本) |

**可榨取价值**: APK可反编译提取资源、分析应用结构。使用 `apktool d 应用宝.apk` 反编译。

---

## 2. cube_connector/ — Godot 4.6 方块建造游戏

**项目名**: Cube Builder
**引擎**: Godot 4.6 (Forward Plus)
**分辨率**: 1280x720
**状态**: 开发中，功能基本完整

### 核心脚本

| 文件 | 功能 | 代码行数 | 价值评级 |
|------|------|----------|----------|
| `main.gd` | 主控制器：建造/游玩模式切换、方块放置移除、载具物理 | ~730行 | ★★★★★ |
| `cube_manager.gd` | 方块网格管理器 | - | ★★★★ |
| `game_manager.gd` | 游戏状态管理 | - | ★★★ |
| `input_manager.gd` | 输入管理 | - | ★★★ |
| `audio_manager.gd` | 音频管理 | - | ★★ |
| `save_manager.gd` | 存档管理 | - | ★★★ |
| `ui_manager.gd` | UI管理 | - | ★★★ |
| `main_menu.gd` | 主菜单 | - | ★★★ |
| `settings_menu.gd` | 设置菜单 | - | ★★ |
| `advanced_wheel.gd` | 高级轮子系统 | - | ★★★★ |
| `wheel_block.gd` | 轮子方块 | - | ★★★ |
| `wheel_visual.gd` | 轮子视觉 | - | ★★ |
| `bug_reporter.gd` | Bug报告 | - | ★★ |

### 游戏特性 (从main.gd分析)

- **双模式**: BUILD(建造) / PLAY(驾驶)
- **双创造模式**: CREATIVE(创造) / SURVIVAL(生存)
- **方块类型**: 普通方块、驱动轮、转向轮、驱动转向轮
- **载具系统**: 自动分组、刚体物理、虚空检测
- **本地化**: 多语言支持
- **输入映射**: 鼠标放置/移除、R旋转、1-4快捷栏、L切换语言

### 可榨取价值

1. **完整游戏框架** — 可作为Godot游戏开发模板
2. **载具物理系统** — 建造→驾驶模式切换逻辑可复用
3. **网格建造系统** — 方块放置/移除/旋转逻辑可移植
4. **轮子物理** — advanced_wheel.gd 包含高级轮子模拟

---

## 3. exo_extract/ — exo 分布式AI集群框架

**项目**: exo v1.0.69
**来源**: [exo-explore/exo](https://github.com/exo-explore/exo)
**许可证**: Apache 2.0
**语言**: Rust (核心) + Python (绑定)
**功能**: 将多台设备连接为AI推理集群

### 技术架构

| 组件 | 路径 | 说明 |
|------|------|------|
| networking | `rust/networking` | libp2p网络层 |
| exo_pyo3_bindings | `rust/exo_pyo3_bindings` | Python绑定(PyO3) |
| util | `rust/util` | 工具库 |

### 核心依赖

- `libp2p 0.56` — P2P网络
- `tokio 1.46` — 异步运行时
- `keccak-const` — 哈希
- Rust Edition 2024

### 关键特性

- **自动设备发现** — 零配置P2P
- **RDMA over Thunderbolt 5** — 99%延迟降低
- **拓扑感知自动并行** — 智能模型分片
- **张量并行** — 2设备1.8x加速，4设备3.2x加速
- **MLX支持** — Apple Silicon GPU加速
- **多API兼容** — OpenAI/Claude/Ollama格式

### 可榨取价值

1. **Rust网络编程范例** — libp2p使用、P2P发现协议
2. **分布式系统设计** — 拓扑感知调度、张量并行
3. **PyO3绑定** — Rust-Python互操作参考
4. **Nix Flakes** — 完整的Nix构建配置
5. **Clippy严格配置** — 100+条lint规则，可作为Rust项目模板

---

## 4. mcp/ — MCP服务器集群

**版本**: v4.1 Ultimate + Cloud
**架构**: 6层分层设计
**总服务数**: 36个

### 核心文件

| 文件 | 功能 | 价值 |
|------|------|------|
| `mcp_ultimate_fixed.py` | 核心管理器 v4.1 | ★★★★★ |
| `mcp_config.json` | 服务配置(16个服务) | ★★★★★ |
| `mcp_ultimate.json` | Ultimate配置 | ★★★★ |
| `mcp_supervisor.py` | 监控守护 | ★★★★ |
| `auto_manager.py` | 自动管理器 | ★★★★ |
| `auto_start_manager.py` | 自动启动管理 | ★★★ |
| `stepfun_integration.py` | 阶跃AI集成 | ★★★★ |
| `cloud_storage_manager.py` | 云存储管理(8网盘) | ★★★★ |
| `cloud_storage_cli.py` | 云存储CLI | ★★★ |
| `mcp_enhancer.py` | MCP增强器 | ★★★ |
| `auto_reply_plugin.py` | 自动回复插件 | ★★★ |

### 引擎MCP服务器

| 文件 | 引擎 | 功能数 | 价值 |
|------|------|--------|------|
| `engines/godot_mcp_server.py` | Godot | 10个工具 | ★★★★ |
| `engines/unity_mcp_server.py` | Unity | 14个工具 | ★★★★★ |
| `engines/unreal_mcp_server.py` | Unreal | - | ★★★ |

### 游戏MCP服务器

| 文件 | 平台 | 功能数 | 价值 |
|------|------|--------|------|
| `gaming/steam_mcp_server.py` | Steam | 30+工具 | ★★★★★ |

### 配置的服务 (mcp_config.json)

| 分组 | 服务 | 自动启动 |
|------|------|----------|
| 核心服务 | filesystem, fetch, memory | ✅ |
| 代码优化 | python-analyzer, eslint, prettier, complexity-analyzer, security-scanner | ✅ |
| 游戏开发 | godot, unity | ❌ |
| 数据库 | sqlite, redis | ✅ |
| 开发工具 | git, python, node, npm | ❌ |

### 可榨取价值

1. **Unity MCP Server** — 完整的Unity编辑器远程控制，14个工具含场景创建、Prefab、物理、材质、光照
2. **Steam MCP Server** — 30+工具覆盖游戏库/下载/好友/成就/创意工坊/云存档/Proton
3. **Godot MCP Server** — 10个工具远程控制Godot编辑器
4. **MCP架构设计** — 6层分层、健康检查、自动重启、资源限制
5. **云存储集成** — 8网盘+4加速器的统一管理方案
6. **阶跃AI自动化** — 阶跃AI启动/关闭时自动管理MCP服务

---

## 5. 网络工具集/

**版本**: v1.0
**原始位置**: `%SOFTWARE_DIR%\WL\101`

### 工具清单

| 文件 | 功能 | 价值 |
|------|------|------|
| `启动.bat` / `启动.ps1` | 主启动器 | ★★★ |
| `网络优化工具.bat` | TCP/IP参数调优 | ★★★★ |
| `一键网络优化.reg` | 注册表优化 | ★★★ |
| `hosts加速-GitHub.bat` | GitHub Hosts加速 | ★★★★ |
| `一键系统优化.bat` | 系统级优化 | ★★★ |
| `一键设备网络优化.bat` | 设备网络优化 | ★★★ |
| `内存清理-立即释放.bat` | 内存释放 | ★★ |
| `显卡驱动优化.bat` | GPU驱动优化 | ★★★ |
| `浏览器加速-Chrome Edge.bat` | 浏览器加速 | ★★★ |
| `禁用不必要服务.bat` | 服务禁用 | ★★★ |
| `WPS专用优化.bat` | WPS优化 | ★★ |
| `设备优化.ps1` | 设备综合优化 | ★★★ |

### 可榨取价值

1. **网络优化脚本** — TCP/IP参数、注册表优化可复用
2. **GitHub加速** — hosts文件自动更新方案
3. **系统优化** — 一套完整的Windows优化方案

---

## 6. 记录每天看心情/

**类型**: 个人日记
**时间范围**: 2024年10月

| 日期 | 内容 |
|------|------|
| 2024-10-21 | "今天不想上学，告诉我爸" |
| 2024-10-24 | (有记录) |

---

## 7. 阶跃AI/ — TerraTech模组开发 + 游戏资产提取

### 7.1 BioCorp_Mod/ — 生物公司模组

**游戏**: TerraTech
**版本**: 1.0.0
**目标游戏版本**: 1.4.0
**语言**: C# / Unity

| 文件 | 功能 | 价值 |
|------|------|------|
| `BioCorpMod.cs` | 主类：5大子系统初始化 | ★★★★★ |
| `BioCorpPlugin.cs` | 模组加载入口 | ★★★★ |
| `BioCorp.csproj` | 项目配置 | ★★★ |
| `BioCorp.corp` | 公司定义文件 | ★★★ |
| `manifest.json` | 模组清单 | ★★★ |
| `COMPILE_ALL.ps1` | 一键编译脚本 | ★★★ |

#### 核心系统 (从BioCorpMod.cs分析)

| 系统 | 类名 | 功能 |
|------|------|------|
| 生物能量 | `BioEnergySystem` | 昼夜周期(5分钟)、能量/修复倍率 |
| 共生网络 | `SymbioticNetworkManager` | 4级网络(2/6/11/21方块)、3种效果倍率 |
| 基因实验室 | `GeneLabManager` | 基因编辑/合成 |
| 虫群母舰 | `SwarmMothershipManager` | 虫群AI管理 |
| 腐化系统 | `CorruptionSystem` | 腐化扩散/净化 |

#### 昼夜能量系统

| 周期 | 能量倍率 | 修复倍率 |
|------|----------|----------|
| 白天 | 1.5x | 1.0x |
| 黄昏 | 1.0x | 1.0x |
| 夜晚 | 0.5x | 2.0x |
| 黎明 | 0.8x | 1.5x |

#### 共生网络等级

| 等级 | 方块数 | 能量传输 | 修复速度 | 伤害加成 |
|------|--------|----------|----------|----------|
| 基础共生 | 2-5 | 1.1x | 1.0x | 1.0x |
| 初级网络 | 6-10 | 1.2x | 1.25x | 1.0x |
| 中级网络 | 11-20 | 1.3x | 1.5x | 1.15x |
| 超级有机体 | 21+ | 1.5x | 2.0x | 1.3x |

### 7.2 FoundationPatch/ — TerraTech基础修复补丁

**版本**: v1.0.0
**状态**: 核心修复完成(21个Bug修复模块)

| Bug分类 | 数量 | 状态 |
|---------|------|------|
| 核心Bug | 5 | ✅ 全部修复 |
| 多人同步 | 4 | ✅ 全部修复 |
| 载具系统 | 5 | ✅ 全部修复 |
| 工厂系统 | 5 | ✅ 全部修复 |
| 物理系统 | 2 | ✅ 全部修复 |
| 隐藏Bug(分析) | 13 | 📝 文档完成 |

**可榨取价值**: 完整的Unity游戏Bug修复框架，双层架构(可调整层+算法层)

### 7.3 NuterraSteam/ — 泰拉科技生产级模组框架

**代码量**: 12,105行 / 27个C#文件
**核心特性**: 多核优化、GPU剔除、实例化渲染、对象池

| 子项目 | 代码行数 | 说明 |
|--------|----------|------|
| NuterraSteam.Core | 8,246 | 核心框架 |
| CommunityPatch | 316 | 社区补丁 |
| TTML | 1,468 | 模组加载器 |
| MultiCoreMod | 2,075 | 多核优化 |

**性能提升**: 1000方块物理 30→60+FPS，大规模战斗 20→50+FPS，内存-40%

### 7.4 FragmentRecovery/ — 碎片恢复模组

**目标**: TerraTech
**框架**: BepInEx
**构建**: dotnet + .NET Framework 4.72

### 7.5 UnityBuild/ — Unity构建脚本

| 文件 | 功能 |
|------|------|
| `BuildBioCorp.cs` | BioCorp模组Unity编辑器构建脚本 |

### 7.6 工具/ — 游戏资产提取工具

| 工具 | 路径 | 功能 | 价值 |
|------|------|------|------|
| **FModel** | `FModel/FModel.exe` | Unreal Engine资产查看器 | ★★★★★ |
| **QuickBMS** | `QuickBMS/quickbms.exe` | 通用游戏资源提取 | ★★★★★ |
| **UModel** | `UModel/umodel.exe` | Unreal模型/纹理查看 | ★★★★★ |
| `unreal_tournament_4.bms` | 根目录 | UE4 PAK提取脚本 | ★★★★ |
| `extract_pak.bat` | 根目录 | TerraTech PAK提取脚本 | ★★★★ |
| `auto_extract.vbs` | 根目录 | 自动提取VBS脚本 | ★★★ |

**提取目标**: `H:\yx\TerraTech.Worlds\TT2\Content\Paks\pakchunk0-Windows.pak`

### 7.7 提取完成/ — 已提取的游戏资产

| 目录 | 内容 | 数量 |
|------|------|------|
| `3D模型_Godot/OBJ/` | Godot用3D模型 | cube.obj |
| `原始数据/` | 提取的纹理PNG | 300+张 |

### 7.8 工具脚本/

| 文件 | 功能 | 价值 |
|------|------|------|
| `stepfun_auto_chat.py` | 阶跃AI自动对话(Playwright) | ★★★★ |
| `generate_report.py` | 报告生成 | ★★★ |
| `install_deps.bat` | 依赖安装 | ★★ |

### 7.9 下载文件/

| 文件 | 说明 |
|------|------|
| `rustup-init.exe` | Rust安装器 |
| `unidot_importer.zip` | Unity资源导入工具 |

---

## 8. 根目录散落文件

### 高价值脚本

| 文件 | 功能 | 价值 |
|------|------|------|
| `auto_update_software.ps1` | Windows软件自动更新 | ★★★★ |
| `check_updates.ps1` | 软件更新检查 | ★★★ |
| `video_generator.py` | 法庭审判4K视频生成器 | ★★★★ |
| `fix_all_string_interp.py` | C#字符串插值修复 | ★★★ |
| `fix_syntax_errors.py` | C#语法错误修复 | ★★★ |
| `fix_hoverbooster_properly.py` | HoverBooster修复 | ★★★ |
| `remove_elementaffinity.py` | 元素亲和移除 | ★★★ |
| `remove_techlevel.py` | 科技等级移除 | ★★★ |
| `extract_with_unrar.py` | RAR解压 | ★★ |
| `filter_software.ps1` | 软件过滤 | ★★ |
| `memory_check.ps1` | 内存检查 | ★★ |
| `cleanup_logs.ps1` | 日志清理 | ★★ |

### 图标替换脚本

| 文件 | 功能 |
|------|------|
| `ApplyIcons.ps1` / `.bat` | 应用自定义图标 |
| `ApplyWin11Icons.ps1` | Win11图标替换 |
| `RestoreDefaultIcons.ps1` / `.bat` | 恢复默认图标 |
| `CreateBlankIcon.ps1` | 创建空白图标 |

### 编译脚本 (TerraTech模组)

| 文件 | 目标 |
|------|------|
| `compile_core.ps1` / `_v2.ps1` | 核心编译 |
| `compile_corp.bat` / `_v2~v6.bat` | BioCorp编译 |
| `compile_mod.bat` | 通用模组编译 |
| `build-all.ps1` / `build_all.ps1` | 全量构建 |
| `build_unity.ps1` | Unity构建 |

### 其他文件

| 文件 | 说明 |
|------|------|
| `PsExec.exe` | Sysinternals远程执行工具 |
| `FModel.zip` | FModel打包 |
| `WolvenKit-8.17.3.zip` | Cyberpunk 2077模组工具 |
| `deep-reading-analyst.zip` | 深度阅读分析工具 |
| `多媒体.7z` | 多媒体资源 |
| `演示文稿2/3.pptx` | PPT演示文稿 |
| `software_list.csv` | 已安装软件列表 |
| `programming_folders.csv` | 编程目录列表 |
| `mdbx.dat` | LMDB数据库文件 |
| `delete_sogou.bat` / `dism删除搜狗.ps1` | 搜狗清理 |
| `sogou_cleanup.reg` / `彻底清理搜狗残留.reg` | 搜狗注册表清理 |

---

## 价值总结与待开发方向

### ★★★★★ 最高价值

1. **Unity MCP Server** — 14个工具，可远程控制Unity编辑器，适合AI辅助游戏开发
2. **Steam MCP Server** — 30+工具，完整的Steam平台MCP集成
3. **cube_connector (Godot游戏)** — 完整的方块建造+载具驾驶游戏，730行核心代码
4. **BioCorp Mod** — 5大子系统、昼夜能量、共生网络，完整的Unity模组架构
5. **FModel + QuickBMS + UModel** — 三大游戏资产提取工具，可反编译UE4游戏

### ★★★★ 高价值

6. **exo框架** — 分布式AI推理集群，Rust+Python，libp2p网络
7. **FoundationPatch** — 21个Bug修复模块，双层架构设计
8. **NuterraSteam** — 12,105行多核优化框架
9. **stepfun_auto_chat.py** — Playwright自动化对话，可扩展到其他AI平台
10. **video_generator.py** — 4K视频生成器，OpenCV+MoviePy
11. **MCP集群架构** — 6层设计、健康检查、自动重启

### ★★★ 中等价值

12. **网络工具集** — 完整的Windows网络优化方案
13. **auto_update_software.ps1** — 软件自动更新框架
14. **C#修复脚本** — 字符串插值、语法错误批量修复
15. **图标替换脚本** — Win11自定义图标方案

### 待开发方向

1. **APK反编译** — 应用宝APK可用apktool反编译分析
2. **TerraTech PAK提取** — 已有工具和脚本，可继续提取游戏资产
3. **MCP服务器整合** — 将散落的MCP服务器统一到当前MCP配置
4. **exo本地部署** — 在Windows上部署exo分布式AI集群
5. **Godot-Unity互操作** — cube_connector的GDScript逻辑可移植到Unity
6. **视频生成器扩展** — 法庭审判视频生成器可模板化为通用视频生成框架
7. **WolvenKit** — Cyberpunk 2077模组工具，可探索CP77模组开发
