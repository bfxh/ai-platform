@tool
extends EditorImportPlugin
class_name UnitySceneImporter

func _get_importer_name():
    return "unity.scene.importer"

func _get_visible_name():
    return "Unity Scene Importer"

func _get_recognized_extensions():
    return ["unity"]

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
        {"name": "import_cameras", "default_value": true},
        {"name": "import_lights", "default_value": true},
        {"name": "import_physics", "default_value": true},
        {"name": "scale_factor", "default_value": 1.0},
        {"name": "flip_y", "default_value": true},
    ]

func _import(source_file, save_path, options, platform_variants, gen_files):
    var file = FileAccess.open(source_file, FileAccess.READ)
    if file == null:
        return FAILED

    var content = file.get_as_text()
    file.close()

    var game_objects = _parse_unity_yaml(content)
    if game_objects.is_empty():
        return FAILED

    var root = Node3D.new()
    root.name = source_file.get_file().get_basename()

    for go_data in game_objects:
        var node = _create_node_from_unity(go_data, options)
        if node:
            root.add_child(node)
            node.owner = root

    var scene = PackedScene.new()
    if scene.pack(root) != OK:
        return FAILED

    var filename = save_path + "." + _get_save_extension()
    return ResourceSaver.save(scene, filename)

func _parse_unity_yaml(content: String) -> Array:
    var documents = []
    var current_doc = ""
    var lines = content.split("\n")

    for line in lines:
        if line.strip_edges() == "---":
            if current_doc != "":
                documents.append(current_doc)
            current_doc = ""
        else:
            current_doc += line + "\n"

    if current_doc != "":
        documents.append(current_doc)

    var game_objects = []
    for doc in documents:
        var go = _parse_single_document(doc)
        if go.has("m_Name") or go.has("m_Component"):
            game_objects.append(go)

    return game_objects

func _parse_single_document(doc: String) -> Dictionary:
    var result = {}
    var lines = doc.split("\n")
    var current_path = ""
    var indent_stack = [{"path": "", "indent": -1}]

    for line in lines:
        if line.strip_edges() == "":
            continue

        var indent = 0
        var trimmed = line
        while trimmed.begins_with("  "):
            indent += 1
            trimmed = trimmed.substr(2)

        while indent_stack.size() > 1 and indent_stack[-1]["indent"] >= indent:
            indent_stack.pop_back()

        var key_value = trimmed.split(":", 1)
        if key_value.size() == 2:
            var key = key_value[0].strip_edges()
            var value = key_value[1].strip_edges()
            if value != "":
                result[key] = _parse_yaml_value(value)

        if key_value.size() >= 1:
            indent_stack.append({"path": key_value[0].strip_edges(), "indent": indent})

    return result

func _parse_yaml_value(value: String) -> Variant:
    if value == "true":
        return true
    if value == "false":
        return false
    if value.is_valid_int():
        return value.to_int()
    if value.is_valid_float():
        return value.to_float()
    if value.begins_with('"') and value.ends_with('"'):
        return value.substr(1, value.length() - 2)
    if value.begins_with('{') and value.ends_with('}'):
        return _parse_inline_dict(value)
    return value

func _parse_inline_dict(value: String) -> Dictionary:
    var result = {}
    var inner = value.substr(1, value.length() - 2)
    var pairs = inner.split(",")
    for pair in pairs:
        var kv = pair.split(":", 1)
        if kv.size() == 2:
            result[kv[0].strip_edges()] = _parse_yaml_value(kv[1].strip_edges())
    return result

func _create_node_from_unity(go_data: Dictionary, options: Dictionary) -> Node:
    var name = go_data.get("m_Name", "Unnamed")
    var components = go_data.get("m_Component", [])

    var node_type = _determine_node_type(components, options)
    var node = _create_typed_node(node_type)
    node.name = name

    if go_data.has("m_LocalPosition"):
        var pos = go_data["m_LocalPosition"]
        if pos is Dictionary:
            var scale = options.get("scale_factor", 1.0)
            var flip = options.get("flip_y", true)
            var x = float(pos.get("x", 0)) * scale
            var y = float(pos.get("y", 0)) * scale
            var z = float(pos.get("z", 0)) * scale
            if flip:
                node.position = Vector3(x, z, y)
            else:
                node.position = Vector3(x, y, z)

    if go_data.has("m_LocalRotation"):
        var rot = go_data["m_LocalRotation"]
        if rot is Dictionary:
            var qx = float(rot.get("x", 0))
            var qy = float(rot.get("y", 0))
            var qz = float(rot.get("z", 0))
            var qw = float(rot.get("w", 1))
            node.quaternion = Quaternion(qx, qy, qz, qw)

    if go_data.has("m_LocalScale"):
        var sc = go_data["m_LocalScale"]
        if sc is Dictionary:
            node.scale = Vector3(
                float(sc.get("x", 1)),
                float(sc.get("y", 1)),
                float(sc.get("z", 1))
            )

    return node

func _determine_node_type(components: Array, options: Dictionary) -> String:
    var has_camera = false
    var has_light = false
    var has_physics = false
    var has_mesh = false

    for comp in components:
        var comp_str = str(comp).to_lower()
        if "camera" in comp_str:
            has_camera = true
        if "light" in comp_str:
            has_light = true
        if "collider" in comp_str or "rigidbody" in comp_str:
            has_physics = true
        if "mesh" in comp_str or "renderer" in comp_str:
            has_mesh = true

    if has_camera and options.get("import_cameras", true):
        return "Camera3D"
    if has_light and options.get("import_lights", true):
        if "directional" in str(components).to_lower():
            return "DirectionalLight3D"
        if "point" in str(components).to_lower():
            return "OmniLight3D"
        if "spot" in str(components).to_lower():
            return "SpotLight3D"
        return "Light3D"
    if has_physics and options.get("import_physics", true):
        if "rigidbody" in str(components).to_lower():
            return "RigidBody3D"
        return "StaticBody3D"
    if has_mesh:
        return "MeshInstance3D"
    return "Node3D"

func _create_typed_node(type: String) -> Node:
    match type:
        "Camera3D":
            return Camera3D.new()
        "DirectionalLight3D":
            return DirectionalLight3D.new()
        "OmniLight3D":
            return OmniLight3D.new()
        "SpotLight3D":
            return SpotLight3D.new()
        "RigidBody3D":
            return RigidBody3D.new()
        "StaticBody3D":
            return StaticBody3D.new()
        "MeshInstance3D":
            return MeshInstance3D.new()
        "CharacterBody3D":
            return CharacterBody3D.new()
        _:
            return Node3D.new()
