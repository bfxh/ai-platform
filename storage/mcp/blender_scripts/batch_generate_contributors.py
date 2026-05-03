#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成《游戏也太真实了》奉献者3D角色
根据用户提供的详细信息定制角色
"""

import bpy
import os
import sys
from pathlib import Path

# 输出目录
OUTPUT_DIR = Path("/python/Output/Characters/3D")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 奉献者配置 - 根据用户描述更新
CONTRIBUTORS = [
    {
        "id": 1,
        "name": "群主",
        "title": "研究与策划",
        "description": "负责研究并且制作小说的PPT以及各种东西，不是小说作者",
        "pose": "presenting",  # 展示/演讲姿势
        "color_theme": ["#2d3436", "#636e72", "#b2bec3", "#0984e3"],
        "emission_color": "#0984e3",
        "halo_radius": 1.4,
        "icon": "📊"
    },
    {
        "id": 2,
        "name": "漫改负责人",
        "title": "漫画改编",
        "description": "负责小说的漫画改编工作，将文字转化为视觉艺术",
        "pose": "drawing",  # 绘画/创作姿势
        "color_theme": ["#2d1f3d", "#5b2c6f", "#9b59b6", "#e056fd"],
        "emission_color": "#e056fd",
        "halo_radius": 1.6,
        "icon": "🎨"
    },
    {
        "id": 3,
        "name": "思想指导员",
        "title": "群管理员",
        "description": "群的思想指导员，引领团队方向，激发创作灵感",
        "pose": "guiding",  # 指引/引领姿势
        "color_theme": ["#1e272e", "#3d5af1", "#00cec9", "#81ecec"],
        "emission_color": "#00cec9",
        "halo_radius": 1.3,
        "icon": "💡"
    }
]

def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_body():
    """创建身体"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    body = bpy.context.active_object
    body.name = "Body"
    body.scale = (0.4, 0.4, 1.2)
    
    sub_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    return body

def create_head():
    """创建头部"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.2))
    head = bpy.context.active_object
    head.name = "Head"
    
    sub_mod = head.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = 2
    return head

def create_limbs():
    """创建四肢"""
    limbs = []
    
    # 左臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.8, location=(0.5, 0, 1.5))
    upper_arm_l = bpy.context.active_object
    upper_arm_l.name = "UpperArm_L"
    upper_arm_l.rotation_euler.x = 1.5708
    limbs.append(upper_arm_l)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.7, location=(0.5, 0, 0.8))
    lower_arm_l = bpy.context.active_object
    lower_arm_l.name = "LowerArm_L"
    lower_arm_l.rotation_euler.x = 1.5708
    limbs.append(lower_arm_l)
    
    # 右臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.8, location=(-0.5, 0, 1.5))
    upper_arm_r = bpy.context.active_object
    upper_arm_r.name = "UpperArm_R"
    upper_arm_r.rotation_euler.x = 1.5708
    limbs.append(upper_arm_r)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.7, location=(-0.5, 0, 0.8))
    lower_arm_r = bpy.context.active_object
    lower_arm_r.name = "LowerArm_R"
    lower_arm_r.rotation_euler.x = 1.5708
    limbs.append(lower_arm_r)
    
    # 左腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.0, location=(0.15, 0, 0.4))
    thigh_l = bpy.context.active_object
    thigh_l.name = "Thigh_L"
    limbs.append(thigh_l)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.9, location=(0.15, 0, -0.5))
    calf_l = bpy.context.active_object
    calf_l.name = "Calf_L"
    limbs.append(calf_l)
    
    # 右腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.0, location=(-0.15, 0, 0.4))
    thigh_r = bpy.context.active_object
    thigh_r.name = "Thigh_R"
    limbs.append(thigh_r)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.9, location=(-0.15, 0, -0.5))
    calf_r = bpy.context.active_object
    calf_r.name = "Calf_R"
    limbs.append(calf_r)
    
    # 手和脚
    for side in ['L', 'R']:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0.5 if side == 'L' else -0.5, 0, 0.1))
        hand = bpy.context.active_object
        hand.name = f"Hand_{side}"
        limbs.append(hand)
        
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=(0.15 if side == 'L' else -0.15, 0, -1.3))
        foot = bpy.context.active_object
        foot.name = f"Foot_{side}"
        foot.scale = (1.5, 0.8, 2.0)
        limbs.append(foot)
    
    return limbs

def create_armature():
    """创建骨骼"""
    bpy.ops.object.armature_add(location=(0, 0, 1))
    armature = bpy.context.active_object
    armature.name = "Armature"
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    bones = armature.data.edit_bones
    
    # 基础骨骼
    if len(bones) > 0:
        spine = bones[0]
        spine.name = 'Spine'
    else:
        spine = bones.new('Spine')
    spine.head = (0, 0, 0.5)
    spine.tail = (0, 0, 1.8)
    
    head = bones.new('Head')
    head.head = spine.tail
    head.tail = (0, 0, 2.5)
    head.parent = spine
    
    # 手臂骨骼
    for side, x in [('L', 0.3), ('R', -0.3)]:
        upper = bones.new(f'UpperArm_{side}')
        upper.head = (x, 0, 1.5)
        upper.tail = (x * 2.5, 0, 1.5)
        upper.parent = spine
        
        lower = bones.new(f'LowerArm_{side}')
        lower.head = upper.tail
        lower.tail = (x * 4, 0, 1.5)
        lower.parent = upper
    
    # 腿部骨骼
    for side, x in [('L', 0.15), ('R', -0.15)]:
        thigh = bones.new(f'Thigh_{side}')
        thigh.head = (x, 0, 0.5)
        thigh.tail = (x, 0, -0.5)
        
        calf = bones.new(f'Calf_{side}')
        calf.head = thigh.tail
        calf.tail = (x, 0, -1.5)
        calf.parent = thigh
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return armature

def create_material(name, color_theme, emission_color):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清除默认节点
    for node in list(nodes):
        nodes.remove(node)
    
    # 创建节点
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    emission = nodes.new('ShaderNodeEmission')
    mix = nodes.new('ShaderNodeMixShader')
    color_ramp = nodes.new('ShaderNodeValToRGB')
    noise = nodes.new('ShaderNodeTexNoise')
    mapping = nodes.new('ShaderNodeMapping')
    tex_coord = nodes.new('ShaderNodeTexCoord')
    
    # 设置噪声
    noise.inputs['Scale'].default_value = 5.0
    
    # 设置颜色
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    
    color_ramp.color_ramp.elements[0].color = hex_to_rgb(color_theme[0]) + (1,)
    color_ramp.color_ramp.elements[1].color = hex_to_rgb(color_theme[2]) + (1,)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[1].position = 0.7
    
    # 设置发光
    emission.inputs['Color'].default_value = hex_to_rgb(emission_color) + (1,)
    emission.inputs['Strength'].default_value = 2.0
    
    # 连接节点
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], noise.inputs['Vector'])
    links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(color_ramp.outputs['Color'], emission.inputs['Color'])
    links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    links.new(emission.outputs['Emission'], mix.inputs[2])
    links.new(noise.outputs['Fac'], mix.inputs[0])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat

def set_pose(armature, pose_type):
    """设置姿势"""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = armature.pose.bones
    
    if pose_type == "presenting":
        # 展示/演讲姿势 - 群主
        pose_bones['UpperArm_L'].rotation_euler.z = -0.5
        pose_bones['UpperArm_L'].rotation_euler.x = -0.3
        pose_bones['LowerArm_L'].rotation_euler.x = -0.5
        
        pose_bones['UpperArm_R'].rotation_euler.z = 0.5
        pose_bones['UpperArm_R'].rotation_euler.x = -0.3
        pose_bones['LowerArm_R'].rotation_euler.x = 0.8
        
    elif pose_type == "drawing":
        # 绘画/创作姿势 - 漫改负责人
        pose_bones['UpperArm_L'].rotation_euler.z = -1.2
        pose_bones['UpperArm_L'].rotation_euler.x = 0.2
        pose_bones['LowerArm_L'].rotation_euler.x = -0.8
        
        pose_bones['UpperArm_R'].rotation_euler.z = 0.8
        pose_bones['UpperArm_R'].rotation_euler.x = -0.2
        
    elif pose_type == "guiding":
        # 指引/引领姿势 - 思想指导员
        pose_bones['Head'].rotation_euler.y = 0.2
        pose_bones['UpperArm_L'].rotation_euler.z = -0.8
        pose_bones['UpperArm_L'].rotation_euler.x = -0.5
        pose_bones['LowerArm_L'].rotation_euler.x = 1.0
        
        pose_bones['UpperArm_R'].rotation_euler.z = 0.3
        pose_bones['UpperArm_R'].rotation_euler.x = -0.2
        
    elif pose_type == "prayer":
        # 祈祷姿势
        pose_bones['Head'].rotation_euler.x = 0.3
        pose_bones['UpperArm_L'].rotation_euler.z = -0.8
        pose_bones['UpperArm_L'].rotation_euler.x = -0.5
        pose_bones['UpperArm_R'].rotation_euler.z = 0.8
        pose_bones['UpperArm_R'].rotation_euler.x = -0.5
        pose_bones['LowerArm_L'].rotation_euler.x = 0.8
        pose_bones['LowerArm_R'].rotation_euler.x = 0.8
        
    bpy.ops.object.mode_set(mode='OBJECT')

def add_halo(radius, emission_color):
    """添加光环"""
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.05, location=(0, 0, 2.5))
    halo = bpy.context.active_object
    halo.name = "Halo"
    
    mat = create_material("Halo_Mat", ["#ffffff", "#ffffff", "#ffffff", "#ffffff"], emission_color)
    halo.data.materials.clear()
    halo.data.materials.append(mat)
    
    # 增强发光
    for node in mat.node_tree.nodes:
        if node.type == 'EMISSION':
            node.inputs['Strength'].default_value = 5.0
            break
    
    return halo

def add_accessory(contributor):
    """根据角色添加配饰"""
    if contributor['title'] == "研究与策划":
        # 添加文件夹/文档
        bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.8, 0.3, 1.0))
        folder = bpy.context.active_object
        folder.name = "Document"
        folder.scale = (1.5, 0.1, 1.2)
        
    elif contributor['title'] == "漫画改编":
        # 添加画板/画布
        bpy.ops.mesh.primitive_plane_add(size=0.4, location=(-0.8, 0.3, 1.2))
        canvas = bpy.context.active_object
        canvas.name = "Canvas"
        canvas.rotation_euler.z = 0.2
        
    elif contributor['title'] == "群管理员":
        # 添加发光球体/思想之光
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, -0.3, 2.0))
        orb = bpy.context.active_object
        orb.name = "Thought_Orb"
        
        # 为光球创建发光材质
        mat = bpy.data.materials.new(name="Orb_Mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        for node in list(nodes):
            nodes.remove(node)
        
        output = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
        
        emission.inputs['Color'].default_value = hex_to_rgb(contributor['emission_color']) + (1,)
        emission.inputs['Strength'].default_value = 4.0
        
        mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        orb.data.materials.clear()
        orb.data.materials.append(mat)

def setup_scene():
    """设置场景"""
    # 相机
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.rotation_euler = (1.0, 0, 0.785)
    bpy.context.scene.camera = camera
    
    # 光源
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (0.785, 0.785, 0)
    
    bpy.ops.object.light_add(type='AREA', location=(-3, 2, 4))
    fill = bpy.context.active_object
    fill.name = "Fill"
    fill.data.energy = 200
    
    # 渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True

def generate_contributor(contributor):
    """生成奉献者角色"""
    print(f"\n🎨 生成角色: {contributor['icon']} {contributor['name']}")
    print(f"   角色: {contributor['title']}")
    print(f"   描述: {contributor['description']}")
    
    # 清空场景
    clear_scene()
    
    # 创建身体部件
    body = create_body()
    head = create_head()
    limbs = create_limbs()
    
    # 创建骨骼
    armature = create_armature()
    
    # 创建材质
    material = create_material(f"{contributor['name']}_Mat", 
                               contributor['color_theme'], 
                               contributor['emission_color'])
    
    # 应用材质
    all_objects = [body, head] + limbs
    for obj in all_objects:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    
    # 设置姿势
    set_pose(armature, contributor['pose'])
    
    # 添加配饰
    add_accessory(contributor)
    
    # 添加光环
    add_halo(contributor['halo_radius'], contributor['emission_color'])
    
    # 设置场景
    setup_scene()
    
    # 保存文件
    blend_file = OUTPUT_DIR / f"Dedication_{contributor['name']}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))
    
    # 渲染
    render_file = OUTPUT_DIR / f"Dedication_{contributor['name']}.png"
    bpy.context.scene.render.filepath = str(render_file)
    bpy.ops.render.render(write_still=True)
    
    print(f"   ✅ 完成!")
    print(f"      Blender文件: {blend_file}")
    print(f"      渲染图片: {render_file}")
    
    return True

def main():
    """主函数"""
    print(f"\n{'='*70}")
    print("🌟 《游戏也太真实了》奉献者3D角色生成")
    print(f"{'='*70}")
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and '--' in sys.argv:
        args = sys.argv[sys.argv.index('--') + 1:]
        if args:
            contributor_id = int(args[0])
            for c in CONTRIBUTORS:
                if c['id'] == contributor_id:
                    generate_contributor(c)
                    return
            print(f"未找到ID为 {contributor_id} 的奉献者")
            return
    
    # 批量生成所有奉献者
    for contributor in CONTRIBUTORS:
        generate_contributor(contributor)
    
    print(f"\n{'='*70}")
    print("🎉 所有奉献者角色生成完成!")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
