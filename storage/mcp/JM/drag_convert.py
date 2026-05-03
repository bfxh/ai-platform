#!/usr/bin/env python3
"""
拖拽转换工具 - 把3D模型文件拖进来自动转换
支持: .obj .fbx .gltf .glb .dae .abc .usd .usda .usdc .stl .3mf .ply
输出: 带烘焙贴图的GLB (Godot/UE5/Unity通用)
"""
import sys
import os
import asyncio
import time
import shutil
import subprocess
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import Config
from core.blender_bridge import BlenderBridge
from core.state import ConvertState

SUPPORTED_EXT = {".obj", ".fbx", ".gltf", ".glb", ".dae", ".abc", ".usd", ".usda", ".usdc", ".stl", ".3mf", ".ply", ".blend"}


def convert(input_path: str):
    config = Config.load()

    p = Path(input_path.strip().strip('"').strip("'"))
    if not p.exists():
        print(f"[ERROR] 文件不存在: {p}")
        return False

    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXT:
        print(f"[ERROR] 不支持的格式: {ext}")
        print(f"  支持: {', '.join(sorted(SUPPORTED_EXT))}")
        return False

    model_name = p.stem
    for suffix in [".mesh", ".model", ".asset", ".shape", ".geometry"]:
        if model_name.lower().endswith(suffix):
            model_name = model_name[:len(model_name) - len(suffix)]
            break

    out_dir = Path(config.output_dir) / model_name
    out_dir.mkdir(parents=True, exist_ok=True)

    state = ConvertState(out_dir, model_name)

    if state.has_incomplete:
        print(f"[续转] 检测到未完成的转换: {model_name}")
        print(f"  已完成步骤: {', '.join(state.data['steps_completed'])}")
        print(f"  失败步骤: {', '.join(state.data['steps_failed'])}")
        if state.data.get("last_error"):
            print(f"  上次错误: {state.data['last_error']}")
        print("\n是否从断点续转? (Y/N): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            state.data = {
                "model_name": model_name,
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "steps_completed": [],
                "steps_failed": [],
                "output_files": {},
                "last_error": None,
            }
            state.save()
            print("已重置状态，从头开始转换。")

    print("=" * 60)
    print(f"  拖拽转换工具 v2.0")
    print(f"  输入: {p.name}")
    print(f"  输出: {out_dir}")
    print(f"  策略: 智能保留原始材质，无材质时自动补全")
    print("=" * 60)

    bridge = BlenderBridge(config.blender_path)
    godot_path = config.godot_path
    godot_project = config.godot_project

    print("\n[1/4] Blender 烘焙转换中...")
    glb_file = out_dir / f"{model_name}.glb"
    if state.is_completed("blender_bake"):
        print("  Blender烘焙已完成，跳过")
    else:
        if not bridge.is_available():
            state.mark_failed("blender_bake", f"Blender 未找到: {config.blender_path}")
            print(f"[ERROR] Blender 未找到: {config.blender_path}")
            return False

        t0 = time.time()
        warnings = []
        output_files = asyncio.run(bridge.bake(
            p, out_dir, model_name,
            preset="smart_auto",
            bake_size=config.bake_size,
            warnings=warnings,
        ))
        elapsed = time.time() - t0

        if warnings:
            for w in warnings:
                print(f"  [WARN] {w}")

        if not output_files or not glb_file.exists():
            state.mark_failed("blender_bake", "GLB 文件未生成")
            print("[ERROR] Blender 烘焙失败，GLB 文件未生成")
            return False

        glb_size = glb_file.stat().st_size / 1024
        print(f"  GLB: {glb_size:.1f} KB ({elapsed:.1f}s)")

        fbx_file = out_dir / f"{model_name}.fbx"
        if fbx_file.exists():
            fbx_size = fbx_file.stat().st_size / 1024
            print(f"  FBX: {fbx_size:.1f} KB")

        for tex in ["_Albedo.png", "_Roughness.png", "_Normal.png"]:
            tex_file = out_dir / f"{model_name}{tex}"
            if tex_file.exists():
                tex_size = tex_file.stat().st_size / 1024
                print(f"  贴图: {tex_file.name} ({tex_size:.1f} KB)")

        state.mark_completed("blender_bake", {
            "glb": str(glb_file),
            "fbx": str(fbx_file) if fbx_file.exists() else "",
        })

    print("\n[2/4] 复制到 Godot 项目...")
    godot_models = Path(godot_project) / "models"
    if state.is_completed("copy_to_godot"):
        print("  复制到Godot已完成，跳过")
    else:
        godot_models.mkdir(parents=True, exist_ok=True)

        import_files = list(godot_models.glob("*.import"))
        for f in import_files:
            try:
                f.unlink()
            except Exception:
                pass

        imported_dir = Path(godot_project) / ".godot" / "imported"
        if imported_dir.exists():
            shutil.rmtree(imported_dir, ignore_errors=True)

        shutil.copy2(glb_file, godot_models / glb_file.name)
        print(f"  已复制: {godot_models / glb_file.name}")
        state.mark_completed("copy_to_godot", {"godot_glb": str(godot_models / glb_file.name)})

    print("\n[3/4] Godot 导入...")
    if state.is_completed("godot_import"):
        print("  Godot导入已完成，跳过")
    else:
        result = subprocess.run(
            [godot_path, "--headless", "--import", "--path", godot_project, "--quit"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
        )
        if result.returncode == 0:
            print("  导入成功!")
        else:
            print("  导入有警告，但可能仍然可用")
        state.mark_completed("godot_import")

    print("\n[4/4] 更新场景文件...")
    scene_file = Path(godot_project) / "scenes" / f"{model_name}.tscn"
    if state.is_completed("update_scene"):
        print("  场景更新已完成，跳过")
    else:
        import_file = godot_models / f"{model_name}.glb.import"
        uid = ""
        if import_file.exists():
            for line in import_file.read_text(encoding='utf-8').split('\n'):
                if line.startswith('uid='):
                    uid = line.split('"')[1]
                    break

        scene_dir = Path(godot_project) / "scenes"
        scene_dir.mkdir(parents=True, exist_ok=True)

        uid_str = f' uid="{uid}"' if uid else ''
        scene_content = f'''[gd_scene load_steps=2 format=3]

[ext_resource type="PackedScene"{uid_str} path="res://models/{model_name}.glb" id="1_glb"]

[node name="{model_name}" type="Node3D"]

[node name="Model" parent="." instance=ExtResource("1_glb")]

[node name="Camera3D" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 0.866025, 0.5, 0, -0.5, 0.866025, 0, 3, 5)
current = true

[node name="DirectionalLight3D" type="DirectionalLight3D" parent="."]
transform = Transform3D(0.866025, -0.433013, 0.25, 0, 0.5, 0.866025, -0.5, -0.75, 0.433013, 0, 5, 0)
shadow_enabled = true
'''
        scene_file.write_text(scene_content, encoding='utf-8')

        project_godot = Path(godot_project) / "project.godot"
        if project_godot.exists():
            content = project_godot.read_text(encoding='utf-8')
            main_scene = f'res://scenes/{model_name}.tscn'
            if 'run/main_scene' in content:
                content = re.sub(r'run/main_scene="[^"]*"', f'run/main_scene="{main_scene}"', content)
            else:
                content += f'\n[application]\nrun/main_scene="{main_scene}"\n'
            project_godot.write_text(content, encoding='utf-8')

        print(f"  场景: {scene_file}")
        state.mark_completed("update_scene", {"tscn": str(scene_file)})

    state.cleanup()

    print("\n" + "=" * 60)
    print("  转换完成!")
    print("=" * 60)
    print(f"\n  输出文件:")
    print(f"    GLB: {glb_file}")
    fbx_file = out_dir / f"{model_name}.fbx"
    print(f"    FBX: {fbx_file if fbx_file.exists() else 'N/A'}")
    print(f"    Godot: {godot_models / glb_file.name}")
    print(f"\n  打开 Godot 查看:")
    print(f"    {godot_path} --path {godot_project} --editor")
    print(f"\n  或双击: /python\\storage\\mcp\\JM\\启动转换器.bat")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("拖拽转换工具 v2.0 (core模块 + 断点续转)")
        print("用法: 把3D模型文件拖到这个脚本上")
        print(f"支持格式: {', '.join(sorted(SUPPORTED_EXT))}")
        input("\n按回车退出...")
        sys.exit(0)

    success = convert(sys.argv[1])
    if not success:
        input("\n转换失败，按回车退出...")
        sys.exit(1)

    config = Config.load()
    print("\n是否立即在 Godot 中打开? (Y/N): ", end="")
    choice = input().strip().lower()
    if choice == 'y':
        subprocess.Popen([config.godot_path, "--path", config.godot_project, "--editor"])
