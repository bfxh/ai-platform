#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Godot MCP Server v2.1
直接通过命令行控制 Godot 4.x（不需要 Godot 内部 WebSocket）

工作模式：
    1. Godot --headless --script <script.gd> → 执行 GDScript
    2. 通过 --path 指定项目目录

用法：
    python godot_mcp_server.py list_nodes --project /python/godot_project
    python godot_mcp_server.py create_scene --project /python/godot_project --name MyScene
    python godot_mcp_server.py export --project /python/godot_project --output game.pck
    python godot_mcp_server.py mcp  # 启动 MCP Server 模式
"""

import os
import sys
import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── 配置 ────────────────────────────────────────────────
GODOT_EXE = Path("%SOFTWARE_DIR%/KF/JM/Godot_v4.6.1-stable_win64.exe")


def _build_gdscript(user_code: str) -> str:
    """
    构建 GDScript。
    GDScript 不允许在函数体内嵌套 func 定义。
    user_code 只能包含语句/表达式，不能定义新 func。

    缩进策略：保留原始嵌套结构，以首行基准缩进为参照，
    计算每行的相对缩进并叠加 8 空格基础偏移。
    """
    lines = user_code.strip().split("\n")

    # 找第一非空行的缩进量作为基准
    base_indent = 0
    for l in lines:
        stripped = l.strip()
        if stripped:
            base_indent = len(l) - len(stripped)
            break

    # 重构每行：保留相对缩进，以 _init() body 级别（4 空格）为基准
    result_lines = []
    for l in lines:
        if not l.strip():
            continue  # 跳过纯空行
        stripped = l.strip()
        orig_indent = len(l) - len(stripped)
        rel_indent = orig_indent - base_indent
        new_indent = 4 + rel_indent
        result_lines.append(" " * new_indent + stripped)

    body_stmts = "\n".join(result_lines) + "\n"

    class_level = (
        "extends SceneTree\n"
        "\n"
        "var _result = null\n"
        "\n"
    )

    init_body = (
        "func _init():\n"
        "    _result = null\n"
        + body_stmts + "\n"
        "    var output = {\n"
        '        "success": true,\n'
        '        "result": _result,\n'
        '        "error": null,\n'
        '        "scene": get_root().get_child_count(),\n'
        '        "tree_loaded": true\n'
        "    }\n"
        "    print(JSON.stringify(output))\n"
        "    quit()\n"
    )

    return class_level + init_body


class GodotCLI:
    """Godot 4.x 命令行控制"""

    def __init__(self, godot_exe: Path = None, project_path: str = None):
        self.godot = godot_exe or GODOT_EXE
        self.project = project_path

    def _run(self, script_code: str, project: str = None, timeout: int = 30) -> Dict:
        """在 Godot 中执行 GDScript，返回 JSON 输出"""
        project = project or self.project
        if not project:
            return {"error": "未指定 Godot 项目目录 (--project)"}
        if not Path(project).exists():
            return {"error": f"项目目录不存在: {project}"}

        gd_script = _build_gdscript(script_code)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".gd", encoding="utf-8", delete=False
        ) as f:
            f.write(gd_script)
            script_path = f.name

        try:
            cmd = [str(self.godot), "--headless", "--path", project,
                   "--script", script_path]
            result = subprocess.run(
                cmd, capture_output=True, timeout=timeout,
                encoding="utf-8", errors="replace"
            )
            # 优先从 stdout 末尾找 JSON 输出
            for line in reversed((result.stdout or "").split("\n")):
                line = line.strip()
                if line.startswith("{") and '"success"' in line:
                    try:
                        parsed = json.loads(line)
                        # 检查 stderr 是否有 SCRIPT ERROR
                        stderr_txt = (result.stderr or "")
                        if "SCRIPT ERROR" in stderr_txt:
                            # 从 stderr 提取错误信息
                            for err_line in stderr_txt.split("\n"):
                                if "SCRIPT ERROR" in err_line:
                                    parsed["success"] = False
                                    parsed["error"] = err_line.strip()[:200]
                                    break
                            return parsed
                        return parsed
                    except Exception:
                        pass
            # 没有找到 JSON，检查 stderr
            stderr_txt = (result.stderr or "")
            if "SCRIPT ERROR" in stderr_txt:
                err_msg = ""
                for line in stderr_txt.split("\n"):
                    line = line.strip()
                    if "SCRIPT ERROR" in line:
                        err_msg = line.strip()[:200]
                        break
                return {"success": False, "error": err_msg,
                        "returncode": result.returncode}
            return {
                "stdout": (result.stdout or "")[:500],
                "stderr": (result.stderr or "")[:500],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Godot 执行超时 ({timeout}s)"}
        except FileNotFoundError:
            return {"error": f"Godot 未找到: {self.godot}"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            try:
                os.unlink(script_path)
            except Exception:
                pass

    # ── 预置命令 ────────────────────────────────────────

    def list_nodes(self, project: str = None) -> Dict:
        """列出当前已加载场景的节点树"""
        return self._run(
            'var root = get_root()\n'
            '_result = []\n'
            'var stack = [root]\n'
            'var i = 0\n'
            'while i < stack.size():\n'
            '    var node = stack[i]\n'
            '    i += 1\n'
            '    var node_path = str(node.name)\n'
            '    var parent_node = node.get_parent()\n'
            '    if parent_node and parent_node != root:\n'
            '        node_path = str(parent_node.name) + "/" + str(node.name)\n'
            '    _result.append({"path": node_path, "type": node.get_class(), "name": node.name, "children": node.get_child_count()})\n'
            '    var j = 0\n'
            '    while j < node.get_child_count():\n'
            '        stack.append(node.get_child(j))\n'
            '        j += 1',
            project, timeout=60
        )

    def get_scene_info(self, scene_path: str, project: str = None) -> Dict:
        """获取场景信息"""
        return self._run(
            'var scene_res = load("' + scene_path + '")\n'
            'var scene = scene_res.instantiate()\n'
            '_result = {"path": "' + scene_path + '", '
            '"root_type": scene.get_class(), '
            '"name": scene.name, '
            '"child_count": scene.get_child_count()}\n'
            'scene.free()',
            project
        )

    def create_scene(self, name: str, project: str = None) -> Dict:
        """创建新场景"""
        return self._run(
            'var scene = Node.new()\n'
            'scene.name = "' + name + '"\n'
            'var packed = PackedScene.new()\n'
            'packed.pack(scene)\n'
            'var path = "res://' + name + '.tscn"\n'
            'var err = ResourceSaver.save(packed, path)\n'
            '_result = {"path": path, "success": err == 0}\n'
            'scene.free()',
            project
        )

    def export_project(self, output: str, project: str = None) -> Dict:
        """导出项目"""
        project = project or self.project
        cmd = [str(self.godot), "--headless", "--path", project,
               "--export-release", output]
        try:
            result = subprocess.run(
                cmd, capture_output=True, timeout=300,
                encoding="utf-8", errors="replace"
            )
            return {
                "success": result.returncode == 0,
                "output": output,
                "stderr": (result.stderr or "")[:500],
            }
        except Exception as e:
            return {"error": str(e)}


# ─── MCP Server ──────────────────────────────────────────────────────────────

async def godot_mcp_main():
    """Godot MCP Server 异步主函数"""
    try:
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool
    except ImportError:
        print("错误: 需要安装 mcp 库: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = Server("godot-mcp")
    godot = GodotCLI()

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(name="godot_list_nodes", description="列出 Godot 项目场景中所有节点",
                 inputSchema={"type": "object", "properties": {
                     "project": {"type": "string", "description": "Godot 项目目录"}}},
                 required=["project"]),
            Tool(name="godot_scene_info", description="获取 Godot 场景文件信息",
                 inputSchema={"type": "object", "properties": {
                     "scene_path": {"type": "string", "description": "场景路径 (res://...)"},
                     "project": {"type": "string", "description": "Godot 项目目录"}}},
                 required=["scene_path"]),
            Tool(name="godot_create_scene", description="创建新的 Godot 场景",
                 inputSchema={"type": "object", "properties": {
                     "name": {"type": "string", "description": "场景名称"},
                     "project": {"type": "string", "description": "Godot 项目目录"}}},
                 required=["name"]),
            Tool(name="godot_export", description="导出 Godot 项目",
                 inputSchema={"type": "object", "properties": {
                     "output": {"type": "string", "description": "导出输出路径"},
                     "project": {"type": "string", "description": "Godot 项目目录"}}},
                 required=["output"]),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[TextContent]:
        try:
            if name == "godot_list_nodes":
                result = godot.list_nodes(arguments.get("project"))
            elif name == "godot_scene_info":
                result = godot.get_scene_info(
                    arguments["scene_path"], arguments.get("project"))
            elif name == "godot_create_scene":
                result = godot.create_scene(
                    arguments["name"], arguments.get("project"))
            elif name == "godot_export":
                result = godot.export_project(
                    arguments["output"], arguments.get("project"))
            else:
                result = {"error": f"未知命令: {name}"}
            return [TextContent(type="text",
                                text=json.dumps(result, ensure_ascii=False, indent=2))]
        except Exception as e:
            return [TextContent(type="text",
                                text=json.dumps({"error": str(e)}))]

    async with stdio_server() as (read, write):
        await server.run(
            read, write,
            InitializationOptions(
                server_name="godot-mcp",
                server_version="2.1.0",
                instructions="Godot 4.x MCP Server"
            )
        )


# ─── CLI 主入口 ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("""Godot MCP CLI v2.1

用法:
    python godot_mcp_server.py list_nodes --project <path>
    python godot_mcp_server.py scene_info <scene.tscn> --project <path>
    python godot_mcp_server.py create_scene <name> --project <path>
    python godot_mcp_server.py export <output.pck> --project <path>
    python godot_mcp_server.py mcp
        """)
        return

    godot = GodotCLI()
    args = sys.argv[2:]
    project = None
    for i, a in enumerate(args):
        if a == "--project" and i + 1 < len(args):
            project = args[i + 1]

    cmd = sys.argv[1]
    if cmd == "mcp":
        asyncio.run(godot_mcp_main())
    elif cmd == "list_nodes":
        result = godot.list_nodes(project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "scene_info":
        scene = args[0] if args and not args[0].startswith("--") else "res://Main.tscn"
        result = godot.get_scene_info(scene, project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "create_scene":
        name = args[0] if args and not args[0].startswith("--") else "NewScene"
        result = godot.create_scene(name, project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "export":
        output = args[0] if args and not args[0].startswith("--") else "export.pck"
        result = godot.export_project(output, project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
