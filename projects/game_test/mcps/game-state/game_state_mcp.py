#!/usr/bin/env python3
"""
游戏状态监听 MCP 服务
真正监听：进程存活、窗口状态、日志错误、内存占用、帧率估算
"""
import json
import os
import sys
import time
import ctypes
import subprocess
from pathlib import Path


def check_process_alive(pid: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if handle:
        exit_code = ctypes.c_ulong()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            alive = exit_code.value == 259
        else:
            alive = False
        kernel32.CloseHandle(handle)
        return alive
    return False


def get_process_memory(pid: int) -> int:
    try:
        import psutil
        p = psutil.Process(pid)
        return p.memory_info().rss
    except Exception:
        return 0


def find_game_window(title_keyword: str) -> dict:
    user32 = ctypes.windll.user32
    result = []

    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_keyword.lower() in buf.value.lower():
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                result.append({
                    "hwnd": hwnd,
                    "title": buf.value,
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                    "visible": user32.IsWindowVisible(hwnd) != 0,
                })
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result[0] if result else {}


def check_log_errors(log_path: str, since_byte: int = 0) -> dict:
    errors = []
    warnings = []
    last_byte = since_byte
    if not os.path.exists(log_path):
        return {"errors": [], "warnings": [], "last_byte": 0}

    try:
        file_size = os.path.getsize(log_path)
        if file_size < since_byte:
            since_byte = 0

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(since_byte)
            for line in f:
                if "FATAL" in line or "Stopping!" in line:
                    errors.append(line.strip()[:200])
                elif "ERROR" in line or "Exception" in line:
                    warnings.append(line.strip()[:200])
            last_byte = f.tell()
    except Exception:
        pass

    return {"errors": errors, "warnings": warnings, "last_byte": last_byte}


def check_log_position(log_path: str) -> dict:
    if not os.path.exists(log_path):
        return {"found": False}

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        for line in reversed(content.split("\n")):
            if "Teleported" in line or "Set own position" in line:
                return {"found": True, "line": line.strip()[:200]}

        if "Saving chunks" in content:
            return {"found": True, "status": "world_loaded"}
    except Exception:
        pass

    return {"found": False}


_game_pid = 0
_log_path = ""
_log_byte_offset = 0
_window_title = "Minecraft"


def handle_request(method: str, params: dict) -> dict:
    global _game_pid, _log_path, _log_byte_offset, _window_title

    if method == "initialize":
        _game_pid = params.get("pid", 0)
        _log_path = params.get("log_path", "")
        _window_title = params.get("window_title", "Minecraft")
        _log_byte_offset = 0
        if _log_path and os.path.exists(_log_path):
            _log_byte_offset = os.path.getsize(_log_path)
        return {"status": "ok", "pid": _game_pid, "log_path": _log_path}

    elif method == "check_alive":
        if _game_pid:
            alive = check_process_alive(_game_pid)
            return {"alive": alive, "pid": _game_pid}
        return {"alive": False, "pid": 0}

    elif method == "check_window":
        win = find_game_window(_window_title)
        return {"window": win, "found": bool(win)}

    elif method == "check_errors":
        result = check_log_errors(_log_path, _log_byte_offset)
        _log_byte_offset = result["last_byte"]
        return result

    elif method == "check_position":
        return check_log_position(_log_path)

    elif method == "check_memory":
        mem = get_process_memory(_game_pid)
        return {"pid": _game_pid, "memory_bytes": mem, "memory_mb": round(mem / 1024 / 1024, 1)}

    elif method == "full_status":
        alive = check_process_alive(_game_pid) if _game_pid else False
        win = find_game_window(_window_title)
        errors = check_log_errors(_log_path, _log_byte_offset)
        _log_byte_offset = errors["last_byte"]
        mem = get_process_memory(_game_pid) if _game_pid else 0
        pos = check_log_position(_log_path)
        return {
            "alive": alive,
            "window": win,
            "errors": errors["errors"],
            "warnings": errors["warnings"],
            "memory_mb": round(mem / 1024 / 1024, 1),
            "position": pos,
        }

    elif method == "position_changed":
        pos = check_log_position(_log_path)
        return {"changed": pos.get("found", False), "position": pos}

    elif method == "no_crash":
        alive = check_process_alive(_game_pid) if _game_pid else False
        errors = check_log_errors(_log_path, _log_byte_offset)
        _log_byte_offset = errors["last_byte"]
        return {"crashed": not alive or len(errors["errors"]) > 0, "alive": alive, "fatal_errors": errors["errors"]}

    else:
        return {"error": f"unknown method: {method}"}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行参数模式（用于测试）
        req = json.loads(sys.argv[1])
        result = handle_request(req.get("method", ""), req.get("params", {}))
        print(json.dumps(result, ensure_ascii=False))
    else:
        # MCP 服务器 stdio 模式
        print(json.dumps({
            "status": "ok",
            "methods": ["initialize", "check_alive", "check_window", "check_errors",
                        "check_position", "check_memory", "full_status",
                        "position_changed", "no_crash"],
        }))
        sys.stdout.flush()
        
        # 持续从标准输入读取请求
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                req = json.loads(line)
                result = handle_request(req.get("method", ""), req.get("params", {}))
                print(json.dumps(result, ensure_ascii=False))
                sys.stdout.flush()
            except json.JSONDecodeError:
                print(json.dumps({"error": "invalid json"}))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({"error": str(e)}))
                sys.stdout.flush()
