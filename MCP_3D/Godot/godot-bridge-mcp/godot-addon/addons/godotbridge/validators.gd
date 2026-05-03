@tool
extends RefCounted


## Validate a resource path (res://)
func validate_res_path(path: String) -> Dictionary:
	if path.is_empty():
		return _error(4001, "Path cannot be empty")
	
	if not path.begins_with("res://"):
		return _error(4030, "Path must start with res://", {"path": path})
	
	if ".." in path:
		return _error(4030, "Path traversal (..) not allowed", {"path": path})
	
	return {"ok": true, "path": path}


func validate_user_path(path: String) -> Dictionary:
	if path.is_empty():
		return _error(4001, "Path cannot be empty")
	
	if not path.begins_with("user://"):
		return _error(4030, "Path must start with user://", {"path": path})
	
	if ".." in path:
		return _error(4030, "Path traversal (..) not allowed", {"path": path})
	
	return {"ok": true, "path": path}


func validate_file_path(path: String, allow_user: bool = false) -> Dictionary:
	if path.is_empty():
		return _error(4001, "Path cannot be empty")
	
	if path.begins_with("res://"):
		return validate_res_path(path)
	elif path.begins_with("user://") and allow_user:
		return validate_user_path(path)
	else:
		if allow_user:
			return _error(4030, "Path must start with res:// or user://", {"path": path})
		else:
			return _error(4030, "Path must start with res://", {"path": path})


func validate_node_type(type_name: String) -> Dictionary:
	if type_name.is_empty():
		return _error(4002, "Node type cannot be empty")
	
	if not ClassDB.class_exists(type_name):
		return _error(4002, "Unknown node type", {"type": type_name})
	
	if not ClassDB.is_parent_class(type_name, "Node") and type_name != "Node":
		return _error(4002, "Type is not a Node class", {"type": type_name})
	
	if not ClassDB.can_instantiate(type_name):
		return _error(4002, "Cannot instantiate node type", {"type": type_name})
	
	return {"ok": true, "type": type_name}


func validate_node_path(path: String) -> Dictionary:
	if path.is_empty():
		return _error(4001, "Node path cannot be empty")
	
	var node_path = NodePath(path)
	if node_path.is_empty():
		return _error(4001, "Invalid node path format", {"path": path})
	
	return {"ok": true, "path": path, "node_path": node_path}


func validate_node_name(node_name: String) -> Dictionary:
	if node_name.is_empty():
		return _error(4001, "Node name cannot be empty")
	
	var invalid_chars = [".", ":", "/", "@", "%"]
	for c in invalid_chars:
		if c in node_name:
			return _error(4001, "Node name contains invalid character: %s" % c, {"name": node_name})
	
	return {"ok": true, "name": node_name}


func validate_properties(properties: Dictionary, node: Node) -> Dictionary:
	if properties.is_empty():
		return {"ok": true, "properties": properties}
	
	var errors = []
	var valid_props = {}
	
	for key in properties:
		if typeof(key) != TYPE_STRING:
			errors.append("Property key must be string: %s" % str(key))
			continue
		
		var prop_list = node.get_property_list()
		var prop_found = false
		
		for prop in prop_list:
			if prop.get("name") == key:
				prop_found = true
				break
		
		if not prop_found:
			errors.append("Property not found: %s" % key)
			continue
		
		valid_props[key] = properties[key]
	
	if errors.size() > 0:
		return _error(4003, "Invalid properties", {"errors": errors})
	
	return {"ok": true, "properties": valid_props}


func validate_signal(node: Node, signal_name: String) -> Dictionary:
	if signal_name.is_empty():
		return _error(4004, "Signal name cannot be empty")
	
	var signal_list = node.get_signal_list()
	for sig in signal_list:
		if sig.get("name") == signal_name:
			return {"ok": true, "signal": signal_name}
	
	return _error(4004, "Signal not found on node", {"signal": signal_name, "node": node.name})


func validate_scene_path(path: String) -> Dictionary:
	var path_result = validate_res_path(path)
	if not path_result.get("ok", false):
		return path_result
	
	if not path.ends_with(".tscn") and not path.ends_with(".scn"):
		return _error(4006, "Not a scene file", {"path": path})
	
	return {"ok": true, "path": path}


func resource_exists(path: String) -> bool:
	return ResourceLoader.exists(path)


func file_exists(path: String) -> bool:
	return FileAccess.file_exists(path)


func dir_exists(path: String) -> bool:
	return DirAccess.dir_exists_absolute(path)


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
