@tool
extends RefCounted

signal client_connected(peer_id: int)
signal client_disconnected(peer_id: int)
signal message_received(peer_id: int, message: Dictionary)

const MAX_MESSAGE_SIZE: int = 1048576  # 1MB
const POLL_INTERVAL: float = 0.05  # 50ms

var _tcp_server: TCPServer = null
var _peers: Dictionary = {}  # peer_id -> WebSocketPeer
var _authenticated_peers: Dictionary = {}  # peer_id -> bool
var _session_token: String = ""
var _port: int = 49631
var _plugin: EditorPlugin = null
var _handlers = null
var _timer: Timer = null
var _request_id_counter: int = 0

# Allowlist of RPC methods
const ALLOWED_METHODS = [
	"auth.hello",
	"auth.ping",
	"project.get_info",
	"project.get_autoloads",
	"project.get_input_map",
	"project.add_input_action",
	"project.remove_input_action",
	"editor.get_state",
	"editor.open_scene",
	"editor.save_scene",
	"editor.save_all",
	"editor.get_logs",
	"editor.clear_logs",
	"scene.get_tree",
	"scene.list_nodes",
	"scene.get_node",
	"scene.get_node_properties",
	"scene.set_node_properties",
	"scene.add_node",
	"scene.remove_node",
	"scene.rename_node",
	"scene.reparent_node",
	"scene.duplicate_node",
	"scene.create_scene",
	"scene.assign_script",
	"scene.create_mesh",
	"scene.instance_scene",
	"signals.list",
	"signals.list_connections",
	"signals.connect",
	"signals.disconnect",
	"filesystem.search",
	"filesystem.read_text",
	"filesystem.write_text",
	"filesystem.create_folder",
	"filesystem.delete",
	"filesystem.refresh",
	"play.run_main",
	"play.run_current",
	"play.stop",
	"play.get_state",
	"resources.create_material",
	"resources.set_material",
	"resources.load_texture",
	"resources.set_sprite_texture",
	"resources.create_collision_shape",
	"resources.set_modulate",
	"resources.create_light",
	"resources.configure_camera",
	"resources.create_environment",
	"resources.create_audio_player",
	# Sprite2D tools
	"sprite2d.set_texture",
	"sprite2d.set_grid",
	"sprite2d.set_frame",
	"sprite2d.set_frame_coords",
	"sprite2d.get_grid",
	"sprite2d.enable_region",
	"sprite2d.set_region_rect",
	"sprite2d.set_region_clip",
	# AtlasTexture tools
	"atlas.create",
	"atlas.batch_create",
	"atlas.set_texture",
	# SpriteFrames tools
	"spriteframes.create",
	"spriteframes.add_animation",
	"spriteframes.set_fps",
	"spriteframes.set_loop",
	"spriteframes.add_frame",
	"spriteframes.remove_frame",
	"spriteframes.rename_animation",
	"spriteframes.list_animations",
	# AnimatedSprite2D tools
	"animsprite.attach",
	"animsprite.play",
	"animsprite.stop",
	"animsprite.pause",
	"animsprite.set_speed",
	# Animation tools
	"animation.create",
	"animation.add_track",
	"animation.insert_key",
	# AnimationPlayer tools
	"animplayer.add_animation",
	"animplayer.play",
	"animplayer.stop",
	# TileSet tools
	"tileset.ensure_atlas",
	"tileset.create_tile",
	"tileset.list_tiles",
	# Introspection tools
	"introspect.class_properties",
	"introspect.node_properties",
	"introspect.property_describe",
	"introspect.validate_properties",
	"introspect.catalog",
	"introspect.resource_info",
	"introspect.animation_info",
	"introspect.spriteframes_info",
	"introspect.texture_info"
]


func initialize(port: int, token: String, plugin: EditorPlugin) -> void:
	_port = port
	_session_token = token
	_plugin = plugin
	
	# Load handlers dynamically to avoid preload issues
	var handlers_script = load("res://addons/godotbridge/rpc_handlers.gd")
	if handlers_script:
		_handlers = handlers_script.new()
		_handlers.initialize(plugin)
	else:
		push_error("[GodotBridge] Failed to load handlers script")
		return
	
	# Start TCP server
	_tcp_server = TCPServer.new()
	var err := _tcp_server.listen(_port, "127.0.0.1")
	if err != OK:
		push_error("[GodotBridge] Failed to start server on port %d: %s" % [_port, error_string(err)])
		return
	
	# Create poll timer
	_timer = Timer.new()
	_timer.wait_time = POLL_INTERVAL
	_timer.autostart = true
	_timer.timeout.connect(_poll)
	plugin.add_child(_timer)
	
	print("[GodotBridge] Server listening on 127.0.0.1:%d" % _port)


func shutdown() -> void:
	if _timer:
		_timer.stop()
		_timer.queue_free()
		_timer = null
	
	for peer_id in _peers.keys():
		var peer: WebSocketPeer = _peers[peer_id]
		peer.close()
	_peers.clear()
	_authenticated_peers.clear()
	
	if _tcp_server:
		_tcp_server.stop()
		_tcp_server = null
	
	print("[GodotBridge] Server stopped")


func _poll() -> void:
	# Accept new connections
	if _tcp_server and _tcp_server.is_connection_available():
		var conn := _tcp_server.take_connection()
		if conn:
			var peer := WebSocketPeer.new()
			var err := peer.accept_stream(conn)
			if err == OK:
				var peer_id := _get_next_peer_id()
				_peers[peer_id] = peer
				_authenticated_peers[peer_id] = false
				print("[GodotBridge] New connection: peer_%d" % peer_id)
				client_connected.emit(peer_id)
	
	# Poll all peers
	var to_remove: Array[int] = []
	for peer_id in _peers.keys():
		var peer: WebSocketPeer = _peers[peer_id]
		peer.poll()
		
		var state := peer.get_ready_state()
		match state:
			WebSocketPeer.STATE_OPEN:
				while peer.get_available_packet_count() > 0:
					var packet := peer.get_packet()
					_handle_packet(peer_id, packet)
			WebSocketPeer.STATE_CLOSING:
				pass  # Wait for close
			WebSocketPeer.STATE_CLOSED:
				print("[GodotBridge] Connection closed: peer_%d (code: %d)" % [peer_id, peer.get_close_code()])
				to_remove.append(peer_id)
				client_disconnected.emit(peer_id)
	
	# Remove closed peers
	for peer_id in to_remove:
		_peers.erase(peer_id)
		_authenticated_peers.erase(peer_id)


func _get_next_peer_id() -> int:
	_request_id_counter += 1
	return _request_id_counter


func _handle_packet(peer_id: int, packet: PackedByteArray) -> void:
	if packet.size() > MAX_MESSAGE_SIZE:
		_send_error(peer_id, null, -32600, "Message too large")
		return
	
	var text := packet.get_string_from_utf8()
	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		_send_error(peer_id, null, -32700, "Parse error: %s" % json.get_error_message())
		return
	
	var message = json.data
	if typeof(message) != TYPE_DICTIONARY:
		_send_error(peer_id, null, -32600, "Invalid request: expected object")
		return
	
	_process_request(peer_id, message)


func _process_request(peer_id: int, request: Dictionary) -> void:
	# Validate JSON-RPC structure
	if not request.has("jsonrpc") or request.get("jsonrpc") != "2.0":
		_send_error(peer_id, request.get("id"), -32600, "Invalid JSON-RPC version")
		return
	
	if not request.has("method") or typeof(request.get("method")) != TYPE_STRING:
		_send_error(peer_id, request.get("id"), -32600, "Missing or invalid method")
		return
	
	var method: String = request.get("method")
	var params: Dictionary = request.get("params", {})
	var request_id = request.get("id")
	
	# Check authentication (except for auth.hello)
	if method != "auth.hello" and not _authenticated_peers.get(peer_id, false):
		_send_error(peer_id, request_id, 4010, "Not authenticated")
		return
	
	# Check allowlist
	if method not in ALLOWED_METHODS:
		_send_error(peer_id, request_id, -32601, "Method not found: %s" % method)
		return
	
	# Handle auth methods specially
	if method == "auth.hello":
		_handle_auth_hello(peer_id, request_id, params)
		return
	
	if method == "auth.ping":
		_send_result(peer_id, request_id, {"ok": true, "t": Time.get_unix_time_from_system()})
		return
	
	# Dispatch to handlers
	var start_time := Time.get_ticks_msec()
	var result = _handlers.handle(method, params)
	var duration := Time.get_ticks_msec() - start_time
	
	if result is Dictionary and result.has("error"):
		var error_data: Dictionary = result.get("error")
		_send_error(peer_id, request_id, error_data.get("code", -32000), error_data.get("message", "Unknown error"), error_data.get("data"))
		print("[GodotBridge] %s -> ERROR (%dms)" % [method, duration])
	else:
		_send_result(peer_id, request_id, result)
		print("[GodotBridge] %s -> OK (%dms)" % [method, duration])


func _handle_auth_hello(peer_id: int, request_id, params: Dictionary) -> void:
	var token: String = params.get("token", "")
	var client: String = params.get("client", "unknown")
	var version: String = params.get("version", "0.0")
	
	if token != _session_token:
		_send_error(peer_id, request_id, 4010, "Invalid token")
		return
	
	_authenticated_peers[peer_id] = true
	print("[GodotBridge] Client authenticated: %s v%s" % [client, version])
	
	_send_result(peer_id, request_id, {
		"ok": true,
		"editor_version": Engine.get_version_info().get("string", "unknown"),
		"project_path": ProjectSettings.globalize_path("res://"),
		"capabilities": ALLOWED_METHODS
	})


func _send_result(peer_id: int, request_id, result) -> void:
	var response := {
		"jsonrpc": "2.0",
		"id": request_id,
		"result": result
	}
	_send_message(peer_id, response)


func _send_error(peer_id: int, request_id, code: int, message: String, data = null) -> void:
	var error := {
		"code": code,
		"message": message
	}
	if data != null:
		error["data"] = data
	
	var response := {
		"jsonrpc": "2.0",
		"id": request_id,
		"error": error
	}
	_send_message(peer_id, response)


func _send_message(peer_id: int, message: Dictionary) -> void:
	if not _peers.has(peer_id):
		return
	
	var peer: WebSocketPeer = _peers[peer_id]
	if peer.get_ready_state() != WebSocketPeer.STATE_OPEN:
		return
	
	var json := JSON.stringify(message)
	peer.send_text(json)


func broadcast_event(event_name: String, params: Dictionary) -> void:
	var message := {
		"jsonrpc": "2.0",
		"method": "event.%s" % event_name,
		"params": params
	}
	
	for peer_id in _authenticated_peers.keys():
		if _authenticated_peers[peer_id]:
			_send_message(peer_id, message)
