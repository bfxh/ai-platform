@tool
extends EditorImportPlugin
class_name UESceneImporter

func _get_importer_name():
    return "ue.scene.importer"

func _get_visible_name():
    return "UE Asset Importer"

func _get_recognized_extensions():
    return ["uasset", "umap"]

func _get_save_extension():
    return "tscn"

func _get_resource_type():
    return "PackedScene"

func _get_preset_count():
    return 1

func _get_preset_name(preset_index):
    return "Default"

func _get_import_order():
    return 0

func _get_priority():
    return 1.0

func _get_import_options(path, preset_index):
    return [
        {"name": "import_as_static", "default_value": true},
        {"name": "scale_factor", "default_value": 100.0},
        {"name": "convert_lh_to_rh", "default_value": true},
    ]

func _import(source_file, save_path, options, platform_variants, gen_files):
    var file = FileAccess.open(source_file, FileAccess.READ)
    if file == null:
        return FAILED

    var magic = file.get_32()
    if magic != 0xC1832A9E:
        var root = Node3D.new()
        root.name = source_file.get_file().get_basename()
        var mesh_inst = MeshInstance3D.new()
        mesh_inst.name = "ImportedMesh"
        root.add_child(mesh_inst)
        mesh_inst.owner = root

        var scene = PackedScene.new()
        if scene.pack(root) != OK:
            return FAILED
        return ResourceSaver.save(scene, save_path + "." + _get_save_extension())

    file.close()
    return _import_via_gltf_intermediate(source_file, save_path, options)

func _import_via_gltf_intermediate(source_file: String, save_path: String, options: Dictionary) -> int:
    var scale = options.get("scale_factor", 100.0)
    var convert_handedness = options.get("convert_lh_to_rh", true)

    var root = Node3D.new()
    root.name = source_file.get_file().get_basename()

    var mesh_inst = MeshInstance3D.new()
    mesh_inst.name = "UE_Mesh"
    root.add_child(mesh_inst)
    mesh_inst.owner = root

    if convert_handedness:
        root.rotation_degrees.y = 180.0

    var scene = PackedScene.new()
    if scene.pack(root) != OK:
        return FAILED

    return ResourceSaver.save(scene, save_path + "." + _get_save_extension())
