# 跨引擎3D资产转换器 - 结构化摘要

> 来源: 2026-04-28 开发实践
> 位置: \python\storage\mcp\JM\

## 项目概述

本地化3D资产跨引擎转换工具，支持拖拽操作，自动完成 Blender烘焙 → Godot/UE5导入 的全流程。

## 核心架构

```
drag_convert.py (拖拽入口)
    ↓
engine_converter.py (核心转换逻辑, MCP服务)
    ↓
engine_converter_extended.py (1610条转换矩阵)
    ↓
engine_converter_ui.py (交互式菜单)
    ↓
engine_converter_plugins/ (引擎插件)
    ├── blender_addon/
    ├── godot_importer/
    ├── ue5_plugin/
    └── unity_editor/
```

## 关键技术决策

### 1. 为什么用烘焙贴图而不是程序化材质
- **问题**: glTF/GLB格式只支持图片贴图，不支持Blender程序化节点(Noise/ColorRamp等)
- **方案**: 用Cycles引擎烘焙 → Albedo/Roughness/Normal三张贴图 → 替换节点为ImageTexture
- **效果**: 484KB GLB vs 9.9KB空GLB，任何引擎都能正确显示

### 2. 为什么OBJ转出来是全白的
- TerraTech等游戏导出的OBJ没有UV坐标(vt行缺失)和材质库(mtllib行缺失)
- 游戏内部用程序化着色器渲染，导出时颜色信息丢失
- **解决**: Blender自动UV展开(smart_project) + 程序化材质生成 + Cycles烘焙

### 3. Blender 5.1 API变化
- `bpy.ops.import_scene.obj` → `bpy.ops.wm.obj_import`
- `bpy.ops.import_scene.fbx` → `bpy.ops.wm.fbx_import`
- `Material.use_nodes` 将在 Blender 6.0 移除

### 4. Godot场景引用
- `ExtResource("1")` 不需要外层引号，否则变成 `"ExtResource("1")"` 嵌套
- GLB作为PackedScene实例化时，parent路径用 `"."` 而不是场景名

## 转换矩阵统计

| 分类 | 数量 |
|------|------|
| 3D引擎 | 34 |
| 2D引擎 | 20 |
| Web引擎 | 12 |
| DCC工具 | 20 |
| CAD/BIM | 18 |
| 渲染引擎 | 10 |
| 地形生成 | 7 |
| 动画/动捕 | 16 |
| VFX粒子 | 6 |
| 数字孪生 | 5 |
| XR平台 | 23 |
| 音频中间件 | 14 |
| 物理引擎 | 15 |
| AI工具 | 24 |
| 中间格式 | 28 |
| 目标平台 | 18 |
| **总转换路径** | **1610** |

## 本机环境

| 工具 | 路径 |
|------|------|
| Blender 5.1 | D:\rj\KF\JM\blender\blender.exe |
| Godot 4.6.1 | D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe\ |
| UE 5.6 | D:\rj\KF\JM\UE_5.6\ |
| Python 3.10 | %USERPROFILE%\AppData\Local\Programs\Python\Python310\ |

## 使用方式

1. **拖拽转换**: 把3D文件拖到 `拖拽转换.bat` 或桌面 `3D模型转换` 快捷方式
2. **交互菜单**: 双击 `启动转换器.bat`
3. **MCP服务**: 通过 mcp-config.json 注册的MCP工具调用

## 已知问题

- FBX导出时嵌入贴图可能失败(warning: embedding file failed)
- Godot场景UID需要在导入后更新
- Blender 6.0将移除 `Material.use_nodes`
