#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用用户提供的照片生成3D角色
将照片作为纹理贴图应用到3D模型上
"""

import bpy
import os
from pathlib import Path

OUTPUT_DIR = Path("/python/Output/Characters/3D")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 用户照片路径
PHOTO_DIR = Path("F:/照片/项目")

CONTRIBUTORS = [
    {
        "id": 1,
        "name": "群主",
        "title": "研究与策划",
        "description": "负责研究并且制作小说的PPT以及各种东西，不是小说作者",
        "photo": "b_82e96bfed079a79281baf77ac9e002cf.jpg",
        "pose": "presenting",
        "color_theme": ["#2d3436", "#636e72", "#b2bec3", "#0984e3"],
        "emission_color": "#0984e3",
        "outfit_color": "#1e3a5f"
    },
    {
        "id": 2,
        "name": "漫改负责人",
        "title": "漫画改编",
        "description": "负责小说的漫画改编工作，将文字转化为视觉艺术",
        "photo": "b_a6ba05cb237229bf98c48759f26e412e.jpg",
        "pose": "drawing",
        "color_theme": ["#2d1f3d", "#5b2c6f", "#9b59b6", "#e056fd"],
        "emission_color": "#e056fd",
        "outfit_color": "#4a2c6a"
    },
    {
        "id": 3,
        "name": "思想指导员",
        "title": "群管理员",
        "description": "群的思想指导员，引领团队方向，激发创作灵感",
        "photo": "b_b2887f61b605afbd167ea0b542de8686.jpg",
        "pose": "guiding",
        "color_theme": ["#1e272e", "#3d5af1", "#00cec9", "#81ecec"],
        "emission_color": "#00cec9",
        "outfit_color": "#1a4a5c"
    }
]

def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def hex_to_rgb(hex_color):
    """转换颜色"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    return (1, 1, 1)

def create_material_with_texture(name, texture_path, color=(1,1,1), metallic=0.0, roughness=0.5):
    """创建带纹理的材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 删除所有现有节点
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    # 创建纹理节点
    tex_node = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(texture_path):
        tex_image = bpy.data.images.load(str(texture_path))
        tex_node.image = tex_image
        tex_node.interpolation = 'Closest'
    
    # 创建映射节点
    mapping_node = nodes.new(type='ShaderNodeMapping')
    
    # 创建纹理坐标节点
    coord_node = nodes.new(type='ShaderNodeTexCoord')
    
    # 创建Principled BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    # 创建输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # 连接节点
    links.new(coord_node.outputs['UV'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])
    links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_body(outfit_color):
    """创建身体"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0, 0, 1.5))
    body = bpy.context.active_object
    body.name = "Body"
    body.scale = (0.6, 0.45, 0.8)
    
    sub_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    # 添加UV映射
    uv_mod = body.modifiers.new(name="UVMap", type='UV_PROJECT')
    uv_mod.projector_count = 4
    
    mat = create_material("Clothes", (0.1, 0.1, 0.1), metallic=0.1, roughness=0.3)
    body.data.materials.append(mat)
    
    return body

def create_head(photo_path):
    """创建头部并应用照片纹理"""
    # 头部主体
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.3))
    head = bpy.context.active_object
    head.name = "Head"
    head.scale = (0.95, 1.0, 1.05)
    
    sub_mod = head.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    # 创建带照片纹理的材质
    mat = create_material_with_texture("FaceTexture", photo_path, (0.8, 0.6, 0.5), metallic=0, roughness=0.3)
    head.data.materials.append(mat)
    
    # 添加UV展开
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return head

def create_arm(location, side, outfit_color):
    """创建手臂"""
    # 上臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.7, location=(location[0], location[1], location[2]))
    upper_arm = bpy.context.active_object
    upper_arm.name = f"UpperArm_{side}"
    upper_arm.rotation_euler.x = 1.5708
    
    sub_mod = upper_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Clothes_{side}", outfit_color, metallic=0.1, roughness=0.3)
    upper_arm.data.materials.append(mat)
    
    # 前臂
    fore_arm_loc = (location[0], location[1], location[2] - 0.35)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.65, location=fore_arm_loc)
    fore_arm = bpy.context.active_object
    fore_arm.name = f"ForeArm_{side}"
    fore_arm.rotation_euler.x = 1.5708
    
    sub_mod = fore_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Clothes_Fore_{side}", outfit_color, metallic=0.1, roughness=0.3)
    fore_arm.data.materials.append(mat)
    
    # 手
    hand_loc = (location[0], location[1], location[2] - 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=hand_loc)
    hand = bpy.context.active_object
    hand.name = f"Hand_{side}"
    hand.scale = (1, 0.8, 0.7)
    
    sub_mod = hand.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Skin_Hand_{side}", (0.8, 0.6, 0.5), metallic=0, roughness=0.3)
    hand.data.materials.append(mat)
    
    return upper_arm, fore_arm, hand

def create_leg(location, side, outfit_color):
    """创建腿"""
    # 大腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=location)
    thigh = bpy.context.active_object
    thigh.name = f"Thigh_{side}"
    thigh.rotation_euler.x = 1.5708
    
    sub_mod = thigh.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Trousers_{side}", outfit_color, metallic=0.05, roughness=0.4)
    thigh.data.materials.append(mat)
    
    # 小腿
    calf_loc = (location[0], location[1], location[2] - 0.4)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.75, location=calf_loc)
    calf = bpy.context.active_object
    calf.name = f"Calf_{side}"
    calf.rotation_euler.x = 1.5708
    
    sub_mod = calf.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Trousers_Calf_{side}", outfit_color, metallic=0.05, roughness=0.4)
    calf.data.materials.append(mat)
    
    # 脚
    foot_loc = (location[0], location[1], location[2] - 0.77)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.3, location=foot_loc)
    foot = bpy.context.active_object
    foot.name = f"Foot_{side}"
    foot.rotation_euler.x = 0.3
    
    sub_mod = foot.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Shoes_{side}", (0.1, 0.1, 0.1), metallic=0.3, roughness=0.4)
    foot.data.materials.append(mat)
    
    return thigh, calf, foot

def create_material(name, color, metallic=0.0, roughness=0.5, emission_color=(0,0,0), emission_strength=0):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 删除所有现有节点
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    # 创建Principled BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color + (1,)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    if emission_strength > 0:
        bsdf.inputs['Emission'].default_value = emission_color + (1,)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    # 创建输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # 连接节点
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_pose(pose_name):
    """设置角色姿势"""
    if pose_name == "presenting":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -0.5
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 0.5
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.3
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.3
    elif pose_name == "drawing":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -1.2
        bpy.data.objects["ForeArm_R"].rotation_euler.x = 1.2
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.8
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 1.0
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.5
    elif pose_name == "guiding":
        bpy.data.objects["UpperArm_R"].rotation_euler.x = 0.5
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.3
        bpy.data.objects["ForeArm_R"].rotation_euler.x = -0.5
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.4

def create_halo(emission_color):
    """创建发光光环"""
    bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.05, location=(0, 0, 2.5))
    halo = bpy.context.active_object
    halo.name = "Halo"
    
    mat = bpy.data.materials.new(name="HaloMat")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = hex_to_rgb(emission_color) + (1,)
    emission.inputs['Strength'].default_value = 3.0
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    halo.data.materials.append(mat)
    mat.blend_method = 'BLEND'

def create_accessory(contributor):
    """创建角色配饰"""
    pose = contributor['pose']
    emission_color = contributor['emission_color']
    
    if pose == "presenting":
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0.7, -0.1, 0.5))
        folder = bpy.context.active_object
        folder.name = "DocumentFolder"
        folder.scale = (1.5, 0.8, 0.3)
        
        mat = create_material("FolderMat", hex_to_rgb(emission_color), metallic=0.2, roughness=0.3)
        folder.data.materials.append(mat)
        
    elif pose == "drawing":
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(-0.6, -0.1, 1.0))
        canvas = bpy.context.active_object
        canvas.name = "Canvas"
        canvas.scale = (1.2, 0.1, 1.5)
        
        mat = create_material("CanvasMat", (0.95, 0.9, 0.85), metallic=0, roughness=0.8)
        canvas.data.materials.append(mat)
        
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.4, location=(0.4, -0.05, 1.2))
        brush = bpy.context.active_object
        brush.name = "Brush"
        brush.rotation_euler.x = 1.5708
        brush.rotation_euler.z = 0.5
        
        mat = create_material("BrushMat", (0.3, 0.2, 0.1), metallic=0.1, roughness=0.5)
        brush.data.materials.append(mat)
        
    elif pose == "guiding":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0.6, -0.05, 1.8))
        orb = bpy.context.active_object
        orb.name = "ThoughtOrb"
        
        mat = bpy.data.materials.new(name="OrbMat")
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        for node in nodes:
            nodes.remove(node)
        
        emission = nodes.new(type='ShaderNodeEmission')
        emission.inputs['Color'].default_value = hex_to_rgb(emission_color) + (1,)
        emission.inputs['Strength'].default_value = 4.0
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        orb.data.materials.append(mat)
        mat.blend_method = 'BLEND'

def setup_scene():
    """设置场景"""
    # 相机
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.rotation_euler = (1.1, 0, 0.785)
    bpy.context.scene.camera = camera
    
    # 灯光
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 3
    sun.rotation_euler = (0.785, 0.785, 0)
    
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.1, 0.15, 0.2, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1.0
    
    # 地面
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.1))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    mat = create_material("GroundMat", (0.2, 0.25, 0.3), metallic=0.1, roughness=0.8)
    ground.data.materials.append(mat)

def generate_character(contributor):
    """生成角色"""
    clear_scene()
    
    outfit_color = hex_to_rgb(contributor['outfit_color'])
    photo_path = PHOTO_DIR / contributor['photo']
    
    # 创建身体部件
    create_body(outfit_color)
    create_head(str(photo_path))
    
    # 创建手臂
    create_arm((0.5, 0, 1.8), 'R', outfit_color)
    create_arm((-0.5, 0, 1.8), 'L', outfit_color)
    
    # 创建腿
    create_leg((0.2, 0.15, 0.5), 'R', outfit_color)
    create_leg((-0.2, 0.15, 0.5), 'L', outfit_color)
    
    # 设置姿势
    create_pose(contributor['pose'])
    
    # 创建发光光环
    create_halo(contributor['emission_color'])
    
    # 创建配饰
    create_accessory(contributor)
    
    # 设置场景
    setup_scene()
    
    # 设置渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True
    
    # 保存文件
    blend_path = OUTPUT_DIR / f"Photo_{contributor['name']}.blend"
    bpy.ops.wm.save_mainfile(filepath=str(blend_path))
    
    # 渲染图片
    render_path = OUTPUT_DIR / f"Photo_{contributor['name']}.png"
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)
    
    print(f"✅ 生成角色 {contributor['name']} 完成!")
    print(f"   使用照片: {photo_path}")
    print(f"   Blender文件: {blend_path}")
    print(f"   渲染图片: {render_path}")

def main():
    """主函数"""
    print("="*60)
    print("🌟 使用照片生成3D角色")
    print("="*60)
    
    for contributor in CONTRIBUTORS:
        print(f"\n🎨 生成角色: {contributor['name']}")
        print(f"   角色: {contributor['title']}")
        print(f"   照片: {contributor['photo']}")
        generate_character(contributor)
    
    print("\n" + "="*60)
    print("🎉 所有角色生成完成!")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
