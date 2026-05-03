# D盘全盘索引报告

> 生成时间: 2026-04-24
> 总项目数: 232
> 总大小: 78.04 GB

## 快速查询命令

```bash
# Python查询 (推荐)
%SOFTWARE_DIR%\KF\JM\blender\5.1\python\bin\python.exe \python\MCP\Tools\disk_query.py <关键词>

# 批处理查询 (快捷)
\python\MCP\Tools\diskq.bat <关键词>
```

## 查询示例

```bash
# 搜索关键词
diskq godot
diskq rust
diskq 泰拉
diskq ai

# 按分类
diskq -c ai        # AI系统
diskq -c godot     # Godot
diskq -c rust      # Rust
diskq -c tool      # 工具

# 按技术栈
diskq -t rust
diskq -t python
diskq -t node.js
diskq -t c#

# 显示统计
diskq --stats

# 列出所有
diskq --list

# 详细模式
diskq godot -v
```

## 📊 统计总览

### 按分类
| 分类 | 项目数 |
|------|--------|
| GitHub克隆项目 | 64 |
| AI开发环境 | 51 |
| 工具项目 | 46 |
| 泰拉科技移植 | 19 |
| VCP工具箱 | 18 |
| 杂项项目 | 15 |
| 游戏Mod开发 | 7 |
| UE5.6 | 6 |

### 按技术栈
| 技术栈 | 项目数 |
|--------|--------|
| Unknown | 194 |
| Python | 24 |
| Node.js | 8 |
| Rust | 3 |
| C#/.NET | 3 |

## 🎯 重点项目

### 🤖 AI系统 (51个)
- `\python` - 核心AI开发环境
- `\python\core` - AI核心模块
- `\python\MCP_Core` - MCP核心系统
- `\python\knowledge_graph` - 知识图谱
- `\python\multi_ai` - 多AI协作

### 🦀 Rust项目 (3个)
- `\python\ironclaw_source` - 🎮 AI游戏引擎 (2790MB)
- `D:\vcp\VCPToolBox-main\rust-vexus-lite` - 网络工具 (13MB)
- `D:\vcp\VCPToolBox-main\vcp-installer-source` - 安装器 (0.37MB)

### 🎮 Godot相关 (10+)
- `D:\DEV\工具\GitHub\godotengine_godot` - 官方Godot (375MB)
- `D:\DEV\工具\GitHub\godotengine_godot-blender-exporter` - Blender导出器 (50MB)
- `%DEV_DIR%\泰拉科技\TerraTech_Godot_Project` - 泰拉科技Godot版

### 🎯 UE5.6 (6个)
- `%SOFTWARE_DIR%\KF\JM\UE_5.6\BlockWeaponArena` - 方块武器竞技场
- `%SOFTWARE_DIR%\KF\JM\UE_5.6\Engine` - UE5.6引擎

### 🛠️ 工具项目 (46个)
- `%SOFTWARE_DIR%\GJ` - 工具集合
- `D:\vcp\VCPToolBox-main` - VCP工具箱

### 🎮 游戏Mod (7个)
- `%SOFTWARE_DIR%\KF\FBY\tModLoader` - Terraria模组加载器
- `%DEV_DIR%\泰拉瑞亚` - 泰拉瑞亚Mod

## 📁 扫描路径

```
\python                      - 核心AI开发环境
D:\DEV\工具\GitHub         - GitHub克隆项目
%SOFTWARE_DIR%\KF                   - 游戏Mod开发
%SOFTWARE_DIR%\KF\JM\UE_5.6        - UE5.6
%SOFTWARE_DIR%\GJ                   - 工具项目
%DEV_DIR%\泰拉科技            - 泰拉科技移植
%DEV_DIR%\泰拉瑞亚            - 泰拉瑞亚Mod
D:\vcp\VCPToolBox-main     - VCP工具箱
D:\项目文件夹               - 杂项项目
D:\FZZ                     - FZZ
D:\嗷嗷的                  - 嗷嗷的
```

## 🔧 维护命令

```bash
# 重新扫描
diskq --scan

# 更新索引数据库
%SOFTWARE_DIR%\KF\JM\blender\5.1\python\bin\python.exe \python\MCP\Tools\disk_scanner.py scan

# 导出JSON
%SOFTWARE_DIR%\KF\JM\blender\5.1\python\bin\python.exe \python\MCP\Tools\disk_scanner.py export
```

## 📄 相关文件

- 索引数据库: `\python\MCP\Tools\disk_index.db`
- 查询脚本: `\python\MCP\Tools\disk_query.py`
- 扫描脚本: `\python\MCP\Tools\disk_scanner.py`
- 批处理: `\python\MCP\Tools\diskq.bat`
- 配置文件: `\python\MCP\Tools\disk_indexer_config.json`

---
最后更新: 2026-04-24
