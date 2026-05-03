import os
import sys
import json
import shutil
import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

from .config import Config
from .state import ConvertState
from .godot_builder import (
    generate_uid, ensure_dir, safe_write,
    GodotSceneBuilder, GodotMaterialBuilder, GodotProjectInitializer,
    UNITY_SHADER_MAP, UNITY_TEX_PROP_MAP, UNITY_FLOAT_PROP_MAP, UNITY_COLOR_PROP_MAP,
)
from .blender_bridge import BlenderBridge

MCP_PATH = Path("/python/storage/mcp/JM")

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


class BaseConverter:
    def __init__(self, source_path, target_path, config=None):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path)
        self.config = config or Config.load()
        self.report = {"steps": [], "warnings": [], "errors": []}
        self.steps_completed = []
        self.state = ConvertState(Path(target_path), self.source_path.stem)

    async def convert(self) -> Dict[str, Any]:
        raise NotImplementedError

    def _log_step(self, step, message):
        self.report["steps"].append({
            "step": step,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })

    def _step(self, step_name: str, action, output_files: Dict[str, str] = None):
        if self.state.is_completed(step_name):
            self._log_step("SKIP", f"{step_name} 已完成，跳过")
            return True
        try:
            result = action()
            self.state.mark_completed(step_name, output_files)
            return result
        except Exception as e:
            self.state.mark_failed(step_name, str(e))
            raise


class UEToGodotConverter(BaseConverter):
    def __init__(self, source_path, godot_project, scene_name="MainScene", config=None):
        super().__init__(source_path, godot_project, config)
        self.scene_name = scene_name

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 UE → Godot 转换: {self.source_path}")

        init = GodotProjectInitializer(self.target_path, self.scene_name)
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
                bridge = BlenderBridge(self.config.blender_path)
                converted = await bridge.convert_to_glb(
                    fbx_files + obj_files,
                    self.target_path / "models",
                    warnings=self.report["warnings"],
                )
                if converted:
                    await self._assemble_glb_scenes(converted)

        scene_builder = GodotSceneBuilder(self.scene_name, self.target_path / "scenes")
        scene_builder.add_node(self.scene_name, "Node3D", ".", {})

        for mesh_file in copied_meshes:
            mesh_name = mesh_file.stem
            rel_path = f"res://models/{mesh_file.name}"
            mesh_uid = generate_uid(rel_path)
            res_id = scene_builder.add_ext_resource("ArrayMesh", rel_path, mesh_uid)
            scene_builder.add_node(mesh_name, "MeshInstance3D", self.scene_name, {
                "mesh": f'ExtResource("{res_id}")',
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
            "target": str(self.target_path),
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
        dest_dir = self.target_path / subdir
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
                        str(glb), str(self.target_path), scene_name,
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
        tscn_path = self.target_path / "scenes" / f"{scene_name}.tscn"
        safe_write(tscn_path, tscn_content)
        self._log_step("assemble_manual", f"手动场景组装: {scene_name}")


class UnityToGodotConverter(BaseConverter):
    def __init__(self, unity_project, godot_project, config=None):
        super().__init__(unity_project, godot_project, config)
        self.assets_dir = self.source_path / "Assets"
        self.guid_map = {}

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Unity → Godot 转换: {self.source_path}")

        if not self.assets_dir.exists():
            return {"success": False, "error": f"Unity Assets 目录不存在: {self.assets_dir}"}

        init = GodotProjectInitializer(self.target_path, self.source_path.name)
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
            "source": str(self.source_path),
            "target": str(self.target_path),
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
        dest_dir = self.target_path / "textures"
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
        dest_dir = self.target_path / "models"
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
        mat_dir = self.target_path / "materials"
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
                    builder = GodotMaterialBuilder(mat_name, self.target_path)
                    builder.set_from_unity_standard(mat_data)
                    tres_path = builder.save()
                    converted += 1
            except Exception as e:
                self.report["warnings"].append(f"材质转换失败: {mat_file.name} - {e}")
        self._log_step("materials", f"转换 {converted}/{len(mat_files)} 个材质")

    async def _convert_scenes(self, scene_files: List[Path]):
        scenes_dir = self.target_path / "scenes"
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
        scenes_dir = self.target_path / "scenes"
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
        scripts_dir = self.target_path / "scripts"
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
            f"# 原始文件: {cs_file.relative_to(self.source_path)}\n\n"
        )
        return header + "\n".join(lines)


class UnityToUE5Converter(BaseConverter):
    def __init__(self, unity_project, ue_project, config=None):
        super().__init__(unity_project, ue_project, config)
        self.assets_dir = self.source_path / "Assets"

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Unity → UE5 转换: {self.source_path}")

        if not self.assets_dir.exists():
            return {"success": False, "error": f"Unity Assets 目录不存在: {self.assets_dir}"}

        ue_content = self.target_path / "Content"
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
            "source": str(self.source_path),
            "target": str(self.target_path),
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
        dest_dir = self.target_path / "Content" / "Imported" / subdir
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
        import_script = self.target_path / "Content" / "Imported" / "import_meshes.bat"
        lines = ["@echo off", "echo UE5 Mesh Import Script", "echo =======================", ""]
        ue_editor = Path(self.config.ue5_path)

        for mesh in mesh_files:
            import_path = f"/Game/Imported/Meshes/{mesh.stem}"
            if ue_editor.exists():
                lines.append(
                    f'echo Importing: {mesh.name}\n'
                    f'"{ue_editor}" "{self.target_path}" '
                    f'-ImportAsset="/Game/Imported/Meshes" '
                    f'-Source="{mesh}" -quit'
                )
            else:
                lines.append(f'echo MANUAL IMPORT: Copy "{mesh}" to UE Content Browser at {import_path}')

        lines.append("", "echo Done.", "pause")
        safe_write(import_script, "\n".join(lines))
        self._log_step("import_script", f"生成导入脚本: {import_script}")

    async def _convert_materials_to_ue(self, mat_files: List[Path]):
        mat_dir = self.target_path / "Content" / "Imported" / "Materials"
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
        script_dir = self.target_path / "Content" / "Imported" / "Scripts"
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
            uprop_lines.append(f'    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="{class_name}")')
            uprop_lines.append(f"    {ue_type} {var_name};")
            uprop_lines.append("")

        header = (
            f"// 从 Unity C# 自动转换 - {cs_file.name}\n"
            f"// 警告: 此文件为基本映射，需要手动调整逻辑\n"
            f"// 原始文件: {cs_file.relative_to(self.source_path)}\n\n"
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
        scene_dir = self.target_path / "Content" / "Imported" / "Levels"
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


class GodotToUE5Converter(BaseConverter):
    def __init__(self, godot_project, ue_project, config=None):
        super().__init__(godot_project, ue_project, config)

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Godot → UE5 转换: {self.source_path}")

        ue_content = self.target_path / "Content" / "Imported" / "FromGodot"
        ensure_dir(ue_content)
        ensure_dir(ue_content / "Meshes")
        ensure_dir(ue_content / "Textures")
        ensure_dir(ue_content / "Materials")
        ensure_dir(ue_content / "Audio")
        ensure_dir(ue_content / "Levels")
        ensure_dir(ue_content / "Scripts")

        mesh_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".glb", ".gltf")]
        texture_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".hdr", ".svg")]
        audio_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".wav", ".ogg", ".mp3")]
        scene_files = list(self.source_path.rglob("*.tscn"))
        resource_files = list(self.source_path.rglob("*.tres"))
        script_files = list(self.source_path.rglob("*.gd"))

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
            "source": str(self.source_path),
            "target": str(self.target_path),
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


class GodotToUnityConverter(BaseConverter):
    def __init__(self, godot_project, unity_project, config=None):
        super().__init__(godot_project, unity_project, config)

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Godot → Unity 转换: {self.source_path}")

        unity_assets = self.target_path / "Assets" / "Imported" / "FromGodot"
        ensure_dir(unity_assets)
        ensure_dir(unity_assets / "Meshes")
        ensure_dir(unity_assets / "Textures")
        ensure_dir(unity_assets / "Materials")
        ensure_dir(unity_assets / "Audio")
        ensure_dir(unity_assets / "Scenes")
        ensure_dir(unity_assets / "Scripts")

        mesh_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".glb", ".gltf")]
        texture_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".hdr")]
        audio_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".wav", ".ogg", ".mp3")]
        scene_files = list(self.source_path.rglob("*.tscn"))
        resource_files = list(self.source_path.rglob("*.tres"))
        script_files = list(self.source_path.rglob("*.gd"))

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
            "success": True, "source": str(self.source_path), "target": str(self.target_path),
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


class UEToUnityConverter(BaseConverter):
    def __init__(self, ue_export_path, unity_project, config=None):
        super().__init__(ue_export_path, unity_project, config)

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 UE → Unity 转换: {self.source_path}")
        unity_assets = self.target_path / "Assets" / "Imported" / "FromUE"
        ensure_dir(unity_assets)
        ensure_dir(unity_assets / "Meshes")
        ensure_dir(unity_assets / "Textures")
        ensure_dir(unity_assets / "Materials")
        ensure_dir(unity_assets / "Audio")

        mesh_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".fbx", ".obj")]
        texture_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".tga", ".bmp", ".hdr")]
        audio_files = [f for f in self.source_path.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]

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
            "success": True, "source": str(self.source_path), "target": str(self.target_path),
            "stats": {"meshes": len(mesh_files), "textures": len(texture_files), "audio": len(audio_files)},
            "report": self.report,
        }


class BlenderToEngineConverter(BaseConverter):
    def __init__(self, blend_path, target_project, target_engine="godot", config=None):
        super().__init__(blend_path, target_project, config)
        self.target_engine = target_engine

    async def convert(self) -> Dict[str, Any]:
        self._log_step("start", f"开始 Blender → {self.target_engine.upper()} 转换: {self.source_path}")

        bridge = BlenderBridge(self.config.blender_path)
        if not bridge.is_available():
            return {"success": False, "error": f"Blender 未找到: {self.config.blender_path}"}

        if self.target_engine == "godot":
            export_format = "glb"
            output_file = self.target_path / "models" / f"{self.source_path.stem}.glb"
        elif self.target_engine == "ue5":
            export_format = "fbx"
            output_file = self.target_path / "Content" / "Imported" / "Blender" / f"{self.source_path.stem}.fbx"
        elif self.target_engine == "unity":
            export_format = "fbx"
            output_file = self.target_path / "Assets" / "Imported" / "Blender" / f"{self.source_path.stem}.fbx"
        else:
            return {"success": False, "error": f"不支持的目标引擎: {self.target_engine}"}

        success = await bridge.export_blend(
            self.source_path, output_file, export_format,
            warnings=self.report["warnings"],
        )

        if success:
            self._log_step("blender_export", f"Blender 导出: {output_file.name}")
            if self.target_engine == "godot":
                await self._assemble_godot_scene(output_file)

        self._log_step("complete", f"Blender → {self.target_engine.upper()} 转换完成")
        return {
            "success": success,
            "source": str(self.source_path),
            "target": str(self.target_path),
            "output_file": str(output_file),
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
        tscn_path = self.target_path / "scenes" / f"{scene_name}.tscn"
        safe_write(tscn_path, tscn)
        self._log_step("godot_assemble", f"Godot 场景: {tscn_path.name}")
