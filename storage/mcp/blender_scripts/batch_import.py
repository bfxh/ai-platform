import bpy, os

input_dir = "D:/搞阶跃的/Models"
ext = ".glb"
scale = 0.01

for f in os.listdir(input_dir):
    if f.lower().endswith(ext):
        filepath = os.path.join(input_dir, f)
        if ext in ['.glb', '.gltf']:
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext == '.obj':
            bpy.ops.wm.obj_import(filepath=filepath)
        elif ext == '.psk':
            bpy.ops.import_scene.psk(filepath=filepath)
        
        for obj in bpy.context.selected_objects:
            obj.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)
        print(f"Imported: {f}")

print(f"Done! {len(bpy.data.objects)} objects")
