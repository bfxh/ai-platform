@tool
extends EditorImportPlugin
class_name BlenderSceneImporter

func _get_importer_name():
    return "blender.scene.importer"

func _get_visible_name():
    return "Blender Scene Importer"

func _get_recognized_extensions():
    return ["blend"]

func _get_save_extension():
    return "tscn"

func _get_resource_type():
    return "PackedScene"

func _get_preset_count():
    return 2

func _get_preset_name(preset_index):
    match preset_index:
        0: return "Full Scene"
        1: return "Objects Only"
    return "Unknown"

func _get_import_order():
    return 0

func _get_priority():
    return 0.8

func _get_import_options(path, preset_index):
    var options = [
        {"name": "import_cameras", "default_value": true},
        {"name": "import_lights", "default_value": true},
        {"name": "import_armatures", "default_value": true},
        {"name": "import_shapekeys", "default_value": true},
        {"name": "apply_modifiers", "default_value": true},
        {"name": "scale_factor", "default_value": 1.0},
    ]
    if preset_index == 1:
        options.append({"name": "skip_empty", "default_value": true})
    return options

func _import(source_file, save_path, options, platform_variants, gen_files):
    var gltf_path = _convert_blend_to_gltf(source_file)
    if gltf_path == "":
        return _create_placeholder_scene(source_file, save_path)

    var gltf_doc = GLTFDocument.new()
    var gltf_state = GLTFState.new()

    var err = gltf_doc.append_from_file(gltf_path, gltf_state)
    if err != OK:
        return _create_placeholder_scene(source_file, save_path)

    var root = _process_gltf_scene(gltf_doc, gltf_state, options)
    if root == null:
        return FAILED

    var scene = PackedScene.new()
    if scene.pack(root) != OK:
        return FAILED

    return ResourceSaver.save(scene, save_path + "." + _get_save_extension())

func _convert_blend_to_gltf(blend_path: String) -> String:
    var output_path = blend_path.get_basename() + ".glb"

    if FileAccess.file_exists(output_path):
        return output_path

    var blender_exe = _find_blender()
    if blender_exe == "":
        return ""

    var script_content = """
import bpy
bpy.ops.export_scene.gltf(filepath=r"%s", export_format='GLB', use_selection=False)
""" % output_path

    var script_path = OS.get_cache_dir().path_join("blend_convert.py")
    var f = FileAccess.open(script_path, FileAccess.WRITE)
    if f:
        f.store_string(script_content)
        f.close()

    var args = PackedStringArray([
        blender_exe, "--background", "--python", script_path, "--", blend_path
    ])
    var pid = OS.create_process(blender_exe, [
        "--background", blend_path, "--python", script_path
    ])

    var timeout = 30.0
    var elapsed = 0.0
    while not FileAccess.file_exists(output_path) and elapsed < timeout:
        OS.delay_msec(500)
        elapsed += 0.5

    if FileAccess.file_exists(output_path):
        return output_path
    return ""

func _find_blender() -> String:
    var paths = [
        "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
        "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe",
        "C:/Program Files/Blender Foundation/Blender/blender.exe",
    ]
    for p in paths:
        if FileAccess.file_exists(p):
            return p

    var env_path = OS.get_environment("BLENDER_EXECUTABLE")
    if env_path != "" and FileAccess.file_exists(env_path):
        return env_path

    return ""

func _process_gltf_scene(gltf_doc: GLTFDocument, gltf_state: GLTFState, options: Dictionary) -> Node3D:
    var root = gltf_doc.generate_scene(gltf_state)
    if root == null:
        return null

    if not root is Node3D:
        var new_root = Node3D.new()
        new_root.name = root.name
        for child in root.get_children():
            root.remove_child(child)
            new_root.add_child(child)
        root.free()
        root = new_root

    _filter_nodes(root, options)
    _apply_scale(root, options.get("scale_factor", 1.0))

    return root

func _filter_nodes(node: Node, options: Dictionary):
    var to_remove = []
    for child in node.get_children():
        if child is Camera3D and not options.get("import_cameras", true):
            to_remove.append(child)
        elif child is Light3D and not options.get("import_lights", true):
            to_remove.append(child)
        elif child is Skeleton3D and not options.get("import_armatures", true):
            to_remove.append(child)
        else:
            _filter_nodes(child, options)

    for child in to_remove:
        child.queue_free()

func _apply_scale(node: Node3D, scale: float):
    if scale != 1.0:
        node.scale *= scale
    for child in node.get_children():
        if child is Node3D:
            _apply_scale(child, scale)

func _create_placeholder_scene(source_file: String, save_path: String) -> int:
    var root = Node3D.new()
    root.name = source_file.get_file().get_basename()

    var mesh_inst = MeshInstance3D.new()
    mesh_inst.name = "BlenderObject"
    root.add_child(mesh_inst)
    mesh_inst.owner = root

    var scene = PackedScene.new()
    if scene.pack(root) != OK:
        return FAILED
    return ResourceSaver.save(scene, save_path + "." + _get_save_extension())
