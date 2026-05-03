# glTF烘焙贴图

> 跨引擎3D资产转换的核心技术

## 问题
glTF/GLB格式只支持ImageTexture节点，不支持程序化材质节点(Noise/ColorRamp/Mix/Bump等)。直接导出GLB时，程序化材质被丢弃，模型显示为全白。

## 解决方案
1. 在Blender中创建程序化材质(Noise+ColorRamp+Principled BSDF)
2. 切换到Cycles渲染引擎
3. 创建空白ImageTexture节点
4. 用 `bpy.ops.object.bake()` 烘焙到图片:
   - `type='DIFFUSE', pass_filter={'COLOR'}` → Albedo贴图
   - `type='ROUGHNESS'` → Roughness贴图
   - `type='NORMAL'` → Normal贴图
5. 用烘焙后的ImageTexture替换程序化节点
6. 导出GLB，贴图自动嵌入

## 效果对比
- 无烘焙: 9.9 KB GLB (全白)
- 有烘焙: 484 KB GLB (带PBR贴图)

## 代码模式
```python
bpy.context.scene.render.engine = 'CYCLES'
tex_node.image = albedo_img
nodes.active = tex_node
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, width=512, height=512)
```

## 关联
- [[3D中间格式对比]]
- [[Blender Python API]]
- [[跨引擎资产转换]]
