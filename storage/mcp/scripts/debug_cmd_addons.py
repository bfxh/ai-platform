"""测试 bpy.utils API"""
import sys
sys.path.insert(0, "/python/MCP")
from blender_mcp import blender_exec

code = '''import bpy, pathlib
print("STEP1")
# 检查 bpy.utils 方法
print("script_path_user:", bpy.utils.script_path_user())
print("STEP2_user")
try:
    p = bpy.utils.script_path_prefs()
    print("script_path_prefs:", p)
except Exception as e:
    print("script_path_prefs ERR:", e)
print("STEP3_prefs")
# 检查是否有 script_path_pref (无s)
try:
    p2 = bpy.utils.script_path_pref()
    print("script_path_pref:", p2)
except Exception as e:
    print("script_path_pref ERR:", e)
print("STEP4")
'''

result = blender_exec(code)
print(result)
