#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Access MCP Filesystem Server (Python版)
完全绕过 npm @modelcontextprotocol/server-filesystem 的路径限制问题。
支持所有盘符和目录的读写操作。

用法（作为MCP Server运行）：
    python filesystem_server.py

配置到 TRAE mcp.json：
    {
      "command": "python",
      "args": ["/python/MCP/filesystem_server.py"],
      "env": {}
    }
"""

import json
import sys
import os
import shutil
import stat
import time
import base64
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# ─── 配置：允许访问的盘符根目录 ──────────────────────────
ALLOWED_ROOTS = [
    Path("C:\\"),
    Path("D:\\"),
    Path("E:\\"),
    Path("F:\\"),
    Path("G:\\"),
    Path("H:\\"),
]

# 自动检测所有存在的盘符（兜底）
def _detect_all_drives():
    extra = []
    import string
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive) and not any(Path(drive) == r for r in ALLOWED_ROOTS):
            extra.append(Path(drive))
    return extra

AUTO_DETECTED_DRIVES = _detect_all_drives()

# 排除的系统目录（防止误操作）
BLOCKED_PATHS = [
    Path("C:\\Windows\\System32\\config"),  # 注册表 hive
    Path("C:\\$RECYCLE.BIN"),
    Path("C:\\System Volume Information"),
    Path("C:\\Pagefile.sys"),
]


def is_path_allowed(path_str: str) -> bool:
    """检查路径是否在允许范围内"""
    try:
        p = Path(path_str).resolve()
        # 检查是否在允许的根目录下（手动配置 + 自动检测）
        all_roots = ALLOWED_ROOTS + AUTO_DETECTED_DRIVES
        for root in all_roots:
            try:
                if p.is_relative_to(root.resolve()):
                    # 检查是否在黑名单中
                    for blocked in BLOCKED_PATHS:
                        if p.is_relative_to(blocked.resolve()):
                            return False
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def file_info_dict(p: Path) -> Dict[str, Any]:
    try:
        st = p.stat()
        return {
            "name": p.name,
            "path": str(p),
            "type": "directory" if p.is_dir() else "file",
            "size": st.st_size,
            "size_formatted": format_size(st.st_size),
            "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
            "readable": os.access(p, os.R_OK),
            "writable": os.access(p, os.W_OK),
        }
    except Exception as e:
        return {"name": p.name, "path": str(p), "error": str(e)}


# ════════════════════════════════════════
# MCP 协议处理（stdio 模式）
# ════════════════════════════════════════


def handle_list_directory(params: Dict) -> Dict:
    target = params.get("target_directory", ".")
    ignore_globs = params.get("ignore_globs", [])

    if not is_path_allowed(target):
        return {"error": f"Access denied: {target}", "content": []}

    p = Path(target)
    if not p.exists():
        return {"error": f"Not found: {target}", "content": []}
    if not p.is_dir():
        return {"error": f"Not a directory: {target}", "content": []}

    result = []
    try:
        entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        for entry in entries:
            info = {
                "name": entry.name,
                "path": str(entry),
                "type": "directory" if entry.is_dir() else "file",
            }
            if entry.is_file():
                try:
                    info["size"] = entry.stat().st_size
                    info["size_formatted"] = format_size(info["size"])
                except Exception:
                    pass
            result.append(info)
        return {"content": result, "path": str(p)}
    except PermissionError as e:
        return {"error": f"Permission denied: {e}", "content": [], "path": str(p)}
    except Exception as e:
        return {"error": str(e), "content": [], "path": str(p)}


def handle_read_file(params: Dict) -> Dict:
    path = params.get("filePath", "")

    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    p = Path(path)
    if not p.exists():
        return {"error": f"Not found: {path}"}
    if not p.is_file():
        return {"error": f"Not a file: {path}"}

    limit = params.get("limit")
    offset = params.get("offset")

    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        if offset or limit:
            start = offset or 0
            end = (start + limit) if limit else len(lines)
            lines = lines[start:end]
            content = "\n".join(lines)

        return {"content": content, "path": str(p)}
    except Exception as e:
        return {"error": str(e)}


def handle_write_file(params: Dict) -> Dict:
    path = params.get("filePath", "")
    content = params.get("content", "")

    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(p), "message": f"Written {len(content)} bytes"}
    except Exception as e:
        return {"error": str(e)}


def handle_search_files(params: Dict) -> Dict:
    pattern = params.get("pattern", "*")
    target = params.get("target_directory", "D:\\")
    recursive = params.get("recursive", True)

    if not is_path_allowed(target):
        return {"error": f"Access denied: {target}", "files": []}

    import glob as globmod
    results = []
    try:
        p = Path(target)
        search_pattern = str(p / ("**/" + pattern if recursive else pattern))
        matches = globmod.glob(search_pattern, recursive=recursive)

        for match in sorted(matches)[:200]:  # 最多返回200个结果
            mp = Path(match)
            if is_path_allowed(match):
                results.append({
                    "path": match,
                    "type": "directory" if mp.is_dir() else "file",
                    "name": mp.name,
                })
        return {"files": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e), "files": []}


def handle_create_directory(params: Dict) -> Dict:
    path = params.get("target_directory", "")
    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    try:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": str(p)}
    except Exception as e:
        return {"error": str(e)}


def handle_move_file(params: Dict) -> Dict:
    src = params.get("source", "")
    dst = params.get("destination", "")
    if not is_path_allowed(src) or not is_path_allowed(dst):
        return {"error": "Access denied"}

    try:
        shutil.move(str(src), str(dst))
        return {"success": True, "source": src, "destination": dst}
    except Exception as e:
        return {"error": str(e)}


def handle_delete_file(params: Dict) -> Dict:
    path = params.get("target_file", "")
    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    try:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return {"success": True, "deleted": path}
    except Exception as e:
        return {"error": str(e)}


def handle_get_file_info(params: Dict) -> Dict:
    path = params.get("filePath", "")
    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    p = Path(path)
    if not p.exists():
        return {"error": f"Not found: {path}"}

    return file_info_dict(p)


def handle_list_allowed_directories(params: Dict) -> Dict:
    roots = []
    for r in ALLOWED_ROOTS:
        exists = r.exists()
        info = {"path": str(r), "exists": exists}
        if exists:
            try:
                info["label"] = f"{r.drive} Drive"
            except Exception:
                pass
        roots.append(info)
    return {"allowed_directories": roots, "note": "All subdirectories are accessible within these roots"}


def handle_directory_tree(params: Dict) -> Dict:
    path = params.get("target_directory", "D:\\")
    max_depth = params.get("max_depth", 3)

    if not is_path_allowed(path):
        return {"error": f"Access denied: {path}"}

    def build_tree(p: Path, depth: int) -> Dict:
        node = {"name": p.name, "path": str(p), "type": "dir" if p.is_dir() else "file"}
        if p.is_dir() and depth < max_depth:
            try:
                children = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                node["children"] = [build_tree(c, depth + 1) for c in children[:50]]
            except Exception:
                node["children"] = []
        elif p.is_dir():
            node["children"] = []
        return node

    try:
        root = Path(path)
        return build_tree(root, 0)
    except Exception as e:
        return {"error": str(e)}


# 工具路由表
TOOLS = {
    "list_directory": handle_list_directory,
    "list_dir": handle_list_directory,
    "read_file": handle_read_file,
    "read_text_file": handle_read_file,
    "write_file": handle_write_file,
    "create_directory": handle_create_directory,
    "mkdir": handle_create_directory,
    "search_files": handle_search_files,
    "search_file": handle_search_files,
    "move_file": handle_move_file,
    "delete_file": handle_delete_file,
    "get_file_info": handle_get_file_info,
    "list_allowed_directories": handle_list_allowed_directories,
    "directory_tree": handle_directory_tree,
}


def send_response(result: Any, req_id=None):
    resp = {"result": result}
    if req_id:
        resp["id"] = req_id
    json.dump(resp, sys.stdout)
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_stdio():
    """MCP stdio 主循环"""
    all_roots = [str(r) for r in (ALLOWED_ROOTS + AUTO_DETECTED_DRIVES)]
    # 发送初始化完成消息
    send_response({
        "server_name": "full-access-filesystem",
        "version": "2.0.0",
        "description": "Python Full Access Filesystem - ALL DETECTED DRIVES",
        "allowed_roots": all_roots,
        "manual_roots": [str(r) for r in ALLOWED_ROOTS],
        "auto_detected_drives": [str(r) for r in AUTO_DETECTED_DRIVES],
    })

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method", "")
            params = req.get("params", {})
            req_id = req.get("id")

            if method == "tools/list":
                send_response({
                    "tools": [
                        {"name": "list_directory", "description": "List files in directory"},
                        {"name": "read_file", "description": "Read file contents"},
                        {"name": "write_file", "description": "Write/create file"},
                        {"name": "search_files", "description": "Search files by pattern"},
                        {"name": "create_directory", "description": "Create directory"},
                        {"name": "delete_file", "description": "Delete file or directory"},
                        {"name": "move_file", "description": "Move/rename file"},
                        {"name": "get_file_info", "description": "Get file metadata"},
                        {"name": "list_allowed_directories", "description": "Show allowed directories"},
                        {"name": "directory_tree", "description": "Get tree view of directory"},
                    ]
                }, req_id)

            elif method == "tools/call":
                tool_name = params.get("name", "")
                args = params.get("arguments", {})
                handler = TOOLS.get(tool_name)
                if handler:
                    send_response(handler(args), req_id)
                else:
                    send_response({"error": f"Unknown tool: {tool_name}"}, req_id)
            else:
                send_response({"error": f"Unknown method: {method}"}, req_id)

        except json.JSONDecodeError:
            send_response({"error": "Invalid JSON"})
        except Exception as e:
            send_response({"error": str(e)})


if __name__ == "__main__":
    if "--test" in sys.argv:
        # 独立测试模式
        print("=== Full Access Filesystem Server Test ===")
        print(f"\nAllowed roots: {[str(r) for r in ALLOWED_ROOTS]}")
        for r in ALLOWED_ROOTS:
            exists = r.exists()
            print(f"  {r} -> {'OK' if exists else 'MISSING'}")

        print("\n--- list_directory D:\\ ---")
        result = handle_list_directory({"target_directory": "D:\\"})
        items = result.get("content", [])[:10]
        for item in items:
            t = "[DIR]" if item["type"] == "directory" else "[FILE]"
            print(f"  {t} {item['name']}")

        print("\n--- list_allowed_directories ---")
        result2 = handle_list_allowed_directories({})
        print(json.dumps(result2, indent=2))
    else:
        run_stdio()
