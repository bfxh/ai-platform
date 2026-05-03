"""WebSocket RPC client for communicating with the Godot plugin."""

import asyncio
import json
import logging
import uuid
from typing import Any, Optional
from dataclasses import dataclass, field

import websockets
from websockets.client import WebSocketClientProtocol

from .security import get_token, get_ws_url


logger = logging.getLogger(__name__)


class RPCError(Exception):
    """RPC call error."""
    
    def __init__(self, code: int, message: str, data: Optional[dict] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"RPC Error {code}: {message}")


@dataclass
class RPCClient:
    """WebSocket RPC client for Godot plugin communication."""
    
    ws_url: str = field(default_factory=get_ws_url)
    token: Optional[str] = field(default_factory=get_token)
    client_name: str = "godot-mcp-bridge"
    client_version: str = "1.0.0"
    
    _ws: Optional[WebSocketClientProtocol] = field(default=None, init=False, repr=False)
    _pending_requests: dict = field(default_factory=dict, init=False, repr=False)
    _request_id: int = field(default=0, init=False, repr=False)
    _authenticated: bool = field(default=False, init=False, repr=False)
    _receive_task: Optional[asyncio.Task] = field(default=None, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    
    # Reconnection settings
    _max_retries: int = field(default=5, init=False)
    _retry_delay: float = field(default=1.0, init=False)
    _max_retry_delay: float = field(default=30.0, init=False)
    
    async def connect(self) -> bool:
        """Connect to the Godot plugin WebSocket server."""
        if self._ws is not None and self._ws.open:
            return True
        
        retry_count = 0
        delay = self._retry_delay
        
        while retry_count < self._max_retries:
            try:
                logger.info(f"Connecting to Godot at {self.ws_url}...")
                self._ws = await websockets.connect(
                    self.ws_url,
                    max_size=1048576,  # 1MB
                    ping_interval=30,
                    ping_timeout=10
                )
                
                # Start receive task
                self._receive_task = asyncio.create_task(self._receive_loop())
                
                # Authenticate
                await self._authenticate()
                
                logger.info("Connected and authenticated with Godot")
                return True
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"Connection attempt {retry_count} failed: {e}")
                
                if retry_count < self._max_retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, self._max_retry_delay)
        
        logger.error("Failed to connect to Godot after max retries")
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from the Godot plugin."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        self._authenticated = False
        self._pending_requests.clear()
        logger.info("Disconnected from Godot")
    
    async def _authenticate(self) -> None:
        """Authenticate with the Godot plugin."""
        if not self.token:
            raise RPCError(4010, "No authentication token available")
        
        result = await self.call("auth.hello", {
            "token": self.token,
            "client": self.client_name,
            "version": self.client_version
        })
        
        if result.get("ok"):
            self._authenticated = True
            logger.info(f"Authenticated with Godot {result.get('editor_version', 'unknown')}")
        else:
            raise RPCError(4010, "Authentication failed")
    
    async def _receive_loop(self) -> None:
        """Background task to receive messages from the WebSocket."""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message[:100]}")
        except websockets.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self._authenticated = False
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
    
    async def _handle_message(self, data: dict) -> None:
        """Handle a received message."""
        # Check if it's a response to a pending request
        request_id = data.get("id")
        if request_id is not None and request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if not future.done():
                if "error" in data:
                    error = data["error"]
                    future.set_exception(RPCError(
                        error.get("code", -32000),
                        error.get("message", "Unknown error"),
                        error.get("data")
                    ))
                else:
                    future.set_result(data.get("result"))
        
        # Check if it's an event
        elif data.get("method", "").startswith("event."):
            event_name = data["method"][6:]  # Remove "event." prefix
            params = data.get("params", {})
            logger.debug(f"Received event: {event_name} - {params}")
    
    async def call(self, method: str, params: Optional[dict] = None, timeout: float = 30.0) -> Any:
        """Call an RPC method on the Godot plugin.
        
        Args:
            method: The RPC method name (e.g., "scene.list_nodes")
            params: Optional parameters dictionary
            timeout: Request timeout in seconds
            
        Returns:
            The result from the RPC call
            
        Raises:
            RPCError: If the call fails
        """
        async with self._lock:
            # Ensure connected (skip for auth.hello)
            if method != "auth.hello":
                if not self._ws or not self._ws.open:
                    connected = await self.connect()
                    if not connected:
                        raise RPCError(-32000, "Not connected to Godot")
            
            # Generate request ID
            self._request_id += 1
            request_id = str(self._request_id)
            
            # Build request
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {}
            }
            
            # Create future for response
            future = asyncio.get_event_loop().create_future()
            self._pending_requests[request_id] = future
            
            try:
                # Send request
                await self._ws.send(json.dumps(request))
                logger.debug(f"Sent RPC request: {method}")
                
                # Wait for response
                result = await asyncio.wait_for(future, timeout=timeout)
                return result
                
            except asyncio.TimeoutError:
                self._pending_requests.pop(request_id, None)
                raise RPCError(-32000, f"Request timed out: {method}")
            except Exception as e:
                self._pending_requests.pop(request_id, None)
                if isinstance(e, RPCError):
                    raise
                raise RPCError(-32000, str(e))
    
    async def ensure_connected(self) -> bool:
        """Ensure we're connected to Godot."""
        if self._ws and self._ws.open and self._authenticated:
            return True
        return await self.connect()
    
    @property
    def is_connected(self) -> bool:
        """Check if we're connected and authenticated."""
        return self._ws is not None and self._ws.open and self._authenticated


# Global client instance
_client: Optional[RPCClient] = None


def get_client() -> RPCClient:
    """Get the global RPC client instance."""
    global _client
    if _client is None:
        _client = RPCClient()
    return _client


async def call_godot(method: str, params: Optional[dict] = None) -> Any:
    """Convenience function to call a Godot RPC method.
    
    Args:
        method: The RPC method name
        params: Optional parameters
        
    Returns:
        The result from the RPC call
    """
    client = get_client()
    await client.ensure_connected()
    return await client.call(method, params)
