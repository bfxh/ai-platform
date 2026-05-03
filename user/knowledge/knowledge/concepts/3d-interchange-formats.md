# 3D中间格式对比

> 跨引擎转换的桥梁格式选择

## 格式矩阵

| 格式 | 类型 | 所有者 | 支持内容 | 引擎兼容 |
|------|------|--------|---------|---------|
| FBX | 专有 | Autodesk | 网格+骨骼+动画+材质引用 | UE5/Unity/Blender/Maya |
| glTF/GLB | 开放标准 | Khronos | 网格+骨骼+动画+PBR材质+贴图 | Godot/Web/Bevy/Defold |
| USD | 开放标准 | Pixar/OpenUSD | 完整场景+合成+图层 | UE5/Omniverse/Houdini/Maya |
| OBJ | 开放 | Wavefront | 仅网格+UV(无动画) | 通用(静态模型) |
| ABC | 开放标准 | Sony/ILM | 顶点动画缓存+曲线 | Maya/Houdini/UE5 |
| DAE | 开放标准 | Khronos | 网格+骨骼+动画+材质 | Godot/Blender |
| STEP | ISO标准 | ISO 10303 | 精确BRep/NURBS | CAD/BIM |
| IFC | ISO标准 | buildingSMART | 建筑数据+几何 | BIM/ArchViz |

## 选择策略

- **游戏引擎间互转**: FBX (UE5/Unity) 或 glTF (Godot/Web)
- **DCC→游戏引擎**: FBX+USD (Maya/Houdini→UE5) 或 glTF (Blender→Godot)
- **CAD/BIM→游戏引擎**: Datasmith(UE5) 或 IFC+FBX
- **Web/移动端**: glTF/GLB (唯一选择)
- **数字孪生**: USD (Omniverse管线)

## 关联
- [[glTF烘焙贴图]]
- [[跨引擎资产转换]]
