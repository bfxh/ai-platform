import bpy, os, sys
sys.path.insert(0, "/python/MCP")
from blender_mcp import blender_exec

code = """import bpy, inspect

# 获取 glTF 导出操作符的参数
op = bpy.ops.export_scene.gltf
print("glTF export operator params:")
sig = None
try:
    import io
    from io import BytesIO
    # 尝试获取参数
    import ast
    print("Checking Blender API for gltf export params...")
except:
    pass

# 列出 glTF exporter 可用的关键字
params = [
    "filepath", "export_format", "use_selection",
    "export_materials", "export_normals", "export_texcoords",
    "export_colors", "export_attributes",
]
for p in params:
    print("  param:", p)
"""

result = blender_exec(code)
print(result)
