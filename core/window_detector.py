#!/usr/bin/env python3
"""
Windows 窗口视觉检测系统
不只是看进程，而是检查实际可见窗口
解决"只看进程不知道窗口开没开"的问题
"""

import ctypes
import ctypes.wintypes
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_VISIBLE = 0x10000000
WS_MINIMIZE = 0x20000000
GWL_HWNDPARENT = -8
OWNER_DESKTOP = 0

APP_MAPPINGS = {
    "trae": {
        "process_names": ["Trae.exe", "trae.exe"],
        "window_titles": ["Trae", "Trae AI", "Trae -"],
        "check_path": "%SOFTWARE_DIR%/AI/Trae",
        "description": "Trae AI IDE",
    },
    "vscode": {
        "process_names": ["Code.exe", "VSCodium.exe"],
        "window_titles": ["Visual Studio Code", "VS Code", "VSCodium"],
        "check_path": None,
        "description": "VS Code",
    },
    "blender": {
        "process_names": ["blender.exe", "blender-launcher.exe"],
        "window_titles": ["Blender"],
        "check_path": None,
        "description": "Blender 3D",
    },
    "unreal": {
        "process_names": ["UnrealEditor.exe", "UE5Editor.exe", "UnrealEditor-Win64-DebugGame.exe"],
        "window_titles": ["Unreal Editor", "Unreal Engine"],
        "check_path": None,
        "description": "Unreal Engine",
    },
    "unity": {
        "process_names": ["Unity.exe", "Unity Hub.exe"],
        "window_titles": ["Unity", "Unity Hub"],
        "check_path": None,
        "description": "Unity",
    },
    "godot": {
        "process_names": ["Godot_v", "godot.exe"],
        "window_titles": ["Godot Engine"],
        "check_path": None,
        "description": "Godot Engine",
    },
    "github_desktop": {
        "process_names": ["GitHubDesktop.exe"],
        "window_titles": ["GitHub Desktop"],
        "check_path": None,
        "description": "GitHub Desktop",
    },
    "chrome": {
        "process_names": ["chrome.exe"],
        "window_titles": ["Google Chrome"],
        "check_path": None,
        "description": "Google Chrome",
    },
    "firefox": {
        "process_names": ["firefox.exe"],
        "window_titles": ["Mozilla Firefox"],
        "check_path": None,
        "description": "Firefox",
    },
    "steam": {
        "process_names": ["steam.exe", "steamwebhelper.exe"],
        "window_titles": ["Steam"],
        "check_path": None,
        "description": "Steam",
    },
    "watt_toolkit": {
        "process_names": ["Steam++.exe", "Watt Toolkit.exe"],
        "window_titles": ["Watt Toolkit", "Steam++"],
        "check_path": None,
        "description": "Watt Toolkit (Steam++)",
    },
    "claude": {
        "process_names": ["Claude.exe"],
        "window_titles": ["Claude"],
        "check_path": None,
        "description": "Claude Desktop",
    },
    "cursor": {
        "process_names": ["Cursor.exe"],
        "window_titles": ["Cursor"],
        "check_path": None,
        "description": "Cursor AI",
    },
    "terminal": {
        "process_names": ["WindowsTerminal.exe", "cmd.exe", "powershell.exe"],
        "window_titles": ["Windows Terminal", "Command Prompt", "PowerShell"],
        "check_path": None,
        "description": "Terminal",
    },
    "python": {
        "process_names": ["python.exe", "pythonw.exe"],
        "window_titles": [],
        "check_path": None,
        "description": "Python",
    },
}


def get_visible_windows() -> List[Dict]:
    windows = []

    def enum_callback(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        if not (style & WS_VISIBLE):
            return True

        title_len = user32.GetWindowTextLengthW(hwnd)
        if title_len == 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(title_len + 1)
        user32.GetWindowTextW(hwnd, title_buffer, title_len + 1)
        title = title_buffer.value

        if not title.strip():
            return True

        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        is_minimized = bool(style & WS_MINIMIZE)

        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        width = rect.right - rect.left
        height = rect.bottom - rect.top

        class_name_buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_name_buffer, 256)
        class_name = class_name_buffer.value

        windows.append(
            {
                "hwnd": hwnd,
                "title": title,
                "pid": pid.value,
                "minimized": is_minimized,
                "visible": True,
                "width": width,
                "height": height,
                "class_name": class_name,
                "has_ui": width > 50 and height > 50,
            }
        )

        return True

    user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
    return windows


def get_process_list() -> Dict[int, str]:
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, encoding="gbk", errors="replace"
    )

    processes = {}
    for line in result.stdout.strip().split("\n"):
        try:
            parts = line.strip().split('","')
            if len(parts) >= 2:
                name = parts[0].strip('"')
                pid = int(parts[1].strip('"'))
                processes[pid] = name
        except (ValueError, IndexError):
            continue

    return processes


def find_process_by_name(process_name: str) -> List[int]:
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {process_name}"],
        capture_output=True,
        text=True,
        encoding="gbk",
        errors="replace",
    )

    pids = []
    for line in result.stdout.strip().split("\n"):
        try:
            parts = line.strip().split('","')
            if len(parts) >= 2:
                pid = int(parts[1].strip('"'))
                pids.append(pid)
        except (ValueError, IndexError):
            continue

    return pids


def check_app_status(app_name: str) -> Dict:
    app_name = app_name.lower().replace(" ", "_").replace("-", "_")

    mapping = None
    for key, val in APP_MAPPINGS.items():
        if key.lower() == app_name:
            mapping = val
            break

    if not mapping:
        for key, val in APP_MAPPINGS.items():
            if app_name in key.lower() or key.lower() in app_name:
                mapping = val
                break

    if not mapping:
        return {
            "app": app_name,
            "status": "unknown",
            "process_running": False,
            "window_visible": False,
            "window_minimized": False,
            "window_title": None,
            "message": f"未知应用: {app_name}",
        }

    process_running = False
    running_pids = []

    for proc_name in mapping["process_names"]:
        pids = find_process_by_name(proc_name)
        if pids:
            process_running = True
            running_pids.extend(pids)

    windows = get_visible_windows()
    processes = get_process_list()

    app_windows = []
    for win in windows:
        pid = win["pid"]
        proc_name = processes.get(pid, "")

        matched = False
        if pid in running_pids:
            matched = True
        else:
            for pn in mapping["process_names"]:
                if pn.lower() == proc_name.lower():
                    matched = True
                    break

        if not matched:
            for title_keyword in mapping["window_titles"]:
                if title_keyword.lower() in win["title"].lower():
                    matched = True
                    break

        if matched and win["has_ui"]:
            app_windows.append(win)

    visible_windows = [w for w in app_windows if not w["minimized"]]
    minimized_windows = [w for w in app_windows if w["minimized"]]

    if visible_windows:
        status = "visible"
        primary = visible_windows[0]
    elif minimized_windows:
        status = "minimized"
        primary = minimized_windows[0]
    elif process_running:
        status = "background"
        primary = None
    else:
        status = "not_running"
        primary = None

    result = {
        "app": mapping["description"],
        "status": status,
        "process_running": process_running,
        "window_visible": len(visible_windows) > 0,
        "window_minimized": len(minimized_windows) > 0,
        "window_count": len(app_windows),
        "running_pids": running_pids,
    }

    if primary:
        result["window_title"] = primary["title"]
        result["window_size"] = f"{primary['width']}x{primary['height']}"
        result["is_minimized"] = primary["minimized"]

    if status == "background":
        result["message"] = f"{mapping['description']} 进程在运行但窗口不可见，可能需要点击托盘图标打开"
    elif status == "not_running":
        result["message"] = f"{mapping['description']} 未运行"
    elif status == "minimized":
        result["message"] = f"{mapping['description']} 已最小化"
    else:
        result["message"] = f"{mapping['description']} 正常运行中"

    return result


def list_all_visible_apps() -> List[Dict]:
    windows = get_visible_windows()
    processes = get_process_list()

    app_results = {}

    for app_key, mapping in APP_MAPPINGS.items():
        app_windows = []
        running_pids = []

        for proc_name in mapping["process_names"]:
            pids = find_process_by_name(proc_name)
            running_pids.extend(pids)

        for win in windows:
            pid = win["pid"]
            proc_name = processes.get(pid, "")

            matched = False
            if pid in running_pids:
                matched = True
            else:
                for pn in mapping["process_names"]:
                    if pn.lower() == proc_name.lower():
                        matched = True
                        break

            if not matched:
                for title_keyword in mapping["window_titles"]:
                    if title_keyword.lower() in win["title"].lower():
                        matched = True
                        break

            if matched and win["has_ui"]:
                app_windows.append(win)

        if running_pids or app_windows:
            visible = [w for w in app_windows if not w["minimized"]]
            minimized = [w for w in app_windows if w["minimized"]]

            if visible:
                status = "visible"
            elif minimized:
                status = "minimized"
            else:
                status = "background"

            app_results[app_key] = {
                "app": mapping["description"],
                "status": status,
                "window_count": len(app_windows),
                "primary_title": app_windows[0]["title"] if app_windows else None,
            }

    return app_results


def is_app_really_visible(app_name: str) -> bool:
    status = check_app_status(app_name)
    return status.get("status") == "visible"


def smart_detect(app_name: str) -> str:
    status = check_app_status(app_name)
    return status.get("message", "未知状态")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check":
            app = sys.argv[2] if len(sys.argv) > 2 else "trae"
            result = check_app_status(app)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif cmd == "list":
            apps = list_all_visible_apps()
            for key, info in apps.items():
                status_icon = {"visible": "🟢", "minimized": "🟡", "background": "🔴"}.get(info["status"], "⚪")
                title = f" - {info['primary_title']}" if info.get("primary_title") else ""
                print(f"  {status_icon} {info['app']}: {info['status']}{title}")

        elif cmd == "visible":
            app = sys.argv[2] if len(sys.argv) > 2 else "trae"
            result = is_app_really_visible(app)
            print("YES" if result else "NO")

        elif cmd == "smart":
            app = sys.argv[2] if len(sys.argv) > 2 else "trae"
            print(smart_detect(app))

        else:
            print("Usage: python window_detector.py [check|list|visible|smart] [app_name]")
    else:
        print("Windows Window Detector")
        print("=" * 40)
        print()

        print("Running apps with windows:")
        apps = list_all_visible_apps()
        for key, info in sorted(
            apps.items(), key=lambda x: {"visible": 0, "minimized": 1, "background": 2}.get(x[1]["status"], 3)
        ):
            status_icon = {"visible": "🟢", "minimized": "🟡", "background": "🔴"}.get(info["status"], "⚪")
            title = f" - {info['primary_title']}" if info.get("primary_title") else ""
            print(f"  {status_icon} {info['app']}: {info['status']}{title}")

        print()
        print(f"Total: {len(apps)} apps detected")
