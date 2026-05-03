#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    Config, analyze_project, BlenderBridge,
    UEToGodotConverter, UnityToGodotConverter, UnityToUE5Converter,
    GodotToUE5Converter, GodotToUnityConverter, UEToUnityConverter,
    BlenderToEngineConverter, UNITY_COMPONENT_MAP,
    generate_conversion_report,
)

try:
    from engine_converter_extended import (
        XRProjectConverter, ExtendedEngineConverter, DCCBridgeConverter,
        get_full_conversion_matrix, XR_COMPONENT_MAP, XR_PLATFORM_MAP,
        ENGINE_FORMAT_MAP, DCC_FORMAT_MAP, ANIMATION_FORMAT_MAP,
        PLATFORM_MAP, CAD_FORMAT_MAP,
    )
    HAS_EXTENDED = True
except ImportError:
    HAS_EXTENDED = False

BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
RESET = "\033[0m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def title(text):
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")

def subtitle(text):
    print(f"\n{BOLD}{YELLOW}--- {text} ---{RESET}\n")

def info(text):
    print(f"  {CYAN}i{RESET} {text}")

def success(text):
    print(f"  {GREEN}OK{RESET} {text}")

def warn(text):
    print(f"  {YELLOW}!{RESET} {text}")

def error(text):
    print(f"  {RED}X{RESET} {text}")

def input_path(prompt, create=False):
    val = input(f"  {GREEN}>{RESET} {prompt}: ").strip().strip('"').strip("'")
    if not val:
        return None
    p = Path(val)
    if create and not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
            success(f"已创建目录: {val}")
        except Exception as e:
            error(f"无法创建目录: {e}")
            return None
    elif not p.exists():
        error(f"路径不存在: {val}")
        return None
    return p

def input_str(prompt, default=""):
    val = input(f"  {GREEN}>{RESET} {prompt} [{default}]: ").strip()
    return val if val else default

def pause():
    input(f"\n  {DIM}按回车继续...{RESET}")

def show_main_menu():
    config = Config.load()
    clear()
    title("引擎资产转换器 v2.1 - 交互式菜单")
    print(f"  {BOLD}1.{RESET} 分析项目 (自动检测引擎类型)")
    print(f"  {BOLD}2.{RESET} 转换资产 (选择转换路径)")
    print(f"  {BOLD}3.{RESET} 查看转换矩阵 (1610条路径)")
    print(f"  {BOLD}4.{RESET} 查看组件映射表")
    print(f"  {BOLD}5.{RESET} 查看XR/VR平台支持")
    print(f"  {BOLD}6.{RESET} 查看DCC工具桥梁")
    print(f"  {BOLD}7.{RESET} 查看CAD/BIM桥梁")
    print(f"  {BOLD}8.{RESET} 查看中间格式说明")
    print(f"  {BOLD}9.{RESET} 查看目标平台支持")
    print(f"  {BOLD}m.{RESET} 切换材质方案 (当前: {CYAN}{config.material_preset}{RESET})")
    print(f"  {BOLD}0.{RESET} 退出")
    print()

def show_convert_menu():
    clear()
    title("选择转换路径")
    print(f"  {BOLD}UE/虚幻引擎 →:{RESET}")
    print(f"    1. UE → Godot")
    print(f"    2. UE → Unity")
    print()
    print(f"  {BOLD}Unity →:{RESET}")
    print(f"    3. Unity → Godot")
    print(f"    4. Unity → UE5")
    print()
    print(f"  {BOLD}Godot →:{RESET}")
    print(f"    5. Godot → UE5")
    print(f"    6. Godot → Unity")
    print()
    print(f"  {BOLD}Blender →:{RESET}")
    print(f"    7. Blender → Godot")
    print(f"    8. Blender → UE5")
    print(f"    9. Blender → Unity")
    print()
    if HAS_EXTENDED:
        print(f"  {BOLD}扩展转换:{RESET}")
        print(f"    a. XR/VR项目转换")
        print(f"    b. 扩展引擎转换 (CryEngine/Defold/Cocos等)")
        print(f"    c. DCC资产转换 (Maya/Houdini/Substance等)")
    print(f"    0. 返回主菜单")
    print()

def do_analyze():
    clear()
    title("项目分析")
    p = input_path("输入项目路径")
    if not p:
        return
    result = analyze_project(p)
    print()
    success(f"引擎类型: {BOLD}{result['engine']}{RESET}")
    if result.get("assets"):
        subtitle("资产统计")
        for k, v in result["assets"].items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    info(f"{kk}: {vv}")
            else:
                info(f"{k}: {v}")
    if result.get("convertible"):
        subtitle("可转换到")
        for eng in result["convertible"]:
            info(f"→ {eng}")
    pause()

def do_convert(choice):
    clear()
    try:
        if choice == "1":
            title("UE → Godot 转换")
            src = input_path("UE导出资产路径")
            if not src:
                return
            dst = input_path("Godot项目目标目录 (不存在会自动创建)", create=True)
            if not dst:
                return
            name = input_str("场景名称", "MainScene")
            converter = UEToGodotConverter(src, dst, name)
            result = asyncio.run(converter.convert())
        elif choice == "2":
            title("UE → Unity 转换")
            src = input_path("UE导出资产路径")
            if not src:
                return
            dst = input_path("Unity项目目录")
            if not dst:
                return
            converter = UEToUnityConverter(src, dst)
            result = asyncio.run(converter.convert())
        elif choice == "3":
            title("Unity → Godot 转换")
            src = input_path("Unity项目目录 (含Assets文件夹)")
            if not src:
                return
            dst = input_path("Godot项目目标目录", create=True)
            if not dst:
                return
            converter = UnityToGodotConverter(src, dst)
            result = asyncio.run(converter.convert())
        elif choice == "4":
            title("Unity → UE5 转换")
            src = input_path("Unity项目目录 (含Assets文件夹)")
            if not src:
                return
            dst = input_path("UE5项目目录")
            if not dst:
                return
            converter = UnityToUE5Converter(src, dst)
            result = asyncio.run(converter.convert())
        elif choice == "5":
            title("Godot → UE5 转换")
            src = input_path("Godot项目目录")
            if not src:
                return
            dst = input_path("UE5项目目录")
            if not dst:
                return
            converter = GodotToUE5Converter(src, dst)
            result = asyncio.run(converter.convert())
        elif choice == "6":
            title("Godot → Unity 转换")
            src = input_path("Godot项目目录")
            if not src:
                return
            dst = input_path("Unity项目目录")
            if not dst:
                return
            converter = GodotToUnityConverter(src, dst)
            result = asyncio.run(converter.convert())
        elif choice == "7":
            title("Blender → Godot 转换")
            src = input_path(".blend文件路径")
            if not src:
                return
            dst = input_path("Godot项目目录")
            if not dst:
                return
            converter = BlenderToEngineConverter(src, dst, "godot")
            result = asyncio.run(converter.convert())
        elif choice == "8":
            title("Blender → UE5 转换")
            src = input_path(".blend文件路径")
            if not src:
                return
            dst = input_path("UE5项目目录")
            if not dst:
                return
            converter = BlenderToEngineConverter(src, dst, "ue5")
            result = asyncio.run(converter.convert())
        elif choice == "9":
            title("Blender → Unity 转换")
            src = input_path(".blend文件路径")
            if not src:
                return
            dst = input_path("Unity项目目录")
            if not dst:
                return
            converter = BlenderToEngineConverter(src, dst, "unity")
            result = asyncio.run(converter.convert())
        elif choice == "a" and HAS_EXTENDED:
            title("XR/VR项目转换")
            src = input_path("源项目路径")
            if not src:
                return
            src_eng = input_str("源引擎 (unity/ue5/godot)", "unity")
            dst_eng = input_str("目标引擎 (unity/ue5/godot)", "godot")
            converter = XRProjectConverter(src, src_eng, dst_eng)
            result = asyncio.run(converter.convert())
        elif choice == "b" and HAS_EXTENDED:
            title("扩展引擎转换")
            src = input_path("源项目路径")
            if not src:
                return
            dst_eng = input_str("目标引擎 (unity/ue5/godot/defold/cocos_creator/cryengine)", "godot")
            dst = input_path("目标项目路径", create=True)
            if not dst:
                return
            converter = ExtendedEngineConverter(src, dst_eng, dst)
            result = asyncio.run(converter.convert())
        elif choice == "c" and HAS_EXTENDED:
            title("DCC资产转换")
            src = input_path("DCC文件/项目路径")
            if not src:
                return
            dst_eng = input_str("目标引擎 (unity/ue5/godot/defold/cocos_creator)", "unity")
            dst = input_path("目标项目路径", create=True)
            if not dst:
                return
            converter = DCCBridgeConverter(src, dst_eng, dst)
            result = asyncio.run(converter.convert())
        else:
            return

        print()
        print(generate_conversion_report(result))
        pause()

    except Exception as e:
        error(f"转换失败: {e}")
        import traceback
        traceback.print_exc()
        pause()

def do_show_matrix():
    clear()
    title("转换矩阵 (1610条路径)")
    if not HAS_EXTENDED:
        warn("扩展模块未加载，显示基础矩阵")
        pause()
        return

    matrix = get_full_conversion_matrix()
    skip_keys = [k for k in matrix if k.startswith("total_")]

    for cat_name, cat_data in matrix.items():
        if cat_name in skip_keys or not isinstance(cat_data, dict):
            continue
        subtitle(cat_name.replace("_", " ").upper())
        count = 0
        for src, info in cat_data.items():
            if isinstance(info, dict) and "targets" in info:
                targets = info["targets"]
                bridge = info.get("bridge", "?")
                if count < 5:
                    print(f"    {src:25s} → {', '.join(targets[:8])}")
                    if len(targets) > 8:
                        print(f"    {'':25s}   ... +{len(targets)-8} more")
                    print(f"    {'':25s}   桥梁格式: {bridge}")
                count += 1
            elif isinstance(info, dict) and "engines" in info:
                engines = info["engines"]
                if count < 3:
                    print(f"    {src:25s} → {', '.join(engines[:6])}")
                    if len(engines) > 6:
                        print(f"    {'':25s}   ... +{len(engines)-6} more")
                count += 1
            elif isinstance(info, dict) and "type" in info:
                if count < 3:
                    print(f"    {src:15s} 类型={info.get('type','?')} 内容={info.get('content','?')}")
                count += 1
        if count > 5:
            print(f"    {DIM}... 共 {count} 条{RESET}")

    subtitle("总计")
    for k in sorted(matrix.keys()):
        if k.startswith("total_"):
            label = k.replace("total_", "").replace("_", " ")
            print(f"    {label:30s} {matrix[k]}")

    pause()

def do_show_mapping():
    clear()
    title("组件映射表")
    subtitle("Unity → Godot")
    for unity_comp, targets in UNITY_COMPONENT_MAP.items():
        print(f"    {unity_comp:30s} → {targets['godot']}")
    subtitle("Unity → UE5")
    for unity_comp, targets in UNITY_COMPONENT_MAP.items():
        print(f"    {unity_comp:30s} → {targets['ue']}")
    pause()

def do_show_xr():
    clear()
    title("XR/VR平台支持")
    if not HAS_EXTENDED:
        warn("扩展模块未加载")
        pause()
        return
    for pid, pinfo in XR_PLATFORM_MAP.items():
        status = pinfo.get("status", "?")
        s_icon = GREEN + "OK" if status == "active" else YELLOW + "!!" if status == "limited" else RED + "XX"
        print(f"  {s_icon}{RESET} {pinfo.get('name', pid)} ({status})")
        for eng in ["unity", "ue5", "godot", "web"]:
            impl = pinfo.get(eng)
            if impl:
                print(f"      {eng:10s} → {impl}")
    pause()

def do_show_dcc():
    clear()
    title("DCC工具桥梁")
    if not HAS_EXTENDED:
        warn("扩展模块未加载")
        pause()
        return
    for dcc, info in DCC_FORMAT_MAP.items():
        print(f"  {BOLD}{info.get('name', dcc)}{RESET}")
        print(f"      导出格式: {info.get('export_formats', '?')}")
        print(f"      桥梁策略: {info.get('bridge_strategy', '?')}")
        eng_import = info.get("engine_import", {})
        if eng_import:
            for eng, method in eng_import.items():
                print(f"      → {eng}: {method}")
        print()
    pause()

def do_show_cad():
    clear()
    title("CAD/BIM桥梁")
    if not HAS_EXTENDED:
        warn("扩展模块未加载")
        pause()
        return
    for cad, info in CAD_FORMAT_MAP.items():
        print(f"  {BOLD}{info.get('name', cad)}{RESET}")
        print(f"      格式: {info.get('format', '?')}")
        print(f"      导出格式: {info.get('export_formats', '?')}")
        print(f"      桥梁策略: {info.get('bridge_strategy', '?')}")
        eng_import = info.get("engine_import", {})
        if eng_import:
            for eng, method in eng_import.items():
                print(f"      → {eng}: {method}")
        print()
    pause()

def do_show_formats():
    clear()
    title("中间格式说明")
    if not HAS_EXTENDED:
        warn("扩展模块未加载")
        pause()
        return
    matrix = get_full_conversion_matrix()
    fmt_data = matrix.get("interchange_formats", {})
    for fmt_name, fmt_info in fmt_data.items():
        if not isinstance(fmt_info, dict):
            continue
        ftype = fmt_info.get("type", "?")
        owner = fmt_info.get("owner", "?")
        content = fmt_info.get("content", "?")
        engines = fmt_info.get("engines", "?")
        type_color = GREEN if "open" in ftype.lower() else YELLOW
        print(f"  {BOLD}.{fmt_name}{RESET}  {type_color}[{ftype}]{RESET}  {DIM}by {owner}{RESET}")
        print(f"      适用: {engines}")
        print(f"      内容: {content}")
        print()
    pause()

def do_show_platforms():
    clear()
    title("目标平台支持")
    if not HAS_EXTENDED:
        warn("扩展模块未加载")
        pause()
        return
    matrix = get_full_conversion_matrix()
    platforms = matrix.get("target_platforms", {})
    for pname, pinfo in platforms.items():
        engines = pinfo.get("engines", [])
        print(f"  {BOLD}{pname}{RESET}")
        print(f"      支持引擎: {', '.join(engines)}")
        print()
    pause()

def do_switch_preset():
    clear()
    title("切换材质方案")
    config = Config.load()
    template_dir = Path(__file__).parent / "bake_templates"
    presets = sorted([f.stem for f in template_dir.glob("*.py")])

    if not presets:
        warn("未找到烘焙模板")
        pause()
        return

    print(f"  当前方案: {CYAN}{config.material_preset}{RESET}")
    print()
    print(f"  可用方案:")
    for i, preset in enumerate(presets, 1):
        marker = f" {GREEN}← 当前{RESET}" if preset == config.material_preset else ""
        print(f"    {BOLD}{i}.{RESET} {preset}{marker}")
    print()

    choice = input(f"  {GREEN}>{RESET} 选择方案编号 (0=取消): ").strip()
    if not choice or choice == "0":
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(presets):
            new_preset = presets[idx]
            config_path = Path(__file__).parent / "config.yaml"
            if config_path.exists():
                try:
                    import yaml
                    with open(config_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    data["material_preset"] = new_preset
                    with open(config_path, "w", encoding="utf-8") as f:
                        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                    success(f"已切换材质方案: {config.material_preset} → {new_preset}")
                except ImportError:
                    warn("pyyaml 未安装，无法写入配置文件")
            else:
                warn(f"配置文件不存在: {config_path}")
        else:
            warn("无效选择")
    except ValueError:
        warn("请输入数字")

    pause()

def main():
    while True:
        show_main_menu()
        choice = input(f"  {GREEN}>{RESET} 选择: ").strip().lower()
        if choice == "1":
            do_analyze()
        elif choice == "2":
            while True:
                show_convert_menu()
                c = input(f"  {GREEN}>{RESET} 选择转换路径: ").strip().lower()
                if c == "0":
                    break
                do_convert(c)
        elif choice == "3":
            do_show_matrix()
        elif choice == "4":
            do_show_mapping()
        elif choice == "5":
            do_show_xr()
        elif choice == "6":
            do_show_dcc()
        elif choice == "7":
            do_show_cad()
        elif choice == "8":
            do_show_formats()
        elif choice == "9":
            do_show_platforms()
        elif choice == "m":
            do_switch_preset()
        elif choice == "0":
            print(f"\n  {DIM}再见!{RESET}\n")
            break

if __name__ == "__main__":
    main()
