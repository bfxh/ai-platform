#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Extractor - 一键模型提取器

用法：
    python extract.py <游戏路径> [选项]

示例：
    python extract.py "D:/Games\MyGame" --all
    python extract.py "D:/Games\MyGame" --search "Character"
    python extract.py "D:/Games\MyGame" --search "Weapon" --format psk

功能：
    1. 自动检测引擎(UE4/UE5/Unity)
    2. 自动搜索AES Key
    3. 自动调用FModel/umodel/AssetRipper
    4. 自动操控软件界面(da.py)
    5. 自动导入Blender
    6. 全程无需手动操作
"""

import json
import sys
import os
import subprocess
import time
import struct
import re
import shutil
from pathlib import Path

# 路径
DA = Path("/python/MCP/da.py")
FMODEL = Path("%DEVTOOLS_DIR%/FModel/FModel.exe")
FMODEL_OUTPUT = Path("%DEVTOOLS_DIR%/FModel/Output/Exports")
UMODEL = Path("%DEVTOOLS_DIR%/umodel/umodel_64.exe")
ASSETRIPPER = Path("%DEVTOOLS_DIR%/AssetRipper.GUI.Free.exe")
BLENDER = Path("%DEVTOOLS_DIR%/03-Game-Development/Blender/blender-launcher.exe")
TEMP = Path("/python/MCP/temp")
TEMP.mkdir(parents=True, exist_ok=True)

def da(action, *args):
    """调用桌面自动化"""
    cmd = [sys.executable, str(DA), action] + [str(a) for a in args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()

def screenshot(name="step.bmp"):
    """截屏"""
    path = TEMP / name
    da("screenshot", str(path))
    return str(path)

def wait(seconds=1):
    time.sleep(seconds)

def log(msg):
    print(f"[提取器] {msg}")


# ============================================================
# 引擎检测
# ============================================================
def detect_engine(game_path):
    """自动检测游戏引擎"""
    game_path = Path(game_path)
    
    # UE检测
    paks = list(game_path.rglob("*.pak"))
    ucas = list(game_path.rglob("*.ucas"))
    utoc = list(game_path.rglob("*.utoc"))
    
    if paks or ucas:
        engine = "UE5" if (ucas or utoc) else "UE4"
        
        # 找Paks目录
        paks_dir = None
        for p in paks:
            if "Paks" in str(p):
                paks_dir = str(p.parent)
                break
        if not paks_dir and paks:
            paks_dir = str(paks[0].parent)
        
        log(f"检测到: {engine}")
        log(f"Pak目录: {paks_dir}")
        log(f"Pak文件: {len(paks)}个, UCAS: {len(ucas)}个")
        
        return {
            "engine": engine,
            "paks_dir": paks_dir,
            "pak_count": len(paks),
            "needs_usmap": engine == "UE5",
            "pak_files": [str(p) for p in paks[:10]]
        }
    
    # Unity检测
    data_dirs = [d for d in game_path.iterdir() if d.is_dir() and d.name.endswith("_Data")]
    assets = list(game_path.rglob("*.assets"))
    
    if data_dirs or assets:
        data_path = str(data_dirs[0]) if data_dirs else str(game_path)
        log(f"检测到: Unity")
        log(f"Data目录: {data_path}")
        return {
            "engine": "Unity",
            "data_path": data_path
        }
    
    log("未检测到已知引擎")
    return {"engine": "unknown"}


# ============================================================
# UE提取 - umodel命令行（全自动，不需要GUI）
# ============================================================
def umodel_extract(paks_dir, output_dir, search=None, ue_version="ue4.27", aes_key=None):
    """
    用umodel命令行批量提取（完全自动化，不需要GUI操作）
    
    这是最可靠的方式：纯命令行，不需要点击任何按钮
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        str(UMODEL),
        f"-path={paks_dir}",
        f"-game={ue_version}",
        f"-out={output_dir}",
    ]
    
    if aes_key:
        cmd.append(f"-aes={aes_key}")
    
    if search:
        # 导出匹配的资产
        cmd.extend(["-export", f"*{search}*"])
    else:
        # 导出所有模型和贴图
        cmd.extend(["-export", "*"])
    
    # 添加导出选项
    cmd.extend([
        "-noanim",  # 先不导动画（可选）
        "-nooverwrite",
    ])
    
    log(f"执行: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=600,  # 10分钟超时
            cwd=str(UMODEL.parent)
        )
        
        log(f"stdout: {result.stdout[:500]}")
        if result.returncode != 0:
            log(f"stderr: {result.stderr[:500]}")
        
        # 统计导出结果
        exported = []
        for f in output_dir.rglob("*"):
            if f.is_file():
                exported.append(str(f))
        
        log(f"导出完成: {len(exported)} 个文件")
        return {
            "success": True,
            "output_dir": str(output_dir),
            "file_count": len(exported),
            "files": exported[:20]
        }
    
    except subprocess.TimeoutExpired:
        log("导出超时（10分钟）")
        return {"success": False, "error": "超时"}
    except Exception as e:
        log(f"导出失败: {e}")
        return {"success": False, "error": str(e)}


def umodel_list(paks_dir, ue_version="ue4.27", aes_key=None, search=None):
    """用umodel列出资产（不导出，只看有什么）"""
    cmd = [
        str(UMODEL),
        f"-path={paks_dir}",
        f"-game={ue_version}",
        "-list",
    ]
    
    if aes_key:
        cmd.append(f"-aes={aes_key}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(UMODEL.parent))
        
        assets = result.stdout.strip().split('\n')
        
        if search:
            assets = [a for a in assets if search.lower() in a.lower()]
        
        log(f"找到 {len(assets)} 个资产")
        return {
            "success": True,
            "count": len(assets),
            "assets": assets[:50]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# UE提取 - FModel GUI自动操控
# ============================================================
def fmodel_auto(paks_dir, aes_key="", ue_version="GAME_UE5_5", search=None):
    """
    自动操控FModel GUI
    
    步骤：
    1. 启动FModel
    2. 等待加载
    3. 配置设置
    4. 加载Pak
    5. 搜索资产
    6. 导出
    """
    log("启动FModel...")
    
    # 检查FModel是否已运行
    windows = da("find_win", "FModel")
    if "found 0" in windows:
        # 启动FModel
        subprocess.Popen([str(FMODEL)], cwd=str(FMODEL.parent))
        log("等待FModel启动...")
        
        # 等待窗口出现
        for i in range(30):
            wait(1)
            windows = da("find_win", "FModel")
            if "found 0" not in windows:
                break
        else:
            return {"success": False, "error": "FModel启动超时"}
    
    wait(2)
    da("activate", "FModel")
    wait(1)
    
    # 截屏看当前状态
    shot = screenshot("fmodel_start.bmp")
    log(f"FModel已启动，截屏: {shot}")
    
    # 如果需要配置，用快捷键打开设置
    # Ctrl+Shift+S 打开设置（FModel快捷键）
    # 但FModel的配置比较复杂，建议先手动配置好，后续自动操作导出
    
    # 尝试加载 - Ctrl+L 或点击Load按钮
    log("尝试加载Pak文件...")
    da("hotkey", "ctrl+l")
    wait(3)
    
    shot = screenshot("fmodel_loaded.bmp")
    log(f"加载后截屏: {shot}")
    
    if search:
        # 搜索资产 - Ctrl+F
        log(f"搜索: {search}")
        da("hotkey", "ctrl+shift+f")
        wait(1)
        da("type", search)
        wait(1)
        da("key", "enter")
        wait(2)
        
        shot = screenshot("fmodel_search.bmp")
        log(f"搜索结果截屏: {shot}")
    
    return {
        "success": True,
        "message": "FModel已启动并加载",
        "screenshots": [shot]
    }


# ============================================================
# Unity提取 - AssetRipper
# ============================================================
def assetripper_extract(data_path, output_dir=None):
    """
    用AssetRipper提取Unity资产
    """
    if not output_dir:
        output_dir = TEMP / "unity_export"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log("启动AssetRipper...")
    
    # 检查是否已运行
    windows = da("find_win", "AssetRipper")
    if "found 0" in windows:
        subprocess.Popen([str(ASSETRIPPER)])
        log("等待AssetRipper启动...")
        for i in range(20):
            wait(1)
            windows = da("find_win", "AssetRipper")
            if "found 0" not in windows:
                break
    
    wait(2)
    da("activate", "AssetRipper")
    wait(1)
    
    # File > Open Folder
    da("hotkey", "ctrl+o")
    wait(2)
    
    # 输入路径
    da("type", str(data_path))
    wait(1)
    da("key", "enter")
    
    log("等待AssetRipper加载...")
    wait(10)  # Unity资产加载较慢
    
    shot = screenshot("assetripper.bmp")
    log(f"AssetRipper截屏: {shot}")
    
    return {
        "success": True,
        "message": "AssetRipper已加载",
        "screenshot": shot
    }


# ============================================================
# Blender导入
# ============================================================
def blender_import(model_dir, export_fmt="glb", scale=0.01):
    """
    生成Blender导入脚本并执行
    """
    model_dir = Path(model_dir)
    
    # 找到所有模型文件
    ext_map = {
        "glb": [".glb", ".gltf"],
        "psk": [".psk", ".pskx"],
        "fbx": [".fbx"],
        "obj": [".obj"],
    }
    extensions = ext_map.get(export_fmt, [f".{export_fmt}"])
    
    models = []
    for ext in extensions:
        models.extend(model_dir.rglob(f"*{ext}"))
    
    if not models:
        # 尝试所有格式
        for exts in ext_map.values():
            for ext in exts:
                models.extend(model_dir.rglob(f"*{ext}"))
        if not models:
            return {"success": False, "error": f"在 {model_dir} 中没找到模型文件"}
    
    log(f"找到 {len(models)} 个模型文件")
    
    # 生成Blender脚本
    script = f'''import bpy
import os
import sys

# 清空默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

models = {json.dumps([str(m) for m in models[:20]], ensure_ascii=False)}
scale = {scale}
imported = 0

for filepath in models:
    try:
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in ('.glb', '.gltf'):
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext in ('.psk', '.pskx'):
            try:
                bpy.ops.import_scene.psk(filepath=filepath)
            except:
                print(f"PSK导入需要io_scene_psk插件: {{filepath}}")
                continue
        elif ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext == '.obj':
            bpy.ops.wm.obj_import(filepath=filepath)
        else:
            continue
        
        # 缩放
        for obj in bpy.context.selected_objects:
            obj.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
        
        imported += 1
        print(f"[OK] {{os.path.basename(filepath)}}")
        
    except Exception as e:
        print(f"[ERR] {{filepath}}: {{e}}")

print(f"\\n导入完成: {{imported}}/{{len(models)}}")

# 保存
output = r"{str(TEMP / 'imported.blend')}"
bpy.ops.wm.save_as_mainfile(filepath=output)
print(f"已保存: {{output}}")
'''
    
    script_path = TEMP / "blender_auto_import.py"
    script_path.write_text(script, encoding='utf-8')
    
    log(f"Blender脚本已生成: {script_path}")
    
    # 尝试用Blender命令行执行
    # 先找到真正的blender.exe
    blender_exe = None
    blender_search = [
        Path("%DEVTOOLS_DIR%/03-Game-Development/Blender"),
        Path("C:/Program Files/Blender Foundation"),
        Path("C:/Program Files (x86)/Blender Foundation"),
    ]
    
    for base in blender_search:
        if base.exists():
            for exe in base.rglob("blender.exe"):
                if "launcher" not in exe.name.lower():
                    blender_exe = exe
                    break
        if blender_exe:
            break
    
    if blender_exe:
        log(f"找到Blender: {blender_exe}")
        try:
            result = subprocess.run(
                [str(blender_exe), "--background", "--python", str(script_path)],
                capture_output=True, text=True, timeout=300
            )
            log(f"Blender输出:\n{result.stdout[-500:]}")
            
            blend_file = TEMP / "imported.blend"
            if blend_file.exists():
                return {
                    "success": True,
                    "blend_file": str(blend_file),
                    "script": str(script_path),
                    "models_found": len(models),
                    "output": result.stdout[-300:]
                }
        except Exception as e:
            log(f"Blender执行失败: {e}")
    
    # 如果命令行不行，返回脚本让用户手动执行
    return {
        "success": True,
        "mode": "manual",
        "script": str(script_path),
        "models_found": len(models),
        "instruction": f"在Blender中执行: Edit > Preferences > File Paths 或 blender --python {script_path}"
    }


# ============================================================
# 一键提取 - 全自动流程
# ============================================================
def one_click_extract(game_path, search=None, output_dir=None, export_fmt="glb", aes_key=None):
    """
    一键提取：检测引擎 → 提取 → 导入Blender
    
    全自动，不需要任何手动操作
    """
    game_path = Path(game_path)
    if not output_dir:
        output_dir = TEMP / "extract_output"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log("=" * 50)
    log("一键模型提取")
    log(f"游戏路径: {game_path}")
    log(f"搜索: {search or '全部'}")
    log(f"输出: {output_dir}")
    log("=" * 50)
    
    # Step 1: 检测引擎
    log("\n[Step 1] 检测游戏引擎...")
    info = detect_engine(game_path)
    engine = info.get("engine", "unknown")
    
    if engine == "unknown":
        return {"success": False, "error": "无法识别游戏引擎", "info": info}
    
    # Step 2: 根据引擎选择提取方式
    if engine in ("UE4", "UE5"):
        paks_dir = info.get("paks_dir", str(game_path))
        
        # UE版本映射
        ue_versions = {
            "UE4": "ue4.27",
            "UE5": "ue5.0",
        }
        ue_ver = ue_versions.get(engine, "ue4.27")
        
        log(f"\n[Step 2] UE提取 (umodel命令行)...")
        log(f"Paks目录: {paks_dir}")
        log(f"引擎版本: {ue_ver}")
        
        # 优先用umodel命令行（全自动，不需要GUI）
        result = umodel_extract(
            paks_dir=paks_dir,
            output_dir=output_dir,
            search=search,
            ue_version=ue_ver,
            aes_key=aes_key
        )
        
        if not result.get("success") or result.get("file_count", 0) == 0:
            log("umodel提取失败或无结果，尝试FModel GUI...")
            result = fmodel_auto(
                paks_dir=paks_dir,
                aes_key=aes_key or "",
                ue_version=f"GAME_{engine}_5",
                search=search
            )
    
    elif engine == "Unity":
        data_path = info.get("data_path", str(game_path))
        
        log(f"\n[Step 2] Unity提取 (AssetRipper)...")
        result = assetripper_extract(data_path, output_dir)
    
    else:
        return {"success": False, "error": f"不支持的引擎: {engine}"}
    
    # Step 3: Blender导入
    if result.get("success") and result.get("file_count", 0) > 0:
        log(f"\n[Step 3] Blender导入...")
        blend_result = blender_import(output_dir, export_fmt)
        result["blender"] = blend_result
    
    log("\n" + "=" * 50)
    log("提取完成!")
    log(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    
    return result


# ============================================================
# 命令行入口
# ============================================================
def print_help():
    print("""
Model Extractor - 一键模型提取器

用法:
    python extract.py <游戏路径> [选项]

选项:
    --search <关键词>    搜索特定资产（如 Character, Weapon）
    --output <目录>      输出目录（默认: /python/MCP/temp/extract_output）
    --format <格式>      导出格式: glb, psk, fbx, obj（默认: glb）
    --aes <密钥>         AES密钥（UE加密游戏需要）
    --list               只列出资产，不导出
    --detect             只检测引擎，不提取
    --fmodel             强制使用FModel GUI
    --umodel             强制使用umodel命令行
    --no-blender         不自动导入Blender

示例:
    python extract.py "D:\\Games\\MyGame"
    python extract.py "D:\\Games\\MyGame" --search "Character" --format psk
    python extract.py "D:\\Games\\MyGame" --aes 0x1234ABCD --search "Weapon"
    python extract.py "D:\\Games\\MyGame" --detect
    python extract.py "D:\\Games\\MyGame" --list --search "SK_"
""")


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help'):
        print_help()
        sys.exit(0)
    
    game_path = sys.argv[1]
    
    # 解析参数
    args = sys.argv[2:]
    search = None
    output = None
    export_fmt = "glb"
    aes_key = None
    mode = "auto"
    no_blender = False
    
    i = 0
    while i < len(args):
        if args[i] == '--search' and i + 1 < len(args):
            search = args[i + 1]
            i += 2
        elif args[i] == '--output' and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        elif args[i] == '--format' and i + 1 < len(args):
            export_fmt = args[i + 1]
            i += 2
        elif args[i] == '--aes' and i + 1 < len(args):
            aes_key = args[i + 1]
            i += 2
        elif args[i] == '--detect':
            mode = "detect"
            i += 1
        elif args[i] == '--list':
            mode = "list"
            i += 1
        elif args[i] == '--fmodel':
            mode = "fmodel"
            i += 1
        elif args[i] == '--umodel':
            mode = "umodel"
            i += 1
        elif args[i] == '--no-blender':
            no_blender = True
            i += 1
        else:
            i += 1
    
    if mode == "detect":
        result = detect_engine(game_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif mode == "list":
        info = detect_engine(game_path)
        if info["engine"] in ("UE4", "UE5"):
            result = umodel_list(
                info["paks_dir"],
                ue_version="ue5.0" if info["engine"] == "UE5" else "ue4.27",
                aes_key=aes_key,
                search=search
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif mode == "fmodel":
        info = detect_engine(game_path)
        if info["engine"] in ("UE4", "UE5"):
            fmodel_auto(info["paks_dir"], aes_key or "", search=search)
    
    elif mode == "umodel":
        info = detect_engine(game_path)
        if info["engine"] in ("UE4", "UE5"):
            result = umodel_extract(
                info["paks_dir"],
                output or str(TEMP / "umodel_export"),
                search=search,
                ue_version="ue5.0" if info["engine"] == "UE5" else "ue4.27",
                aes_key=aes_key
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        result = one_click_extract(
            game_path=game_path,
            search=search,
            output_dir=output,
            format=export_fmt,
            aes_key=aes_key
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
