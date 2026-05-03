# 跨引擎3D资产转换

> 3D模型在不同游戏引擎/DCC/CAD之间迁移的完整知识体系

## 核心问题
3D资产在不同软件间转换时，材质、动画、骨骼、UV等信息容易丢失。

## 解决方案架构
```
源文件 → Blender(统一中间层) → 烘焙贴图 → glTF/FBX → 目标引擎
```

## 关键概念
- [[glTF烘焙贴图]] - 程序化材质→图片贴图的核心技术
- [[3D中间格式对比]] - 不同格式的能力和选择策略
- [[Blender Python API]] - Blender自动化脚本的关键API

## 工具位置
- 拖拽转换: `\python\storage\mcp\JM\拖拽转换.bat`
- 桌面快捷方式: `3D模型转换.lnk`
- 交互菜单: `\python\storage\mcp\JM\启动转换器.bat`

## 支持的转换路径
1610条路径，覆盖34个3D引擎、20个2D引擎、12个Web引擎、20个DCC工具、18个CAD/BIM软件等。详见 `engine_converter_extended.py`。

## 实测案例
- TerraTech Vortex_V1_Suppression.mesh.obj → Godot (1.7s, 484KB GLB, 蓝青色PBR材质)
- test_cube.stl → Godot (1.6s, 136.5KB GLB)

## 关联
- [[glTF烘焙贴图]]
- [[3D中间格式对比]]
- [[Blender Python API]]
