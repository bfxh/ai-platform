@tool
extends RefCounted

var Serializers = null
var Validators = null

var _plugin: EditorPlugin = null
var _undo_redo: EditorUndoRedoManager = null
var _log_entries: Array = []
var _max_log_entries: int = 1000


func initialize(plugin: EditorPlugin) -> void:
	_plugin = plugin
	_undo_redo = plugin.get_undo_redo()
	
	# Create instances of helper scripts
	var serializers_script = load("res://addons/godotbridge/serializers.gd")
	var validators_script = load("res://addons/godotbridge/validators.gd")
	
	if serializers_script:
		Serializers = serializers_script.new()
	if validators_script:
		Validators = validators_script.new()


func handle(method: String, params: Dictionary):
	var parts = method.split(".")
	if parts.size() != 2:
		return _error(-32601, "Invalid method format")
	
	var category = parts[0]
	var action = parts[1]
	
	match category:
		"project":
			return _handle_project(action, params)
		"editor":
			return _handle_editor(action, params)
		"scene":
			return _handle_scene(action, params)
		"signals":
			return _handle_signals(action, params)
		"filesystem":
			return _handle_filesystem(action, params)
		"play":
			return _handle_play(action, params)
		"resources":
			return _handle_resources(action, params)
		"sprite2d":
			return _handle_sprite2d(action, params)
		"atlas":
			return _handle_atlas(action, params)
		"spriteframes":
			return _handle_spriteframes(action, params)
		"animsprite":
			return _handle_animsprite(action, params)
		"animation":
			return _handle_animation(action, params)
		"animplayer":
			return _handle_animplayer(action, params)
		"tileset":
			return _handle_tileset(action, params)
		"introspect":
			return _handle_introspect(action, params)
		_:
			return _error(-32601, "Unknown category: %s" % category)


# ============================================================================
# PROJECT HANDLERS
# ============================================================================

func _handle_project(action: String, params: Dictionary):
	match action:
		"get_info":
			return _project_get_info()
		"get_autoloads":
			return _project_get_autoloads()
		"get_input_map":
			return _project_get_input_map()
		"add_input_action":
			return _project_add_input_action(params)
		"remove_input_action":
			return _project_remove_input_action(params)
		_:
			return _error(-32601, "Unknown project action: %s" % action)


func _project_get_info() -> Dictionary:
	var config = ConfigFile.new()
	var project_name = "Unknown"
	var main_scene = ""
	var features = []
	
	if config.load("res://project.godot") == OK:
		project_name = config.get_value("application", "config/name", "Unknown")
		main_scene = config.get_value("application", "run/main_scene", "")
		features = config.get_value("application", "config/features", [])
	
	return {
		"name": project_name,
		"godot_version": Engine.get_version_info().get("string", "unknown"),
		"project_path": ProjectSettings.globalize_path("res://"),
		"main_scene": main_scene,
		"features": features
	}


func _project_get_autoloads() -> Array:
	var autoloads = []
	var config = ConfigFile.new()
	
	if config.load("res://project.godot") == OK:
		if config.has_section("autoload"):
			for key in config.get_section_keys("autoload"):
				var value = config.get_value("autoload", key, "")
				autoloads.append({
					"name": key,
					"path": value.trim_prefix("*")
				})
	
	return autoloads


func _project_get_input_map() -> Array:
	var actions = []
	var action_list = InputMap.get_actions()
	
	for action_name in action_list:
		if String(action_name).begins_with("ui_"):
			continue
		
		var events = []
		for event in InputMap.action_get_events(action_name):
			events.append(Serializers.serialize(event))
		
		actions.append({
			"action": String(action_name),
			"events": events
		})
	
	return actions


func _project_add_input_action(params: Dictionary):
	var action_name: String = _get_param_string(params, "action_name")
	var key: String = _get_param_string(params, "key")
	var physical_key: String = _get_param_string(params, "physical_key")
	
	if action_name.is_empty():
		return _error(4001, "Action name cannot be empty")
	
	# Add action if it doesn't exist
	if not InputMap.has_action(action_name):
		InputMap.add_action(action_name)
	
	# Create key event
	if not key.is_empty():
		var event = InputEventKey.new()
		
		# Map common key names to keycodes - FULL alphabet and common keys
		var key_map = {
			# Arrows
			"KEY_UP": KEY_UP, "UP": KEY_UP,
			"KEY_DOWN": KEY_DOWN, "DOWN": KEY_DOWN,
			"KEY_LEFT": KEY_LEFT, "LEFT": KEY_LEFT,
			"KEY_RIGHT": KEY_RIGHT, "RIGHT": KEY_RIGHT,
			# Letters A-Z
			"KEY_A": KEY_A, "A": KEY_A,
			"KEY_B": KEY_B, "B": KEY_B,
			"KEY_C": KEY_C, "C": KEY_C,
			"KEY_D": KEY_D, "D": KEY_D,
			"KEY_E": KEY_E, "E": KEY_E,
			"KEY_F": KEY_F, "F": KEY_F,
			"KEY_G": KEY_G, "G": KEY_G,
			"KEY_H": KEY_H, "H": KEY_H,
			"KEY_I": KEY_I, "I": KEY_I,
			"KEY_J": KEY_J, "J": KEY_J,
			"KEY_K": KEY_K, "K": KEY_K,
			"KEY_L": KEY_L, "L": KEY_L,
			"KEY_M": KEY_M, "M": KEY_M,
			"KEY_N": KEY_N, "N": KEY_N,
			"KEY_O": KEY_O, "O": KEY_O,
			"KEY_P": KEY_P, "P": KEY_P,
			"KEY_Q": KEY_Q, "Q": KEY_Q,
			"KEY_R": KEY_R, "R": KEY_R,
			"KEY_S": KEY_S, "S": KEY_S,
			"KEY_T": KEY_T, "T": KEY_T,
			"KEY_U": KEY_U, "U": KEY_U,
			"KEY_V": KEY_V, "V": KEY_V,
			"KEY_W": KEY_W, "W": KEY_W,
			"KEY_X": KEY_X, "X": KEY_X,
			"KEY_Y": KEY_Y, "Y": KEY_Y,
			"KEY_Z": KEY_Z, "Z": KEY_Z,
			# Numbers
			"KEY_0": KEY_0, "0": KEY_0,
			"KEY_1": KEY_1, "1": KEY_1,
			"KEY_2": KEY_2, "2": KEY_2,
			"KEY_3": KEY_3, "3": KEY_3,
			"KEY_4": KEY_4, "4": KEY_4,
			"KEY_5": KEY_5, "5": KEY_5,
			"KEY_6": KEY_6, "6": KEY_6,
			"KEY_7": KEY_7, "7": KEY_7,
			"KEY_8": KEY_8, "8": KEY_8,
			"KEY_9": KEY_9, "9": KEY_9,
			# Special keys
			"KEY_SPACE": KEY_SPACE, "SPACE": KEY_SPACE,
			"KEY_ENTER": KEY_ENTER, "ENTER": KEY_ENTER, "RETURN": KEY_ENTER,
			"KEY_ESCAPE": KEY_ESCAPE, "ESCAPE": KEY_ESCAPE, "ESC": KEY_ESCAPE,
			"KEY_TAB": KEY_TAB, "TAB": KEY_TAB,
			"KEY_BACKSPACE": KEY_BACKSPACE, "BACKSPACE": KEY_BACKSPACE,
			"KEY_DELETE": KEY_DELETE, "DELETE": KEY_DELETE, "DEL": KEY_DELETE,
			"KEY_INSERT": KEY_INSERT, "INSERT": KEY_INSERT,
			"KEY_HOME": KEY_HOME, "HOME": KEY_HOME,
			"KEY_END": KEY_END, "END": KEY_END,
			"KEY_PAGEUP": KEY_PAGEUP, "PAGEUP": KEY_PAGEUP,
			"KEY_PAGEDOWN": KEY_PAGEDOWN, "PAGEDOWN": KEY_PAGEDOWN,
			# Modifiers
			"KEY_SHIFT": KEY_SHIFT, "SHIFT": KEY_SHIFT,
			"KEY_CTRL": KEY_CTRL, "CTRL": KEY_CTRL, "CONTROL": KEY_CTRL,
			"KEY_ALT": KEY_ALT, "ALT": KEY_ALT,
			# Function keys
			"KEY_F1": KEY_F1, "F1": KEY_F1,
			"KEY_F2": KEY_F2, "F2": KEY_F2,
			"KEY_F3": KEY_F3, "F3": KEY_F3,
			"KEY_F4": KEY_F4, "F4": KEY_F4,
			"KEY_F5": KEY_F5, "F5": KEY_F5,
			"KEY_F6": KEY_F6, "F6": KEY_F6,
			"KEY_F7": KEY_F7, "F7": KEY_F7,
			"KEY_F8": KEY_F8, "F8": KEY_F8,
			"KEY_F9": KEY_F9, "F9": KEY_F9,
			"KEY_F10": KEY_F10, "F10": KEY_F10,
			"KEY_F11": KEY_F11, "F11": KEY_F11,
			"KEY_F12": KEY_F12, "F12": KEY_F12,
		}
		
		var keycode = key_map.get(key.to_upper(), 0)
		if keycode == 0:
			# Try to parse as direct keycode number
			if key.is_valid_int():
				keycode = int(key)
			else:
				return _error(4001, "Unknown key. Use format: KEY_W, W, KEY_SPACE, etc.", {"key": key, "available_keys": ["A-Z", "0-9", "UP/DOWN/LEFT/RIGHT", "SPACE", "ENTER", "ESCAPE", "TAB", "SHIFT", "CTRL", "ALT", "F1-F12"]})
		
		event.keycode = keycode
		InputMap.action_add_event(action_name, event)
	
	# Save to project settings
	var action_data = {
		"deadzone": 0.5,
		"events": []
	}
	for ev in InputMap.action_get_events(action_name):
		action_data["events"].append(ev)
	
	ProjectSettings.set_setting("input/" + action_name, action_data)
	ProjectSettings.save()
	
	return {"ok": true, "action": action_name, "key": key}


func _project_remove_input_action(params: Dictionary):
	var action_name: String = _get_param_string(params, "action_name")
	
	if action_name.is_empty():
		return _error(4001, "Action name cannot be empty")
	
	if not InputMap.has_action(action_name):
		return {"ok": true, "existed": false}
	
	InputMap.erase_action(action_name)
	
	if ProjectSettings.has_setting("input/" + action_name):
		ProjectSettings.set_setting("input/" + action_name, null)
		ProjectSettings.save()
	
	return {"ok": true, "existed": true}


# ============================================================================
# EDITOR HANDLERS
# ============================================================================

func _handle_editor(action: String, params: Dictionary):
	match action:
		"get_state":
			return _editor_get_state()
		"open_scene":
			return _editor_open_scene(params)
		"save_scene":
			return _editor_save_scene(params)
		"save_all":
			return _editor_save_all()
		"get_logs":
			return _editor_get_logs(params)
		"clear_logs":
			return _editor_clear_logs()
		_:
			return _error(-32601, "Unknown editor action: %s" % action)


func _editor_get_state() -> Dictionary:
	var open_scenes = []
	var edited_scene = EditorInterface.get_edited_scene_root()
	var active_scene_path = ""
	
	for i in range(EditorInterface.get_open_scenes().size()):
		open_scenes.append(EditorInterface.get_open_scenes()[i])
	
	if edited_scene != null:
		active_scene_path = edited_scene.scene_file_path
	
	var selection = []
	var editor_selection = EditorInterface.get_selection()
	for node in editor_selection.get_selected_nodes():
		selection.append(String(node.get_path()) if node.is_inside_tree() else node.name)
	
	return {
		"open_scenes": open_scenes,
		"active_scene": active_scene_path,
		"selection": selection
	}


func _editor_open_scene(params: Dictionary):
	var scene_path: String = _get_param_string(params, "scene_path")
	
	var validation = Validators.validate_scene_path(scene_path)
	if not validation.get("ok", false):
		return validation
	
	if not Validators.resource_exists(scene_path):
		return _error(4010, "Scene not found", {"path": scene_path})
	
	EditorInterface.open_scene_from_path(scene_path)
	
	return {"active_scene": scene_path}


func _editor_save_scene(params: Dictionary):
	var scene_path_param = params.get("scene_path")
	var scene_path: String = scene_path_param if scene_path_param != null else ""
	var edited_scene = EditorInterface.get_edited_scene_root()
	
	if edited_scene == null:
		return _error(4010, "No scene currently open")
	
	if scene_path.is_empty():
		scene_path = edited_scene.scene_file_path
	
	if scene_path.is_empty():
		return _error(4001, "Scene has no file path, specify scene_path")
	
	var validation = Validators.validate_scene_path(scene_path)
	if not validation.get("ok", false):
		return validation
	
	EditorInterface.save_scene_as(scene_path)
	
	return {"saved": true, "scene_path": scene_path}


func _editor_save_all():
	EditorInterface.save_all_scenes()
	return {"saved": true}


func _editor_get_logs(params: Dictionary) -> Dictionary:
	var since: float = _get_param_float(params, "since", 0.0)
	var filtered = []
	
	for entry in _log_entries:
		if entry.get("ts", 0.0) >= since:
			filtered.append(entry)
	
	return {"entries": filtered}


func _editor_clear_logs() -> Dictionary:
	_log_entries.clear()
	return {"ok": true}


# ============================================================================
# SCENE HANDLERS
# ============================================================================

func _handle_scene(action: String, params: Dictionary):
	match action:
		"get_tree":
			return _scene_get_tree(params)
		"list_nodes":
			return _scene_list_nodes(params)
		"get_node":
			return _scene_get_node(params)
		"get_node_properties":
			return _scene_get_node_properties(params)
		"set_node_properties":
			return _scene_set_node_properties(params)
		"add_node":
			return _scene_add_node(params)
		"remove_node":
			return _scene_remove_node(params)
		"rename_node":
			return _scene_rename_node(params)
		"reparent_node":
			return _scene_reparent_node(params)
		"duplicate_node":
			return _scene_duplicate_node(params)
		"create_scene":
			return _scene_create_scene(params)
		"assign_script":
			return _scene_assign_script(params)
		"create_mesh":
			return _scene_create_mesh(params)
		"instance_scene":
			return _scene_instance_scene(params)
		_:
			return _error(-32601, "Unknown scene action: %s" % action)


func _get_scene_root() -> Node:
	return EditorInterface.get_edited_scene_root()


## Unified node resolution helper
## Handles all cases: empty path, root name, relative paths, absolute paths
func _resolve_node(path: String) -> Node:
	var root = _get_scene_root()
	if root == null:
		return null
	
	# Empty path or "/" means root
	if path.is_empty() or path == "/" or path == "/root":
		return root
	
	# If path equals root name, return root
	if path == root.name:
		return root
	
	# If path starts with root name + "/", strip it
	var root_prefix = root.name + "/"
	if path.begins_with(root_prefix):
		path = path.substr(root_prefix.length())
	
	# Try to find as relative path from root
	var node = root.get_node_or_null(path)
	if node != null:
		return node
	
	# Try with NodePath conversion (handles edge cases)
	var node_path = NodePath(path)
	node = root.get_node_or_null(node_path)
	
	return node


## Resolve node with parent support (for add_node, create_light, etc.)
func _resolve_parent(path: String) -> Node:
	var root = _get_scene_root()
	if root == null:
		return null
	
	# Empty path means root
	if path.is_empty() or path == "/" or path == "/root":
		return root
	
	return _resolve_node(path)


func _scene_get_tree(params: Dictionary):
	var root = _get_scene_root()
	
	if root == null:
		return _error(4010, "No scene open")
	
	return {"root": _build_tree_recursive(root)}


func _build_tree_recursive(node: Node, depth: int = 0) -> Dictionary:
	if depth > 20:
		return {"name": node.name, "type": node.get_class(), "truncated": true}
	
	var result = Serializers.serialize_node_summary(node)
	
	if node.get_child_count() > 0:
		var children = []
		for child in node.get_children():
			children.append(_build_tree_recursive(child, depth + 1))
		result["children"] = children
	
	return result


func _scene_list_nodes(params: Dictionary):
	var parent_path: String = _get_param_string(params, "parent_path")
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var parent = _resolve_parent(parent_path)
	if parent == null:
		return _error(4010, "Parent node not found", {"path": parent_path})
	
	var nodes = []
	for child in parent.get_children():
		nodes.append(Serializers.serialize_node_summary(child))
	
	return nodes


func _scene_get_node(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var result = Serializers.serialize_node_summary(node)
	result["properties_summary"] = _get_important_properties(node)
	
	return result


func _get_important_properties(node: Node) -> Dictionary:
	var summary = {}
	
	if "visible" in node:
		summary["visible"] = node.visible
	
	if node is Control:
		summary["size"] = Serializers.serialize(node.size)
		summary["position"] = Serializers.serialize(node.position)
		if "text" in node:
			summary["text"] = node.text
	
	if node is Node2D:
		summary["position"] = Serializers.serialize(node.position)
		summary["rotation"] = node.rotation
		summary["scale"] = Serializers.serialize(node.scale)
	
	if node is Node3D:
		summary["position"] = Serializers.serialize(node.position)
		summary["rotation"] = Serializers.serialize(node.rotation)
		summary["scale"] = Serializers.serialize(node.scale)
	
	return summary


func _scene_get_node_properties(params: Dictionary):
	var node_path: String = params.get("node_path", "")
	var keys_param = params.get("keys")
	var keys: Array = keys_param if keys_param != null else []
	
	if node_path.is_empty():
		return _error(4001, "Node path cannot be empty")
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})

	if Serializers == null:
		return _error(5000, "Serializers not initialized")
	
	var properties: Dictionary = Serializers.serialize_node_properties(node, keys)
	
	return {"node_path": node_path, "node_type": node.get_class(), "properties": properties}


func _scene_set_node_properties(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var properties: Dictionary = _get_param_dict(params, "properties")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var prop_validation = Validators.validate_properties(properties, node)
	if not prop_validation.get("ok", false):
		return prop_validation
	
	var applied = []
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Set Node Properties")
		
		for key in properties:
			var old_value = node.get(key)
			var new_value = Serializers.deserialize(properties[key])
			_undo_redo.add_do_property(node, key, new_value)
			_undo_redo.add_undo_property(node, key, old_value)
			applied.append(key)
		
		_undo_redo.commit_action()
	else:
		for key in properties:
			var new_value = Serializers.deserialize(properties[key])
			node.set(key, new_value)
			applied.append(key)
	
	return {"ok": true, "applied": applied}


func _scene_add_node(params: Dictionary):
	var parent_path: String = _get_param_string(params, "parent_path")
	var type_name: String = _get_param_string(params, "type")
	var node_name: String = _get_param_string(params, "name")
	var properties: Dictionary = _get_param_dict(params, "properties")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var type_validation = Validators.validate_node_type(type_name)
	if not type_validation.get("ok", false):
		return type_validation
	
	var name_validation = Validators.validate_node_name(node_name)
	if not name_validation.get("ok", false):
		return name_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var parent = _resolve_parent(parent_path)
	if parent == null:
		return _error(4010, "Parent node not found", {"path": parent_path})
	
	var new_node = ClassDB.instantiate(type_name)
	if new_node == null:
		return _error(5000, "Failed to instantiate node", {"type": type_name})
	
	new_node.name = node_name
	
	for key in properties:
		if key in new_node:
			new_node.set(key, Serializers.deserialize(properties[key]))
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Add Node: %s" % node_name)
		_undo_redo.add_do_method(parent, "add_child", new_node, true)
		_undo_redo.add_do_method(new_node, "set_owner", root)
		_undo_redo.add_do_reference(new_node)
		_undo_redo.add_undo_method(parent, "remove_child", new_node)
		_undo_redo.commit_action()
	else:
		parent.add_child(new_node, true)
		new_node.owner = root
	
	var new_path = String(new_node.get_path()) if new_node.is_inside_tree() else ""
	
	return {"node_path": new_path, "name": new_node.name}


func _scene_remove_node(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	if node == root:
		return _error(4030, "Cannot remove root node")
	
	var parent = node.get_parent()
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Remove Node: %s" % node.name)
		_undo_redo.add_do_method(parent, "remove_child", node)
		_undo_redo.add_undo_method(parent, "add_child", node, true)
		_undo_redo.add_undo_method(node, "set_owner", root)
		_undo_redo.add_undo_reference(node)
		_undo_redo.commit_action()
	else:
		parent.remove_child(node)
		node.queue_free()
	
	return {"ok": true}


func _scene_rename_node(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var new_name: String = _get_param_string(params, "new_name")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var path_validation = Validators.validate_node_path(node_path)
	if not path_validation.get("ok", false):
		return path_validation
	
	var name_validation = Validators.validate_node_name(new_name)
	if not name_validation.get("ok", false):
		return name_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var old_name = node.name
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Rename Node: %s -> %s" % [old_name, new_name])
		_undo_redo.add_do_property(node, "name", new_name)
		_undo_redo.add_undo_property(node, "name", old_name)
		_undo_redo.commit_action()
	else:
		node.name = new_name
	
	var new_path = String(node.get_path()) if node.is_inside_tree() else ""
	
	return {"new_path": new_path}


func _scene_reparent_node(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var new_parent_path: String = _get_param_string(params, "new_parent_path")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var new_parent = _resolve_parent(new_parent_path)
	if new_parent == null:
		return _error(4010, "New parent node not found", {"path": new_parent_path})
	
	if node == root:
		return _error(4030, "Cannot reparent root node")
	
	var old_parent = node.get_parent()
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Reparent Node: %s" % node.name)
		_undo_redo.add_do_method(node, "reparent", new_parent)
		_undo_redo.add_undo_method(node, "reparent", old_parent)
		_undo_redo.commit_action()
	else:
		node.reparent(new_parent)
	
	var new_path = String(node.get_path()) if node.is_inside_tree() else ""
	
	return {"new_path": new_path}


func _scene_duplicate_node(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var new_name: String = _get_param_string(params, "new_name")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var duplicate = node.duplicate()
	if duplicate == null:
		return _error(5000, "Failed to duplicate node")
	
	if not new_name.is_empty():
		duplicate.name = new_name
	
	var parent = node.get_parent()
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Duplicate Node: %s" % node.name)
		_undo_redo.add_do_method(parent, "add_child", duplicate, true)
		_undo_redo.add_do_method(duplicate, "set_owner", root)
		_undo_redo.add_do_reference(duplicate)
		_undo_redo.add_undo_method(parent, "remove_child", duplicate)
		_undo_redo.commit_action()
	else:
		parent.add_child(duplicate, true)
		duplicate.owner = root
	
	var new_path = String(duplicate.get_path()) if duplicate.is_inside_tree() else ""
	
	return {"new_path": new_path}


func _scene_create_scene(params: Dictionary):
	var root_type: String = _get_param_string(params, "root_type", "Node3D")
	var root_name: String = _get_param_string(params, "root_name", "Root")
	var scene_path: String = _get_param_string(params, "scene_path")
	
	# Validate root type
	var type_validation = Validators.validate_node_type(root_type)
	if not type_validation.get("ok", false):
		return type_validation
	
	# Create new root node
	var new_root = ClassDB.instantiate(root_type)
	if new_root == null:
		return _error(5000, "Failed to create root node", {"type": root_type})
	
	new_root.name = root_name
	
	# Create packed scene
	var packed_scene = PackedScene.new()
	var err = packed_scene.pack(new_root)
	if err != OK:
		new_root.queue_free()
		return _error(5000, "Failed to pack scene")
	
	# Save if path provided
	if not scene_path.is_empty():
		var path_validation = Validators.validate_scene_path(scene_path)
		if not path_validation.get("ok", false):
			new_root.queue_free()
			return path_validation
		
		err = ResourceSaver.save(packed_scene, scene_path)
		if err != OK:
			new_root.queue_free()
			return _error(5000, "Failed to save scene", {"path": scene_path})
		
		EditorInterface.get_resource_filesystem().scan()
		EditorInterface.open_scene_from_path(scene_path)
	else:
		# Open as new unsaved scene
		EditorInterface.edit_resource(packed_scene)
	
	new_root.queue_free()
	return {"ok": true, "scene_path": scene_path, "root_type": root_type}


func _scene_assign_script(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var script_path: String = _get_param_string(params, "script_path")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	# Load or create script
	var script = null
	if not script_path.is_empty():
		if Validators.file_exists(script_path):
			script = load(script_path)
		else:
			return _error(4010, "Script not found", {"path": script_path})
	
	var old_script = node.get_script()
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Assign Script to %s" % node.name)
		_undo_redo.add_do_method(node, "set_script", script)
		_undo_redo.add_undo_method(node, "set_script", old_script)
		_undo_redo.commit_action()
	else:
		node.set_script(script)
	
	return {"ok": true, "node_path": node_path, "script_path": script_path}


func _scene_create_mesh(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var mesh_type: String = _get_param_string(params, "mesh_type", "BoxMesh")
	var mesh_params: Dictionary = _get_param_dict(params, "mesh_params")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	if not (node is MeshInstance3D or node is MeshInstance2D):
		return _error(4002, "Node must be MeshInstance3D or MeshInstance2D", {"node_type": node.get_class()})
	
	# Create mesh resource
	var mesh = null
	match mesh_type:
		"BoxMesh":
			mesh = BoxMesh.new()
			if mesh_params.has("size"):
				var s = mesh_params.get("size")
				mesh.size = Vector3(s.get("x", 1), s.get("y", 1), s.get("z", 1))
		"SphereMesh":
			mesh = SphereMesh.new()
			if mesh_params.has("radius"):
				mesh.radius = mesh_params.get("radius")
			if mesh_params.has("height"):
				mesh.height = mesh_params.get("height")
		"CylinderMesh":
			mesh = CylinderMesh.new()
			if mesh_params.has("top_radius"):
				mesh.top_radius = mesh_params.get("top_radius")
			if mesh_params.has("bottom_radius"):
				mesh.bottom_radius = mesh_params.get("bottom_radius")
			if mesh_params.has("height"):
				mesh.height = mesh_params.get("height")
		"PlaneMesh":
			mesh = PlaneMesh.new()
			if mesh_params.has("size"):
				var s = mesh_params.get("size")
				mesh.size = Vector2(s.get("x", 1), s.get("y", 1))
		"CapsuleMesh":
			mesh = CapsuleMesh.new()
			if mesh_params.has("radius"):
				mesh.radius = mesh_params.get("radius")
			if mesh_params.has("height"):
				mesh.height = mesh_params.get("height")
		"QuadMesh":
			mesh = QuadMesh.new()
			if mesh_params.has("size"):
				var s = mesh_params.get("size")
				mesh.size = Vector2(s.get("x", 1), s.get("y", 1))
		_:
			return _error(4002, "Unknown mesh type", {"mesh_type": mesh_type})
	
	var old_mesh = node.mesh
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Set Mesh on %s" % node.name)
		_undo_redo.add_do_property(node, "mesh", mesh)
		_undo_redo.add_undo_property(node, "mesh", old_mesh)
		_undo_redo.commit_action()
	else:
		node.mesh = mesh
	
	return {"ok": true, "mesh_type": mesh_type}


func _scene_instance_scene(params: Dictionary):
	var parent_path: String = _get_param_string(params, "parent_path")
	var scene_path: String = _get_param_string(params, "scene_path")
	var instance_name: String = _get_param_string(params, "name")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var scene_validation = Validators.validate_scene_path(scene_path)
	if not scene_validation.get("ok", false):
		return scene_validation
	
	if not Validators.resource_exists(scene_path):
		return _error(4010, "Scene not found", {"path": scene_path})
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var parent = _resolve_parent(parent_path)
	if parent == null:
		return _error(4010, "Parent node not found", {"path": parent_path})
	
	var packed_scene = load(scene_path)
	if packed_scene == null:
		return _error(5000, "Failed to load scene", {"path": scene_path})
	
	var instance = packed_scene.instantiate()
	if instance == null:
		return _error(5000, "Failed to instantiate scene")
	
	if not instance_name.is_empty():
		instance.name = instance_name
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Instance Scene: %s" % scene_path.get_file())
		_undo_redo.add_do_method(parent, "add_child", instance, true)
		_undo_redo.add_do_method(instance, "set_owner", root)
		_undo_redo.add_do_reference(instance)
		_undo_redo.add_undo_method(parent, "remove_child", instance)
		_undo_redo.commit_action()
	else:
		parent.add_child(instance, true)
		instance.owner = root
	
	var new_path = String(instance.get_path()) if instance.is_inside_tree() else ""
	
	return {"ok": true, "node_path": new_path}


# ============================================================================
# SIGNALS HANDLERS
# ============================================================================

func _handle_signals(action: String, params: Dictionary):
	match action:
		"list":
			return _signals_list(params)
		"list_connections":
			return _signals_list_connections(params)
		"connect":
			return _signals_connect(params)
		"disconnect":
			return _signals_disconnect(params)
		_:
			return _error(-32601, "Unknown signals action: %s" % action)


func _signals_list(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var signals = []
	for sig in node.get_signal_list():
		var args = []
		for arg in sig.get("args", []):
			args.append({
				"name": arg.get("name", ""),
				"type": arg.get("type", 0)
			})
		signals.append({
			"name": sig.get("name", ""),
			"args": args
		})
	
	return signals


func _signals_list_connections(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	var validation = Validators.validate_node_path(node_path)
	if not validation.get("ok", false):
		return validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var connections = []
	
	for sig in node.get_signal_list():
		var sig_name = sig.get("name", "")
		for conn in node.get_signal_connection_list(sig_name):
			var target = conn.get("callable").get_object()
			var target_path = ""
			if target is Node and target.is_inside_tree():
				target_path = String(target.get_path())
			connections.append({
				"signal": sig_name,
				"target_path": target_path,
				"method": String(conn.get("callable").get_method()),
				"flags": conn.get("flags", 0)
			})
	
	return connections


func _signals_connect(params: Dictionary):
	var from_path: String = _get_param_string(params, "from_path")
	var signal_name: String = _get_param_string(params, "signal")
	var to_path: String = _get_param_string(params, "to_path")
	var method_name: String = _get_param_string(params, "method")
	var flags: int = _get_param_int(params, "flags", 0)
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var from_validation = Validators.validate_node_path(from_path)
	if not from_validation.get("ok", false):
		return from_validation
	
	var to_validation = Validators.validate_node_path(to_path)
	if not to_validation.get("ok", false):
		return to_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var from_node = _resolve_node(from_path)
	if from_node == null:
		return _error(4010, "Source node not found", {"path": from_path})
	
	var to_node = _resolve_node(to_path)
	if to_node == null:
		return _error(4010, "Target node not found", {"path": to_path})
	
	var signal_validation = Validators.validate_signal(from_node, signal_name)
	if not signal_validation.get("ok", false):
		return signal_validation
	
	if from_node.is_connected(signal_name, Callable(to_node, method_name)):
		return {"ok": true, "already_connected": true}
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Connect Signal")
		_undo_redo.add_do_method(from_node, "connect", signal_name, Callable(to_node, method_name), flags)
		_undo_redo.add_undo_method(from_node, "disconnect", signal_name, Callable(to_node, method_name))
		_undo_redo.commit_action()
	else:
		from_node.connect(signal_name, Callable(to_node, method_name), flags)
	
	return {"ok": true}


func _signals_disconnect(params: Dictionary):
	var from_path: String = _get_param_string(params, "from_path")
	var signal_name: String = _get_param_string(params, "signal")
	var to_path: String = _get_param_string(params, "to_path")
	var method_name: String = _get_param_string(params, "method")
	var use_undo: bool = _get_param_bool(params, "use_undo", true)
	
	var from_validation = Validators.validate_node_path(from_path)
	if not from_validation.get("ok", false):
		return from_validation
	
	var to_validation = Validators.validate_node_path(to_path)
	if not to_validation.get("ok", false):
		return to_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var from_node = _resolve_node(from_path)
	if from_node == null:
		return _error(4010, "Source node not found", {"path": from_path})
	
	var to_node = _resolve_node(to_path)
	if to_node == null:
		return _error(4010, "Target node not found", {"path": to_path})
	
	if not from_node.is_connected(signal_name, Callable(to_node, method_name)):
		return {"ok": true, "was_connected": false}
	
	if use_undo and _undo_redo != null:
		_undo_redo.create_action("Disconnect Signal")
		_undo_redo.add_do_method(from_node, "disconnect", signal_name, Callable(to_node, method_name))
		_undo_redo.add_undo_method(from_node, "connect", signal_name, Callable(to_node, method_name))
		_undo_redo.commit_action()
	else:
		from_node.disconnect(signal_name, Callable(to_node, method_name))
	
	return {"ok": true}


# ============================================================================
# FILESYSTEM HANDLERS
# ============================================================================

func _handle_filesystem(action: String, params: Dictionary):
	match action:
		"search":
			return _filesystem_search(params)
		"read_text":
			return _filesystem_read_text(params)
		"write_text":
			return _filesystem_write_text(params)
		"create_folder":
			return _filesystem_create_folder(params)
		"delete":
			return _filesystem_delete(params)
		"refresh":
			return _filesystem_refresh()
		_:
			return _error(-32601, "Unknown filesystem action: %s" % action)


func _filesystem_search(params: Dictionary):
	var query: String = _get_param_string(params, "query")
	var type_filter: String = _get_param_string(params, "type")
	var folder: String = _get_param_string(params, "folder", "res://")
	var limit: int = _get_param_int(params, "limit", 100)
	
	var folder_validation = Validators.validate_res_path(folder)
	if not folder_validation.get("ok", false):
		return folder_validation
	
	var results = []
	_search_recursive(folder, query, type_filter, results, limit)
	
	return results


func _search_recursive(path: String, query: String, type_filter: String, results: Array, limit: int) -> void:
	if results.size() >= limit:
		return
	
	var dir = DirAccess.open(path)
	if dir == null:
		return
	
	dir.list_dir_begin()
	var file_name = dir.get_next()
	
	while file_name != "" and results.size() < limit:
		if file_name.begins_with("."):
			file_name = dir.get_next()
			continue
		
		var full_path = path.path_join(file_name)
		
		if dir.current_is_dir():
			_search_recursive(full_path, query, type_filter, results, limit)
		else:
			var matches_query = query.is_empty() or file_name.containsn(query)
			var matches_type = type_filter.is_empty() or file_name.ends_with("." + type_filter)
			
			if matches_query and matches_type:
				results.append({
					"path": full_path,
					"type": file_name.get_extension(),
					"name": file_name
				})
		
		file_name = dir.get_next()
	
	dir.list_dir_end()


func _filesystem_read_text(params: Dictionary):
	var path: String = _get_param_string(params, "path")
	
	var validation = Validators.validate_file_path(path, true)
	if not validation.get("ok", false):
		return validation
	
	if not Validators.file_exists(path):
		return _error(4010, "File not found", {"path": path})
	
	var file = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return _error(5000, "Failed to open file", {"path": path})
	
	var content = file.get_as_text()
	file.close()
	
	return {"content": content}


func _filesystem_write_text(params: Dictionary):
	var path: String = _get_param_string(params, "path")
	var content: String = _get_param_string(params, "content")
	var create_dirs: bool = _get_param_bool(params, "create_dirs", false)
	
	var validation = Validators.validate_file_path(path, false)
	if not validation.get("ok", false):
		return validation
	
	if create_dirs:
		var dir_path = path.get_base_dir()
		if not Validators.dir_exists(dir_path):
			var err = DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir_path))
			if err != OK:
				return _error(5000, "Failed to create directories", {"path": dir_path})
	
	var file = FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return _error(5000, "Failed to open file for writing", {"path": path})
	
	file.store_string(content)
	file.close()
	
	EditorInterface.get_resource_filesystem().scan()
	
	return {"ok": true}


func _filesystem_create_folder(params: Dictionary):
	var path: String = _get_param_string(params, "path")
	
	var validation = Validators.validate_res_path(path)
	if not validation.get("ok", false):
		return validation
	
	var err = DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path))
	if err != OK:
		return _error(5000, "Failed to create folder", {"path": path})
	
	EditorInterface.get_resource_filesystem().scan()
	
	return {"ok": true}


func _filesystem_delete(params: Dictionary):
	var path: String = _get_param_string(params, "path")
	var use_trash: bool = _get_param_bool(params, "use_trash", true)
	
	var validation = Validators.validate_res_path(path)
	if not validation.get("ok", false):
		return validation
	
	var global_path = ProjectSettings.globalize_path(path)
	
	if use_trash:
		var err = OS.move_to_trash(global_path)
		if err != OK:
			return _error(5000, "Failed to move to trash", {"path": path})
	else:
		var err = DirAccess.remove_absolute(global_path)
		if err != OK:
			return _error(5000, "Failed to delete", {"path": path})
	
	EditorInterface.get_resource_filesystem().scan()
	
	return {"ok": true}


func _filesystem_refresh():
	EditorInterface.get_resource_filesystem().scan()
	return {"ok": true}


# ============================================================================
# PLAY HANDLERS
# ============================================================================

func _handle_play(action: String, params: Dictionary):
	match action:
		"run_main":
			return _play_run_main()
		"run_current":
			return _play_run_current()
		"stop":
			return _play_stop()
		"get_state":
			return _play_get_state()
		_:
			return _error(-32601, "Unknown play action: %s" % action)


func _play_run_main():
	EditorInterface.play_main_scene()
	return {"ok": true}


func _play_run_current():
	EditorInterface.play_current_scene()
	return {"ok": true}


func _play_stop():
	EditorInterface.stop_playing_scene()
	return {"ok": true}


func _play_get_state() -> Dictionary:
	var is_playing = EditorInterface.is_playing_scene()
	return {"running": is_playing}


# ============================================================================
# RESOURCES HANDLERS (Materials, Textures, Collision, etc.)
# ============================================================================

func _handle_resources(action: String, params: Dictionary):
	match action:
		"create_material":
			return _resources_create_material(params)
		"set_material":
			return _resources_set_material(params)
		"load_texture":
			return _resources_load_texture(params)
		"set_sprite_texture":
			return _resources_set_sprite_texture(params)
		"create_collision_shape":
			return _resources_create_collision_shape(params)
		"set_modulate":
			return _resources_set_modulate(params)
		"create_light":
			return _resources_create_light(params)
		"configure_camera":
			return _resources_configure_camera(params)
		"create_environment":
			return _resources_create_environment(params)
		"create_audio_player":
			return _resources_create_audio_player(params)
		_:
			return _error(-32601, "Unknown resources action: %s" % action)


func _resources_create_material(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var material_type: String = _get_param_string(params, "material_type", "StandardMaterial3D")
	var properties: Dictionary = _get_param_dict(params, "properties")
	var surface_index: int = _get_param_int(params, "surface_index", 0)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var material = null
	match material_type:
		"StandardMaterial3D":
			material = StandardMaterial3D.new()
			if properties.has("albedo_color"):
				var c = properties.get("albedo_color")
				material.albedo_color = Color(c.get("r", 1), c.get("g", 1), c.get("b", 1), c.get("a", 1))
			if properties.has("metallic"):
				material.metallic = properties.get("metallic")
			if properties.has("roughness"):
				material.roughness = properties.get("roughness")
			if properties.has("emission_enabled"):
				material.emission_enabled = properties.get("emission_enabled")
			if properties.has("emission"):
				var e = properties.get("emission")
				material.emission = Color(e.get("r", 0), e.get("g", 0), e.get("b", 0))
			if properties.has("emission_energy"):
				material.emission_energy_multiplier = properties.get("emission_energy")
		"CanvasItemMaterial":
			material = CanvasItemMaterial.new()
		_:
			return _error(4002, "Unknown material type", {"material_type": material_type})
	
	# Apply material based on node type
	if node is MeshInstance3D:
		node.set_surface_override_material(surface_index, material)
	elif node is CSGShape3D:
		node.material = material
	elif node is GeometryInstance3D:
		node.material_override = material
	elif node is CanvasItem:
		node.material = material
	else:
		return _error(4002, "Node type doesn't support materials", {"node_type": node.get_class()})
	
	return {"ok": true, "material_type": material_type}


func _resources_set_material(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var material_path: String = _get_param_string(params, "material_path")
	var surface_index: int = _get_param_int(params, "surface_index", 0)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var material = load(material_path)
	if material == null:
		return _error(4010, "Material not found", {"path": material_path})
	
	if node is MeshInstance3D:
		node.set_surface_override_material(surface_index, material)
	elif node is GeometryInstance3D:
		node.material_override = material
	elif node is CanvasItem:
		node.material = material
	else:
		return _error(4002, "Node type doesn't support materials")
	
	return {"ok": true}


func _resources_load_texture(params: Dictionary):
	var path: String = _get_param_string(params, "path")
	
	if not Validators.resource_exists(path):
		return _error(4010, "Texture not found", {"path": path})
	
	var texture = load(path)
	if texture == null or not (texture is Texture2D):
		return _error(4002, "Invalid texture file", {"path": path})
	
	return {
		"ok": true,
		"path": path,
		"size": {"width": texture.get_width(), "height": texture.get_height()}
	}


func _resources_set_sprite_texture(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var texture_path: String = _get_param_string(params, "texture_path")
	var region_enabled: bool = _get_param_bool(params, "region_enabled", false)
	var region_rect = params.get("region_rect")  # Can be null or dict
	var hframes: int = _get_param_int(params, "hframes", 1)
	var vframes: int = _get_param_int(params, "vframes", 1)
	var frame: int = _get_param_int(params, "frame", 0)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	if not (node is Sprite2D or node is Sprite3D):
		return _error(4002, "Node must be Sprite2D or Sprite3D", {"node_type": node.get_class()})
	
	# Load and set texture
	if not texture_path.is_empty():
		var texture = load(texture_path)
		if texture == null:
			return _error(4010, "Texture not found", {"path": texture_path})
		node.texture = texture
	
	# Configure sprite properties
	if node is Sprite2D:
		node.region_enabled = region_enabled
		if region_rect != null:
			node.region_rect = Rect2(
				region_rect.get("x", 0),
				region_rect.get("y", 0),
				region_rect.get("w", 0),
				region_rect.get("h", 0)
			)
		node.hframes = hframes
		node.vframes = vframes
		node.frame = frame
	
	return {"ok": true}


func _resources_create_collision_shape(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var shape_type: String = _get_param_string(params, "shape_type", "BoxShape3D")
	var shape_params: Dictionary = _get_param_dict(params, "shape_params")
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var shape = null
	
	# 3D Shapes
	match shape_type:
		"BoxShape3D":
			shape = BoxShape3D.new()
			if shape_params.has("size"):
				var s = shape_params.get("size")
				shape.size = Vector3(s.get("x", 1), s.get("y", 1), s.get("z", 1))
		"SphereShape3D":
			shape = SphereShape3D.new()
			if shape_params.has("radius"):
				shape.radius = shape_params.get("radius")
		"CapsuleShape3D":
			shape = CapsuleShape3D.new()
			if shape_params.has("radius"):
				shape.radius = shape_params.get("radius")
			if shape_params.has("height"):
				shape.height = shape_params.get("height")
		"CylinderShape3D":
			shape = CylinderShape3D.new()
			if shape_params.has("radius"):
				shape.radius = shape_params.get("radius")
			if shape_params.has("height"):
				shape.height = shape_params.get("height")
		# 2D Shapes
		"RectangleShape2D":
			shape = RectangleShape2D.new()
			if shape_params.has("size"):
				var s = shape_params.get("size")
				shape.size = Vector2(s.get("x", 1), s.get("y", 1))
		"CircleShape2D":
			shape = CircleShape2D.new()
			if shape_params.has("radius"):
				shape.radius = shape_params.get("radius")
		"CapsuleShape2D":
			shape = CapsuleShape2D.new()
			if shape_params.has("radius"):
				shape.radius = shape_params.get("radius")
			if shape_params.has("height"):
				shape.height = shape_params.get("height")
		_:
			return _error(4002, "Unknown shape type", {"shape_type": shape_type})
	
	# Apply to CollisionShape node
	if node is CollisionShape3D or node is CollisionShape2D:
		node.shape = shape
	else:
		return _error(4002, "Node must be CollisionShape2D or CollisionShape3D")
	
	return {"ok": true, "shape_type": shape_type}


func _resources_set_modulate(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var color: Dictionary = _get_param_dict(params, "color")
	var self_modulate: bool = _get_param_bool(params, "self_modulate", false)
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var c = Color(
		color.get("r", 1),
		color.get("g", 1),
		color.get("b", 1),
		color.get("a", 1)
	)
	
	if node is CanvasItem:
		if self_modulate:
			node.self_modulate = c
		else:
			node.modulate = c
	elif node is Node3D and "modulate" in node:
		node.modulate = c
	else:
		return _error(4002, "Node doesn't support modulate")
	
	return {"ok": true}


func _resources_create_light(params: Dictionary):
	var parent_path: String = _get_param_string(params, "parent_path")
	var light_type: String = _get_param_string(params, "light_type", "DirectionalLight3D")
	var light_name: String = _get_param_string(params, "name", "Light")
	var properties: Dictionary = _get_param_dict(params, "properties")
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var parent = _resolve_parent(parent_path)
	if parent == null:
		return _error(4010, "Parent node not found", {"path": parent_path})
	
	var light = null
	match light_type:
		"DirectionalLight3D":
			light = DirectionalLight3D.new()
		"OmniLight3D":
			light = OmniLight3D.new()
			if properties.has("omni_range"):
				light.omni_range = properties.get("omni_range")
		"SpotLight3D":
			light = SpotLight3D.new()
			if properties.has("spot_range"):
				light.spot_range = properties.get("spot_range")
			if properties.has("spot_angle"):
				light.spot_angle = properties.get("spot_angle")
		"PointLight2D":
			light = PointLight2D.new()
			if properties.has("energy"):
				light.energy = properties.get("energy")
		"DirectionalLight2D":
			light = DirectionalLight2D.new()
		_:
			return _error(4002, "Unknown light type", {"light_type": light_type})
	
	light.name = light_name
	
	# Common light properties
	if properties.has("light_color"):
		var c = properties.get("light_color")
		light.light_color = Color(c.get("r", 1), c.get("g", 1), c.get("b", 1))
	if properties.has("light_energy"):
		light.light_energy = properties.get("light_energy")
	if properties.has("shadow_enabled"):
		light.shadow_enabled = properties.get("shadow_enabled")
	
	# Position
	if properties.has("position"):
		var p = properties.get("position")
		if light is Node3D:
			light.position = Vector3(p.get("x", 0), p.get("y", 0), p.get("z", 0))
		elif light is Node2D:
			light.position = Vector2(p.get("x", 0), p.get("y", 0))
	
	# Rotation
	if properties.has("rotation"):
		var r = properties.get("rotation")
		if light is Node3D:
			light.rotation_degrees = Vector3(r.get("x", 0), r.get("y", 0), r.get("z", 0))
	
	parent.add_child(light, true)
	light.owner = root
	
	var new_path = String(light.get_path()) if light.is_inside_tree() else ""
	return {"ok": true, "node_path": new_path, "light_type": light_type}


func _resources_configure_camera(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var properties: Dictionary = _get_param_dict(params, "properties")
	
	var node_validation = Validators.validate_node_path(node_path)
	if not node_validation.get("ok", false):
		return node_validation
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	if node is Camera3D:
		if properties.has("fov"):
			node.fov = properties.get("fov")
		if properties.has("near"):
			node.near = properties.get("near")
		if properties.has("far"):
			node.far = properties.get("far")
		if properties.has("projection"):
			match properties.get("projection"):
				"perspective":
					node.projection = Camera3D.PROJECTION_PERSPECTIVE
				"orthogonal":
					node.projection = Camera3D.PROJECTION_ORTHOGONAL
		if properties.has("current"):
			node.current = properties.get("current")
	elif node is Camera2D:
		if properties.has("zoom"):
			var z = properties.get("zoom")
			node.zoom = Vector2(z.get("x", 1), z.get("y", 1))
		if properties.has("enabled"):
			node.enabled = properties.get("enabled")
		if properties.has("position_smoothing_enabled"):
			node.position_smoothing_enabled = properties.get("position_smoothing_enabled")
		if properties.has("position_smoothing_speed"):
			node.position_smoothing_speed = properties.get("position_smoothing_speed")
	else:
		return _error(4002, "Node must be Camera2D or Camera3D")
	
	return {"ok": true}


func _resources_create_environment(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var properties: Dictionary = _get_param_dict(params, "properties")
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var node = null
	if node_path.is_empty():
		# Create WorldEnvironment node
		node = WorldEnvironment.new()
		node.name = "WorldEnvironment"
		root.add_child(node, true)
		node.owner = root
	else:
		node = _resolve_node(node_path)
		if node == null:
			return _error(4010, "Node not found", {"path": node_path})
	
	if not (node is WorldEnvironment):
		return _error(4002, "Node must be WorldEnvironment")
	
	# Create environment resource
	var env = Environment.new()
	
	# Background
	if properties.has("background_mode"):
		match properties.get("background_mode"):
			"sky":
				env.background_mode = Environment.BG_SKY
			"color":
				env.background_mode = Environment.BG_COLOR
			"canvas":
				env.background_mode = Environment.BG_CANVAS
			"clear_color":
				env.background_mode = Environment.BG_CLEAR_COLOR
	
	if properties.has("background_color"):
		var c = properties.get("background_color")
		env.background_color = Color(c.get("r", 0), c.get("g", 0), c.get("b", 0))
	
	# Ambient light
	if properties.has("ambient_light_color"):
		var c = properties.get("ambient_light_color")
		env.ambient_light_color = Color(c.get("r", 1), c.get("g", 1), c.get("b", 1))
	if properties.has("ambient_light_energy"):
		env.ambient_light_energy = properties.get("ambient_light_energy")
	
	# Fog
	if properties.has("fog_enabled"):
		env.fog_enabled = properties.get("fog_enabled")
	if properties.has("fog_light_color"):
		var c = properties.get("fog_light_color")
		env.fog_light_color = Color(c.get("r", 1), c.get("g", 1), c.get("b", 1))
	
	# Glow
	if properties.has("glow_enabled"):
		env.glow_enabled = properties.get("glow_enabled")
	
	node.environment = env
	
	var new_path = String(node.get_path()) if node.is_inside_tree() else ""
	return {"ok": true, "node_path": new_path}


func _resources_create_audio_player(params: Dictionary):
	var parent_path: String = _get_param_string(params, "parent_path")
	var audio_type: String = _get_param_string(params, "audio_type", "AudioStreamPlayer")
	var audio_name: String = _get_param_string(params, "name", "AudioPlayer")
	var stream_path: String = _get_param_string(params, "stream_path")
	var properties: Dictionary = _get_param_dict(params, "properties")
	
	var root = _get_scene_root()
	if root == null:
		return _error(4010, "No scene open")
	
	var parent = _resolve_parent(parent_path)
	if parent == null:
		return _error(4010, "Parent node not found", {"path": parent_path})
	
	var audio = null
	match audio_type:
		"AudioStreamPlayer":
			audio = AudioStreamPlayer.new()
		"AudioStreamPlayer2D":
			audio = AudioStreamPlayer2D.new()
		"AudioStreamPlayer3D":
			audio = AudioStreamPlayer3D.new()
		_:
			return _error(4002, "Unknown audio type", {"audio_type": audio_type})
	
	audio.name = audio_name
	
	# Load stream
	if not stream_path.is_empty() and Validators.resource_exists(stream_path):
		var stream = load(stream_path)
		if stream is AudioStream:
			audio.stream = stream
	
	# Properties
	if properties.has("volume_db"):
		audio.volume_db = properties.get("volume_db")
	if properties.has("autoplay"):
		audio.autoplay = properties.get("autoplay")
	if audio is AudioStreamPlayer2D or audio is AudioStreamPlayer3D:
		if properties.has("max_distance"):
			audio.max_distance = properties.get("max_distance")
	
	parent.add_child(audio, true)
	audio.owner = root
	
	var new_path = String(audio.get_path()) if audio.is_inside_tree() else ""
	return {"ok": true, "node_path": new_path, "audio_type": audio_type}


# ============================================================================
# HELPERS
# ============================================================================

## Safe parameter getter - returns default if param is null or missing
func _get_param_string(params: Dictionary, key: String, default: String = "") -> String:
	var value = params.get(key)
	if value == null:
		return default
	return str(value)


func _get_param_array(params: Dictionary, key: String, default: Array = []) -> Array:
	var value = params.get(key)
	if value == null or not (value is Array):
		return default
	return value


func _get_param_dict(params: Dictionary, key: String, default: Dictionary = {}) -> Dictionary:
	var value = params.get(key)
	if value == null or not (value is Dictionary):
		return default
	return value


func _get_param_int(params: Dictionary, key: String, default: int = 0) -> int:
	var value = params.get(key)
	if value == null:
		return default
	return int(value)


func _get_param_float(params: Dictionary, key: String, default: float = 0.0) -> float:
	var value = params.get(key)
	if value == null:
		return default
	return float(value)


func _get_param_bool(params: Dictionary, key: String, default: bool = false) -> bool:
	var value = params.get(key)
	if value == null:
		return default
	return bool(value)


func _error(code: int, message: String, data: Dictionary = {}) -> Dictionary:
	var result = {
		"error": {
			"code": code,
			"message": message
		}
	}
	if not data.is_empty():
		result["error"]["data"] = data
	return result


# ============================================================================
# SPRITE2D HANDLERS
# ============================================================================

func _handle_sprite2d(action: String, params: Dictionary):
	match action:
		"set_texture":
			return _sprite2d_set_texture(params)
		"set_grid":
			return _sprite2d_set_grid(params)
		"set_frame":
			return _sprite2d_set_frame(params)
		"set_frame_coords":
			return _sprite2d_set_frame_coords(params)
		"get_grid":
			return _sprite2d_get_grid(params)
		"enable_region":
			return _sprite2d_enable_region(params)
		"set_region_rect":
			return _sprite2d_set_region_rect(params)
		"set_region_clip":
			return _sprite2d_set_region_clip(params)
		_:
			return _error(-32601, "Unknown sprite2d action: %s" % action)


func _sprite2d_set_texture(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var texture_path: String = _get_param_string(params, "texture_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var texture = load(texture_path)
	if texture == null or not (texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	node.texture = texture
	return {"ok": true, "texture_path": texture_path}


func _sprite2d_set_grid(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var hframes: int = _get_param_int(params, "hframes", 1)
	var vframes: int = _get_param_int(params, "vframes", 1)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	hframes = maxi(1, hframes)
	vframes = maxi(1, vframes)
	
	node.hframes = hframes
	node.vframes = vframes
	
	return {"ok": true, "hframes": hframes, "vframes": vframes, "total_frames": hframes * vframes}


func _sprite2d_set_frame(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var frame: int = _get_param_int(params, "frame", 0)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	var max_frame = (node.hframes * node.vframes) - 1
	frame = clampi(frame, 0, max_frame)
	
	node.frame = frame
	return {"ok": true, "frame": frame, "max_frame": max_frame}


func _sprite2d_set_frame_coords(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var x: int = _get_param_int(params, "x", 0)
	var y: int = _get_param_int(params, "y", 0)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	x = clampi(x, 0, node.hframes - 1)
	y = clampi(y, 0, node.vframes - 1)
	
	node.frame_coords = Vector2i(x, y)
	return {"ok": true, "frame_coords": {"x": x, "y": y}}


func _sprite2d_get_grid(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	return {
		"hframes": node.hframes,
		"vframes": node.vframes,
		"frame": node.frame,
		"frame_coords": {"x": node.frame_coords.x, "y": node.frame_coords.y},
		"total_frames": node.hframes * node.vframes,
		"region_enabled": node.region_enabled,
		"region_rect": {
			"x": node.region_rect.position.x,
			"y": node.region_rect.position.y,
			"w": node.region_rect.size.x,
			"h": node.region_rect.size.y
		}
	}


func _sprite2d_enable_region(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var enabled: bool = _get_param_bool(params, "enabled", true)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	node.region_enabled = enabled
	return {"ok": true, "region_enabled": enabled}


func _sprite2d_set_region_rect(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var x: float = _get_param_float(params, "x", 0)
	var y: float = _get_param_float(params, "y", 0)
	var w: float = _get_param_float(params, "w", 0)
	var h: float = _get_param_float(params, "h", 0)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	node.region_rect = Rect2(x, y, w, h)
	# Auto-enable region if setting rect
	if not node.region_enabled:
		node.region_enabled = true
	
	return {"ok": true, "region_rect": {"x": x, "y": y, "w": w, "h": h}, "region_enabled": true}


func _sprite2d_set_region_clip(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var enabled: bool = _get_param_bool(params, "enabled", true)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is Sprite2D):
		return _error(4002, "Node must be Sprite2D", {"type": node.get_class()})
	
	node.region_filter_clip_enabled = enabled
	return {"ok": true, "region_filter_clip_enabled": enabled}


# ============================================================================
# ATLAS TEXTURE HANDLERS
# ============================================================================

func _handle_atlas(action: String, params: Dictionary):
	match action:
		"create":
			return _atlas_create(params)
		"batch_create":
			return _atlas_batch_create(params)
		"set_texture":
			return _atlas_set_texture(params)
		_:
			return _error(-32601, "Unknown atlas action: %s" % action)


func _atlas_create(params: Dictionary):
	var texture_path: String = _get_param_string(params, "texture_path")
	var rect: Dictionary = _get_param_dict(params, "rect")
	var margin: Dictionary = _get_param_dict(params, "margin")
	var save_path: String = _get_param_string(params, "save_path")
	
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	if rect.is_empty():
		return _error(4001, "rect is required")
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var base_texture = load(texture_path)
	if base_texture == null or not (base_texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	var atlas = AtlasTexture.new()
	atlas.atlas = base_texture
	atlas.region = Rect2(
		rect.get("x", 0),
		rect.get("y", 0),
		rect.get("w", 0),
		rect.get("h", 0)
	)
	
	if not margin.is_empty():
		atlas.margin = Rect2(
			margin.get("x", 0),
			margin.get("y", 0),
			margin.get("w", 0),
			margin.get("h", 0)
		)
	
	var result_path = ""
	if not save_path.is_empty():
		var err = ResourceSaver.save(atlas, save_path)
		if err != OK:
			return _error(5001, "Failed to save AtlasTexture", {"error": error_string(err)})
		result_path = save_path
		EditorInterface.get_resource_filesystem().scan()
	
	return {
		"ok": true,
		"atlas_path": result_path,
		"region": {"x": atlas.region.position.x, "y": atlas.region.position.y, "w": atlas.region.size.x, "h": atlas.region.size.y}
	}


func _atlas_batch_create(params: Dictionary):
	var texture_path: String = _get_param_string(params, "texture_path")
	var rects: Array = _get_param_array(params, "rects")
	var margin: Dictionary = _get_param_dict(params, "margin")
	var save_folder: String = _get_param_string(params, "save_folder")
	
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	if rects.is_empty():
		return _error(4001, "rects array is required")
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var base_texture = load(texture_path)
	if base_texture == null or not (base_texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	var created = []
	var idx = 0
	
	for rect_data in rects:
		if not (rect_data is Dictionary):
			continue
		
		var atlas = AtlasTexture.new()
		atlas.atlas = base_texture
		atlas.region = Rect2(
			rect_data.get("x", 0),
			rect_data.get("y", 0),
			rect_data.get("w", 0),
			rect_data.get("h", 0)
		)
		
		if not margin.is_empty():
			atlas.margin = Rect2(
				margin.get("x", 0),
				margin.get("y", 0),
				margin.get("w", 0),
				margin.get("h", 0)
			)
		
		var result_path = ""
		if not save_folder.is_empty():
			var filename = "atlas_%03d.tres" % idx
			result_path = save_folder.path_join(filename)
			var err = ResourceSaver.save(atlas, result_path)
			if err != OK:
				created.append({"error": error_string(err), "index": idx})
				continue
		
		created.append({
			"index": idx,
			"path": result_path,
			"region": {"x": atlas.region.position.x, "y": atlas.region.position.y, "w": atlas.region.size.x, "h": atlas.region.size.y}
		})
		idx += 1
	
	if not save_folder.is_empty():
		EditorInterface.get_resource_filesystem().scan()
	
	return {"ok": true, "created": created, "count": created.size()}


func _atlas_set_texture(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var texture_path: String = _get_param_string(params, "texture_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var texture = load(texture_path)
	if texture == null or not (texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	if node is Sprite2D:
		node.texture = texture
	elif node is Sprite3D:
		node.texture = texture
	elif node is TextureRect:
		node.texture = texture
	elif node is TextureButton:
		node.texture_normal = texture
	else:
		return _error(4002, "Node type does not support texture", {"type": node.get_class()})
	
	return {"ok": true, "texture_path": texture_path, "node_type": node.get_class()}


# ============================================================================
# SPRITEFRAMES HANDLERS
# ============================================================================

func _handle_spriteframes(action: String, params: Dictionary):
	match action:
		"create":
			return _spriteframes_create(params)
		"add_animation":
			return _spriteframes_add_animation(params)
		"set_fps":
			return _spriteframes_set_fps(params)
		"set_loop":
			return _spriteframes_set_loop(params)
		"add_frame":
			return _spriteframes_add_frame(params)
		"remove_frame":
			return _spriteframes_remove_frame(params)
		"rename_animation":
			return _spriteframes_rename_animation(params)
		"list_animations":
			return _spriteframes_list_animations(params)
		_:
			return _error(-32601, "Unknown spriteframes action: %s" % action)


func _spriteframes_create(params: Dictionary):
	var save_path: String = _get_param_string(params, "save_path")
	
	var sf = SpriteFrames.new()
	
	var result_path = ""
	if not save_path.is_empty():
		var err = ResourceSaver.save(sf, save_path)
		if err != OK:
			return _error(5001, "Failed to save SpriteFrames", {"error": error_string(err)})
		result_path = save_path
		EditorInterface.get_resource_filesystem().scan()
	
	return {"ok": true, "spriteframes_path": result_path, "animations": sf.get_animation_names()}


func _spriteframes_add_animation(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if sf.has_animation(anim_name):
		return _error(4004, "Animation already exists", {"name": anim_name})
	
	sf.add_animation(anim_name)
	ResourceSaver.save(sf, sf_path)
	
	return {"ok": true, "animation_name": anim_name, "animations": sf.get_animation_names()}


func _spriteframes_set_fps(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var fps: float = _get_param_float(params, "fps", 10.0)
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if not sf.has_animation(anim_name):
		return _error(4004, "Animation not found", {"name": anim_name})
	
	sf.set_animation_speed(anim_name, fps)
	ResourceSaver.save(sf, sf_path)
	
	return {"ok": true, "animation_name": anim_name, "fps": fps}


func _spriteframes_set_loop(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var loop: bool = _get_param_bool(params, "loop", true)
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if not sf.has_animation(anim_name):
		return _error(4004, "Animation not found", {"name": anim_name})
	
	sf.set_animation_loop(anim_name, loop)
	ResourceSaver.save(sf, sf_path)
	
	return {"ok": true, "animation_name": anim_name, "loop": loop}


func _spriteframes_add_frame(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var texture_path: String = _get_param_string(params, "texture_path")
	var duration: float = _get_param_float(params, "duration", 1.0)
	var at_position: int = _get_param_int(params, "at_position", -1)
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if not sf.has_animation(anim_name):
		return _error(4004, "Animation not found", {"name": anim_name})
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var texture = load(texture_path)
	if texture == null or not (texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	sf.add_frame(anim_name, texture, duration, at_position)
	ResourceSaver.save(sf, sf_path)
	
	var frame_count = sf.get_frame_count(anim_name)
	return {"ok": true, "animation_name": anim_name, "frame_count": frame_count, "added_at": at_position if at_position >= 0 else frame_count - 1}


func _spriteframes_remove_frame(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var frame_index: int = _get_param_int(params, "frame_index", 0)
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if not sf.has_animation(anim_name):
		return _error(4004, "Animation not found", {"name": anim_name})
	
	var frame_count = sf.get_frame_count(anim_name)
	if frame_index < 0 or frame_index >= frame_count:
		return _error(4005, "Frame index out of range", {"index": frame_index, "count": frame_count})
	
	sf.remove_frame(anim_name, frame_index)
	ResourceSaver.save(sf, sf_path)
	
	return {"ok": true, "animation_name": anim_name, "removed_index": frame_index, "frame_count": sf.get_frame_count(anim_name)}


func _spriteframes_rename_animation(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	var old_name: String = _get_param_string(params, "old_name")
	var new_name: String = _get_param_string(params, "new_name")
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	if old_name.is_empty():
		return _error(4001, "old_name is required")
	if new_name.is_empty():
		return _error(4001, "new_name is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	if not sf.has_animation(old_name):
		return _error(4004, "Animation not found", {"name": old_name})
	
	if sf.has_animation(new_name):
		return _error(4004, "Animation with new name already exists", {"name": new_name})
	
	sf.rename_animation(old_name, new_name)
	ResourceSaver.save(sf, sf_path)
	
	return {"ok": true, "old_name": old_name, "new_name": new_name, "animations": sf.get_animation_names()}


func _spriteframes_list_animations(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	var animations = []
	for anim_name in sf.get_animation_names():
		animations.append({
			"name": anim_name,
			"fps": sf.get_animation_speed(anim_name),
			"loop": sf.get_animation_loop(anim_name),
			"frame_count": sf.get_frame_count(anim_name)
		})
	
	return {"animations": animations, "count": animations.size()}


# ============================================================================
# ANIMATEDSPRITE2D HANDLERS
# ============================================================================

func _handle_animsprite(action: String, params: Dictionary):
	match action:
		"attach":
			return _animsprite_attach(params)
		"play":
			return _animsprite_play(params)
		"stop":
			return _animsprite_stop(params)
		"pause":
			return _animsprite_pause(params)
		"set_speed":
			return _animsprite_set_speed(params)
		_:
			return _error(-32601, "Unknown animsprite action: %s" % action)


func _animsprite_attach(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimatedSprite2D):
		return _error(4002, "Node must be AnimatedSprite2D", {"type": node.get_class()})
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	node.sprite_frames = sf
	return {"ok": true, "spriteframes_path": sf_path, "animations": sf.get_animation_names()}


func _animsprite_play(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var custom_speed: float = _get_param_float(params, "custom_speed", 1.0)
	var from_end: bool = _get_param_bool(params, "from_end", false)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimatedSprite2D):
		return _error(4002, "Node must be AnimatedSprite2D", {"type": node.get_class()})
	
	if node.sprite_frames == null:
		return _error(4006, "No SpriteFrames attached to node")
	
	if anim_name.is_empty():
		anim_name = node.animation
	
	if not node.sprite_frames.has_animation(anim_name):
		return _error(4004, "Animation not found", {"name": anim_name})
	
	node.play(anim_name, custom_speed, from_end)
	return {"ok": true, "animation": anim_name, "playing": true}


func _animsprite_stop(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimatedSprite2D):
		return _error(4002, "Node must be AnimatedSprite2D", {"type": node.get_class()})
	
	node.stop()
	return {"ok": true, "playing": false}


func _animsprite_pause(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimatedSprite2D):
		return _error(4002, "Node must be AnimatedSprite2D", {"type": node.get_class()})
	
	node.pause()
	return {"ok": true, "paused": true}


func _animsprite_set_speed(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var speed_scale: float = _get_param_float(params, "speed_scale", 1.0)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimatedSprite2D):
		return _error(4002, "Node must be AnimatedSprite2D", {"type": node.get_class()})
	
	node.speed_scale = speed_scale
	return {"ok": true, "speed_scale": speed_scale}


# ============================================================================
# ANIMATION HANDLERS
# ============================================================================

func _handle_animation(action: String, params: Dictionary):
	match action:
		"create":
			return _animation_create(params)
		"add_track":
			return _animation_add_track(params)
		"insert_key":
			return _animation_insert_key(params)
		_:
			return _error(-32601, "Unknown animation action: %s" % action)


func _animation_create(params: Dictionary):
	var anim_name: String = _get_param_string(params, "name", "animation")
	var length: float = _get_param_float(params, "length", 1.0)
	var loop_mode_str: String = _get_param_string(params, "loop_mode", "none")
	var step: float = _get_param_float(params, "step", 0.1)
	var save_path: String = _get_param_string(params, "save_path")
	
	var anim = Animation.new()
	anim.length = length
	anim.step = step
	
	match loop_mode_str:
		"linear":
			anim.loop_mode = Animation.LOOP_LINEAR
		"pingpong":
			anim.loop_mode = Animation.LOOP_PINGPONG
		_:
			anim.loop_mode = Animation.LOOP_NONE
	
	var result_path = ""
	if not save_path.is_empty():
		var err = ResourceSaver.save(anim, save_path)
		if err != OK:
			return _error(5001, "Failed to save Animation", {"error": error_string(err)})
		result_path = save_path
		EditorInterface.get_resource_filesystem().scan()
	
	return {
		"ok": true,
		"animation_path": result_path,
		"name": anim_name,
		"length": length,
		"loop_mode": loop_mode_str,
		"step": step
	}


func _animation_add_track(params: Dictionary):
	var anim_path: String = _get_param_string(params, "animation_path")
	var node_path: String = _get_param_string(params, "node_path")
	var property: String = _get_param_string(params, "property")
	
	if anim_path.is_empty():
		return _error(4001, "animation_path is required")
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if property.is_empty():
		return _error(4001, "property is required")
	
	if not Validators.resource_exists(anim_path):
		return _error(4003, "Animation not found", {"path": anim_path})
	
	var anim = load(anim_path)
	if anim == null or not (anim is Animation):
		return _error(4003, "Invalid Animation resource", {"path": anim_path})
	
	var track_idx = anim.add_track(Animation.TYPE_VALUE)
	var track_path = "%s:%s" % [node_path, property]
	anim.track_set_path(track_idx, track_path)
	
	ResourceSaver.save(anim, anim_path)
	
	return {
		"ok": true,
		"track_index": track_idx,
		"track_path": track_path,
		"track_count": anim.get_track_count()
	}


func _animation_insert_key(params: Dictionary):
	var anim_path: String = _get_param_string(params, "animation_path")
	var track_index: int = _get_param_int(params, "track_index", 0)
	var time: float = _get_param_float(params, "time", 0)
	var value = params.get("value")
	
	if anim_path.is_empty():
		return _error(4001, "animation_path is required")
	
	if not Validators.resource_exists(anim_path):
		return _error(4003, "Animation not found", {"path": anim_path})
	
	var anim = load(anim_path)
	if anim == null or not (anim is Animation):
		return _error(4003, "Invalid Animation resource", {"path": anim_path})
	
	if track_index < 0 or track_index >= anim.get_track_count():
		return _error(4005, "Track index out of range", {"index": track_index, "count": anim.get_track_count()})
	
	# Deserialize value if needed
	var final_value = Serializers.deserialize(value)
	
	var key_idx = anim.track_insert_key(track_index, time, final_value)
	ResourceSaver.save(anim, anim_path)
	
	return {
		"ok": true,
		"track_index": track_index,
		"time": time,
		"key_index": key_idx,
		"key_count": anim.track_get_key_count(track_index)
	}


# ============================================================================
# ANIMATIONPLAYER HANDLERS
# ============================================================================

func _handle_animplayer(action: String, params: Dictionary):
	match action:
		"add_animation":
			return _animplayer_add_animation(params)
		"play":
			return _animplayer_play(params)
		"stop":
			return _animplayer_stop(params)
		_:
			return _error(-32601, "Unknown animplayer action: %s" % action)


func _animplayer_add_animation(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var anim_path: String = _get_param_string(params, "animation_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	if anim_path.is_empty():
		return _error(4001, "animation_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimationPlayer):
		return _error(4002, "Node must be AnimationPlayer", {"type": node.get_class()})
	
	if not Validators.resource_exists(anim_path):
		return _error(4003, "Animation not found", {"path": anim_path})
	
	var anim = load(anim_path)
	if anim == null or not (anim is Animation):
		return _error(4003, "Invalid Animation resource", {"path": anim_path})
	
	# Get or create animation library
	var lib_name = ""
	var lib: AnimationLibrary = null
	
	if node.has_animation_library(""):
		lib = node.get_animation_library("")
	else:
		lib = AnimationLibrary.new()
		node.add_animation_library("", lib)
	
	var err = lib.add_animation(anim_name, anim)
	if err != OK:
		return _error(5001, "Failed to add animation", {"error": error_string(err)})
	
	return {"ok": true, "animation_name": anim_name, "animations": node.get_animation_list()}


func _animplayer_play(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var anim_name: String = _get_param_string(params, "animation_name")
	var custom_blend: float = _get_param_float(params, "custom_blend", -1)
	var custom_speed: float = _get_param_float(params, "custom_speed", 1.0)
	var from_end: bool = _get_param_bool(params, "from_end", false)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if anim_name.is_empty():
		return _error(4001, "animation_name is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimationPlayer):
		return _error(4002, "Node must be AnimationPlayer", {"type": node.get_class()})
	
	if not node.has_animation(anim_name):
		return _error(4004, "Animation not found in player", {"name": anim_name})
	
	node.play(anim_name, custom_blend, custom_speed, from_end)
	return {"ok": true, "animation": anim_name, "playing": true}


func _animplayer_stop(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var keep_state: bool = _get_param_bool(params, "keep_state", false)
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	if not (node is AnimationPlayer):
		return _error(4002, "Node must be AnimationPlayer", {"type": node.get_class()})
	
	node.stop(keep_state)
	return {"ok": true, "playing": false, "keep_state": keep_state}


# ============================================================================
# TILESET HANDLERS
# ============================================================================

func _handle_tileset(action: String, params: Dictionary):
	match action:
		"ensure_atlas":
			return _tileset_ensure_atlas(params)
		"create_tile":
			return _tileset_create_tile(params)
		"list_tiles":
			return _tileset_list_tiles(params)
		_:
			return _error(-32601, "Unknown tileset action: %s" % action)


func _tileset_ensure_atlas(params: Dictionary):
	var ts_path: String = _get_param_string(params, "tileset_path")
	var texture_path: String = _get_param_string(params, "texture_path")
	var tile_size: Dictionary = _get_param_dict(params, "tile_size")
	var margins: Dictionary = _get_param_dict(params, "margins")
	var separation: Dictionary = _get_param_dict(params, "separation")
	
	if ts_path.is_empty():
		return _error(4001, "tileset_path is required")
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	if tile_size.is_empty():
		return _error(4001, "tile_size is required")
	
	# Load or create TileSet
	var tileset: TileSet = null
	var is_new = false
	
	if Validators.resource_exists(ts_path):
		tileset = load(ts_path)
		if tileset == null or not (tileset is TileSet):
			return _error(4003, "Invalid TileSet resource", {"path": ts_path})
	else:
		tileset = TileSet.new()
		is_new = true
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var texture = load(texture_path)
	if texture == null or not (texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	# Set tile size on tileset
	tileset.tile_size = Vector2i(
		tile_size.get("x", 16),
		tile_size.get("y", 16)
	)
	
	# Check if atlas source with this texture exists
	var source_id = -1
	for i in tileset.get_source_count():
		var sid = tileset.get_source_id(i)
		var source = tileset.get_source(sid)
		if source is TileSetAtlasSource:
			if source.texture == texture:
				source_id = sid
				break
	
	# Create new atlas source if not found
	if source_id == -1:
		var atlas_source = TileSetAtlasSource.new()
		atlas_source.texture = texture
		atlas_source.texture_region_size = Vector2i(
			tile_size.get("x", 16),
			tile_size.get("y", 16)
		)
		
		if not margins.is_empty():
			atlas_source.margins = Vector2i(
				margins.get("x", 0),
				margins.get("y", 0)
			)
		
		if not separation.is_empty():
			atlas_source.separation = Vector2i(
				separation.get("x", 0),
				separation.get("y", 0)
			)
		
		source_id = tileset.add_source(atlas_source)
	
	# Save tileset
	var err = ResourceSaver.save(tileset, ts_path)
	if err != OK:
		return _error(5001, "Failed to save TileSet", {"error": error_string(err)})
	
	EditorInterface.get_resource_filesystem().scan()
	
	return {
		"ok": true,
		"tileset_path": ts_path,
		"source_id": source_id,
		"is_new": is_new,
		"tile_size": {"x": tileset.tile_size.x, "y": tileset.tile_size.y}
	}


func _tileset_create_tile(params: Dictionary):
	var ts_path: String = _get_param_string(params, "tileset_path")
	var source_id: int = _get_param_int(params, "source_id", 0)
	var atlas_coords: Dictionary = _get_param_dict(params, "atlas_coords")
	var size: Dictionary = _get_param_dict(params, "size")
	
	if ts_path.is_empty():
		return _error(4001, "tileset_path is required")
	if atlas_coords.is_empty():
		return _error(4001, "atlas_coords is required")
	
	if not Validators.resource_exists(ts_path):
		return _error(4003, "TileSet not found", {"path": ts_path})
	
	var tileset = load(ts_path)
	if tileset == null or not (tileset is TileSet):
		return _error(4003, "Invalid TileSet resource", {"path": ts_path})
	
	if not tileset.has_source(source_id):
		return _error(4005, "Source ID not found", {"source_id": source_id})
	
	var source = tileset.get_source(source_id)
	if not (source is TileSetAtlasSource):
		return _error(4002, "Source must be TileSetAtlasSource", {"source_id": source_id})
	
	var coords = Vector2i(
		atlas_coords.get("x", 0),
		atlas_coords.get("y", 0)
	)
	
	var tile_size = Vector2i(1, 1)
	if not size.is_empty():
		tile_size = Vector2i(
			size.get("x", 1),
			size.get("y", 1)
		)
	
	# Check if tile already exists
	if source.has_tile(coords):
		return _error(4004, "Tile already exists at coords", {"coords": {"x": coords.x, "y": coords.y}})
	
	source.create_tile(coords, tile_size)
	ResourceSaver.save(tileset, ts_path)
	
	return {
		"ok": true,
		"atlas_coords": {"x": coords.x, "y": coords.y},
		"size": {"x": tile_size.x, "y": tile_size.y}
	}


func _tileset_list_tiles(params: Dictionary):
	var ts_path: String = _get_param_string(params, "tileset_path")
	var source_id: int = _get_param_int(params, "source_id", 0)
	
	if ts_path.is_empty():
		return _error(4001, "tileset_path is required")
	
	if not Validators.resource_exists(ts_path):
		return _error(4003, "TileSet not found", {"path": ts_path})
	
	var tileset = load(ts_path)
	if tileset == null or not (tileset is TileSet):
		return _error(4003, "Invalid TileSet resource", {"path": ts_path})
	
	if not tileset.has_source(source_id):
		return _error(4005, "Source ID not found", {"source_id": source_id})
	
	var source = tileset.get_source(source_id)
	if not (source is TileSetAtlasSource):
		return _error(4002, "Source must be TileSetAtlasSource", {"source_id": source_id})
	
	var tiles = []
	var tile_count = source.get_tiles_count()
	for i in tile_count:
		var coords = source.get_tile_id(i)
		var tile_size = source.get_tile_size_in_atlas(coords)
		tiles.append({
			"atlas_coords": {"x": coords.x, "y": coords.y},
			"size": {"x": tile_size.x, "y": tile_size.y}
		})
	
	return {
		"tiles": tiles,
		"count": tile_count,
		"source_id": source_id,
		"texture_region_size": {
			"x": source.texture_region_size.x,
			"y": source.texture_region_size.y
		}
	}


# ============================================================================
# INTROSPECTION HANDLERS
# ============================================================================

func _handle_introspect(action: String, params: Dictionary):
	match action:
		"class_properties":
			return _introspect_class_properties(params)
		"node_properties":
			return _introspect_node_properties(params)
		"property_describe":
			return _introspect_property_describe(params)
		"validate_properties":
			return _introspect_validate_properties(params)
		"catalog":
			return _introspect_catalog(params)
		"resource_info":
			return _introspect_resource_info(params)
		"animation_info":
			return _introspect_animation_info(params)
		"spriteframes_info":
			return _introspect_spriteframes_info(params)
		"texture_info":
			return _introspect_texture_info(params)
		_:
			return _error(-32601, "Unknown introspect action: %s" % action)


# ============================================================================
# INTROSPECTION HELPERS
# ============================================================================

func _type_to_string(type: int) -> String:
	match type:
		TYPE_NIL: return "null"
		TYPE_BOOL: return "bool"
		TYPE_INT: return "int"
		TYPE_FLOAT: return "float"
		TYPE_STRING: return "String"
		TYPE_VECTOR2: return "Vector2"
		TYPE_VECTOR2I: return "Vector2i"
		TYPE_RECT2: return "Rect2"
		TYPE_RECT2I: return "Rect2i"
		TYPE_VECTOR3: return "Vector3"
		TYPE_VECTOR3I: return "Vector3i"
		TYPE_TRANSFORM2D: return "Transform2D"
		TYPE_VECTOR4: return "Vector4"
		TYPE_VECTOR4I: return "Vector4i"
		TYPE_PLANE: return "Plane"
		TYPE_QUATERNION: return "Quaternion"
		TYPE_AABB: return "AABB"
		TYPE_BASIS: return "Basis"
		TYPE_TRANSFORM3D: return "Transform3D"
		TYPE_PROJECTION: return "Projection"
		TYPE_COLOR: return "Color"
		TYPE_STRING_NAME: return "StringName"
		TYPE_NODE_PATH: return "NodePath"
		TYPE_RID: return "RID"
		TYPE_OBJECT: return "Object"
		TYPE_CALLABLE: return "Callable"
		TYPE_SIGNAL: return "Signal"
		TYPE_DICTIONARY: return "Dictionary"
		TYPE_ARRAY: return "Array"
		TYPE_PACKED_BYTE_ARRAY: return "PackedByteArray"
		TYPE_PACKED_INT32_ARRAY: return "PackedInt32Array"
		TYPE_PACKED_INT64_ARRAY: return "PackedInt64Array"
		TYPE_PACKED_FLOAT32_ARRAY: return "PackedFloat32Array"
		TYPE_PACKED_FLOAT64_ARRAY: return "PackedFloat64Array"
		TYPE_PACKED_STRING_ARRAY: return "PackedStringArray"
		TYPE_PACKED_VECTOR2_ARRAY: return "PackedVector2Array"
		TYPE_PACKED_VECTOR3_ARRAY: return "PackedVector3Array"
		TYPE_PACKED_COLOR_ARRAY: return "PackedColorArray"
		_: return "Unknown(%d)" % type


func _hint_to_string(hint: int) -> String:
	match hint:
		PROPERTY_HINT_NONE: return "none"
		PROPERTY_HINT_RANGE: return "range"
		PROPERTY_HINT_ENUM: return "enum"
		PROPERTY_HINT_ENUM_SUGGESTION: return "enum_suggestion"
		PROPERTY_HINT_EXP_EASING: return "exp_easing"
		PROPERTY_HINT_LINK: return "link"
		PROPERTY_HINT_FLAGS: return "flags"
		PROPERTY_HINT_LAYERS_2D_RENDER: return "layers_2d_render"
		PROPERTY_HINT_LAYERS_2D_PHYSICS: return "layers_2d_physics"
		PROPERTY_HINT_LAYERS_2D_NAVIGATION: return "layers_2d_navigation"
		PROPERTY_HINT_LAYERS_3D_RENDER: return "layers_3d_render"
		PROPERTY_HINT_LAYERS_3D_PHYSICS: return "layers_3d_physics"
		PROPERTY_HINT_LAYERS_3D_NAVIGATION: return "layers_3d_navigation"
		PROPERTY_HINT_FILE: return "file"
		PROPERTY_HINT_DIR: return "dir"
		PROPERTY_HINT_GLOBAL_FILE: return "global_file"
		PROPERTY_HINT_GLOBAL_DIR: return "global_dir"
		PROPERTY_HINT_RESOURCE_TYPE: return "resource_type"
		PROPERTY_HINT_MULTILINE_TEXT: return "multiline_text"
		PROPERTY_HINT_EXPRESSION: return "expression"
		PROPERTY_HINT_PLACEHOLDER_TEXT: return "placeholder_text"
		PROPERTY_HINT_COLOR_NO_ALPHA: return "color_no_alpha"
		PROPERTY_HINT_OBJECT_ID: return "object_id"
		PROPERTY_HINT_TYPE_STRING: return "type_string"
		PROPERTY_HINT_NODE_PATH_TO_EDITED_NODE: return "node_path_to_edited_node"
		PROPERTY_HINT_OBJECT_TOO_BIG: return "object_too_big"
		PROPERTY_HINT_NODE_PATH_VALID_TYPES: return "node_path_valid_types"
		PROPERTY_HINT_SAVE_FILE: return "save_file"
		PROPERTY_HINT_GLOBAL_SAVE_FILE: return "global_save_file"
		PROPERTY_HINT_INT_IS_OBJECTID: return "int_is_objectid"
		PROPERTY_HINT_INT_IS_POINTER: return "int_is_pointer"
		PROPERTY_HINT_ARRAY_TYPE: return "array_type"
		PROPERTY_HINT_LOCALE_ID: return "locale_id"
		PROPERTY_HINT_LOCALIZABLE_STRING: return "localizable_string"
		PROPERTY_HINT_NODE_TYPE: return "node_type"
		PROPERTY_HINT_HIDE_QUATERNION_EDIT: return "hide_quaternion_edit"
		PROPERTY_HINT_PASSWORD: return "password"
		_: return "hint(%d)" % hint


func _generate_example_payload(type: int, hint: int, hint_string: String):
	match type:
		TYPE_BOOL:
			return true
		TYPE_INT:
			if hint == PROPERTY_HINT_RANGE and not hint_string.is_empty():
				var parts = hint_string.split(",")
				if parts.size() >= 2:
					var min_val = int(parts[0])
					var max_val = int(parts[1])
					return (min_val + max_val) / 2
			if hint == PROPERTY_HINT_ENUM and not hint_string.is_empty():
				return 0  # First enum value
			return 0
		TYPE_FLOAT:
			if hint == PROPERTY_HINT_RANGE and not hint_string.is_empty():
				var parts = hint_string.split(",")
				if parts.size() >= 2:
					var min_val = float(parts[0])
					var max_val = float(parts[1])
					return (min_val + max_val) / 2.0
			return 0.0
		TYPE_STRING:
			return ""
		TYPE_VECTOR2:
			return {"x": 0, "y": 0}
		TYPE_VECTOR2I:
			return {"x": 0, "y": 0}
		TYPE_VECTOR3:
			return {"x": 0, "y": 0, "z": 0}
		TYPE_VECTOR3I:
			return {"x": 0, "y": 0, "z": 0}
		TYPE_VECTOR4:
			return {"x": 0, "y": 0, "z": 0, "w": 0}
		TYPE_RECT2:
			return {"x": 0, "y": 0, "w": 0, "h": 0}
		TYPE_COLOR:
			return {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
		TYPE_TRANSFORM2D:
			return {"origin": {"x": 0, "y": 0}, "x": {"x": 1, "y": 0}, "y": {"x": 0, "y": 1}}
		TYPE_TRANSFORM3D:
			return {"origin": {"x": 0, "y": 0, "z": 0}}
		TYPE_NODE_PATH:
			return "NodeName"
		TYPE_ARRAY:
			return []
		TYPE_DICTIONARY:
			return {}
		TYPE_OBJECT:
			if hint == PROPERTY_HINT_RESOURCE_TYPE:
				return "res://path/to/resource.tres"
			return null
		_:
			return null


func _is_property_useful(prop: Dictionary) -> bool:
	var usage = prop.get("usage", 0)
	# Skip internal/editor-only properties
	if usage & PROPERTY_USAGE_INTERNAL:
		return false
	if usage & PROPERTY_USAGE_EDITOR:
		# Include if also has storage or script variable
		if not (usage & PROPERTY_USAGE_STORAGE or usage & PROPERTY_USAGE_SCRIPT_VARIABLE):
			return false
	# Must be at least storable or visible in editor
	return usage & (PROPERTY_USAGE_STORAGE | PROPERTY_USAGE_EDITOR | PROPERTY_USAGE_SCRIPT_VARIABLE) != 0


func _format_property(prop: Dictionary, include_example: bool = false) -> Dictionary:
	var type_int = prop.get("type", TYPE_NIL)
	var hint_int = prop.get("hint", PROPERTY_HINT_NONE)
	var hint_string = prop.get("hint_string", "")
	
	var result = {
		"name": prop.get("name", ""),
		"type": _type_to_string(type_int),
		"type_id": type_int,
		"hint": _hint_to_string(hint_int),
		"hint_string": hint_string
	}
	
	if include_example:
		result["example"] = _generate_example_payload(type_int, hint_int, hint_string)
	
	# Parse enum values if present
	if hint_int == PROPERTY_HINT_ENUM and not hint_string.is_empty():
		var enum_values = []
		var idx = 0
		for part in hint_string.split(","):
			var clean = part.strip_edges()
			if ":" in clean:
				var kv = clean.split(":")
				enum_values.append({"name": kv[0], "value": int(kv[1])})
			else:
				enum_values.append({"name": clean, "value": idx})
			idx += 1
		result["enum_values"] = enum_values
	
	# Parse range if present
	if hint_int == PROPERTY_HINT_RANGE and not hint_string.is_empty():
		var parts = hint_string.split(",")
		if parts.size() >= 2:
			result["range"] = {
				"min": float(parts[0]),
				"max": float(parts[1]),
				"step": float(parts[2]) if parts.size() > 2 else 1.0
			}
	
	return result


# ============================================================================
# INTROSPECTION IMPLEMENTATIONS
# ============================================================================

func _introspect_class_properties(params: Dictionary):
	var class_name_param: String = _get_param_string(params, "class_name")
	
	if class_name_param.is_empty():
		return _error(4001, "class_name is required")
	
	if not ClassDB.class_exists(class_name_param):
		return _error(4003, "Class not found", {"class_name": class_name_param})
	
	var props = ClassDB.class_get_property_list(class_name_param, true)
	var result = []
	
	for prop in props:
		if _is_property_useful(prop):
			result.append(_format_property(prop, true))
	
	# Get parent class
	var parent_class = ClassDB.get_parent_class(class_name_param)
	
	return {
		"class_name": class_name_param,
		"parent_class": parent_class,
		"properties": result,
		"count": result.size()
	}


func _introspect_node_properties(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var props = node.get_property_list()
	var result = []
	
	for prop in props:
		if _is_property_useful(prop):
			var formatted = _format_property(prop, true)
			# Add current value
			var prop_name = prop.get("name", "")
			if not prop_name.is_empty():
				var current_value = node.get(prop_name)
				formatted["current_value"] = Serializers.serialize(current_value)
			result.append(formatted)
	
	return {
		"node_path": node_path,
		"node_type": node.get_class(),
		"properties": result,
		"count": result.size()
	}


func _introspect_property_describe(params: Dictionary):
	var target: String = _get_param_string(params, "target")
	var property_name: String = _get_param_string(params, "property_name")
	
	if target.is_empty():
		return _error(4001, "target is required (class name or node path)")
	if property_name.is_empty():
		return _error(4001, "property_name is required")
	
	var prop_info: Dictionary = {}
	var current_value = null
	var is_node = false
	var node_type = ""
	
	# Check if target is a class name
	if ClassDB.class_exists(target):
		var props = ClassDB.class_get_property_list(target, true)
		for prop in props:
			if prop.get("name") == property_name:
				prop_info = prop
				break
	else:
		# Try as node path
		var node = _resolve_node(target)
		if node != null:
			is_node = true
			node_type = node.get_class()
			var props = node.get_property_list()
			for prop in props:
				if prop.get("name") == property_name:
					prop_info = prop
					current_value = node.get(property_name)
					break
		else:
			return _error(4010, "Target not found (not a valid class or node path)", {"target": target})
	
	if prop_info.is_empty():
		return _error(4004, "Property not found", {"property": property_name, "target": target})
	
	var result = _format_property(prop_info, true)
	result["target"] = target
	result["is_node"] = is_node
	
	if is_node:
		result["node_type"] = node_type
		result["current_value"] = Serializers.serialize(current_value)
	
	return result


func _introspect_validate_properties(params: Dictionary):
	var node_path: String = _get_param_string(params, "node_path")
	var properties: Dictionary = _get_param_dict(params, "properties")
	
	if node_path.is_empty():
		return _error(4001, "node_path is required")
	if properties.is_empty():
		return _error(4001, "properties is required")
	
	var node = _resolve_node(node_path)
	if node == null:
		return _error(4010, "Node not found", {"path": node_path})
	
	var node_props = node.get_property_list()
	var prop_map = {}
	for prop in node_props:
		prop_map[prop.get("name", "")] = prop
	
	var errors = []
	var warnings = []
	var valid_props = []
	
	for prop_name in properties.keys():
		var value = properties[prop_name]
		
		# Check if property exists
		if not prop_map.has(prop_name):
			errors.append({
				"property": prop_name,
				"error": "Property does not exist on this node",
				"suggestion": "Use godot_node_get_property_list to see available properties"
			})
			continue
		
		var prop_info = prop_map[prop_name]
		var expected_type = prop_info.get("type", TYPE_NIL)
		var hint = prop_info.get("hint", PROPERTY_HINT_NONE)
		var hint_string = prop_info.get("hint_string", "")
		
		# Check type compatibility
		var type_ok = _check_type_compatibility(value, expected_type)
		if not type_ok:
			errors.append({
				"property": prop_name,
				"error": "Type mismatch",
				"expected_type": _type_to_string(expected_type),
				"received_type": typeof(value),
				"example": _generate_example_payload(expected_type, hint, hint_string)
			})
			continue
		
		# Check range if applicable
		if hint == PROPERTY_HINT_RANGE and not hint_string.is_empty():
			var range_check = _check_range_value(value, hint_string)
			if range_check != "":
				warnings.append({
					"property": prop_name,
					"warning": range_check
				})
		
		# Check enum if applicable
		if hint == PROPERTY_HINT_ENUM and not hint_string.is_empty():
			var enum_check = _check_enum_value(value, hint_string)
			if enum_check != "":
				errors.append({
					"property": prop_name,
					"error": enum_check,
					"valid_values": hint_string
				})
				continue
		
		valid_props.append(prop_name)
	
	return {
		"valid": errors.is_empty(),
		"node_path": node_path,
		"node_type": node.get_class(),
		"valid_properties": valid_props,
		"errors": errors,
		"warnings": warnings
	}


func _check_type_compatibility(value, expected_type: int) -> bool:
	var actual_type = typeof(value)
	
	# Direct match
	if actual_type == expected_type:
		return true
	
	# Allow some conversions
	match expected_type:
		TYPE_FLOAT:
			return actual_type in [TYPE_INT, TYPE_FLOAT]
		TYPE_INT:
			return actual_type in [TYPE_INT, TYPE_FLOAT]
		TYPE_VECTOR2, TYPE_VECTOR2I, TYPE_VECTOR3, TYPE_VECTOR3I, TYPE_RECT2, TYPE_COLOR:
			# Allow dictionaries/arrays for vector types
			return actual_type in [TYPE_DICTIONARY, TYPE_ARRAY]
		TYPE_OBJECT:
			# Allow strings (resource paths) for object types
			return actual_type in [TYPE_OBJECT, TYPE_STRING, TYPE_NIL]
		TYPE_STRING:
			return actual_type in [TYPE_STRING, TYPE_STRING_NAME]
		_:
			return false


func _check_range_value(value, hint_string: String) -> String:
	var parts = hint_string.split(",")
	if parts.size() < 2:
		return ""
	
	var min_val = float(parts[0])
	var max_val = float(parts[1])
	var num_value = float(value) if typeof(value) in [TYPE_INT, TYPE_FLOAT] else 0
	
	if num_value < min_val or num_value > max_val:
		return "Value %s is outside range [%s, %s]" % [str(num_value), str(min_val), str(max_val)]
	
	return ""


func _check_enum_value(value, hint_string: String) -> String:
	if typeof(value) not in [TYPE_INT, TYPE_FLOAT]:
		return "Enum value must be an integer"
	
	var int_value = int(value)
	var valid_values = []
	var idx = 0
	
	for part in hint_string.split(","):
		var clean = part.strip_edges()
		if ":" in clean:
			var kv = clean.split(":")
			valid_values.append(int(kv[1]))
		else:
			valid_values.append(idx)
		idx += 1
	
	if int_value not in valid_values:
		return "Invalid enum value: %d" % int_value
	
	return ""


func _introspect_catalog(params: Dictionary):
	var kind: String = _get_param_string(params, "kind")
	
	if kind.is_empty():
		return _error(4001, "kind is required")
	
	var catalog = {}
	
	match kind:
		"mesh":
			catalog = {
				"kind": "mesh",
				"description": "Available mesh types for MeshInstance3D",
				"options": [
					{"name": "BoxMesh", "params": {"size": "Vector3"}, "example": {"size": {"x": 1, "y": 1, "z": 1}}},
					{"name": "SphereMesh", "params": {"radius": "float", "height": "float"}, "example": {"radius": 0.5, "height": 1.0}},
					{"name": "CylinderMesh", "params": {"radius": "float", "height": "float"}, "example": {"radius": 0.5, "height": 2.0}},
					{"name": "CapsuleMesh", "params": {"radius": "float", "height": "float"}, "example": {"radius": 0.5, "height": 2.0}},
					{"name": "PlaneMesh", "params": {"size": "Vector2"}, "example": {"size": {"x": 2, "y": 2}}},
					{"name": "PrismMesh", "params": {"size": "Vector3"}, "example": {"size": {"x": 1, "y": 1, "z": 1}}},
					{"name": "TorusMesh", "params": {"inner_radius": "float", "outer_radius": "float"}, "example": {"inner_radius": 0.5, "outer_radius": 1.0}},
					{"name": "QuadMesh", "params": {"size": "Vector2"}, "example": {"size": {"x": 1, "y": 1}}}
				]
			}
		"shape2d":
			catalog = {
				"kind": "shape2d",
				"description": "Available 2D collision shapes for CollisionShape2D",
				"options": [
					{"name": "RectangleShape2D", "params": {"size": "Vector2"}, "example": {"size": {"x": 32, "y": 32}}},
					{"name": "CircleShape2D", "params": {"radius": "float"}, "example": {"radius": 16}},
					{"name": "CapsuleShape2D", "params": {"radius": "float", "height": "float"}, "example": {"radius": 16, "height": 64}},
					{"name": "SegmentShape2D", "params": {"a": "Vector2", "b": "Vector2"}, "example": {"a": {"x": 0, "y": 0}, "b": {"x": 32, "y": 0}}},
					{"name": "WorldBoundaryShape2D", "params": {"normal": "Vector2", "distance": "float"}, "example": {"normal": {"x": 0, "y": -1}, "distance": 0}}
				]
			}
		"shape3d":
			catalog = {
				"kind": "shape3d",
				"description": "Available 3D collision shapes for CollisionShape3D",
				"options": [
					{"name": "BoxShape3D", "params": {"size": "Vector3"}, "example": {"size": {"x": 1, "y": 1, "z": 1}}},
					{"name": "SphereShape3D", "params": {"radius": "float"}, "example": {"radius": 0.5}},
					{"name": "CapsuleShape3D", "params": {"radius": "float", "height": "float"}, "example": {"radius": 0.5, "height": 2.0}},
					{"name": "CylinderShape3D", "params": {"radius": "float", "height": "float"}, "example": {"radius": 0.5, "height": 2.0}},
					{"name": "WorldBoundaryShape3D", "params": {"plane": "Plane"}, "example": {"plane": {"normal": {"x": 0, "y": 1, "z": 0}, "d": 0}}}
				]
			}
		"light2d":
			catalog = {
				"kind": "light2d",
				"description": "Available 2D light node types",
				"options": [
					{"name": "PointLight2D", "params": {"color": "Color", "energy": "float", "texture": "Texture2D"}, "example": {"light_color": {"r": 1, "g": 1, "b": 1, "a": 1}, "light_energy": 1.0}},
					{"name": "DirectionalLight2D", "params": {"color": "Color", "energy": "float"}, "example": {"light_color": {"r": 1, "g": 1, "b": 1, "a": 1}, "light_energy": 1.0}}
				]
			}
		"light3d":
			catalog = {
				"kind": "light3d",
				"description": "Available 3D light node types",
				"options": [
					{"name": "DirectionalLight3D", "params": {"color": "Color", "energy": "float", "shadow_enabled": "bool"}, "example": {"light_color": {"r": 1, "g": 1, "b": 1, "a": 1}, "light_energy": 1.0, "shadow_enabled": true}},
					{"name": "OmniLight3D", "params": {"color": "Color", "energy": "float", "range": "float"}, "example": {"light_color": {"r": 1, "g": 1, "b": 1, "a": 1}, "light_energy": 1.0, "omni_range": 5.0}},
					{"name": "SpotLight3D", "params": {"color": "Color", "energy": "float", "range": "float", "angle": "float"}, "example": {"light_color": {"r": 1, "g": 1, "b": 1, "a": 1}, "light_energy": 1.0, "spot_range": 5.0, "spot_angle": 45.0}}
				]
			}
		"audio":
			catalog = {
				"kind": "audio",
				"description": "Available audio player node types",
				"options": [
					{"name": "AudioStreamPlayer", "params": {"volume_db": "float", "autoplay": "bool", "bus": "StringName"}, "example": {"volume_db": 0.0, "autoplay": false, "bus": "Master"}},
					{"name": "AudioStreamPlayer2D", "params": {"volume_db": "float", "autoplay": "bool", "max_distance": "float"}, "example": {"volume_db": 0.0, "autoplay": false, "max_distance": 2000.0}},
					{"name": "AudioStreamPlayer3D", "params": {"volume_db": "float", "autoplay": "bool", "max_distance": "float", "unit_size": "float"}, "example": {"volume_db": 0.0, "autoplay": false, "max_distance": 0.0, "unit_size": 10.0}}
				]
			}
		"loop_mode":
			catalog = {
				"kind": "loop_mode",
				"description": "Animation loop modes",
				"options": [
					{"name": "none", "value": 0, "description": "No looping, animation plays once"},
					{"name": "linear", "value": 1, "description": "Loops from end to beginning"},
					{"name": "pingpong", "value": 2, "description": "Plays forward then backward"}
				]
			}
		"background_mode":
			catalog = {
				"kind": "background_mode",
				"description": "Environment background modes",
				"options": [
					{"name": "clear_color", "value": 0, "description": "Use clear color as background"},
					{"name": "custom_color", "value": 1, "description": "Use custom color"},
					{"name": "sky", "value": 2, "description": "Use a sky resource"},
					{"name": "canvas", "value": 3, "description": "Use the canvas background"},
					{"name": "keep", "value": 4, "description": "Keep previous frame"},
					{"name": "camera_feed", "value": 5, "description": "Use camera feed"}
				]
			}
		"node_2d":
			catalog = {
				"kind": "node_2d",
				"description": "Common 2D node types",
				"options": [
					{"name": "Node2D", "description": "Base 2D node"},
					{"name": "Sprite2D", "description": "2D sprite"},
					{"name": "AnimatedSprite2D", "description": "Animated 2D sprite"},
					{"name": "CharacterBody2D", "description": "2D character physics body"},
					{"name": "RigidBody2D", "description": "2D rigid physics body"},
					{"name": "StaticBody2D", "description": "2D static physics body"},
					{"name": "Area2D", "description": "2D area for detection"},
					{"name": "CollisionShape2D", "description": "2D collision shape"},
					{"name": "Camera2D", "description": "2D camera"},
					{"name": "TileMap", "description": "Tile-based map"},
					{"name": "Path2D", "description": "2D path"},
					{"name": "Line2D", "description": "2D line"},
					{"name": "Polygon2D", "description": "2D polygon"}
				]
			}
		"node_3d":
			catalog = {
				"kind": "node_3d",
				"description": "Common 3D node types",
				"options": [
					{"name": "Node3D", "description": "Base 3D node"},
					{"name": "MeshInstance3D", "description": "3D mesh instance"},
					{"name": "CharacterBody3D", "description": "3D character physics body"},
					{"name": "RigidBody3D", "description": "3D rigid physics body"},
					{"name": "StaticBody3D", "description": "3D static physics body"},
					{"name": "Area3D", "description": "3D area for detection"},
					{"name": "CollisionShape3D", "description": "3D collision shape"},
					{"name": "Camera3D", "description": "3D camera"},
					{"name": "DirectionalLight3D", "description": "Directional light"},
					{"name": "OmniLight3D", "description": "Omnidirectional light"},
					{"name": "SpotLight3D", "description": "Spot light"},
					{"name": "WorldEnvironment", "description": "World environment settings"},
					{"name": "Path3D", "description": "3D path"}
				]
			}
		"node_ui":
			catalog = {
				"kind": "node_ui",
				"description": "Common UI/Control node types",
				"options": [
					{"name": "Control", "description": "Base control node"},
					{"name": "Button", "description": "Clickable button"},
					{"name": "Label", "description": "Text label"},
					{"name": "TextEdit", "description": "Multi-line text editor"},
					{"name": "LineEdit", "description": "Single-line text input"},
					{"name": "Panel", "description": "Panel container"},
					{"name": "VBoxContainer", "description": "Vertical box container"},
					{"name": "HBoxContainer", "description": "Horizontal box container"},
					{"name": "GridContainer", "description": "Grid container"},
					{"name": "TextureRect", "description": "Texture display"},
					{"name": "ProgressBar", "description": "Progress bar"},
					{"name": "CheckBox", "description": "Checkbox"},
					{"name": "OptionButton", "description": "Dropdown button"},
					{"name": "SpinBox", "description": "Numeric spin box"},
					{"name": "ColorPickerButton", "description": "Color picker"}
				]
			}
		_:
			return _error(4004, "Unknown catalog kind", {
				"kind": kind,
				"available": ["mesh", "shape2d", "shape3d", "light2d", "light3d", "audio", "loop_mode", "background_mode", "node_2d", "node_3d", "node_ui"]
			})
	
	return catalog


func _introspect_resource_info(params: Dictionary):
	var resource_path: String = _get_param_string(params, "resource_path")
	
	if resource_path.is_empty():
		return _error(4001, "resource_path is required")
	
	if not Validators.resource_exists(resource_path):
		return _error(4003, "Resource not found", {"path": resource_path})
	
	var resource = load(resource_path)
	if resource == null:
		return _error(4003, "Failed to load resource", {"path": resource_path})
	
	var props = resource.get_property_list()
	var properties = {}
	var subresources = []
	
	for prop in props:
		if _is_property_useful(prop):
			var prop_name = prop.get("name", "")
			if prop_name.is_empty():
				continue
			
			var value = resource.get(prop_name)
			
			# Check if it's a subresource
			if value is Resource and value.resource_path.is_empty():
				subresources.append({
					"property": prop_name,
					"type": value.get_class()
				})
			elif value is Resource and not value.resource_path.is_empty():
				subresources.append({
					"property": prop_name,
					"type": value.get_class(),
					"path": value.resource_path
				})
			
			# Serialize main properties
			properties[prop_name] = Serializers.serialize(value)
	
	return {
		"path": resource_path,
		"class": resource.get_class(),
		"properties": properties,
		"subresources": subresources
	}


func _introspect_animation_info(params: Dictionary):
	var anim_path: String = _get_param_string(params, "animation_path")
	
	if anim_path.is_empty():
		return _error(4001, "animation_path is required")
	
	if not Validators.resource_exists(anim_path):
		return _error(4003, "Animation not found", {"path": anim_path})
	
	var anim = load(anim_path)
	if anim == null or not (anim is Animation):
		return _error(4003, "Invalid Animation resource", {"path": anim_path})
	
	var loop_mode_str = "none"
	match anim.loop_mode:
		Animation.LOOP_LINEAR:
			loop_mode_str = "linear"
		Animation.LOOP_PINGPONG:
			loop_mode_str = "pingpong"
	
	var tracks = []
	for i in anim.get_track_count():
		var track_type = anim.track_get_type(i)
		var type_str = "unknown"
		match track_type:
			Animation.TYPE_VALUE:
				type_str = "value"
			Animation.TYPE_POSITION_3D:
				type_str = "position_3d"
			Animation.TYPE_ROTATION_3D:
				type_str = "rotation_3d"
			Animation.TYPE_SCALE_3D:
				type_str = "scale_3d"
			Animation.TYPE_BLEND_SHAPE:
				type_str = "blend_shape"
			Animation.TYPE_METHOD:
				type_str = "method"
			Animation.TYPE_BEZIER:
				type_str = "bezier"
			Animation.TYPE_AUDIO:
				type_str = "audio"
			Animation.TYPE_ANIMATION:
				type_str = "animation"
		
		var path = anim.track_get_path(i)
		var path_str = str(path)
		var node_path = ""
		var property = ""
		
		if ":" in path_str:
			var parts = path_str.split(":")
			node_path = parts[0]
			property = parts[1]
		else:
			node_path = path_str
		
		var keys = []
		var key_count = anim.track_get_key_count(i)
		for k in mini(key_count, 10):  # Limit to first 10 keys for performance
			keys.append({
				"time": anim.track_get_key_time(i, k),
				"value": Serializers.serialize(anim.track_get_key_value(i, k))
			})
		
		tracks.append({
			"index": i,
			"type": type_str,
			"path": path_str,
			"node_path": node_path,
			"property": property,
			"key_count": key_count,
			"keys_preview": keys
		})
	
	return {
		"path": anim_path,
		"length": anim.length,
		"loop_mode": loop_mode_str,
		"step": anim.step,
		"track_count": anim.get_track_count(),
		"tracks": tracks
	}


func _introspect_spriteframes_info(params: Dictionary):
	var sf_path: String = _get_param_string(params, "spriteframes_path")
	
	if sf_path.is_empty():
		return _error(4001, "spriteframes_path is required")
	
	if not Validators.resource_exists(sf_path):
		return _error(4003, "SpriteFrames not found", {"path": sf_path})
	
	var sf = load(sf_path)
	if sf == null or not (sf is SpriteFrames):
		return _error(4003, "Invalid SpriteFrames resource", {"path": sf_path})
	
	var animations = []
	for anim_name in sf.get_animation_names():
		var frames = []
		var frame_count = sf.get_frame_count(anim_name)
		
		for i in mini(frame_count, 20):  # Limit for performance
			var texture = sf.get_frame_texture(anim_name, i)
			var duration = sf.get_frame_duration(anim_name, i)
			var frame_info = {
				"index": i,
				"duration": duration
			}
			if texture != null:
				frame_info["texture_type"] = texture.get_class()
				if not texture.resource_path.is_empty():
					frame_info["texture_path"] = texture.resource_path
			frames.append(frame_info)
		
		animations.append({
			"name": anim_name,
			"fps": sf.get_animation_speed(anim_name),
			"loop": sf.get_animation_loop(anim_name),
			"frame_count": frame_count,
			"frames": frames
		})
	
	return {
		"path": sf_path,
		"animation_count": animations.size(),
		"animations": animations
	}


func _introspect_texture_info(params: Dictionary):
	var texture_path: String = _get_param_string(params, "texture_path")
	
	if texture_path.is_empty():
		return _error(4001, "texture_path is required")
	
	if not Validators.resource_exists(texture_path):
		return _error(4003, "Texture not found", {"path": texture_path})
	
	var texture = load(texture_path)
	if texture == null or not (texture is Texture2D):
		return _error(4003, "Invalid texture", {"path": texture_path})
	
	var width = texture.get_width()
	var height = texture.get_height()
	
	# Calculate common grid divisors
	var grid_suggestions = []
	var common_sizes = [8, 16, 24, 32, 48, 64, 128, 256]
	
	for size in common_sizes:
		if width % size == 0 and height % size == 0:
			var h = width / size
			var v = height / size
			if h > 0 and v > 0 and h <= 32 and v <= 32:
				grid_suggestions.append({
					"cell_size": size,
					"hframes": h,
					"vframes": v,
					"total_frames": h * v
				})
	
	# Also check for non-square cells
	for w in common_sizes:
		for h in common_sizes:
			if w != h and width % w == 0 and height % h == 0:
				var hf = width / w
				var vf = height / h
				if hf > 0 and vf > 0 and hf <= 32 and vf <= 32:
					var suggestion = {
						"cell_width": w,
						"cell_height": h,
						"hframes": hf,
						"vframes": vf,
						"total_frames": hf * vf
					}
					# Avoid duplicates
					var exists = false
					for s in grid_suggestions:
						if s.get("hframes") == hf and s.get("vframes") == vf:
							exists = true
							break
					if not exists:
						grid_suggestions.append(suggestion)
	
	# Detect if it's likely a spritesheet
	var is_likely_spritesheet = grid_suggestions.size() > 0 and (width != height or width > 256)
	
	# Get image info if available
	var has_alpha = false
	var format_name = "unknown"
	
	if texture is ImageTexture or texture is CompressedTexture2D:
		var image = texture.get_image()
		if image != null:
			has_alpha = image.detect_alpha() != Image.ALPHA_NONE
			format_name = _image_format_to_string(image.get_format())
	
	return {
		"path": texture_path,
		"class": texture.get_class(),
		"width": width,
		"height": height,
		"has_alpha": has_alpha,
		"format": format_name,
		"is_likely_spritesheet": is_likely_spritesheet,
		"grid_suggestions": grid_suggestions
	}


func _image_format_to_string(format: int) -> String:
	match format:
		Image.FORMAT_L8: return "L8"
		Image.FORMAT_LA8: return "LA8"
		Image.FORMAT_R8: return "R8"
		Image.FORMAT_RG8: return "RG8"
		Image.FORMAT_RGB8: return "RGB8"
		Image.FORMAT_RGBA8: return "RGBA8"
		Image.FORMAT_RGBA4444: return "RGBA4444"
		Image.FORMAT_RGB565: return "RGB565"
		Image.FORMAT_RF: return "RF"
		Image.FORMAT_RGF: return "RGF"
		Image.FORMAT_RGBF: return "RGBF"
		Image.FORMAT_RGBAF: return "RGBAF"
		Image.FORMAT_RH: return "RH"
		Image.FORMAT_RGH: return "RGH"
		Image.FORMAT_RGBH: return "RGBH"
		Image.FORMAT_RGBAH: return "RGBAH"
		Image.FORMAT_RGBE9995: return "RGBE9995"
		Image.FORMAT_DXT1: return "DXT1"
		Image.FORMAT_DXT3: return "DXT3"
		Image.FORMAT_DXT5: return "DXT5"
		Image.FORMAT_RGTC_R: return "RGTC_R"
		Image.FORMAT_RGTC_RG: return "RGTC_RG"
		Image.FORMAT_BPTC_RGBA: return "BPTC_RGBA"
		Image.FORMAT_BPTC_RGBF: return "BPTC_RGBF"
		Image.FORMAT_BPTC_RGBFU: return "BPTC_RGBFU"
		Image.FORMAT_ETC: return "ETC"
		Image.FORMAT_ETC2_R11: return "ETC2_R11"
		Image.FORMAT_ETC2_R11S: return "ETC2_R11S"
		Image.FORMAT_ETC2_RG11: return "ETC2_RG11"
		Image.FORMAT_ETC2_RG11S: return "ETC2_RG11S"
		Image.FORMAT_ETC2_RGB8: return "ETC2_RGB8"
		Image.FORMAT_ETC2_RGBA8: return "ETC2_RGBA8"
		Image.FORMAT_ETC2_RGB8A1: return "ETC2_RGB8A1"
		Image.FORMAT_ETC2_RA_AS_RG: return "ETC2_RA_AS_RG"
		Image.FORMAT_DXT5_RA_AS_RG: return "DXT5_RA_AS_RG"
		Image.FORMAT_ASTC_4x4: return "ASTC_4x4"
		Image.FORMAT_ASTC_4x4_HDR: return "ASTC_4x4_HDR"
		Image.FORMAT_ASTC_8x8: return "ASTC_8x8"
		Image.FORMAT_ASTC_8x8_HDR: return "ASTC_8x8_HDR"
		_: return "unknown(%d)" % format
