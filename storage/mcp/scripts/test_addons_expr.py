import sys
sys.path.insert(0, "/python/MCP")
from blender_mcp import blender_run

script = """import bpy, addon_utils, os

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

# 列出所有可用 addon (只含 godot/scene)
print("=== godot/scene addon 模块 ===")
for mod in addon_utils.module_list():
    if 'godot' in mod.lower() or 'io_scene_godot' in mod.lower():
        print(f"  FOUND: {mod}")

# 检查 preferences.addons
print()
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

print(blender_run("/python/MCP/scripts/test_addons_expr_blender.py", background=True))


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

# 列出所有可用 addon (只含 godot/scene)
print("=== godot/scene addon 模块 ===")
for mod in addon_utils.module_list():
    if 'godot' in mod.lower() or 'io_scene_godot' in mod.lower():
        print(f"  FOUND: {mod}")

# 检查 preferences.addons
print()
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
