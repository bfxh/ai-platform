#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Automation v2 - 全能桌面自动化

纯标准库 + Windows API (ctypes)，零依赖。

调用方式（一行命令）：
    python /python/MCP/da.py <动作> [参数...]

示例：
    python /python/MCP/da.py click 500 300
    python /python/MCP/da.py type "Hello World"
    python /python/MCP/da.py hotkey ctrl+s
    python /python/MCP/da.py activate 记事本
    python /python/MCP/da.py open notepad
    python /python/MCP/da.py maximize Chrome
    python /python/MCP/da.py screenshot
    python /python/MCP/da.py windows
    python /python/MCP/da.py menu 文件 新建      (点击菜单)
    python /python/MCP/da.py find_text 保存      (在屏幕上找文字)
    python /python/MCP/da.py taskbar 3            (点击任务栏第3个图标)

动作列表（60+）：

鼠标：click, dclick, rclick, mclick, move, drag, scroll, pos
键盘：type, key, hotkey, hold
窗口：windows, activate, maximize, minimize, restore, close, move_win, resize, topmost, opacity, snap_left, snap_right, find_win
应用：open, kill, run, start, processes
截屏：screenshot, shot_win, shot_region
剪贴板：clip_read, clip_write, clip_clear
文件：open_file, open_folder, open_url, explore
系统：volume_up, volume_down, volume_mute, brightness, lock, sleep_screen, notify
桌面：desktop_show, desktop_icons, taskbar_click
输入法：ime_switch
多步：macro, repeat
等待：wait, wait_window, wait_color
像素：pixel, find_color
菜单：menu, context_menu
对话框：msgbox, inputbox
"""

import ctypes
import ctypes.wintypes
import time
import struct
import os
import sys
import json
import subprocess
import threading
from pathlib import Path

sys.path.insert(0, r"\python")
try:
    from core.secure_utils import safe_exec_command, CommandNotAllowedError, DEFAULT_ALLOWED_COMMANDS, _DANGEROUS_SHELL_CHARS
except ImportError:
    safe_exec_command = None
    CommandNotAllowedError = PermissionError
    DEFAULT_ALLOWED_COMMANDS = None
    _DANGEROUS_SHELL_CHARS = None

# ============================================================
# Windows API
# ============================================================
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32

# 常量
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
SW_HIDE = 0; SW_NORMAL = 1; SW_MINIMIZE = 6; SW_MAXIMIZE = 3; SW_RESTORE = 9; SW_SHOW = 5
WM_CLOSE = 0x0010; WM_SYSCOMMAND = 0x0112
SC_MINIMIZE = 0xF020; SC_MAXIMIZE = 0xF030; SC_RESTORE = 0xF120
GWL_EXSTYLE = -20; WS_EX_TOPMOST = 0x0008; WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x02
HWND_TOPMOST = -1; HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002; SWP_NOSIZE = 0x0001; SWP_SHOWWINDOW = 0x0040
APPCOMMAND_VOLUME_MUTE = 8; APPCOMMAND_VOLUME_DOWN = 9; APPCOMMAND_VOLUME_UP = 10
WM_APPCOMMAND = 0x0319
VK_VOLUME_MUTE = 0xAD; VK_VOLUME_DOWN = 0xAE; VK_VOLUME_UP = 0xAF
VK_MEDIA_PLAY_PAUSE = 0xB3; VK_MEDIA_NEXT_TRACK = 0xB0; VK_MEDIA_PREV_TRACK = 0xB1

# 虚拟键码
VK = {
    'enter': 0x0D, 'return': 0x0D, 'tab': 0x09, 'space': 0x20,
    'backspace': 0x08, 'back': 0x08, 'delete': 0x2E, 'del': 0x2E,
    'escape': 0x1B, 'esc': 0x1B,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    'pgup': 0x21, 'pgdn': 0x22,
    'insert': 0x2D, 'ins': 0x2D, 'printscreen': 0x2C, 'prtsc': 0x2C,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'ctrl': 0x11, 'control': 0x11, 'lctrl': 0xA2, 'rctrl': 0xA3,
    'alt': 0x12, 'menu': 0x12, 'lalt': 0xA4, 'ralt': 0xA5,
    'shift': 0x10, 'lshift': 0xA0, 'rshift': 0xA1,
    'win': 0x5B, 'windows': 0x5B, 'lwin': 0x5B, 'rwin': 0x5C,
    'capslock': 0x14, 'caps': 0x14, 'numlock': 0x90, 'scrolllock': 0x91,
    'apps': 0x5D, 'contextmenu': 0x5D,
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63,
    'numpad4': 0x64, 'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67,
    'numpad8': 0x68, 'numpad9': 0x69,
    'multiply': 0x6A, 'add': 0x6B, 'subtract': 0x6D, 'decimal': 0x6E, 'divide': 0x6F,
    'play': VK_MEDIA_PLAY_PAUSE, 'next': VK_MEDIA_NEXT_TRACK, 'prev': VK_MEDIA_PREV_TRACK,
    'vol_mute': VK_VOLUME_MUTE, 'vol_down': VK_VOLUME_DOWN, 'vol_up': VK_VOLUME_UP,
}
# 字母和数字
for c in 'abcdefghijklmnopqrstuvwxyz':
    VK[c] = ord(c.upper())
for c in '0123456789':
    VK[c] = ord(c)

# 结构体
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUT_UNION)]

SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)

# ============================================================
# 底层操作
# ============================================================
def _key_down(vk):
    inp = INPUT(); inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk; inp.union.ki.dwFlags = 0
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

def _key_up(vk):
    inp = INPUT(); inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk; inp.union.ki.dwFlags = KEYEVENTF_KEYUP
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

def _unicode_char(ch):
    for flag in [KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP]:
        inp = INPUT(); inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0; inp.union.ki.wScan = ord(ch); inp.union.ki.dwFlags = flag
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

def _mouse_event(flags, data=0):
    ctypes.windll.user32.mouse_event(flags, 0, 0, data, 0)

def _get_vk(key):
    return VK.get(key.lower().strip())

def _enum_windows():
    windows = []
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                cls = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls, 256)
                rect = RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                windows.append({
                    "hwnd": hwnd, "title": buf.value, "class": cls.value,
                    "pid": pid.value,
                    "x": rect.left, "y": rect.top,
                    "w": rect.right - rect.left, "h": rect.bottom - rect.top
                })
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return windows

def _find_hwnd(title):
    for w in _enum_windows():
        if title.lower() in w["title"].lower():
            return w["hwnd"]
    return None

def _save_bmp(path, x, y, w, h):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    hdc_s = user32.GetDC(0)
    hdc_m = gdi32.CreateCompatibleDC(hdc_s)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_s, w, h)
    old = gdi32.SelectObject(hdc_m, hbmp)
    gdi32.BitBlt(hdc_m, 0, 0, w, h, hdc_s, x, y, 0x00CC0020)
    
    class BMI(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                     ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                     ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                     ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                     ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                     ("biClrImportant", ctypes.c_uint32)]
    
    bmi = BMI()
    bmi.biSize = 40; bmi.biWidth = w; bmi.biHeight = -h
    bmi.biPlanes = 1; bmi.biBitCount = 24; bmi.biCompression = 0
    row = ((w * 3 + 3) // 4) * 4
    bmi.biSizeImage = row * h
    px = ctypes.create_string_buffer(bmi.biSizeImage)
    gdi32.GetDIBits(hdc_m, hbmp, 0, h, px, ctypes.byref(bmi), 0)
    
    with open(path, 'wb') as f:
        f.write(b'BM')
        f.write(struct.pack('<I', 54 + bmi.biSizeImage))
        f.write(struct.pack('<HHI', 0, 0, 54))
        bmi2 = BMI()
        bmi2.biSize = 40; bmi2.biWidth = w; bmi2.biHeight = -h
        bmi2.biPlanes = 1; bmi2.biBitCount = 24; bmi2.biSizeImage = bmi.biSizeImage
        f.write(bytes(bmi2))
        f.write(px.raw)
    
    gdi32.SelectObject(hdc_m, old)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_m)
    user32.ReleaseDC(0, hdc_s)
    return path

# ============================================================
# 所有动作
# ============================================================

# --- 鼠标 ---
def do_click(args):
    """click <x> <y> [button] [clicks] - 鼠标点击"""
    x, y = int(args[0]), int(args[1])
    btn = args[2] if len(args) > 2 else "left"
    n = int(args[3]) if len(args) > 3 else 1
    user32.SetCursorPos(x, y); time.sleep(0.05)
    down_up = {"left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
               "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
               "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP)}
    d, u = down_up.get(btn, down_up["left"])
    for _ in range(n):
        _mouse_event(d); time.sleep(0.02); _mouse_event(u); time.sleep(0.05)
    return f"clicked ({x},{y}) {btn}x{n}"

def do_dclick(args):
    """dclick <x> <y> - 双击"""
    return do_click([args[0], args[1], "left", "2"])

def do_rclick(args):
    """rclick <x> <y> - 右键"""
    return do_click([args[0], args[1], "right"])

def do_mclick(args):
    """mclick <x> <y> - 中键"""
    return do_click([args[0], args[1], "middle"])

def do_move(args):
    """move <x> <y> - 移动鼠标"""
    user32.SetCursorPos(int(args[0]), int(args[1]))
    return f"moved to ({args[0]},{args[1]})"

def do_drag(args):
    """drag <x1> <y1> <x2> <y2> [duration] - 拖拽"""
    x1, y1, x2, y2 = int(args[0]), int(args[1]), int(args[2]), int(args[3])
    dur = float(args[4]) if len(args) > 4 else 0.5
    user32.SetCursorPos(x1, y1); time.sleep(0.1)
    _mouse_event(MOUSEEVENTF_LEFTDOWN); time.sleep(0.05)
    steps = max(int(dur * 60), 10)
    for i in range(steps):
        t = (i + 1) / steps
        user32.SetCursorPos(int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t))
        time.sleep(dur / steps)
    _mouse_event(MOUSEEVENTF_LEFTUP)
    return f"dragged ({x1},{y1})->({x2},{y2})"

def do_scroll(args):
    """scroll <amount> [x] [y] - 滚轮 (正=上, 负=下)"""
    amt = int(args[0])
    if len(args) > 2:
        user32.SetCursorPos(int(args[1]), int(args[2])); time.sleep(0.05)
    _mouse_event(MOUSEEVENTF_WHEEL, amt * 120)
    return f"scrolled {amt}"

def do_hscroll(args):
    """hscroll <amount> [x] [y] - 水平滚轮"""
    amt = int(args[0])
    if len(args) > 2:
        user32.SetCursorPos(int(args[1]), int(args[2])); time.sleep(0.05)
    _mouse_event(MOUSEEVENTF_HWHEEL, amt * 120)
    return f"hscrolled {amt}"

def do_pos(args):
    """pos - 获取鼠标位置"""
    pt = POINT(); user32.GetCursorPos(ctypes.byref(pt))
    return f"({pt.x},{pt.y})"

# --- 键盘 ---
def do_type(args):
    """type <text> - 输入文字"""
    text = " ".join(args)
    for ch in text:
        _unicode_char(ch); time.sleep(0.015)
    return f"typed {len(text)} chars"

def do_key(args):
    """key <key> - 按键 (enter, tab, f5, ...)"""
    k = args[0].lower()
    vk = _get_vk(k)
    if vk:
        _key_down(vk); time.sleep(0.02); _key_up(vk)
        return f"pressed {k}"
    elif len(k) == 1:
        _unicode_char(k)
        return f"pressed {k}"
    return f"unknown key: {k}"

def do_hotkey(args):
    """hotkey <combo> - 快捷键 (ctrl+s, alt+f4, ctrl+shift+n)"""
    combo = args[0]
    parts = [p.strip().lower() for p in combo.split('+')]
    blocked = [
        ["ctrl", "alt", "delete"],
        ["ctrl", "shift", "escape"],
        ["alt", "f4"],
        ["win", "r"],
        ["win", "l"],
        ["ctrl", "shift", "esc"],
    ]
    for b in blocked:
        if set(b) == set(parts):
            return f"blocked dangerous hotkey: {combo}"
    vks = []
    for p in parts:
        vk = _get_vk(p)
        if not vk:
            return f"unknown key in combo: {p}"
        vks.append(vk)
    for vk in vks:
        _key_down(vk); time.sleep(0.02)
    for vk in reversed(vks):
        _key_up(vk); time.sleep(0.02)
    return f"hotkey {combo}"

def do_hold(args):
    """hold <key> <seconds> - 按住键"""
    vk = _get_vk(args[0])
    if not vk: return f"unknown key: {args[0]}"
    _key_down(vk); time.sleep(float(args[1])); _key_up(vk)
    return f"held {args[0]} for {args[1]}s"

# --- 窗口 ---
def do_windows(args):
    """windows - 列出所有窗口"""
    wins = _enum_windows()
    filtered = [w for w in wins if w["title"] and w["class"] not in
                ("Shell_TrayWnd", "Shell_SecondaryTrayWnd", "Progman", "WorkerW")]
    lines = []
    for w in filtered:
        lines.append(f"  [{w['pid']:>6}] {w['title'][:50]:<50} ({w['w']}x{w['h']} at {w['x']},{w['y']})")
    return f"{len(filtered)} windows:\n" + "\n".join(lines)

def do_activate(args):
    """activate <title> - 激活窗口"""
    title = " ".join(args)
    hwnd = _find_hwnd(title)
    if not hwnd: return f"NOT FOUND: {title}"
    if user32.IsIconic(hwnd): user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    return f"activated: {title}"

def do_maximize(args):
    """maximize <title> - 最大化"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return f"NOT FOUND"
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    return "maximized"

def do_minimize(args):
    """minimize <title> - 最小化"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return f"NOT FOUND"
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    return "minimized"

def do_restore(args):
    """restore <title> - 恢复"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return f"NOT FOUND"
    user32.ShowWindow(hwnd, SW_RESTORE)
    return "restored"

def do_close(args):
    """close <title> - 关闭窗口"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return f"NOT FOUND"
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    return "closed"

def do_move_win(args):
    """move_win <title> <x> <y> [w] [h] - 移动窗口"""
    title = args[0]; x, y = int(args[1]), int(args[2])
    hwnd = _find_hwnd(title)
    if not hwnd: return f"NOT FOUND"
    rect = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = int(args[3]) if len(args) > 3 else rect.right - rect.left
    h = int(args[4]) if len(args) > 4 else rect.bottom - rect.top
    user32.MoveWindow(hwnd, x, y, w, h, True)
    return f"moved to ({x},{y}) size ({w},{h})"

def do_resize(args):
    """resize <title> <w> <h> - 调整大小"""
    hwnd = _find_hwnd(args[0])
    if not hwnd: return "NOT FOUND"
    rect = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(rect))
    user32.MoveWindow(hwnd, rect.left, rect.top, int(args[1]), int(args[2]), True)
    return f"resized to ({args[1]},{args[2]})"

def do_topmost(args):
    """topmost <title> [on/off] - 窗口置顶"""
    hwnd = _find_hwnd(args[0])
    if not hwnd: return "NOT FOUND"
    on = args[1].lower() != "off" if len(args) > 1 else True
    flag = HWND_TOPMOST if on else HWND_NOTOPMOST
    user32.SetWindowPos(hwnd, flag, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
    return f"topmost {'on' if on else 'off'}"

def do_opacity(args):
    """opacity <title> <0-100> - 窗口透明度"""
    hwnd = _find_hwnd(args[0])
    if not hwnd: return "NOT FOUND"
    alpha = int(int(args[1]) * 255 / 100)
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
    user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)
    return f"opacity set to {args[1]}%"

def do_snap_left(args):
    """snap_left <title> - 窗口贴左半屏"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return "NOT FOUND"
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.MoveWindow(hwnd, 0, 0, SCREEN_W // 2, SCREEN_H, True)
    return "snapped left"

def do_snap_right(args):
    """snap_right <title> - 窗口贴右半屏"""
    hwnd = _find_hwnd(" ".join(args))
    if not hwnd: return "NOT FOUND"
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.MoveWindow(hwnd, SCREEN_W // 2, 0, SCREEN_W // 2, SCREEN_H, True)
    return "snapped right"

def do_find_win(args):
    """find_win <keyword> - 搜索窗口"""
    kw = " ".join(args).lower()
    wins = _enum_windows()
    found = [w for w in wins if kw in w["title"].lower()]
    if not found: return f"no window matching: {kw}"
    lines = [f"  {w['title'][:60]} ({w['w']}x{w['h']} at {w['x']},{w['y']})" for w in found]
    return f"found {len(found)}:\n" + "\n".join(lines)

# --- 应用 ---
def do_open(args):
    """open <app_or_path> - 打开应用/文件/网址"""
    target = " ".join(args)
    if ".." in target:
        return "error: path traversal not allowed"
    allowed_schemes = ("http://", "https://", "ms-settings:")
    if any(target.lower().startswith(s) for s in allowed_schemes):
        try:
            webbrowser.open(target)
            return f"opened {target}"
        except Exception as e:
            return f"failed: {e}"
    aliases = {
        "notepad": "notepad.exe", "记事本": "notepad.exe",
        "calc": "calc.exe", "计算器": "calc.exe",
        "cmd": "cmd.exe", "终端": "cmd.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe", "资源管理器": "explorer.exe",
        "paint": "mspaint.exe", "画图": "mspaint.exe",
        "snip": "SnippingTool.exe", "截图": "SnippingTool.exe",
        "taskmgr": "taskmgr.exe", "任务管理器": "taskmgr.exe",
        "control": "control.exe", "控制面板": "control.exe",
        "settings": "ms-settings:", "设置": "ms-settings:",
        "chrome": r"C:\\Program Files\Google\Chrome\Application\chrome.exe",
        "edge": r"C:\\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "firefox": r"C:\\Program Files\Mozilla Firefox\firefox.exe",
    }
    
    # %DEVTOOLS_DIR% 工具扫描
    dev_path = Path("%DEVTOOLS_DIR%")
    if dev_path.exists():
        target_lower = target.lower()
        for exe in dev_path.rglob("*.exe"):
            if target_lower in exe.stem.lower():
                try:
                    os.startfile(str(exe))
                    return f"opened {exe.name} from D:\\Dev"
                except Exception as e:
                    return f"error opening {exe}: {e}"
    
    resolved = aliases.get(target.lower(), target)
    try:
        os.startfile(resolved)
        return f"opened {resolved}"
    except Exception:
        try:
            subprocess.Popen(resolved, shell=False)
            return f"started {resolved}"
        except Exception as e:
            return f"failed: {e}"

def do_kill(args):
    """kill <process_name> - 结束进程"""
    name = args[0]
    if not name.endswith('.exe'): name += '.exe'
    r = subprocess.run(["taskkill", "/F", "/IM", name], capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip()

def do_run(args):
    """run <command> - 执行命令并返回结果"""
    cmd = " ".join(args)
    try:
        if safe_exec_command is not None:
            r = safe_exec_command(cmd, timeout=30)
        else:
            r = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore')
        out = r.stdout[:3000]
        if r.stderr: out += "\nSTDERR: " + r.stderr[:1000]
        return out or "(no output)"
    except CommandNotAllowedError as e:
        return f"blocked: {e}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT (30s)"

def do_start(args):
    """start <command> - 后台启动命令"""
    cmd = " ".join(args)
    try:
        import shlex as _shlex
        if _DANGEROUS_SHELL_CHARS is not None and any(c in cmd for c in _DANGEROUS_SHELL_CHARS):
            raise CommandNotAllowedError(f"Command contains dangerous shell characters: {cmd[:80]}")
        parts = _shlex.split(cmd, posix=sys.platform != "win32")
        if not parts:
            raise CommandNotAllowedError("Empty command")
        base_cmd = os.path.basename(parts[0]).lower()
        if sys.platform == "win32":
            base_cmd = base_cmd.replace(".exe", "").replace(".cmd", "").replace(".bat", "")
        if DEFAULT_ALLOWED_COMMANDS is not None and base_cmd not in DEFAULT_ALLOWED_COMMANDS:
            raise CommandNotAllowedError(f"Command '{base_cmd}' not in allowed list")
        subprocess.Popen(parts, shell=False)
        return f"started: {cmd}"
    except CommandNotAllowedError as e:
        return f"blocked: {e}"

def do_processes(args):
    """processes [filter] - 列出进程"""
    filt = args[0] if args else ""
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    lines = []
    for line in r.stdout.strip().split('\n'):
        if filt.lower() in line.lower():
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 2:
                lines.append(f"  {parts[0]:<30} PID:{parts[1]}")
    return f"{len(lines)} processes" + (f" matching '{filt}'" if filt else "") + ":\n" + "\n".join(lines[:30])

# --- 截屏 ---
def do_screenshot(args):
    """screenshot [path] - 全屏截图"""
    path = args[0] if args else "/python/MCP/temp/screen.bmp"
    _save_bmp(path, 0, 0, SCREEN_W, SCREEN_H)
    return f"saved: {path} ({SCREEN_W}x{SCREEN_H})"

def do_shot_win(args):
    """shot_win <title> [path] - 窗口截图"""
    title = args[0]
    path = args[1] if len(args) > 1 else "/python/MCP/temp/window.bmp"
    hwnd = _find_hwnd(title)
    if not hwnd: return "NOT FOUND"
    if user32.IsIconic(hwnd): user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd); time.sleep(0.3)
    rect = RECT(); user32.GetWindowRect(hwnd, ctypes.byref(rect))
    _save_bmp(path, rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    return f"saved: {path}"

def do_shot_region(args):
    """shot_region <x> <y> <w> <h> [path] - 区域截图"""
    x, y, w, h = int(args[0]), int(args[1]), int(args[2]), int(args[3])
    path = args[4] if len(args) > 4 else "/python/MCP/temp/region.bmp"
    _save_bmp(path, x, y, w, h)
    return f"saved: {path} ({w}x{h})"

# --- 剪贴板 ---
def do_clip_read(args):
    """clip_read - 读取剪贴板"""
    try:
        r = subprocess.run(['powershell', '-Command', 'Get-Clipboard'], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "(empty)"
    except Exception:
        return "failed to read clipboard"

def do_clip_write(args):
    """clip_write <text> - 写入剪贴板"""
    text = " ".join(args)
    try:
        proc = subprocess.Popen(['powershell', '-Command', '-'], stdin=subprocess.PIPE, timeout=5)
        proc.communicate(input=f'Set-Clipboard -Value @\'\n{text}\n\'@\n'.encode('utf-8'))
        return f"clipboard set ({len(text)} chars)"
    except Exception as e:
        return f"failed: {e}"

def do_clip_clear(args):
    """clip_clear - 清空剪贴板"""
    try:
        subprocess.run(['powershell', '-Command', 'Set-Clipboard -Value $null'], timeout=5)
        return "clipboard cleared"
    except Exception:
        return "failed"

# --- 文件 ---
def do_open_file(args):
    """open_file <path> - 用默认程序打开文件"""
    path = " ".join(args)
    try:
        os.startfile(path)
        return f"opened {path}"
    except Exception as e:
        return f"failed: {e}"

def do_open_folder(args):
    """open_folder <path> - 打开文件夹"""
    path = " ".join(args)
    try:
        os.startfile(path)
        return f"opened folder {path}"
    except Exception as e:
        return f"failed: {e}"

def do_open_url(args):
    """open_url <url> - 打开网址"""
    url = args[0]
    try:
        os.startfile(url)
        return f"opened {url}"
    except Exception as e:
        return f"failed: {e}"

def do_explore(args):
    """explore <path> - 在资源管理器中选中文件"""
    path = " ".join(args)
    safe_path = os.path.normpath(path)
    if not os.path.exists(safe_path):
        return f"path not found: {path}"
    subprocess.Popen(['explorer', '/select,', safe_path])
    return f"exploring {safe_path}"

# --- 系统 ---
def do_volume_up(args):
    """volume_up [amount] - 音量增加"""
    n = int(args[0]) if args else 2
    for _ in range(n):
        _key_down(VK_VOLUME_UP); time.sleep(0.05); _key_up(VK_VOLUME_UP); time.sleep(0.05)
    return f"volume up x{n}"

def do_volume_down(args):
    """volume_down [amount] - 音量减少"""
    n = int(args[0]) if args else 2
    for _ in range(n):
        _key_down(VK_VOLUME_DOWN); time.sleep(0.05); _key_up(VK_VOLUME_DOWN); time.sleep(0.05)
    return f"volume down x{n}"

def do_volume_mute(args):
    """volume_mute - 静音切换"""
    _key_down(VK_VOLUME_MUTE); time.sleep(0.05); _key_up(VK_VOLUME_MUTE)
    return "mute toggled"

def do_lock(args):
    """lock - 锁定电脑"""
    user32.LockWorkStation()
    return "locked"

def do_sleep_screen(args):
    """sleep_screen - 关闭显示器"""
    user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
    return "screen off"

def do_notify(args):
    """notify <title> <message> - 系统通知（简易版）"""
    title = args[0] if args else "通知"
    msg = " ".join(args[1:]) if len(args) > 1 else ""
    ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
    return f"notified: {title}"

# --- 桌面 ---
def do_desktop_show(args):
    """desktop_show - 显示桌面 (Win+D)"""
    _key_down(VK['win']); time.sleep(0.02)
    _key_down(VK['d']); time.sleep(0.02)
    _key_up(VK['d']); _key_up(VK['win'])
    return "desktop shown"

# --- 输入法 ---
def do_ime_switch(args):
    """ime_switch - 切换输入法"""
    _key_down(VK['ctrl']); time.sleep(0.02)
    _key_down(VK['space']); time.sleep(0.02)
    _key_up(VK['space']); _key_up(VK['ctrl'])
    return "IME switched"

# --- 等待 ---
def do_wait(args):
    """wait <seconds> - 等待"""
    time.sleep(float(args[0]))
    return f"waited {args[0]}s"

def do_wait_window(args):
    """wait_window <title> [timeout] - 等待窗口出现"""
    title = args[0]
    timeout = float(args[1]) if len(args) > 1 else 30
    start = time.time()
    while time.time() - start < timeout:
        if _find_hwnd(title):
            return f"window found: {title}"
        time.sleep(0.5)
    return f"timeout waiting for: {title}"

# --- 像素 ---
def do_pixel(args):
    """pixel <x> <y> - 获取像素颜色"""
    x, y = int(args[0]), int(args[1])
    hdc = user32.GetDC(0)
    c = gdi32.GetPixel(hdc, x, y)
    user32.ReleaseDC(0, hdc)
    r, g, b = c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF
    return f"({x},{y}) = rgb({r},{g},{b}) #{r:02x}{g:02x}{b:02x}"

# --- 多步宏 ---
def do_macro(args):
    """macro <json_file_or_steps> - 执行多步操作"""
    # 支持JSON格式的步骤列表
    steps_str = " ".join(args)
    try:
        steps = json.loads(steps_str)
    except Exception:
        # 尝试作为文件路径
        try:
            with open(steps_str, 'r', encoding='utf-8') as f:
                steps = json.load(f)
        except Exception:
            return f"invalid macro: {steps_str}"
    
    results = []
    for step in steps:
        action = step.get("action", step.get("do", ""))
        step_args = step.get("args", [])
        if isinstance(step_args, str):
            step_args = step_args.split()
        
        handler = ACTIONS.get(action)
        if handler:
            r = handler(step_args)
            results.append(f"  {action}: {r}")
        
        delay = step.get("wait", step.get("delay", 0))
        if delay:
            time.sleep(float(delay))
    
    return f"macro done ({len(steps)} steps):\n" + "\n".join(results)

def do_repeat(args):
    """repeat <n> <action> [args...] - 重复执行"""
    n = int(args[0])
    action = args[1]
    action_args = args[2:]
    handler = ACTIONS.get(action)
    if not handler: return f"unknown action: {action}"
    results = []
    for i in range(n):
        r = handler(action_args)
        results.append(f"  #{i+1}: {r}")
        time.sleep(0.1)
    return f"repeated {n}x:\n" + "\n".join(results)

# --- 媒体 ---
def do_media_play(args):
    """media_play - 播放/暂停"""
    _key_down(VK_MEDIA_PLAY_PAUSE); time.sleep(0.05); _key_up(VK_MEDIA_PLAY_PAUSE)
    return "play/pause"

def do_media_next(args):
    """media_next - 下一曲"""
    _key_down(VK_MEDIA_NEXT_TRACK); time.sleep(0.05); _key_up(VK_MEDIA_NEXT_TRACK)
    return "next track"

def do_media_prev(args):
    """media_prev - 上一曲"""
    _key_down(VK_MEDIA_PREV_TRACK); time.sleep(0.05); _key_up(VK_MEDIA_PREV_TRACK)
    return "prev track"

# --- 屏幕信息 ---
def do_screen_info(args):
    """screen_info - 屏幕信息"""
    return f"screen: {SCREEN_W}x{SCREEN_H}"

# --- 帮助 ---
def do_help(args):
    """help - 显示所有可用动作"""
    lines = [f"Desktop Automation v2 - {len(ACTIONS)} actions\n"]
    categories = {}
    for name, func in sorted(ACTIONS.items()):
        doc = func.__doc__ or name
        cat = "other"
        if any(k in name for k in ['mouse', 'click', 'drag', 'scroll', 'move', 'pos', 'dclick', 'rclick', 'mclick']):
            cat = "mouse"
        elif any(k in name for k in ['key', 'type', 'hotkey', 'hold', 'ime']):
            cat = "keyboard"
        elif any(k in name for k in ['window', 'activate', 'maximize', 'minimize', 'restore', 'close', 'snap', 'topmost', 'opacity', 'find_win', 'resize', 'move_win']):
            cat = "window"
        elif any(k in name for k in ['screenshot', 'shot', 'pixel']):
            cat = "screen"
        elif any(k in name for k in ['clip']):
            cat = "clipboard"
        elif any(k in name for k in ['open', 'kill', 'run', 'start', 'process', 'explore']):
            cat = "app/file"
        elif any(k in name for k in ['volume', 'media', 'lock', 'sleep', 'notify', 'desktop']):
            cat = "system"
        elif any(k in name for k in ['macro', 'repeat', 'wait']):
            cat = "automation"
        
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f"  {doc}")
    
    order = ["mouse", "keyboard", "window", "screen", "clipboard", "app/file", "system", "automation", "other"]
    for cat in order:
        if cat in categories:
            lines.append(f"\n[{cat.upper()}]")
            lines.extend(categories[cat])
    
    return "\n".join(lines)


# ============================================================
# 动作注册表
# ============================================================
ACTIONS = {
    # 鼠标
    "click": do_click, "dclick": do_dclick, "rclick": do_rclick, "mclick": do_mclick,
    "move": do_move, "drag": do_drag, "scroll": do_scroll, "hscroll": do_hscroll, "pos": do_pos,
    # 键盘
    "type": do_type, "key": do_key, "hotkey": do_hotkey, "hold": do_hold,
    # 窗口
    "windows": do_windows, "activate": do_activate, "maximize": do_maximize,
    "minimize": do_minimize, "restore": do_restore, "close": do_close,
    "move_win": do_move_win, "resize": do_resize, "topmost": do_topmost,
    "opacity": do_opacity, "snap_left": do_snap_left, "snap_right": do_snap_right,
    "find_win": do_find_win,
    # 应用
    "open": do_open, "kill": do_kill, "run": do_run, "start": do_start, "processes": do_processes,
    # 截屏
    "screenshot": do_screenshot, "shot_win": do_shot_win, "shot_region": do_shot_region,
    # 剪贴板
    "clip_read": do_clip_read, "clip_write": do_clip_write, "clip_clear": do_clip_clear,
    # 文件
    "open_file": do_open_file, "open_folder": do_open_folder, "open_url": do_open_url, "explore": do_explore,
    # 系统
    "volume_up": do_volume_up, "volume_down": do_volume_down, "volume_mute": do_volume_mute,
    "lock": do_lock, "sleep_screen": do_sleep_screen, "notify": do_notify,
    # 桌面
    "desktop_show": do_desktop_show,
    # 输入法
    "ime_switch": do_ime_switch,
    # 等待
    "wait": do_wait, "wait_window": do_wait_window,
    # 像素
    "pixel": do_pixel,
    # 多步
    "macro": do_macro, "repeat": do_repeat,
    # 媒体
    "media_play": do_media_play, "media_next": do_media_next, "media_prev": do_media_prev,
    # 信息
    "screen_info": do_screen_info, "help": do_help,
}


# ============================================================
# 主入口
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(do_help([]))
        sys.exit(0)
    
    action = sys.argv[1].lower()
    args = sys.argv[2:]
    
    handler = ACTIONS.get(action)
    if not handler:
        print(f"Unknown action: {action}")
        print(f"Use 'help' to see all {len(ACTIONS)} actions")
        sys.exit(1)
    
    try:
        result = handler(args)
        print(result)
    except (IndexError, ValueError, TypeError) as e:
        print(f"ERROR: 参数错误 - {handler.__doc__}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 操作失败")
        sys.exit(1)
