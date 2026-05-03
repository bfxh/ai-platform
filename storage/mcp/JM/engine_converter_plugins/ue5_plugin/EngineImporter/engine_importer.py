import unreal
import json
import os
from pathlib import Path
from typing import Dict, Any, List

class EngineImporter:
    """UE5 编辑器内跨引擎资产导入器"""

    COMPONENT_MAP = {
        "MeshFilter": "StaticMeshComponent",
        "MeshRenderer": "StaticMeshComponent",
        "SkinnedMeshRenderer": "SkeletalMeshComponent",
        "Camera": "CameraComponent",
        "Light": "LightComponent",
        "Rigidbody": "StaticMeshComponent",
        "BoxCollider": "BoxCollision",
        "SphereCollider": "SphereCollision",
        "CapsuleCollider": "CapsuleCollision",
        "AudioSource": "AudioComponent",
        "Animator": "AnimMontage",
        "ParticleSystem": "NiagaraComponent",
        "CharacterController": "CharacterMovementComponent",
    }

    def __init__(self):
        self.editor_util = unreal.EditorLevelLibrary
        self.asset_util = unreal.EditorAssetLibrary
        self.import_util = unreal.ImportSubsystem

    def import_unity_project(self, unity_project_path: str, ue_content_path: str = "/Game/Imported/Unity") -> Dict[str, Any]:
        """从 Unity 项目导入资产到 UE5"""
        report = {"steps": [], "imported": [], "warnings": [], "errors": []}

        unity_assets = Path(unity_project_path) / "Assets"
        if not unity_assets.exists():
            return {"success": False, "error": f"Unity Assets 目录不存在: {unity_assets}"}

        mesh_files = list(unity_assets.rglob("*.fbx")) + list(unity_assets.rglob("*.obj"))
        texture_files = [f for f in unity_assets.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".tga", ".bmp", ".hdr")]
        audio_files = [f for f in unity_assets.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]
        material_files = list(unity_assets.rglob("*.mat"))
        scene_files = list(unity_assets.rglob("*.unity"))

        report["steps"].append(f"扫描: {len(mesh_files)} 网格, {len(texture_files)} 贴图, {len(audio_files)} 音频")

        for mesh_file in mesh_files:
            result = self._import_fbx_to_ue(str(mesh_file), ue_content_path + "/Meshes")
            if result["success"]:
                report["imported"].append(result["asset_path"])
            else:
                report["warnings"].append(f"网格导入失败: {mesh_file.name}")

        for tex_file in texture_files:
            result = self._import_texture_to_ue(str(tex_file), ue_content_path + "/Textures")
            if result["success"]:
                report["imported"].append(result["asset_path"])
            else:
                report["warnings"].append(f"贴图导入失败: {tex_file.name}")

        for audio_file in audio_files:
            result = self._import_audio_to_ue(str(audio_file), ue_content_path + "/Audio")
            if result["success"]:
                report["imported"].append(result["asset_path"])
            else:
                report["warnings"].append(f"音频导入失败: {audio_file.name}")

        if material_files:
            mat_report = self._convert_unity_materials(material_files, ue_content_path + "/Materials")
            report["steps"].append(f"材质映射: {mat_report['converted']}/{len(material_files)}")

        if scene_files:
            scene_report = self._convert_unity_scenes(scene_files, ue_content_path + "/Levels")
            report["steps"].append(f"场景: {scene_report['converted']}/{len(scene_files)}")

        report["success"] = True
        report["total_imported"] = len(report["imported"])
        return report

    def import_godot_project(self, godot_project_path: str, ue_content_path: str = "/Game/Imported/Godot") -> Dict[str, Any]:
        """从 Godot 项目导入资产到 UE5"""
        report = {"steps": [], "imported": [], "warnings": []}

        godot_path = Path(godot_project_path)

        mesh_files = [f for f in godot_path.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".glb", ".gltf")]
        texture_files = [f for f in godot_path.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".hdr")]
        audio_files = [f for f in godot_path.rglob("*") if f.suffix.lower() in (".wav", ".ogg", ".mp3")]
        scene_files = list(godot_path.rglob("*.tscn"))
        resource_files = list(godot_path.rglob("*.tres"))
        script_files = list(godot_path.rglob("*.gd"))

        report["steps"].append(
            f"扫描: {len(mesh_files)} 网格, {len(texture_files)} 贴图, "
            f"{len(scene_files)} 场景, {len(resource_files)} 资源, {len(script_files)} 脚本"
        )

        for mesh_file in mesh_files:
            if mesh_file.suffix.lower() in (".glb", ".gltf"):
                result = self._import_gltf_to_ue(str(mesh_file), ue_content_path + "/Meshes")
            else:
                result = self._import_fbx_to_ue(str(mesh_file), ue_content_path + "/Meshes")
            if result["success"]:
                report["imported"].append(result["asset_path"])

        for tex_file in texture_files:
            result = self._import_texture_to_ue(str(tex_file), ue_content_path + "/Textures")
            if result["success"]:
                report["imported"].append(result["asset_path"])

        if scene_files:
            self._convert_godot_scenes(scene_files, ue_content_path + "/Levels")

        if resource_files:
            self._convert_godot_resources(resource_files, ue_content_path + "/Materials")

        report["success"] = True
        report["total_imported"] = len(report["imported"])
        return report

    def import_blender_file(self, blend_path: str, ue_content_path: str = "/Game/Imported/Blender") -> Dict[str, Any]:
        """从 Blender 文件导入到 UE5"""
        report = {"steps": [], "imported": [], "warnings": []}

        fbx_path = self._convert_blend_to_fbx(blend_path)
        if fbx_path:
            result = self._import_fbx_to_ue(fbx_path, ue_content_path + "/Meshes")
            if result["success"]:
                report["imported"].append(result["asset_path"])
                report["steps"].append(f"Blender → FBX → UE5: {Path(blend_path).name}")
        else:
            report["warnings"].append(f"Blender 转换失败: {blend_path}")

        report["success"] = True
        return report

    def _import_fbx_to_ue(self, fbx_path: str, content_path: str) -> Dict[str, Any]:
        try:
            task = unreal.AssetImportTask()
            task.filename = fbx_path
            task.destination_path = content_path
            task.destination_name = Path(fbx_path).stem
            task.replace_existing = True
            task.automated = True
            task.save = True

            options = unreal.FbxImportUI()
            options.import_mesh = True
            options.import_as_skeletal = False
            options.import_materials = True
            options.import_textures = True
            options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            options.static_mesh_import_data.generate_lightmap_u_vs = True
            options.static_mesh_import_data.auto_compute_lightmap_u_vs = True

            task.options = options

            subsystem = unreal.get_editor_subsystem(unreal.ImportSubsystem)
            subsystem.import_asset_tasks([task])

            asset_path = content_path + "/" + Path(fbx_path).stem
            return {"success": True, "asset_path": asset_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _import_gltf_to_ue(self, gltf_path: str, content_path: str) -> Dict[str, Any]:
        try:
            task = unreal.AssetImportTask()
            task.filename = gltf_path
            task.destination_path = content_path
            task.destination_name = Path(gltf_path).stem
            task.replace_existing = True
            task.automated = True
            task.save = True

            subsystem = unreal.get_editor_subsystem(unreal.ImportSubsystem)
            subsystem.import_asset_tasks([task])

            asset_path = content_path + "/" + Path(gltf_path).stem
            return {"success": True, "asset_path": asset_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _import_texture_to_ue(self, tex_path: str, content_path: str) -> Dict[str, Any]:
        try:
            task = unreal.AssetImportTask()
            task.filename = tex_path
            task.destination_path = content_path
            task.destination_name = Path(tex_path).stem
            task.replace_existing = True
            task.automated = True
            task.save = True

            subsystem = unreal.get_editor_subsystem(unreal.ImportSubsystem)
            subsystem.import_asset_tasks([task])

            asset_path = content_path + "/" + Path(tex_path).stem
            return {"success": True, "asset_path": asset_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _import_audio_to_ue(self, audio_path: str, content_path: str) -> Dict[str, Any]:
        try:
            task = unreal.AssetImportTask()
            task.filename = audio_path
            task.destination_path = content_path
            task.destination_name = Path(audio_path).stem
            task.replace_existing = True
            task.automated = True
            task.save = True

            subsystem = unreal.get_editor_subsystem(unreal.ImportSubsystem)
            subsystem.import_asset_tasks([task])

            asset_path = content_path + "/" + Path(audio_path).stem
            return {"success": True, "asset_path": asset_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _convert_blend_to_fbx(self, blend_path: str) -> str:
        output_fbx = str(Path(blend_path).with_suffix(".fbx"))
        if os.path.exists(output_fbx):
            return output_fbx

        blender_exe = os.getenv("BLENDER_EXECUTABLE", "blender")
        script = f'''
import bpy
bpy.ops.export_scene.fbx(
    filepath=r"{output_fbx}",
    use_selection=False,
    global_scale=1.0,
    apply_unit_scale=True,
    axis_forward='-Z',
    axis_up='Y'
)
'''
        script_path = str(Path(blend_path).parent / "_convert_fbx.py")
        with open(script_path, "w") as f:
            f.write(script)

        import subprocess
        cmd = [blender_exe, "--background", blend_path, "--python", script_path]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            if result.returncode == 0 and os.path.exists(output_fbx):
                return output_fbx
        except Exception:
            pass
        return ""

    def _convert_unity_materials(self, mat_files: List[Path], content_path: str) -> Dict[str, Any]:
        converted = 0
        for mat_file in mat_files:
            try:
                mat_json = self._parse_unity_mat(mat_file)
                json_path = str(mat_file.with_suffix(".json"))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(mat_json, f, indent=2, ensure_ascii=False)
                converted += 1
            except Exception:
                pass
        return {"converted": converted}

    def _parse_unity_mat(self, mat_file: Path) -> Dict:
        try:
            import yaml
            with open(mat_file, "r", encoding="utf-8", errors="ignore") as f:
                docs = list(yaml.safe_load_all(f))
            for doc in docs:
                if doc and "m_SavedProperties" in doc:
                    props = doc["m_SavedProperties"]
                    return {
                        "name": mat_file.stem,
                        "shader": doc.get("m_Shader", {}).get("m_Name", "Standard"),
                        "textures": props.get("m_TexEnvs", {}),
                        "floats": props.get("m_Floats", {}),
                        "colors": props.get("m_Colors", {}),
                    }
        except Exception:
            pass
        return {"name": mat_file.stem, "error": "parse failed"}

    def _convert_unity_scenes(self, scene_files: List[Path], content_path: str) -> Dict[str, Any]:
        converted = 0
        for scene_file in scene_files:
            try:
                level_data = self._parse_unity_scene(scene_file)
                json_path = str(scene_file.with_suffix(".json"))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(level_data, f, indent=2, ensure_ascii=False)
                converted += 1
            except Exception:
                pass
        return {"converted": converted}

    def _parse_unity_scene(self, scene_file: Path) -> Dict:
        try:
            import yaml
            with open(scene_file, "r", encoding="utf-8", errors="ignore") as f:
                docs = list(yaml.safe_load_all(f))
            actors = []
            for doc in docs:
                if doc and "m_Name" in doc:
                    actors.append({
                        "name": doc.get("m_Name", "Unnamed"),
                        "type": "AActor",
                    })
            return {"name": scene_file.stem, "actors": actors}
        except Exception:
            return {"name": scene_file.stem, "error": "parse failed"}

    def _convert_godot_scenes(self, scene_files: List[Path], content_path: str) -> Dict[str, Any]:
        converted = 0
        for scene_file in scene_files:
            try:
                level_data = self._parse_godot_tscn(scene_file)
                json_path = str(scene_file.with_suffix(".json"))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(level_data, f, indent=2, ensure_ascii=False)
                converted += 1
            except Exception:
                pass
        return {"converted": converted}

    def _parse_godot_tscn(self, tscn_file: Path) -> Dict:
        nodes = []
        with open(tscn_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith('[node name='):
                    import re
                    match = re.search(r'name="([^"]+)".*type="([^"]+)"', line)
                    if match:
                        nodes.append({"name": match.group(1), "type": match.group(2)})
        return {"name": tscn_file.stem, "nodes": nodes}

    def _convert_godot_resources(self, resource_files: List[Path], content_path: str) -> Dict[str, Any]:
        converted = 0
        for res_file in resource_files:
            try:
                res_data = self._parse_godot_tres(res_file)
                json_path = str(res_file.with_suffix(".json"))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(res_data, f, indent=2, ensure_ascii=False)
                converted += 1
            except Exception:
                pass
        return {"converted": converted}

    def _parse_godot_tres(self, tres_file: Path) -> Dict:
        props = {}
        with open(tres_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("["):
                    key, _, val = line.partition("=")
                    props[key.strip()] = val.strip().strip('"')
        return {"name": tres_file.stem, "properties": props}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="UE5 Engine Importer")
    parser.add_argument("action", choices=["import_unity", "import_godot", "import_blender"])
    parser.add_argument("source_path", help="源项目路径")
    parser.add_argument("--content-path", default="/Game/Imported", help="UE Content 路径")
    args = parser.parse_args()

    importer = EngineImporter()
    if args.action == "import_unity":
        result = importer.import_unity_project(args.source_path, args.content_path + "/Unity")
    elif args.action == "import_godot":
        result = importer.import_godot_project(args.source_path, args.content_path + "/Godot")
    elif args.action == "import_blender":
        result = importer.import_blender_file(args.source_path, args.content_path + "/Blender")

    print(json.dumps(result, indent=2, ensure_ascii=False))
