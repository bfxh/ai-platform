import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

try:
    from engine_converter_extended import (
        XRProjectConverter, ExtendedEngineConverter, DCCBridgeConverter,
        XR_COMPONENT_MAP, XR_PLATFORM_MAP, ENGINE_FORMAT_MAP,
        DCC_FORMAT_MAP, ANIMATION_FORMAT_MAP, PLATFORM_MAP,
        CAD_FORMAT_MAP, get_full_conversion_matrix,
    )
    HAS_EXTENDED = True
except ImportError:
    HAS_EXTENDED = False

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

from .scanner import analyze_project
from .config import Config
from .converters import (
    UEToGodotConverter,
    UnityToGodotConverter,
    UnityToUE5Converter,
    GodotToUE5Converter,
    GodotToUnityConverter,
    UEToUnityConverter,
    BlenderToEngineConverter,
    UNITY_COMPONENT_MAP,
    UNITY_SHADER_MAP,
    UNITY_TEX_PROP_MAP,
    UNITY_FLOAT_PROP_MAP,
    UNITY_COLOR_PROP_MAP,
)


def generate_conversion_report(conversion_result: Dict) -> str:
    report = conversion_result.get("report", {})
    lines = [
        "=" * 60,
        "引擎资产转换报告",
        "=" * 60,
        f"源: {conversion_result.get('source', 'N/A')}",
        f"目标: {conversion_result.get('target', 'N/A')}",
        "",
    ]

    if "stats" in conversion_result:
        lines.append("资产统计:")
        for key, val in conversion_result["stats"].items():
            lines.append(f"  {key}: {val}")
        lines.append("")

    if report.get("steps"):
        lines.append("转换步骤:")
        for step in report["steps"]:
            lines.append(f"  [{step['step']}] {step['message']}")
        lines.append("")

    if report.get("warnings"):
        lines.append(f"警告 ({len(report['warnings'])}):")
        for w in report["warnings"][:20]:
            lines.append(f"  ⚠ {w}")
        if len(report["warnings"]) > 20:
            lines.append(f"  ... 还有 {len(report['warnings']) - 20} 条警告")
        lines.append("")

    if report.get("errors"):
        lines.append(f"错误 ({len(report['errors'])}):")
        for e in report["errors"]:
            lines.append(f"  ✗ {e}")
        lines.append("")

    lines.append(f"结果: {'成功 ✓' if conversion_result.get('success') else '失败 ✗'}")
    lines.append("=" * 60)
    return "\n".join(lines)


if FastMCP:
    mcp = FastMCP("engine-converter")

    @mcp.tool()
    async def convert_ue_to_godot(
        source_path: str,
        godot_project: str,
        scene_name: str = "MainScene"
    ) -> Dict[str, Any]:
        """
        UE资产转Godot - 支持FBX/OBJ/glTF网格、贴图、场景组装

        Args:
            source_path: UE导出的资产目录或单个文件路径
            godot_project: Godot项目目标目录
            scene_name: 场景名称

        Returns:
            转换结果报告
        """
        converter = UEToGodotConverter(Path(source_path), Path(godot_project), scene_name)
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_unity_to_godot(
        unity_project: str,
        godot_project: str
    ) -> Dict[str, Any]:
        """
        Unity项目转Godot - 解析场景/预制体/材质/脚本，生成Godot 4.x项目

        Args:
            unity_project: Unity项目目录（含Assets文件夹）
            godot_project: Godot项目目标目录

        Returns:
            转换结果报告
        """
        converter = UnityToGodotConverter(Path(unity_project), Path(godot_project))
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_unity_to_ue5(
        unity_project: str,
        ue_project: str
    ) -> Dict[str, Any]:
        """
        Unity项目转UE5 - 复制资产、生成材质映射、C#→C++头文件、场景JSON

        Args:
            unity_project: Unity项目目录（含Assets文件夹）
            ue_project: UE5项目目录

        Returns:
            转换结果报告
        """
        converter = UnityToUE5Converter(Path(unity_project), Path(ue_project))
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_godot_to_ue5(
        godot_project: str,
        ue_project: str
    ) -> Dict[str, Any]:
        """
        Godot项目转UE5 - 解析.tscn/.tres/.gd，复制资产，生成UE5项目结构

        Args:
            godot_project: Godot项目目录
            ue_project: UE5项目目录

        Returns:
            转换结果报告
        """
        converter = GodotToUE5Converter(Path(godot_project), Path(ue_project))
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_godot_to_unity(
        godot_project: str,
        unity_project: str
    ) -> Dict[str, Any]:
        """
        Godot项目转Unity - 解析.tscn/.tres/.gd，复制资产，GDScript→C#

        Args:
            godot_project: Godot项目目录
            unity_project: Unity项目目录

        Returns:
            转换结果报告
        """
        converter = GodotToUnityConverter(Path(godot_project), Path(unity_project))
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_ue_to_unity(
        ue_export_path: str,
        unity_project: str
    ) -> Dict[str, Any]:
        """
        UE导出资产转Unity - FBX/贴图/音频复制到Unity项目

        Args:
            ue_export_path: UE导出的资产目录
            unity_project: Unity项目目录

        Returns:
            转换结果报告
        """
        converter = UEToUnityConverter(Path(ue_export_path), Path(unity_project))
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def convert_blender_to_engine(
        blend_path: str,
        target_project: str,
        target_engine: str = "godot"
    ) -> Dict[str, Any]:
        """
        Blender文件转到目标引擎 - 支持.blend→Godot/UE5/Unity

        Args:
            blend_path: .blend文件路径
            target_project: 目标引擎项目目录
            target_engine: 目标引擎 (godot/ue5/unity)

        Returns:
            转换结果报告
        """
        converter = BlenderToEngineConverter(Path(blend_path), Path(target_project), target_engine)
        result = await converter.convert()
        result["report_text"] = generate_conversion_report(result)
        return result

    @mcp.tool()
    async def list_conversion_paths() -> Dict[str, Any]:
        """
        列出所有支持的转换路径

        Returns:
            完整转换矩阵
        """
        if HAS_EXTENDED:
            return get_full_conversion_matrix()
        return {
            "conversion_matrix": {
                "UE": {"→ Godot": "FBX/glTF → .tscn", "→ Unity": "FBX/贴图/音频复制", "→ Blender": "FBX/glTF导入"},
                "Unity": {"→ Godot": "YAML解析 → .tscn/.tres/.gd", "→ UE5": "FBX → Content, C#→C++", "→ Blender": "FBX导入"},
                "Godot": {"→ UE5": ".tscn→JSON, .tres→JSON, .gd→C++", "→ Unity": ".tscn→JSON, .gd→C#", "→ Blender": "glTF/FBX导出"},
                "Blender": {"→ Godot": ".blend→.glb→.tscn", "→ UE5": ".blend→.fbx→Content", "→ Unity": ".blend→.fbx→Assets"},
            },
            "engine_plugins": {
                "Godot": "engine_converter_plugins/godot_importer/addons/engine_importer/",
                "UE5": "engine_converter_plugins/ue5_plugin/EngineImporter/",
                "Unity": "engine_converter_plugins/unity_editor/Editor/EngineImporter/",
                "Blender": "engine_converter_plugins/blender_addon/engine_converter.py",
            },
            "total_paths": 12,
            "note": "材质/脚本转换为基本映射，复杂逻辑需手动调整",
        }

    if HAS_EXTENDED:
        @mcp.tool()
        async def convert_xr_project(
            source_project: str,
            source_engine: str,
            target_engine: str
        ) -> Dict[str, Any]:
            """
            VR/XR项目转换 - 检测XR组件、映射跨引擎XR SDK、生成XR Rig配置

            Args:
                source_project: 源项目路径
                source_engine: 源引擎 (unity/ue5/godot)
                target_engine: 目标引擎 (unity/ue5/godot)

            Returns:
                XR转换结果（组件映射、平台兼容性、XR Rig脚本）
            """
            converter = XRProjectConverter(Path(source_project), source_engine, target_engine)
            result = await converter.convert()
            return result

        @mcp.tool()
        async def convert_extended_engine(
            source_path: str,
            target_engine: str,
            target_path: str
        ) -> Dict[str, Any]:
            """
            扩展引擎转换 - 支持CryEngine/Defold/Cocos Creator等更多引擎

            Args:
                source_path: 源项目路径
                target_engine: 目标引擎 (unity/ue5/godot/defold/cocos_creator/cryengine)
                target_path: 目标项目路径

            Returns:
                转换结果
            """
            converter = ExtendedEngineConverter(Path(source_path), target_engine, Path(target_path))
            result = await converter.convert()
            return result

        @mcp.tool()
        async def convert_dcc_asset(
            source_path: str,
            target_engine: str,
            target_path: str
        ) -> Dict[str, Any]:
            """
            DCC工具资产转换 - Maya/Houdini/Substance/SketchUp/Revit/Spine/DragonBones

            Args:
                source_path: DCC文件或项目路径
                target_engine: 目标引擎 (unity/ue5/godot/defold/cocos_creator)
                target_path: 目标项目路径

            Returns:
                转换结果（含导入步骤指南）
            """
            converter = DCCBridgeConverter(Path(source_path), target_engine, Path(target_path))
            result = await converter.convert()
            return result

        @mcp.tool()
        async def get_xr_component_mapping() -> Dict[str, Any]:
            """
            获取VR/XR组件跨引擎映射表 - 13种XR组件 x 5个引擎

            Returns:
                XR组件映射表
            """
            return {
                "components": XR_COMPONENT_MAP,
                "platforms": XR_PLATFORM_MAP,
                "total_components": len(XR_COMPONENT_MAP),
                "total_platforms": len(XR_PLATFORM_MAP),
                "note": "PSVR2需要NDA, VisionPro仅Unity支持, WebXR仅Godot原生支持",
            }

        @mcp.tool()
        async def get_engine_format_info(engine_name: str = "all") -> Dict[str, Any]:
            """
            获取引擎文件格式信息 - 支持的导入/导出格式

            Args:
                engine_name: 引擎名称 (all/cryengine/defold/cocos_creator/construct/rpg_maker)

            Returns:
                引擎格式信息
            """
            if engine_name == "all":
                return ENGINE_FORMAT_MAP
            return ENGINE_FORMAT_MAP.get(engine_name, {"error": f"Unknown engine: {engine_name}"})

        @mcp.tool()
        async def get_dcc_bridge_info(dcc_name: str = "all") -> Dict[str, Any]:
            """
            获取DCC工具桥梁信息 - Maya/Houdini/Substance导出策略

            Args:
                dcc_name: DCC工具名 (all/maya/houdini/substance)

            Returns:
                DCC桥梁策略
            """
            if dcc_name == "all":
                return DCC_FORMAT_MAP
            return DCC_FORMAT_MAP.get(dcc_name, {"error": f"Unknown DCC: {dcc_name}"})

        @mcp.tool()
        async def get_animation_format_info() -> Dict[str, Any]:
            """
            获取2D动画格式信息 - Spine/DragonBones/Lottie引擎支持

            Returns:
                动画格式兼容性表
            """
            return ANIMATION_FORMAT_MAP

        @mcp.tool()
        async def get_platform_info(platform_name: str = "all") -> Dict[str, Any]:
            """
            获取目标平台信息 - Android/iOS/WebGL/WebXR

            Args:
                platform_name: 平台名 (all/android/ios/webgl/webxr)

            Returns:
                平台信息和引擎支持
            """
            if platform_name == "all":
                return PLATFORM_MAP
            return PLATFORM_MAP.get(platform_name, {"error": f"Unknown platform: {platform_name}"})

        @mcp.tool()
        async def get_cad_bridge_info() -> Dict[str, Any]:
            """
            获取CAD/BIM桥梁信息 - SketchUp/Revit/AutoCAD到引擎的转换

            Returns:
                CAD/BIM桥梁策略
            """
            return CAD_FORMAT_MAP

    @mcp.tool()
    async def analyze_engine_project(project_path: str) -> Dict[str, Any]:
        """
        分析游戏引擎项目 - 自动检测引擎类型、统计资产、推荐转换路径

        Args:
            project_path: 项目目录路径

        Returns:
            项目分析结果
        """
        return analyze_project(Path(project_path))

    @mcp.tool()
    async def get_component_mapping(
        source_engine: str,
        target_engine: str
    ) -> Dict[str, Any]:
        """
        获取引擎组件映射表 - 查看Unity/UE/Godot之间的组件对应关系

        Args:
            source_engine: 源引擎 (unity/ue)
            target_engine: 目标引擎 (godot/ue5)

        Returns:
            组件映射表
        """
        mapping = {}
        for unity_comp, targets in UNITY_COMPONENT_MAP.items():
            if source_engine == "unity":
                if target_engine == "godot":
                    mapping[unity_comp] = targets.get("godot", "Node3D")
                elif target_engine == "ue5":
                    mapping[unity_comp] = targets.get("ue", "UObject")
            elif source_engine == "ue":
                if target_engine == "godot":
                    for gd_comp, ue_comp in {
                        "StaticMeshComponent": "MeshInstance3D",
                        "SkeletalMeshComponent": "MeshInstance3D",
                        "CameraComponent": "Camera3D",
                        "DirectionalLightComponent": "DirectionalLight3D",
                        "PointLightComponent": "OmniLight3D",
                        "SpotLightComponent": "SpotLight3D",
                        "BoxCollision": "CollisionShape3D",
                        "SphereCollision": "CollisionShape3D",
                        "CapsuleCollision": "CollisionShape3D",
                        "AudioComponent": "AudioStreamPlayer3D",
                        "NiagaraComponent": "GPUParticles3D",
                        "Landscape": "Terrain3D",
                    }.items():
                        mapping[gd_comp] = ue_comp
        return {
            "source_engine": source_engine,
            "target_engine": target_engine,
            "mapping": mapping,
            "total": len(mapping),
            "note": "复杂组件（如蓝图、动画状态机）需要手动重建",
        }

    @mcp.tool()
    async def get_shader_mapping() -> Dict[str, Any]:
        """
        获取Unity→Godot着色器映射表

        Returns:
            着色器映射表和纹理属性映射
        """
        return {
            "shader_map": UNITY_SHADER_MAP,
            "texture_property_map": UNITY_TEX_PROP_MAP,
            "float_property_map": UNITY_FLOAT_PROP_MAP,
            "color_property_map": UNITY_COLOR_PROP_MAP,
            "note": "自定义Shader需要手动在Godot中用Shader语言重写",
        }


def cli_main():
    parser = argparse.ArgumentParser(
        description="引擎资产转换器 - 全矩阵版 (4引擎 x 4引擎)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
转换路径 (12条):
  ue_to_godot       UE → Godot (FBX/glTF → Godot .tscn)
  ue_to_unity       UE → Unity (FBX/贴图/音频复制)
  unity_to_godot    Unity → Godot (YAML → .tscn/.tres/.gd)
  unity_to_ue5      Unity → UE5 (FBX → Content, C# → C++头文件)
  godot_to_ue5      Godot → UE5 (.tscn→JSON, .gd→C++)
  godot_to_unity    Godot → Unity (.tscn→JSON, .gd→C#)
  blender_to_godot  Blender → Godot (.blend → .glb → .tscn)
  blender_to_ue5    Blender → UE5 (.blend → .fbx)
  blender_to_unity  Blender → Unity (.blend → .fbx)

示例:
  python engine_converter.py analyze D:/MyUnityProject
  python engine_converter.py ue_to_godot D:/UE_Export D:/GodotProject MainScene
  python engine_converter.py unity_to_godot D:/MyUnityProject D:/GodotProject
  python engine_converter.py unity_to_ue5 D:/MyUnityProject D:/UE5Project
  python engine_converter.py godot_to_ue5 D:/GodotProject D:/UE5Project
  python engine_converter.py godot_to_unity D:/GodotProject D:/UnityProject
  python engine_converter.py blender_to_godot D:/model.blend D:/GodotProject
  python engine_converter.py mcp
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    p_analyze = subparsers.add_parser("analyze", help="分析项目")
    p_analyze.add_argument("project_path", help="项目路径")

    p_ue2godot = subparsers.add_parser("ue_to_godot", help="UE → Godot")
    p_ue2godot.add_argument("source_path", help="UE导出资产路径")
    p_ue2godot.add_argument("godot_project", help="Godot项目目录")
    p_ue2godot.add_argument("scene_name", nargs="?", default="MainScene", help="场景名")

    p_ue2unity = subparsers.add_parser("ue_to_unity", help="UE → Unity")
    p_ue2unity.add_argument("ue_export_path", help="UE导出资产路径")
    p_ue2unity.add_argument("unity_project", help="Unity项目目录")

    p_unity2godot = subparsers.add_parser("unity_to_godot", help="Unity → Godot")
    p_unity2godot.add_argument("unity_project", help="Unity项目目录")
    p_unity2godot.add_argument("godot_project", help="Godot项目目录")

    p_unity2ue5 = subparsers.add_parser("unity_to_ue5", help="Unity → UE5")
    p_unity2ue5.add_argument("unity_project", help="Unity项目目录")
    p_unity2ue5.add_argument("ue_project", help="UE5项目目录")

    p_godot2ue5 = subparsers.add_parser("godot_to_ue5", help="Godot → UE5")
    p_godot2ue5.add_argument("godot_project", help="Godot项目目录")
    p_godot2ue5.add_argument("ue_project", help="UE5项目目录")

    p_godot2unity = subparsers.add_parser("godot_to_unity", help="Godot → Unity")
    p_godot2unity.add_argument("godot_project", help="Godot项目目录")
    p_godot2unity.add_argument("unity_project", help="Unity项目目录")

    p_blend2godot = subparsers.add_parser("blender_to_godot", help="Blender → Godot")
    p_blend2godot.add_argument("blend_path", help=".blend文件路径")
    p_blend2godot.add_argument("godot_project", help="Godot项目目录")

    p_blend2ue5 = subparsers.add_parser("blender_to_ue5", help="Blender → UE5")
    p_blend2ue5.add_argument("blend_path", help=".blend文件路径")
    p_blend2ue5.add_argument("ue_project", help="UE5项目目录")

    p_blend2unity = subparsers.add_parser("blender_to_unity", help="Blender → Unity")
    p_blend2unity.add_argument("blend_path", help=".blend文件路径")
    p_blend2unity.add_argument("unity_project", help="Unity项目目录")

    subparsers.add_parser("mcp", help="启动MCP服务")
    subparsers.add_parser("mapping", help="显示组件映射表")
    subparsers.add_parser("paths", help="显示所有转换路径")

    if HAS_EXTENDED:
        p_xr = subparsers.add_parser("xr_convert", help="VR/XR项目转换")
        p_xr.add_argument("source_project", help="源项目路径")
        p_xr.add_argument("source_engine", choices=["unity", "ue5", "godot"], help="源引擎")
        p_xr.add_argument("target_engine", choices=["unity", "ue5", "godot"], help="目标引擎")

        p_ext = subparsers.add_parser("engine_convert", help="扩展引擎转换(CryEngine/Defold/Cocos等)")
        p_ext.add_argument("source_path", help="源项目路径")
        p_ext.add_argument("target_engine", choices=["unity", "ue5", "godot", "defold", "cocos_creator", "cryengine"], help="目标引擎")
        p_ext.add_argument("target_path", help="目标项目路径")

        p_dcc = subparsers.add_parser("dcc_convert", help="DCC工具资产转换(Maya/Houdini/Substance等)")
        p_dcc.add_argument("source_path", help="DCC文件/项目路径")
        p_dcc.add_argument("target_engine", choices=["unity", "ue5", "godot", "defold", "cocos_creator"], help="目标引擎")
        p_dcc.add_argument("target_path", help="目标项目路径")

        subparsers.add_parser("xr_mapping", help="显示XR组件映射表")
        subparsers.add_parser("engine_formats", help="显示引擎格式信息")
        subparsers.add_parser("dcc_info", help="显示DCC桥梁信息")
        subparsers.add_parser("animation_info", help="显示2D动画格式信息")
        subparsers.add_parser("platform_info", help="显示目标平台信息")
        subparsers.add_parser("cad_info", help="显示CAD/BIM桥梁信息")

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_project(Path(args.project_path))
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "ue_to_godot":
        converter = UEToGodotConverter(Path(args.source_path), Path(args.godot_project), args.scene_name)
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "ue_to_unity":
        converter = UEToUnityConverter(Path(args.ue_export_path), Path(args.unity_project))
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "unity_to_godot":
        converter = UnityToGodotConverter(Path(args.unity_project), Path(args.godot_project))
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "unity_to_ue5":
        converter = UnityToUE5Converter(Path(args.unity_project), Path(args.ue_project))
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "godot_to_ue5":
        converter = GodotToUE5Converter(Path(args.godot_project), Path(args.ue_project))
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "godot_to_unity":
        converter = GodotToUnityConverter(Path(args.godot_project), Path(args.unity_project))
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "blender_to_godot":
        converter = BlenderToEngineConverter(Path(args.blend_path), Path(args.godot_project), "godot")
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "blender_to_ue5":
        converter = BlenderToEngineConverter(Path(args.blend_path), Path(args.ue_project), "ue5")
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "blender_to_unity":
        converter = BlenderToEngineConverter(Path(args.blend_path), Path(args.unity_project), "unity")
        result = asyncio.run(converter.convert())
        print(generate_conversion_report(result))

    elif args.command == "mcp":
        if FastMCP:
            mcp.run()
        else:
            print("错误: FastMCP 未安装。请运行: pip install fastmcp")

    elif args.command == "mapping":
        print("Unity → Godot 组件映射:")
        for unity_comp, targets in UNITY_COMPONENT_MAP.items():
            print(f"  {unity_comp:30s} → {targets['godot']}")
        print()
        print("Unity → UE5 组件映射:")
        for unity_comp, targets in UNITY_COMPONENT_MAP.items():
            print(f"  {unity_comp:30s} → {targets['ue']}")

    elif args.command == "paths":
        print("引擎资产转换 - 完整转换矩阵 (12条路径)")
        print("=" * 60)
        print()
        print("UE 出发:")
        print("  UE → Godot   FBX/glTF → Godot .tscn 场景组装")
        print("  UE → Unity   FBX/贴图/音频复制到 Assets/")
        print("  UE → Blender FBX/glTF 导入 Blender")
        print()
        print("Unity 出发:")
        print("  Unity → Godot  YAML解析 → .tscn/.tres/.gd 生成")
        print("  Unity → UE5    FBX → Content, C#→C++头文件")
        print("  Unity → Blender FBX导入 Blender")
        print()
        print("Godot 出发:")
        print("  Godot → UE5    .tscn→JSON, .tres→JSON, .gd→C++")
        print("  Godot → Unity  .tscn→JSON, .gd→C#")
        print("  Godot → Blender glTF/FBX导出")
        print()
        print("Blender 出发:")
        print("  Blender → Godot  .blend → .glb → .tscn 场景组装")
        print("  Blender → UE5    .blend → .fbx → Content/")
        print("  Blender → Unity  .blend → .fbx → Assets/")
        print()
        print("引擎原生插件:")
        print("  Godot:  engine_converter_plugins/godot_importer/addons/engine_importer/")
        print("  UE5:    engine_converter_plugins/ue5_plugin/EngineImporter/")
        print("  Unity:  engine_converter_plugins/unity_editor/Editor/EngineImporter/")
        print("  Blender: engine_converter_plugins/blender_addon/engine_converter.py")

    elif HAS_EXTENDED and args.command == "xr_convert":
        converter = XRProjectConverter(Path(args.source_project), args.source_engine, args.target_engine)
        result = asyncio.run(converter.convert())
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif HAS_EXTENDED and args.command == "engine_convert":
        converter = ExtendedEngineConverter(Path(args.source_path), args.target_engine, Path(args.target_path))
        result = asyncio.run(converter.convert())
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif HAS_EXTENDED and args.command == "dcc_convert":
        converter = DCCBridgeConverter(Path(args.source_path), args.target_engine, Path(args.target_path))
        result = asyncio.run(converter.convert())
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif HAS_EXTENDED and args.command == "xr_mapping":
        print("VR/XR 组件跨引擎映射:")
        print("=" * 80)
        for comp, engines in XR_COMPONENT_MAP.items():
            print(f"\n  {comp}:")
            for eng, impl in engines.items():
                print(f"    {eng:20s} → {impl}")
        print(f"\n\nXR 平台支持:")
        print("=" * 80)
        for pid, pinfo in XR_PLATFORM_MAP.items():
            print(f"\n  {pinfo['name']} (状态: {pinfo['status']}):")
            for eng, impl in pinfo.items():
                if eng not in ("name", "status", "devices"):
                    print(f"    {eng:20s} → {impl}")

    elif HAS_EXTENDED and args.command == "engine_formats":
        print("引擎文件格式信息:")
        print("=" * 80)
        for eng, info in ENGINE_FORMAT_MAP.items():
            print(f"\n  {info['name']}:")
            print(f"    原生格式: {info['formats']}")
            print(f"    可导入: {info['import_formats']}")
            print(f"    桥梁格式: {info['bridge_format']}")
            print(f"    脚本语言: {info['script_language']}")

    elif HAS_EXTENDED and args.command == "dcc_info":
        print("DCC工具桥梁信息:")
        print("=" * 80)
        for dcc, info in DCC_FORMAT_MAP.items():
            print(f"\n  {info['name']}:")
            print(f"    导出格式: {list(info['export_formats'].keys()) if isinstance(info['export_formats'], dict) else info['export_formats']}")
            print(f"    桥梁策略: {info['bridge_strategy']}")

    elif HAS_EXTENDED and args.command == "animation_info":
        print("2D动画格式兼容性:")
        print("=" * 80)
        for anim, info in ANIMATION_FORMAT_MAP.items():
            print(f"\n  {info['name']}:")
            print(f"    运行时格式: {info.get('runtime_json', info.get('format', 'N/A'))}")
            print(f"    引擎支持:")
            for eng, support in info["engine_support"].items():
                print(f"      {eng:15s} → {support}")

    elif HAS_EXTENDED and args.command == "platform_info":
        print("目标平台信息:")
        print("=" * 80)
        for pid, pinfo in PLATFORM_MAP.items():
            print(f"\n  {pinfo['name']}:")
            print(f"    纹理格式: {pinfo.get('texture_format', 'N/A')}")
            print(f"    音频格式: {pinfo.get('audio_format', 'N/A')}")
            print(f"    XR支持: {pinfo.get('xr_support', [])}")
            print(f"    引擎支持:")
            for eng, support in pinfo["engine_support"].items():
                print(f"      {eng:15s} → {support}")

    elif HAS_EXTENDED and args.command == "cad_info":
        print("CAD/BIM桥梁信息:")
        print("=" * 80)
        for cad, info in CAD_FORMAT_MAP.items():
            print(f"\n  {info['name']}:")
            print(f"    格式: {info['format']}")
            print(f"    导出格式: {info['export_formats']}")
            print(f"    桥梁策略: {info['bridge_strategy']}")
            print(f"    引擎导入:")
            for eng, method in info["engine_import"].items():
                print(f"      {eng:15s} → {method}")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli_main()
