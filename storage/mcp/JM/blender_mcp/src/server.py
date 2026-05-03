#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blender MCP 服务器

功能:
- 提供 Blender 控制接口
- 支持自然语言命令执行
- 与 GSTACK 架构集成

用法:
    python server.py [--port PORT] [--blender-path PATH]
"""

import json
import sys
import argparse
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import bpy
except ImportError:
    print("警告: bpy 模块未安装，请在 Blender 中运行此脚本")
    sys.exit(1)


class BlenderHTTPHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""
    server = None

    def do_POST(self):
        """处理 POST 请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            command = data.get('command', '')
            
            if not command:
                self.send_error(400, 'Missing command parameter')
                return
            
            result = self.server.execute_command(command)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Blender MCP Server is running')
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self.send_error(404, 'Not Found')


class BlenderMCPServer:
    """Blender MCP 服务器"""

    def __init__(self, port=8400):
        self.port = port
        self.running = False
        self.http_server = None
        self.server_thread = None

    def execute_command(self, command: str) -> dict:
        """执行 Blender 命令"""
        try:
            result = {"success": True, "data": None, "error": None}

            # 自然语言命令解析
            command_lower = command.lower()
            if "scene info" in command_lower or "场景信息" in command_lower:
                result["data"] = self._get_scene_info()
            elif "list objects" in command_lower or "列出对象" in command_lower:
                result["data"] = self._list_objects()
            elif "add cube" in command_lower or "创建立方体" in command_lower:
                result["data"] = self._add_cube()
            elif "add monkey" in command_lower or "创建猴子" in command_lower:
                result["data"] = self._add_monkey()
            elif ("delete" in command_lower and "object" in command_lower) or "删除" in command_lower:
                obj_name = self._extract_object_name(command)
                if obj_name:
                    result["data"] = self._delete_object(obj_name)
                else:
                    result["success"] = False
                    result["error"] = "请指定要删除的对象名称"
            elif "set material" in command_lower or "设置材质" in command_lower:
                material_name = self._extract_material_name(command)
                if material_name:
                    result["data"] = self._set_material(material_name)
                else:
                    result["success"] = False
                    result["error"] = "请指定材质名称"
            elif "render" in command_lower or "渲染" in command_lower:
                result["data"] = self._render_scene()
            elif "clear scene" in command_lower or "清空场景" in command_lower:
                result["data"] = self._clear_scene()
            else:
                # 传统命令格式
                if command == "scene.info":
                    result["data"] = self._get_scene_info()
                elif command == "objects.list":
                    result["data"] = self._list_objects()
                elif command.startswith("object."):
                    parts = command.split(".")
                    if len(parts) >= 3:
                        obj_name = parts[2] if len(parts) > 2 else None
                        action = parts[1]
                        result["data"] = self._handle_object_action(action, obj_name)
                else:
                    result["success"] = False
                    result["error"] = f"未知命令: {command}"

            return result

        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def _get_scene_info(self) -> dict:
        """获取场景信息"""
        return {
            "name": bpy.data.filepath or "未命名场景",
            "objects_count": len(bpy.data.objects),
            "materials_count": len(bpy.data.materials),
            "collections_count": len(bpy.data.collections)
        }

    def _list_objects(self) -> list:
        """列出所有对象"""
        return [
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "visible": obj.visible_get()
            }
            for obj in bpy.data.objects
        ]

    def _add_cube(self) -> dict:
        """添加立方体"""
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        return {"message": f"已添加立方体: {bpy.context.active_object.name}"}

    def _add_monkey(self) -> dict:
        """添加猴子头"""
        bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))
        return {"message": f"已添加猴子头: {bpy.context.active_object.name}"}

    def _delete_object(self, obj_name: str) -> dict:
        """删除对象"""
        obj = bpy.data.objects.get(obj_name)
        if obj:
            bpy.data.objects.remove(obj)
            return {"message": f"已删除对象: {obj_name}"}
        return {"error": f"对象不存在: {obj_name}"}

    def _set_material(self, material_name: str) -> dict:
        """设置材质"""
        # 创建材质
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # 设置基本颜色
        if material_name == "red":
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (1, 0, 0, 1)
        elif material_name == "blue":
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 0, 1, 1)
        elif material_name == "green":
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0, 1, 0, 1)
        else:
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
        
        # 应用到选中对象
        if bpy.context.active_object:
            obj = bpy.context.active_object
            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
            return {"message": f"已设置材质: {material_name}"}
        return {"error": "没有选中的对象"}

    def _render_scene(self) -> dict:
        """渲染场景"""
        output_path = str(Path(__file__).parent.parent / "render.png")
        bpy.context.scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        return {"message": f"渲染完成，保存到: {output_path}"}

    def _clear_scene(self) -> dict:
        """清空场景"""
        # 删除所有对象
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        return {"message": "场景已清空"}

    def _extract_object_name(self, command: str) -> str:
        """从命令中提取对象名称"""
        # 简单的名称提取逻辑
        parts = command.split()
        for i, part in enumerate(parts):
            if part in ["object", "对象"] and i + 1 < len(parts):
                return parts[i + 1]
        return ""

    def _extract_material_name(self, command: str) -> str:
        """从命令中提取材质名称"""
        # 简单的材质名称提取逻辑
        parts = command.split()
        for i, part in enumerate(parts):
            if part in ["material", "材质"] and i + 1 < len(parts):
                return parts[i + 1]
        return ""

    def _handle_object_action(self, action: str, obj_name: str = None) -> dict:
        """处理对象操作"""
        if action == "add" and obj_name:
            if obj_name == "cube":
                return self._add_cube()
            elif obj_name == "monkey":
                return self._add_monkey()
            else:
                return {"error": f"不支持的对象类型: {obj_name}"}
        elif action == "delete" and obj_name:
            return self._delete_object(obj_name)
        elif action == "list":
            return self._list_objects()
        return {"error": f"未知操作: {action}"}

    def start(self):
        """启动服务器"""
        if self.running:
            return {"success": False, "error": "服务器已启动"}
        
        try:
            BlenderHTTPHandler.server = self
            self.http_server = HTTPServer(('localhost', self.port), BlenderHTTPHandler)
            self.running = True
            
            # 在后台线程中运行服务器
            def run_server():
                while self.running:
                    try:
                        self.http_server.handle_request()
                    except:
                        if not self.running:
                            break
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            
            return {"success": True, "message": f"服务器已启动，端口: {self.port}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shutdown(self):
        """关闭服务器"""
        self.running = False
        return {"success": True, "message": "服务器已关闭"}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Blender MCP 服务器")
    parser.add_argument("--port", type=int, default=8400, help="服务端口")
    parser.add_argument("--blender-path", type=str, help="Blender 可执行文件路径")
    args = parser.parse_args()

    server = BlenderMCPServer(port=args.port)
    start_result = server.start()

    if start_result["success"]:
        print(start_result["message"])
        print("可用命令:")
        print("  - 自然语言: 创建立方体, 创建猴子, 列出对象, 渲染场景, 清空场景")
        print("  - 传统格式: scene.info, objects.list, object.add.cube, object.delete <name>")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("服务器正在关闭...")
            server.shutdown()
    else:
        print(f"启动失败: {start_result['error']}")


if __name__ == "__main__":
    import time
    main()