#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Godot 场景组装器 - Blender glTF → Godot 4.x

用法：
    python godot_scene_assembler.py <glb_file> <godot_project_dir> <scene_name>

示例：
    python godot_scene_assembler.py /python/test.glb /python/MyGame MainScene
    python godot_scene_assembler.py /python/test.glb /python/MyGame NPC --nodes 3

功能：
    1. 复制 .glb 文件到 Godot 项目 res://assets/ 目录
    2. 生成 Godot 4.x .tscn 场景文件（可直接拖入 Godot 编辑器）
    3. 自动处理材质路径引用
    4. 生成 import/ .glb.import 文件（让 Godot 识别导入设置）
"""
import os
import sys
import json
import shutil
import argparse
from pathlib import Path


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def copy_glb_to_godot(glb_file, godot_project):
    """复制 glb 到 Godot 资源目录"""
    assets_dir = os.path.join(godot_project, "assets")
    ensure_dir(assets_dir)

    dest_path = os.path.join(assets_dir, os.path.basename(glb_file))
    shutil.copy2(glb_file, dest_path)
    print(f"  [1/4] GLB 已复制: {dest_path}")
    return dest_path


def generate_godot_import_file(glb_path, godot_project):
    """生成 .glb.import 文件（Godot 导入配置）"""
    rel_path = os.path.relpath(glb_path, godot_project).replace("\\", "/")
    import_path = glb_path + ".import"

    # Godot 4.x .import 文件格式
    import_content = f"""[remap]
importer="scene"
type="PackedScene"
uid="uid://{generate_uid(rel_path)}"
path="res://{rel_path.replace('.glb', '.scn')}"

[deps]
source_file="res://{rel_path}"
dest_files=["res://{rel_path.replace('.glb', '.scn')}"]
"""

    with open(import_path, "w", encoding="utf-8") as f:
        f.write(import_content)
    print(f"  [2/4] Import 配置: {import_path}")
    return import_path


def generate_uid(path):
    """生成 Godot UID（基于路径的确定性 hash）"""
    import hashlib
    h = hashlib.sha256(path.encode()).digest()
    # Godot UID 格式: uid:// + base62 encoded (简化版)
    uid_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    uid = "uid://" + "".join(uid_chars[b % 62] for b in h[:21])
    return uid


def generate_tscn(glb_path, godot_project, scene_name, extra_nodes=None):
    """生成 Godot 4.x .tscn 场景文件"""
    rel_path = os.path.relpath(glb_path, godot_project).replace("\\", "/")
    uid = generate_uid(rel_path)
    scene_uid = generate_uid(scene_name)

    # Godot 4.x .tscn 格式
    node_id = 1
    scene_uid_short = scene_uid[9:]

    lines = [
        "[gd_scene load_steps=2 format=3 uid=\"%s\"]" % scene_uid,
        "",
        "[ext_resource type=\"PackedScene\" uid=\"%s\" path=\"res://%s\" id=\"1_%s\"]" % (uid, rel_path, scene_uid_short),
        "",
        "[node name=\"%s\" type=\"Node3D\"]" % scene_name,
    ]

    # 添加子节点（如果指定）
    if extra_nodes:
        lines.append("")
        for i, node_info in enumerate(extra_nodes, start=2):
            node_type = node_info.get("type", "Node3D")
            node_name = node_info.get("name", f"Child{i}")
            node_uid = generate_uid(f"{scene_name}_{node_name}")
            lines.append("")
            lines.append('[node name="%s" type="%s" parent="."]' % (node_name, node_type))
            if "position" in node_info:
                lines.append("transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, %s)" % node_info["position"])

    lines.extend([
        "",
        "[node name=\"glTF_Scene\" type=\"Node3D\" parent=\".\"]",
        '  [node name="%s" parent="." index="0"]' % scene_name,
        f'  ext_resource/path = "res://{rel_path}" [ext_resource type="PackedScene" id=1_{scene_uid_short}]',
    ])

    tscn_path = os.path.join(godot_project, f"{scene_name}.tscn")
    with open(tscn_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [3/4] 场景文件: {tscn_path}")
    return tscn_path


def update_project_godot(godot_project, scene_name):
    """更新 project.godot，添加场景引用"""
    project_file = os.path.join(godot_project, "project.godot")

    if not os.path.exists(project_file):
        # 创建基本 project.godot
        basic_project = f"""; Engine configuration file.
; It's best edited using the editor UI and not directly,
; since the parameters that go here are not all obvious.
;
; Format:
;   [section] ; section goes between []
;   param=value ; assign values to parameters

config_version=5

[application]
config/name="AI Generated Project"
run/main_scene="res://{scene_name}.tscn"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
"""
        with open(project_file, "w", encoding="utf-8") as f:
            f.write(basic_project)
        print(f"  [4/4] project.godot 已创建")


def main():
    parser = argparse.ArgumentParser(
        description="Blender glTF → Godot 4.x 场景组装",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python godot_scene_assembler.py /python/test.glb /python/MyGame MainScene
  python godot_scene_assembler.py model.glb ./godot_project Level1 --nodes 3
        """
    )
    parser.add_argument("glb_file", help="glTF/GLB 文件路径")
    parser.add_argument("godot_project", help="Godot 项目目录")
    parser.add_argument("scene_name", help="场景名称")
    parser.add_argument("--nodes", type=int, default=0,
                        help="额外子节点数量（默认: 0）")
    parser.add_argument("--subdirectory", default="assets",
                        help="Godot 资源子目录（默认: assets）")

    args = parser.parse_args()

    glb_file = Path(args.glb_file).resolve()
    godot_project = Path(args.godot_project).resolve()
    scene_name = args.scene_name

    if not glb_file.exists():
        print(f"错误: 文件不存在: {glb_file}")
        sys.exit(1)

    print(f"\n=== Godot 场景组装器 ===")
    print(f"GLB文件: {glb_file}")
    print(f"Godot项目: {godot_project}")
    print(f"场景名: {scene_name}")
    print()

    # 1. 复制到 Godot 资源目录
    dest_glb = copy_glb_to_godot(str(glb_file), str(godot_project))

    # 2. 生成 .import 文件
    generate_godot_import_file(dest_glb, str(godot_project))

    # 3. 生成 .tscn 场景文件
    extra_nodes = [{"type": "Camera3D", "name": "Camera", "position": "7, -7, 5"}] if args.nodes > 0 else None
    tscn_path = generate_tscn(dest_glb, str(godot_project), scene_name, extra_nodes)

    # 4. 更新/创建 project.godot
    update_project_godot(str(godot_project), scene_name)

    print()
    print(f"=== 完成 ===")
    print(f"GLB: res://{os.path.relpath(dest_glb, godot_project).replace(chr(92), '/')}")
    print(f"场景: res://{scene_name}.tscn")
    print()
    print(f"在 Godot 中打开: {godot_project}")
    print(f"  → 双击 {scene_name}.tscn 导入场景")
    print(f"  → 或直接拖入 .glb 文件到场景编辑器")

    return {
        "glb_file": dest_glb,
        "tscn_file": tscn_path,
        "success": True
    }


if __name__ == "__main__":
    result = main()
