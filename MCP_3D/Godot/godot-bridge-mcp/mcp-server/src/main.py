"""Main entry point for the Godot MCP Bridge server - Windows compatible."""

import json
import sys
import os
import threading
import queue
import time

# Configure logging to stderr
import logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('GODOT_MCP_VERBOSE') else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)
logging.getLogger('websockets').setLevel(logging.WARNING)


class GodotRPCClient:
    """Synchronous WebSocket client for Godot plugin."""
    
    def __init__(self, ws_url, token):
        self.ws_url = ws_url
        self.token = token
        self.ws = None
        self.request_id = 0
        self.authenticated = False
    
    def connect(self):
        """Connect to Godot WebSocket server."""
        try:
            import websockets.sync.client as ws_client
            logger.info(f"Connecting to Godot at {self.ws_url}...")
            self.ws = ws_client.connect(self.ws_url)
            
            # Authenticate
            result = self.call("auth.hello", {
                "token": self.token,
                "client": "godot-mcp-bridge",
                "version": "1.0.0"
            })
            
            if result.get("ok"):
                self.authenticated = True
                logger.info(f"Connected to Godot {result.get('editor_version', 'unknown')}")
                return True
            else:
                logger.error("Authentication failed")
                return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def call(self, method, params=None):
        """Call an RPC method on Godot."""
        if self.ws is None:
            raise Exception("Not connected to Godot")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": str(self.request_id),
            "method": method,
            "params": params or {}
        }
        
        self.ws.send(json.dumps(request))
        
        # Wait for response
        while True:
            response_text = self.ws.recv()
            response = json.loads(response_text)
            
            if response.get("id") == str(self.request_id):
                if "error" in response:
                    error = response["error"]
                    raise Exception(f"RPC Error {error.get('code')}: {error.get('message')}")
                return response.get("result", {})
    
    def close(self):
        """Close connection."""
        if self.ws:
            self.ws.close()
            self.ws = None


class MCPServer:
    """Simple MCP Server over STDIO."""
    
    def __init__(self):
        self.godot = None
        self.tools = self._define_tools()
    
    def _define_tools(self):
        """Define available MCP tools."""
        return [
            # Project tools
            {"name": "godot_get_project_info", "description": "Get Godot project information", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "godot_add_input_action", "description": "Add input action with key binding", "inputSchema": {"type": "object", "properties": {"action_name": {"type": "string"}, "key": {"type": "string", "description": "KEY_UP, KEY_W, KEY_SPACE, etc."}}, "required": ["action_name", "key"]}},
            {"name": "godot_remove_input_action", "description": "Remove an input action", "inputSchema": {"type": "object", "properties": {"action_name": {"type": "string"}}, "required": ["action_name"]}},
            
            # Editor tools
            {"name": "godot_get_editor_state", "description": "Get editor state", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "godot_open_scene", "description": "Open a scene file", "inputSchema": {"type": "object", "properties": {"scene_path": {"type": "string"}}, "required": ["scene_path"]}},
            {"name": "godot_save_scene", "description": "Save current scene", "inputSchema": {"type": "object", "properties": {"scene_path": {"type": "string"}}, "required": []}},
            
            # Scene tools
            {"name": "godot_create_scene", "description": "Create new scene", "inputSchema": {"type": "object", "properties": {"root_type": {"type": "string", "description": "Node3D, Node2D, Control"}, "root_name": {"type": "string"}, "scene_path": {"type": "string"}}, "required": ["root_type", "scene_path"]}},
            {"name": "godot_instance_scene", "description": "Instance a scene", "inputSchema": {"type": "object", "properties": {"parent_path": {"type": "string"}, "scene_path": {"type": "string"}, "name": {"type": "string"}}, "required": ["parent_path", "scene_path"]}},
            {"name": "godot_get_scene_tree", "description": "Get scene tree", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "godot_list_nodes", "description": "List child nodes", "inputSchema": {"type": "object", "properties": {"parent_path": {"type": "string"}}, "required": []}},
            {"name": "godot_get_node_properties", "description": "Get node properties", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            {"name": "godot_set_node_properties", "description": "Set node properties", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "properties": {"type": "object"}}, "required": ["node_path", "properties"]}},
            {"name": "godot_add_node", "description": "Add a node", "inputSchema": {"type": "object", "properties": {"parent_path": {"type": "string"}, "type": {"type": "string"}, "name": {"type": "string"}, "properties": {"type": "object"}}, "required": ["parent_path", "type", "name"]}},
            {"name": "godot_remove_node", "description": "Remove a node", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            
            # Mesh tools
            {"name": "godot_create_mesh", "description": "Create mesh on MeshInstance3D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "mesh_type": {"type": "string", "description": "BoxMesh, SphereMesh, CylinderMesh, PlaneMesh, CapsuleMesh"}, "mesh_params": {"type": "object"}}, "required": ["node_path", "mesh_type"]}},
            
            # Material tools
            {"name": "godot_create_material", "description": "Create and apply material to node", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "material_type": {"type": "string", "description": "StandardMaterial3D, CanvasItemMaterial"}, "properties": {"type": "object", "description": "albedo_color, metallic, roughness, emission"}}, "required": ["node_path"]}},
            {"name": "godot_set_material", "description": "Set existing material on node", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "material_path": {"type": "string"}, "surface_index": {"type": "integer"}}, "required": ["node_path", "material_path"]}},
            
            # Sprite/Texture tools
            {"name": "godot_set_sprite_texture", "description": "Set texture on Sprite2D/3D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "texture_path": {"type": "string"}, "hframes": {"type": "integer"}, "vframes": {"type": "integer"}, "frame": {"type": "integer"}}, "required": ["node_path", "texture_path"]}},
            {"name": "godot_set_modulate", "description": "Set color modulation on CanvasItem", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "color": {"type": "object", "description": "{r, g, b, a}"}, "self_modulate": {"type": "boolean"}}, "required": ["node_path", "color"]}},
            
            # Collision tools
            {"name": "godot_create_collision_shape", "description": "Create collision shape", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "shape_type": {"type": "string", "description": "BoxShape3D, SphereShape3D, CapsuleShape3D, RectangleShape2D, CircleShape2D"}, "shape_params": {"type": "object"}}, "required": ["node_path", "shape_type"]}},
            
            # Light tools
            {"name": "godot_create_light", "description": "Create light node", "inputSchema": {"type": "object", "properties": {"parent_path": {"type": "string"}, "light_type": {"type": "string", "description": "DirectionalLight3D, OmniLight3D, SpotLight3D, PointLight2D"}, "name": {"type": "string"}, "properties": {"type": "object", "description": "light_color, light_energy, shadow_enabled, position, rotation"}}, "required": ["parent_path", "light_type"]}},
            
            # Camera tools
            {"name": "godot_configure_camera", "description": "Configure camera properties", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "properties": {"type": "object", "description": "fov, near, far, projection, zoom, current"}}, "required": ["node_path", "properties"]}},
            
            # Environment tools
            {"name": "godot_create_environment", "description": "Create/configure WorldEnvironment", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "properties": {"type": "object", "description": "background_mode, background_color, ambient_light_color, fog_enabled, glow_enabled"}}, "required": []}},
            
            # Audio tools
            {"name": "godot_create_audio_player", "description": "Create audio player node", "inputSchema": {"type": "object", "properties": {"parent_path": {"type": "string"}, "audio_type": {"type": "string", "description": "AudioStreamPlayer, AudioStreamPlayer2D, AudioStreamPlayer3D"}, "name": {"type": "string"}, "stream_path": {"type": "string"}, "properties": {"type": "object", "description": "volume_db, autoplay, max_distance"}}, "required": ["parent_path"]}},
            
            # Script tools
            {"name": "godot_read_script", "description": "Read script content", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
            {"name": "godot_write_script", "description": "Write script content", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
            {"name": "godot_assign_script", "description": "Assign script to node", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "script_path": {"type": "string"}}, "required": ["node_path", "script_path"]}},
            
            # Run tools
            {"name": "godot_run_main", "description": "Run main scene", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "godot_run_current", "description": "Run current scene", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            {"name": "godot_stop", "description": "Stop running scene", "inputSchema": {"type": "object", "properties": {}, "required": []}},
            
            # File tools
            {"name": "godot_search_files", "description": "Search files", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "type": {"type": "string"}, "folder": {"type": "string"}}, "required": []}},
            
            # ============================================================
            # SPRITE2D TOOLS - Grid and Region
            # ============================================================
            {"name": "godot_sprite2d_set_texture", "description": "Set texture on Sprite2D node", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "texture_path": {"type": "string"}}, "required": ["node_path", "texture_path"]}},
            {"name": "godot_sprite2d_set_grid", "description": "Configure Sprite2D grid (hframes/vframes) for sprite sheets", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "hframes": {"type": "integer", "description": "Horizontal frames"}, "vframes": {"type": "integer", "description": "Vertical frames"}}, "required": ["node_path", "hframes", "vframes"]}},
            {"name": "godot_sprite2d_set_frame", "description": "Set current frame by index on Sprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "frame": {"type": "integer"}}, "required": ["node_path", "frame"]}},
            {"name": "godot_sprite2d_set_frame_coords", "description": "Set current frame by coordinates (x,y) on Sprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["node_path", "x", "y"]}},
            {"name": "godot_sprite2d_get_grid", "description": "Get Sprite2D grid configuration and current frame", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            {"name": "godot_sprite2d_enable_region", "description": "Enable/disable region mode on Sprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "enabled": {"type": "boolean"}}, "required": ["node_path", "enabled"]}},
            {"name": "godot_sprite2d_set_region_rect", "description": "Set region rectangle on Sprite2D (x, y, width, height)", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "x": {"type": "number"}, "y": {"type": "number"}, "w": {"type": "number"}, "h": {"type": "number"}}, "required": ["node_path", "x", "y", "w", "h"]}},
            {"name": "godot_sprite2d_set_region_clip", "description": "Enable/disable region filter clip on Sprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "enabled": {"type": "boolean"}}, "required": ["node_path", "enabled"]}},
            
            # ============================================================
            # ATLAS TEXTURE TOOLS
            # ============================================================
            {"name": "godot_atlas_create", "description": "Create AtlasTexture from a texture region", "inputSchema": {"type": "object", "properties": {"texture_path": {"type": "string"}, "rect": {"type": "object", "description": "{x, y, w, h}"}, "margin": {"type": "object", "description": "{x, y, w, h} optional"}, "save_path": {"type": "string", "description": "Optional path to save .tres"}}, "required": ["texture_path", "rect"]}},
            {"name": "godot_atlas_batch_create", "description": "Create multiple AtlasTextures from rects", "inputSchema": {"type": "object", "properties": {"texture_path": {"type": "string"}, "rects": {"type": "array", "items": {"type": "object"}, "description": "[{x, y, w, h}, ...]"}, "margin": {"type": "object"}, "save_folder": {"type": "string"}}, "required": ["texture_path", "rects"]}},
            {"name": "godot_node_set_texture", "description": "Set any Texture2D (including AtlasTexture) on Sprite2D/TextureRect", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "texture_path": {"type": "string"}}, "required": ["node_path", "texture_path"]}},
            
            # ============================================================
            # SPRITEFRAMES TOOLS
            # ============================================================
            {"name": "godot_spriteframes_create", "description": "Create new SpriteFrames resource", "inputSchema": {"type": "object", "properties": {"save_path": {"type": "string", "description": "Optional path to save .tres"}}, "required": []}},
            {"name": "godot_spriteframes_add_animation", "description": "Add animation to SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "animation_name": {"type": "string"}}, "required": ["spriteframes_path", "animation_name"]}},
            {"name": "godot_spriteframes_set_fps", "description": "Set animation FPS in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "animation_name": {"type": "string"}, "fps": {"type": "number"}}, "required": ["spriteframes_path", "animation_name", "fps"]}},
            {"name": "godot_spriteframes_set_loop", "description": "Set animation loop in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "animation_name": {"type": "string"}, "loop": {"type": "boolean"}}, "required": ["spriteframes_path", "animation_name", "loop"]}},
            {"name": "godot_spriteframes_add_frame", "description": "Add frame to animation in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "animation_name": {"type": "string"}, "texture_path": {"type": "string"}, "duration": {"type": "number", "description": "Frame duration multiplier (default 1.0)"}, "at_position": {"type": "integer", "description": "Insert position (-1 for end)"}}, "required": ["spriteframes_path", "animation_name", "texture_path"]}},
            {"name": "godot_spriteframes_remove_frame", "description": "Remove frame from animation in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "animation_name": {"type": "string"}, "frame_index": {"type": "integer"}}, "required": ["spriteframes_path", "animation_name", "frame_index"]}},
            {"name": "godot_spriteframes_rename_animation", "description": "Rename animation in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}, "old_name": {"type": "string"}, "new_name": {"type": "string"}}, "required": ["spriteframes_path", "old_name", "new_name"]}},
            {"name": "godot_spriteframes_list_animations", "description": "List all animations in SpriteFrames", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}}, "required": ["spriteframes_path"]}},
            
            # ============================================================
            # ANIMATEDSPRITE2D TOOLS
            # ============================================================
            {"name": "godot_animsprite_attach", "description": "Attach SpriteFrames resource to AnimatedSprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "spriteframes_path": {"type": "string"}}, "required": ["node_path", "spriteframes_path"]}},
            {"name": "godot_animsprite_play", "description": "Play animation on AnimatedSprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "animation_name": {"type": "string"}, "custom_speed": {"type": "number"}, "from_end": {"type": "boolean"}}, "required": ["node_path"]}},
            {"name": "godot_animsprite_stop", "description": "Stop animation on AnimatedSprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            {"name": "godot_animsprite_pause", "description": "Pause animation on AnimatedSprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            {"name": "godot_animsprite_set_speed", "description": "Set speed scale on AnimatedSprite2D", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "speed_scale": {"type": "number"}}, "required": ["node_path", "speed_scale"]}},
            
            # ============================================================
            # ANIMATION TOOLS
            # ============================================================
            {"name": "godot_animation_create", "description": "Create new Animation resource", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}, "length": {"type": "number"}, "loop_mode": {"type": "string", "description": "none, linear, pingpong"}, "step": {"type": "number"}, "save_path": {"type": "string"}}, "required": ["name", "length"]}},
            {"name": "godot_animation_add_track", "description": "Add value track to Animation", "inputSchema": {"type": "object", "properties": {"animation_path": {"type": "string"}, "node_path": {"type": "string"}, "property": {"type": "string"}}, "required": ["animation_path", "node_path", "property"]}},
            {"name": "godot_animation_insert_key", "description": "Insert keyframe into Animation track", "inputSchema": {"type": "object", "properties": {"animation_path": {"type": "string"}, "track_index": {"type": "integer"}, "time": {"type": "number"}, "value": {}}, "required": ["animation_path", "track_index", "time", "value"]}},
            
            # ============================================================
            # ANIMATIONPLAYER TOOLS
            # ============================================================
            {"name": "godot_animplayer_add_animation", "description": "Add Animation to AnimationPlayer library", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "animation_name": {"type": "string"}, "animation_path": {"type": "string"}}, "required": ["node_path", "animation_name", "animation_path"]}},
            {"name": "godot_animplayer_play", "description": "Play animation on AnimationPlayer", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "animation_name": {"type": "string"}, "custom_blend": {"type": "number"}, "custom_speed": {"type": "number"}, "from_end": {"type": "boolean"}}, "required": ["node_path", "animation_name"]}},
            {"name": "godot_animplayer_stop", "description": "Stop AnimationPlayer", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "keep_state": {"type": "boolean"}}, "required": ["node_path"]}},
            
            # ============================================================
            # TILESET TOOLS
            # ============================================================
            {"name": "godot_tileset_ensure_atlas", "description": "Ensure TileSetAtlasSource exists in TileSet", "inputSchema": {"type": "object", "properties": {"tileset_path": {"type": "string"}, "texture_path": {"type": "string"}, "tile_size": {"type": "object", "description": "{x, y}"}, "margins": {"type": "object", "description": "{x, y}"}, "separation": {"type": "object", "description": "{x, y}"}}, "required": ["tileset_path", "texture_path", "tile_size"]}},
            {"name": "godot_tileset_create_tile", "description": "Create tile in TileSetAtlasSource", "inputSchema": {"type": "object", "properties": {"tileset_path": {"type": "string"}, "source_id": {"type": "integer"}, "atlas_coords": {"type": "object", "description": "{x, y}"}, "size": {"type": "object", "description": "{x, y} in cells"}}, "required": ["tileset_path", "source_id", "atlas_coords"]}},
            {"name": "godot_tileset_list_tiles", "description": "List tiles in TileSetAtlasSource", "inputSchema": {"type": "object", "properties": {"tileset_path": {"type": "string"}, "source_id": {"type": "integer"}}, "required": ["tileset_path", "source_id"]}},
            
            # ============================================================
            # INTROSPECTION TOOLS - Query metadata before actions
            # ============================================================
            {"name": "godot_class_get_property_list", "description": "Get all properties of a Godot class with types, hints, ranges, and examples. Use before set_node_properties to know valid properties.", "inputSchema": {"type": "object", "properties": {"class_name": {"type": "string", "description": "Godot class name (e.g. Camera3D, Sprite2D, CharacterBody2D)"}}, "required": ["class_name"]}},
            {"name": "godot_node_get_property_list", "description": "Get all properties of a specific node instance including current values. Better than class version as it includes script properties.", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}}, "required": ["node_path"]}},
            {"name": "godot_property_describe", "description": "Get detailed info about a specific property including type, range, enum values, and example payload.", "inputSchema": {"type": "object", "properties": {"target": {"type": "string", "description": "Class name or node path"}, "property_name": {"type": "string"}}, "required": ["target", "property_name"]}},
            {"name": "godot_validate_set_properties", "description": "Validate properties before applying them. Returns errors for invalid properties/types/values without modifying anything.", "inputSchema": {"type": "object", "properties": {"node_path": {"type": "string"}, "properties": {"type": "object"}}, "required": ["node_path", "properties"]}},
            {"name": "godot_catalog_get", "description": "Get catalog of valid options for meshes, shapes, lights, etc. with parameters and examples.", "inputSchema": {"type": "object", "properties": {"kind": {"type": "string", "description": "mesh, shape2d, shape3d, light2d, light3d, audio, loop_mode, background_mode, node_2d, node_3d, node_ui"}}, "required": ["kind"]}},
            {"name": "godot_resource_get_info", "description": "Get information about a resource file (.tres/.res) including class, properties, and subresources.", "inputSchema": {"type": "object", "properties": {"resource_path": {"type": "string"}}, "required": ["resource_path"]}},
            {"name": "godot_animation_get_info", "description": "Get detailed Animation resource info: length, loop mode, tracks with paths and keys.", "inputSchema": {"type": "object", "properties": {"animation_path": {"type": "string"}}, "required": ["animation_path"]}},
            {"name": "godot_spriteframes_get_info", "description": "Get SpriteFrames resource info: animations with fps, loop, frame count and texture paths.", "inputSchema": {"type": "object", "properties": {"spriteframes_path": {"type": "string"}}, "required": ["spriteframes_path"]}},
            {"name": "godot_texture_get_info", "description": "Get texture info: dimensions, format, alpha, and grid suggestions for spritesheets.", "inputSchema": {"type": "object", "properties": {"texture_path": {"type": "string"}}, "required": ["texture_path"]}},
        ]
    
    def connect_godot(self):
        """Connect to Godot."""
        ws_url = os.environ.get('GODOT_WS_URL', 'ws://127.0.0.1:49631')
        token = os.environ.get('GODOT_TOKEN', '')
        
        if not token:
            token_file = os.environ.get('GODOT_TOKEN_FILE')
            if token_file and os.path.exists(token_file):
                with open(token_file) as f:
                    data = json.load(f)
                    token = data.get('token', '')
        
        self.godot = GodotRPCClient(ws_url, token)
        return self.godot.connect()
    
    def handle_tool_call(self, name, arguments):
        """Handle a tool call."""
        if not self.godot or not self.godot.authenticated:
            if not self.connect_godot():
                return json.dumps({"error": "Failed to connect to Godot. Is the editor running with the plugin enabled?"})
        
        try:
            result = self._execute_tool(name, arguments)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Tool error: {e}")
            return json.dumps({"error": str(e)})
    
    def _execute_tool(self, name, args):
        """Execute a tool."""
        tool_map = {
            # Project
            "godot_get_project_info": ("project.get_info", {}),
            "godot_add_input_action": ("project.add_input_action", {"action_name": args.get("action_name"), "key": args.get("key")}),
            "godot_remove_input_action": ("project.remove_input_action", {"action_name": args.get("action_name")}),
            
            # Editor
            "godot_get_editor_state": ("editor.get_state", {}),
            "godot_open_scene": ("editor.open_scene", {"scene_path": args.get("scene_path")}),
            "godot_save_scene": ("editor.save_scene", {"scene_path": args.get("scene_path")}),
            
            # Scene
            "godot_create_scene": ("scene.create_scene", {"root_type": args.get("root_type", "Node3D"), "root_name": args.get("root_name", "Root"), "scene_path": args.get("scene_path")}),
            "godot_instance_scene": ("scene.instance_scene", {"parent_path": args.get("parent_path"), "scene_path": args.get("scene_path"), "name": args.get("name", "")}),
            "godot_get_scene_tree": ("scene.get_tree", {}),
            "godot_list_nodes": ("scene.list_nodes", {"parent_path": args.get("parent_path", "")}),
            "godot_get_node_properties": ("scene.get_node_properties", {"node_path": args.get("node_path"), "keys": args.get("keys")}),
            "godot_set_node_properties": ("scene.set_node_properties", {"node_path": args.get("node_path"), "properties": args.get("properties", {})}),
            "godot_add_node": ("scene.add_node", {"parent_path": args.get("parent_path"), "type": args.get("type"), "name": args.get("name"), "properties": args.get("properties", {})}),
            "godot_remove_node": ("scene.remove_node", {"node_path": args.get("node_path")}),
            
            # Mesh
            "godot_create_mesh": ("scene.create_mesh", {"node_path": args.get("node_path"), "mesh_type": args.get("mesh_type"), "mesh_params": args.get("mesh_params", {})}),
            
            # Materials
            "godot_create_material": ("resources.create_material", {"node_path": args.get("node_path"), "material_type": args.get("material_type", "StandardMaterial3D"), "properties": args.get("properties", {}), "surface_index": args.get("surface_index", 0)}),
            "godot_set_material": ("resources.set_material", {"node_path": args.get("node_path"), "material_path": args.get("material_path"), "surface_index": args.get("surface_index", 0)}),
            
            # Sprites/Textures
            "godot_set_sprite_texture": ("resources.set_sprite_texture", {"node_path": args.get("node_path"), "texture_path": args.get("texture_path"), "region_enabled": args.get("region_enabled", False), "region_rect": args.get("region_rect"), "hframes": args.get("hframes", 1), "vframes": args.get("vframes", 1), "frame": args.get("frame", 0)}),
            "godot_set_modulate": ("resources.set_modulate", {"node_path": args.get("node_path"), "color": args.get("color", {}), "self_modulate": args.get("self_modulate", False)}),
            
            # Collision
            "godot_create_collision_shape": ("resources.create_collision_shape", {"node_path": args.get("node_path"), "shape_type": args.get("shape_type"), "shape_params": args.get("shape_params", {})}),
            
            # Lights
            "godot_create_light": ("resources.create_light", {"parent_path": args.get("parent_path"), "light_type": args.get("light_type", "DirectionalLight3D"), "name": args.get("name", "Light"), "properties": args.get("properties", {})}),
            
            # Camera
            "godot_configure_camera": ("resources.configure_camera", {"node_path": args.get("node_path"), "properties": args.get("properties", {})}),
            
            # Environment
            "godot_create_environment": ("resources.create_environment", {"node_path": args.get("node_path", ""), "properties": args.get("properties", {})}),
            
            # Audio
            "godot_create_audio_player": ("resources.create_audio_player", {"parent_path": args.get("parent_path"), "audio_type": args.get("audio_type", "AudioStreamPlayer"), "name": args.get("name", "AudioPlayer"), "stream_path": args.get("stream_path", ""), "properties": args.get("properties", {})}),
            
            # Script
            "godot_read_script": ("filesystem.read_text", {"path": args.get("path")}),
            "godot_write_script": ("filesystem.write_text", {"path": args.get("path"), "content": args.get("content")}),
            "godot_assign_script": ("scene.assign_script", {"node_path": args.get("node_path"), "script_path": args.get("script_path")}),
            
            # Play
            "godot_run_main": ("play.run_main", {}),
            "godot_run_current": ("play.run_current", {}),
            "godot_stop": ("play.stop", {}),
            
            # Files
            "godot_search_files": ("filesystem.search", {"query": args.get("query", ""), "type": args.get("type"), "folder": args.get("folder", "res://")}),
            
            # Sprite2D Grid
            "godot_sprite2d_set_texture": ("sprite2d.set_texture", {"node_path": args.get("node_path"), "texture_path": args.get("texture_path")}),
            "godot_sprite2d_set_grid": ("sprite2d.set_grid", {"node_path": args.get("node_path"), "hframes": args.get("hframes", 1), "vframes": args.get("vframes", 1)}),
            "godot_sprite2d_set_frame": ("sprite2d.set_frame", {"node_path": args.get("node_path"), "frame": args.get("frame", 0)}),
            "godot_sprite2d_set_frame_coords": ("sprite2d.set_frame_coords", {"node_path": args.get("node_path"), "x": args.get("x", 0), "y": args.get("y", 0)}),
            "godot_sprite2d_get_grid": ("sprite2d.get_grid", {"node_path": args.get("node_path")}),
            
            # Sprite2D Region
            "godot_sprite2d_enable_region": ("sprite2d.enable_region", {"node_path": args.get("node_path"), "enabled": args.get("enabled", True)}),
            "godot_sprite2d_set_region_rect": ("sprite2d.set_region_rect", {"node_path": args.get("node_path"), "x": args.get("x", 0), "y": args.get("y", 0), "w": args.get("w", 0), "h": args.get("h", 0)}),
            "godot_sprite2d_set_region_clip": ("sprite2d.set_region_clip", {"node_path": args.get("node_path"), "enabled": args.get("enabled", True)}),
            
            # AtlasTexture
            "godot_atlas_create": ("atlas.create", {"texture_path": args.get("texture_path"), "rect": args.get("rect", {}), "margin": args.get("margin"), "save_path": args.get("save_path")}),
            "godot_atlas_batch_create": ("atlas.batch_create", {"texture_path": args.get("texture_path"), "rects": args.get("rects", []), "margin": args.get("margin"), "save_folder": args.get("save_folder")}),
            "godot_node_set_texture": ("atlas.set_texture", {"node_path": args.get("node_path"), "texture_path": args.get("texture_path")}),
            
            # SpriteFrames
            "godot_spriteframes_create": ("spriteframes.create", {"save_path": args.get("save_path")}),
            "godot_spriteframes_add_animation": ("spriteframes.add_animation", {"spriteframes_path": args.get("spriteframes_path"), "animation_name": args.get("animation_name")}),
            "godot_spriteframes_set_fps": ("spriteframes.set_fps", {"spriteframes_path": args.get("spriteframes_path"), "animation_name": args.get("animation_name"), "fps": args.get("fps", 10)}),
            "godot_spriteframes_set_loop": ("spriteframes.set_loop", {"spriteframes_path": args.get("spriteframes_path"), "animation_name": args.get("animation_name"), "loop": args.get("loop", True)}),
            "godot_spriteframes_add_frame": ("spriteframes.add_frame", {"spriteframes_path": args.get("spriteframes_path"), "animation_name": args.get("animation_name"), "texture_path": args.get("texture_path"), "duration": args.get("duration", 1.0), "at_position": args.get("at_position", -1)}),
            "godot_spriteframes_remove_frame": ("spriteframes.remove_frame", {"spriteframes_path": args.get("spriteframes_path"), "animation_name": args.get("animation_name"), "frame_index": args.get("frame_index", 0)}),
            "godot_spriteframes_rename_animation": ("spriteframes.rename_animation", {"spriteframes_path": args.get("spriteframes_path"), "old_name": args.get("old_name"), "new_name": args.get("new_name")}),
            "godot_spriteframes_list_animations": ("spriteframes.list_animations", {"spriteframes_path": args.get("spriteframes_path")}),
            
            # AnimatedSprite2D
            "godot_animsprite_attach": ("animsprite.attach", {"node_path": args.get("node_path"), "spriteframes_path": args.get("spriteframes_path")}),
            "godot_animsprite_play": ("animsprite.play", {"node_path": args.get("node_path"), "animation_name": args.get("animation_name"), "custom_speed": args.get("custom_speed", 1.0), "from_end": args.get("from_end", False)}),
            "godot_animsprite_stop": ("animsprite.stop", {"node_path": args.get("node_path")}),
            "godot_animsprite_pause": ("animsprite.pause", {"node_path": args.get("node_path")}),
            "godot_animsprite_set_speed": ("animsprite.set_speed", {"node_path": args.get("node_path"), "speed_scale": args.get("speed_scale", 1.0)}),
            
            # Animation
            "godot_animation_create": ("animation.create", {"name": args.get("name"), "length": args.get("length", 1.0), "loop_mode": args.get("loop_mode", "none"), "step": args.get("step", 0.1), "save_path": args.get("save_path")}),
            "godot_animation_add_track": ("animation.add_track", {"animation_path": args.get("animation_path"), "node_path": args.get("node_path"), "property": args.get("property")}),
            "godot_animation_insert_key": ("animation.insert_key", {"animation_path": args.get("animation_path"), "track_index": args.get("track_index", 0), "time": args.get("time", 0), "value": args.get("value")}),
            
            # AnimationPlayer
            "godot_animplayer_add_animation": ("animplayer.add_animation", {"node_path": args.get("node_path"), "animation_name": args.get("animation_name"), "animation_path": args.get("animation_path")}),
            "godot_animplayer_play": ("animplayer.play", {"node_path": args.get("node_path"), "animation_name": args.get("animation_name"), "custom_blend": args.get("custom_blend", -1), "custom_speed": args.get("custom_speed", 1.0), "from_end": args.get("from_end", False)}),
            "godot_animplayer_stop": ("animplayer.stop", {"node_path": args.get("node_path"), "keep_state": args.get("keep_state", False)}),
            
            # TileSet
            "godot_tileset_ensure_atlas": ("tileset.ensure_atlas", {"tileset_path": args.get("tileset_path"), "texture_path": args.get("texture_path"), "tile_size": args.get("tile_size", {}), "margins": args.get("margins"), "separation": args.get("separation")}),
            "godot_tileset_create_tile": ("tileset.create_tile", {"tileset_path": args.get("tileset_path"), "source_id": args.get("source_id", 0), "atlas_coords": args.get("atlas_coords", {}), "size": args.get("size")}),
            "godot_tileset_list_tiles": ("tileset.list_tiles", {"tileset_path": args.get("tileset_path"), "source_id": args.get("source_id", 0)}),
            
            # Introspection
            "godot_class_get_property_list": ("introspect.class_properties", {"class_name": args.get("class_name")}),
            "godot_node_get_property_list": ("introspect.node_properties", {"node_path": args.get("node_path")}),
            "godot_property_describe": ("introspect.property_describe", {"target": args.get("target"), "property_name": args.get("property_name")}),
            "godot_validate_set_properties": ("introspect.validate_properties", {"node_path": args.get("node_path"), "properties": args.get("properties", {})}),
            "godot_catalog_get": ("introspect.catalog", {"kind": args.get("kind")}),
            "godot_resource_get_info": ("introspect.resource_info", {"resource_path": args.get("resource_path")}),
            "godot_animation_get_info": ("introspect.animation_info", {"animation_path": args.get("animation_path")}),
            "godot_spriteframes_get_info": ("introspect.spriteframes_info", {"spriteframes_path": args.get("spriteframes_path")}),
            "godot_texture_get_info": ("introspect.texture_info", {"texture_path": args.get("texture_path")}),
        }
        
        if name not in tool_map:
            raise Exception(f"Unknown tool: {name}")
        
        method, params = tool_map[name]
        return self.godot.call(method, params)
    
    def send_response(self, msg_id, result):
        """Send JSON-RPC response."""
        response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
        output = json.dumps(response)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    
    def send_error(self, msg_id, code, message):
        """Send JSON-RPC error."""
        response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
        output = json.dumps(response)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    
    def handle_message(self, message):
        """Handle incoming MCP message."""
        method = message.get("method", "")
        msg_id = message.get("id")
        params = message.get("params", {})
        
        logger.debug(f"Received: {method}")
        
        if method == "initialize":
            self.send_response(msg_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "godot-mcp-bridge", "version": "1.0.0"}
            })
        
        elif method == "notifications/initialized":
            pass  # No response needed for notifications
        
        elif method == "tools/list":
            self.send_response(msg_id, {"tools": self.tools})
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = self.handle_tool_call(tool_name, tool_args)
            self.send_response(msg_id, {"content": [{"type": "text", "text": result}]})
        
        elif method == "resources/list":
            self.send_response(msg_id, {"resources": []})
        
        elif method == "prompts/list":
            self.send_response(msg_id, {"prompts": []})
        
        else:
            if msg_id is not None:
                self.send_error(msg_id, -32601, f"Method not found: {method}")
    
    def run(self):
        """Run the MCP server - synchronous stdin reading."""
        logger.info("Godot MCP Bridge starting...")
        
        # Simple synchronous stdin reading
        for line in sys.stdin:
            try:
                line = line.strip()
                if not line:
                    continue
                
                message = json.loads(line)
                self.handle_message(message)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON error: {e}")
            except Exception as e:
                logger.exception(f"Error: {e}")


def main():
    server = MCPServer()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
