#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev Manager MCP - D:\\Dev 软件管理中心

管理D:\\Dev下所有软件的安装/配置/更新/启动。

用法：
    python dev_mgr.py list                       # 列出所有软件(按分类)
    python dev_mgr.py find <keyword>             # 搜索软件
    python dev_mgr.py open <name>                # 打开软件
    python dev_mgr.py path <name>                # 获取路径
    python dev_mgr.py install <name>             # 安装软件(从预设源)
    python dev_mgr.py download <name>            # 下载软件(不安装)
    python dev_mgr.py update <name>              # 更新软件
    python dev_mgr.py config <name>              # 查看/编辑配置
    python dev_mgr.py info <name>                # 软件详细信息
    python dev_mgr.py tree                       # 目录树
    python dev_mgr.py check                      # 检查所有软件状态
    python dev_mgr.py backup <name>              # 备份配置
    python dev_mgr.py restore <name>             # 恢复配置
"""

import json
import sys
import os
import subprocess
import shutil
import ssl
import urllib.request
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, r"\python")
from core.secure_utils import create_ssl_context

DEV = Path("%DEVTOOLS_DIR%")
CATALOG_FILE = DEV / "catalog.json"
BACKUP_DIR = DEV / "_backups"
BACKUP_DIR.mkdir(exist_ok=True)

ctx = create_ssl_context()
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# ============================================================
# 软件目录（%DEVTOOLS_DIR%的完整映射）
# ============================================================
CATALOG = {
    # === 提取器 ===
    "fmodel": {
        "name": "FModel",
        "path": "%DEVTOOLS_DIR%/提取器/FModel_EN",
        "exe": "FModel.exe",
        "desc": "UE4/UE5资产浏览器和导出工具",
        "category": "提取器",
        "config_path": "C:/Users/abc/AppData/Local/FModel",
        "download": {"type": "github", "repo": "4sval/FModel", "asset": "FModel.exe"},
        "version_cmd": None
    },
    "fmodel_cn": {
        "name": "FModel汉化版",
        "path": "%DEVTOOLS_DIR%/提取器/FModel_汉化版",
        "exe": "FModel.exe",
        "desc": "FModel中文版",
        "category": "提取器",
        "config_path": "C:/Users/abc/AppData/Local/FModel"
    },
    "umodel": {
        "name": "UEViewer (umodel)",
        "path": "%DEVTOOLS_DIR%/RJ/umodel",
        "exe": "umodel_64.exe",
        "desc": "UE模型批量导出，命令行友好",
        "category": "提取器",
        "download": {"type": "url", "url": "https://www.gildor.org/down/51/umodel/umodel_win32.zip"}
    },
    "assetripper": {
        "name": "AssetRipper",
        "path": "%DEVTOOLS_DIR%",
        "exe": "AssetRipper.GUI.Free.exe",
        "desc": "Unity游戏资产提取",
        "category": "提取器",
        "download": {"type": "github", "repo": "AssetRipper/AssetRipper", "asset": "AssetRipper_win_x64.zip"}
    },
    "assetstudio": {
        "name": "AssetStudio",
        "path": "%DEVTOOLS_DIR%/RJ/AssetStudio",
        "exe": "AssetStudioGUI.exe",
        "desc": "Unity资产查看器",
        "category": "提取器"
    },
    "ilspy": {
        "name": "ILSpy",
        "path": "%DEVTOOLS_DIR%/逆向工程/ILSpy",
        "exe": "ILSpy.exe",
        "desc": ".NET反编译器",
        "category": "逆向工程",
        "download": {"type": "github", "repo": "icsharpcode/ILSpy", "asset": "ILSpy_Binaries"}
    },

    # === 游戏引擎 ===
    "blender": {
        "name": "Blender",
        "path": "%DEVTOOLS_DIR%/DevEnv/GameEngines/游戏引擎/Blender",
        "exe": "blender.exe",
        "desc": "3D建模/动画/渲染",
        "category": "游戏引擎",
        "download": {"type": "url", "url": "https://www.blender.org/download/"}
    },
    "unity_hub": {
        "name": "Unity Hub",
        "path": "%DEVTOOLS_DIR%/DevEnv/GameEngines/UnityHub",
        "exe": "Unity Hub.exe",
        "desc": "Unity项目管理器",
        "category": "游戏引擎",
        "config_path": "C:/Users/abc/AppData/Roaming/UnityHub"
    },
    "ue5": {
        "name": "Unreal Engine 5.7",
        "path": "%DEVTOOLS_DIR%/DevEnv/GameEngines/游戏引擎/UE_5.7",
        "exe": "Engine/Binaries/Win64/UnrealEditor.exe",
        "desc": "虚幻引擎5.7",
        "category": "游戏引擎"
    },
    "epic_launcher": {
        "name": "Epic Games Launcher",
        "path": "%DEVTOOLS_DIR%/Epic Games/Launcher",
        "exe": "Portal/Binaries/Win64/EpicGamesLauncher.exe",
        "desc": "Epic Games启动器",
        "category": "游戏引擎"
    },

    # === 开发工具 ===
    "vscode": {
        "name": "VS Code",
        "path": "%DEVTOOLS_DIR%/DevEnv/IDETools/VSCode",
        "exe": "Code.exe",
        "desc": "代码编辑器",
        "category": "开发工具",
        "download": {"type": "url", "url": "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-archive"}
    },
    "deveco": {
        "name": "DevEco Testing",
        "path": "%DEVTOOLS_DIR%/DevEnv/IDETools/DevEco Testing",
        "exe": "bin/DevEcoTesting.exe",
        "desc": "HarmonyOS测试工具",
        "category": "开发工具"
    },

    # === 系统工具 ===
    "7zip": {
        "name": "7-Zip",
        "path": "%DEVTOOLS_DIR%/Installers",
        "exe": "7z-setup.exe",
        "desc": "压缩解压工具",
        "category": "系统工具",
        "download": {"type": "url", "url": "https://www.7-zip.org/a/7z2408-x64.exe"}
    },
    "toolbox": {
        "name": "图吧工具箱",
        "path": "%DEVTOOLS_DIR%/System/图吧工具箱202403",
        "exe": "",
        "desc": "硬件检测工具合集",
        "category": "系统工具"
    },

    # === 常用下载源 ===
    "renderdoc": {
        "name": "RenderDoc",
        "path": "%DEVTOOLS_DIR%/工具",
        "exe": "qrenderdoc.exe",
        "desc": "GPU调试器",
        "category": "调试工具",
        "download": {"type": "url", "url": "https://renderdoc.org/stable/1.36/RenderDoc_1.36_64.zip"},
        "installed": False
    },
    "dnspy": {
        "name": "dnSpy",
        "path": "%DEVTOOLS_DIR%/逆向工程",
        "exe": "dnSpy.exe",
        "desc": ".NET调试器和反编译器",
        "category": "逆向工程",
        "download": {"type": "github", "repo": "dnSpyEx/dnSpy", "asset": "dnSpy-net-win64.zip"},
        "installed": False
    },
    "ninja_ripper": {
        "name": "Ninja Ripper",
        "path": "%DEVTOOLS_DIR%/提取器",
        "exe": "NinjaRipper.exe",
        "desc": "运行时3D模型抓取",
        "category": "提取器",
        "download": {"type": "url", "url": "https://ninjaripper.com/download/"},
        "installed": False
    },
}


def get_full_exe_path(tool):
    """获取完整exe路径"""
    p = Path(tool["path"]) / tool.get("exe", "")
    return p if p.exists() else None


def save_catalog():
    """保存目录到文件"""
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(CATALOG, f, ensure_ascii=False, indent=1)


# ============================================================
# 命令实现
# ============================================================
def cmd_list():
    """按分类列出所有软件"""
    categories = {}
    for tid, tool in CATALOG.items():
        cat = tool.get("category", "未分类")
        categories.setdefault(cat, []).append((tid, tool))
    
    for cat in sorted(categories.keys()):
        tools = categories[cat]
        print(f"\n{'='*50}")
        print(f"  {cat} ({len(tools)})")
        print(f"{'='*50}")
        for tid, tool in sorted(tools, key=lambda x: x[1]["name"]):
            exe = get_full_exe_path(tool)
            status = "✓" if exe and exe.exists() else "✗"
            print(f"  {status} {tid:18s} {tool['name']:25s} {tool['desc'][:35]}")


def cmd_find(keyword):
    """搜索软件"""
    kw = keyword.lower()
    results = []
    for tid, tool in CATALOG.items():
        if (kw in tid.lower() or kw in tool["name"].lower() or 
            kw in tool.get("desc", "").lower() or kw in tool.get("category", "").lower()):
            results.append((tid, tool))
    
    if results:
        print(f"搜索 '{keyword}': {len(results)} 个结果")
        for tid, tool in results:
            exe = get_full_exe_path(tool)
            status = "✓" if exe and exe.exists() else "✗"
            print(f"  {status} {tid:18s} {tool['name']:25s} {tool['path']}")
    else:
        print(f"未找到: {keyword}")


def cmd_open(name):
    """打开软件"""
    tool = CATALOG.get(name)
    if not tool:
        # 模糊匹配
        for tid, t in CATALOG.items():
            if name.lower() in tid.lower() or name.lower() in t["name"].lower():
                tool = t
                name = tid
                break
    
    if not tool:
        print(f"未找到: {name}")
        return
    
    exe = get_full_exe_path(tool)
    if exe and exe.exists():
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
        print(f"opened: {tool['name']} ({exe})")
    else:
        print(f"exe不存在: {tool.get('exe', '?')} in {tool['path']}")
        if tool.get("download"):
            print(f"可下载: python {__file__} download {name}")


def cmd_path(name):
    """获取路径"""
    tool = CATALOG.get(name)
    if not tool:
        for tid, t in CATALOG.items():
            if name.lower() in tid.lower() or name.lower() in t["name"].lower():
                tool = t
                break
    if tool:
        exe = get_full_exe_path(tool)
        if exe and exe.exists():
            print(str(exe))
        else:
            print(tool["path"])
    else:
        print(f"未找到: {name}")


def cmd_download(name):
    """下载软件"""
    tool = CATALOG.get(name)
    if not tool:
        print(f"未找到: {name}")
        return
    
    dl = tool.get("download")
    if not dl:
        print(f"{tool['name']} 没有配置下载源")
        return
    
    output_dir = Path(tool["path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if dl["type"] == "github":
        repo = dl["repo"]
        asset_filter = dl.get("asset", "")
        print(f"从GitHub下载: {repo}")
        cmd = [sys.executable, "/python/MCP/github_dl.py", "release", repo]
        if asset_filter:
            cmd.extend(["--filter", asset_filter.split(".")[-1]])
        subprocess.run(cmd)
    
    elif dl["type"] == "url":
        url = dl["url"]
        filename = url.split("/")[-1]
        output = output_dir / filename
        print(f"下载: {url}")
        print(f"保存: {output}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=60, context=ctx)
            data = resp.read()
            with open(output, 'wb') as f:
                f.write(data)
            print(f"✓ 完成 ({len(data)/1024/1024:.1f}MB)")
            
            # 自动解压zip
            if filename.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(output, 'r') as z:
                    z.extractall(output_dir)
                print(f"✓ 已解压到 {output_dir}")
        except Exception as e:
            print(f"✗ 下载失败: {e}")


def cmd_install(name):
    """下载并安装"""
    cmd_download(name)
    tool = CATALOG.get(name)
    if tool:
        exe = get_full_exe_path(tool)
        if exe and exe.exists() and exe.suffix == '.exe' and 'setup' in exe.name.lower():
            print(f"运行安装程序: {exe}")
            subprocess.Popen([str(exe)])


def cmd_info(name):
    """软件详细信息"""
    tool = CATALOG.get(name)
    if not tool:
        for tid, t in CATALOG.items():
            if name.lower() in tid.lower():
                tool = t
                name = tid
                break
    if not tool:
        print(f"未找到: {name}")
        return
    
    exe = get_full_exe_path(tool)
    print(f"名称: {tool['name']}")
    print(f"ID: {name}")
    print(f"描述: {tool['desc']}")
    print(f"分类: {tool.get('category', '未分类')}")
    print(f"路径: {tool['path']}")
    print(f"EXE: {tool.get('exe', '无')}")
    print(f"状态: {'已安装 ✓' if exe and exe.exists() else '未安装 ✗'}")
    
    if exe and exe.exists():
        print(f"大小: {exe.stat().st_size/1024/1024:.1f}MB")
    
    if tool.get("config_path"):
        cp = Path(tool["config_path"])
        print(f"配置: {cp} ({'存在' if cp.exists() else '不存在'})")
    
    if tool.get("download"):
        dl = tool["download"]
        if dl["type"] == "github":
            print(f"下载: github.com/{dl['repo']}")
        else:
            print(f"下载: {dl.get('url', '?')[:60]}")


def cmd_config(name):
    """查看配置"""
    tool = CATALOG.get(name)
    if not tool:
        print(f"未找到: {name}")
        return
    
    config_path = tool.get("config_path")
    if not config_path:
        print(f"{tool['name']} 没有配置路径")
        return
    
    cp = Path(config_path)
    if not cp.exists():
        print(f"配置目录不存在: {cp}")
        return
    
    print(f"配置目录: {cp}")
    for f in sorted(cp.rglob("*.json"))[:20]:
        print(f"  {f.relative_to(cp)} ({f.stat().st_size/1024:.1f}KB)")


def cmd_backup(name):
    """备份配置"""
    tool = CATALOG.get(name)
    if not tool:
        print(f"未找到: {name}")
        return
    
    config_path = tool.get("config_path")
    if not config_path or not Path(config_path).exists():
        print(f"{tool['name']} 没有可备份的配置")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{name}_{timestamp}"
    shutil.copytree(config_path, str(backup_path))
    print(f"✓ 已备份: {backup_path}")


def cmd_restore(name):
    """恢复配置"""
    tool = CATALOG.get(name)
    if not tool:
        print(f"未找到: {name}")
        return
    
    # 找最新备份
    backups = sorted(BACKUP_DIR.glob(f"{name}_*"), reverse=True)
    if not backups:
        print(f"没有 {name} 的备份")
        return
    
    latest = backups[0]
    config_path = tool.get("config_path")
    if config_path:
        print(f"恢复: {latest} → {config_path}")
        if Path(config_path).exists():
            shutil.rmtree(config_path)
        shutil.copytree(str(latest), config_path)
        print(f"✓ 已恢复")


def cmd_tree():
    """显示%DEVTOOLS_DIR%目录树"""
    def _tree(path, prefix="", depth=0, max_depth=2):
        if depth > max_depth:
            return
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        
        dirs = [i for i in items if i.is_dir() and not i.name.startswith('_') and not i.name.startswith('.')]
        files = [i for i in items if i.is_file() and i.suffix in ['.exe', '.bat', '.msi']]
        
        for f in files:
            print(f"{prefix}  {f.name}")
        for d in dirs:
            print(f"{prefix}  {d.name}/")
            _tree(d, prefix + "    ", depth + 1, max_depth)
    
    print(f"D:\\Dev/")
    _tree(DEV)


def cmd_check():
    """检查所有软件状态"""
    installed = 0
    missing = 0
    
    print(f"{'名称':25s} {'分类':10s} {'状态':6s} {'路径'}")
    print("-" * 80)
    
    for tid, tool in sorted(CATALOG.items(), key=lambda x: x[1].get("category", "")):
        exe = get_full_exe_path(tool)
        if exe and exe.exists():
            status = "✓"
            installed += 1
        else:
            status = "✗"
            missing += 1
        print(f"{tool['name']:25s} {tool.get('category',''):10s} {status:6s} {tool['path']}")
    
    print(f"\n已安装: {installed} / 未安装: {missing} / 总计: {installed+missing}")


def main():
    if len(sys.argv) < 2:
        print("""Dev Manager - D:\\Dev 软件管理中心

用法: python dev_mgr.py <action> [args...]

  list                    列出所有软件(按分类)
  find <keyword>          搜索软件
  open <name>             打开软件
  path <name>             获取路径
  info <name>             详细信息
  config <name>           查看配置
  download <name>         下载软件
  install <name>          下载并安装
  backup <name>           备份配置
  restore <name>          恢复配置
  tree                    目录树
  check                   检查所有软件状态""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "list": cmd_list()
    elif action == "find": cmd_find(args[0] if args else "")
    elif action == "open": cmd_open(args[0] if args else "")
    elif action == "path": cmd_path(args[0] if args else "")
    elif action == "info": cmd_info(args[0] if args else "")
    elif action == "config": cmd_config(args[0] if args else "")
    elif action == "download": cmd_download(args[0] if args else "")
    elif action == "install": cmd_install(args[0] if args else "")
    elif action == "backup": cmd_backup(args[0] if args else "")
    elif action == "restore": cmd_restore(args[0] if args else "")
    elif action == "tree": cmd_tree()
    elif action == "check": cmd_check()
    else: print(f"未知: {action}")


if __name__ == '__main__':
    main()
