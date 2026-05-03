#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片转3D角色生成器
为《游戏也太真实了》小说创作奉献者打造的3D角色

功能：
1. 从2D图片生成3D角色模型
2. 添加艺术风格 - 奉献精神主题
3. 批量处理多个角色
4. 支持自定义材质和姿势
"""

import bpy
import os
import json
from pathlib import Path

# ============================================================
# 配置参数
# ============================================================
CONFIG = {
    "output_dir": "/python/Output/Characters/3D",
    "texture_size": 2048,
    "subdivision_levels": 2,
    "art_style": "dedication",  # dedication, heroic, artistic
    "base_mesh": "humanoid",
}

# 艺术风格配置
ART_STYLES = {
    "dedication": {
        "name": "奉献精神",
        "description": "为事业奉献自身的崇高感",
        "color_palette": ["#1a1a2e", "#16213e", "#0f3460", "#e94560", "#ffffff"],
        "emission_strength": 2.0,
        "metallic": 0.3,
        "roughness": 0.6,
    },
    "heroic": {
        "name": "英雄史诗",
        "description": "史诗般的英雄气概",
        "color_palette": ["#4a4a4a", "#8b4513", "#ffd700", "#c0c0c0", "#1a1a1a"],
        "emission_strength": 1.5,
        "metallic": 0.8,
        "roughness": 0.2,
    },
    "artistic": {
        "name": "艺术抽象",
        "description": "抽象艺术风格",
        "color_palette": ["#4361ee", "#4cc9f0", "#ff006e", "#f72585", "#7209b7"],
        "emission_strength": 3.0,
        "metallic": 0.1,
        "roughness": 0.8,
    },
}

# ============================================================
# 核心功能
# ============================================================
def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("✓ 场景已清空")

def create_base_mesh(mesh_type="humanoid"):
    """创建基础网格"""
    if mesh_type == "humanoid":
        # 创建基础人形
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
        body = bpy.context.active_object
        body.name = "Body"
        
        # 缩放成人体比例
        body.scale = (0.4, 0.4, 1.2)
        
        # 添加细分曲面
        sub_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
        sub_mod.levels = CONFIG["subdivision_levels"]
        sub_mod.render_levels = CONFIG["subdivision_levels"]
        
        print("✓ 创建基础人形网格")
        return body
    else:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        return bpy.context.active_object

def create_head():
    """创建头部"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2.2))
    head = bpy.context.active_object
    head.name = "Head"
    
    # 添加细分
    sub_mod = head.modifiers.new(name="Subdivision", type='SUBSURF')
    sub_mod.levels = CONFIG["subdivision_levels"]
    
    print("✓ 创建头部")
    return head

def create_arm(location, side):
    """创建手臂"""
    # 上臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.8, location=location)
    upper_arm = bpy.context.active_object
    upper_arm.name = f"UpperArm_{side}"
    upper_arm.rotation_euler.x = 1.5708
    
    # 前臂
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.7, location=(location[0], location[1], location[2]-0.7))
    lower_arm = bpy.context.active_object
    lower_arm.name = f"LowerArm_{side}"
    lower_arm.rotation_euler.x = 1.5708
    
    # 手
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(location[0], location[1], location[2]-1.3))
    hand = bpy.context.active_object
    hand.name = f"Hand_{side}"
    
    print(f"✓ 创建{side}手臂")
    return upper_arm, lower_arm, hand

def create_leg(location, side):
    """创建腿部"""
    # 大腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1.0, location=location)
    thigh = bpy.context.active_object
    thigh.name = f"Thigh_{side}"
    
    # 小腿
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.9, location=(location[0], location[1], location[2]-0.9))
    calf = bpy.context.active_object
    calf.name = f"Calf_{side}"
    
    # 脚
    bpy.ops.mesh.primitive_cube_add(size=0.3, location=(location[0], location[1], location[2]-1.7))
    foot = bpy.context.active_object
    foot.name = f"Foot_{side}"
    foot.scale = (1.5, 0.8, 2.0)
    
    print(f"✓ 创建{side}腿部")
    return thigh, calf, foot

def create_character_armature():
    """创建角色骨骼"""
    bpy.ops.object.armature_add(location=(0, 0, 1))
    armature = bpy.context.active_object
    armature.name = "Character_Armature"
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    
    bones = armature.data.edit_bones
    
    # 脊柱 - 获取或创建骨骼
    if len(bones) > 0:
        spine = bones[0]
        spine.name = 'Spine'
    else:
        spine = bones.new('Spine')
    spine.head = (0, 0, 0.5)
    spine.tail = (0, 0, 1.8)
    
    # 头部
    head = bones.new('Head')
    head.head = spine.tail
    head.tail = (0, 0, 2.5)
    head.parent = spine
    
    # 左臂
    upper_arm_l = bones.new('UpperArm_L')
    upper_arm_l.head = (0.3, 0, 1.5)
    upper_arm_l.tail = (0.8, 0, 1.5)
    upper_arm_l.parent = spine
    
    lower_arm_l = bones.new('LowerArm_L')
    lower_arm_l.head = upper_arm_l.tail
    lower_arm_l.tail = (1.3, 0, 1.5)
    lower_arm_l.parent = upper_arm_l
    
    # 右臂
    upper_arm_r = bones.new('UpperArm_R')
    upper_arm_r.head = (-0.3, 0, 1.5)
    upper_arm_r.tail = (-0.8, 0, 1.5)
    upper_arm_r.parent = spine
    
    lower_arm_r = bones.new('LowerArm_R')
    lower_arm_r.head = upper_arm_r.tail
    lower_arm_r.tail = (-1.3, 0, 1.5)
    lower_arm_r.parent = upper_arm_r
    
    # 左腿
    thigh_l = bones.new('Thigh_L')
    thigh_l.head = (0.15, 0, 0.4)
    thigh_l.tail = (0.15, 0, -0.6)
    
    calf_l = bones.new('Calf_L')
    calf_l.head = thigh_l.tail
    calf_l.tail = (0.15, 0, -1.5)
    calf_l.parent = thigh_l
    
    # 右腿
    thigh_r = bones.new('Thigh_R')
    thigh_r.head = (-0.15, 0, 0.4)
    thigh_r.tail = (-0.15, 0, -0.6)
    
    calf_r = bones.new('Calf_R')
    calf_r.head = thigh_r.tail
    calf_r.tail = (-0.15, 0, -1.5)
    calf_r.parent = thigh_r
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print("✓ 创建骨骼绑定")
    return armature

def create_dedication_material(name, style="dedication"):
    """创建奉献主题材质"""
    style_config = ART_STYLES.get(style, ART_STYLES["dedication"])
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清除默认节点
    for node in nodes:
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
    noise.inputs['Detail'].default_value = 2.0
    
    # 设置颜色渐变 - 奉献主题配色
    colors = style_config["color_palette"]
    
    def hex_to_rgb(hex_color):
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
    
    color_ramp.color_ramp.elements[0].color = hex_to_rgb(colors[0]) + (1,)
    color_ramp.color_ramp.elements[1].color = hex_to_rgb(colors[3]) + (1,)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[1].position = 0.7
    
    # 设置BSDF
    bsdf.inputs['Metallic'].default_value = style_config["metallic"]
    bsdf.inputs['Roughness'].default_value = style_config["roughness"]
    
    # 设置发光
    emission.inputs['Strength'].default_value = style_config["emission_strength"]
    
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
    
    print(f"✓ 创建材质: {name} ({style_config['name']})")
    return mat

def apply_material_to_objects(material, objects):
    """应用材质到对象"""
    for obj in objects:
        if obj.type == 'MESH':
            obj.data.materials.clear()
            obj.data.materials.append(material)
    print(f"✓ 应用材质到 {len(objects)} 个对象")

def create_pose_of_dedication(armature):
    """创建奉献姿态 - 双手合十/祈祷的姿势"""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # 设置姿势 - 奉献/祈祷姿态
    pose_bones = armature.pose.bones
    
    # 头部微微低下，表达敬意
    pose_bones['Head'].rotation_euler.x = 0.3
    
    # 双臂抬起，双手合十
    pose_bones['UpperArm_L'].rotation_euler.z = -0.8
    pose_bones['UpperArm_L'].rotation_euler.x = -0.5
    
    pose_bones['UpperArm_R'].rotation_euler.z = 0.8
    pose_bones['UpperArm_R'].rotation_euler.x = -0.5
    
    pose_bones['LowerArm_L'].rotation_euler.x = 0.8
    pose_bones['LowerArm_R'].rotation_euler.x = 0.8
    
    # 身体微微前倾
    pose_bones['Spine'].rotation_euler.x = 0.2
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print("✓ 设置奉献姿态")

def add_particle_effect(obj, effect_type="glow"):
    """添加粒子效果"""
    # 添加发光效果
    mat = obj.data.materials[0] if obj.data.materials else None
    if mat and mat.node_tree:
        nodes = mat.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Emission Strength'].default_value = 3.0
    
    # 创建光环
    bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.05, location=(0, 0, 2.5))
    halo = bpy.context.active_object
    halo.name = "Halo"
    
    halo_mat = create_dedication_material("Halo_Material", "dedication")
    halo.data.materials.clear()
    halo.data.materials.append(halo_mat)
    
    # 添加发光纹理
    # 查找Emission节点
    emission_node = None
    for node in halo_mat.node_tree.nodes:
        if node.type == 'EMISSION':
            emission_node = node
            break
    if emission_node:
        emission_node.inputs['Strength'].default_value = 5.0
    
    print("✓ 添加光环效果")
    return halo

def import_reference_image(image_path):
    """导入参考图片作为背景"""
    if os.path.exists(image_path):
        # 创建参考平面
        bpy.ops.mesh.primitive_plane_add(size=5, location=(3, 0, 1.5))
        ref_plane = bpy.context.active_object
        ref_plane.name = "Reference_Plane"
        ref_plane.rotation_euler.y = 1.5708
        
        # 创建材质
        mat = bpy.data.materials.new(name="Reference_Mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # 清除默认节点
        for node in nodes:
            nodes.remove(node)
        
        output = nodes.new('ShaderNodeOutputMaterial')
        diffuse = nodes.new('ShaderNodeBsdfDiffuse')
        tex_image = nodes.new('ShaderNodeTexImage')
        
        # 加载图片
        img = bpy.data.images.load(image_path)
        tex_image.image = img
        
        # 连接节点
        mat.node_tree.links.new(tex_image.outputs['Color'], diffuse.inputs['Color'])
        mat.node_tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
        
        ref_plane.data.materials.append(mat)
        ref_plane.hide_render = True
        
        print(f"✓ 导入参考图片: {image_path}")
        return ref_plane
    return None

def setup_camera_and_lighting():
    """设置相机和光照"""
    # 创建相机
    bpy.ops.object.camera_add(location=(5, -5, 3))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    camera.rotation_euler = (1.0, 0, 0.785)
    bpy.context.scene.camera = camera
    
    # 创建主光源
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.name = "Sun_Light"
    sun.data.energy = 3.0
    sun.rotation_euler = (0.785, 0.785, 0)
    
    # 创建补光
    bpy.ops.object.light_add(type='AREA', location=(-3, 2, 4))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 200
    fill_light.data.size = 2
    
    # 创建背光
    bpy.ops.object.light_add(type='SPOT', location=(0, 5, 3))
    rim_light = bpy.context.active_object
    rim_light.name = "Rim_Light"
    rim_light.data.energy = 1000
    rim_light.rotation_euler = (0, 3.14, 0)
    
    print("✓ 设置相机和光照")

def generate_character(image_path=None, character_name="Dedication_Character"):
    """生成3D角色"""
    print(f"\n{'='*60}")
    print(f"🎨 生成角色: {character_name}")
    print(f"{'='*60}")
    
    # 清空场景
    clear_scene()
    
    # 创建基础网格
    body = create_base_mesh()
    head = create_head()
    upper_arm_l, lower_arm_l, hand_l = create_arm((0.5, 0, 1.5), "L")
    upper_arm_r, lower_arm_r, hand_r = create_arm((-0.5, 0, 1.5), "R")
    thigh_l, calf_l, foot_l = create_leg((0.15, 0, 0.4), "L")
    thigh_r, calf_r, foot_r = create_leg((-0.15, 0, 0.4), "R")
    
    # 创建骨骼
    armature = create_character_armature()
    
    # 创建材质
    material = create_dedication_material("Dedication_Material", CONFIG["art_style"])
    
    # 收集所有网格对象
    all_meshes = [body, head, upper_arm_l, lower_arm_l, hand_l,
                  upper_arm_r, lower_arm_r, hand_r,
                  thigh_l, calf_l, foot_l, thigh_r, calf_r, foot_r]
    
    # 应用材质
    apply_material_to_objects(material, all_meshes)
    
    # 设置奉献姿态
    create_pose_of_dedication(armature)
    
    # 添加粒子效果
    add_particle_effect(body)
    
    # 导入参考图片
    if image_path and os.path.exists(image_path):
        import_reference_image(image_path)
    
    # 设置相机和光照
    setup_camera_and_lighting()
    
    # 设置渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = True
    
    # 保存Blender文件
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    blend_file = output_dir / f"{character_name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))
    
    # 渲染输出
    render_file = output_dir / f"{character_name}.png"
    bpy.context.scene.render.filepath = str(render_file)
    bpy.ops.render.render(write_still=True)
    
    print(f"\n🎉 角色生成完成!")
    print(f"📁 Blender文件: {blend_file}")
    print(f"🖼️ 渲染图片: {render_file}")
    
    return {
        "success": True,
        "character_name": character_name,
        "blend_file": str(blend_file),
        "render_file": str(render_file),
        "style": ART_STYLES[CONFIG["art_style"]]["name"],
        "objects_count": len(all_meshes)
    }

def batch_generate_characters(image_paths, base_name="Contributor"):
    """批量生成角色"""
    results = []
    
    for i, image_path in enumerate(image_paths):
        if os.path.exists(image_path):
            character_name = f"{base_name}_{i+1}"
            result = generate_character(image_path, character_name)
            results.append(result)
        else:
            print(f"⚠️ 图片不存在: {image_path}")
            results.append({
                "success": False,
                "error": f"File not found: {image_path}"
            })
    
    # 生成汇总报告
    report = {
        "total": len(image_paths),
        "successful": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results
    }
    
    report_file = Path(CONFIG["output_dir"]) / "batch_report.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"\n📊 批量生成完成!")
    print(f"✅ 成功: {report['successful']}")
    print(f"❌ 失败: {report['failed']}")
    print(f"📋 报告文件: {report_file}")
    
    return report

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    # 示例：批量生成角色
    contributor_images = [
        # 这里可以添加实际的图片路径
        "/python/Input/Characters/contributor1.png",
        "/python/Input/Characters/contributor2.png",
        "/python/Input/Characters/contributor3.png",
    ]
    
    # 检查是否有命令行参数
    import sys
    if len(sys.argv) > 1:
        # Blender命令行模式
        # 格式: blender --background --python image_to_3d_character.py -- <image_path> <character_name>
        args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
        
        if len(args) >= 1:
            image_path = args[0]
            character_name = args[1] if len(args) > 1 else "Character"
            generate_character(image_path, character_name)
        else:
            # 生成默认角色
            generate_character(None, "Dedication_Hero")
    else:
        # 生成默认角色
        generate_character(None, "Dedication_Hero")
