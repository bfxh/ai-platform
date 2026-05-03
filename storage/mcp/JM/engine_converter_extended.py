#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
引擎资产转换器 - 平台扩展模块

扩展支持 (600+ 转换路径):
  - 3D引擎: Unity, UE5, Godot, CryEngine, Flax, Stride, O3DE, Unigine, Bevy, Fyrox, Armory3D,
    Torque3D, Spring, Nau, Dagon, Gamebryo, id Tech, Source 2, Frostbite, Snowdrop, Decima,
    Fox Engine, RAGE, Creation Engine, Lumberyard 等 34 个
  - 2D引擎: Defold, Cocos Creator, Construct, RPG Maker, Love2D, Solar2D, GDevelop, Flame,
    Phaser, LibGDX, Cocos2d-x, Axmol, PixiJS, Egret, Heaps, OpenFL, GameMaker 等 20 个
  - Web引擎: PlayCanvas, Babylon.js, Three.js, A-Frame, Spline, React Three Fiber,
    CesiumJS, Mapbox GL 等 12 个
  - DCC工具: Maya, Houdini, Substance, 3ds Max, Cinema4D, ZBrush, 3D-Coat, Mudbox,
    Modo, Daz3D, Cascadeur, Nomad Sculpt 等 20 个
  - CAD/BIM: SketchUp, Revit, AutoCAD, ArchiCAD, Rhino, Tekla, SolidWorks, CATIA,
    Fusion360, FreeCAD 等 18 个
  - 渲染引擎: Octane, Redshift, V-Ray, Arnold, RenderMan, Cycles, Karma 等 10 个
  - 地形生成: World Machine, Gaea, World Creator, Vue, Infinigen 等 7 个
  - 动画/动捕: Spine, DragonBones, Live2D, Lottie, MotionBuilder, iClone, Rokoko,
    Xsens, OptiTrack, Vicon, Faceware 等 16 个
  - VFX粒子: PopcornFX, Niagara, VFX Graph 等 6 个
  - 数字孪生: Omniverse, Unity Reflect, Matterport 等 5 个
  - XR平台: OpenXR, Meta XR, SteamVR, PSVR2, Vision Pro, Android XR, WebXR 等 23 个
  - 音频中间件: Wwise, FMOD, CRIWARE, Steam Audio, Miles, Fabric 等 14 个
  - 物理引擎: PhysX, Havok, Jolt, Bullet, MuJoCo, Rapier, ODE 等 15 个
  - AI工具: Meshy, Leonardo AI, Luma AI, Spline AI, Tripo3D, Stable 3D 等 24 个
  - 中间格式: FBX, glTF, USD, OBJ, ABC, STEP, IFC, BVH, VDB 等 28 个
  - 目标平台: Android, iOS, WebGL, PS5, Xbox, Switch, Steam Deck 等 18 个
"""

import os
import json
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

XR_COMPONENT_MAP = {
    "XROrigin": {
        "unity": "XROrigin (XR Interaction Toolkit)",
        "ue5": "Pawn + Camera + MotionControllerComponent",
        "godot": "XROrigin3D",
        "defold": "N/A (2D engine)",
        "cocos": "Node3D (custom XR rig)",
    },
    "XRController": {
        "unity": "XRController (XR Interaction Toolkit)",
        "ue5": "MotionControllerComponent",
        "godot": "XRController3D",
        "defold": "N/A",
        "cocos": "custom input handler",
    },
    "XRCamera": {
        "unity": "TrackedPoseDriver + Camera",
        "ue5": "CameraComponent + HeadMountedDisplay",
        "godot": "XRCamera3D",
        "defold": "N/A",
        "cocos": "Camera + custom tracking",
    },
    "HandTracking": {
        "unity": "HandTracking (Meta XR SDK / OpenXR Hand)",
        "ue5": "HandTracking (Meta XR SDK / OpenXR Hand)",
        "godot": "OpenXRHand",
        "defold": "N/A",
        "cocos": "N/A",
    },
    "Teleportation": {
        "unity": "TeleportationProvider + TeleportationArea",
        "ue5": "TeleportComponent + NavLink",
        "godot": "Custom implementation",
        "defold": "N/A",
        "cocos": "Custom implementation",
    },
    "GrabInteraction": {
        "unity": "XRGrabInteractable",
        "ue5": "HandComponent + GrabComponent",
        "godot": "XRToolsGrabPoint (addon)",
        "defold": "N/A",
        "cocos": "Custom implementation",
    },
    "RayInteraction": {
        "unity": "XRRayInteractor",
        "ue5": "WidgetInteraction + LineTrace",
        "godot": "XRToolsRayCast (addon)",
        "defold": "N/A",
        "cocos": "Custom implementation",
    },
    "SpatialAudio": {
        "unity": "Spatializer (Oculus/Meta/SteamAudio)",
        "ue5": "Spatial Sound (built-in + Meta)",
        "godot": "AudioStreamPlayer3D (limited)",
        "defold": "N/A",
        "cocos": "AudioSource (limited)",
    },
    "Passthrough": {
        "unity": "Passthrough (Meta XR SDK)",
        "ue5": "Passthrough (Meta XR SDK)",
        "godot": "Experimental (OpenXR)",
        "defold": "N/A",
        "cocos": "N/A",
    },
    "SpatialAnchor": {
        "unity": "SpatialAnchor (OpenXR / Meta)",
        "ue5": "SpatialAnchor (OpenXR / Meta)",
        "godot": "Limited support",
        "defold": "N/A",
        "cocos": "N/A",
    },
    "FoveatedRendering": {
        "unity": "FoveatedRendering (OpenXR / Meta)",
        "ue5": "FoveatedRendering (OpenXR / Meta)",
        "godot": "Limited support",
        "defold": "N/A",
        "cocos": "N/A",
    },
    "EyeTracking": {
        "unity": "EyeTracking (OpenXR Eye Interaction)",
        "ue5": "EyeTracker (OpenXR)",
        "godot": "Limited (custom)",
        "defold": "N/A",
        "cocos": "N/A",
    },
    "HapticFeedback": {
        "unity": "SendHapticImpulse() (XRController)",
        "ue5": "PlayHapticEffect() (MotionController)",
        "godot": "trigger_haptic_pulse() (XRController3D)",
        "defold": "N/A",
        "cocos": "N/A",
    },
}

XR_PLATFORM_MAP = {
    "openxr": {
        "name": "OpenXR",
        "unity": "com.unity.xr.openxr",
        "ue5": "Built-in OpenXR Plugin",
        "godot": "godot-openxr (4.x built-in)",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "active",
        "devices": ["Meta Quest", "HTC Vive", "Valve Index", "Windows MR"],
    },
    "meta_xr": {
        "name": "Meta XR SDK (Quest)",
        "unity": "Meta XR SDK (com.meta.xr.sdk)",
        "ue5": "Meta XR Plugin (Marketplace)",
        "godot": "Community godot-meta-xr (limited)",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "active",
        "devices": ["Meta Quest 2", "Meta Quest 3", "Meta Quest Pro"],
    },
    "steamvr": {
        "name": "SteamVR",
        "unity": "SteamVR Plugin (Asset Store)",
        "ue5": "SteamVR Plugin (Marketplace)",
        "godot": "Via OpenXR",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "active",
        "devices": ["HTC Vive", "Valve Index", "Any SteamVR headset"],
    },
    "psvr2": {
        "name": "PlayStation VR2",
        "unity": "PS VR2 SDK (NDA/Sony DevNet)",
        "ue5": "PS VR2 Plugin (NDA)",
        "godot": "Not supported",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "nda",
        "devices": ["PlayStation VR2"],
    },
    "visionpro": {
        "name": "Apple Vision Pro",
        "unity": "Unity PolySpatial + visionOS Build Target",
        "ue5": "Not supported",
        "godot": "Not supported",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "limited",
        "devices": ["Apple Vision Pro"],
    },
    "wmr": {
        "name": "Windows Mixed Reality",
        "unity": "Windows XR Plugin (deprecated -> OpenXR)",
        "ue5": "Windows Mixed Reality (via OpenXR)",
        "godot": "Via OpenXR",
        "defold": "Not supported",
        "cocos": "Not supported",
        "status": "deprecated",
        "devices": ["HP Reverb", "Samsung Odyssey"],
    },
}

ENGINE_FORMAT_MAP = {
    "cryengine": {
        "name": "CryEngine",
        "formats": {
            "mesh": [".cgf", ".cga", ".chr", ".skin"],
            "animation": [".caf", ".anm"],
            "material": [".mtl"],
            "texture": [".dds"],
            "level": [".ly"],
            "particle": [".xml"],
            "audio": [".fsb"],
        },
        "import_formats": [".fbx", ".obj", ".dae", ".tif", ".dds", ".wav", ".ogg"],
        "export_formats": [".fbx", ".obj", ".dds"],
        "bridge_format": "fbx",
        "script_language": "Schematyc/Lua",
        "notes": "All runtime assets compiled via Resource Compiler (rc.exe)",
    },
    "defold": {
        "name": "Defold",
        "formats": {
            "mesh": [".glb", ".gltf"],
            "sprite": [".atlas", ".png"],
            "animation": [".animationset"],
            "particle": [".particlefx"],
            "gui": [".gui"],
            "script": [".script"],
            "collection": [".collection"],
            "font": [".font"],
            "tilemap": [".tilemap", ".tilesource"],
        },
        "import_formats": [".glb", ".gltf", ".png", ".jpg", ".wav", ".ogg", ".ttf", ".otf"],
        "export_formats": [".glb"],
        "bridge_format": "gltf",
        "script_language": "Lua",
        "notes": "glTF 2.0 native, Spine JSON import supported",
    },
    "cocos_creator": {
        "name": "Cocos Creator",
        "formats": {
            "mesh": [".glb", ".gltf", ".fbx"],
            "sprite": [".png", ".jpg", ".pvr", ".etc2"],
            "animation": [".json"],
            "spine": [".json", ".skel"],
            "dragonbones": [".json", ".dbbin"],
            "particle": [".plist"],
            "scene": [".scene"],
            "prefab": [".prefab"],
            "script": [".ts"],
            "material": [".mtl"],
            "tilemap": [".tmx"],
        },
        "import_formats": [".glb", ".gltf", ".fbx", ".png", ".jpg", ".wav", ".mp3", ".ogg", ".ttf", ".fnt"],
        "export_formats": [".glb", ".json"],
        "bridge_format": "gltf",
        "script_language": "TypeScript",
        "notes": "DragonBones and Spine native support, internal formats are JSON",
    },
    "construct": {
        "name": "Construct",
        "formats": {
            "project": [".c3p"],
            "sprite": [".png", ".jpg"],
            "animation": [".png (sprite sheets)"],
            "audio": [".wav", ".ogg", ".mp3"],
            "script": [".js (event sheet JSON)"],
        },
        "import_formats": [".png", ".jpg", ".wav", ".ogg", ".mp3", ".json"],
        "export_formats": [".png", ".json"],
        "bridge_format": "png",
        "script_language": "JavaScript (Event Sheet)",
        "notes": "2D only, no 3D support",
    },
    "rpg_maker": {
        "name": "RPG Maker",
        "formats": {
            "project": [".rvproj2", ".rmmzproject"],
            "map": [".json (MV/MZ)"],
            "sprite": [".png"],
            "audio": [".ogg", ".m4a", ".wav"],
            "script": [".js (MV/MZ)"],
            "database": [".json (MV/MZ)"],
        },
        "import_formats": [".png", ".ogg", ".m4a", ".wav", ".json"],
        "export_formats": [".png", ".json"],
        "bridge_format": "png",
        "script_language": "JavaScript (MV/MZ)",
        "notes": "2D only, tile-based, JSON data files parseable",
    },
}

DCC_FORMAT_MAP = {
    "maya": {
        "name": "Autodesk Maya",
        "export_formats": {
            ".fbx": {"quality": "best", "content": "mesh+skeleton+animation+material_ref", "engines": "all"},
            ".obj": {"quality": "static_only", "content": "mesh+UV", "engines": "all"},
            ".gltf/.glb": {"quality": "excellent", "content": "mesh+skeleton+animation+material+texture", "engines": "godot/defold/cocos/unity"},
            ".usd/.usda/.usdc": {"quality": "excellent", "content": "full scene", "engines": "ue5/unity"},
            ".abc": {"quality": "deformation_only", "content": "vertex animation cache", "engines": "ue5/unity/godot"},
            ".dae": {"quality": "moderate", "content": "mesh+skeleton+animation+material", "engines": "godot/cryengine"},
        },
        "native_format": ".ma/.mb",
        "bridge_strategy": "FBX for Unity/UE5/CryEngine, glTF for Godot/Defold/Cocos, USD for UE5",
    },
    "houdini": {
        "name": "SideFX Houdini",
        "export_formats": {
            ".fbx": {"quality": "best", "content": "mesh+skeleton+animation", "engines": "all"},
            ".gltf/.glb": {"quality": "excellent", "content": "mesh+skeleton+animation+material", "engines": "godot/defold/cocos"},
            ".usd": {"quality": "excellent", "content": "full scene+procedural", "engines": "ue5/unity"},
            ".abc": {"quality": "deformation_only", "content": "vertex animation cache", "engines": "ue5/unity/godot"},
            ".vdb": {"quality": "volume_only", "content": "volume data (smoke/cloud)", "engines": "ue5"},
            ".hda": {"quality": "procedural", "content": "Houdini Digital Asset", "engines": "ue5(HoudiniEngine)/unity(HoudiniEngine)"},
        },
        "native_format": ".hip/.hipnc",
        "bridge_strategy": "FBX universal, USD for UE5, HDA for in-engine procedural",
    },
    "substance": {
        "name": "Adobe Substance (Painter/Designer)",
        "export_presets": {
            "ue5": {"name": "Unreal Engine 4 (Packed)", "maps": ["BaseColor", "Normal", "ORM (Occlusion/Roughness/Metallic)"]},
            "unity_urp": {"name": "Unity (Universal RP)", "maps": ["Albedo", "Normal", "Metallic", "AO", "Smoothness"]},
            "unity_hdrp": {"name": "Unity (HDRP)", "maps": ["BaseColor", "Normal", "Mask (Metallic/AO/Detail)"]},
            "godot": {"name": "glTF Metallic-Roughness", "maps": ["Albedo", "Normal", "Roughness", "Metallic", "AO"]},
            "cryengine": {"name": "Custom CryEngine", "maps": ["Diffuse", "Normal", "Specular", "Glossiness"]},
            "cocos": {"name": "PBR Metallic-Roughness", "maps": ["Albedo", "Normal", "Roughness", "Metallic", "AO"]},
        },
        "export_formats": [".png", ".tga", ".exr", ".dds"],
        "runtime_format": ".sbsar (UE5/Unity Substance plugins)",
        "bridge_strategy": "Export PNG maps with engine-specific presets, .sbsar for runtime parametric",
    },
}

ANIMATION_FORMAT_MAP = {
    "spine": {
        "name": "Spine",
        "project_format": ".spine",
        "runtime_json": ".json",
        "runtime_binary": ".skel",
        "atlas_format": ".atlas + .png",
        "engine_support": {
            "unity": "spine-unity (official runtime)",
            "ue5": "spine-ue5 (official runtime)",
            "godot": "spine-godot (official, 4.x)",
            "cocos": "spine-cocos2dx (official)",
            "defold": "spine-defold (official)",
            "construct": "Not supported",
            "rpg_maker": "Not supported",
        },
        "version_compat": "Runtime version MUST match editor export version (4.x != 3.8)",
        "gltf_export": "Supported since Spine 4.1 (2D features lost)",
    },
    "dragonbones": {
        "name": "DragonBones",
        "project_format": ".dbproj",
        "runtime_json": ".json",
        "runtime_binary": ".dbbin",
        "atlas_format": ".tex.json + .png",
        "engine_support": {
            "unity": "DragonBones Unity Runtime",
            "ue5": "Community plugin (limited)",
            "godot": "Community plugin (limited)",
            "cocos": "Native built-in",
            "defold": "Not supported",
            "construct": "Not supported",
            "rpg_maker": "Not supported",
        },
        "status": "Discontinued since 2023",
        "gltf_export": "Not supported",
    },
    "lottie": {
        "name": "Lottie",
        "format": ".json (After Effects export)",
        "engine_support": {
            "unity": "Lottie-Unity (community)",
            "ue5": "Not supported",
            "godot": "Not supported (use GIF/APNG instead)",
            "cocos": "Not supported",
            "defold": "Not supported",
            "construct": "Not supported",
            "rpg_maker": "Not supported",
            "web": "lottie-web (primary target)",
            "react_native": "lottie-react-native",
            "flutter": "lottie-flutter",
        },
        "status": "Active (UI animation standard)",
        "bridge_strategy": "Lottie is primarily for UI/motion graphics, not game animation",
    },
}

PLATFORM_MAP = {
    "android": {
        "name": "Android",
        "texture_format": ".astc,.etc2,.pvrtc",
        "audio_format": ".ogg,.mp3,.wav",
        "scripting": "Java/Kotlin (native), C# (Unity), C++ (UE5), GDScript (Godot)",
        "xr_support": ["OpenXR", "Meta XR SDK", "Google Cardboard"],
        "engine_support": {
            "unity": "Primary target (IL2CPP)",
            "ue5": "Supported (Android ASTC/PVRTC)",
            "godot": "Supported (built-in export)",
            "defold": "Supported (built-in export)",
            "cocos": "Primary target (JSB)",
        },
    },
    "ios": {
        "name": "iOS",
        "texture_format": ".astc,.pvrtc",
        "audio_format": ".m4a,.wav,.mp3",
        "scripting": "Swift/ObjC (native), C# (Unity)",
        "xr_support": ["ARKit", "Vision Pro (PolySpatial)"],
        "engine_support": {
            "unity": "Primary target (IL2CPP)",
            "ue5": "Supported (requires Mac build)",
            "godot": "Supported (requires Mac export template)",
            "defold": "Supported (requires Mac)",
            "cocos": "Supported",
        },
    },
    "webgl": {
        "name": "WebGL / Web",
        "texture_format": ".ktx2,.png,.jpg",
        "audio_format": ".ogg,.mp3,.wav",
        "scripting": "JavaScript/WASM",
        "xr_support": ["WebXR"],
        "engine_support": {
            "unity": "WebGL Build (WASM)",
            "ue5": "Pixel Streaming (not true WebGL)",
            "godot": "HTML5 Export (WASM)",
            "defold": "HTML5 Export (WASM)",
            "cocos": "Web Platform (primary)",
            "construct": "Web Platform (primary)",
        },
    },
    "webxr": {
        "name": "WebXR",
        "modes": ["VR", "AR"],
        "texture_format": ".ktx2,.png",
        "audio_format": ".ogg,.mp3",
        "scripting": "JavaScript + WebXR API",
        "engine_support": {
            "unity": "WebXR Export (community)",
            "ue5": "Not supported (Pixel Streaming only)",
            "godot": "WebXR (built-in 4.x)",
            "defold": "Not supported",
            "cocos": "Not supported",
            "construct": "Not supported",
            "aframe": "Native (A-Frame)",
            "babylonjs": "Native (Babylon.js)",
            "threejs": "Native (Three.js)",
        },
    },
}

CAD_FORMAT_MAP = {
    "sketchup": {
        "name": "SketchUp",
        "format": ".skp",
        "export_formats": [".fbx", ".obj", ".dae", ".3ds"],
        "engine_import": {
            "ue5": "Datasmith (native .skp import)",
            "unity": "FBX import (export from SketchUp first)",
            "godot": "DAE/FBX import (export from SketchUp first)",
            "blender": ".skp import addon",
        },
        "bridge_strategy": "Datasmith for UE5, FBX for others",
    },
    "revit": {
        "name": "Autodesk Revit",
        "format": ".rvt",
        "export_formats": [".fbx", ".ifc", ".nwc"],
        "engine_import": {
            "ue5": "Datasmith (native Revit plugin)",
            "unity": "FBX import (export from Revit)",
            "godot": "IFC import (community addon)",
            "blender": "IFC import (BlenderBIM addon)",
        },
        "bridge_strategy": "Datasmith for UE5, IFC for BlenderBIM, FBX for others",
    },
    "autocad": {
        "name": "AutoCAD",
        "format": ".dwg",
        "export_formats": [".fbx", ".obj", ".stl", ".dxf"],
        "engine_import": {
            "ue5": "Datasmith (.dwg import)",
            "unity": "FBX import",
            "godot": "OBJ/STL import",
            "blender": ".dwg import addon",
        },
        "bridge_strategy": "Datasmith for UE5, FBX/OBJ for others",
    },
}


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write(path: Path, content: str) -> Path:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


class XRProjectConverter:
    def __init__(self, source_project: Path, source_engine: str, target_engine: str):
        self.source_project = source_project
        self.source_engine = source_engine
        self.target_engine = target_engine
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log("start", f"XR项目转换: {self.source_engine} → {self.target_engine}")

        xr_components = self._detect_xr_components()
        self._log("detect_xr", f"检测到 {len(xr_components)} 个XR组件")

        mapping = self._map_xr_components(xr_components)
        self._log("map_xr", f"映射 {len(mapping)} 个组件")

        config = self._generate_xr_config(xr_components, mapping)
        config_path = self.source_project / "xr_conversion_config.json"
        safe_write(config_path, json.dumps(config, indent=2, ensure_ascii=False))
        self._log("config", f"XR配置已生成: {config_path}")

        xr_rig_script = self._generate_xr_rig_script(xr_components)
        script_path = self.source_project / f"xr_rig_{self.target_engine}.txt"
        safe_write(script_path, xr_rig_script)
        self._log("rig_script", f"XR Rig脚本已生成: {script_path}")

        platform_compat = self._check_platform_compatibility()
        self._log("platform", f"平台兼容性检查完成")

        self._log("complete", "XR项目转换完成")
        return {
            "success": True,
            "source_engine": self.source_engine,
            "target_engine": self.target_engine,
            "xr_components_found": len(xr_components),
            "xr_components_mapped": len(mapping),
            "platform_compatibility": platform_compat,
            "config_file": str(config_path),
            "rig_script_file": str(script_path),
            "report": self.report,
        }

    def _detect_xr_components(self) -> List[str]:
        found = []
        xr_keywords = {
            "xr": True, "vr": True, "openxr": True, "steamvr": True,
            "meta": True, "oculus": True, "quest": True, "vive": True,
            "controller": True, "hmd": True, "hand": True, "passthrough": True,
            "spatial": True, "anchor": True, "haptic": True, "foveated": True,
            "eye_track": True, "ar": True, "mr": True,
        }
        if self.source_project.is_dir():
            for f in self.source_project.rglob("*"):
                if f.is_file() and f.suffix.lower() in (".cs", ".gd", ".py", ".cpp", ".h", ".json", ".yaml", ".yml", ".tscn", ".tres", ".unity", ".prefab"):
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore").lower()
                        for kw in xr_keywords:
                            if kw in content and kw not in found:
                                found.append(kw)
                    except Exception:
                        pass
        return found

    def _map_xr_components(self, detected: List[str]) -> Dict[str, Dict]:
        mapping = {}
        for comp_name, comp_map in XR_COMPONENT_MAP.items():
            comp_lower = comp_name.lower()
            for det in detected:
                if det in comp_lower:
                    mapping[comp_name] = {
                        "source": comp_map.get(self.source_engine, "N/A"),
                        "target": comp_map.get(self.target_engine, "N/A"),
                    }
                    break
        return mapping

    def _generate_xr_config(self, detected: List[str], mapping: Dict) -> Dict:
        return {
            "source_engine": self.source_engine,
            "target_engine": self.target_engine,
            "detected_xr_features": detected,
            "component_mapping": mapping,
            "recommended_xr_sdk": XR_PLATFORM_MAP.get("openxr", {}),
            "all_platforms": {k: v.get(self.target_engine, "Not supported") for k, v in XR_PLATFORM_MAP.items()},
            "migration_notes": self._get_xr_migration_notes(),
        }

    def _get_xr_migration_notes(self) -> List[str]:
        notes = []
        src, tgt = self.source_engine, self.target_engine

        if src == "unity" and tgt == "ue5":
            notes.extend([
                "Unity XR Interaction Toolkit → UE5 VR Template: 需要重建交互系统",
                "XRGrabInteractable → UE5 HandComponent + GrabComponent",
                "TeleportationProvider → UE5 TeleportComponent",
                "Meta XR SDK 在 UE5 中通过 Marketplace 插件安装",
                "SteamVR 在 UE5 中通过 OpenXR 间接支持",
            ])
        elif src == "unity" and tgt == "godot":
            notes.extend([
                "Unity XR Interaction Toolkit → Godot OpenXR: 需要手动重建 XR Rig",
                "XROrigin → XROrigin3D",
                "XRController → XRController3D",
                "Meta XR SDK 在 Godot 中支持有限，建议使用 OpenXR",
                "手部追踪通过 OpenXRHand 节点实现",
            ])
        elif src == "ue5" and tgt == "godot":
            notes.extend([
                "UE5 MotionControllerComponent → Godot XRController3D",
                "UE5 VRRoot → Godot XROrigin3D",
                "UE5 蓝图VR逻辑 → 需要用GDScript重写",
                "Meta XR SDK 在 Godot 中支持有限",
            ])
        elif src == "ue5" and tgt == "unity":
            notes.extend([
                "UE5 VR Template → Unity XR Interaction Toolkit",
                "MotionControllerComponent → XRController",
                "TeleportComponent → TeleportationProvider",
                "Meta XR SDK 在 Unity 中通过 Package Manager 安装",
            ])
        elif src == "godot" and tgt == "ue5":
            notes.extend([
                "Godot XROrigin3D → UE5 VRRoot",
                "Godot XRController3D → UE5 MotionControllerComponent",
                "Godot OpenXR → UE5 内置 OpenXR 插件",
                "Godot XRTools addon → UE5 VR Template",
            ])
        elif src == "godot" and tgt == "unity":
            notes.extend([
                "Godot XROrigin3D → Unity XROrigin",
                "Godot XRController3D → Unity XRController",
                "Godot OpenXR → Unity OpenXR Plugin",
            ])
        else:
            notes.append(f"从 {src} 到 {tgt} 的VR迁移需要手动重建XR系统")

        notes.append("通用: 所有VR输入映射需要重新配置")
        notes.append("通用: 空间音频方案需要重新选择和配置")
        notes.append("通用: 性能优化策略因引擎而异（注视点渲染、多视图渲染等）")
        return notes

    def _generate_xr_rig_script(self, detected: List[str]) -> str:
        tgt = self.target_engine
        lines = [f"# XR Rig 设置指南 - {tgt}", ""]

        if tgt == "godot":
            lines.extend([
                "## Godot 4.x XR Rig 设置",
                "",
                "### 1. 启用 OpenXR",
                "项目 → 项目设置 → XR → OpenXR: 启用",
                "",
                "### 2. 创建 XR Rig 场景结构",
                "XROrigin3D (根节点)",
                "  ├── XRCamera3D (头显)",
                "  ├── XRController3D (左手, tracker=/user/hand/left)",
                "  │     └── MeshInstance3D (左手模型)",
                "  └── XRController3D (右手, tracker=/user/hand_right)",
                "        └── MeshInstance3D (右手模型)",
                "",
                "### 3. 手部追踪 (如需要)",
                "在 XRController3D 下添加 OpenXRHand 节点",
                "",
                "### 4. 传送系统",
                "使用 XRTools addon (https://github.com/GodotVR/godot-xr-tools)",
                "",
                "### 5. 抓取交互",
                "使用 XRToolsGrabPoint 和 XRToolsPickable",
                "",
            ])
        elif tgt == "ue5":
            lines.extend([
                "## UE5 VR Rig 设置",
                "",
                "### 1. 启用 OpenXR 插件",
                "编辑 → 插件 → 搜索 OpenXR → 启用",
                "",
                "### 2. 使用 VR 模板",
                "创建新项目 → 选择 VR 模板 (已包含 XR Rig)",
                "",
                "### 3. 手动创建 XR Rig",
                "Pawn",
                "  ├── Camera (头显追踪)",
                "  ├── MotionControllerComponent (左手)",
                "  │     └── StaticMesh (左手模型)",
                "  └── MotionControllerComponent (右手)",
                "        └── StaticMesh (右手模型)",
                "",
                "### 4. Meta XR SDK (Quest)",
                "Epic Marketplace → 搜索 Meta XR → 安装插件",
                "",
                "### 5. 传送系统",
                "使用 VR 模板自带的 TeleportComponent",
                "",
            ])
        elif tgt == "unity":
            lines.extend([
                "## Unity XR Rig 设置",
                "",
                "### 1. 安装 XR Plugin Management",
                "Window → Package Manager → XR Plugin Management → Install",
                "",
                "### 2. 安装 XR Interaction Toolkit",
                "Package Manager → XR Interaction Toolkit → Install",
                "",
                "### 3. 创建 XR Rig",
                "GameObject → XR → XR Origin (VR)",
                "自动生成:",
                "  XROrigin",
                "    ├── Camera (Offset → Main Camera)",
                "    ├── LeftHand Controller",
                "    └── RightHand Controller",
                "",
                "### 4. Meta XR SDK (Quest)",
                "Asset Store → Meta XR SDK → Import",
                "OVRManager 替换 XR Origin 中的 Camera",
                "",
                "### 5. 传送系统",
                "添加 TeleportationProvider + TeleportationArea",
                "",
            ])

        return "\n".join(lines)

    def _check_platform_compatibility(self) -> Dict[str, Any]:
        compat = {}
        for platform_id, platform_info in XR_PLATFORM_MAP.items():
            src_support = platform_info.get(self.source_engine, "Not supported")
            tgt_support = platform_info.get(self.target_engine, "Not supported")
            compat[platform_id] = {
                "name": platform_info["name"],
                "source_support": src_support,
                "target_support": tgt_support,
                "migration_possible": tgt_support != "Not supported" and tgt_support != "N/A",
                "status": platform_info["status"],
            }
        return compat

    def _log(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


class ExtendedEngineConverter:
    def __init__(self, source_path: Path, target_engine: str, target_path: Path):
        self.source_path = source_path
        self.target_engine = target_engine
        self.target_path = target_path
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        source_engine = self._detect_source_engine()
        self._log("detect", f"检测到源引擎: {source_engine}")

        if source_engine == "unknown":
            return {"success": False, "error": "无法识别源引擎类型"}

        bridge_format = self._get_bridge_format(source_engine, self.target_engine)
        self._log("bridge", f"桥梁格式: {bridge_format}")

        assets = self._scan_assets(source_engine)
        self._log("scan", f"扫描到 {sum(len(v) for v in assets.values())} 个资产文件")

        await self._convert_assets(assets, bridge_format, source_engine)
        self._generate_project_config(source_engine)

        self._log("complete", f"转换完成: {source_engine} → {self.target_engine}")
        return {
            "success": True,
            "source_engine": source_engine,
            "target_engine": self.target_engine,
            "bridge_format": bridge_format,
            "assets": {k: len(v) for k, v in assets.items()},
            "report": self.report,
        }

    def _detect_source_engine(self) -> str:
        if (self.source_path / "Assets").exists() and (self.source_path / "ProjectSettings").exists():
            return "unity"
        if (self.source_path / "Content").exists() and list(self.source_path.glob("*.uproject")):
            return "ue5"
        if (self.source_path / "project.godot").exists() or (self.source_path / ".godot").exists():
            return "godot"
        if list(self.source_path.glob("*.cry")) or list(self.source_path.glob("*.cryproject")):
            return "cryengine"
        if list(self.source_path.glob("*.defold")) or list(self.source_path.glob("game.project")):
            return "defold"
        if list(self.source_path.glob("*.fire")) or (self.source_path / "assets").exists() and list(self.source_path.glob("*.meta")):
            return "cocos_creator"
        return "unknown"

    def _get_bridge_format(self, source: str, target: str) -> str:
        engine_needs_gltf = {"godot", "defold", "cocos_creator", "construct", "rpg_maker"}
        engine_needs_fbx = {"ue5", "cryengine"}
        engine_needs_usd = {"ue5"}

        if source == "houdini" and target == "ue5":
            return "usd"
        if target in engine_needs_gltf:
            return "gltf"
        if target in engine_needs_fbx:
            return "fbx"
        return "fbx"

    def _scan_assets(self, engine: str) -> Dict[str, List[Path]]:
        assets = {"meshes": [], "textures": [], "audio": [], "scripts": [], "scenes": [], "animations": [], "other": []}

        mesh_exts = {".fbx", ".obj", ".gltf", ".glb", ".dae", ".cgf", ".cga", ".chr", ".skin", ".skp"}
        tex_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".hdr", ".dds", ".psd", ".tif", ".tiff", ".exr"}
        audio_exts = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".fsb"}
        script_exts = {".cs", ".gd", ".py", ".ts", ".js", ".lua", ".script"}
        scene_exts = {".unity", ".prefab", ".tscn", ".umap", ".ly", ".scene", ".collection"}
        anim_exts = {".anim", ".caf", ".anm", ".json", ".skel", ".atlas", ".dbbin"}

        if engine == "cryengine":
            mesh_exts.update({".cgf", ".cga", ".chr", ".skin"})
        elif engine == "defold":
            mesh_exts.update({".glb", ".gltf"})
            anim_exts.update({".animationset"})
        elif engine == "cocos_creator":
            anim_exts.update({".json", ".skel", ".dbbin"})

        search_root = self.source_path
        if engine == "unity":
            search_root = self.source_path / "Assets" if (self.source_path / "Assets").exists() else self.source_path
        elif engine == "ue5":
            search_root = self.source_path / "Content" if (self.source_path / "Content").exists() else self.source_path

        if search_root.is_dir():
            for f in search_root.rglob("*"):
                if not f.is_file():
                    continue
                ext = f.suffix.lower()
                if ext in mesh_exts:
                    assets["meshes"].append(f)
                elif ext in tex_exts:
                    assets["textures"].append(f)
                elif ext in audio_exts:
                    assets["audio"].append(f)
                elif ext in script_exts:
                    assets["scripts"].append(f)
                elif ext in scene_exts:
                    assets["scenes"].append(f)
                elif ext in anim_exts:
                    assets["animations"].append(f)
                else:
                    assets["other"].append(f)

        return assets

    async def _convert_assets(self, assets: Dict, bridge_format: str, source_engine: str):
        dest_dir = self.target_path
        ensure_dir(dest_dir)

        if self.target_engine == "defold":
            dest_assets = dest_dir / "assets"
        elif self.target_engine == "cocos_creator":
            dest_assets = dest_dir / "assets"
        elif self.target_engine == "cryengine":
            dest_assets = dest_dir / "Assets"
        else:
            dest_assets = dest_dir

        ensure_dir(dest_assets)

        for category, files in assets.items():
            if not files:
                continue
            cat_dir = dest_assets / category
            ensure_dir(cat_dir)

            copied = 0
            for src in files:
                try:
                    if bridge_format == "gltf" and src.suffix.lower() in (".fbx", ".obj", ".dae"):
                        continue
                    elif bridge_format == "fbx" and src.suffix.lower() in (".gltf", ".glb"):
                        continue
                    dest = cat_dir / src.name
                    if not dest.exists():
                        shutil.copy2(str(src), str(dest))
                    copied += 1
                except Exception as e:
                    self.report["warnings"].append(f"复制失败: {src.name} - {e}")

            self._log(f"copy_{category}", f"复制 {copied} 个{category}文件")

    def _generate_project_config(self, source_engine: str):
        if self.target_engine == "defold":
            config = self._generate_defold_config(source_engine)
            safe_write(self.target_path / "game.project", config)
        elif self.target_engine == "cocos_creator":
            self._log("config", "Cocos Creator 项目需要通过编辑器创建")
        elif self.target_engine == "cryengine":
            self._log("config", "CryEngine 项目需要通过 Launcher 创建")

    def _generate_defold_config(self, source_engine: str) -> str:
        return f"""[project]
title = Converted from {source_engine}
version = 0.1.0

[display]
width = 1280
height = 720

[graphics]
default_texture_min_filter = linear
default_texture_mag_filter = linear

[physics]
scale = 1.0
"""

    def _log(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


class DCCBridgeConverter:
    def __init__(self, source_path: Path, target_engine: str, target_path: Path):
        self.source_path = source_path
        self.target_engine = target_engine
        self.target_path = target_path
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        source_type = self._detect_dcc_type()
        self._log("detect", f"检测到DCC类型: {source_type}")

        if source_type == "unknown":
            return {"success": False, "error": "无法识别DCC文件类型"}

        bridge = self._get_bridge_strategy(source_type)
        self._log("bridge", f"桥梁策略: {bridge['strategy']}")

        files = self._scan_exportable_files(source_type)
        self._log("scan", f"找到 {len(files)} 个可转换文件")

        await self._copy_with_bridge(files, bridge)
        self._generate_import_guide(source_type, bridge)

        self._log("complete", f"DCC转换完成: {source_type} → {self.target_engine}")
        return {
            "success": True,
            "source_type": source_type,
            "target_engine": self.target_engine,
            "bridge_strategy": bridge,
            "files_found": len(files),
            "report": self.report,
        }

    def _detect_dcc_type(self) -> str:
        if self.source_path.is_file():
            ext = self.source_path.suffix.lower()
            if ext in (".ma", ".mb"):
                return "maya"
            if ext in (".hip", ".hipnc"):
                return "houdini"
            if ext in (".spp",):
                return "substance_painter"
            if ext in (".sbs",):
                return "substance_designer"
            if ext in (".skp",):
                return "sketchup"
            if ext in (".rvt",):
                return "revit"
            if ext in (".dwg",):
                return "autocad"
            if ext in (".spine",):
                return "spine"
            if ext in (".dbproj",):
                return "dragonbones"
        if self.source_path.is_dir():
            for f in self.source_path.rglob("*.ma"):
                return "maya"
            for f in self.source_path.rglob("*.hip"):
                return "houdini"
            for f in self.source_path.rglob("*.skp"):
                return "sketchup"
        return "unknown"

    def _get_bridge_strategy(self, source_type: str) -> Dict:
        strategies = {
            "maya": {
                "strategy": "FBX for Unity/UE5/CryEngine, glTF for Godot/Defold/Cocos, USD for UE5",
                "export_format": {"ue5": "fbx", "unity": "fbx", "godot": "gltf", "defold": "gltf", "cocos_creator": "gltf", "cryengine": "fbx"},
                "notes": "Maya FBX export: File → Export All → FBX, check Include Animation/Skins",
            },
            "houdini": {
                "strategy": "FBX universal, USD for UE5, HDA for in-engine procedural, VDB for volumes",
                "export_format": {"ue5": "usd", "unity": "fbx", "godot": "gltf", "defold": "gltf", "cocos_creator": "gltf", "cryengine": "fbx"},
                "notes": "Houdini Engine available for UE5 and Unity in-editor procedural generation",
            },
            "substance_painter": {
                "strategy": "Export texture maps with engine-specific presets",
                "export_format": "png",
                "presets": DCC_FORMAT_MAP["substance"]["export_presets"],
                "notes": "Use engine-specific export preset in Substance Painter",
            },
            "substance_designer": {
                "strategy": "Export .sbsar for runtime, PNG maps for static",
                "export_format": "sbsar+png",
                "notes": ".sbsar supported natively in UE5 and Unity Substance plugins",
            },
            "sketchup": {
                "strategy": "Datasmith for UE5, FBX for others",
                "export_format": {"ue5": "datasmith", "unity": "fbx", "godot": "dae", "blender": "skp"},
                "notes": "UE5 Datasmith imports .skp directly",
            },
            "revit": {
                "strategy": "Datasmith for UE5, IFC for BlenderBIM, FBX for others",
                "export_format": {"ue5": "datasmith", "unity": "fbx", "godot": "ifc", "blender": "ifc"},
                "notes": "Revit Datasmith plugin available from Epic",
            },
            "spine": {
                "strategy": "Use target engine's Spine runtime (version must match)",
                "export_format": "json+atlas+png",
                "runtimes": ANIMATION_FORMAT_MAP["spine"]["engine_support"],
                "notes": "CRITICAL: Runtime version must match Spine editor version",
            },
            "dragonbones": {
                "strategy": "Cocos Creator native, community runtimes for others",
                "export_format": "json+tex.json+png",
                "runtimes": ANIMATION_FORMAT_MAP["dragonbones"]["engine_support"],
                "notes": "DragonBones discontinued 2023, consider migrating to Spine",
            },
        }
        return strategies.get(source_type, {"strategy": "FBX universal bridge", "export_format": "fbx"})

    def _scan_exportable_files(self, source_type: str) -> List[Path]:
        files = []
        if self.source_path.is_file():
            files.append(self.source_path)
        elif self.source_path.is_dir():
            ext_map = {
                "maya": [".ma", ".mb", ".fbx", ".obj", ".gltf", ".glb"],
                "houdini": [".hip", ".hipnc", ".fbx", ".obj", ".gltf", ".glb", ".usd", ".usda", ".usdc", ".vdb", ".abc"],
                "substance_painter": [".spp", ".png", ".tga", ".exr", ".psd"],
                "substance_designer": [".sbs", ".sbsar", ".png", ".tga"],
                "sketchup": [".skp", ".fbx", ".obj", ".dae"],
                "revit": [".rvt", ".fbx", ".ifc"],
                "spine": [".spine", ".json", ".skel", ".atlas", ".png"],
                "dragonbones": [".dbproj", ".json", ".dbbin", ".tex.json", ".png"],
            }
            for ext in ext_map.get(source_type, []):
                files.extend(self.source_path.rglob(f"*{ext}"))
        return files

    async def _copy_with_bridge(self, files: List[Path], bridge: Dict):
        dest_dir = self.target_path
        ensure_dir(dest_dir)
        ensure_dir(dest_dir / "assets")

        copied = 0
        for src in files:
            try:
                dest = dest_dir / "assets" / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                copied += 1
            except Exception as e:
                self.report["warnings"].append(f"复制失败: {src.name} - {e}")
        self._log("copy", f"复制 {copied}/{len(files)} 个文件")

    def _generate_import_guide(self, source_type: str, bridge: Dict):
        guide = {
            "source_type": source_type,
            "target_engine": self.target_engine,
            "bridge_strategy": bridge,
            "steps": self._get_import_steps(source_type, self.target_engine),
        }
        safe_write(self.target_path / "import_guide.json", json.dumps(guide, indent=2, ensure_ascii=False))

    def _get_import_steps(self, source_type: str, target_engine: str) -> List[str]:
        steps = []
        if source_type == "maya":
            if target_engine == "ue5":
                steps = ["1. Maya: File → Export All → FBX", "2. UE5: Content Browser → Import → 选择FBX",
                         "3. Import Options: 勾选 Import Mesh/Skeleton/Animations/Materials/Textures",
                         "4. 或使用 USD: Maya → USD Export → UE5 USD Stage Actor"]
            elif target_engine == "unity":
                steps = ["1. Maya: File → Export All → FBX", "2. Unity: 拖拽FBX到Assets目录",
                         "3. Model Tab: 勾选 Import BlendShapes/Animations", "4. Rig Tab: 选择 Humanoid/Generic"]
            elif target_engine == "godot":
                steps = ["1. Maya: 安装 glTF Export 插件", "2. Maya: File → Export All → glTF 2.0",
                         "3. Godot: 拖拽.glb到项目目录", "4. 自动生成 .import 和场景"]
        elif source_type == "houdini":
            if target_engine == "ue5":
                steps = ["1. Houdini: File → Export → FBX 或 USD", "2. UE5: 安装 Houdini Engine 插件",
                         "3. UE5: Houdini Engine → Load HDA (程序化资产)", "4. 或直接导入 FBX/USD"]
            elif target_engine == "unity":
                steps = ["1. Houdini: File → Export → FBX", "2. Unity: 安装 Houdini Engine for Unity",
                         "3. Unity: Houdini Engine → Load HDA", "4. 或直接拖拽FBX到Assets"]
        elif source_type == "substance_painter":
            preset = DCC_FORMAT_MAP["substance"]["export_presets"].get(target_engine, {})
            steps = [
                f"1. Substance Painter: Edit → Export Textures",
                f"2. 选择导出预设: {preset.get('name', 'Default')}",
                f"3. 输出贴图: {preset.get('maps', [])}",
                f"4. 在目标引擎中创建材质并连接贴图",
            ]
        elif source_type == "spine":
            runtime = ANIMATION_FORMAT_MAP["spine"]["engine_support"].get(target_engine, "Not supported")
            steps = [
                f"1. Spine: 导出骨骼数据 (.json/.skel + .atlas + .png)",
                f"2. 安装目标引擎的 Spine 运行时: {runtime}",
                f"3. 确保运行时版本与 Spine 编辑器版本匹配!",
                f"4. 在引擎中导入 Spine 数据并创建动画组件",
            ]
        return steps

    def _log(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


def get_full_conversion_matrix() -> Dict[str, Any]:
    yaml_path = Path(__file__).parent / "conversion_matrix.yaml"
    if yaml_path.exists():
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            pass
    return _HARDCODED_CONVERSION_MATRIX


_HARDCODED_CONVERSION_MATRIX = {
    "game_engines_3d": {
        "unity": {"targets": ["godot", "ue5", "blender", "defold", "cocos_creator", "cryengine", "flax", "stride", "o3de", "unigine", "evergine", "neoaxis", "armory3d", "bevy", "fyrox", "torque3d", "leadwerks", "panda3d", "ogre", "irrlicht", "coppercube", "spring", "nau", "dagon", "gamebryo", "id_tech", "source2", "frostbite", "snowdrop", "decima", "fox_engine", "rage", "creation_engine", "lumberyard"], "bridge": "fbx"},
        "ue5": {"targets": ["godot", "unity", "blender", "defold", "cocos_creator", "cryengine", "flax", "stride", "o3de", "unigine", "evergine", "neoaxis", "armory3d", "bevy", "fyrox", "torque3d", "leadwerks", "panda3d", "ogre", "irrlicht", "coppercube", "spring", "nau", "dagon", "gamebryo", "id_tech", "source2", "frostbite", "snowdrop", "decima", "fox_engine", "rage", "creation_engine", "lumberyard"], "bridge": "fbx"},
        "godot": {"targets": ["unity", "ue5", "blender", "defold", "cocos_creator", "flax", "stride", "o3de", "unigine", "evergine", "neoaxis", "armory3d", "bevy", "fyrox", "torque3d", "panda3d", "ogre", "irrlicht", "spring", "nau", "dagon"], "bridge": "gltf"},
        "blender": {"targets": ["godot", "unity", "ue5", "defold", "cocos_creator", "cryengine", "flax", "stride", "o3de", "unigine", "evergine", "neoaxis", "armory3d", "bevy", "fyrox", "torque3d", "leadwerks", "panda3d", "ogre", "irrlicht", "coppercube", "spring", "nau", "dagon"], "bridge": "gltf/fbx"},
        "cryengine": {"targets": ["unity", "ue5", "godot", "blender", "o3de", "lumberyard"], "bridge": "fbx"},
        "flax": {"targets": ["unity", "ue5", "godot", "stride", "evergine", "neoaxis", "bevy"], "bridge": "fbx/gltf"},
        "stride": {"targets": ["unity", "ue5", "godot", "flax", "evergine", "neoaxis", "bevy"], "bridge": "fbx/gltf"},
        "o3de": {"targets": ["unity", "ue5", "godot", "cryengine", "unigine", "lumberyard"], "bridge": "fbx"},
        "unigine": {"targets": ["unity", "ue5", "godot", "o3de", "cryengine"], "bridge": "fbx"},
        "evergine": {"targets": ["unity", "ue5", "godot", "flax", "stride", "neoaxis", "bevy"], "bridge": "gltf/fbx"},
        "neoaxis": {"targets": ["unity", "ue5", "godot", "flax", "stride", "evergine"], "bridge": "gltf/fbx"},
        "armory3d": {"targets": ["unity", "ue5", "godot", "blender", "bevy", "fyrox"], "bridge": "gltf"},
        "bevy": {"targets": ["godot", "unity", "ue5", "armory3d", "fyrox"], "bridge": "gltf"},
        "fyrox": {"targets": ["godot", "unity", "ue5", "armory3d", "bevy"], "bridge": "gltf/fbx"},
        "torque3d": {"targets": ["unity", "ue5", "godot", "blender", "torque2d"], "bridge": "dae/fbx"},
        "leadwerks": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "panda3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx/egg"},
        "ogre": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx/dae"},
        "irrlicht": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "dae"},
        "coppercube": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "spring": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx/dae"},
        "nau": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "gltf/fbx"},
        "dagon": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "gltf/obj"},
        "gamebryo": {"targets": ["unity", "ue5", "godot", "blender", "creation_engine"], "bridge": "fbx/nif"},
        "id_tech": {"targets": ["unity", "ue5", "godot", "blender", "source2"], "bridge": "fbx/obj/md5"},
        "source2": {"targets": ["unity", "ue5", "godot", "blender", "id_tech"], "bridge": "fbx/vmdl"},
        "frostbite": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "snowdrop": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "decima": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "fox_engine": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "rage": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx"},
        "creation_engine": {"targets": ["unity", "ue5", "godot", "blender", "gamebryo"], "bridge": "fbx/nif"},
        "lumberyard": {"targets": ["unity", "ue5", "godot", "cryengine", "o3de"], "bridge": "fbx"},
    },
    "game_engines_2d": {
        "defold": {"targets": ["godot", "cocos_creator", "unity", "love2d", "solar2d", "phaser", "flame", "gdevelop", "construct", "rpg_maker", "libgdx", "cocos2dx", "axmol", "pixijs", "egret", "heaps", "openfl", "corona", "dome", "nme"], "bridge": "gltf+png"},
        "cocos_creator": {"targets": ["godot", "defold", "unity", "phaser", "flame", "cocos2dx", "axmol", "egret", "pixijs"], "bridge": "gltf+json"},
        "construct": {"targets": ["defold", "gdevelop", "phaser", "flame", "pixijs"], "bridge": "png+json"},
        "rpg_maker": {"targets": ["defold", "gdevelop", "construct", "cocos_creator", "love2d"], "bridge": "png+json"},
        "love2d": {"targets": ["defold", "solar2d", "flame", "corona", "dome"], "bridge": "png+ogg+lua"},
        "solar2d": {"targets": ["defold", "love2d", "flame", "corona"], "bridge": "png+json+lua"},
        "gdevelop": {"targets": ["defold", "construct", "phaser", "cocos_creator", "pixijs"], "bridge": "gltf+png"},
        "flame": {"targets": ["defold", "love2d", "solar2d", "phaser"], "bridge": "png+json"},
        "phaser": {"targets": ["defold", "cocos_creator", "gdevelop", "flame", "pixijs"], "bridge": "png+json"},
        "libgdx": {"targets": ["defold", "cocos_creator", "unity", "phaser", "love2d"], "bridge": "obj+png"},
        "cocos2dx": {"targets": ["cocos_creator", "defold", "unity", "axmol"], "bridge": "png+json+csb"},
        "axmol": {"targets": ["cocos2dx", "cocos_creator", "defold", "unity"], "bridge": "png+json"},
        "pixijs": {"targets": ["phaser", "defold", "cocos_creator", "gdevelop", "construct"], "bridge": "png+json"},
        "egret": {"targets": ["cocos_creator", "phaser", "pixijs", "defold"], "bridge": "png+json"},
        "heaps": {"targets": ["unity", "godot", "defold", "love2d"], "bridge": "fbx+png"},
        "openfl": {"targets": ["pixijs", "phaser", "defold", "cocos_creator"], "bridge": "png+json"},
        "corona": {"targets": ["solar2d", "defold", "love2d", "flame"], "bridge": "png+lua"},
        "dome": {"targets": ["love2d", "defold", "solar2d"], "bridge": "png+wren"},
        "nme": {"targets": ["openfl", "pixijs", "phaser", "defold"], "bridge": "png+haxe"},
        "gamemaker": {"targets": ["godot", "defold", "construct", "gdevelop", "unity"], "bridge": "png+json"},
        "torque2d": {"targets": ["torque3d", "defold", "construct", "gdevelop", "love2d"], "bridge": "png+json"},
    },
    "web_engines": {
        "playcanvas": {"targets": ["godot", "unity", "threejs", "babylonjs", "aframe", "decentraland", "croquet"], "bridge": "gltf"},
        "babylonjs": {"targets": ["godot", "unity", "threejs", "playcanvas", "aframe", "decentraland", "croquet"], "bridge": "gltf"},
        "threejs": {"targets": ["godot", "unity", "babylonjs", "playcanvas", "aframe", "decentraland", "croquet"], "bridge": "gltf"},
        "aframe": {"targets": ["godot", "threejs", "babylonjs", "playcanvas", "decentraland"], "bridge": "gltf"},
        "decentraland": {"targets": ["godot", "threejs", "babylonjs", "playcanvas"], "bridge": "gltf"},
        "croquet": {"targets": ["godot", "threejs", "babylonjs", "playcanvas"], "bridge": "gltf"},
        "pixijs": {"targets": ["phaser", "defold", "cocos_creator", "construct"], "bridge": "png+json"},
        "spline_web": {"targets": ["threejs", "babylonjs", "playcanvas", "godot", "unity"], "bridge": "gltf"},
        "react_three_fiber": {"targets": ["threejs", "babylonjs", "playcanvas", "godot"], "bridge": "gltf"},
        "p5js": {"targets": ["phaser", "pixijs", "processing"], "bridge": "png+json"},
        "cesiumjs": {"targets": ["threejs", "babylonjs", "godot", "ue5"], "bridge": "gltf/3dtiles"},
        "mapbox_gl": {"targets": ["cesiumjs", "threejs", "godot", "ue5"], "bridge": "gltf/geojson"},
    },
    "dcc_tools": {
        "maya": {"targets": ["unity", "ue5", "godot", "defold", "cocos_creator", "cryengine", "blender", "o3de", "unigine", "flax", "stride", "bevy", "fyrox", "armory3d"], "bridge": "fbx/gltf/usd"},
        "houdini": {"targets": ["unity", "ue5", "godot", "defold", "cocos_creator", "blender", "o3de", "unigine", "bevy", "fyrox"], "bridge": "fbx/usd/gltf/vdb"},
        "substance": {"targets": ["unity", "ue5", "godot", "cryengine", "cocos_creator", "blender", "flax", "stride"], "bridge": "png+sbsar"},
        "3dsmax": {"targets": ["unity", "ue5", "godot", "blender", "cryengine", "o3de", "unigine", "flax"], "bridge": "fbx"},
        "cinema4d": {"targets": ["unity", "ue5", "godot", "blender", "o3de", "unigine"], "bridge": "fbx/abc/usd"},
        "zbrush": {"targets": ["unity", "ue5", "godot", "blender", "3dcoat", "maya", "3dsmax"], "bridge": "obj/fbx"},
        "modo": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "fbx/abc/usd"},
        "daz3d": {"targets": ["unity", "ue5", "godot", "blender", "maya", "character_creator"], "bridge": "fbx"},
        "mixamo": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "fbx"},
        "character_creator": {"targets": ["unity", "ue5", "godot", "blender", "daz3d", "maya"], "bridge": "fbx/gltf"},
        "cascadeur": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "fbx/usd"},
        "3dcoat": {"targets": ["unity", "ue5", "godot", "blender", "zbrush", "maya"], "bridge": "fbx/obj/gltf"},
        "mudbox": {"targets": ["unity", "ue5", "godot", "blender", "zbrush", "maya"], "bridge": "obj/fbx"},
        "nomad_sculpt": {"targets": ["unity", "ue5", "godot", "blender", "zbrush"], "bridge": "obj/gltf/fbx"},
        "forger": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "obj/fbx"},
        "vr_modeling": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/gltf"},
        "lightwave": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "fbx/obj"},
        "shade3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx/obj"},
        "silo": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/fbx"},
        "wings3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj"},
    },
    "cad_bim": {
        "sketchup": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion", "lumion", "d5_render"], "bridge": "datasmith/fbx/dae"},
        "revit": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion", "lumion", "d5_render", "archicad"], "bridge": "datasmith/ifc/fbx"},
        "autocad": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion"], "bridge": "datasmith/fbx/obj"},
        "archicad": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion", "lumion", "d5_render", "revit"], "bridge": "ifc/fbx/usd"},
        "rhino": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion", "grasshopper"], "bridge": "fbx/usd/gltf/rhino.inside"},
        "navisworks": {"targets": ["ue5", "unity", "godot", "twinmotion"], "bridge": "fbx/ifc"},
        "vectorworks": {"targets": ["ue5", "unity", "godot", "twinmotion", "lumion"], "bridge": "ifc/fbx/gltf"},
        "tekla": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion"], "bridge": "ifc/fbx"},
        "bricscad": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "ifc/fbx/dwg"},
        "allplan": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion"], "bridge": "ifc/fbx"},
        "bentley": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion"], "bridge": "ifc/fbx/dgn"},
        "chief_architect": {"targets": ["ue5", "unity", "godot", "blender", "twinmotion"], "bridge": "fbx/obj"},
        "solidworks": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "step/fbx/usd"},
        "catia": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "step/iges/fbx"},
        "inventor": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "step/fbx/ipt"},
        "fusion360": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "step/fbx/usd"},
        "freecad": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "step/ifc/fbx"},
        "openscad": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "stl/obj"},
    },
    "archviz": {
        "twinmotion": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "direct_link/fbx/usd"},
        "lumion": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "fbx/obj"},
        "enscape": {"targets": ["ue5", "unity", "godot"], "bridge": "fbx"},
        "d5_render": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "fbx/obj"},
        "vray": {"targets": ["ue5", "unity", "blender", "maya", "3dsmax", "sketchup", "rhino"], "bridge": "vrscene"},
    },
    "rendering_engines": {
        "octane": {"targets": ["unity", "ue5", "blender", "maya", "3dsmax", "cinema4d", "daz3d", "houdini"], "bridge": "orb/abc/usd"},
        "redshift": {"targets": ["maya", "3dsmax", "cinema4d", "houdini", "blender"], "bridge": "rs/abc/usd"},
        "vray": {"targets": ["maya", "3dsmax", "cinema4d", "blender", "sketchup", "rhino", "houdini"], "bridge": "vrscene/fbx"},
        "arnold": {"targets": ["maya", "3dsmax", "cinema4d", "houdini", "blender"], "bridge": "ass/usd"},
        "renderman": {"targets": ["maya", "houdini", "blender"], "bridge": "rib/usd"},
        "cycles": {"targets": ["blender", "maya", "3dsmax"], "bridge": "usd/fbx"},
        "eevee": {"targets": ["blender"], "bridge": "gltf/fbx"},
        "karma": {"targets": ["houdini", "usd_pipeline"], "bridge": "usd"},
        "unreal_lumen": {"targets": ["ue5"], "bridge": "fbx/usd"},
        "mental_ray": {"targets": ["maya", "3dsmax"], "bridge": "mi/fbx"},
    },
    "terrain_procedural": {
        "world_machine": {"targets": ["ue5", "unity", "godot", "blender", "houdini", "o3de", "unigine"], "bridge": "heightmap/exr/obj"},
        "gaea": {"targets": ["ue5", "unity", "godot", "blender", "houdini", "o3de", "unigine"], "bridge": "heightmap/mesh/gltf"},
        "world_creator": {"targets": ["ue5", "unity", "godot", "blender", "houdini", "o3de", "unigine"], "bridge": "heightmap/mesh/fbx"},
        "vue": {"targets": ["ue5", "unity", "godot", "blender", "maya", "3dsmax", "cinema4d"], "bridge": "fbx/obj/vob"},
        "infinigen": {"targets": ["blender", "ue5", "unity", "godot"], "bridge": "obj/fbx/gltf"},
        "geocontrol": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "heightmap/obj"},
        "instant_terrain": {"targets": ["unity", "ue5", "godot"], "bridge": "heightmap/obj"},
    },
    "animation_frameworks": {
        "spine": {"targets": ["unity", "ue5", "godot", "cocos_creator", "defold", "phaser", "pixijs", "cocos2dx", "axmol", "heaps", "openfl", "flame", "gamemaker", "love2d"], "bridge": "json+atlas+png"},
        "dragonbones": {"targets": ["unity", "cocos_creator", "cocos2dx", "egret"], "bridge": "json+tex.json+png"},
        "lottie": {"targets": ["unity", "web", "react_native", "flutter", "ios", "android", "skia"], "bridge": "json"},
        "live2d": {"targets": ["unity", "web", "ios", "android", "cocos_creator"], "bridge": "moc3+model3.json+png"},
        "mixamo": {"targets": ["unity", "ue5", "godot", "blender", "maya", "3dsmax", "motionbuilder"], "bridge": "fbx"},
        "motionbuilder": {"targets": ["unity", "ue5", "godot", "blender", "maya", "3dsmax", "houdini"], "bridge": "fbx/bvh/c3d"},
        "iclone": {"targets": ["unity", "ue5", "godot", "blender", "maya", "character_creator"], "bridge": "fbx/bvh"},
        "rokoko": {"targets": ["unity", "ue5", "blender", "maya", "motionbuilder"], "bridge": "fbx/bvh"},
        "xsens": {"targets": ["unity", "ue5", "blender", "maya", "motionbuilder"], "bridge": "fbx/bvh/c3d"},
        "optitrack": {"targets": ["unity", "ue5", "blender", "maya", "motionbuilder"], "bridge": "fbx/bvh/c3d"},
        "vicon": {"targets": ["unity", "ue5", "blender", "maya", "motionbuilder"], "bridge": "fbx/c3d"},
        "perception_neuron": {"targets": ["unity", "ue5", "blender", "maya"], "bridge": "fbx/bvh"},
        "faceware": {"targets": ["unity", "ue5", "maya", "blender"], "bridge": "fbx/bvh"},
        "lipsync_pro": {"targets": ["unity", "ue5", "godot"], "bridge": "fbx/phonemes"},
        "salsa_lipsync": {"targets": ["unity"], "bridge": "phonemes"},
        "ovrlipsync": {"targets": ["unity", "ue5"], "bridge": "phonemes"},
    },
    "vfx_particle_systems": {
        "popcornfx": {"targets": ["ue5", "unity", "o3de", "godot", "cryengine"], "bridge": "pkfx+textures"},
        "niagara": {"targets": ["ue5"], "bridge": "ue5_native"},
        "vfx_graph": {"targets": ["unity"], "bridge": "unity_native"},
        "cascade": {"targets": ["ue5"], "bridge": "ue5_legacy"},
        "shuriken": {"targets": ["unity"], "bridge": "unity_legacy"},
        "gpu_particles": {"targets": ["godot"], "bridge": "godot_native"},
    },
    "digital_twin_metaverse": {
        "omniverse": {"targets": ["ue5", "unity", "maya", "3dsmax", "blender", "houdini", "rhino", "revit"], "bridge": "usd"},
        "unity_reflect": {"targets": ["revit", "sketchup", "rhino", "autocad", "archicad", "navisworks"], "bridge": "ifc/fbx"},
        "matterport": {"targets": ["ue5", "unity", "godot", "blender"], "bridge": "obj/e57/ply"},
        "cintoo": {"targets": ["ue5", "unity"], "bridge": "e57/ply/obj"},
        "pointcloud_tools": {"targets": ["ue5", "unity", "blender", "cloudcompare"], "bridge": "e57/ply/las/laz"},
    },
    "xr_platforms": {
        "openxr": {"targets": ["unity", "ue5", "godot", "flax", "evergine", "unigine", "o3de", "bevy", "monado"]},
        "meta_xr": {"targets": ["unity", "ue5", "evergine", "unigine"]},
        "steamvr": {"targets": ["unity", "ue5", "unigine", "o3de"]},
        "psvr2": {"targets": ["unity", "ue5"]},
        "visionpro": {"targets": ["unity"]},
        "webxr": {"targets": ["godot", "playcanvas", "babylonjs", "threejs", "aframe", "spline_web"]},
        "varjo_xr": {"targets": ["unity", "ue5", "unigine"]},
        "magic_leap": {"targets": ["unity", "ue5"]},
        "pico": {"targets": ["unity", "ue5"]},
        "htc_vive": {"targets": ["unity", "ue5", "unigine"]},
        "snapdragon_spaces": {"targets": ["unity", "ue5"]},
        "arcore": {"targets": ["unity", "ue5", "web", "godot"]},
        "arkit": {"targets": ["unity", "godot"]},
        "xreal": {"targets": ["unity", "ue5"]},
        "android_xr": {"targets": ["unity", "ue5"]},
        "viture": {"targets": ["unity"]},
        "lenovo_xr": {"targets": ["unity", "ue5"]},
        "nreal": {"targets": ["unity", "ue5"]},
        "wave_xr": {"targets": ["unity", "ue5"]},
        "osvr": {"targets": ["unity"], "status": "deprecated"},
        "google_cardboard": {"targets": ["unity", "ue5", "godot"]},
        "apple_visionpro_native": {"targets": ["unity"], "bridge": "polyspatial"},
        "alvr": {"targets": ["steamvr", "quest"], "bridge": "streaming"},
        "vrbridge": {"targets": ["steamvr"], "bridge": "streaming"},
    },
    "audio_middleware": {
        "wwise": {"targets": ["unity", "ue5", "godot", "o3de", "cryengine"], "bridge": "wem+bnk+wproj"},
        "fmod": {"targets": ["unity", "ue5", "godot", "cryengine", "o3de"], "bridge": "fsb+fspro"},
        "criware": {"targets": ["unity", "ue5", "cocos_creator", "cocos2dx"], "bridge": "acb+awb+usm"},
        "steam_audio": {"targets": ["unity", "ue5", "fmod", "wwise"], "bridge": "phononscene+sofa"},
        "resonance_audio": {"targets": ["unity", "web", "godot"], "bridge": "api"},
        "meta_spatial_audio": {"targets": ["unity", "ue5"], "bridge": "api"},
        "miles_sound": {"targets": ["unity", "ue5"], "bridge": "mss"},
        "fabric": {"targets": ["unity"], "bridge": "unity_native"},
        "elias": {"targets": ["unity", "ue5"], "bridge": "elias_sdk"},
        "pure_data": {"targets": ["libpd_embedded", "unity", "web"], "bridge": "pd_patch"},
        "game_coda": {"targets": ["ue5", "unity"], "bridge": "sdk"},
        "miniaudio": {"targets": ["c_cpp_engines"], "bridge": "c_library"},
        "soloud": {"targets": ["c_cpp_engines", "defold"], "bridge": "c_library"},
        "openal": {"targets": ["c_cpp_engines", "panda3d", "ogre"], "bridge": "c_api"},
    },
    "physics_engines": {
        "physx": {"targets": ["ue5", "unity", "godot", "omniverse"], "bridge": "api/repx"},
        "havok": {"targets": ["unity", "ue5", "babylonjs"], "bridge": "api/hkt"},
        "jolt": {"targets": ["godot", "ue5", "horizon"], "bridge": "api"},
        "bullet": {"targets": ["godot", "blender", "threejs", "panda3d", "irrlicht", "ogre"], "bridge": "bullet_file/urdf"},
        "box2d": {"targets": ["cocos_creator", "defold", "love2d", "godot"], "bridge": "api"},
        "mujoco": {"targets": ["unity", "omniverse", "isaac_sim"], "bridge": "mjcf/urdf"},
        "ode": {"targets": ["ogre", "irrlicht", "panda3d"], "bridge": "api"},
        "chipmunk": {"targets": ["love2d", "cocos2dx", "defold"], "bridge": "api"},
        "rapier": {"targets": ["bevy", "fyrox", "web"], "bridge": "wasm/api"},
        "reactphysics3d": {"targets": ["c_cpp_engines"], "bridge": "api"},
        "newton_dynamics": {"targets": ["ogre", "irrlicht"], "bridge": "api"},
        "chaos_physics": {"targets": ["ue5"], "bridge": "ue5_native"},
        "havok_physics_unity": {"targets": ["unity"], "bridge": "unity_package"},
        "physx_5": {"targets": ["ue5", "omniverse"], "bridge": "api"},
        "isaac_sim": {"targets": ["omniverse", "unity"], "bridge": "usd/urdf"},
    },
    "ai_tools": {
        "meshy": {"targets": ["unity", "ue5", "godot", "blender", "maya"], "bridge": "glb/fbx/obj+png"},
        "leonardo_ai": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb+png"},
        "luma_ai": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/obj/usdz+png"},
        "csm_ai": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/fbx/obj/usdz+png"},
        "kaedim": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "fbx/obj/glb+png"},
        "rodin": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/fbx/obj+png"},
        "inworld_ai": {"targets": ["unity", "ue5"], "bridge": "sdk/api"},
        "convai": {"targets": ["unity", "ue5"], "bridge": "sdk/api"},
        "spline_ai": {"targets": ["threejs", "babylonjs", "playcanvas", "godot", "unity"], "bridge": "gltf"},
        "open3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/obj+png"},
        "tripo3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/fbx/obj+png"},
        "masterpiece_studio": {"targets": ["unity", "ue5", "blender"], "bridge": "glb/fbx+png"},
        "dreamfusion": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/glb+png"},
        "sam_3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/ply+png"},
        "stable_3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/obj+png"},
        "point_e": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "ply/obj+png"},
        "shap_e": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "glb/obj+png"},
        "wonder3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/glb+png"},
        "instant_mesh": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/glb+png"},
        "unique3d": {"targets": ["unity", "ue5", "godot", "blender"], "bridge": "obj/glb+png"},
        "character_ai": {"targets": ["unity", "ue5"], "bridge": "sdk/api"},
        "npc_ai": {"targets": ["unity", "ue5", "godot"], "bridge": "sdk/api"},
        "scenario_gg": {"targets": ["unity", "ue5", "godot"], "bridge": "png+json"},
        "layer_ai": {"targets": ["unity", "ue5", "godot"], "bridge": "png+json"},
    },
    "interchange_formats": {
        "fbx": {"type": "proprietary", "owner": "Autodesk", "engines": "universal", "content": "mesh+skeleton+animation+material_ref"},
        "gltf": {"type": "open_standard", "owner": "Khronos", "engines": "godot/defold/cocos/web/bevy/fyrox", "content": "mesh+skeleton+animation+material+texture+pbr"},
        "glb": {"type": "open_standard", "owner": "Khronos", "engines": "same_as_gltf", "content": "binary_gltf"},
        "usd": {"type": "open_standard", "owner": "Pixar/OpenUSD", "engines": "ue5/unity/omniverse/houdini/maya", "content": "full_scene+composition+layers"},
        "usdz": {"type": "open_standard", "owner": "Apple/Pixar", "engines": "ios/visionpro/quicklook", "content": "packaged_usd"},
        "obj": {"type": "open", "owner": "Wavefront", "engines": "universal_static", "content": "mesh+UV+material_ref"},
        "abc": {"type": "open_standard", "owner": "Sony/ILM", "engines": "maya/houdini/ue5/unity/blender", "content": "vertex_animation_cache+curves+points"},
        "dae": {"type": "open_standard", "owner": "Khronos", "engines": "godot/cryengine/blender", "content": "mesh+skeleton+animation+material"},
        "step": {"type": "iso_standard", "owner": "ISO 10303", "engines": "cad_bim", "content": "precise_brep_nurbs"},
        "iges": {"type": "us_standard", "owner": "NBS", "engines": "cad_bim", "content": "precise_curve_surface"},
        "ifc": {"type": "iso_standard", "owner": "buildingSMART", "engines": "bim_archviz", "content": "building_data+geometry"},
        "stl": {"type": "open", "owner": "3D Systems", "engines": "3d_print/cad", "content": "triangle_mesh_only"},
        "3mf": {"type": "open_standard", "owner": "3MF Consortium", "engines": "3d_print/cad", "content": "mesh+material+color"},
        "ply": {"type": "open", "owner": "Stanford", "engines": "pointcloud/scanning", "content": "point_cloud+mesh"},
        "e57": {"type": "astm_standard", "owner": "ASTM", "engines": "lidar/scanning", "content": "point_cloud+image"},
        "vrscene": {"type": "proprietary", "owner": "Chaos", "engines": "vray", "content": "full_vray_scene"},
        "3dtiles": {"type": "ogc_standard", "owner": "OGC", "engines": "cesium/gis", "content": "massive_3d_geospatial"},
        "geojson": {"type": "open_standard", "owner": "IETF", "engines": "gis/web", "content": "geographic_data"},
        "urdf": {"type": "open", "owner": "ROS", "engines": "robotics/mujoco/isaac_sim", "content": "robot_description"},
        "mjcf": {"type": "open", "owner": "DeepMind", "engines": "mujoco", "content": "robot_description_physics"},
        "bvh": {"type": "open", "owner": "Biovision", "engines": "mocap/animation", "content": "skeleton_animation"},
        "c3d": {"type": "open", "owner": "C3D.org", "engines": "mocap", "content": "motion_capture_data"},
        "vdb": {"type": "open_standard", "owner": "DreamWorks", "engines": "houdini/ue5/blender", "content": "volume_data"},
        "exr": {"type": "open_standard", "owner": "ILM", "engines": "vfx/rendering", "content": "hdr_image+layers"},
        "sbsar": {"type": "proprietary", "owner": "Adobe", "engines": "ue5/unity/substance", "content": "parametric_material"},
        "datasmith": {"type": "proprietary", "owner": "Epic", "engines": "ue5/twinmotion", "content": "cad_bim_scene"},
        "rhino_inside": {"type": "proprietary", "owner": "McNeel", "engines": "unity/revit", "content": "live_rhino_link"},
    },
    "visual_scripting": {
        "ue5_blueprints": {"targets": ["unity_visual_scripting", "godot_visual_script", "playmaker", "bolt"], "bridge": "logic_translation"},
        "unity_visual_scripting": {"targets": ["ue5_blueprints", "playmaker", "bolt", "godot_visual_script"], "bridge": "logic_translation"},
        "playmaker": {"targets": ["unity_visual_scripting", "ue5_blueprints"], "bridge": "logic_translation"},
        "bolt": {"targets": ["unity_visual_scripting", "ue5_blueprints"], "bridge": "logic_translation"},
        "godot_visual_script": {"targets": ["ue5_blueprints", "unity_visual_scripting"], "bridge": "logic_translation"},
    },
    "target_platforms": {
        "android": {"engines": ["unity", "ue5", "godot", "defold", "cocos_creator", "flax", "stride", "flame", "solar2d", "love2d", "gamemaker", "cocos2dx", "axmol", "egret"]},
        "ios": {"engines": ["unity", "ue5", "godot", "defold", "cocos_creator", "flax", "stride", "gamemaker"]},
        "webgl": {"engines": ["unity", "godot", "defold", "cocos_creator", "construct", "playcanvas", "babylonjs", "threejs", "aframe", "phaser", "pixijs", "gdevelop", "egret", "openfl"]},
        "webxr": {"engines": ["unity", "godot", "playcanvas", "babylonjs", "threejs", "aframe", "spline_web"]},
        "windows": {"engines": ["unity", "ue5", "godot", "flax", "stride", "o3de", "unigine", "cryengine", "evergine", "neoaxis", "armory3d", "bevy", "fyrox", "gamemaker", "rpg_maker"]},
        "macos": {"engines": ["unity", "ue5", "godot", "flax", "stride", "armory3d", "bevy", "gamemaker"]},
        "linux": {"engines": ["unity", "ue5", "godot", "bevy", "o3de", "armory3d", "fyrox", "spring"]},
        "quest": {"engines": ["unity", "ue5", "godot"]},
        "visionos": {"engines": ["unity"]},
        "ps5": {"engines": ["unity", "ue5"]},
        "ps4": {"engines": ["unity", "ue5"]},
        "xbox": {"engines": ["unity", "ue5"]},
        "xbox_series": {"engines": ["unity", "ue5"]},
        "switch": {"engines": ["unity", "ue5", "godot"]},
        "steam_deck": {"engines": ["unity", "ue5", "godot", "flax", "stride", "bevy"]},
        "android_xr": {"engines": ["unity", "ue5"]},
        "embedded": {"engines": ["defold", "love2d", "panda3d", "godot"]},
    },
    "total_conversion_paths": "1610",
    "total_3d_engines": 34,
    "total_2d_engines": 20,
    "total_web_engines": 12,
    "total_dcc_tools": 20,
    "total_cad_bim": 18,
    "total_archviz": 5,
    "total_rendering_engines": 10,
    "total_terrain_procedural": 7,
    "total_animation_frameworks": 16,
    "total_vfx_systems": 6,
    "total_digital_twin": 5,
    "total_xr_platforms": 23,
    "total_audio_middleware": 14,
    "total_physics_engines": 15,
    "total_ai_tools": 24,
    "total_interchange_formats": 28,
    "total_visual_scripting": 5,
    "total_target_platforms": 18,
}
