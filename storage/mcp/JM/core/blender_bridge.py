import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from .godot_builder import ensure_dir, safe_write


class BlenderBridge:
    def __init__(self, blender_exe: str):
        self.blender_exe = Path(blender_exe)

    def is_available(self) -> bool:
        return self.blender_exe.exists()

    def import_file(self, filepath: Path) -> str:
        ext = filepath.suffix.lower()
        if ext == ".fbx":
            return (
                "try:\n"
                "    bpy.ops.import_scene.fbx(filepath=r\"{filepath}\")\n"
                "except AttributeError:\n"
                "    bpy.ops.wm.fbx_import(filepath=r\"{filepath}\")\n"
            ).format(filepath=filepath)
        elif ext == ".obj":
            return (
                "try:\n"
                "    bpy.ops.wm.obj_import(filepath=r\"{filepath}\")\n"
                "except AttributeError:\n"
                "    bpy.ops.import_scene.obj(filepath=r\"{filepath}\")\n"
            ).format(filepath=filepath)
        elif ext == ".gltf" or ext == ".glb":
            return (
                "bpy.ops.import_scene.gltf(filepath=r\"{filepath}\")\n"
            ).format(filepath=filepath)
        elif ext == ".blend":
            return (
                "bpy.ops.wm.open_mainfile(filepath=r\"{filepath}\")\n"
            ).format(filepath=filepath)
        else:
            return (
                "try:\n"
                "    bpy.ops.import_scene.fbx(filepath=r\"{filepath}\")\n"
                "except Exception:\n"
                "    pass\n"
            ).format(filepath=filepath)

    async def convert_to_glb(
        self,
        input_files: List[Path],
        output_dir: Path,
        warnings: Optional[list] = None,
    ) -> List[Path]:
        converted = []
        if not self.is_available():
            if warnings is not None:
                warnings.append("Blender 未找到，跳过 FBX/OBJ → glTF 转换")
            return converted

        ensure_dir(output_dir)

        for src in input_files:
            output_glb = output_dir / f"{src.stem}.glb"
            import_code = self.import_file(src)
            script = (
                "import bpy\n"
                "bpy.ops.object.select_all(action='SELECT')\n"
                "bpy.ops.object.delete(use_global=False)\n"
                f"{import_code}"
                "bpy.ops.object.select_all(action='SELECT')\n"
                "bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)\n"
                "bpy.ops.export_scene.gltf(filepath=r\"{output_glb}\", use_selection=True, export_format='GLB')\n"
            ).format(output_glb=output_glb)
            script_path = Path(f"/python/Temp/blender_convert_{src.stem}.py")
            safe_write(script_path, script)

            try:
                cmd = [str(self.blender_exe), "--background", "--python", str(script_path)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0 and output_glb.exists():
                    converted.append(output_glb)
                else:
                    if warnings is not None:
                        warnings.append(f"Blender 转换失败: {src.name}")
            except Exception as e:
                if warnings is not None:
                    warnings.append(f"Blender 执行错误: {e}")

        return converted

    async def convert_to_fbx(
        self,
        input_files: List[Path],
        output_dir: Path,
        warnings: Optional[list] = None,
    ) -> List[Path]:
        converted = []
        if not self.is_available():
            if warnings is not None:
                warnings.append("Blender 未找到，跳过 → FBX 转换")
            return converted

        ensure_dir(output_dir)

        for src in input_files:
            output_fbx = output_dir / f"{src.stem}.fbx"
            import_code = self.import_file(src)
            script = (
                "import bpy\n"
                "bpy.ops.object.select_all(action='SELECT')\n"
                "bpy.ops.object.delete(use_global=False)\n"
                f"{import_code}"
                "bpy.ops.object.select_all(action='SELECT')\n"
                "bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)\n"
                "bpy.ops.export_scene.fbx(filepath=r\"{output_fbx}\", "
                "use_selection=False, global_scale=1.0, "
                "apply_unit_scale=True, axis_forward='-Z', axis_up='Y')\n"
            ).format(output_fbx=output_fbx)
            script_path = Path(f"/python/Temp/blender_convert_fbx_{src.stem}.py")
            safe_write(script_path, script)

            try:
                cmd = [str(self.blender_exe), "--background", "--python", str(script_path)]
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode == 0 and output_fbx.exists():
                    converted.append(output_fbx)
                else:
                    if warnings is not None:
                        warnings.append(f"Blender FBX导出失败: {src.name}")
            except Exception as e:
                if warnings is not None:
                    warnings.append(f"Blender 执行错误: {e}")

        return converted

    async def export_blend(
        self,
        blend_path: Path,
        output_file: Path,
        export_format: str = "glb",
        warnings: Optional[list] = None,
    ) -> bool:
        if not self.is_available():
            if warnings is not None:
                warnings.append(f"Blender 未找到: {self.blender_exe}")
            return False

        ensure_dir(output_file.parent)

        if export_format == "glb":
            export_cmd = (
                "bpy.ops.export_scene.gltf(filepath=r'%s', export_format='GLB')" % output_file
            )
        else:
            export_cmd = (
                "bpy.ops.export_scene.fbx(filepath=r'%s', use_selection=False, "
                "global_scale=1.0, apply_unit_scale=True, axis_forward='-Z', axis_up='Y')" % output_file
            )

        script = (
            "import bpy\n"
            f"bpy.ops.wm.open_mainfile(filepath=r\"{blend_path}\")\n"
            "bpy.ops.object.select_all(action='SELECT')\n"
            "bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)\n"
            f"{export_cmd}\n"
            'print("EXPORT_OK")\n'
        )
        script_path = Path(f"/python/Temp/blender_export_{blend_path.stem}.py")
        safe_write(script_path, script)

        try:
            cmd = [str(self.blender_exe), "--background", "--python", str(script_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and output_file.exists():
                return True
            else:
                if warnings is not None:
                    warnings.append(f"Blender 导出失败: {stderr.decode()[-500:]}")
        except Exception as e:
            if warnings is not None:
                warnings.append(f"Blender 执行错误: {e}")

        return False

    async def bake(
        self,
        input_path: Path,
        output_dir: Path,
        model_name: str,
        preset: str = "default_cyan_metallic",
        bake_size: int = 512,
        warnings: Optional[list] = None,
    ) -> List[Path]:
        if not self.is_available():
            if warnings is not None:
                warnings.append(f"Blender 未找到: {self.blender_exe}")
            return []

        template_dir = Path(__file__).parent.parent / "bake_templates"
        template_path = template_dir / f"{preset}.py"
        if not template_path.exists():
            raise FileNotFoundError(f"烘焙模板不存在: {preset}")

        template_content = template_path.read_text(encoding="utf-8")
        script_content = template_content.format(
            src=str(input_path).replace("\\", "\\\\"),
            out_dir=str(output_dir).replace("\\", "\\\\"),
            model_name=model_name,
            bake_size=bake_size,
        )

        ensure_dir(output_dir)
        script_path = Path(f"/python/Temp/blender_bake_{model_name}.py")
        safe_write(script_path, script_content)

        output_files = []
        try:
            cmd = [str(self.blender_exe), "--background", "--python", str(script_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                if warnings is not None:
                    err_msg = stderr.decode(errors="replace")[-500:] if stderr else "unknown"
                    warnings.append(f"Blender 烘焙失败: {err_msg}")
                return []

            glb_file = output_dir / f"{model_name}.glb"
            fbx_file = output_dir / f"{model_name}.fbx"
            albedo_file = output_dir / f"{model_name}_Albedo.png"
            rough_file = output_dir / f"{model_name}_Roughness.png"
            normal_file = output_dir / f"{model_name}_Normal.png"

            for f in [glb_file, fbx_file, albedo_file, rough_file, normal_file]:
                if f.exists():
                    output_files.append(f)

        except Exception as e:
            if warnings is not None:
                warnings.append(f"Blender 执行错误: {e}")

        return output_files
