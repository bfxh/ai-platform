@tool
extends EditorPlugin

var _rpc_server = null
var _session_token: String = ""
var _port: int = 49631
var _enabled: bool = true
var _last_scene_path: String = ""

const SETTING_PORT = "godotbridge/network/port"
const SETTING_ENABLED = "godotbridge/network/enabled"
const TOKEN_FILE = "user://godotbridge_token.txt"


func _enter_tree() -> void:
	_setup_editor_settings()
	_load_settings()
	
	if _enabled:
		_generate_token()
		_start_server()
		# Defer signal connection to next frame to ensure everything is loaded
		call_deferred("_connect_editor_signals")
	
	print("[GodotBridge] Plugin initialized on port %d" % _port)


func _exit_tree() -> void:
	_disconnect_editor_signals()
	_stop_server()
	print("[GodotBridge] Plugin disabled")


func _setup_editor_settings() -> void:
	var settings = EditorInterface.get_editor_settings()
	
	if not settings.has_setting(SETTING_PORT):
		settings.set_setting(SETTING_PORT, 49631)
		settings.set_initial_value(SETTING_PORT, 49631, false)
		settings.add_property_info({
			"name": SETTING_PORT,
			"type": TYPE_INT,
			"hint": PROPERTY_HINT_RANGE,
			"hint_string": "1024,65535"
		})
	
	if not settings.has_setting(SETTING_ENABLED):
		settings.set_setting(SETTING_ENABLED, true)
		settings.set_initial_value(SETTING_ENABLED, true, false)


func _load_settings() -> void:
	var settings = EditorInterface.get_editor_settings()
	_port = settings.get_setting(SETTING_PORT)
	_enabled = settings.get_setting(SETTING_ENABLED)


func _generate_token() -> void:
	var crypto = Crypto.new()
	var bytes = crypto.generate_random_bytes(32)
	_session_token = bytes.hex_encode()
	
	var file = FileAccess.open(TOKEN_FILE, FileAccess.WRITE)
	if file:
		var token_data = {
			"token": _session_token,
			"port": _port,
			"generated_at": Time.get_datetime_string_from_system()
		}
		file.store_string(JSON.stringify(token_data, "\t"))
		file.close()
		print("[GodotBridge] Token saved to: %s" % ProjectSettings.globalize_path(TOKEN_FILE))
	else:
		push_error("[GodotBridge] Failed to save token file")


func _start_server() -> void:
	if _rpc_server != null:
		return
	
	var server_script = load("res://addons/godotbridge/rpc_server.gd")
	if server_script:
		_rpc_server = server_script.new()
		_rpc_server.initialize(_port, _session_token, self)
	else:
		push_error("[GodotBridge] Failed to load RPC server script")


func _stop_server() -> void:
	if _rpc_server != null:
		_rpc_server.shutdown()
		_rpc_server = null


func get_session_token() -> String:
	return _session_token


func get_port() -> int:
	return _port


# ============================================================================
# EDITOR EVENTS
# ============================================================================

func _connect_editor_signals() -> void:
	var filesystem = EditorInterface.get_resource_filesystem()
	if filesystem:
		if not filesystem.filesystem_changed.is_connected(_on_filesystem_changed):
			filesystem.filesystem_changed.connect(_on_filesystem_changed)
		if not filesystem.resources_reimported.is_connected(_on_resources_reimported):
			filesystem.resources_reimported.connect(_on_resources_reimported)
	
	var selection = EditorInterface.get_selection()
	if selection:
		if not selection.selection_changed.is_connected(_on_selection_changed):
			selection.selection_changed.connect(_on_selection_changed)


func _disconnect_editor_signals() -> void:
	var filesystem = EditorInterface.get_resource_filesystem()
	if filesystem:
		if filesystem.filesystem_changed.is_connected(_on_filesystem_changed):
			filesystem.filesystem_changed.disconnect(_on_filesystem_changed)
		if filesystem.resources_reimported.is_connected(_on_resources_reimported):
			filesystem.resources_reimported.disconnect(_on_resources_reimported)
	
	var selection = EditorInterface.get_selection()
	if selection:
		if selection.selection_changed.is_connected(_on_selection_changed):
			selection.selection_changed.disconnect(_on_selection_changed)


func _process(delta: float) -> void:
	if _rpc_server != null:
		var current_scene = EditorInterface.get_edited_scene_root()
		var current_path = ""
		if current_scene != null:
			current_path = current_scene.scene_file_path
		
		if current_path != _last_scene_path:
			_last_scene_path = current_path
			_broadcast_event("scene_changed", {
				"scene_path": current_path,
				"timestamp": Time.get_datetime_string_from_system()
			})


func _on_filesystem_changed() -> void:
	_broadcast_event("filesystem_changed", {
		"timestamp": Time.get_datetime_string_from_system()
	})


func _on_resources_reimported(resources: PackedStringArray) -> void:
	_broadcast_event("resources_reimported", {
		"resources": Array(resources),
		"timestamp": Time.get_datetime_string_from_system()
	})


func _on_selection_changed() -> void:
	var selection = EditorInterface.get_selection()
	var selected_nodes = []
	for node in selection.get_selected_nodes():
		if node.is_inside_tree():
			selected_nodes.append(String(node.get_path()))
		else:
			selected_nodes.append(node.name)
	
	_broadcast_event("selection_changed", {
		"selection": selected_nodes,
		"timestamp": Time.get_datetime_string_from_system()
	})


func _broadcast_event(event_name: String, params: Dictionary) -> void:
	if _rpc_server != null:
		_rpc_server.broadcast_event(event_name, params)
