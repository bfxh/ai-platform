#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender MCP - Blender自动化控制

通过命令行和Python脚本控制Blender，无需手动操作。

用法：
    python blender_mcp.py <action> [args...]

示例：
    python blender_mcp.py open                          # 打开Blender
    python blender_mcp.py run script.py                 # 在Blender中执行脚本
    python blender_mcp.py import model.glb              # 导入模型
    python blender_mcp.py import_dir D:/models/ glb     # 批量导入目录
    python blender_mcp.py export model.fbx              # 导出当前场景
    python blender_mcp.py render output.png             # 渲染当前场景
    python blender_mcp.py info                          # Blender版本信息
    python blender_mcp.py addons                        # 列出已安装插件
    python blender_mcp.py install_addon path.zip        # 安装插件
    python blender_mcp.py template char                 # 生成角色建模模板脚本
    python blender_mcp.py template pbr                  # 生成PBR材质模板脚本
    python blender_mcp.py template rig                  # 生成绑定模板脚本
    python blender_mcp.py template batch_import         # 生成批量导入脚本
    python blender_mcp.py template batch_export         # 生成批量导出脚本
    python blender_mcp.py template decimate             # 生成减面脚本
    python blender_mcp.py fix_materials dir             # 修复材质(关联贴图)
    python blender_mcp.py convert in.glb out.fbx        # 格式转换
"""

import json
import sys
import os
import subprocess
import shutil
from pathlib import Path

# ─── Blender 5.1 安装路径（2026-04-11 更新）───────────────────
BLENDER = Path("%SOFTWARE_DIR%/KF/JM/blender/blender.exe")
# Blender 内置 Python（用于 pip install 等）
BLENDER_PYTHON = Path("%SOFTWARE_DIR%/KF/JM/blender/5.1/python/bin/python.exe")
# Blender 用户插件目录（blenderkit/godot-exporter 等）
BLENDER_USER_ADDONS = Path("%SOFTWARE_DIR%/KF/JM/blender/scripts/addons")
# Blender 5.1 版本插件目录
BLENDER_51_ADDONS = Path("%SOFTWARE_DIR%/KF/JM/blender/5.1/scripts/addons")
# Blender → Godot ESCN 导出器（godot-blender-bridge）
ESCN_EXPORTER = Path("/python/addons/godot-blender-bridge/io_scene_godot")
SCRIPTS_DIR = Path("/python/MCP/blender_scripts")
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP = Path("/python/MCP/temp")
TEMP.mkdir(parents=True, exist_ok=True)


def blender_run(script_path, background=True):
    """在Blender中执行Python脚本"""
    cmd = [str(BLENDER)]
    if background:
        cmd.append("--background")
    cmd.extend(["--python", str(script_path)])

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120,
                                encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[blender_run error] {e}"

    if result is None or result.stdout is None:
        # Blender 崩溃或超时，返回 stderr
        return (result.stderr or "[no output]")[:500]

    # 过滤Blender启动噪音
    output = []
    for line in result.stdout.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith(('Read', 'Info', 'addon_utils', 'add-on')):
            output.append(stripped)
    return '\n'.join(output)


def blender_exec(code, background=True):
    """直接执行Python代码"""
    script = TEMP / "blender_exec.py"
    script.write_text(code, encoding='utf-8')
    return blender_run(str(script), background)


# ============================================================
# 脚本模板
# ============================================================
TEMPLATES = {
    "batch_import": '''import bpy, os

input_dir = "{input_dir}"
ext = "{ext}"
scale = {scale}

for f in os.listdir(input_dir):
    if f.lower().endswith(ext):
        filepath = os.path.join(input_dir, f)
        if ext in ['.glb', '.gltf']:
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext == '.obj':
            bpy.ops.wm.obj_import(filepath=filepath)
        elif ext == '.psk':
            bpy.ops.import_scene.psk(filepath=filepath)
        
        for obj in bpy.context.selected_objects:
            obj.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
        print(f"Imported: {{f}}")

print(f"Done! {{len(bpy.data.objects)}} objects")
''',

    "batch_export": '''import bpy, os

output_dir = "{output_dir}"
os.makedirs(output_dir, exist_ok=True)

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        filepath = os.path.join(output_dir, f"{{obj.name}}.{ext}")
        if "{ext}" == "fbx":
            bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True)
        elif "{ext}" == "glb":
            bpy.ops.export_scene.gltf(filepath=filepath, use_selection=True, export_format='GLB')
        elif "{ext}" == "obj":
            bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
        
        print(f"Exported: {{filepath}}")
''',

    "pbr_material": '''import bpy, os

def create_pbr(name, tex_dir):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    
    channel_map = {{
        'Base Color': ['_D', '_BC', '_Albedo', '_Diffuse', '_BaseColor', '_Color'],
        'Normal': ['_N', '_NM', '_Normal', '_Nor'],
        'Roughness': ['_R', '_RG', '_Roughness', '_Rough'],
        'Metallic': ['_M', '_MT', '_Metallic', '_Metal'],
        'Emission Color': ['_E', '_EM', '_Emissive', '_Emit'],
    }}
    
    for channel, suffixes in channel_map.items():
        for suffix in suffixes:
            for ext in ['.png', '.tga', '.jpg', '.jpeg']:
                tex_path = os.path.join(tex_dir, f"{{name}}{{suffix}}{{ext}}")
                if os.path.exists(tex_path):
                    tex = nodes.new('ShaderNodeTexImage')
                    tex.image = bpy.data.images.load(tex_path)
                    if channel == 'Normal':
                        tex.image.colorspace_settings.name = 'Non-Color'
                        nm = nodes.new('ShaderNodeNormalMap')
                        links.new(tex.outputs['Color'], nm.inputs['Color'])
                        links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
                    elif channel in ['Roughness', 'Metallic']:
                        tex.image.colorspace_settings.name = 'Non-Color'
                        links.new(tex.outputs['Color'], bsdf.inputs[channel])
                    else:
                        links.new(tex.outputs['Color'], bsdf.inputs[channel])
                    print(f"  {{channel}} ← {{tex_path}}")
                    break
            else:
                continue
            break
    
    return mat

# 使用
tex_dir = "{tex_dir}"
mat_name = "{mat_name}"
mat = create_pbr(mat_name, tex_dir)

# 应用到选中物体
for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        print(f"Applied to {{obj.name}}")
''',

    "decimate": '''import bpy

ratio = {ratio}

for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        before = len(obj.data.polygons)
        mod = obj.modifiers.new('Decimate', 'DECIMATE')
        mod.ratio = ratio
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='Decimate')
        after = len(obj.data.polygons)
        print(f"{{obj.name}}: {{before}} → {{after}} faces ({{after/before*100:.0f}}%)")
''',

    "rig_basic": '''import bpy

# 基础人形骨骼
bpy.ops.object.armature_add()
arm = bpy.context.active_object
arm.name = "Armature"

bpy.ops.object.mode_set(mode='EDIT')
bones = arm.data.edit_bones

# 脊柱
spine = bones['Bone']
spine.name = 'Spine'
spine.head = (0, 0, 1.0)
spine.tail = (0, 0, 1.3)

chest = bones.new('Chest')
chest.head = spine.tail
chest.tail = (0, 0, 1.5)
chest.parent = spine

neck = bones.new('Neck')
neck.head = chest.tail
neck.tail = (0, 0, 1.6)
neck.parent = chest

head = bones.new('Head')
head.head = neck.tail
head.tail = (0, 0, 1.8)
head.parent = neck

# 左臂
for side, sign in [('L', 1), ('R', -1)]:
    upper = bones.new(f'UpperArm.{{side}}')
    upper.head = (sign*0.2, 0, 1.45)
    upper.tail = (sign*0.5, 0, 1.45)
    upper.parent = chest
    
    lower = bones.new(f'LowerArm.{{side}}')
    lower.head = upper.tail
    lower.tail = (sign*0.8, 0, 1.45)
    lower.parent = upper
    
    hand = bones.new(f'Hand.{{side}}')
    hand.head = lower.tail
    hand.tail = (sign*0.95, 0, 1.45)
    hand.parent = lower

# 腿
hips = bones.new('Hips')
hips.head = (0, 0, 1.0)
hips.tail = (0, 0, 0.95)

for side, sign in [('L', 1), ('R', -1)]:
    thigh = bones.new(f'Thigh.{{side}}')
    thigh.head = (sign*0.1, 0, 0.95)
    thigh.tail = (sign*0.1, 0, 0.5)
    thigh.parent = hips
    
    shin = bones.new(f'Shin.{{side}}')
    shin.head = thigh.tail
    shin.tail = (sign*0.1, 0, 0.08)
    shin.parent = thigh
    
    foot = bones.new(f'Foot.{{side}}')
    foot.head = shin.tail
    foot.tail = (sign*0.1, -0.15, 0.0)
    foot.parent = shin

bpy.ops.object.mode_set(mode='OBJECT')
print("Basic humanoid rig created!")
''',

    "convert": '''import bpy, sys

input_file = "{input_file}"
output_file = "{output_file}"

# 清空场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 导入
ext = input_file.rsplit('.', 1)[-1].lower()
if ext in ['glb', 'gltf']:
    bpy.ops.import_scene.gltf(filepath=input_file)
elif ext == 'fbx':
    bpy.ops.import_scene.fbx(filepath=input_file)
elif ext == 'obj':
    bpy.ops.wm.obj_import(filepath=input_file)
elif ext == 'psk':
    bpy.ops.import_scene.psk(filepath=input_file)

# 导出
out_ext = output_file.rsplit('.', 1)[-1].lower()
if out_ext == 'fbx':
    bpy.ops.export_scene.fbx(filepath=output_file)
elif out_ext in ['glb', 'gltf']:
    fmt = 'GLB' if out_ext == 'glb' else 'GLTF_SEPARATE'
    bpy.ops.export_scene.gltf(filepath=output_file, export_format=fmt)
elif out_ext == 'obj':
    bpy.ops.wm.obj_export(filepath=output_file)

print(f"Converted: {{input_file}} → {{output_file}}")
''',

    # ── Godot ESCN 导出（godot-blender-bridge）────────────────
    "escn_export": """import bpy, os

output_file = r"{output_file}"
use_selection = {use_selection}

# ── Blender → Godot 资产管线 ─────────────────────────────
# 推荐: glTF 2.0（Godot 4.x 内置支持，Blender 内置导出器）
# godot-blender-exporter (escn) 与 Blender 5.x 存在 shader node API 不兼容
# 参考: https://github.com/godotengine/godot-blender-exporter README
#   "consider using glTF 2.0 instead. (The glTF 2.0 exporter is built-in.)"

# glTF 导出（Blender 内置，跨版本兼容）
export_format = "GLB" if output_file.lower().endswith(".glb") else "GLTF_SEPARATE"

try:
    bpy.ops.export_scene.gltf(
        filepath=output_file,
        export_format=export_format,
        use_selection=use_selection,
    )
    print("glTF 导出成功: " + output_file)
    print("  -> 复制到 Godot 项目 res:// 目录即可使用")
    print("  -> Godot 4.x: 直接拖入 .glb 文件，或 File -> Import -> glTF")
except AttributeError as e:
    print("glTF 导出操作符不可用: " + str(e))
except Exception as e:
    print("glTF 导出失败: " + str(e))
    print("  -> 备选: python blender_mcp.py export output.fbx")
""",

    # ── glTF → Godot 场景组装脚本 ───────────────────────────
    "godot_scene_assemble": """import bpy, os

asset_dir = r"{asset_dir}"
godot_project = r"{godot_project}"
scene_name = "{scene_name}"

# 清理场景
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# 导入所有 glTF/glb 文件
imported = []
for root, _, files in os.walk(asset_dir):
    for f in files:
        ext = f.lower().rsplit(".", 1)[-1]
        if ext in ["glb", "gltf"]:
            path = os.path.join(root, f)
            try:
                bpy.ops.import_scene.gltf(filepath=path)
                imported.append(f)
            except Exception as e:
                print("跳过 " + f + ": " + str(e))

print("已导入 " + str(len(imported)) + " 个资产: " + scene_name)
print("  提示: 导出为 glTF 后复制到 Godot 项目 res:// 目录")
print("  Godot 4.x 内置 glTF 支持: 直接拖入或 File → Import")
""",
}


# ─── BlenderKit / Godot Exporter 状态 ──────────────────────
def cmd_addons():
    """列出 Blender 中已安装的插件"""
    code = '''import bpy, pathlib

# 已启用的 addon
enabled = [a.module for a in bpy.context.preferences.addons]

# 扫描所有 addon 目录（用户目录 + Blender 安装目录）
addon_dirs = [
    pathlib.Path(bpy.utils.script_path_user()) / "addons",
]
all_addon_names = set()
for addon_base in addon_dirs:
    if addon_base.exists():
        for d in sorted(addon_base.iterdir()):
            if d.is_dir() and (d / "__init__.py").exists():
                all_addon_names.add(d.name)

# 检查 Blender 安装目录（blenderkit 等内置插件）
blender_install = pathlib.Path(bpy.app.binary_path).parent / "scripts" / "addons"
if blender_install.exists():
    for d in sorted(blender_install.iterdir()):
        if d.is_dir() and (d / "__init__.py").exists():
            all_addon_names.add(d.name)

print("=== 已启用插件 (%d 个) ===" % len(enabled))
for m in sorted(set(enabled)):
    print(m)

print()
print("=== 所有可用插件 (%d 个) ===" % len(all_addon_names))
for m in sorted(all_addon_names):
    status = "[已启用]" if m in enabled else ""
    print("  " + m + " " + status)

print()
print("=== BlenderKit 状态 ===")
if "blenderkit" in all_addon_names:
    if "blenderkit" in enabled:
        print("BlenderKit: 已启用")
        print("  → 配置 API Key: python blender_mcp.py blenderkit_login <your_api_key>")
    else:
        print("BlenderKit: 文件存在但未启用")
        print("  → 启用: Blender → Edit → Preferences → Add-ons → 搜索 blenderkit → 勾选")
else:
    print("BlenderKit: 未找到 (请从 blenderkit.com 下载 blenderkit.zip)")

print()
print("=== Godot Exporter 状态 ===")
if "io_scene_godot" in all_addon_names:
    if "io_scene_godot" in enabled:
        has_op = hasattr(bpy.ops.export_scene, "godot")
        print("Godot Exporter: 已启用")
        print("  export_scene.godot: " + ("可用" if has_op else "操作符未注册"))
        print("  用法: python blender_mcp.py escn output.escn")
    else:
        print("Godot Exporter: 文件存在但未启用")
        print("  → 启用: Blender → Edit → Preferences → Add-ons → 搜索 godot → 勾选")
        print("  → CLI导出: python blender_mcp.py escn output.escn")
else:
    print("Godot Exporter: 未安装")
    print("  → 运行: python blender_mcp.py install_godot_exporter")
'''
    print(blender_exec(code))


def cmd_install_addon(zip_path):
    """安装插件（ZIP 格式）"""
    code = f'''import bpy, addon_utils
bpy.ops.preferences.execute_opengl_module()
result = bpy.ops.preferences.addon_install(filepath=r"{zip_path}", filter="*.zip")
print(result)
'''
    print(blender_exec(code))


# ============================================================
# Godot / ESCN 相关命令
# ============================================================
def cmd_escn_export(output_file, use_selection=False):
    """导出为 Godot ESCN 格式"""
    code = TEMPLATES["escn_export"].format(
        output_file=output_file,
        use_selection=use_selection,
    )
    script = TEMP / "escn_export.py"
    script.write_text(code, encoding="utf-8")
    print(blender_run(str(script), background=True))


def cmd_godot_scene_assemble(asset_dir, godot_project, scene_name):
    """从 glTF 资产组装 Godot 场景"""
    code = TEMPLATES["godot_scene_assemble"].format(
        asset_dir=asset_dir,
        godot_project=godot_project,
        scene_name=scene_name,
    )
    script = TEMP / "godot_assemble.py"
    script.write_text(code, encoding="utf-8")
    print(blender_run(str(script), background=True))


def cmd_blenderkit_login(api_key):
    """配置 BlenderKit API Key"""
    code = f'''import bpy, json
try:
    import blenderkit.global_vars as gv
    gv.set("api_key", "{api_key}")
    gv.save_settings()
    print("BlenderKit API Key 已保存")
except Exception as e:
    print(f"配置 BlenderKit 失败: {{e}}")
'''
    print(blender_exec(code))


def cmd_blenderkit_search(query, category="model", count=20):
    """搜索 BlenderKit 资产（需配置 API Key）"""
    code = f'''import bpy, json
try:
    from blenderkit import search, tasks_queue, global_vars
    if not global_vars.get("api_key"):
        print("错误: BlenderKit 未配置 API Key (python blender_mcp.py blenderkit_login <api_key>)")
    else:
        search.search(text="{query}", categories="{{category}}", progress=None)
        print("BlenderKit 搜索已提交...")
        print("在 Blender 窗口中查看 BlenderKit 面板")
except Exception as e:
    print(f"BlenderKit 搜索失败: {{e}}")
'''
    print(blender_exec(code))


# ============================================================
# 命令处理
# ============================================================
def cmd_open():
    subprocess.Popen([str(BLENDER)])
    print(f"opened: {BLENDER}")

def cmd_run(script):
    output = blender_run(script, background=True)
    print(output)

def cmd_import(filepath, scale=1.0):
    ext = Path(filepath).suffix.lower()
    code = f"""import bpy
bpy.ops.import_scene.gltf(filepath=r'{filepath}')
for obj in bpy.context.selected_objects:
    obj.scale = ({scale}, {scale}, {scale})
bpy.ops.object.transform_apply(scale=True)
print(f"Imported: {{len(bpy.context.selected_objects)}} objects")
"""
    if ext == '.fbx':
        code = code.replace('import_scene.gltf', 'import_scene.fbx')
    elif ext == '.obj':
        code = code.replace('import_scene.gltf', 'wm.obj_import')
    
    print(blender_exec(code))

def cmd_export(filepath):
    ext = Path(filepath).suffix.lower()
    code = f"""import bpy
bpy.ops.export_scene.fbx(filepath=r'{filepath}')
print("Exported: {filepath}")
"""
    if ext in ['.glb', '.gltf']:
        code = code.replace('export_scene.fbx', 'export_scene.gltf')
    elif ext == '.obj':
        code = code.replace('export_scene.fbx', 'wm.obj_export')
    
    print(blender_exec(code))

def cmd_render(output, engine='CYCLES', samples=128):
    code = f"""import bpy
bpy.context.scene.render.engine = '{engine}'
if '{engine}' == 'CYCLES':
    bpy.context.scene.cycles.samples = {samples}
bpy.context.scene.render.filepath = r'{output}'
bpy.ops.render.render(write_still=True)
print("Rendered: {output}")
"""
    print(blender_exec(code))

def cmd_info():
    code = """import bpy
print(f"Blender {bpy.app.version_string}")
print(f"Python {bpy.app.version_string}")
print(f"Objects: {len(bpy.data.objects)}")
print(f"Meshes: {len(bpy.data.meshes)}")
print(f"Materials: {len(bpy.data.materials)}")
print(f"Textures: {len(bpy.data.images)}")
"""
    print(blender_exec(code))

def cmd_template(name, **kwargs):
    if name not in TEMPLATES:
        print(f"可用模板: {', '.join(TEMPLATES.keys())}")
        return
    
    # 默认值
    defaults = {
        "input_dir": "D:/搞阶跃的/Models",
        "output_dir": "D:/搞阶跃的/Export",
        "ext": ".glb",
        "scale": 0.01,
        "ratio": 0.5,
        "tex_dir": "D:/搞阶跃的/Textures",
        "mat_name": "Material",
        "input_file": "",
        "output_file": "",
    }
    defaults.update(kwargs)
    
    code = TEMPLATES[name].format(**defaults)
    
    # 保存脚本
    script_path = SCRIPTS_DIR / f"{name}.py"
    script_path.write_text(code, encoding='utf-8')
    print(f"模板脚本: {script_path}")
    print(f"在Blender中执行: 打开Blender > Scripting > 打开 {script_path} > 运行")
    print(f"或命令行: python {__file__} run {script_path}")

def cmd_convert(input_file, output_file):
    code = TEMPLATES["convert"].format(input_file=input_file, output_file=output_file)
    script = TEMP / "blender_convert.py"
    script.write_text(code, encoding='utf-8')
    output = blender_run(str(script), background=True)
    print(output)


def main():
    if len(sys.argv) < 2:
        print("""Blender MCP v2.0 - Blender 5.1 + Godot 自动化

用法: python blender_mcp.py <action> [args...]

  open                          打开Blender
  run <script.py>               执行脚本
  import <file> [scale]         导入模型(glTF/FBX/OBJ)
  export <file>                 导出场景(FBX/glTF)
  render <output.png> [engine]  渲染(CYCLES/EEVEE)
  info                          版本信息
  convert <in> <out>            格式转换
  addons                         列出已安装插件(BlenderKit/Godot Exporter)
  install_addon <zip>           安装插件(ZIP)
  escn|gltf <output.glb> [sel]  导出glTF/GLB(Blender→Godot推荐格式)
  godot_scene <assets/> <proj/> <name>  glTF资产组装Godot场景
  blenderkit_login <api_key>     BlenderKit登录
  blenderkit_search <query>     BlenderKit搜索资产
  template <name> [key=val]     生成脚本模板
    模板: batch_import, batch_export, pbr_material,
          decimate, rig_basic, convert, escn_export
          (blender内置glTF导出器, Godot 4.x内置glTF支持)""")
        return

    action = sys.argv[1]
    args = sys.argv[2:]

    if action == "open":
        cmd_open()
    elif action == "run":
        cmd_run(args[0] if args else "")
    elif action == "import":
        scale = float(args[1]) if len(args) > 1 else 1.0
        cmd_import(args[0] if args else "", scale)
    elif action == "export":
        cmd_export(args[0] if args else "output.fbx")
    elif action == "render":
        engine = args[1] if len(args) > 1 else "CYCLES"
        cmd_render(args[0] if args else "render.png", engine)
    elif action == "info":
        cmd_info()
    elif action == "convert":
        if len(args) >= 2:
            cmd_convert(args[0], args[1])
        else:
            print("用法: convert <input> <output>")
    elif action == "addons":
        cmd_addons()
    elif action == "install_addon":
        cmd_install_addon(args[0] if args else "")
    elif action == "escn":
        sel = (args[1] == "--sel") if len(args) > 1 else False
        cmd_escn_export(args[0] if args else "output.glb", use_selection=sel)
    elif action == "gltf":
        """导出 glTF/GLB（Blender → Godot 推荐格式）"""
        sel = (args[1] == "--sel") if len(args) > 1 else False
        cmd_escn_export(args[0] if args else "output.glb", use_selection=sel)
    elif action == "godot_scene":
        if len(args) >= 3:
            cmd_godot_scene_assemble(args[0], args[1], args[2])
        else:
            print("用法: godot_scene <assets_dir> <godot_project_path> <scene_name>")
    elif action == "blenderkit_login":
        cmd_blenderkit_login(args[0] if args else "")
    elif action == "blenderkit_search":
        query = args[0] if args else ""
        cat = args[1] if len(args) > 1 else "model"
        cmd_blenderkit_search(query, cat)
    elif action == "template":
        if args:
            cmd_template(args[0], **dict(a.split("=", 1) for a in args[1:] if "=" in a))
        else:
            print("用法: template <name> [key=val...]")
    else:
        print(f"未知命令: {action}")


if __name__ == '__main__':
    main()
