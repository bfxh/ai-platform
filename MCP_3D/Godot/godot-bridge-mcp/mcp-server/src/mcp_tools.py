"""MCP Tools for Godot Editor integration."""

import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import ValidationError

from .rpc_client import call_godot, RPCError
from .schemas import (
    GetProjectInfoParams,
    GetEditorStateParams,
    OpenSceneParams,
    SaveSceneParams,
    ListNodesParams,
    GetNodePropertiesParams,
    SetNodePropertiesParams,
    AddNodeParams,
    RemoveNodeParams,
    RenameNodeParams,
    DuplicateNodeParams,
    ConnectSignalParams,
    DisconnectSignalParams,
    ListSignalsParams,
    ReadScriptParams,
    WriteScriptParams,
    SearchFilesParams,
    PlayParams,
    GetSceneTreeParams,
)


logger = logging.getLogger(__name__)


def format_result(result: Any) -> list[TextContent]:
    """Format a result as MCP text content."""
    import json
    if isinstance(result, dict) or isinstance(result, list):
        text = json.dumps(result, indent=2)
    else:
        text = str(result)
    return [TextContent(type="text", text=text)]


def format_error(error: Exception) -> list[TextContent]:
    """Format an error as MCP text content."""
    if isinstance(error, RPCError):
        text = f"Error {error.code}: {error.message}"
        if error.data:
            import json
            text += f"\nDetails: {json.dumps(error.data)}"
    elif isinstance(error, ValidationError):
        text = f"Validation Error: {error}"
    else:
        text = f"Error: {str(error)}"
    return [TextContent(type="text", text=text)]


def register_tools(server: Server) -> None:
    """Register all MCP tools with the server."""
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools."""
        return [
            # Project tools
            Tool(
                name="godot_get_project_info",
                description="Get information about the current Godot project including name, version, main scene, and features.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="godot_get_autoloads",
                description="Get the list of autoload singletons configured in the project.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Editor tools
            Tool(
                name="godot_get_editor_state",
                description="Get the current editor state including open scenes, active scene, and selection.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="godot_open_scene",
                description="Open a scene file in the editor.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scene_path": {
                            "type": "string",
                            "description": "Path to the scene file (e.g., res://scenes/Main.tscn)"
                        }
                    },
                    "required": ["scene_path"]
                }
            ),
            Tool(
                name="godot_save_scene",
                description="Save the current or specified scene.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scene_path": {
                            "type": "string",
                            "description": "Optional path to save the scene to. If not specified, saves current scene."
                        }
                    },
                    "required": []
                }
            ),
            
            # Scene tools
            Tool(
                name="godot_get_scene_tree",
                description="Get the full scene tree hierarchy of the current or specified scene.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scene_path": {
                            "type": "string",
                            "description": "Optional scene path. Uses current scene if not specified."
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="godot_list_nodes",
                description="List nodes in the current scene, optionally under a specific parent.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scene_path": {
                            "type": "string",
                            "description": "Optional scene path"
                        },
                        "parent_path": {
                            "type": "string",
                            "description": "Optional parent node path to list children of"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="godot_get_node_properties",
                description="Get properties of a specific node.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node (e.g., /root/Main/Player)"
                        },
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of specific property keys to retrieve"
                        }
                    },
                    "required": ["node_path"]
                }
            ),
            Tool(
                name="godot_set_node_properties",
                description="Set properties on a node. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Properties to set as key-value pairs"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["node_path", "properties"]
                }
            ),
            Tool(
                name="godot_add_node",
                description="Add a new node to the scene. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "parent_path": {
                            "type": "string",
                            "description": "Path to the parent node"
                        },
                        "type": {
                            "type": "string",
                            "description": "Node type to create (e.g., 'Button', 'Sprite2D', 'Node3D')"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name for the new node"
                        },
                        "properties": {
                            "type": "object",
                            "description": "Optional initial properties to set"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["parent_path", "type", "name"]
                }
            ),
            Tool(
                name="godot_remove_node",
                description="Remove a node from the scene. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node to remove"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["node_path"]
                }
            ),
            Tool(
                name="godot_rename_node",
                description="Rename a node. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "New name for the node"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["node_path", "new_name"]
                }
            ),
            Tool(
                name="godot_duplicate_node",
                description="Duplicate a node. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node to duplicate"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "Optional name for the duplicate"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["node_path"]
                }
            ),
            
            # Signal tools
            Tool(
                name="godot_list_signals",
                description="List all signals available on a node.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node"
                        }
                    },
                    "required": ["node_path"]
                }
            ),
            Tool(
                name="godot_list_connections",
                description="List all signal connections on a node.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_path": {
                            "type": "string",
                            "description": "Path to the node"
                        }
                    },
                    "required": ["node_path"]
                }
            ),
            Tool(
                name="godot_connect_signal",
                description="Connect a signal from one node to a method on another node. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_path": {
                            "type": "string",
                            "description": "Path to the source node"
                        },
                        "signal": {
                            "type": "string",
                            "description": "Name of the signal to connect"
                        },
                        "to_path": {
                            "type": "string",
                            "description": "Path to the target node"
                        },
                        "method": {
                            "type": "string",
                            "description": "Name of the method to call"
                        },
                        "flags": {
                            "type": "integer",
                            "description": "Optional connection flags",
                            "default": 0
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["from_path", "signal", "to_path", "method"]
                }
            ),
            Tool(
                name="godot_disconnect_signal",
                description="Disconnect a signal connection. Supports undo/redo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_path": {
                            "type": "string",
                            "description": "Path to the source node"
                        },
                        "signal": {
                            "type": "string",
                            "description": "Name of the signal"
                        },
                        "to_path": {
                            "type": "string",
                            "description": "Path to the target node"
                        },
                        "method": {
                            "type": "string",
                            "description": "Name of the method"
                        },
                        "use_undo": {
                            "type": "boolean",
                            "description": "Whether to use undo/redo (default: true)",
                            "default": True
                        }
                    },
                    "required": ["from_path", "signal", "to_path", "method"]
                }
            ),
            
            # Filesystem tools
            Tool(
                name="godot_read_script",
                description="Read the content of a script file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the script file (e.g., res://scripts/player.gd)"
                        }
                    },
                    "required": ["path"]
                }
            ),
            Tool(
                name="godot_write_script",
                description="Write content to a script file.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the script file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Script content to write"
                        },
                        "create_dirs": {
                            "type": "boolean",
                            "description": "Create parent directories if needed",
                            "default": False
                        }
                    },
                    "required": ["path", "content"]
                }
            ),
            Tool(
                name="godot_search_files",
                description="Search for files in the project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (matches file names)"
                        },
                        "type": {
                            "type": "string",
                            "description": "File type filter (e.g., 'gd', 'tscn', 'tres')"
                        },
                        "folder": {
                            "type": "string",
                            "description": "Folder to search in (default: res://)",
                            "default": "res://"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 100
                        }
                    },
                    "required": []
                }
            ),
            
            # Play tools
            Tool(
                name="godot_run_main",
                description="Run the main scene in the editor.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="godot_run_current",
                description="Run the current scene in the editor.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="godot_stop",
                description="Stop the running scene.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="godot_get_play_state",
                description="Get the current play state (running or not).",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls."""
        try:
            result = await _execute_tool(name, arguments)
            return format_result(result)
        except (RPCError, ValidationError) as e:
            return format_error(e)
        except Exception as e:
            logger.exception(f"Error executing tool {name}")
            return format_error(e)


async def _execute_tool(name: str, arguments: dict) -> Any:
    """Execute a tool and return the result."""
    
    # Project tools
    if name == "godot_get_project_info":
        return await call_godot("project.get_info")
    
    elif name == "godot_get_autoloads":
        return await call_godot("project.get_autoloads")
    
    # Editor tools
    elif name == "godot_get_editor_state":
        return await call_godot("editor.get_state")
    
    elif name == "godot_open_scene":
        params = OpenSceneParams(**arguments)
        return await call_godot("editor.open_scene", {"scene_path": params.scene_path})
    
    elif name == "godot_save_scene":
        params = SaveSceneParams(**arguments)
        return await call_godot("editor.save_scene", {"scene_path": params.scene_path})
    
    # Scene tools
    elif name == "godot_get_scene_tree":
        params = GetSceneTreeParams(**arguments)
        return await call_godot("scene.get_tree", {"scene_path": params.scene_path})
    
    elif name == "godot_list_nodes":
        params = ListNodesParams(**arguments)
        return await call_godot("scene.list_nodes", {
            "scene_path": params.scene_path,
            "parent_path": params.parent_path
        })
    
    elif name == "godot_get_node_properties":
        params = GetNodePropertiesParams(**arguments)
        return await call_godot("scene.get_node_properties", {
            "node_path": params.node_path,
            "keys": params.keys
        })
    
    elif name == "godot_set_node_properties":
        params = SetNodePropertiesParams(**arguments)
        return await call_godot("scene.set_node_properties", {
            "node_path": params.node_path,
            "properties": params.properties,
            "use_undo": params.use_undo
        })
    
    elif name == "godot_add_node":
        params = AddNodeParams(**arguments)
        return await call_godot("scene.add_node", {
            "parent_path": params.parent_path,
            "type": params.type,
            "name": params.name,
            "properties": params.properties or {},
            "use_undo": params.use_undo
        })
    
    elif name == "godot_remove_node":
        params = RemoveNodeParams(**arguments)
        return await call_godot("scene.remove_node", {
            "node_path": params.node_path,
            "use_undo": params.use_undo
        })
    
    elif name == "godot_rename_node":
        params = RenameNodeParams(**arguments)
        return await call_godot("scene.rename_node", {
            "node_path": params.node_path,
            "new_name": params.new_name,
            "use_undo": params.use_undo
        })
    
    elif name == "godot_duplicate_node":
        params = DuplicateNodeParams(**arguments)
        return await call_godot("scene.duplicate_node", {
            "node_path": params.node_path,
            "new_name": params.new_name,
            "use_undo": params.use_undo
        })
    
    # Signal tools
    elif name == "godot_list_signals":
        params = ListSignalsParams(**arguments)
        return await call_godot("signals.list", {"node_path": params.node_path})
    
    elif name == "godot_list_connections":
        params = ListSignalsParams(**arguments)
        return await call_godot("signals.list_connections", {"node_path": params.node_path})
    
    elif name == "godot_connect_signal":
        params = ConnectSignalParams(**arguments)
        return await call_godot("signals.connect", {
            "from_path": params.from_path,
            "signal": params.signal,
            "to_path": params.to_path,
            "method": params.method,
            "flags": params.flags,
            "use_undo": params.use_undo
        })
    
    elif name == "godot_disconnect_signal":
        params = DisconnectSignalParams(**arguments)
        return await call_godot("signals.disconnect", {
            "from_path": params.from_path,
            "signal": params.signal,
            "to_path": params.to_path,
            "method": params.method,
            "use_undo": params.use_undo
        })
    
    # Filesystem tools
    elif name == "godot_read_script":
        params = ReadScriptParams(**arguments)
        return await call_godot("filesystem.read_text", {"path": params.path})
    
    elif name == "godot_write_script":
        params = WriteScriptParams(**arguments)
        return await call_godot("filesystem.write_text", {
            "path": params.path,
            "content": params.content,
            "create_dirs": params.create_dirs
        })
    
    elif name == "godot_search_files":
        params = SearchFilesParams(**arguments)
        return await call_godot("filesystem.search", {
            "query": params.query,
            "type": params.type,
            "folder": params.folder,
            "limit": params.limit
        })
    
    # Play tools
    elif name == "godot_run_main":
        return await call_godot("play.run_main")
    
    elif name == "godot_run_current":
        return await call_godot("play.run_current")
    
    elif name == "godot_stop":
        return await call_godot("play.stop")
    
    elif name == "godot_get_play_state":
        return await call_godot("play.get_state")
    
    else:
        raise ValueError(f"Unknown tool: {name}")
