#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender自动化脚本

用于在Blender中执行自动化操作：
- 导入模型
- 优化拓扑
- 生成材质
- 导出FBX/glTF

用法（在Blender中运行）：
    blender --background --python blender_automation.py -- [args]

或在Blender Python控制台中（安全动态导入）：
    import importlib.util
    spec = importlib.util.spec_from_file_location("blender_automation", "/python/MCP/blender_automation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
"""

import bpy
import sys
import argparse
import json
import importlib.util
from pathlib import Path

# ============================================================
# 安全动态加载
# ============================================================
def safe_load_module(module_name: str, file_path: str):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            print(f"Error: Cannot create module spec for {file_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module {module_name} from {file_path}: {e}")
        return None

# ============================================================
# 配置
# ============================================================
CONFIG = {
    "export_formats": {
        "fbx": {
            "operator": "export_scene.fbx",
            "extension": ".fbx"
        },
        "gltf": {
            "operator": "export_scene.gltf",
            "extension": ".glb"
        },
        "obj": {
            "operator": "export_scene.obj",
            "extension": ".obj"
        }
    }
}

# ============================================================
# 工具函数
# ============================================================
def clear_scene():
    """清理场景"""
    # 删除所有对象
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 清理数据块
    for data in [bpy.data.meshes, bpy.data.materials, bpy.data.textures]:
        for block in data:
            if block.users == 0:
                data.remove(block)

def import_model(file_path: str) -> bool:
    """导入模型"""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    ext = path.suffix.lower()
    
    try:
        if ext == ".obj":
            bpy.ops.import_scene.obj(filepath=str(path))
        elif ext == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(path))
        elif ext in [".glb", ".gltf"]:
            bpy.ops.import_scene.gltf(filepath=str(path))
        elif ext in [".stl"]:
            bpy.ops.import_scene.stl(filepath=str(path))
        else:
            print(f"Error: Unsupported format: {ext}")
            return False
        
        print(f"Imported: {file_path}")
        return True
    except Exception as e:
        print(f"Error importing: {e}")
        return False

def apply_transforms():
    """应用所有变换"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print("Transforms applied")

def generate_pbr_material(name: str = "PBR_Material"):
    """生成PBR材质"""
    # 创建新材质
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 获取 principled BSDF
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    # 设置基础参数
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.0
    
    # 应用到选中对象
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
    
    print(f"Generated material: {name}")
    return mat

def generate_lod_levels():
    """生成LOD级别"""
    selected = bpy.context.selected_objects
    
    for obj in selected:
        if obj.type != 'MESH':
            continue
        
        # 创建LOD0（原始）
        lod0 = obj
        
        # 创建LOD1（50%面数）
        bpy.ops.object.select_all(action='DESELECT')
        lod0.select_set(True)
        bpy.context.view_layer.objects.active = lod0
        bpy.ops.object.duplicate()
        lod1 = bpy.context.active_object
        lod1.name = f"{obj.name}_LOD1"
        
        # 添加Decimate修改器
        decimate = lod1.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = 0.5
        bpy.ops.object.modifier_apply(modifier="Decimate")
        
        # 创建LOD2（25%面数）
        bpy.ops.object.duplicate()
        lod2 = bpy.context.active_object
        lod2.name = f"{obj.name}_LOD2"
        
        decimate2 = lod2.modifiers.new(name="Decimate", type='DECIMATE')
        decimate2.ratio = 0.5
        bpy.ops.object.modifier_apply(modifier="Decimate")
        
        print(f"Generated LODs for: {obj.name}")

def generate_collision():
    """生成碰撞体"""
    selected = bpy.context.selected_objects
    
    for obj in selected:
        if obj.type != 'MESH':
            continue
        
        # 复制对象
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.duplicate()
        
        collision = bpy.context.active_object
        collision.name = f"UCX_{obj.name}"
        
        # 简化网格
        decimate = collision.modifiers.new(name="Decimate", type='DECIMATE')
        decimate.ratio = 0.1
        bpy.ops.object.modifier_apply(modifier="Decimate")
        
        print(f"Generated collision for: {obj.name}")

def export_model(output_path: str, export_fmt: str = "fbx", selected_only: bool = False):
    """导出模型"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if export_fmt not in CONFIG["export_formats"]:
        print(f"Error: Unsupported format: {export_fmt}")
        return False
    
    export_config = CONFIG["export_formats"][export_fmt]
    
    try:
        if selected_only:
            bpy.ops.object.select_all(action='DESELECT')
            # 选择所有网格对象
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH':
                    obj.select_set(True)
        else:
            bpy.ops.object.select_all(action='SELECT')
        
        # 导出
        if export_fmt == "fbx":
            bpy.ops.export_scene.fbx(
                filepath=str(path),
                use_selection=True,
                global_scale=1.0,
                apply_unit_scale=True,
                apply_scale_options='FBX_SCALE_UNITS',
                axis_forward='-Z',
                axis_up='Y',
                bake_space_transform=True,
                object_types={'MESH', 'ARMATURE'},
                use_mesh_modifiers=True,
                mesh_smooth_type='OFF',
                add_leaf_bones=False,
                path_mode='AUTO',
                embed_textures=False
            )
        elif export_fmt == "gltf":
            bpy.ops.export_scene.gltf(
                filepath=str(path),
                use_selection=True,
                export_format='GLB',
                export_yup=True
            )
        elif export_fmt == "obj":
            bpy.ops.export_scene.obj(
                filepath=str(path),
                use_selection=True,
                axis_forward='-Z',
                axis_up='Y'
            )
        
        print(f"Exported to: {output_path}")
        return True
    except Exception as e:
        print(f"Error exporting: {e}")
        return False

def optimize_topology():
    """优化拓扑"""
    selected = bpy.context.selected_objects
    
    for obj in selected:
        if obj.type != 'MESH':
            continue
        
        # 进入编辑模式
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        # 选择所有
        bpy.ops.mesh.select_all(action='SELECT')
        
        # 三角面转四边面
        bpy.ops.mesh.tris_convert_to_quads()
        
        # 返回对象模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print(f"Optimized topology for: {obj.name}")

def main():
    """主函数"""
    # 解析参数
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    
    parser = argparse.ArgumentParser(description='Blender Automation')
    parser.add_argument('--action', required=True, choices=[
        'import', 'export', 'clear', 'apply_transforms', 
        'generate_material', 'generate_lod', 'generate_collision',
        'optimize'
    ])
    parser.add_argument('--input', help='Input file path')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', default='fbx', help='Export format')
    parser.add_argument('--selected-only', action='store_true', help='Export selected only')
    
    args = parser.parse_args(argv)
    
    # 执行操作
    if args.action == 'clear':
        clear_scene()
    elif args.action == 'import':
        if args.input:
            import_model(args.input)
    elif args.action == 'export':
        if args.output:
            export_model(args.output, args.format, args.selected_only)
    elif args.action == 'apply_transforms':
        apply_transforms()
    elif args.action == 'generate_material':
        generate_pbr_material()
    elif args.action == 'generate_lod':
        generate_lod_levels()
    elif args.action == 'generate_collision':
        generate_collision()
    elif args.action == 'optimize':
        optimize_topology()

if __name__ == "__main__":
    main()
