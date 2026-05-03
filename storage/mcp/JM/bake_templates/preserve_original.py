import bpy
import os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

src = r"{src}"
out_dir = r"{out_dir}"
model_name = "{model_name}"

ext = os.path.splitext(src)[1].lower()

if ext == ".blend":
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    if ext == ".obj":
        try:
            bpy.ops.wm.obj_import(filepath=src)
        except Exception:
            bpy.ops.import_scene.obj(filepath=src)
    elif ext == ".fbx":
        try:
            bpy.ops.wm.fbx_import(filepath=src)
        except Exception:
            bpy.ops.import_scene.fbx(filepath=src)
    elif ext == ".gltf" or ext == ".glb":
        bpy.ops.import_scene.gltf(filepath=src)
    elif ext == ".dae":
        bpy.ops.wm.collada_import(filepath=src)
    elif ext == ".abc":
        bpy.ops.wm.alembic_import(filepath=src)
    elif ext in (".usd", ".usda", ".usdc"):
        bpy.ops.wm.usd_import(filepath=src)
    elif ext == ".stl":
        try:
            bpy.ops.wm.stl_import(filepath=src)
        except Exception:
            bpy.ops.import_mesh.stl(filepath=src)
    elif ext == ".ply":
        bpy.ops.wm.ply_import(filepath=src)
    elif ext == ".3mf":
        try:
            bpy.ops.wm.three_mf_import(filepath=src)
        except Exception:
            print("3MF not supported, skipping")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

for obj in bpy.context.selected_objects:
    if obj.type == 'MESH':
        bpy.context.view_layer.objects.active = obj

        needs_uv = False
        if not obj.data.uv_layers:
            needs_uv = True
        else:
            for uv in obj.data.uv_layers:
                has_coords = False
                for loop in obj.data.loops:
                    co = uv.data[loop.index].uv
                    if co.x != 0.0 or co.y != 0.0:
                        has_coords = True
                        break
                if not has_coords:
                    needs_uv = True
                    break

        if needs_uv:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=1.15)
            bpy.ops.object.mode_set(mode='OBJECT')
            print(f"UV unwrapped: {{obj.name}}")

        bpy.ops.object.shade_smooth()

bpy.ops.object.select_all(action='SELECT')

glb_path = os.path.join(out_dir, model_name + ".glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_materials='EXPORT',
)
print(f"GLB_EXPORTED: {{glb_path}}")

fbx_path = os.path.join(out_dir, model_name + ".fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    mesh_smooth_type='FACE',
    path_mode='COPY',
    embed_textures=True,
)
print(f"FBX_EXPORTED: {{fbx_path}}")

print("ALL_DONE")
