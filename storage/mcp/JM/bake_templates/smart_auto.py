import bpy
import os
import glob

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

src = r"{src}"
out_dir = r"{out_dir}"
model_name = "{model_name}"
bake_size = {bake_size}

ext = os.path.splitext(src)[1].lower()
src_dir = os.path.dirname(src)

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
    elif ext in (".gltf", ".glb"):
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
            print("3MF not supported")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 1

def has_image_textures(mat):
    if not mat or not mat.use_nodes:
        return False
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            return True
    return False

def find_companion_textures(obj_name, src_dir):
    textures = {{}}
    if not src_dir or not os.path.isdir(src_dir):
        return textures
    base = os.path.splitext(os.path.basename(src))[0]
    candidates = [base, obj_name, base.replace("_mesh", ""), base.replace(".mesh", "")]
    for c in candidates:
        for tex_ext in [".png", ".jpg", ".jpeg", ".tga", ".bmp", ".hdr"]:
            for prefix in ["", "tex_", "texture_", "diff_", "albedo_", "color_"]:
                for suffix in ["", "_Albedo", "_Color", "_BaseColor", "_Diffuse", "_albedo", "_color", "_D"]:
                    path = os.path.join(src_dir, prefix + c + suffix + tex_ext)
                    if os.path.exists(path) and "albedo" not in textures:
                        textures["albedo"] = path
            for prefix in ["", "tex_", "normal_", "nrm_"]:
                for suffix in ["", "_Normal", "_Nrm", "_normal", "_N"]:
                    path = os.path.join(src_dir, prefix + c + suffix + tex_ext)
                    if os.path.exists(path) and "normal" not in textures:
                        textures["normal"] = path
            for prefix in ["", "tex_", "rough_", "rgh_"]:
                for suffix in ["", "_Roughness", "_Rgh", "_rough", "_R"]:
                    path = os.path.join(src_dir, prefix + c + suffix + tex_ext)
                    if os.path.exists(path) and "roughness" not in textures:
                        textures["roughness"] = path
            for prefix in ["", "tex_", "metal_", "mtl_"]:
                for suffix in ["", "_Metallic", "_Mtl", "_metal", "_M"]:
                    path = os.path.join(src_dir, prefix + c + suffix + tex_ext)
                    if os.path.exists(path) and "metallic" not in textures:
                        textures["metallic"] = path
    return textures

def load_image(path):
    if path and os.path.exists(path):
        try:
            return bpy.data.images.load(path)
        except Exception:
            pass
    return None

def save_and_reload_image(img, filepath):
    img.filepath_raw = filepath
    img.file_format = 'PNG'
    img.save()
    img.reload()
    img.pack()
    return img

def build_baked_material(mat_name, albedo_path, roughness_path=None, normal_path=None, metallic=0.5, roughness_default=0.35):
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (0, 0)
    principled.inputs['Metallic'].default_value = metallic
    principled.inputs['Roughness'].default_value = roughness_default
    
    if albedo_path and os.path.exists(albedo_path):
        albedo_img = bpy.data.images.load(albedo_path)
        albedo_img.colorspace_settings.name = 'sRGB'
        tex_albedo = nodes.new('ShaderNodeTexImage')
        tex_albedo.location = (-400, 200)
        tex_albedo.image = albedo_img
        links.new(tex_albedo.outputs['Color'], principled.inputs['Base Color'])
    
    if roughness_path and os.path.exists(roughness_path):
        rough_img = bpy.data.images.load(roughness_path)
        rough_img.colorspace_settings.name = 'Non-Color'
        tex_rough = nodes.new('ShaderNodeTexImage')
        tex_rough.location = (-400, 0)
        tex_rough.image = rough_img
        links.new(tex_rough.outputs['Color'], principled.inputs['Roughness'])
    
    if normal_path and os.path.exists(normal_path):
        norm_img = bpy.data.images.load(normal_path)
        norm_img.colorspace_settings.name = 'Non-Color'
        tex_normal = nodes.new('ShaderNodeTexImage')
        tex_normal.location = (-400, -200)
        tex_normal.image = norm_img
        nmap = nodes.new('ShaderNodeNormalMap')
        nmap.location = (0, -200)
        links.new(tex_normal.outputs['Color'], nmap.inputs['Color'])
        links.new(nmap.outputs['Normal'], principled.inputs['Normal'])
    
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return mat

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
        
        has_mat = False
        if obj.data.materials:
            for mat in obj.data.materials:
                if mat and has_image_textures(mat):
                    has_mat = True
                    break
        
        if has_mat:
            print(f"KEEP material: {{obj.name}} (has image textures)")
            continue
        
        companion = find_companion_textures(obj.name, src_dir)
        
        if companion:
            print(f"FOUND companion textures for {{obj.name}}: {{list(companion.keys())}}")
            mat = build_baked_material(
                "Auto_" + obj.name,
                companion.get("albedo"),
                companion.get("roughness"),
                companion.get("normal"),
                metallic=0.5,
                roughness_default=0.35,
            )
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
            print(f"APPLIED companion textures: {{obj.name}}")
            continue
        
        has_vertex_colors = False
        if obj.data.color_attributes:
            for ca in obj.data.color_attributes:
                if ca.domain in ('POINT', 'CORNER'):
                    has_vertex_colors = True
                    break
        
        if has_vertex_colors:
            print(f"FOUND vertex colors: {{obj.name}}")
            mat = bpy.data.materials.new(name="VCol_" + obj.name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()
            
            output = nodes.new('ShaderNodeOutputMaterial')
            output.location = (400, 0)
            principled = nodes.new('ShaderNodeBsdfPrincipled')
            principled.location = (0, 0)
            
            vcol = nodes.new('ShaderNodeVertexColor')
            vcol.location = (-400, 200)
            vcol.layer_name = obj.data.color_attributes[0].name
            
            links.new(vcol.outputs['Color'], principled.inputs['Base Color'])
            links.new(principled.outputs['BSDF'], output.inputs['Surface'])
            
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat
            
            albedo_path = os.path.join(out_dir, model_name + "_Albedo.png")
            albedo_img = bpy.data.images.new("Bake_VCol_" + obj.name, width=bake_size, height=bake_size)
            albedo_img.colorspace_settings.name = 'sRGB'
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = albedo_img
            nodes.active = tex_node
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={{'COLOR'}}, width=bake_size, height=bake_size)
            
            albedo_img = save_and_reload_image(albedo_img, albedo_path)
            
            nodes.clear()
            output2 = nodes.new('ShaderNodeOutputMaterial')
            output2.location = (400, 0)
            principled2 = nodes.new('ShaderNodeBsdfPrincipled')
            principled2.location = (0, 0)
            tex_albedo = nodes.new('ShaderNodeTexImage')
            tex_albedo.location = (-400, 200)
            tex_albedo.image = albedo_img
            links.new(tex_albedo.outputs['Color'], principled2.inputs['Base Color'])
            links.new(principled2.outputs['BSDF'], output2.inputs['Surface'])
            
            print(f"BAKED vertex colors: {{obj.name}}")
            continue
        
        print(f"NO material/texture/vcol found, generating color: {{obj.name}}")
        mat = bpy.data.materials.new(name="AutoGen_" + obj.name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        principled.inputs['Metallic'].default_value = 0.5
        principled.inputs['Roughness'].default_value = 0.35
        
        albedo_img = bpy.data.images.new("Albedo_" + obj.name, width=1, height=1)
        albedo_img.colorspace_settings.name = 'sRGB'
        albedo_img.pixels[0] = 0.05
        albedo_img.pixels[1] = 0.55
        albedo_img.pixels[2] = 0.85
        albedo_img.pixels[3] = 1.0
        albedo_img.update()
        albedo_img.pack()
        
        tex_albedo = nodes.new('ShaderNodeTexImage')
        tex_albedo.image = albedo_img
        tex_albedo.location = (-400, 200)
        
        links.new(tex_albedo.outputs['Color'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        
        print(f"APPLIED color material: {{obj.name}}")

bpy.ops.object.select_all(action='SELECT')

glb_path = os.path.join(out_dir, model_name + ".glb")
try:
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        export_texcoords=True,
        export_normals=True,
        export_materials='EXPORT',
        export_cameras=False,
        export_lights=False,
        export_yup=True,
        export_apply=True,
    )
except TypeError:
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
