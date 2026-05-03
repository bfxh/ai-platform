# Godot AI 全生态系统 - 对比文档

> 项目: FragmentWeaponGame @ Godot 4.6 | Jolt Physics 3D
> 全开源 · GDExtension优先 · Godot 4.4+

---

## 1. Godot MCP Server (AI远程控制Godot引擎)

| 方案 | 语言 | 工具数 | 状态 | 特点 |
|------|------|--------|------|------|
| **[Vollkorn-Games](https://github.com/Vollkorn-Games/godot-mcp)** (主选) | TypeScript | 61+ | 源码已克隆，待 `npm run build` | 功能最全：场景/节点/脚本/截图/动画/TileMap/自动加载/信号组/测试运行/UID |
| **[Coding-Solo](https://github.com/Coding-Solo/godot-mcp)** (备选) | TypeScript | ~20 | 源码已克隆，待 `npm run build` | 轻量：项目启动/运行/调试输出 |
| **[godot-mcp-cn](https://github.com/hhhh124hhhh/godot-mcp-cn)** | TypeScript | ~15 | 源码已克隆，待 `npm run build` | 中文优化 + 20+子技能 + CLI自动启动 |
| **[godot-bridge-mcp](https://github.com/GodotBridge/godot-bridge-mcp)** | Python | ~12 | 已克隆 | 双向WebSocket通信，Godot↔MCP互调 |
| **[Higodot](https://github.com/hi-godot/godot-ai)** | Python | 30+ | 已克隆 + 插件已在项目 | 生产级FastMCP + WebSocket + 编辑器调试面板 |

---

## 2. Godot编辑器内AI助手 (Editor AI Plugins)

| 方案 | Provider支持 | 状态 | 特点 |
|------|-------------|------|------|
| **[Fuku](https://github.com/af009/fuku)** (主选) | Ollama/OpenAI/Claude/Gemini/Docker | ✅ 已安装到项目 | 底部面板AI，Markdown渲染 + GDScript语法高亮 |
| AI Coding Assistant | OpenAI/Claude/Ollama | 源码已克隆 | 专注代码生成，上下文感知 |
| AI Assistant Hub | 多provider | 源码已克隆 | Hub模式管理多种AI后端 |

---

## 3. Godot游戏内LLM推理 (GDExtension)

| 方案 | 语言 | 功能 | 状态 |
|------|------|------|------|
| **[GDLlama](https://github.com/xarillian/GDLlama)** (主选) | C++ | LLM推理/Embedding/多模态 | 源码已克隆，需CMake编译 |
| **[Godot Llama](https://github.com/Adriankhl/godot-llm)** (备选) | C++ | LLM/RAG/Embedding/SQLite | 源码已克隆，需CMake编译 |

---

## 4. Godot程序化破碎/破坏

| 方案 | 技术 | 特点 | 状态 |
|------|------|------|------|
| **[VoronoiShatter](https://github.com/robertvaradan/voronoishatter)** (主选) | C# Plugin | Voronoi碎裂，配置化 | ✅ 已安装 |
| **[Destruct3D](https://github.com/OffByTwoDev/Destruct3D)** (备选) | C# Plugin | 实时BSPTree破坏 | ✅ 已安装 |
| Concave Mesh Slicer | GDScript | 凹面实时切片 | ✅ 已安装 |
| Mesh Slicing GDExtension | C++ | 高性能C++切片 | ✅ 已安装 |

---

## 5. 项目当前Addon清单

| 工具 | 功能 | 状态 |
|------|------|------|
| Fuku | 编辑器AI助手 | ✅ |
| Godot AI (Higodot) | MCP服务端插件 | ✅ |
| GUT | GDScript单元测试 | ✅ |
| Godot E2E | 端到端自动化测试 | ✅ |
| Godot Jolt | 高性能3D物理 | ✅ |
| VoronoiShatter | Voronoi碎裂 | ✅ |
| Destruct3D | 实时破坏 | ✅ |
| Concave Mesh Slicer | 实时网格切片 | ✅ |
| Mesh Slicing GDExtension | 高性能C++切片 | ✅ |
| AI Context Generator | 项目结构JSON导出 | ✅ |
| Fragment Weapon System | 碎片武器系统 | ✅ |

---

## 6. MCP 统一配置对照 (mcp_3d_unified.json)

| MCP条目 | 入口 | 状态 |
|---------|------|------|
| `godot-mcp` | `godot-mcp-vollkorn/build/index.js` | ⚠️ 待编译 |
| `godot-mcp-coding-solo` | `godot-mcp-coding-solo/build/index.js` | ⚠️ 待编译 |
| `godot-mcp-cn` | `godot-mcp-cn/server/dist/index.js` | ⚠️ 待编译 |
| `godot-ai` | `python -m godot_ai` | ⚠️ 待pip |
| `godot-bridge-mcp` | `npx tsx ...` | ✅ 即时编译 |
| blender | `uvx blender-mcp` | ✅ |
| unreal-mcp | `unreal-mcp/dist/bin.js` | ✅ |
| uemcp | `uemcp/server/dist/index.js` | ✅ |
| unity-mcp | `unity-mcp-coplay/...` | ✅ |
| houdini-mcp | `houdini-mcp/main.py` | ✅ |
| maya-mcp | `MayaMCP/...` | ✅ |
| rhino-mcp | `rhino3d-mcp/main.py` | ✅ |
| rhino-gh-mcp | `rhino_gh_mcp/main.py` | ✅ |

---

*全开源 · Godot 4.4+ · GDExtension优先 · 对比方案 Blender/UE5/Unity 完整MCP生态*
