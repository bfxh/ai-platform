@tool
extends RefCounted

const MAX_DEPTH = 10
const MAX_ARRAY_SIZE = 1000
const MAX_STRING_LENGTH = 100000


func serialize(value, depth: int = 0):
	if depth > MAX_DEPTH:
		return {"_type": "max_depth_exceeded"}
	
	match typeof(value):
		TYPE_NIL:
			return null
		TYPE_BOOL:
			return value
		TYPE_INT:
			return value
		TYPE_FLOAT:
			if is_nan(value) or is_inf(value):
				return null
			return value
		TYPE_STRING:
			if value.length() > MAX_STRING_LENGTH:
				return value.substr(0, MAX_STRING_LENGTH) + "...[truncated]"
			return value
		TYPE_STRING_NAME:
			return String(value)
		TYPE_VECTOR2:
			return {"_type": "Vector2", "x": value.x, "y": value.y}
		TYPE_VECTOR2I:
			return {"_type": "Vector2i", "x": value.x, "y": value.y}
		TYPE_RECT2:
			return {"_type": "Rect2", "position": serialize(value.position, depth + 1), "size": serialize(value.size, depth + 1)}
		TYPE_VECTOR3:
			return {"_type": "Vector3", "x": value.x, "y": value.y, "z": value.z}
		TYPE_VECTOR3I:
			return {"_type": "Vector3i", "x": value.x, "y": value.y, "z": value.z}
		TYPE_COLOR:
			return {"_type": "Color", "r": value.r, "g": value.g, "b": value.b, "a": value.a}
		TYPE_NODE_PATH:
			return {"_type": "NodePath", "path": String(value)}
		TYPE_OBJECT:
			return _serialize_object(value, depth)
		TYPE_DICTIONARY:
			return _serialize_dictionary(value, depth)
		TYPE_ARRAY:
			return _serialize_array(value, depth)
		_:
			return {"_type": "unknown", "type_id": typeof(value)}


func _serialize_object(obj: Object, depth: int) -> Dictionary:
	if obj == null:
		return {"_type": "Object", "null": true}
	
	var result = {
		"_type": "Object",
		"class": obj.get_class(),
		"instance_id": obj.get_instance_id()
	}
	
	if obj is Resource and obj.resource_path != "":
		result["resource_path"] = obj.resource_path
	
	if obj is Node:
		var node = obj as Node
		if node.is_inside_tree():
			result["node_path"] = String(node.get_path())
		result["name"] = node.name
	
	var script = obj.get_script()
	if script != null and script is Script:
		if script.resource_path != "":
			result["script_path"] = script.resource_path
	
	return result


func _serialize_dictionary(dict: Dictionary, depth: int) -> Dictionary:
	var result = {}
	var count = 0
	for key in dict:
		if count >= MAX_ARRAY_SIZE:
			result["_truncated"] = true
			break
		var key_str: String
		if typeof(key) == TYPE_STRING:
			key_str = key
		else:
			key_str = str(key)
		result[key_str] = serialize(dict[key], depth + 1)
		count += 1
	return result


func _serialize_array(arr: Array, depth: int) -> Array:
	var result = []
	var size = mini(arr.size(), MAX_ARRAY_SIZE)
	for i in range(size):
		result.append(serialize(arr[i], depth + 1))
	return result


func deserialize(value):
	if value == null:
		return null
	
	if typeof(value) != TYPE_DICTIONARY:
		return value
	
	var dict = value as Dictionary
	if not dict.has("_type"):
		var result = {}
		for key in dict:
			result[key] = deserialize(dict[key])
		return result
	
	var type_name = dict.get("_type", "")
	match type_name:
		"Vector2":
			return Vector2(dict.get("x", 0), dict.get("y", 0))
		"Vector2i":
			return Vector2i(dict.get("x", 0), dict.get("y", 0))
		"Vector3":
			return Vector3(dict.get("x", 0), dict.get("y", 0), dict.get("z", 0))
		"Vector3i":
			return Vector3i(dict.get("x", 0), dict.get("y", 0), dict.get("z", 0))
		"Color":
			return Color(dict.get("r", 0), dict.get("g", 0), dict.get("b", 0), dict.get("a", 1))
		"NodePath":
			return NodePath(dict.get("path", ""))
		_:
			return dict


func serialize_node_properties(node: Node, keys: Array = []) -> Dictionary:
	var result = {}
	var property_list = node.get_property_list()
	
	for prop in property_list:
		var prop_name = prop.get("name", "")
		if prop_name.is_empty():
			continue
		
		if keys.size() > 0 and prop_name not in keys:
			continue
		
		if prop_name.begins_with("_"):
			continue
		
		var usage = prop.get("usage", 0)
		if not (usage & PROPERTY_USAGE_EDITOR):
			continue
		
		var prop_value = node.get(prop_name)
		result[prop_name] = serialize(prop_value)
	
	return result


func serialize_node_summary(node: Node) -> Dictionary:
	var result = {
		"node_path": String(node.get_path()) if node.is_inside_tree() else "",
		"name": node.name,
		"type": node.get_class(),
		"children_count": node.get_child_count()
	}
	
	var script = node.get_script()
	if script != null and script is Script and script.resource_path != "":
		result["script_path"] = script.resource_path
	
	if node.owner != null:
		result["owner"] = node.owner.name
	
	return result
