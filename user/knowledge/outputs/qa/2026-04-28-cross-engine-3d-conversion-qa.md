# Q&A: 跨引擎3D资产转换

## Q: 为什么OBJ文件转出来是全白的？
A: 很多游戏(如TerraTech)导出的OBJ文件缺少UV坐标和材质库。游戏内部用程序化着色器渲染，导出时颜色信息丢失。解决方法是用Blender自动UV展开+程序化材质生成+Cycles烘焙贴图。

## Q: 为什么Blender里看着有颜色，导出GLB就变白了？
A: glTF/GLB格式只支持ImageTexture，不支持Blender的程序化节点(Noise/ColorRamp等)。导出时这些节点被丢弃。必须先用Cycles烘焙把程序化材质"烧"成PNG图片，再用ImageTexture替换节点。

## Q: 怎么把3D模型转到Godot？
A: 三种方式：
1. 拖拽到 `3D模型转换` 快捷方式（最简单）
2. 双击 `启动转换器.bat` 用交互菜单
3. 命令行 `python drag_convert.py "文件路径"`

## Q: 支持哪些格式？
A: .obj .fbx .gltf .glb .dae .abc .usd .usda .usdc .stl .3mf .ply .blend

## Q: 转换完的文件在哪？
A: `\python\Temp\Converted\{模型名}\` 下有GLB(通用)、FBX(UE5)、Albedo/Roughness/Normal贴图。Godot项目在 `\python\Temp\VortexTest\`。

## Q: FBX和GLB选哪个？
A: GLB用于Godot/Web/移动端，FBX用于UE5/Unity/3ds Max。如果不确定，两个都导出。

## Q: 怎么在UE5里用？
A: 把FBX复制到UE5项目的Content目录，在编辑器里右键Import即可。

## Q: Blender 5.1有什么API变化？
A: `import_scene.obj` → `wm.obj_import`，`import_scene.fbx` → `wm.fbx_import`，`Material.use_nodes` 将在6.0移除。
