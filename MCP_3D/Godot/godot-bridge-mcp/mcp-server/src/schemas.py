"""Pydantic schemas for MCP tools input validation."""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import re


class NodePathMixin:
    """Mixin for node path validation."""
    
    @field_validator('node_path', 'parent_path', 'from_path', 'to_path', 'new_parent_path', mode='before', check_fields=False)
    @classmethod
    def validate_node_path(cls, v: str) -> str:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError('Node path must be a string')
        if v and '..' in v:
            raise ValueError('Path traversal (..) not allowed')
        return v


class ResPathMixin:
    """Mixin for res:// path validation."""
    
    @field_validator('scene_path', 'path', mode='before', check_fields=False)
    @classmethod
    def validate_res_path(cls, v: str) -> str:
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError('Path must be a string')
        if v and not v.startswith('res://'):
            raise ValueError('Path must start with res://')
        if '..' in v:
            raise ValueError('Path traversal (..) not allowed')
        return v


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class GetProjectInfoParams(BaseModel):
    """Parameters for godot_get_project_info tool."""
    pass


# ============================================================================
# EDITOR SCHEMAS
# ============================================================================

class GetEditorStateParams(BaseModel):
    """Parameters for godot_get_editor_state tool."""
    pass


class OpenSceneParams(BaseModel, ResPathMixin):
    """Parameters for godot_open_scene tool."""
    scene_path: str = Field(..., description="Path to the scene file (res://...)")


class SaveSceneParams(BaseModel, ResPathMixin):
    """Parameters for godot_save_scene tool."""
    scene_path: Optional[str] = Field(None, description="Path to save scene (optional, uses current if not specified)")


# ============================================================================
# SCENE SCHEMAS
# ============================================================================

class ListNodesParams(BaseModel, NodePathMixin):
    """Parameters for godot_list_nodes tool."""
    scene_path: Optional[str] = Field(None, description="Scene path (optional, uses current scene)")
    parent_path: Optional[str] = Field(None, description="Parent node path to list children of")


class GetNodePropertiesParams(BaseModel, NodePathMixin):
    """Parameters for godot_get_node_properties tool."""
    node_path: str = Field(..., description="Path to the node")
    keys: Optional[list[str]] = Field(None, description="Specific property keys to retrieve")


class SetNodePropertiesParams(BaseModel, NodePathMixin):
    """Parameters for godot_set_node_properties tool."""
    node_path: str = Field(..., description="Path to the node")
    properties: dict[str, Any] = Field(..., description="Properties to set")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


class AddNodeParams(BaseModel, NodePathMixin):
    """Parameters for godot_add_node tool."""
    parent_path: str = Field(..., description="Path to the parent node")
    type: str = Field(..., description="Node type to create (e.g., 'Button', 'Sprite2D')")
    name: str = Field(..., description="Name for the new node")
    properties: Optional[dict[str, Any]] = Field(None, description="Initial properties to set")
    use_undo: bool = Field(True, description="Whether to use undo/redo")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        if not v:
            raise ValueError('Node type cannot be empty')
        if not re.match(r'^[A-Za-z][A-Za-z0-9]*$', v):
            raise ValueError('Invalid node type format')
        return v
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v:
            raise ValueError('Node name cannot be empty')
        invalid_chars = ['.', ':', '/', '@', '%']
        for c in invalid_chars:
            if c in v:
                raise ValueError(f'Node name contains invalid character: {c}')
        return v


class RemoveNodeParams(BaseModel, NodePathMixin):
    """Parameters for godot_remove_node tool."""
    node_path: str = Field(..., description="Path to the node to remove")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


class RenameNodeParams(BaseModel, NodePathMixin):
    """Parameters for godot_rename_node tool."""
    node_path: str = Field(..., description="Path to the node")
    new_name: str = Field(..., description="New name for the node")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


class DuplicateNodeParams(BaseModel, NodePathMixin):
    """Parameters for godot_duplicate_node tool."""
    node_path: str = Field(..., description="Path to the node to duplicate")
    new_name: Optional[str] = Field(None, description="Name for the duplicate")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


# ============================================================================
# SIGNALS SCHEMAS
# ============================================================================

class ConnectSignalParams(BaseModel, NodePathMixin):
    """Parameters for godot_connect_signal tool."""
    from_path: str = Field(..., description="Path to the source node")
    signal: str = Field(..., description="Signal name")
    to_path: str = Field(..., description="Path to the target node")
    method: str = Field(..., description="Method name to call")
    flags: int = Field(0, description="Connection flags")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


class DisconnectSignalParams(BaseModel, NodePathMixin):
    """Parameters for godot_disconnect_signal tool."""
    from_path: str = Field(..., description="Path to the source node")
    signal: str = Field(..., description="Signal name")
    to_path: str = Field(..., description="Path to the target node")
    method: str = Field(..., description="Method name")
    use_undo: bool = Field(True, description="Whether to use undo/redo")


class ListSignalsParams(BaseModel, NodePathMixin):
    """Parameters for godot_list_signals tool."""
    node_path: str = Field(..., description="Path to the node")


# ============================================================================
# FILESYSTEM SCHEMAS
# ============================================================================

class ReadScriptParams(BaseModel, ResPathMixin):
    """Parameters for godot_read_script tool."""
    path: str = Field(..., description="Path to the script file (res://...)")


class WriteScriptParams(BaseModel, ResPathMixin):
    """Parameters for godot_write_script tool."""
    path: str = Field(..., description="Path to the script file (res://...)")
    content: str = Field(..., description="Script content")
    create_dirs: bool = Field(False, description="Create parent directories if needed")


class SearchFilesParams(BaseModel):
    """Parameters for godot_search_files tool."""
    query: str = Field("", description="Search query")
    type: Optional[str] = Field(None, description="File type filter (e.g., 'gd', 'tscn')")
    folder: str = Field("res://", description="Folder to search in")
    limit: int = Field(100, description="Maximum number of results")


# ============================================================================
# PLAY SCHEMAS
# ============================================================================

class PlayParams(BaseModel):
    """Parameters for play tools."""
    pass


class GetSceneTreeParams(BaseModel, ResPathMixin):
    """Parameters for godot_get_scene_tree tool."""
    scene_path: Optional[str] = Field(None, description="Scene path (optional, uses current scene)")
