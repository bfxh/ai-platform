import bpy
import os

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

src = r"{src}"
out_dir = r"{out_dir}"
model_name = "{model_name}"
bake_size = {bake_size}

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

has_materials = False
for obj in bpy.context.selected_objects:
    if obj.type == 'MESH' and obj.data.materials:
        for mat in obj.data.materials:
            if mat and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        has_materials = True
                        break

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 1

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

        if not has_materials:
            mat = bpy.data.materials.new(name="AutoGen_" + model_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            output = nodes.new('ShaderNodeOutputMaterial')
            output.location = (800, 0)
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.location = (400, 0)
            principled.inputs['Metallic'].default_value = 0.5
            principled.inputs['Roughness'].default_value = 0.35

            noise1 = nodes.new('ShaderNodeTexNoise')
            noise1.location = (-800, 200)
            noise1.inputs['Scale'].default_value = 20.0
            noise1.inputs['Detail'].default_value = 10.0

            noise2 = nodes.new('ShaderNodeTexNoise')
            noise2.location = (-800, -100)
            noise2.inputs['Scale'].default_value = 8.0
            noise2.inputs['Detail'].default_value = 6.0

            color_ramp = nodes.new('ShaderNodeValToRGB')
            color_ramp.location = (-400, 200)
            color_ramp.color_ramp.elements[0].position = 0.0
            color_ramp.color_ramp.elements[0].color = (0.02, 0.30, 0.60, 1.0)
            color_ramp.color_ramp.elements[1].position = 1.0
            color_ramp.color_ramp.elements[1].color = (0.10, 0.70, 0.90, 1.0)
            elem = color_ramp.color_ramp.elements.new(0.5)
            elem.color = (0.05, 0.50, 0.80, 1.0)

            mix_rgb = nodes.new('ShaderNodeMix')
            mix_rgb.location = (0, 200)
            mix_rgb.data_type = 'RGBA'
            mix_rgb.inputs[0].default_value = 0.3
            mix_rgb.inputs[6].default_value = (0.05, 0.55, 0.85, 1.0)
            mix_rgb.inputs[7].default_value = (0.0, 0.85, 0.70, 1.0)

            rough_ramp = nodes.new('ShaderNodeValToRGB')
            rough_ramp.location = (-400, -100)
            rough_ramp.color_ramp.elements[0].color = (0.15, 0.15, 0.15, 1.0)
            rough_ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1.0)

            bump = nodes.new('ShaderNodeBump')
            bump.location = (0, -300)
            bump.inputs['Strength'].default_value = 0.3

            links.new(noise1.outputs['Fac'], color_ramp.inputs['Fac'])
            links.new(color_ramp.outputs['Color'], mix_rgb.inputs[6])
            links.new(noise2.outputs['Fac'], mix_rgb.inputs[0])
            links.new(mix_rgb.outputs[2], principled.inputs['Base Color'])
            links.new(noise1.outputs['Fac'], rough_ramp.inputs['Fac'])
            links.new(rough_ramp.outputs['Color'], principled.inputs['Roughness'])
            links.new(noise2.outputs['Fac'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], principled.inputs['Normal'])
            links.new(principled.outputs['BSDF'], output.inputs['Surface'])

            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat

            print(f"Auto material applied: {{obj.name}}")

        bpy.ops.object.shade_smooth()

bpy.ops.object.select_all(action='SELECT')

albedo_img = bpy.data.images.new("Bake_Albedo", width=bake_size, height=bake_size)
albedo_img.colorspace_settings.name = 'sRGB'

rough_img = bpy.data.images.new("Bake_Roughness", width=bake_size, height=bake_size)
rough_img.colorspace_settings.name = 'Non-Color'

normal_img = bpy.data.images.new("Bake_Normal", width=bake_size, height=bake_size)
normal_img.colorspace_settings.name = 'Non-Color'

for obj in bpy.context.selected_objects:
    if obj.type == 'MESH' and obj.data.materials:
        mat = obj.data.materials[0]
        if not mat or not mat.use_nodes:
            continue
        nodes = mat.node_tree.nodes

        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.location = (-600, 400)

        tex_node.image = albedo_img
        tex_node.select = True
        nodes.active = tex_node
        try:
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={{'COLOR'}}, width=bake_size, height=bake_size)
            print("Albedo baked!")
        except Exception as e:
            print(f"Albedo bake failed: {{e}}")

        tex_node.image = rough_img
        nodes.active = tex_node
        try:
            bpy.ops.object.bake(type='ROUGHNESS', width=bake_size, height=bake_size)
            print("Roughness baked!")
        except Exception as e:
            print(f"Roughness bake failed: {{e}}")

        tex_node.image = normal_img
        nodes.active = tex_node
        try:
            bpy.ops.object.bake(type='NORMAL', width=bake_size, height=bake_size)
            print("Normal baked!")
        except Exception as e:
            print(f"Normal bake failed: {{e}}")

        nodes.clear()
        output2 = nodes.new('ShaderNodeOutputMaterial')
        output2.location = (400, 0)
        principled2 = nodes.new('ShaderNodeBsdfPrincipled')
        principled2.location = (0, 0)
        principled2.inputs['Metallic'].default_value = 0.5

        tex_albedo = nodes.new('ShaderNodeTexImage')
        tex_albedo.location = (-400, 200)
        tex_albedo.image = albedo_img

        tex_rough = nodes.new('ShaderNodeTexImage')
        tex_rough.location = (-400, 0)
        tex_rough.image = rough_img

        tex_normal = nodes.new('ShaderNodeTexImage')
        tex_normal.location = (-400, -200)
        tex_normal.image = normal_img

        nmap = nodes.new('ShaderNodeNormalMap')
        nmap.location = (0, -200)

        links = mat.node_tree.links
        links.new(tex_albedo.outputs['Color'], principled2.inputs['Base Color'])
        links.new(tex_rough.outputs['Color'], principled2.inputs['Roughness'])
        links.new(tex_normal.outputs['Color'], nmap.inputs['Color'])
        links.new(nmap.outputs['Normal'], principled2.inputs['Normal'])
        links.new(principled2.outputs['BSDF'], output2.inputs['Surface'])

        break

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

albedo_img.filepath_raw = os.path.join(out_dir, model_name + "_Albedo.png")
albedo_img.file_format = 'PNG'
albedo_img.save()
rough_img.filepath_raw = os.path.join(out_dir, model_name + "_Roughness.png")
rough_img.file_format = 'PNG'
rough_img.save()
normal_img.filepath_raw = os.path.join(out_dir, model_name + "_Normal.png")
normal_img.file_format = 'PNG'
normal_img.save()
print("TEXTURES_SAVED")
print("ALL_DONE")
