#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unreal Engine MCP - 虚幻引擎工具集

管理本地UE安装、项目、插件、资产，提供自动化操作。

功能：
1. UE安装管理 - 检测本地UE版本、路径
2. 项目管理 - 创建/打开/编译UE项目
3. 插件管理 - 搜索/安装/启用插件
4. 资产操作 - 导入/导出/转换资产
5. 蓝图工具 - 蓝图模板生成
6. 打包构建 - 自动化打包
7. 命令行工具 - UAT/UBT/UnrealPak调用
8. Fab商店 - 搜索Fab上的免费资产

用法：
    python ue_mcp.py <action> [args...]

示例：
    python ue_mcp.py versions                    # 列出本地UE版本
    python ue_mcp.py projects                    # 列出UE项目
    python ue_mcp.py open <project.uproject>     # 打开项目
    python ue_mcp.py plugins <ue_version>        # 列出已安装插件
    python ue_mcp.py plugin_search <keyword>     # 搜索插件
    python ue_mcp.py cook <project> <platform>   # 打包项目
    python ue_mcp.py pak_list <pak_file>          # 列出Pak内容
    python ue_mcp.py pak_extract <pak> <output>   # 解包Pak
    python ue_mcp.py pak_create <dir> <output>    # 创建Pak
    python ue_mcp.py import_fbx <fbx> <project>   # 导入FBX
    python ue_mcp.py run_cmd <ue_ver> <command>   # 执行UE命令
    python ue_mcp.py fab_search <keyword>         # 搜索Fab资产
"""

import json
import sys
import os
import subprocess
import re
import shutil
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# UE安装检测
# ============================================================
# 常见UE安装路径
UE_SEARCH_PATHS = [
    Path("%DEVTOOLS_DIR%/游戏引擎"),
    Path("C:/Program Files/Epic Games"),
    Path("D:/Epic Games"),
    Path("E:/Epic Games"),
    Path("C:/UE"),
    Path("D:/UE"),
]

# 缓存
_ue_installations = None


def find_ue_installations():
    """查找所有本地UE安装"""
    global _ue_installations
    if _ue_installations is not None:
        return _ue_installations
    
    installations = []
    
    for search_path in UE_SEARCH_PATHS:
        if not search_path.exists():
            continue
        
        # 直接子目录中查找
        for d in search_path.iterdir():
            if not d.is_dir():
                continue
            
            # 检查是否是UE安装
            engine_dir = d / "Engine"
            if not engine_dir.exists():
                # 可能在子目录中
                for sub in d.iterdir():
                    if sub.is_dir() and (sub / "Engine").exists():
                        engine_dir = sub / "Engine"
                        d = sub
                        break
                else:
                    continue
            
            # 获取版本
            version_file = engine_dir / "Build" / "Build.version"
            version = "unknown"
            if version_file.exists():
                try:
                    with open(version_file, 'r') as f:
                        vdata = json.load(f)
                    version = f"{vdata.get('MajorVersion', '?')}.{vdata.get('MinorVersion', '?')}.{vdata.get('PatchVersion', '?')}"
                except:
                    pass
            
            # 从目录名推断版本
            if version == "unknown":
                m = re.search(r'(\d+\.\d+)', d.name)
                if m:
                    version = m.group(1)
            
            # 检查关键可执行文件
            editor_exe = engine_dir / "Binaries" / "Win64" / "UnrealEditor.exe"
            if not editor_exe.exists():
                editor_exe = engine_dir / "Binaries" / "Win64" / "UE4Editor.exe"
            
            uat = engine_dir / "Build" / "BatchFiles" / "RunUAT.bat"
            ubt = engine_dir / "Build" / "BatchFiles" / "Build.bat"
            unrealpak = engine_dir / "Binaries" / "Win64" / "UnrealPak.exe"
            
            installations.append({
                "version": version,
                "path": str(d),
                "engine": str(engine_dir),
                "editor": str(editor_exe) if editor_exe.exists() else None,
                "uat": str(uat) if uat.exists() else None,
                "ubt": str(ubt) if ubt.exists() else None,
                "unrealpak": str(unrealpak) if unrealpak.exists() else None,
                "name": d.name,
            })
    
    installations.sort(key=lambda x: x['version'], reverse=True)
    _ue_installations = installations
    return installations


def list_versions():
    """列出所有本地UE版本"""
    installs = find_ue_installations()
    
    if not installs:
        print("未找到UE安装")
        return []
    
    print(f"找到 {len(installs)} 个UE安装:")
    for i, inst in enumerate(installs):
        editor = "✓" if inst['editor'] else "✗"
        pak = "✓" if inst['unrealpak'] else "✗"
        print(f"  [{i+1}] UE {inst['version']:8s} Editor={editor} Pak={pak} {inst['path']}")
    
    return installs


def get_ue(version=None):
    """获取指定版本的UE安装信息"""
    installs = find_ue_installations()
    if not installs:
        return None
    
    if version:
        for inst in installs:
            if version in inst['version'] or version in inst['name']:
                return inst
    
    return installs[0]  # 返回最新版


# ============================================================
# 项目管理
# ============================================================
def find_projects(search_dirs=None):
    """查找UE项目"""
    if search_dirs is None:
        search_dirs = [
            Path("D:/"),
            Path("E:/"),
            Path("C:/Users"),
        ]
    
    projects = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        # 搜索.uproject文件（限制深度）
        for uproject in search_dir.rglob("*.uproject"):
            # 限制搜索深度
            rel = uproject.relative_to(search_dir)
            if len(rel.parts) > 5:
                continue
            
            try:
                with open(uproject, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                projects.append({
                    "name": uproject.stem,
                    "path": str(uproject),
                    "dir": str(uproject.parent),
                    "engine_version": data.get("EngineAssociation", "unknown"),
                    "modules": [m.get("Name", "") for m in data.get("Modules", [])],
                    "plugins": len(data.get("Plugins", [])),
                })
            except:
                projects.append({
                    "name": uproject.stem,
                    "path": str(uproject),
                    "dir": str(uproject.parent),
                })
    
    return projects


def list_projects():
    """列出UE项目"""
    projects = find_projects()
    
    print(f"找到 {len(projects)} 个UE项目:")
    for p in projects:
        ver = p.get('engine_version', '?')
        print(f"  {p['name']:30s} UE={ver:10s} {p['dir']}")
    
    return projects


def open_project(uproject_path):
    """打开UE项目"""
    uproject = Path(uproject_path)
    if not uproject.exists():
        print(f"项目不存在: {uproject}")
        return False
    
    # 读取项目信息
    with open(uproject, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    engine_ver = data.get("EngineAssociation", "")
    
    # 找到对应的UE编辑器
    ue = get_ue(engine_ver)
    if ue and ue['editor']:
        print(f"打开项目: {uproject.stem} (UE {engine_ver})")
        subprocess.Popen([ue['editor'], str(uproject)])
        return True
    
    # 直接用关联程序打开
    os.startfile(str(uproject))
    print(f"打开项目: {uproject.stem}")
    return True


# ============================================================
# 插件管理
# ============================================================
def list_plugins(ue_version=None):
    """列出已安装的插件"""
    ue = get_ue(ue_version)
    if not ue:
        print("未找到UE安装")
        return []
    
    plugins_dir = Path(ue['engine']) / "Plugins"
    plugins = []
    
    if plugins_dir.exists():
        for uplugin in plugins_dir.rglob("*.uplugin"):
            try:
                with open(uplugin, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                plugins.append({
                    "name": data.get("FriendlyName", uplugin.stem),
                    "description": data.get("Description", "")[:80],
                    "category": data.get("Category", ""),
                    "version": data.get("VersionName", ""),
                    "enabled": data.get("EnabledByDefault", False),
                    "path": str(uplugin),
                })
            except:
                plugins.append({"name": uplugin.stem, "path": str(uplugin)})
    
    print(f"UE {ue['version']} 插件 ({len(plugins)} 个):")
    for p in plugins[:30]:
        enabled = "ON " if p.get('enabled') else "OFF"
        print(f"  [{enabled}] {p['name']:30s} {p.get('category', ''):20s} {p.get('version', '')}")
    
    if len(plugins) > 30:
        print(f"  ... 还有 {len(plugins)-30} 个")
    
    return plugins


def search_plugins(keyword, ue_version=None):
    """搜索插件"""
    plugins = list_plugins.__wrapped__(ue_version) if hasattr(list_plugins, '__wrapped__') else []
    
    ue = get_ue(ue_version)
    if not ue:
        return []
    
    plugins_dir = Path(ue['engine']) / "Plugins"
    all_plugins = []
    
    if plugins_dir.exists():
        for uplugin in plugins_dir.rglob("*.uplugin"):
            try:
                with open(uplugin, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_plugins.append({
                    "name": data.get("FriendlyName", uplugin.stem),
                    "description": data.get("Description", ""),
                    "category": data.get("Category", ""),
                    "path": str(uplugin),
                })
            except:
                pass
    
    keyword_lower = keyword.lower()
    results = [p for p in all_plugins if 
               keyword_lower in p.get('name', '').lower() or 
               keyword_lower in p.get('description', '').lower() or
               keyword_lower in p.get('category', '').lower()]
    
    print(f"搜索 '{keyword}' 在 UE {ue['version']}:")
    for p in results:
        print(f"  {p['name']:30s} {p.get('description', '')[:60]}")
    
    if not results:
        print("  未找到匹配的插件")
    
    return results


# ============================================================
# UnrealPak 操作
# ============================================================
def pak_list(pak_path, ue_version=None):
    """列出Pak文件内容"""
    ue = get_ue(ue_version)
    if not ue or not ue['unrealpak']:
        print("未找到UnrealPak")
        return []
    
    result = subprocess.run(
        [ue['unrealpak'], pak_path, '-List'],
        capture_output=True, text=True, timeout=60
    )
    
    files = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if line.startswith('"') or '/' in line:
            files.append(line.strip('"'))
    
    print(f"Pak: {pak_path}")
    print(f"  {len(files)} files")
    for f in files[:20]:
        print(f"  {f}")
    if len(files) > 20:
        print(f"  ... 还有 {len(files)-20} 个")
    
    return files


def pak_extract(pak_path, output_dir, ue_version=None):
    """解包Pak文件"""
    ue = get_ue(ue_version)
    if not ue or not ue['unrealpak']:
        print("未找到UnrealPak")
        return False
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"解包: {pak_path} -> {output_dir}")
    result = subprocess.run(
        [ue['unrealpak'], pak_path, '-Extract', output_dir],
        capture_output=True, text=True, timeout=300
    )
    
    print(result.stdout[:500])
    if result.returncode == 0:
        print("解包完成")
        return True
    else:
        print(f"解包失败: {result.stderr[:200]}")
        return False


def pak_create(input_dir, output_pak, ue_version=None):
    """创建Pak文件"""
    ue = get_ue(ue_version)
    if not ue or not ue['unrealpak']:
        print("未找到UnrealPak")
        return False
    
    # 创建响应文件
    response_file = Path(input_dir) / "_response.txt"
    with open(response_file, 'w') as f:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.startswith('_'):
                    continue
                full = os.path.join(root, file)
                rel = os.path.relpath(full, input_dir)
                f.write(f'"{full}" "../../../{rel}"\n')
    
    print(f"创建Pak: {input_dir} -> {output_pak}")
    result = subprocess.run(
        [ue['unrealpak'], output_pak, f'-Create={response_file}'],
        capture_output=True, text=True, timeout=300
    )
    
    response_file.unlink(missing_ok=True)
    
    if result.returncode == 0:
        print("创建完成")
        return True
    else:
        print(f"创建失败: {result.stderr[:200]}")
        return False


# ============================================================
# UAT 命令
# ============================================================
def run_uat(command, ue_version=None, extra_args=None):
    """运行UAT命令"""
    ue = get_ue(ue_version)
    if not ue or not ue['uat']:
        print("未找到RunUAT")
        return None
    
    cmd = [ue['uat'], command]
    if extra_args:
        cmd.extend(extra_args)
    
    print(f"UAT: {' '.join(cmd[:5])}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    print(result.stdout[-500:])
    return result


def cook_project(uproject_path, platform="Win64", ue_version=None):
    """打包项目"""
    ue = get_ue(ue_version)
    if not ue or not ue['uat']:
        print("未找到RunUAT")
        return False
    
    print(f"打包: {uproject_path} for {platform}")
    
    result = subprocess.run([
        ue['uat'],
        'BuildCookRun',
        f'-project={uproject_path}',
        f'-targetplatform={platform}',
        '-clientconfig=Shipping',
        '-cook',
        '-stage',
        '-pak',
        '-archive',
        '-build',
    ], capture_output=True, text=True, timeout=3600)
    
    if result.returncode == 0:
        print("打包完成")
        return True
    else:
        print(f"打包失败")
        print(result.stderr[-500:])
        return False


# ============================================================
# Fab搜索
# ============================================================
def fab_search(keyword):
    """搜索Fab商店资产"""
    import urllib.request
    
    url = f"https://www.fab.com/search?q={urllib.parse.quote(keyword)}"
    print(f"Fab搜索: {keyword}")
    print(f"  链接: {url}")
    print(f"  (需要在浏览器中打开查看结果)")
    return {"url": url, "keyword": keyword}


# ============================================================
# CLI
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""Unreal Engine MCP - 虚幻引擎工具集

用法: python ue_mcp.py <action> [args...]

UE管理:
  versions                      列出本地UE版本
  projects                      列出UE项目
  open <project.uproject>       打开项目
  plugins [ue_ver]              列出插件
  plugin_search <keyword>       搜索插件

Pak操作:
  pak_list <pak_file>           列出Pak内容
  pak_extract <pak> <output>    解包Pak
  pak_create <dir> <output>     创建Pak

构建:
  cook <project> [platform]     打包项目
  run_cmd <command> [args...]   执行UAT命令

资产:
  fab_search <keyword>          搜索Fab商店""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "versions":
        list_versions()
    elif action == "projects":
        list_projects()
    elif action == "open":
        if args:
            open_project(args[0])
        else:
            print("用法: open <project.uproject>")
    elif action == "plugins":
        list_plugins(args[0] if args else None)
    elif action == "plugin_search":
        if args:
            search_plugins(args[0], args[1] if len(args) > 1 else None)
        else:
            print("用法: plugin_search <keyword>")
    elif action == "pak_list":
        if args:
            pak_list(args[0])
        else:
            print("用法: pak_list <pak_file>")
    elif action == "pak_extract":
        if len(args) >= 2:
            pak_extract(args[0], args[1])
        else:
            print("用法: pak_extract <pak> <output_dir>")
    elif action == "pak_create":
        if len(args) >= 2:
            pak_create(args[0], args[1])
        else:
            print("用法: pak_create <input_dir> <output.pak>")
    elif action == "cook":
        if args:
            cook_project(args[0], args[1] if len(args) > 1 else "Win64")
        else:
            print("用法: cook <project.uproject> [platform]")
    elif action == "run_cmd":
        if args:
            run_uat(args[0], extra_args=args[1:])
        else:
            print("用法: run_cmd <command> [args...]")
    elif action == "fab_search":
        if args:
            fab_search(' '.join(args))
        else:
            print("用法: fab_search <keyword>")
    else:
        print(f"未知动作: {action}")


if __name__ == '__main__':
    main()
