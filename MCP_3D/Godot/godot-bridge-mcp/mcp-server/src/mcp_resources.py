"""MCP Resources for Godot Editor integration."""

import json
import logging
import time
from typing import Any, Optional
from dataclasses import dataclass, field

from mcp.server import Server
from mcp.types import Resource, TextResourceContents

from .rpc_client import call_godot, RPCError


logger = logging.getLogger(__name__)


@dataclass
class CachedResource:
    """A cached resource with TTL."""
    data: Any
    timestamp: float
    ttl: float = 5.0  # Default TTL of 5 seconds
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class ResourceCache:
    """Simple in-memory cache for resources."""
    
    def __init__(self):
        self._cache: dict[str, CachedResource] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value if it exists and is not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired:
                return entry.data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: float = 5.0) -> None:
        """Set a cached value with TTL."""
        self._cache[key] = CachedResource(
            data=data,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        self._cache.pop(key, None)
    
    def invalidate_all(self) -> None:
        """Invalidate all cache entries."""
        self._cache.clear()


# Global cache instance
_cache = ResourceCache()


def register_resources(server: Server) -> None:
    """Register all MCP resources with the server."""
    
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List all available resources."""
        return [
            Resource(
                uri="godot://project/summary",
                name="Project Summary",
                description="Complete project information including name, version, main scene, autoloads, and input map.",
                mimeType="application/json"
            ),
            Resource(
                uri="godot://editor/state",
                name="Editor State",
                description="Current editor state including open scenes, active scene, and selection.",
                mimeType="application/json"
            ),
            Resource(
                uri="godot://scene/tree",
                name="Scene Tree",
                description="Full scene tree hierarchy of the currently active scene.",
                mimeType="application/json"
            ),
            Resource(
                uri="godot://logs/recent",
                name="Recent Logs",
                description="Recent log entries from the editor.",
                mimeType="application/json"
            ),
        ]
    
    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource by URI."""
        try:
            # Check cache first
            cached = _cache.get(uri)
            if cached is not None:
                return json.dumps(cached, indent=2)
            
            # Fetch fresh data
            data = await _fetch_resource(uri)
            
            # Cache with appropriate TTL
            ttl = 5.0  # Default TTL
            if uri == "godot://logs/recent":
                ttl = 1.0  # Shorter TTL for logs
            elif uri == "godot://project/summary":
                ttl = 30.0  # Longer TTL for project info
            
            _cache.set(uri, data, ttl)
            
            return json.dumps(data, indent=2)
            
        except RPCError as e:
            error_data = {
                "error": True,
                "code": e.code,
                "message": e.message,
                "data": e.data
            }
            return json.dumps(error_data, indent=2)
        except Exception as e:
            logger.exception(f"Error reading resource {uri}")
            error_data = {
                "error": True,
                "message": str(e)
            }
            return json.dumps(error_data, indent=2)


async def _fetch_resource(uri: str) -> Any:
    """Fetch resource data from Godot."""
    
    if uri == "godot://project/summary":
        # Combine multiple API calls for a complete summary
        project_info = await call_godot("project.get_info")
        autoloads = await call_godot("project.get_autoloads")
        input_map = await call_godot("project.get_input_map")
        
        return {
            "project": project_info,
            "autoloads": autoloads,
            "input_map": input_map
        }
    
    elif uri == "godot://editor/state":
        return await call_godot("editor.get_state")
    
    elif uri == "godot://scene/tree":
        return await call_godot("scene.get_tree")
    
    elif uri == "godot://logs/recent":
        return await call_godot("editor.get_logs", {"since": 0})
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


def invalidate_cache(uri: Optional[str] = None) -> None:
    """Invalidate cached resources.
    
    Args:
        uri: Specific URI to invalidate, or None to invalidate all
    """
    if uri:
        _cache.invalidate(uri)
    else:
        _cache.invalidate_all()
