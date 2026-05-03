#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据照片创建3D角色
确保每张照片对应一个角色
"""

import bpy
import os
from pathlib import Path

OUTPUT_DIR = Path("/python/Output/Characters/3D")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_DIR = Path("F:/照片/项目")

# 照片列表
photos = sorted([f for f in PHOTO_DIR.iterdir() if f.suffix.lower() in ['.jpg', '.png']])

# 角色配置
CHARACTERS = [
    {
        "name": "群主",
        "title": "研究与策划",
        "pose": "presenting",
        "color": "#0984e3",
        "outfit": "#1e3a5f"
    },
    {
        "name": "漫改负责人", 
        "title": "漫画改编",
        "pose": "drawing",
        "color": "#e056fd",
        "outfit": "#4a2c6a"
    },
    {
        "name": "思想指导员",
        "title": "群管理员",
        "pose": "guiding",
        "color": "#00cec9",
        "outfit": "#1a4a5c"
    }
]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    return (1, 1, 1)

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_head(photo_path):
    """创建头部并应用照片纹理"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.3))
    head = bpy.context.active_object
    head.name = "Head"
    head.scale = (0.95, 1.0, 1.05)
    
    sub_mod = head.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    # 创建材质
    mat = bpy.data.materials.new(name="FaceMaterial")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    # 纹理节点
    tex_node = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(photo_path):
        tex_image = bpy.data.images.load(str(photo_path))
        tex_node.image = tex_image
    
    coord_node = nodes.new(type='ShaderNodeTexCoord')
    mapping_node = nodes.new(type='ShaderNodeMapping')
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = 0
    bsdf.inputs['Roughness'].default_value = 0.4
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    links.new(coord_node.outputs['UV'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])
    links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    head.data.materials.append(mat)
    
    # UV展开
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return head

def create_body(outfit_color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0, 0, 1.5))
    body = bpy.context.active_object
    body.name = "Body"
    body.scale = (0.6, 0.45, 0.8)
    
    sub_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    mat = bpy.data.materials.new(name="BodyMat")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = outfit_color + (1,)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.3
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    body.data.materials.append(mat)
    return body

def create_arm(location, side, outfit_color):
    # 上臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.7, location=location)
    upper_arm = bpy.context.active_object
    upper_arm.name = f"UpperArm_{side}"
    upper_arm.rotation_euler.x = 1.5708
    
    sub_mod = upper_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = bpy.data.materials.new(name=f"ArmMat_{side}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = outfit_color + (1,)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.3
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    upper_arm.data.materials.append(mat)
    
    # 前臂
    fore_loc = (location[0], location[1], location[2] - 0.35)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.65, location=fore_loc)
    fore_arm = bpy.context.active_object
    fore_arm.name = f"ForeArm_{side}"
    fore_arm.rotation_euler.x = 1.5708
    
    sub_mod = fore_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    fore_arm.data.materials.append(mat)
    
    # 手
    hand_loc = (location[0], location[1], location[2] - 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=hand_loc)
    hand = bpy.context.active_object
    hand.name = f"Hand_{side}"
    hand.scale = (1, 0.8, 0.7)
    
    sub_mod = hand.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    hand_mat = bpy.data.materials.new(name=f"HandMat_{side}")
    hand_mat.use_nodes = True
    nodes = hand_mat.node_tree.nodes
    links = hand_mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.85, 0.65, 0.5) + (1,)
    bsdf.inputs['Metallic'].default_value = 0
    bsdf.inputs['Roughness'].default_value = 0.3
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    hand.data.materials.append(hand_mat)
    
    return upper_arm, fore_arm, hand

def create_leg(location, side, outfit_color):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.8, location=location)
    thigh = bpy.context.active_object
    thigh.name = f"Thigh_{side}"
    thigh.rotation_euler.x = 1.5708
    
    sub_mod = thigh.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = bpy.data.materials.new(name=f"LegMat_{side}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = outfit_color + (1,)
    bsdf.inputs['Metallic'].default_value = 0.05
    bsdf.inputs['Roughness'].default_value = 0.4
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    thigh.data.materials.append(mat)
    
    calf_loc = (location[0], location[1], location[2] - 0.4)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.75, location=calf_loc)
    calf = bpy.context.active_object
    calf.name = f"Calf_{side}"
    calf.rotation_euler.x = 1.5708
    
    sub_mod = calf.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    calf.data.materials.append(mat)
    
    foot_loc = (location[0], location[1], location[2] - 0.77)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.3, location=foot_loc)
    foot = bpy.context.active_object
    foot.name = f"Foot_{side}"
    foot.rotation_euler.x = 0.3
    
    sub_mod = foot.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    shoe_mat = bpy.data.materials.new(name=f"ShoeMat_{side}")
    shoe_mat.use_nodes = True
    nodes = shoe_mat.node_tree.nodes
    links = shoe_mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1) + (1,)
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.4
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    foot.data.materials.append(shoe_mat)
    
    return thigh, calf, foot

def create_pose(pose_name):
    if pose_name == "presenting":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -0.4
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 0.4
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.25
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.25
    elif pose_name == "drawing":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -1.3
        bpy.data.objects["ForeArm_R"].rotation_euler.x = 1.1
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.7
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 0.9
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.4
    elif pose_name == "guiding":
        bpy.data.objects["UpperArm_R"].rotation_euler.x = 0.6
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.25
        bpy.data.objects["ForeArm_R"].rotation_euler.x = -0.6
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.35

def create_halo(emission_color):
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

def setup_scene():
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.rotation_euler = (1.1, 0, 0.785)
    bpy.context.scene.camera = camera
    
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 3
    sun.rotation_euler = (0.785, 0.785, 0)
    
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.1, 0.15, 0.2, 1)
    
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -0.1))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    mat = bpy.data.materials.new(name="GroundMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.2, 0.25, 0.3) + (1,)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.8
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    ground.data.materials.append(mat)

def create_character(character, photo_path):
    """为每个角色创建3D模型"""
    clear_scene()
    
    outfit_color = hex_to_rgb(character['outfit'])
    
    create_body(outfit_color)
    create_head(str(photo_path))
    
    create_arm((0.5, 0, 1.8), 'R', outfit_color)
    create_arm((-0.5, 0, 1.8), 'L', outfit_color)
    
    create_leg((0.2, 0.15, 0.5), 'R', outfit_color)
    create_leg((-0.2, 0.15, 0.5), 'L', outfit_color)
    
    create_pose(character['pose'])
    create_halo(character['color'])
    
    setup_scene()
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True
    
    blend_path = OUTPUT_DIR / f"Character_{character['name']}.blend"
    bpy.ops.wm.save_mainfile(filepath=str(blend_path))
    
    render_path = OUTPUT_DIR / f"Character_{character['name']}.png"
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)
    
    print(f"✅ {character['name']} - 使用照片: {photo_path.name}")
    print(f"   文件: {blend_path}")

def main():
    print("="*60)
    print("🌟 根据照片创建3D角色")
    print("="*60)
    
    print(f"\n找到 {len(photos)} 张照片:")
    for i, photo in enumerate(photos):
        print(f"   {i+1}. {photo.name}")
    
    print("\n角色配置:")
    for i, char in enumerate(CHARACTERS):
        print(f"   {i+1}. {char['name']} - {char['title']}")
    
    # 一一对应创建角色
    for i, (character, photo) in enumerate(zip(CHARACTERS, photos)):
        print(f"\n🎨 创建角色 {i+1}: {character['name']}")
        print(f"   使用照片: {photo.name}")
        create_character(character, photo)
    
    print("\n" + "="*60)
    print("🎉 所有角色创建完成!")
    print("="*60)

if __name__ == "__main__":
    main()
