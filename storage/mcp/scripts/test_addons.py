#!/usr/bin/env python3
"""测试 Blender addon 扫描 - 特别检查 io_scene_godot"""
import subprocess, sys

BLENDER = "%SOFTWARE_DIR%/KF/JM/blender/blender.exe"

test_code = """
import bpy, addon_utils, os

# 强制扫描 addon 目录
addon_dirs = [
    bpy.utils.script_path_user(),
    bpy.utils.script_path_pref(),
]
print("Script paths:", addon_dirs)
print()

# 检查 io_scene_godot 目录
addon_dir = bpy.utils.script_path_pref()
target = os.path.join(addon_dir, "addons", "io_scene_godot")
print(f"Addon dir: {addon_dir}")
print(f"io_scene_godot path: {target}")
print(f"Exists: {os.path.exists(target)}")
print()

# 列出所有可用 addon
print("=== 所有 addon 模块 ===")
for mod in addon_utils.module_list():
    if 'godot' in mod.lower() or 'scene' in mod.lower():
        print(f"  FOUND: {mod}")
print()

# 检查 preferences.addons
print("=== preferences.addons ===")
for a in bpy.context.preferences.addons:
    print(f"  {a.module}")

# 尝试直接导入
print()
print("=== 尝试导入 io_scene_godot ===")
try:
    import io_scene_godot
    print(f"SUCCESS: {io_scene_godot.bl_info['name']}")
except Exception as e:
    print(f"IMPORT FAILED: {e}")
"""

r = subprocess.run(
    [BLENDER, "--background", "--python-expr", test_code],
    capture_output=True, encoding="utf-8", errors="replace", timeout=60
)
print(r.stdout or r.stderr)
