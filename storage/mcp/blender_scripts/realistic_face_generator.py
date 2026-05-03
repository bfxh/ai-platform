#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业级3D人物面部重建
使用照片进行逼真的面部建模
"""

import bpy
import os
from pathlib import Path

OUTPUT_DIR = Path("/python/Output/Characters/3D")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_DIR = Path("F:/照片/项目")

CONTRIBUTORS = [
    {
        "id": 1,
        "name": "群主",
        "title": "研究与策划",
        "photo": "b_82e96bfed079a79281baf77ac9e002cf.jpg",
        "pose": "presenting",
        "emission_color": "#0984e3",
        "outfit_color": "#1e3a5f"
    },
    {
        "id": 2,
        "name": "漫改负责人",
        "title": "漫画改编",
        "photo": "b_a6ba05cb237229bf98c48759f26e412e.jpg",
        "pose": "drawing",
        "emission_color": "#e056fd",
        "outfit_color": "#4a2c6a"
    },
    {
        "id": 3,
        "name": "思想指导员",
        "title": "群管理员",
        "photo": "b_b2887f61b605afbd167ea0b542de8686.jpg",
        "pose": "guiding",
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

def create_material(name, color, metallic=0.0, roughness=0.5, emission_color=(0,0,0), emission_strength=0):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color + (1,)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    if emission_strength > 0:
        bsdf.inputs['Emission'].default_value = emission_color + (1,)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_face_material(texture_path):
    """创建面部材质"""
    mat = bpy.data.materials.new(name="FaceMaterial")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in nodes:
        nodes.remove(node)
    
    # 纹理节点
    tex_node = nodes.new(type='ShaderNodeTexImage')
    if os.path.exists(texture_path):
        tex_image = bpy.data.images.load(str(texture_path))
        tex_node.image = tex_image
        tex_node.interpolation = 'Linear'
    
    # 纹理坐标
    coord_node = nodes.new(type='ShaderNodeTexCoord')
    
    # 映射节点
    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.inputs['Scale'].default_value = (1, 1, 1)
    
    # BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.4
    
    # 输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # 连接
    links.new(coord_node.outputs['UV'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], tex_node.inputs['Vector'])
    links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_advanced_head(photo_path):
    """创建高级头部模型"""
    # 创建基础头部形状
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.3))
    head = bpy.context.active_object
    head.name = "Head"
    
    # 调整头部形状
    head.scale = (0.95, 1.0, 1.1)
    
    # 添加细分
    sub_mod = head.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    # 添加面部材质
    mat = create_face_material(photo_path)
    head.data.materials.append(mat)
    
    # UV展开
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 创建眼睛
    create_detailed_eyes()
    
    # 创建头发
    create_hair()
    
    return head

def create_detailed_eyes():
    """创建精细的眼睛"""
    # 左眼
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(-0.22, -0.1, 2.82))
    eye_l = bpy.context.active_object
    eye_l.name = "Eye_L"
    eye_l.scale = (1.3, 0.9, 0.7)
    
    mat = create_material("EyeWhite", (0.95, 0.95, 0.95))
    eye_l.data.materials.append(mat)
    
    # 虹膜
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(-0.22, -0.1, 2.84))
    iris_l = bpy.context.active_object
    iris_l.name = "Iris_L"
    
    mat = create_material("Iris", (0.25, 0.35, 0.5))
    iris_l.data.materials.append(mat)
    
    # 瞳孔
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(-0.22, -0.1, 2.85))
    pupil_l = bpy.context.active_object
    pupil_l.name = "Pupil_L"
    
    mat = create_material("Pupil", (0, 0, 0))
    pupil_l.data.materials.append(mat)
    
    # 右眼
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(0.22, -0.1, 2.82))
    eye_r = bpy.context.active_object
    eye_r.name = "Eye_R"
    eye_r.scale = (1.3, 0.9, 0.7)
    
    eye_r.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(0.22, -0.1, 2.84))
    iris_r = bpy.context.active_object
    iris_r.name = "Iris_R"
    
    iris_r.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(0.22, -0.1, 2.85))
    pupil_r = bpy.context.active_object
    pupil_r.name = "Pupil_R"
    
    pupil_r.data.materials.append(mat)

def create_hair():
    """创建头发"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0, 0, 2.45))
    hair = bpy.context.active_object
    hair.name = "Hair"
    hair.scale = (0.96, 0.96, 1.2)
    
    sub_mod = hair.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    mat = create_material("Hair", (0.25, 0.2, 0.15), metallic=0.0, roughness=0.3)
    hair.data.materials.append(mat)

def create_body(outfit_color):
    """创建身体"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0, 0, 1.4))
    body = bpy.context.active_object
    body.name = "Body"
    body.scale = (0.55, 0.4, 0.85)
    
    sub_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 3
    
    mat = create_material("BodyClothes", outfit_color, metallic=0.1, roughness=0.3)
    body.data.materials.append(mat)
    
    return body

def create_arm(location, side, outfit_color):
    """创建手臂"""
    # 上臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.7, location=location)
    upper_arm = bpy.context.active_object
    upper_arm.name = f"UpperArm_{side}"
    upper_arm.rotation_euler.x = 1.5708
    
    sub_mod = upper_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"ArmClothes_{side}", outfit_color, metallic=0.1, roughness=0.3)
    upper_arm.data.materials.append(mat)
    
    # 前臂
    fore_loc = (location[0], location[1], location[2] - 0.35)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.65, location=fore_loc)
    fore_arm = bpy.context.active_object
    fore_arm.name = f"ForeArm_{side}"
    fore_arm.rotation_euler.x = 1.5708
    
    sub_mod = fore_arm.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    fore_arm.data.materials.append(mat)
    
    # 手
    hand_loc = (location[0], location[1], location[2] - 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=hand_loc)
    hand = bpy.context.active_object
    hand.name = f"Hand_{side}"
    hand.scale = (1, 0.75, 0.65)
    
    sub_mod = hand.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"HandSkin_{side}", (0.85, 0.65, 0.5), metallic=0, roughness=0.3)
    hand.data.materials.append(mat)
    
    return upper_arm, fore_arm, hand

def create_leg(location, side, outfit_color):
    """创建腿"""
    # 大腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.17, depth=0.85, location=location)
    thigh = bpy.context.active_object
    thigh.name = f"Thigh_{side}"
    thigh.rotation_euler.x = 1.5708
    
    sub_mod = thigh.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Pants_{side}", outfit_color, metallic=0.05, roughness=0.4)
    thigh.data.materials.append(mat)
    
    # 小腿
    calf_loc = (location[0], location[1], location[2] - 0.42)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=0.78, location=calf_loc)
    calf = bpy.context.active_object
    calf.name = f"Calf_{side}"
    calf.rotation_euler.x = 1.5708
    
    sub_mod = calf.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    calf.data.materials.append(mat)
    
    # 脚
    foot_loc = (location[0], location[1], location[2] - 0.8)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.32, location=foot_loc)
    foot = bpy.context.active_object
    foot.name = f"Foot_{side}"
    foot.rotation_euler.x = 0.3
    
    sub_mod = foot.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    
    mat = create_material(f"Shoes_{side}", (0.15, 0.15, 0.2), metallic=0.3, roughness=0.4)
    foot.data.materials.append(mat)
    
    return thigh, calf, foot

def create_pose(pose_name):
    """设置姿势"""
    if pose_name == "presenting":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -0.4
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 0.4
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.25
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.25
        bpy.data.objects["UpperArm_R"].rotation_euler.x = -0.2
        bpy.data.objects["UpperArm_L"].rotation_euler.x = -0.2
    elif pose_name == "drawing":
        bpy.data.objects["ForeArm_R"].rotation_euler.z = -1.3
        bpy.data.objects["ForeArm_R"].rotation_euler.x = 1.1
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.7
        bpy.data.objects["ForeArm_L"].rotation_euler.z = 0.9
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.4
        bpy.data.objects["UpperArm_L"].rotation_euler.x = -0.3
    elif pose_name == "guiding":
        bpy.data.objects["UpperArm_R"].rotation_euler.x = 0.6
        bpy.data.objects["UpperArm_R"].rotation_euler.z = 0.25
        bpy.data.objects["ForeArm_R"].rotation_euler.x = -0.6
        bpy.data.objects["UpperArm_L"].rotation_euler.z = -0.35
        bpy.data.objects["UpperArm_L"].rotation_euler.x = -0.2

def create_halo(emission_color):
    """创建发光光环"""
    bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.06, location=(0, 0, 2.6))
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
    emission.inputs['Strength'].default_value = 3.5
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    
    halo.data.materials.append(mat)
    mat.blend_method = 'BLEND'

def create_accessory(contributor):
    """创建配饰"""
    pose = contributor['pose']
    emission_color = contributor['emission_color']
    
    if pose == "presenting":
        # 文件夹
        bpy.ops.mesh.primitive_cube_add(size=0.28, location=(0.75, -0.12, 0.45))
        folder = bpy.context.active_object
        folder.name = "DocumentFolder"
        folder.scale = (1.6, 0.75, 0.25)
        
        mat = create_material("FolderMat", hex_to_rgb(emission_color), metallic=0.2, roughness=0.3)
        folder.data.materials.append(mat)
        
    elif pose == "drawing":
        # 画板
        bpy.ops.mesh.primitive_cube_add(size=0.38, location=(-0.65, -0.1, 0.95))
        canvas = bpy.context.active_object
        canvas.name = "Canvas"
        canvas.scale = (1.3, 0.08, 1.6)
        
        mat = create_material("CanvasMat", (0.93, 0.88, 0.82), metallic=0, roughness=0.85)
        canvas.data.materials.append(mat)
        
        # 画笔
        bpy.ops.mesh.primitive_cylinder_add(radius=0.018, depth=0.38, location=(0.42, -0.06, 1.15))
        brush = bpy.context.active_object
        brush.name = "Brush"
        brush.rotation_euler.x = 1.5708
        brush.rotation_euler.z = 0.45
        
        mat = create_material("BrushMat", (0.35, 0.25, 0.15), metallic=0.1, roughness=0.5)
        brush.data.materials.append(mat)
        
    elif pose == "guiding":
        # 思想光球
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(0.62, -0.06, 1.75))
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
        emission.inputs['Strength'].default_value = 4.5
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        orb.data.materials.append(mat)
        mat.blend_method = 'BLEND'

def setup_scene():
    """设置场景"""
    # 相机
    bpy.ops.object.camera_add(location=(5.5, -5.5, 3.2))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.rotation_euler = (1.05, 0, 0.785)
    bpy.context.scene.camera = camera
    
    # 主灯光
    bpy.ops.object.light_add(type='SUN', location=(6, -6, 9))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 3.5
    sun.rotation_euler = (0.785, 0.785, 0)
    
    # 补光
    bpy.ops.object.light_add(type='AREA', location=(-3, -2, 4))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 200
    fill_light.scale = (3, 3, 1)
    
    # 环境
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.12, 0.18, 1)
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 1.0
    
    # 地面
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.12))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    mat = create_material("GroundMat", (0.18, 0.22, 0.28), metallic=0.1, roughness=0.85)
    ground.data.materials.append(mat)

def generate_character(contributor):
    """生成角色"""
    clear_scene()
    
    outfit_color = hex_to_rgb(contributor['outfit_color'])
    photo_path = PHOTO_DIR / contributor['photo']
    
    # 创建身体部件
    create_body(outfit_color)
    create_advanced_head(str(photo_path))
    
    # 创建手臂
    create_arm((0.52, 0, 1.75), 'R', outfit_color)
    create_arm((-0.52, 0, 1.75), 'L', outfit_color)
    
    # 创建腿
    create_leg((0.22, 0.16, 0.48), 'R', outfit_color)
    create_leg((-0.22, 0.16, 0.48), 'L', outfit_color)
    
    # 设置姿势
    create_pose(contributor['pose'])
    
    # 创建光环
    create_halo(contributor['emission_color'])
    
    # 创建配饰
    create_accessory(contributor)
    
    # 设置场景
    setup_scene()
    
    # 渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 256
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True
    
    # 保存文件
    blend_path = OUTPUT_DIR / f"Realistic_{contributor['name']}.blend"
    bpy.ops.wm.save_mainfile(filepath=str(blend_path))
    
    # 渲染
    render_path = OUTPUT_DIR / f"Realistic_{contributor['name']}.png"
    bpy.context.scene.render.filepath = str(render_path)
    bpy.ops.render.render(write_still=True)
    
    print(f"✅ 生成角色 {contributor['name']} 完成!")
    print(f"   照片: {photo_path}")
    print(f"   Blender文件: {blend_path}")

def main():
    """主函数"""
    print("="*60)
    print("🌟 专业级3D人物面部重建")
    print("="*60)
    
    for contributor in CONTRIBUTORS:
        print(f"\n🎨 生成角色: {contributor['name']}")
        print(f"   身份: {contributor['title']}")
        generate_character(contributor)
    
    print("\n" + "="*60)
    print("🎉 所有角色生成完成!")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
