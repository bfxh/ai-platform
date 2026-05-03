#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender MCP Server - MCP服务器

功能：
- 作为MCP Server运行
- 连接Claude AI和Blender Addon
- 提供Blender操作工具

用法：
    python blender_mcp_server.py

环境变量：
    BLENDER_HOST - Blender MCP服务器地址 (默认: localhost)
    BLENDER_PORT - Blender MCP服务器端口 (默认: 8080)
"""

import os
import sys
import json
import socket
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

# FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp")
    raise

# ============================================================
# 配置
# ============================================================
BLENDER_HOST = os.getenv("BLENDER_HOST", "localhost")
BLENDER_PORT = int(os.getenv("BLENDER_PORT", "8080"))

# ============================================================
# Blender MCP客户端
# ============================================================
class BlenderMCPClient:
    """Blender MCP客户端"""
    
    def __init__(self, host: str = BLENDER_HOST, port: int = BLENDER_PORT):
        self.host = host
        self.port = port
        self.socket = None
    
    async def connect(self) -> bool:
        """连接到Blender"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Failed to connect to Blender: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    async def send_command(self, action: str, params: Dict = None) -> Dict:
        """发送命令到Blender"""
        if not self.socket:
            return {"success": False, "error": "Not connected to Blender"}
        
        try:
            # 构建命令
            command = {
                "action": action,
                "params": params or {}
            }
            
            # 发送
            data = json.dumps(command).encode('utf-8')
            self.socket.send(data)
            
            # 接收响应
            response = self.socket.recv(4096)
            result = json.loads(response.decode('utf-8'))
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================================
# FastMCP Server
# ============================================================
mcp = FastMCP("blender-mcp")
client = BlenderMCPClient()

# ============================================================
# MCP Tools
# ============================================================
@mcp.tool()
async def blender_create_object(
    type: str = "cube",
    name: str = "Object",
    location: List[float] = None
) -> Dict[str, Any]:
    """
    在Blender中创建对象
    
    Args:
        type: 对象类型 (cube/sphere/cylinder/plane/torus/monkey)
        name: 对象名称
        location: 位置 [x, y, z]
    
    Returns:
        创建结果
    """
    if location is None:
        location = [0, 0, 0]
    
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("create_object", {
            "type": type,
            "name": name,
            "location": location
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_delete_object(name: str) -> Dict[str, Any]:
    """
    删除Blender中的对象
    
    Args:
        name: 对象名称
    
    Returns:
        删除结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("delete_object", {"name": name})
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_modify_object(
    name: str,
    location: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None
) -> Dict[str, Any]:
    """
    修改Blender对象
    
    Args:
        name: 对象名称
        location: 位置 [x, y, z]
        rotation: 旋转 [x, y, z] (弧度)
        scale: 缩放 [x, y, z]
    
    Returns:
        修改结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    params = {"name": name}
    if location:
        params["location"] = location
    if rotation:
        params["rotation"] = rotation
    if scale:
        params["scale"] = scale
    
    try:
        result = await client.send_command("modify_object", params)
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_add_modifier(
    object: str,
    type: str,
    levels: int = 2,
    width: float = 0.02,
    count: int = 2
) -> Dict[str, Any]:
    """
    添加修改器
    
    Args:
        object: 对象名称
        type: 修改器类型 (SUBSURF/BEVEL/ARRAY/MIRROR)
        levels: 细分级别 (SUBSURF)
        width: 倒角宽度 (BEVEL)
        count: 阵列数量 (ARRAY)
    
    Returns:
        添加结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("add_modifier", {
            "object": object,
            "type": type,
            "levels": levels,
            "width": width,
            "count": count
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_create_material(
    name: str = "Material",
    base_color: List[float] = None,
    metallic: float = 0.0,
    roughness: float = 0.5
) -> Dict[str, Any]:
    """
    创建材质
    
    Args:
        name: 材质名称
        base_color: 基础颜色 [r, g, b, a]
        metallic: 金属度 (0-1)
        roughness: 粗糙度 (0-1)
    
    Returns:
        创建结果
    """
    if base_color is None:
        base_color = [0.8, 0.8, 0.8, 1.0]
    
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("create_material", {
            "name": name,
            "base_color": base_color,
            "metallic": metallic,
            "roughness": roughness
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_apply_material(
    object: str,
    material: str
) -> Dict[str, Any]:
    """
    应用材质到对象
    
    Args:
        object: 对象名称
        material: 材质名称
    
    Returns:
        应用结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("apply_material", {
            "object": object,
            "material": material
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_set_camera(
    location: List[float] = None,
    rotation: List[float] = None
) -> Dict[str, Any]:
    """
    设置相机
    
    Args:
        location: 位置 [x, y, z]
        rotation: 旋转 [x, y, z] (弧度)
    
    Returns:
        设置结果
    """
    if location is None:
        location = [7, -7, 5]
    if rotation is None:
        rotation = [1.1, 0, 0.8]
    
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("set_camera", {
            "location": location,
            "rotation": rotation
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_set_light(
    type: str = "SUN",
    location: List[float] = None,
    energy: float = 3.0
) -> Dict[str, Any]:
    """
    设置灯光
    
    Args:
        type: 灯光类型 (SUN/POINT/AREA)
        location: 位置 [x, y, z]
        energy: 能量/强度
    
    Returns:
        设置结果
    """
    if location is None:
        location = [5, 5, 10]
    
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("set_light", {
            "type": type,
            "location": location,
            "energy": energy
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_render(
    output_path: str = None,
    resolution: List[int] = None,
    samples: int = 128
) -> Dict[str, Any]:
    """
    渲染场景
    
    Args:
        output_path: 输出路径
        resolution: 分辨率 [width, height]
        samples: 采样数
    
    Returns:
        渲染结果
    """
    if resolution is None:
        resolution = [1920, 1080]
    
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("render", {
            "output_path": output_path,
            "resolution": resolution,
            "samples": samples
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_export(
    filepath: str,
    format: str = "fbx"
) -> Dict[str, Any]:
    """
    导出场景
    
    Args:
        filepath: 输出文件路径
        format: 格式 (fbx/obj/gltf)
    
    Returns:
        导出结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("export", {
            "filepath": filepath,
            "format": format
        })
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_import_file(filepath: str) -> Dict[str, Any]:
    """
    导入文件
    
    Args:
        filepath: 文件路径
    
    Returns:
        导入结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("import_file", {"filepath": filepath})
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_get_scene_info() -> Dict[str, Any]:
    """
    获取场景信息
    
    Returns:
        场景信息，包括所有对象
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("get_scene_info")
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_clear_scene() -> Dict[str, Any]:
    """
    清理场景
    
    Returns:
        清理结果
    """
    if not await client.connect():
        return {"success": False, "error": "Cannot connect to Blender"}
    
    try:
        result = await client.send_command("clear_scene")
        return result
    finally:
        client.disconnect()

@mcp.tool()
async def blender_check_connection() -> Dict[str, Any]:
    """
    检查Blender连接
    
    Returns:
        连接状态
    """
    connected = await client.connect()
    if connected:
        client.disconnect()
        return {
            "success": True,
            "connected": True,
            "host": BLENDER_HOST,
            "port": BLENDER_PORT
        }
    else:
        return {
            "success": False,
            "connected": False,
            "error": f"Cannot connect to Blender at {BLENDER_HOST}:{BLENDER_PORT}",
            "hint": "Make sure Blender is running with BlenderMCP addon enabled and server started"
        }

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print(f"Starting Blender MCP Server...")
    print(f"Target: {BLENDER_HOST}:{BLENDER_PORT}")
    print("Make sure Blender is running with BlenderMCP addon enabled")
    mcp.run()
