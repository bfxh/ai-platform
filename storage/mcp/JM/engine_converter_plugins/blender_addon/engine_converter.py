bl_info = {
    "name": "Engine Converter",
    "author": "AI Platform",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Engine Converter",
    "description": "跨引擎资产转换 - Blender ↔ UE/Unity/Godot",
    "category": "Import-Export",
}

import bpy
import os
import json
import shutil
from pathlib import Path
from datetime import datetime


class ENGINE_CONVERTER_Properties(bpy.types.PropertyGroup):
    target_engine: bpy.props.EnumProperty(
        name="Target Engine",
        description="选择目标引擎",
        items=[
            ('UNREAL', "Unreal Engine 5", "导出到 UE5"),
            ('UNITY', "Unity", "导出到 Unity"),
            ('GODOT', "Godot 4.x", "导出到 Godot"),
        ],
        default='UNREAL'
    )

    export_format: bpy.props.EnumProperty(
        name="Export Format",
        items=[
            ('FBX', "FBX", "Autodesk FBX (UE/Unity通用)"),
            ('GLTF', "glTF/GLB", "Khronos glTF (Godot首选)"),
            ('OBJ', "OBJ", "Wavefront OBJ (简单网格)"),
            ('USD', "USD", "Universal Scene Description (UE原生)"),
        ],
        default='FBX'
    )

    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="输出目录",
        subtype='DIR_PATH',
        default=""
    )

    project_path: bpy.props.StringProperty(
        name="Project Path",
        description="目标引擎项目路径",
        subtype='DIR_PATH',
        default=""
    )

    export_meshes: bpy.props.BoolProperty(name="Meshes", default=True)
    export_armatures: bpy.props.BoolProperty(name="Armatures", default=True)
    export_animations: bpy.props.BoolProperty(name="Animations", default=True)
    export_materials: bpy.props.BoolProperty(name="Materials", default=True)
    export_textures: bpy.props.BoolProperty(name="Textures", default=True)
    export_cameras: bpy.props.BoolProperty(name="Cameras", default=False)
    export_lights: bpy.props.BoolProperty(name="Lights", default=False)

    apply_modifiers: bpy.props.BoolProperty(name="Apply Modifiers", default=True)
    apply_transform: bpy.props.BoolProperty(name="Apply Transform", default=True)
    triangulate: bpy.props.BoolProperty(name="Triangulate", default=False)

    ue_scale: bpy.props.FloatProperty(name="UE Scale", default=1.0, min=0.01, max=100.0)
    unity_scale: bpy.props.FloatProperty(name="Unity Scale", default=1.0, min=0.01, max=100.0)
    godot_scale: bpy.props.FloatProperty(name="Godot Scale", default=1.0, min=0.01, max=100.0)

    import_source: bpy.props.EnumProperty(
        name="Import Source",
        items=[
            ('UE', "Unreal Engine", "从UE导入"),
            ('UNITY', "Unity", "从Unity导入"),
            ('GODOT', "Godot", "从Godot导入"),
        ],
        default='UNITY'
    )

    import_path: bpy.props.StringProperty(
        name="Import Path",
        subtype='DIR_PATH',
        default=""
    )

    log_text: bpy.props.StringProperty(name="Log", default="")


class ENGINE_CONVERTER_OT_ExportToEngine(bpy.types.Operator):
    bl_idname = "engine_converter.export"
    bl_label = "Export to Engine"
    bl_description = "导出当前场景到目标引擎"

    def execute(self, context):
        props = context.scene.engine_converter_props
        output_dir = props.output_path

        if not output_dir:
            self.report({'ERROR'}, "请设置输出路径")
            return {'CANCELLED'}

        os.makedirs(output_dir, exist_ok=True)

        if props.apply_transform:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        if props.target_engine == 'UNREAL':
            result = self._export_to_ue(context, output_dir)
        elif props.target_engine == 'UNITY':
            result = self._export_to_unity(context, output_dir)
        elif props.target_engine == 'GODOT':
            result = self._export_to_godot(context, output_dir)
        else:
            result = {'CANCELLED'}

        if props.export_textures:
            self._copy_textures(output_dir)

        self.report({'INFO'}, f"导出完成: {output_dir}")
        return result

    def _export_to_ue(self, context, output_dir):
        props = context.scene.engine_converter_props
        export_file = os.path.join(output_dir, f"{bpy.data.filepath or 'scene'}.fbx")

        if props.export_format == 'FBX':
            bpy.ops.export_scene.fbx(
                filepath=export_file,
                use_selection=False,
                global_scale=props.ue_scale,
                apply_unit_scale=True,
                axis_forward='-Z',
                axis_up='Y',
                use_mesh_modifiers=props.apply_modifiers,
                mesh_smooth_type='face',
                use_tspace=True,
                use_custom_props=True,
                object_types=self._get_object_types(props),
            )
        elif props.export_format == 'GLTF':
            export_file = export_file.replace('.fbx', '.glb')
            bpy.ops.export_scene.gltf(
                filepath=export_file,
                export_format='GLB',
                export_cameras=props.export_cameras,
                export_lights=props.export_lights,
                export_materials=props.export_materials,
                export_colors=True,
                export_textures=props.export_textures,
                export_skins=props.export_armatures,
                export_animations=props.export_animations,
            )
        elif props.export_format == 'USD':
            export_file = export_file.replace('.fbx', '.usdc')
            try:
                bpy.ops.wm.usd_export(
                    filepath=export_file,
                    export_materials=props.export_materials,
                    export_textures=props.export_textures,
                    export_armatures=props.export_armatures,
                )
            except AttributeError:
                self.report({'WARNING'}, "USD 导出需要 Blender 3.6+")

        self._generate_ue_metadata(output_dir, export_file)
        return {'FINISHED'}

    def _export_to_unity(self, context, output_dir):
        props = context.scene.engine_converter_props
        export_file = os.path.join(output_dir, f"{bpy.data.filepath or 'scene'}.fbx")

        bpy.ops.export_scene.fbx(
            filepath=export_file,
            use_selection=False,
            global_scale=props.unity_scale,
            apply_unit_scale=True,
            axis_forward='-Z',
            axis_up='Y',
            use_mesh_modifiers=props.apply_modifiers,
            object_types=self._get_object_types(props),
        )

        self._generate_unity_metadata(output_dir, export_file)
        return {'FINISHED'}

    def _export_to_godot(self, context, output_dir):
        props = context.scene.engine_converter_props
        export_file = os.path.join(output_dir, f"{bpy.data.filepath or 'scene'}.glb")

        bpy.ops.export_scene.gltf(
            filepath=export_file,
            export_format='GLB',
            export_cameras=props.export_cameras,
            export_lights=props.export_lights,
            export_materials=props.export_materials,
            export_colors=True,
            export_textures=props.export_textures,
            export_skins=props.export_armatures,
            export_animations=props.export_animations,
        )

        if props.project_path and os.path.isdir(props.project_path):
            self._assemble_godot_scene(export_file, props.project_path)

        return {'FINISHED'}

    def _assemble_godot_scene(self, glb_path, godot_project):
        scene_name = Path(glb_path).stem
        assets_dir = os.path.join(godot_project, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        dest_glb = os.path.join(assets_dir, os.path.basename(glb_path))
        if glb_path != dest_glb:
            shutil.copy2(glb_path, dest_glb)

        import hashlib
        def gen_uid(p):
            h = hashlib.sha256(p.encode()).digest()
            chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
            return "uid://" + "".join(chars[b % 62] for b in h[:21])

        rel_path = os.path.relpath(dest_glb, godot_project).replace("\\", "/")
        uid = gen_uid(rel_path)
        scene_uid = gen_uid(f"scene_{scene_name}")
        uid_short = scene_uid[9:]

        tscn_content = f'''[gd_scene load_steps=2 format=3 uid="{scene_uid}"]

[ext_resource type="PackedScene" uid="{uid}" path="res://{rel_path}" id="1_{uid_short}"]

[node name="{scene_name}" type="Node3D"]

[node name="ModelRoot" type="Node3D" parent="."]
'''
        tscn_path = os.path.join(godot_project, f"{scene_name}.tscn")
        with open(tscn_path, "w", encoding="utf-8") as f:
            f.write(tscn_content)

        project_file = os.path.join(godot_project, "project.godot")
        if not os.path.exists(project_file):
            with open(project_file, "w", encoding="utf-8") as f:
                f.write(f'''config_version=5

[application]
config/name="{scene_name}"
run/main_scene="res://{scene_name}.tscn"

[rendering]
renderer/rendering_method="forward_plus"
''')

    def _copy_textures(self, output_dir):
        tex_dir = os.path.join(output_dir, "textures")
        os.makedirs(tex_dir, exist_ok=True)

        for img in bpy.data.images:
            if img.filepath:
                src = bpy.path.abspath(img.filepath)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(tex_dir, os.path.basename(src)))

    def _get_object_types(self, props):
        types = {'MESH'}
        if props.export_armatures:
            types.add('ARMATURE')
        if props.export_cameras:
            types.add('CAMERA')
        if props.export_lights:
            types.add('LIGHT')
        return types

    def _generate_ue_metadata(self, output_dir, export_file):
        meta = {
            "engine": "unreal_engine_5",
            "source": "blender",
            "export_format": Path(export_file).suffix,
            "exported_at": datetime.now().isoformat(),
            "objects": [],
        }
        for obj in bpy.context.scene.objects:
            obj_info = {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "rotation_euler": list(obj.rotation_euler),
                "scale": list(obj.scale),
            }
            if obj.type == 'MESH' and obj.data:
                obj_info["vertex_count"] = len(obj.data.vertices)
                obj_info["face_count"] = len(obj.data.polygons)
            meta["objects"].append(obj_info)

        meta_path = os.path.join(output_dir, "_ue_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _generate_unity_metadata(self, output_dir, export_file):
        meta = {
            "engine": "unity",
            "source": "blender",
            "export_format": Path(export_file).suffix,
            "exported_at": datetime.now().isoformat(),
            "objects": [],
        }
        for obj in bpy.context.scene.objects:
            obj_info = {
                "name": obj.name,
                "type": self._blender_type_to_unity(obj.type),
                "position": {"x": obj.location.x, "y": obj.location.y, "z": obj.location.z},
                "rotation": {
                    "x": obj.rotation_euler.x,
                    "y": obj.rotation_euler.y,
                    "z": obj.rotation_euler.z,
                },
                "scale": {"x": obj.scale.x, "y": obj.scale.y, "z": obj.scale.z},
            }
            meta["objects"].append(obj_info)

        meta_path = os.path.join(output_dir, "_unity_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _blender_type_to_unity(self, blender_type):
        mapping = {
            'MESH': "MeshFilter+MeshRenderer",
            'ARMATURE': "Animator",
            'CAMERA': "Camera",
            'LIGHT': "Light",
            'EMPTY': "GameObject",
            'CURVE': "MeshFilter+MeshRenderer",
        }
        return mapping.get(blender_type, "GameObject")


class ENGINE_CONVERTER_OT_ImportFromEngine(bpy.types.Operator):
    bl_idname = "engine_converter.import"
    bl_label = "Import from Engine"
    bl_description = "从其他引擎导入资产到 Blender"

    def execute(self, context):
        props = context.scene.engine_converter_props
        import_path = props.import_path

        if not import_path or not os.path.isdir(import_path):
            self.report({'ERROR'}, "请设置有效的导入路径")
            return {'CANCELLED'}

        if props.import_source == 'UE':
            self._import_from_ue(import_path)
        elif props.import_source == 'UNITY':
            self._import_from_unity(import_path)
        elif props.import_source == 'GODOT':
            self._import_from_godot(import_path)

        self.report({'INFO'}, f"导入完成")
        return {'FINISHED'}

    def _import_from_ue(self, path):
        for fbx in Path(path).rglob("*.fbx"):
            bpy.ops.import_scene.fbx(filepath=str(fbx))
        for obj in Path(path).rglob("*.obj"):
            bpy.ops.import_scene.obj(filepath=str(obj))
        for gltf in list(Path(path).rglob("*.glb")) + list(Path(path).rglob("*.gltf")):
            bpy.ops.import_scene.gltf(filepath=str(gltf))

    def _import_from_unity(self, path):
        assets = Path(path) / "Assets" if (Path(path) / "Assets").exists() else Path(path)

        for fbx in assets.rglob("*.fbx"):
            bpy.ops.import_scene.fbx(filepath=str(fbx))
        for obj in assets.rglob("*.obj"):
            bpy.ops.import_scene.obj(filepath=str(obj))

    def _import_from_godot(self, path):
        for gltf in list(Path(path).rglob("*.glb")) + list(Path(path).rglob("*.gltf")):
            bpy.ops.import_scene.gltf(filepath=str(gltf))
        for fbx in Path(path).rglob("*.fbx"):
            bpy.ops.import_scene.fbx(filepath=str(fbx))


class ENGINE_CONVERTER_OT_BatchConvert(bpy.types.Operator):
    bl_idname = "engine_converter.batch"
    bl_label = "Batch Convert"
    bl_description = "批量转换目录中的所有模型文件"

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        props = context.scene.engine_converter_props
        output_dir = props.output_path

        if not output_dir:
            self.report({'ERROR'}, "请设置输出路径")
            return {'CANCELLED'}

        source_dir = self.directory
        if not source_dir:
            source_dir = "//"

        source_path = bpy.path.abspath(source_dir)
        converted = 0

        for ext in ["*.fbx", "*.obj", "*.glb", "*.gltf"]:
            for f in Path(source_path).rglob(ext):
                bpy.ops.wm.open_mainfile(filepath=str(f))
                out_file = os.path.join(output_dir, f.stem + ".glb")
                bpy.ops.export_scene.gltf(filepath=out_file, export_format='GLB')
                converted += 1

        self.report({'INFO'}, f"批量转换完成: {converted} 个文件")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ENGINE_CONVERTER_PT_MainPanel(bpy.types.Panel):
    bl_label = "Engine Converter"
    bl_idname = "ENGINE_CONVERTER_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Engine Converter"

    def draw(self, context):
        layout = self.layout
        props = context.scene.engine_converter_props

        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        box.prop(props, "target_engine")
        box.prop(props, "export_format")
        box.prop(props, "output_path")
        box.prop(props, "project_path")

        col = box.column(heading="Export Options")
        col.prop(props, "export_meshes")
        col.prop(props, "export_armatures")
        col.prop(props, "export_animations")
        col.prop(props, "export_materials")
        col.prop(props, "export_textures")
        col.prop(props, "export_cameras")
        col.prop(props, "export_lights")

        col = box.column(heading="Transform")
        col.prop(props, "apply_modifiers")
        col.prop(props, "apply_transform")
        col.prop(props, "triangulate")

        if props.target_engine == 'UNREAL':
            box.prop(props, "ue_scale")
        elif props.target_engine == 'UNITY':
            box.prop(props, "unity_scale")
        elif props.target_engine == 'GODOT':
            box.prop(props, "godot_scale")

        box.operator("engine_converter.export", text="Export", icon='EXPORT')

        layout.separator()

        box = layout.box()
        box.label(text="Import", icon='IMPORT')
        box.prop(props, "import_source")
        box.prop(props, "import_path")
        box.operator("engine_converter.import", text="Import", icon='IMPORT')

        layout.separator()

        box = layout.box()
        box.label(text="Batch", icon='FILE_REFRESH')
        box.operator("engine_converter.batch", text="Batch Convert Folder")


classes = (
    ENGINE_CONVERTER_Properties,
    ENGINE_CONVERTER_OT_ExportToEngine,
    ENGINE_CONVERTER_OT_ImportFromEngine,
    ENGINE_CONVERTER_OT_BatchConvert,
    ENGINE_CONVERTER_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.engine_converter_props = bpy.props.PointerProperty(type=ENGINE_CONVERTER_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.engine_converter_props


if __name__ == "__main__":
    register()
