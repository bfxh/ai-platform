# Blender Python API

> Blender自动化脚本的关键API变化

## Blender 5.x API变化 (vs 4.x)

| 旧API (4.x) | 新API (5.x) | 说明 |
|-------------|-------------|------|
| `bpy.ops.import_scene.obj()` | `bpy.ops.wm.obj_import()` | OBJ导入 |
| `bpy.ops.import_scene.fbx()` | `bpy.ops.wm.fbx_import()` | FBX导入 |
| `bpy.ops.import_mesh.stl()` | `bpy.ops.wm.stl_import()` | STL导入 |
| `Material.use_nodes` | 即将移除 | Blender 6.0弃用 |

## 烘焙流程
```python
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 1

tex_node = nodes.new('ShaderNodeTexImage')
tex_node.image = target_image
nodes.active = tex_node

bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
```

## UV展开
```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15)
bpy.ops.object.mode_set(mode='OBJECT')
```

## glTF导出
```python
bpy.ops.export_scene.gltf(
    filepath=dst,
    export_format='GLB',
    export_materials='EXPORT',
)
```

## 关联
- [[glTF烘焙贴图]]
- [[跨引擎资产转换]]
