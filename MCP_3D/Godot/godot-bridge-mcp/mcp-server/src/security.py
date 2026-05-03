"""Security utilities for the MCP server."""

import os
import json
import re
from pathlib import Path
from typing import Optional


# Maximum message size (1MB)
MAX_MESSAGE_SIZE = 1048576

# Maximum content length for scripts
MAX_CONTENT_LENGTH = 500000


def get_token_file_path() -> Optional[Path]:
    """Get the path to the Godot token file.
    
    The token file is stored in the Godot user data directory.
    On Windows: %APPDATA%/Godot/app_userdata/{ProjectName}/godotbridge_token.txt
    On Linux: ~/.local/share/godot/app_userdata/{ProjectName}/godotbridge_token.txt
    On macOS: ~/Library/Application Support/Godot/app_userdata/{ProjectName}/godotbridge_token.txt
    
    For simplicity, we also check user://godotbridge_token.txt which is the relative path.
    """
    # Check environment variable first
    token_file = os.environ.get('GODOT_TOKEN_FILE')
    if token_file:
        path = Path(token_file)
        if path.exists():
            return path
    
    return None


def load_token_from_file(file_path: Path) -> Optional[dict]:
    """Load token data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data
    except (json.JSONDecodeError, FileNotFoundError, PermissionError):
        return None


def get_token() -> Optional[str]:
    """Get the authentication token.
    
    Priority:
    1. GODOT_TOKEN environment variable
    2. Token file specified by GODOT_TOKEN_FILE
    """
    # Check environment variable
    token = os.environ.get('GODOT_TOKEN')
    if token:
        return token
    
    # Check token file
    token_file = get_token_file_path()
    if token_file:
        data = load_token_from_file(token_file)
        if data and 'token' in data:
            return data['token']
    
    return None


def get_ws_url() -> str:
    """Get the WebSocket URL for connecting to Godot."""
    return os.environ.get('GODOT_WS_URL', 'ws://127.0.0.1:49631')


def validate_res_path(path: str) -> bool:
    """Validate that a path is a valid res:// path."""
    if not path:
        return False
    if not path.startswith('res://'):
        return False
    if '..' in path:
        return False
    if '\x00' in path:
        return False
    return True


def validate_node_path(path: str) -> bool:
    """Validate a node path."""
    if not path:
        return False
    if '..' in path:
        return False
    if '\x00' in path:
        return False
    return True


def validate_node_name(name: str) -> bool:
    """Validate a node name."""
    if not name:
        return False
    invalid_chars = ['.', ':', '/', '@', '%']
    for c in invalid_chars:
        if c in name:
            return False
    return True


def validate_node_type(type_name: str) -> bool:
    """Validate a node type name."""
    if not type_name:
        return False
    # Node types should be PascalCase class names
    if not re.match(r'^[A-Za-z][A-Za-z0-9]*$', type_name):
        return False
    return True


def sanitize_content(content: str) -> str:
    """Sanitize script content."""
    if len(content) > MAX_CONTENT_LENGTH:
        raise ValueError(f"Content too large (max {MAX_CONTENT_LENGTH} bytes)")
    return content
