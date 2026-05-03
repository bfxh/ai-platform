import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any

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
