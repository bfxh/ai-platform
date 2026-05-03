#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
引擎资产转换器 - 全矩阵版 (4引擎 x 4引擎)

支持转换路径 (12条):
  UE      → Godot, Unity, Blender
  Unity   → Godot, UE5, Blender
  Godot   → UE5, Unity, Blender
  Blender → Godot, UE5, Unity

引擎原生插件:
  Godot:  engine_converter_plugins/godot_importer/addons/engine_importer/
  UE5:    engine_converter_plugins/ue5_plugin/EngineImporter/
  Unity:  engine_converter_plugins/unity_editor/Editor/EngineImporter/
  Blender: engine_converter_plugins/blender_addon/engine_converter.py

用法:
    python engine_converter.py convert_ue_to_godot <source> <godot_project> [scene_name]
    python engine_converter.py convert_unity_to_godot <unity_project> <godot_project>
    python engine_converter.py convert_unity_to_ue5 <unity_project> <ue_project>
    python engine_converter.py analyze <project_path>
    python engine_converter.py mcp

依赖:
    - 本地工具: godot_scene_assembler.py, blender_mcp.py, ue_import.py
    - Python: pyyaml (Unity YAML 解析)
    - 外部: Blender (格式转换中转)
    - 扩展: engine_converter_extended.py (VR/XR/多引擎/DCC/CAD/2D动画)
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

MCP_PATH = Path("/python/storage/mcp/JM")
BLENDER_EXE = os.getenv("BLENDER_EXECUTABLE", "D:/rj/KF/JM/blender/blender.exe")
GODOT_EXE = os.getenv("GODOT_EXECUTABLE", "%DEVTOOLS_DIR%/Godot/Godot_v4.exe")
UE_EDITOR = os.getenv("UE_EDITOR", "D:/rj/KF/JM/UE_5.6/Engine/Binaries/Win64/UnrealEditor.exe")

UNITY_COMPONENT_MAP = {
    "Transform": {"godot": "Node3D", "ue": "SceneComponent"},
    "RectTransform": {"godot": "Control", "ue": "UWidget"},
    "MeshRenderer": {"godot": "MeshInstance3D", "ue": "StaticMeshComponent"},
    "SkinnedMeshRenderer": {"godot": "MeshInstance3D", "ue": "SkeletalMeshComponent"},
    "MeshFilter": {"godot": "MeshInstance3D", "ue": "StaticMeshComponent"},
    "Camera": {"godot": "Camera3D", "ue": "CameraComponent"},
    "Light": {"godot": "Light3D", "ue": "LightComponent"},
    "DirectionalLight": {"godot": "DirectionalLight3D", "ue": "DirectionalLightComponent"},
    "PointLight": {"godot": "OmniLight3D", "ue": "PointLightComponent"},
    "SpotLight": {"godot": "SpotLight3D", "ue": "SpotLightComponent"},
    "Rigidbody": {"godot": "RigidBody3D", "ue": "StaticMeshComponent"},
    "Rigidbody2D": {"godot": "RigidBody2D", "ue": "StaticMeshComponent"},
    "BoxCollider": {"godot": "CollisionShape3D", "ue": "BoxCollision"},
    "SphereCollider": {"godot": "CollisionShape3D", "ue": "SphereCollision"},
    "CapsuleCollider": {"godot": "CollisionShape3D", "ue": "CapsuleCollision"},
    "MeshCollider": {"godot": "CollisionShape3D", "ue": "StaticMeshComponent"},
    "CharacterController": {"godot": "CharacterBody3D", "ue": "CharacterMovementComponent"},
    "Animator": {"godot": "AnimationPlayer", "ue": "AnimMontage"},
    "AudioSource": {"godot": "AudioStreamPlayer3D", "ue": "AudioComponent"},
    "AudioListener": {"godot": "AudioListener3D", "ue": "AudioComponent"},
    "ParticleSystem": {"godot": "GPUParticles3D", "ue": "NiagaraComponent"},
    "Canvas": {"godot": "CanvasLayer", "ue": "UWidget"},
    "Text": {"godot": "Label", "ue": "UTextBlock"},
    "Image": {"godot": "TextureRect", "ue": "UImage"},
    "Button": {"godot": "Button", "ue": "UButton"},
    "ScrollRect": {"godot": "ScrollContainer", "ue": "UScrollBox"},
    "Toggle": {"godot": "CheckBox", "ue": "UCheckBox"},
    "Slider": {"godot": "HSlider", "ue": "USlider"},
    "InputField": {"godot": "LineEdit", "ue": "UEditableTextBox"},
    "Dropdown": {"godot": "OptionButton", "ue": "UComboBox"},
    "NavMeshAgent": {"godot": "NavigationAgent3D", "ue": "NavMovementComponent"},
    "Terrain": {"godot": "Terrain3D", "ue": "Landscape"},
    "SpriteRenderer": {"godot": "Sprite2D", "ue": "StaticMeshComponent"},
    "CanvasRenderer": {"godot": "CanvasItem", "ue": "UWidget"},
}

UNITY_SHADER_MAP = {
    "Standard": "SpatialMaterial",
    "Standard (Specular setup)": "SpatialMaterial",
    "Unlit/Color": "UnshadedMaterial",
    "Unlit/Texture": "UnshadedMaterial",
    "Unlit/Transparent": "SpatialMaterial",
    "Particles/Standard Unlit": "ParticleProcessMaterial",
    "Mobile/Diffuse": "SpatialMaterial",
    "Mobile/Specular": "SpatialMaterial",
    "UI/Default": "CanvasItemMaterial",
}

UNITY_TEX_PROP_MAP = {
    "_MainTex": "albedo_texture",
    "_BumpMap": "normal_texture",
    "_MetallicGlossMap": "metallic_texture",
    "_SpecGlossMap": "roughness_texture",
    "_ParallaxMap": "heightmap_texture",
    "_OcclusionMap": "ao_texture",
    "_EmissionMap": "emission_texture",
    "_DetailMask": "detail_mask_texture",
    "_DetailAlbedoMap": "detail_albedo_texture",
    "_DetailNormalMap": "detail_normal_texture",
}

UNITY_FLOAT_PROP_MAP = {
    "_Metallic": "metallic",
    "_Glossiness": "roughness",
    "_GlossMapScale": "roughness",
    "_BumpScale": "normal_scale",
    "_Parallax": "height_scale",
    "_OcclusionStrength": "ao_strength",
    "_Cutoff": "alpha_scissor_threshold",
    "_DetailNormalMapScale": "detail_normal_scale",
}

UNITY_COLOR_PROP_MAP = {
    "_Color": "albedo_color",
    "_EmissionColor": "emission_energy",
    "_SpecColor": "specular_color",
}


def generate_uid(path_str: str) -> str:
    h = hashlib.sha256(path_str.encode()).digest()
    uid_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    return "uid://" + "".join(uid_chars[b % 62] for b in h[:21])


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write(path: Path, content: str) -> Path:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def parse_unity_yaml(file_path: Path) -> Optional[Dict]:
    if yaml is None:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            documents = []
            current_doc = []
            for line in lines:
                if line.strip() == "---":
                    if current_doc:
                        documents.append("".join(current_doc))
                    current_doc = []
                else:
                    current_doc.append(line)
            if current_doc:
                documents.append("".join(current_doc))
            parsed = []
            for doc_str in documents:
                try:
                    import re
                    fixed = re.sub(r'^  m_', '  m_', doc_str, flags=re.MULTILINE)
                    obj = yaml.safe_load(fixed)
                    if obj:
                        parsed.append(obj)
                except Exception:
                    pass
            return {"documents": parsed, "raw_path": str(file_path)}
        except Exception as e:
            return {"error": str(e), "raw_path": str(file_path)}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        documents = []
        current_doc = []
        for line in content.split("\n"):
            if line.strip() == "---":
                if current_doc:
                    documents.append("\n".join(current_doc))
                current_doc = []
            else:
                current_doc.append(line)
        if current_doc:
            documents.append("\n".join(current_doc))
        parsed = []
        for doc_str in documents:
            try:
                obj = yaml.safe_load(doc_str)
                if obj:
                    parsed.append(obj)
            except Exception:
                pass
        return {"documents": parsed, "raw_path": str(file_path)}
    except Exception as e:
        return {"error": str(e), "raw_path": str(file_path)}


def parse_unity_yaml_raw(file_path: Path) -> List[Dict]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        documents = []
        current_lines = []
        for line in content.split("\n"):
            if line.strip() == "---":
                if current_lines:
                    documents.append("\n".join(current_lines))
                current_lines = []
            else:
                current_lines.append(line)
        if current_lines:
            documents.append("\n".join(current_lines))
        results = []
        for doc_str in documents:
            try:
                obj = yaml.safe_load(doc_str) if yaml else None
                if obj:
                    results.append(obj)
            except Exception:
                pass
        return results
    except Exception:
        return []


class UnitySceneParser:
    def __init__(self, scene_path: Path):
        self.scene_path = scene_path
        self.game_objects = []
        self.transforms = []
        self.components = []
        self.mesh_renderers = []
        self.cameras = []
        self.lights = []
        self.materials = {}

    def parse(self) -> Dict[str, Any]:
        docs = parse_unity_yaml_raw(self.scene_path)
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            doc_type = doc.get("m_Type", "")
            if "GameObject" in str(doc.get("m_Name", "")) or "m_Component" in doc:
                self._parse_game_object(doc)
            elif "m_LocalPosition" in doc:
                self._parse_transform(doc)
            elif "m_Materials" in doc and "m_Shader" in doc:
                self._parse_material(doc)
        return {
            "game_objects": self.game_objects,
            "transforms": self.transforms,
            "components": self.components,
            "mesh_renderers": self.mesh_renderers,
            "cameras": self.cameras,
            "lights": self.lights,
            "materials": self.materials,
            "total_objects": len(self.game_objects),
        }

    def _parse_game_object(self, doc: Dict):
        name = doc.get("m_Name", "Unnamed")
        is_active = doc.get("m_IsActive", 1)
        components = doc.get("m_Component", [])
        comp_refs = []
        for comp in components:
            if isinstance(comp, dict):
                comp_refs.append(comp.get("component", {}))
        self.game_objects.append({
            "name": name,
            "active": bool(is_active),
            "components": comp_refs,
        })

    def _parse_transform(self, doc: Dict):
        pos = doc.get("m_LocalPosition", {})
        rot = doc.get("m_LocalRotation", {})
        scale = doc.get("m_LocalScale", {})
        self.transforms.append({
            "position": {"x": pos.get("x", 0), "y": pos.get("y", 0), "z": pos.get("z", 0)},
            "rotation": {"x": rot.get("x", 0), "y": rot.get("y", 0), "z": rot.get("z", 0), "w": rot.get("w", 1)},
            "scale": {"x": scale.get("x", 1), "y": scale.get("y", 1), "z": scale.get("z", 1)},
        })

    def _parse_material(self, doc: Dict):
        shader = doc.get("m_Shader", {})
        shader_name = shader.get("m_Name", "Standard") if isinstance(shader, dict) else "Standard"
        textures = {}
        floats = {}
        colors = {}
        saved_props = doc.get("m_SavedProperties", {})
        if isinstance(saved_props, dict):
            tex_props = saved_props.get("m_TexEnvs", {})
            for key, val in tex_props.items():
                if isinstance(val, dict) and "m_Texture" in val:
                    textures[key] = val["m_Texture"]
            float_props = saved_props.get("m_Floats", {})
            for key, val in float_props.items():
                floats[key] = val
            color_props = saved_props.get("m_Colors", {})
            for key, val in color_props.items():
                colors[key] = val
        self.materials[shader_name] = {
            "shader": shader_name,
            "textures": textures,
            "floats": floats,
            "colors": colors,
        }


class GodotSceneBuilder:
    def __init__(self, scene_name: str, godot_project: Path):
        self.scene_name = scene_name
        self.godot_project = godot_project
        self.ext_resources = []
        self.sub_resources = []
        self.nodes = []
        self._res_id = 1
        self._node_id = 1

    def add_ext_resource(self, res_type: str, path: str, uid: str = None) -> int:
        res_id = self._res_id
        self._res_id += 1
        if uid is None:
            uid = generate_uid(path)
        self.ext_resources.append({
            "id": res_id,
            "type": res_type,
            "uid": uid,
            "path": path,
        })
        return res_id

    def add_sub_resource(self, res_type: str, props: Dict = None, uid: str = None) -> int:
        res_id = self._res_id
        self._res_id += 1
        if uid is None:
            uid = generate_uid(f"sub_{res_type}_{res_id}")
        self.sub_resources.append({
            "id": res_id,
            "type": res_type,
            "uid": uid,
            "props": props or {},
        })
        return res_id

    def add_node(self, name: str, node_type: str, parent: str = ".",
                 properties: Dict = None, children: List = None) -> int:
        node_id = self._node_id
        self._node_id += 1
        self.nodes.append({
            "id": node_id,
            "name": name,
            "type": node_type,
            "parent": parent,
            "properties": properties or {},
            "children": children or [],
        })
        return node_id

    def build(self) -> str:
        load_steps = 1 + len(self.ext_resources) + len(self.sub_resources)
        scene_uid = generate_uid(f"scene_{self.scene_name}")
        lines = [f'[gd_scene load_steps={load_steps} format=3 uid="{scene_uid}"]', ""]

        for res in self.ext_resources:
            lines.append(
                f'[ext_resource type="{res["type"]}" uid="{res["uid"]}" '
                f'path="{res["path"]}" id="{res["id"]}"]'
            )
        if self.ext_resources:
            lines.append("")

        for res in self.sub_resources:
            lines.append(f'[sub_resource type="{res["type"]}" id="{res["id"]}"]')
            for key, val in res["props"].items():
                if isinstance(val, str):
                    lines.append(f'{key} = "{val}"')
                elif isinstance(val, bool):
                    lines.append(f'{key} = {"true" if val else "false"}')
                elif isinstance(val, (int, float)):
                    lines.append(f'{key} = {val}')
                elif isinstance(val, dict):
                    lines.append(f'{key} = {json.dumps(val)}')
            lines.append("")

        root_props = {}
        for node in self.nodes:
            if node["parent"] == ".":
                root_props = node["properties"]
                break

        root_node = next((n for n in self.nodes if n["parent"] == "."), None)
        if root_node:
            lines.append(f'[node name="{root_node["name"]}" type="{root_node["type"]}"]')
            for key, val in root_node["properties"].items():
                lines.append(f'{key} = {self._format_prop(val)}')

        for node in self.nodes:
            if node["parent"] == ".":
                continue
            lines.append("")
            lines.append(
                f'[node name="{node["name"]}" type="{node["type"]}" '
                f'parent="{node["parent"]}"]'
            )
            for key, val in node["properties"].items():
                lines.append(f'{key} = {self._format_prop(val)}')

        lines.append("")
        return "\n".join(lines)

    def _format_prop(self, val) -> str:
        if isinstance(val, str):
            if val.startswith("ExtResource(") or val.startswith("SubResource("):
                return val
            return f'"{val}"'
        elif isinstance(val, bool):
            return "true" if val else "false"
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, dict):
            return json.dumps(val)
        return str(val)

    def save(self) -> Path:
        content = self.build()
        tscn_path = self.godot_project / f"{self.scene_name}.tscn"
        safe_write(tscn_path, content)
        return tscn_path


class GodotMaterialBuilder:
    def __init__(self, mat_name: str, godot_project: Path):
        self.mat_name = mat_name
        self.godot_project = godot_project
        self.properties = {}
        self.texture_maps = {}

    def set_from_unity_standard(self, unity_mat: Dict):
        shader_name = unity_mat.get("shader", "Standard")
        godot_shader = UNITY_SHADER_MAP.get(shader_name, "SpatialMaterial")
        self.properties["resource_name"] = self.mat_name
        self.properties["shader_mode"] = 1 if godot_shader == "SpatialMaterial" else 0

        for unity_prop, godot_prop in UNITY_COLOR_PROP_MAP.items():
            color = unity_mat.get("colors", {}).get(unity_prop)
            if color:
                if godot_prop == "albedo_color":
                    self.properties["albedo_color"] = (
                        color.get("r", 1), color.get("g", 1),
                        color.get("b", 1), color.get("a", 1)
                    )
                elif godot_prop == "emission_energy":
                    self.properties["emission_enabled"] = True
                    self.properties["emission_energy"] = max(
                        color.get("r", 0), color.get("g", 0), color.get("b", 0)
                    )

        for unity_prop, godot_prop in UNITY_FLOAT_PROP_MAP.items():
            val = unity_mat.get("floats", {}).get(unity_prop)
            if val is not None:
                if godot_prop == "roughness":
                    self.properties["roughness"] = 1.0 - val
                else:
                    self.properties[godot_prop] = val

        for unity_prop, godot_prop in UNITY_TEX_PROP_MAP.items():
            tex_info = unity_mat.get("textures", {}).get(unity_prop)
            if tex_info and isinstance(tex_info, dict):
                tex_path = tex_info.get("m_Texture", {})
                if tex_path and isinstance(tex_path, dict):
                    guid = tex_path.get("guid", "")
                    if guid:
                        self.texture_maps[godot_prop] = guid

    def build(self) -> str:
        uid = generate_uid(f"mat_{self.mat_name}")
        lines = [
            f'[gd_resource type="StandardMaterial3D" format=3 uid="{uid}"]',
            "",
            "[resource]",
        ]
        for key, val in self.properties.items():
            if key == "albedo_color" and isinstance(val, tuple):
                lines.append(f'albedo_color = Color({val[0]}, {val[1]}, {val[2]}, {val[3]})')
            elif isinstance(val, bool):
                lines.append(f'{key} = {"true" if val else "false"}')
            elif isinstance(val, (int, float)):
                lines.append(f'{key} = {val}')
            elif isinstance(val, str):
                lines.append(f'{key} = "{val}"')
        lines.append("")
        return "\n".join(lines)

    def save(self) -> Path:
        content = self.build()
        tres_path = self.godot_project / "materials" / f"{self.mat_name}.tres"
        safe_write(tres_path, content)
        return tres_path


class GodotProjectInitializer:
    def __init__(self, project_path: Path, project_name: str = "ConvertedProject"):
        self.project_path = project_path
        self.project_name = project_name

    def init_project(self) -> Dict[str, Any]:
        ensure_dir(self.project_path)
        ensure_dir(self.project_path / "assets")
        ensure_dir(self.project_path / "scenes")
        ensure_dir(self.project_path / "scripts")
        ensure_dir(self.project_path / "materials")
        ensure_dir(self.project_path / "textures")
        ensure_dir(self.project_path / "models")
        ensure_dir(self.project_path / "audio")
        ensure_dir(self.project_path / ".godot")

        project_godot = self.project_path / "project.godot"
        if not project_godot.exists():
            content = f"""; Engine configuration file.
config_version=5

[application]
config/name="{self.project_name}"
run/main_scene="res://scenes/Main.tscn"
config/features=PackedStringArray("4.2")

[rendering]
renderer/rendering_method="forward_plus"
renderer/rendering_method.mobile="gl_compatibility"
"""
            safe_write(project_godot, content)

        godot_file = self.project_path / ".godot" / "project_metadata.cfg"
        if not godot_file.exists():
            safe_write(godot_file, '[application]\nconfig/macos_native_icon=""\nconfig/windows_native_icon=""\n')

        return {
            "success": True,
            "project_path": str(self.project_path),
            "project_name": self.project_name,
            "directories": ["assets", "scenes", "scripts", "materials", "textures", "models", "audio"],
        }


class UEToGodotConverter:
    def __init__(self, source_path: Path, godot_project: Path, scene_name: str = "MainScene"):
        self.source_path = source_path
        self.godot_project = godot_project
        self.scene_name = scene_name
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 UE → Godot 转换: {self.source_path}")

        init = GodotProjectInitializer(self.godot_project, self.scene_name)
        init.init_project()
        self._log_step("init_godot", "Godot 项目初始化完成")

        source_files = self._scan_source_files()
        self._log_step("scan", f"扫描到 {len(source_files)} 个源文件")

        mesh_files = [f for f in source_files if f.suffix.lower() in (".fbx", ".obj", ".gltf", ".glb")]
        texture_files = [f for f in source_files if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".hdr")]
        material_files = [f for f in source_files if f.suffix.lower() in (".mtl", ".mat")]

        copied_meshes = await self._copy_assets(mesh_files, "models")
        copied_textures = await self._copy_assets(texture_files, "textures")

        if copied_meshes:
            glb_files = [f for f in copied_meshes if f.suffix.lower() == ".glb"]
            fbx_files = [f for f in copied_meshes if f.suffix.lower() == ".fbx"]
            obj_files = [f for f in copied_meshes if f.suffix.lower() == ".obj"]
            gltf_files = [f for f in copied_meshes if f.suffix.lower() == ".gltf"]

            if glb_files:
                await self._assemble_glb_scenes(glb_files)
            if fbx_files or obj_files:
                converted = await self._convert_via_blender(fbx_files + obj_files)
                if converted:
                    await self._assemble_glb_scenes(converted)

        scene_builder = GodotSceneBuilder(self.scene_name, self.godot_project / "scenes")
        scene_builder.add_node(self.scene_name, "Node3D", ".", {})

        for mesh_file in copied_meshes:
            mesh_name = mesh_file.stem
            rel_path = f"res://models/{mesh_file.name}"
            mesh_uid = generate_uid(rel_path)
            res_id = scene_builder.add_ext_resource("ArrayMesh", rel_path, mesh_uid)
            scene_builder.add_node(mesh_name, "MeshInstance3D", self.scene_name, {
                "mesh": f"ExtResource(\"{res_id}\")",
            })

        scene_builder.add_node("Camera", "Camera3D", self.scene_name, {
            "transform": "Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 5, 10)",
            "current": True,
        })
        scene_builder.add_node("DirectionalLight", "DirectionalLight3D", self.scene_name, {
            "transform": "Transform3D(0.866, -0.433, 0.25, 0, 0.5, 0.866, -0.5, -0.75, 0.433, 0, 10, 0)",
            "shadow_enabled": True,
        })
        tscn_path = scene_builder.save()
        self._log_step("scene", f"Godot 场景已生成: {tscn_path}")

        self._log_step("complete", "UE → Godot 转换完成")
        return {
            "success": True,
            "source": str(self.source_path),
            "target": str(self.godot_project),
            "scene_file": str(tscn_path),
            "meshes_copied": len(copied_meshes),
            "textures_copied": len(copied_textures),
            "report": self.report,
        }

    def _scan_source_files(self) -> List[Path]:
        files = []
        if self.source_path.is_file():
            files.append(self.source_path)
        elif self.source_path.is_dir():
            for ext in ["*.fbx", "*.obj", "*.gltf", "*.glb", "*.png", "*.jpg", "*.jpeg",
                        "*.tga", "*.bmp", "*.hdr", "*.mtl", "*.mat", "*.uasset", "*.umap"]:
                files.extend(self.source_path.rglob(ext))
        return files

    async def _copy_assets(self, files: List[Path], subdir: str) -> List[Path]:
        dest_dir = self.godot_project / subdir
        ensure_dir(dest_dir)
        copied = []
        for src in files:
            try:
                dest = dest_dir / src.name
                shutil.copy2(str(src), str(dest))
                copied.append(dest)
            except Exception as e:
                self.report["warnings"].append(f"复制失败: {src.name} - {e}")
        return copied

    async def _assemble_glb_scenes(self, glb_files: List[Path]):
        assembler = MCP_PATH / "godot_scene_assembler.py"
        for glb in glb_files:
            scene_name = glb.stem
            try:
                if assembler.exists():
                    cmd = [
                        sys.executable, str(assembler),
                        str(glb), str(self.godot_project), scene_name,
                    ]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    await proc.communicate()
                    self._log_step("assemble", f"场景组装: {scene_name}")
                else:
                    self._manual_assemble_glb(glb, scene_name)
            except Exception as e:
                self.report["warnings"].append(f"场景组装失败: {scene_name} - {e}")

    def _manual_assemble_glb(self, glb_path: Path, scene_name: str):
        rel_path = f"res://models/{glb_path.name}"
        uid = generate_uid(rel_path)
        scene_uid = generate_uid(f"scene_{scene_name}")
        uid_short = scene_uid[9:]

        tscn_content = f"""[gd_scene load_steps=2 format=3 uid="{scene_uid}"]

[ext_resource type="PackedScene" uid="{uid}" path="{rel_path}" id="1_{uid_short}"]

[node name="{scene_name}" type="Node3D"]

[node name="ModelRoot" type="Node3D" parent="."]
"""
        tscn_path = self.godot_project / "scenes" / f"{scene_name}.tscn"
        safe_write(tscn_path, tscn_content)
        self._log_step("assemble_manual", f"手动场景组装: {scene_name}")

    async def _convert_via_blender(self, files: List[Path]) -> List[Path]:
        converted = []
        blender = Path(BLENDER_EXE)
        if not blender.exists():
            self.report["warnings"].append("Blender 未找到，跳过 FBX/OBJ → glTF 转换")
            return converted

        exports_dir = self.godot_project / "models"
        ensure_dir(exports_dir)

        for src in files:
            output_glb = exports_dir / f"{src.stem}.glb"
            script = f"""
import bpy
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
ext = "{src.suffix.lower()}"
if ext == ".fbx":
    try:
        bpy.ops.import_scene.fbx(filepath=r"{src}")
    except AttributeError:
        bpy.ops.wm.fbx_import(filepath=r"{src}")
elif ext == ".obj":
    try:
        bpy.ops.wm.obj_import(filepath=r"{src}")
    except AttributeError:
        bpy.ops.import_scene.obj(filepath=r"{src}")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.export_scene.gltf(filepath=r"{output_glb}", use_selection=True, export_format='GLB')
"""
            script_path = Path(f"/python/Temp/blender_convert_{src.stem}.py")
            safe_write(script_path, script)

            try:
                cmd = [str(blender), "--background", "--python", str(script_path)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0 and output_glb.exists():
                    converted.append(output_glb)
                    self._log_step("blender_convert", f"Blender 转换: {src.name} → {output_glb.name}")
                else:
                    self.report["warnings"].append(f"Blender 转换失败: {src.name}")
            except Exception as e:
                self.report["warnings"].append(f"Blender 执行错误: {e}")

        return converted

    def _log_step(self, step: str, message: str):
        self.report["steps"].append({
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })


class UnityToGodotConverter:
    def __init__(self, unity_project: Path, godot_project: Path):
        self.unity_project = unity_project
        self.godot_project = godot_project
        self.assets_dir = unity_project / "Assets"
        self.report = {"steps": [], "warnings": [], "errors": []}
        self.guid_map = {}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Unity → Godot 转换: {self.unity_project}")

        if not self.assets_dir.exists():
            return {"success": False, "error": f"Unity Assets 目录不存在: {self.assets_dir}"}

        init = GodotProjectInitializer(self.godot_project, self.unity_project.name)
        init.init_project()
        self._log_step("init_godot", "Godot 项目初始化完成")

        self._build_guid_map()
        self._log_step("guid_map", f"GUID 映射构建完成: {len(self.guid_map)} 条")

        scene_files = list(self.assets_dir.rglob("*.unity"))
        prefab_files = list(self.assets_dir.rglob("*.prefab"))
        material_files = list(self.assets_dir.rglob("*.mat"))
        script_files = list(self.assets_dir.rglob("*.cs"))
        texture_files = [f for f in self.assets_dir.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".tga", ".psd", ".bmp")]
        mesh_files = [f for f in self.assets_dir.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".gltf", ".glb")]

        self._log_step("scan", (
            f"扫描: {len(scene_files)} 场景, {len(prefab_files)} 预制体, "
            f"{len(material_files)} 材质, {len(script_files)} 脚本, "
            f"{len(texture_files)} 贴图, {len(mesh_files)} 网格"
        ))

        await self._copy_textures(texture_files)
        await self._copy_meshes(mesh_files)
        await self._convert_materials(material_files)
        await self._convert_scenes(scene_files)
        await self._convert_prefabs(prefab_files)
        await self._convert_scripts(script_files)

        self._log_step("complete", "Unity → Godot 转换完成")
        return {
            "success": True,
            "source": str(self.unity_project),
            "target": str(self.godot_project),
            "stats": {
                "scenes": len(scene_files),
                "prefabs": len(prefab_files),
                "materials": len(material_files),
                "scripts": len(script_files),
                "textures": len(texture_files),
                "meshes": len(mesh_files),
            },
            "report": self.report,
        }

    def _build_guid_map(self):
        for meta_file in self.assets_dir.rglob("*.meta"):
            try:
                content = meta_file.read_text(encoding="utf-8", errors="ignore")
                for line in content.split("\n"):
                    if line.startswith("guid:"):
                        guid = line.split(":", 1)[1].strip()
                        asset_path = str(meta_file.parent / meta_file.stem)
                        self.guid_map[guid] = asset_path
                        break
            except Exception:
                pass

    async def _copy_textures(self, files: List[Path]):
        dest_dir = self.godot_project / "textures"
        ensure_dir(dest_dir)
        count = 0
        for src in files:
            try:
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                count += 1
            except Exception as e:
                self.report["warnings"].append(f"贴图复制失败: {src.name} - {e}")
        self._log_step("textures", f"复制 {count} 个贴图")

    async def _copy_meshes(self, files: List[Path]):
        dest_dir = self.godot_project / "models"
        ensure_dir(dest_dir)
        count = 0
        for src in files:
            try:
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                count += 1
            except Exception as e:
                self.report["warnings"].append(f"网格复制失败: {src.name} - {e}")
        self._log_step("meshes", f"复制 {count} 个网格")

    async def _convert_materials(self, mat_files: List[Path]):
        mat_dir = self.godot_project / "materials"
        ensure_dir(mat_dir)
        converted = 0
        for mat_file in mat_files:
            try:
                docs = parse_unity_yaml_raw(mat_file)
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    saved_props = doc.get("m_SavedProperties", {})
                    if not saved_props:
                        continue
                    mat_name = mat_file.stem
                    mat_data = {
                        "shader": doc.get("m_Shader", {}).get("m_Name", "Standard") if isinstance(doc.get("m_Shader"), dict) else "Standard",
                        "textures": saved_props.get("m_TexEnvs", {}),
                        "floats": saved_props.get("m_Floats", {}),
                        "colors": saved_props.get("m_Colors", {}),
                    }
                    builder = GodotMaterialBuilder(mat_name, self.godot_project)
                    builder.set_from_unity_standard(mat_data)
                    tres_path = builder.save()
                    converted += 1
            except Exception as e:
                self.report["warnings"].append(f"材质转换失败: {mat_file.name} - {e}")
        self._log_step("materials", f"转换 {converted}/{len(mat_files)} 个材质")

    async def _convert_scenes(self, scene_files: List[Path]):
        scenes_dir = self.godot_project / "scenes"
        ensure_dir(scenes_dir)
        converted = 0
        for scene_file in scene_files:
            try:
                parser = UnitySceneParser(scene_file)
                scene_data = parser.parse()
                scene_name = scene_file.stem

                builder = GodotSceneBuilder(scene_name, scenes_dir)
                builder.add_node(scene_name, "Node3D", ".", {})

                for i, go in enumerate(scene_data["game_objects"]):
                    go_name = go.get("name", f"GameObject_{i}")
                    node_type = "Node3D"
                    props = {}
                    if i < len(scene_data["transforms"]):
                        t = scene_data["transforms"][i]
                        pos = t["position"]
                        props["transform"] = (
                            f"Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, "
                            f"{pos['x']}, {pos['y']}, {pos['z']})"
                        )
                    builder.add_node(go_name, node_type, scene_name, props)

                tscn_path = builder.save()
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"场景转换失败: {scene_file.name} - {e}")
        self._log_step("scenes", f"转换 {converted}/{len(scene_files)} 个场景")

    async def _convert_prefabs(self, prefab_files: List[Path]):
        scenes_dir = self.godot_project / "scenes"
        ensure_dir(scenes_dir)
        converted = 0
        for prefab_file in prefab_files:
            try:
                parser = UnitySceneParser(prefab_file)
                prefab_data = parser.parse()
                prefab_name = prefab_file.stem

                builder = GodotSceneBuilder(prefab_name, scenes_dir)
                builder.add_node(prefab_name, "Node3D", ".", {})

                for i, go in enumerate(prefab_data["game_objects"]):
                    go_name = go.get("name", f"PrefabObj_{i}")
                    props = {}
                    if i < len(prefab_data["transforms"]):
                        t = prefab_data["transforms"][i]
                        pos = t["position"]
                        props["transform"] = (
                            f"Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, "
                            f"{pos['x']}, {pos['y']}, {pos['z']})"
                        )
                    builder.add_node(go_name, "Node3D", prefab_name, props)

                builder.save()
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"预制体转换失败: {prefab_file.name} - {e}")
        self._log_step("prefabs", f"转换 {converted}/{len(prefab_files)} 个预制体")

    async def _convert_scripts(self, script_files: List[Path]):
        scripts_dir = self.godot_project / "scripts"
        ensure_dir(scripts_dir)
        converted = 0
        for cs_file in script_files:
            try:
                gd_content = self._cs_to_gdscript(cs_file)
                gd_name = cs_file.stem + ".gd"
                gd_path = scripts_dir / gd_name
                safe_write(gd_path, gd_content)
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"脚本转换失败: {cs_file.name} - {e}")
        self._log_step("scripts", f"转换 {converted}/{len(script_files)} 个脚本 (基础映射)")

    def _cs_to_gdscript(self, cs_file: Path) -> str:
        cs_content = cs_file.read_text(encoding="utf-8", errors="ignore")
        class_name = cs_file.stem
        extends_type = "Node3D"
        is_mono = "MonoBehaviour" in cs_content
        is_so = "ScriptableObject" in cs_content

        if is_so:
            extends_type = "Resource"
        elif is_mono:
            extends_type = "Node3D"

        lines = [
            f"extends {extends_type}",
            f"class_name {class_name}",
            "",
        ]

        import re
        serialized_fields = re.findall(
            r'\[SerializeField\]\s+(?:private\s+|public\s+)?(\w+)\s+(\w+)\s*=\s*([^;]+);',
            cs_content
        )
        public_fields = re.findall(
            r'public\s+(\w+)\s+(\w+)\s*=\s*([^;]+);',
            cs_content
        )

        all_fields = serialized_fields + public_fields
        type_map = {
            "float": "float", "int": "int", "bool": "bool", "string": "String",
            "Vector3": "Vector3", "Vector2": "Vector2", "Color": "Color",
            "GameObject": "Node3D", "Transform": "Node3D", "Rigidbody": "RigidBody3D",
            "AudioSource": "AudioStreamPlayer3D", "Animator": "AnimationPlayer",
        }

        for cs_type, var_name, default_val in all_fields:
            gd_type = type_map.get(cs_type, "var")
            if gd_type == "var":
                lines.append(f"@export var {var_name} = {default_val.strip()}")
            else:
                lines.append(f"@export var {var_name}: {gd_type} = {default_val.strip()}")

        lines.extend(["", "func _ready():", "    pass", "", "func _process(delta):", "    pass", ""])

        header = (
            f"# 从 Unity C# 自动转换 - {cs_file.name}\n"
            f"# 警告: 此文件为基本映射，需要手动调整逻辑\n"
            f"# 原始文件: {cs_file.relative_to(self.unity_project)}\n\n"
        )
        return header + "\n".join(lines)

    def _log_step(self, step: str, message: str):
        self.report["steps"].append({
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })


class UnityToUE5Converter:
    def __init__(self, unity_project: Path, ue_project: Path):
        self.unity_project = unity_project
        self.ue_project = ue_project
        self.assets_dir = unity_project / "Assets"
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Unity → UE5 转换: {self.unity_project}")

        if not self.assets_dir.exists():
            return {"success": False, "error": f"Unity Assets 目录不存在: {self.assets_dir}"}

        ue_content = self.ue_project / "Content"
        ensure_dir(ue_content)
        ensure_dir(ue_content / "Imported")
        ensure_dir(ue_content / "Imported" / "Meshes")
        ensure_dir(ue_content / "Imported" / "Textures")
        ensure_dir(ue_content / "Imported" / "Materials")
        ensure_dir(ue_content / "Imported" / "Audio")
        self._log_step("init_ue", "UE5 内容目录初始化完成")

        texture_files = [f for f in self.assets_dir.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".tga", ".bmp", ".hdr")]
        mesh_files = [f for f in self.assets_dir.rglob("*") if f.suffix.lower() in (".fbx", ".obj")]
        audio_files = [f for f in self.assets_dir.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]
        script_files = list(self.assets_dir.rglob("*.cs"))
        material_files = list(self.assets_dir.rglob("*.mat"))
        scene_files = list(self.assets_dir.rglob("*.unity"))

        self._log_step("scan", (
            f"扫描: {len(texture_files)} 贴图, {len(mesh_files)} 网格, "
            f"{len(audio_files)} 音频, {len(script_files)} 脚本, "
            f"{len(material_files)} 材质, {len(scene_files)} 场景"
        ))

        await self._copy_to_ue(mesh_files, "Meshes")
        await self._copy_to_ue(texture_files, "Textures")
        await self._copy_to_ue(audio_files, "Audio")

        await self._generate_ue_import_cmds(mesh_files)
        await self._convert_materials_to_ue(material_files)
        await self._convert_scripts_to_ue(script_files)
        await self._convert_scenes_to_ue(scene_files)

        self._log_step("complete", "Unity → UE5 转换完成")
        return {
            "success": True,
            "source": str(self.unity_project),
            "target": str(self.ue_project),
            "stats": {
                "textures": len(texture_files),
                "meshes": len(mesh_files),
                "audio": len(audio_files),
                "scripts": len(script_files),
                "materials": len(material_files),
                "scenes": len(scene_files),
            },
            "report": self.report,
        }

    async def _copy_to_ue(self, files: List[Path], subdir: str):
        dest_dir = self.ue_project / "Content" / "Imported" / subdir
        ensure_dir(dest_dir)
        count = 0
        for src in files:
            try:
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                count += 1
            except Exception as e:
                self.report["warnings"].append(f"复制失败: {src.name} - {e}")
        self._log_step(f"copy_{subdir.lower()}", f"复制 {count} 个{subdir}文件")

    async def _generate_ue_import_cmds(self, mesh_files: List[Path]):
        import_script = self.ue_project / "Content" / "Imported" / "import_meshes.bat"
        lines = ["@echo off", "echo UE5 Mesh Import Script", "echo =======================", ""]
        ue_editor = Path(UE_EDITOR)

        for mesh in mesh_files:
            import_path = f"/Game/Imported/Meshes/{mesh.stem}"
            if ue_editor.exists():
                lines.append(
                    f'echo Importing: {mesh.name}\n'
                    f'"{ue_editor}" "{self.ue_project}" '
                    f'-ImportAsset="/Game/Imported/Meshes" '
                    f'-Source="{mesh}" -quit'
                )
            else:
                lines.append(f'echo MANUAL IMPORT: Copy "{mesh}" to UE Content Browser at {import_path}')

        lines.append("", "echo Done.", "pause")
        safe_write(import_script, "\n".join(lines))
        self._log_step("import_script", f"生成导入脚本: {import_script}")

    async def _convert_materials_to_ue(self, mat_files: List[Path]):
        mat_dir = self.ue_project / "Content" / "Imported" / "Materials"
        ensure_dir(mat_dir)
        converted = 0
        for mat_file in mat_files:
            try:
                docs = parse_unity_yaml_raw(mat_file)
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    saved_props = doc.get("m_SavedProperties", {})
                    if not saved_props:
                        continue
                    mat_name = mat_file.stem
                    ue_mat = self._unity_mat_to_ue(mat_name, saved_props)
                    mat_json = mat_dir / f"{mat_name}.json"
                    safe_write(mat_json, json.dumps(ue_mat, indent=2, ensure_ascii=False))
                    converted += 1
            except Exception as e:
                self.report["warnings"].append(f"材质转换失败: {mat_file.name} - {e}")
        self._log_step("materials", f"转换 {converted}/{len(mat_files)} 个材质")

    def _unity_mat_to_ue(self, name: str, saved_props: Dict) -> Dict:
        shader_name = "Standard"
        textures = saved_props.get("m_TexEnvs", {})
        floats = saved_props.get("m_Floats", {})
        colors = saved_props.get("m_Colors", {})

        ue_textures = {}
        for u_prop, val in textures.items():
            if isinstance(val, dict) and "m_Texture" in val:
                ue_textures[u_prop] = val["m_Texture"]

        return {
            "name": name,
            "material_domain": "Surface",
            "blend_mode": "Opaque" if floats.get("_Mode", 0) == 0 else "Translucent",
            "shading_model": "Default",
            "base_color": colors.get("_Color", {"r": 1, "g": 1, "b": 1, "a": 1}),
            "metallic": floats.get("_Metallic", 0),
            "roughness": 1.0 - floats.get("_Glossiness", 0.5),
            "normal_intensity": floats.get("_BumpScale", 1),
            "emissive": colors.get("_EmissionColor", None),
            "opacity": floats.get("_Cutoff", None),
            "textures": ue_textures,
            "notes": "需在UE材质编辑器中手动重建节点连接",
        }

    async def _convert_scripts_to_ue(self, script_files: List[Path]):
        script_dir = self.ue_project / "Content" / "Imported" / "Scripts"
        ensure_dir(script_dir)
        converted = 0
        for cs_file in script_files:
            try:
                ue_content = self._cs_to_ue_cpp(cs_file)
                cpp_name = cs_file.stem + ".h"
                cpp_path = script_dir / cpp_name
                safe_write(cpp_path, ue_content)
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"脚本转换失败: {cs_file.name} - {e}")
        self._log_step("scripts", f"转换 {converted}/{len(script_files)} 个脚本 (C#→C++头文件映射)")

    def _cs_to_ue_cpp(self, cs_file: Path) -> str:
        cs_content = cs_file.read_text(encoding="utf-8", errors="ignore")
        class_name = cs_file.stem
        is_mono = "MonoBehaviour" in cs_content
        is_so = "ScriptableObject" in cs_content

        if is_so:
            parent_class = "UDataAsset"
        elif is_mono:
            parent_class = "AActor"
        else:
            parent_class = "UObject"

        import re
        fields = re.findall(r'public\s+(\w+)\s+(\w+)\s*[;=]', cs_content)
        serialized = re.findall(r'\[SerializeField\].*?(\w+)\s+(\w+)', cs_content, re.DOTALL)

        uprop_lines = []
        type_map = {
            "float": "float", "int": "int32", "bool": "bool", "string": "FString",
            "Vector3": "FVector", "Vector2": "FVector2D", "Color": "FLinearColor",
            "GameObject": "AActor*", "Transform": "FTransform",
            "Rigidbody": "URigidbody*", "AudioSource": "UAudioComponent*",
            "Animator": "UAnimMontage*",
        }

        for cs_type, var_name in serialized + fields:
            ue_type = type_map.get(cs_type, "UObject*")
            uprop_lines.append(f"    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=\"{class_name}\")")
            uprop_lines.append(f"    {ue_type} {var_name};")
            uprop_lines.append("")

        header = (
            f"// 从 Unity C# 自动转换 - {cs_file.name}\n"
            f"// 警告: 此文件为基本映射，需要手动调整逻辑\n"
            f"// 原始文件: {cs_file.relative_to(self.unity_project)}\n\n"
        )

        content = (
            f"#pragma once\n\n"
            f"#include \"CoreMinimal.h\"\n"
            f'#include "{class_name}.generated.h"\n\n'
            f"UCLASS()\n"
            f"class A{class_name} : public {parent_class}\n"
            f"{{\n"
            f"    GENERATED_BODY()\n\n"
            f"public:\n"
        )
        if uprop_lines:
            content += "\n".join(uprop_lines) + "\n"
        content += (
            f"    virtual void BeginPlay() override;\n"
            f"    virtual void Tick(float DeltaTime) override;\n"
            f"}};\n"
        )

        return header + content

    async def _convert_scenes_to_ue(self, scene_files: List[Path]):
        scene_dir = self.ue_project / "Content" / "Imported" / "Levels"
        ensure_dir(scene_dir)
        converted = 0
        for scene_file in scene_files:
            try:
                parser = UnitySceneParser(scene_file)
                scene_data = parser.parse()
                level_json = {
                    "name": scene_file.stem,
                    "actors": [],
                }
                for i, go in enumerate(scene_data["game_objects"]):
                    actor = {
                        "name": go.get("name", f"Actor_{i}"),
                        "type": "AActor",
                        "components": [],
                    }
                    if i < len(scene_data["transforms"]):
                        t = scene_data["transforms"][i]
                        actor["transform"] = {
                            "location": t["position"],
                            "rotation": t["rotation"],
                            "scale": t["scale"],
                        }
                    level_json["actors"].append(actor)
                json_path = scene_dir / f"{scene_file.stem}.json"
                safe_write(json_path, json.dumps(level_json, indent=2, ensure_ascii=False))
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"场景转换失败: {scene_file.name} - {e}")
        self._log_step("scenes", f"转换 {converted}/{len(scene_files)} 个场景")

    def _log_step(self, step: str, message: str):
        self.report["steps"].append({
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })


class GodotToUE5Converter:
    def __init__(self, godot_project: Path, ue_project: Path):
        self.godot_project = godot_project
        self.ue_project = ue_project
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Godot → UE5 转换: {self.godot_project}")

        ue_content = self.ue_project / "Content" / "Imported" / "FromGodot"
        ensure_dir(ue_content)
        ensure_dir(ue_content / "Meshes")
        ensure_dir(ue_content / "Textures")
        ensure_dir(ue_content / "Materials")
        ensure_dir(ue_content / "Audio")
        ensure_dir(ue_content / "Levels")
        ensure_dir(ue_content / "Scripts")

        mesh_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".glb", ".gltf")]
        texture_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".hdr", ".svg")]
        audio_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".wav", ".ogg", ".mp3")]
        scene_files = list(self.godot_project.rglob("*.tscn"))
        resource_files = list(self.godot_project.rglob("*.tres"))
        script_files = list(self.godot_project.rglob("*.gd"))

        self._log_step("scan", (
            f"扫描: {len(mesh_files)} 网格, {len(texture_files)} 贴图, "
            f"{len(audio_files)} 音频, {len(scene_files)} 场景, "
            f"{len(resource_files)} 资源, {len(script_files)} 脚本"
        ))

        await self._copy_assets(mesh_files, ue_content / "Meshes")
        await self._copy_assets(texture_files, ue_content / "Textures")
        await self._copy_assets(audio_files, ue_content / "Audio")

        await self._convert_scenes(scene_files, ue_content / "Levels")
        await self._convert_materials(resource_files, ue_content / "Materials")
        await self._convert_scripts(script_files, ue_content / "Scripts")

        self._log_step("complete", "Godot → UE5 转换完成")
        return {
            "success": True,
            "source": str(self.godot_project),
            "target": str(self.ue_project),
            "stats": {
                "meshes": len(mesh_files), "textures": len(texture_files),
                "audio": len(audio_files), "scenes": len(scene_files),
                "resources": len(resource_files), "scripts": len(script_files),
            },
            "report": self.report,
        }

    async def _copy_assets(self, files: List[Path], dest_dir: Path):
        ensure_dir(dest_dir)
        count = 0
        for src in files:
            try:
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                count += 1
            except Exception as e:
                self.report["warnings"].append(f"复制失败: {src.name} - {e}")
        self._log_step("copy", f"复制 {count} 个文件到 {dest_dir.name}")

    async def _convert_scenes(self, scene_files: List[Path], dest_dir: Path):
        ensure_dir(dest_dir)
        converted = 0
        for tscn in scene_files:
            try:
                nodes = self._parse_tscn(tscn)
                level_data = {"name": tscn.stem, "actors": []}
                for node in nodes:
                    actor = {
                        "name": node.get("name", "Unnamed"),
                        "type": self._godot_type_to_ue(node.get("type", "Node3D")),
                    }
                    if "transform" in node:
                        actor["transform"] = node["transform"]
                    level_data["actors"].append(actor)
                json_path = dest_dir / f"{tscn.stem}.json"
                safe_write(json_path, json.dumps(level_data, indent=2, ensure_ascii=False))
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"场景转换失败: {tscn.name} - {e}")
        self._log_step("scenes", f"转换 {converted}/{len(scene_files)} 个场景")

    def _parse_tscn(self, tscn_path: Path) -> List[Dict]:
        nodes = []
        try:
            content = tscn_path.read_text(encoding="utf-8", errors="ignore")
            import re
            for match in re.finditer(r'\[node name="([^"]+)" type="([^"]+)"', content):
                nodes.append({"name": match.group(1), "type": match.group(2)})
        except Exception:
            pass
        return nodes

    def _godot_type_to_ue(self, godot_type: str) -> str:
        mapping = {
            "Node3D": "AActor", "MeshInstance3D": "StaticMeshComponent",
            "Camera3D": "CameraComponent", "DirectionalLight3D": "DirectionalLightComponent",
            "OmniLight3D": "PointLightComponent", "SpotLight3D": "SpotLightComponent",
            "RigidBody3D": "StaticMeshComponent", "StaticBody3D": "StaticMeshComponent",
            "CharacterBody3D": "Character", "CollisionShape3D": "BoxCollision",
            "AnimationPlayer": "AnimMontage", "AudioStreamPlayer3D": "AudioComponent",
            "GPUParticles3D": "NiagaraComponent",
        }
        return mapping.get(godot_type, "AActor")

    async def _convert_materials(self, resource_files: List[Path], dest_dir: Path):
        ensure_dir(dest_dir)
        converted = 0
        for tres in resource_files:
            try:
                props = self._parse_tres(tres)
                if not props:
                    continue
                mat_json = {
                    "name": tres.stem,
                    "source": "godot",
                    "properties": props,
                    "notes": "需在UE材质编辑器中手动重建",
                }
                json_path = dest_dir / f"{tres.stem}.json"
                safe_write(json_path, json.dumps(mat_json, indent=2, ensure_ascii=False))
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"材质转换失败: {tres.name} - {e}")
        self._log_step("materials", f"转换 {converted}/{len(resource_files)} 个资源")

    def _parse_tres(self, tres_path: Path) -> Dict:
        props = {}
        try:
            content = tres_path.read_text(encoding="utf-8", errors="ignore")
            import re
            for match in re.finditer(r'^(\w+)\s*=\s*(.+)$', content, re.MULTILINE):
                key = match.group(1)
                val = match.group(2).strip().strip('"')
                if key not in ("gd_scene", "gd_resource", "format", "uid", "load_steps"):
                    props[key] = val
        except Exception:
            pass
        return props

    async def _convert_scripts(self, script_files: List[Path], dest_dir: Path):
        ensure_dir(dest_dir)
        converted = 0
        for gd in script_files:
            try:
                cpp_content = self._gd_to_cpp(gd)
                h_path = dest_dir / f"{gd.stem}.h"
                safe_write(h_path, cpp_content)
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"脚本转换失败: {gd.name} - {e}")
        self._log_step("scripts", f"转换 {converted}/{len(script_files)} 个脚本 (GDScript→C++头文件)")

    def _gd_to_cpp(self, gd_file: Path) -> str:
        content = gd_file.read_text(encoding="utf-8", errors="ignore")
        class_name = gd_file.stem
        extends = "AActor"
        if "extends RigidBody3D" in content:
            extends = "AActor"
        elif "extends Resource" in content:
            extends = "UDataAsset"

        import re
        exports = re.findall(r'@export\s+var\s+(\w+)\s*:\s*(\w+)', content)
        uprop_lines = []
        gd_to_ue = {
            "int": "int32", "float": "float", "bool": "bool", "String": "FString",
            "Vector3": "FVector", "Vector2": "FVector2D", "Color": "FLinearColor",
            "Node3D": "AActor*", "RigidBody3D": "URigidbody*",
        }
        for var_name, var_type in exports:
            ue_type = gd_to_ue.get(var_type, "UObject*")
            uprop_lines.append(f'    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="{class_name}")')
            uprop_lines.append(f"    {ue_type} {var_name};")

        header = (
            f"// 从 Godot GDScript 自动转换 - {gd_file.name}\n"
            f"// 警告: 需手动调整逻辑\n\n"
        )
        body = (
            f"#pragma once\n\n"
            f'#include "CoreMinimal.h"\n'
            f'#include "{class_name}.generated.h"\n\n'
            f"UCLASS()\n"
            f"class A{class_name} : public {extends}\n{{\n"
            f"    GENERATED_BODY()\n\npublic:\n"
        )
        if uprop_lines:
            body += "\n".join(uprop_lines) + "\n"
        body += "    virtual void BeginPlay() override;\n    virtual void Tick(float DeltaTime) override;\n};\n"
        return header + body

    def _log_step(self, step: str, message: str):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


class GodotToUnityConverter:
    def __init__(self, godot_project: Path, unity_project: Path):
        self.godot_project = godot_project
        self.unity_project = unity_project
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Godot → Unity 转换: {self.godot_project}")

        unity_assets = self.unity_project / "Assets" / "Imported" / "FromGodot"
        ensure_dir(unity_assets)
        ensure_dir(unity_assets / "Meshes")
        ensure_dir(unity_assets / "Textures")
        ensure_dir(unity_assets / "Materials")
        ensure_dir(unity_assets / "Audio")
        ensure_dir(unity_assets / "Scenes")
        ensure_dir(unity_assets / "Scripts")

        mesh_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".glb", ".gltf")]
        texture_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".hdr")]
        audio_files = [f for f in self.godot_project.rglob("*") if f.suffix.lower() in (".wav", ".ogg", ".mp3")]
        scene_files = list(self.godot_project.rglob("*.tscn"))
        resource_files = list(self.godot_project.rglob("*.tres"))
        script_files = list(self.godot_project.rglob("*.gd"))

        self._log_step("scan", (
            f"扫描: {len(mesh_files)} 网格, {len(texture_files)} 贴图, "
            f"{len(audio_files)} 音频, {len(scene_files)} 场景, "
            f"{len(resource_files)} 资源, {len(script_files)} 脚本"
        ))

        await self._copy_assets(mesh_files, unity_assets / "Meshes")
        await self._copy_assets(texture_files, unity_assets / "Textures")
        await self._copy_assets(audio_files, unity_assets / "Audio")
        await self._convert_scenes(scene_files, unity_assets / "Scenes")
        await self._convert_materials(resource_files, unity_assets / "Materials")
        await self._convert_scripts(script_files, unity_assets / "Scripts")

        self._log_step("complete", "Godot → Unity 转换完成")
        return {
            "success": True, "source": str(self.godot_project), "target": str(self.unity_project),
            "stats": {"meshes": len(mesh_files), "textures": len(texture_files),
                      "audio": len(audio_files), "scenes": len(scene_files),
                      "resources": len(resource_files), "scripts": len(script_files)},
            "report": self.report,
        }

    async def _copy_assets(self, files, dest_dir):
        ensure_dir(dest_dir)
        count = 0
        for src in files:
            try:
                dest = dest_dir / src.name
                if not dest.exists():
                    shutil.copy2(str(src), str(dest))
                count += 1
            except Exception as e:
                self.report["warnings"].append(f"复制失败: {src.name}")
        self._log_step("copy", f"复制 {count} 个文件")

    async def _convert_scenes(self, scene_files, dest_dir):
        ensure_dir(dest_dir)
        converted = 0
        for tscn in scene_files:
            try:
                nodes = []
                content = tscn.read_text(encoding="utf-8", errors="ignore")
                import re
                for m in re.finditer(r'\[node name="([^"]+)" type="([^"]+)"', content):
                    nodes.append({"name": m.group(1), "type": m.group(2)})
                scene_json = {"name": tscn.stem, "gameObjects": []}
                for n in nodes:
                    go = {"name": n["name"], "components": [self._gd_type_to_unity_comp(n["type"])]}
                    scene_json["gameObjects"].append(go)
                json_path = dest_dir / f"{tscn.stem}.json"
                safe_write(json_path, json.dumps(scene_json, indent=2, ensure_ascii=False))
                converted += 1
            except Exception as e:
                self.report["warnings"].append(f"场景转换失败: {tscn.name}")
        self._log_step("scenes", f"转换 {converted}/{len(scene_files)} 个场景")

    def _gd_type_to_unity_comp(self, gd_type: str) -> str:
        mapping = {
            "Node3D": "Transform", "MeshInstance3D": "MeshFilter+MeshRenderer",
            "Camera3D": "Camera", "DirectionalLight3D": "Light",
            "OmniLight3D": "Light", "SpotLight3D": "Light",
            "RigidBody3D": "Rigidbody", "StaticBody3D": "MeshCollider",
            "CharacterBody3D": "CharacterController", "CollisionShape3D": "BoxCollider",
            "AnimationPlayer": "Animator", "AudioStreamPlayer3D": "AudioSource",
        }
        return mapping.get(gd_type, "Transform")

    async def _convert_materials(self, resource_files, dest_dir):
        ensure_dir(dest_dir)
        converted = 0
        for tres in resource_files:
            try:
                props = {}
                content = tres.read_text(encoding="utf-8", errors="ignore")
                import re
                for m in re.finditer(r'^(\w+)\s*=\s*(.+)$', content, re.MULTILINE):
                    k, v = m.group(1), m.group(2).strip().strip('"')
                    if k not in ("gd_scene", "gd_resource", "format", "uid", "load_steps"):
                        props[k] = v
                if props:
                    mat_json = {"name": tres.stem, "source": "godot", "properties": props}
                    safe_write(dest_dir / f"{tres.stem}.json", json.dumps(mat_json, indent=2, ensure_ascii=False))
                    converted += 1
            except Exception:
                pass
        self._log_step("materials", f"转换 {converted}/{len(resource_files)} 个资源")

    async def _convert_scripts(self, script_files, dest_dir):
        ensure_dir(dest_dir)
        converted = 0
        for gd in script_files:
            try:
                cs = self._gd_to_cs(gd)
                safe_write(dest_dir / f"{gd.stem}.cs", cs)
                converted += 1
            except Exception:
                pass
        self._log_step("scripts", f"转换 {converted}/{len(script_files)} 个脚本 (GD→C#)")

    def _gd_to_cs(self, gd_file: Path) -> str:
        content = gd_file.read_text(encoding="utf-8", errors="ignore")
        name = gd_file.stem
        extends = "MonoBehaviour"
        if "extends Resource" in content:
            extends = "ScriptableObject"

        import re
        exports = re.findall(r'@export\s+var\s+(\w+)\s*:\s*(\w+)', content)
        gd_to_cs = {"int": "int", "float": "float", "bool": "bool", "String": "string",
                     "Vector3": "Vector3", "Vector2": "Vector2", "Color": "Color"}

        fields = []
        for vname, vtype in exports:
            cs_type = gd_to_cs.get(vtype, "object")
            fields.append(f"    [SerializeField] private {cs_type} {vname};")

        cs = f"// 从 Godot GDScript 自动转换 - {gd_file.name}\n// 警告: 需手动调整逻辑\n\n"
        cs += "using UnityEngine;\n\n"
        cs += f"public class {name} : {extends}\n{{\n"
        cs += "\n".join(fields) + "\n"
        if "_ready" in content:
            cs += "    void Awake() { /* from _ready() */ }\n"
        if "_process" in content:
            cs += "    void Update() { /* from _process() */ }\n"
        cs += "}\n"
        return cs

    def _log_step(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


class UEToUnityConverter:
    def __init__(self, ue_export_path: Path, unity_project: Path):
        self.ue_export_path = ue_export_path
        self.unity_project = unity_project
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 UE → Unity 转换: {self.ue_export_path}")
        unity_assets = self.unity_project / "Assets" / "Imported" / "FromUE"
        ensure_dir(unity_assets)
        ensure_dir(unity_assets / "Meshes")
        ensure_dir(unity_assets / "Textures")
        ensure_dir(unity_assets / "Materials")
        ensure_dir(unity_assets / "Audio")

        mesh_files = [f for f in self.ue_export_path.rglob("*") if f.suffix.lower() in (".fbx", ".obj")]
        texture_files = [f for f in self.ue_export_path.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".tga", ".bmp", ".hdr")]
        audio_files = [f for f in self.ue_export_path.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]

        self._log_step("scan", f"扫描: {len(mesh_files)} 网格, {len(texture_files)} 贴图, {len(audio_files)} 音频")

        for src_list, subdir in [(mesh_files, "Meshes"), (texture_files, "Textures"), (audio_files, "Audio")]:
            dest = unity_assets / subdir
            ensure_dir(dest)
            count = 0
            for src in src_list:
                try:
                    d = dest / src.name
                    if not d.exists():
                        shutil.copy2(str(src), str(d))
                    count += 1
                except Exception:
                    pass
            self._log_step(f"copy_{subdir.lower()}", f"复制 {count} 个{subdir}")

        self._log_step("complete", "UE → Unity 转换完成")
        return {
            "success": True, "source": str(self.ue_export_path), "target": str(self.unity_project),
            "stats": {"meshes": len(mesh_files), "textures": len(texture_files), "audio": len(audio_files)},
            "report": self.report,
        }

    def _log_step(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


class BlenderToEngineConverter:
    def __init__(self, blend_path: Path, target_project: Path, target_engine: str = "godot"):
        self.blend_path = blend_path
        self.target_project = target_project
        self.target_engine = target_engine
        self.report = {"steps": [], "warnings": [], "errors": []}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Blender → {self.target_engine.upper()} 转换: {self.blend_path}")

        blender = Path(BLENDER_EXE)
        if not blender.exists():
            return {"success": False, "error": f"Blender 未找到: {BLENDER_EXE}"}

        if self.target_engine == "godot":
            export_format = "glb"
            output_file = self.target_project / "models" / f"{self.blend_path.stem}.glb"
        elif self.target_engine == "ue5":
            export_format = "fbx"
            output_file = self.target_project / "Content" / "Imported" / "Blender" / f"{self.blend_path.stem}.fbx"
        elif self.target_engine == "unity":
            export_format = "fbx"
            output_file = self.target_project / "Assets" / "Imported" / "Blender" / f"{self.blend_path.stem}.fbx"
        else:
            return {"success": False, "error": f"不支持的目标引擎: {self.target_engine}"}

        ensure_dir(output_file.parent)

        if export_format == "glb":
            export_cmd = "bpy.ops.export_scene.gltf(filepath=r'%s', export_format='GLB')" % output_file
        else:
            export_cmd = (
                "bpy.ops.export_scene.fbx(filepath=r'%s', use_selection=False, "
                "global_scale=1.0, apply_unit_scale=True, axis_forward='-Z', axis_up='Y')" % output_file
            )

        script = f"""
import bpy
bpy.ops.wm.open_mainfile(filepath=r"{self.blend_path}")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
{export_cmd}
print("EXPORT_OK")
"""
        script_path = Path(f"/python/Temp/blender_export_{self.blend_path.stem}.py")
        safe_write(script_path, script)

        try:
            cmd = [str(blender), "--background", "--python", str(script_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and output_file.exists():
                self._log_step("blender_export", f"Blender 导出: {output_file.name}")
                if self.target_engine == "godot":
                    await self._assemble_godot_scene(output_file)
            else:
                self.report["errors"].append(f"Blender 导出失败: {stderr.decode()[-500:]}")
        except Exception as e:
            self.report["errors"].append(f"Blender 执行错误: {e}")

        self._log_step("complete", f"Blender → {self.target_engine.upper()} 转换完成")
        return {
            "success": output_file.exists() if 'output_file' in dir() else False,
            "source": str(self.blend_path), "target": str(self.target_project),
            "output_file": str(output_file) if 'output_file' in dir() else "",
            "report": self.report,
        }

    async def _assemble_godot_scene(self, glb_path: Path):
        scene_name = glb_path.stem
        rel_path = f"res://models/{glb_path.name}"
        uid = generate_uid(rel_path)
        scene_uid = generate_uid(f"scene_{scene_name}")
        uid_short = scene_uid[9:]

        tscn = (
            f'[gd_scene load_steps=2 format=3 uid="{scene_uid}"]\n\n'
            f'[ext_resource type="PackedScene" uid="{uid}" path="{rel_path}" id="1_{uid_short}"]\n\n'
            f'[node name="{scene_name}" type="Node3D"]\n\n'
            f'[node name="ModelRoot" type="Node3D" parent="."]\n'
        )
        tscn_path = self.target_project / "scenes" / f"{scene_name}.tscn"
        safe_write(tscn_path, tscn)
        self._log_step("godot_assemble", f"Godot 场景: {tscn_path.name}")

    def _log_step(self, step, message):
        self.report["steps"].append({"step": step, "message": message, "timestamp": datetime.now().isoformat()})


def analyze_project(project_path: Path) -> Dict[str, Any]:
    result = {
        "path": str(project_path),
        "engine": "unknown",
        "assets": {},
        "convertible": [],
    }

    if (project_path / "Assets").exists() and (project_path / "ProjectSettings").exists():
        result["engine"] = "Unity"
        assets = project_path / "Assets"
        result["assets"] = {
            "scenes": len(list(assets.rglob("*.unity"))),
            "prefabs": len(list(assets.rglob("*.prefab"))),
            "materials": len(list(assets.rglob("*.mat"))),
            "scripts": len(list(assets.rglob("*.cs"))),
            "textures": len([f for f in assets.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".tga", ".psd")]),
            "meshes": len([f for f in assets.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".gltf")]),
            "audio": len([f for f in assets.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]),
        }
        result["convertible"] = ["godot", "ue5", "blender"]

    elif (project_path / "Content").exists() and list(project_path.glob("*.uproject")):
        result["engine"] = "UE"
        content = project_path / "Content"
        result["assets"] = {
            "uassets": len(list(content.rglob("*.uasset"))),
            "umaps": len(list(content.rglob("*.umap"))),
            "blueprints": len(list(content.rglob("*.uasset"))),
        }
        result["convertible"] = ["godot", "unity", "blender"]

    elif (project_path / "project.godot").exists() or (project_path / ".godot").exists():
        result["engine"] = "Godot"
        result["assets"] = {
            "scenes": len(list(project_path.rglob("*.tscn"))),
            "resources": len(list(project_path.rglob("*.tres"))),
            "scripts": len(list(project_path.rglob("*.gd"))),
        }
        result["convertible"] = ["ue5", "unity", "blender"]

    elif (project_path / "Assets").exists():
        result["engine"] = "Unity (partial)"
        assets = project_path / "Assets"
        result["assets"] = {
            "files": len(list(assets.rglob("*"))),
        }
        result["convertible"] = ["godot", "ue5"]

    else:
        ext_counts = {}
        for f in project_path.rglob("*") if project_path.is_dir() else [project_path]:
            if f.is_file():
                ext = f.suffix.lower()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
        result["assets"] = {"by_extension": ext_counts}
        if ".fbx" in ext_counts or ".obj" in ext_counts or ".glb" in ext_counts:
            result["convertible"] = ["godot", "ue5"]

    return result


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
