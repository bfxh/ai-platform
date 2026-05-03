#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screen Eye MCP - 后台屏幕监视器

不切换窗口、不抢焦点，后台静默截取任意窗口内容。

原理：
- PrintWindow API：后台截取窗口，不需要窗口在前台
- BitBlt + DC：直接从窗口DC复制像素
- 窗口枚举：实时获取所有窗口信息

功能：
1. 后台截取任意窗口（不切换焦点）
2. 实时窗口列表监控
3. 窗口内容变化检测
4. 后台窗口像素取色
5. 后台窗口文字区域检测
6. 多窗口同时监控
7. 窗口缩略图生成
8. 窗口布局快照

用法：
    python screen_eye.py <action> [args...]

示例：
    python screen_eye.py capture "FModel"           # 后台截取FModel窗口
    python screen_eye.py capture_all                 # 截取所有可见窗口
    python screen_eye.py list                        # 列出所有窗口
    python screen_eye.py watch "FModel" 3            # 每3秒后台截取FModel
    python screen_eye.py diff "FModel"               # 检测FModel窗口变化
    python screen_eye.py thumb                       # 所有窗口缩略图
    python screen_eye.py layout                      # 窗口布局快照
    python screen_eye.py pick "FModel" 100 200       # 后台取色
    python screen_eye.py info "FModel"               # 窗口详细信息
    python screen_eye.py tree "FModel"               # 窗口控件树
    python screen_eye.py monitor "FModel" "Chrome"   # 同时监控多个窗口
    python screen_eye.py screen                      # 后台全屏截图（不闪）
"""

import ctypes
import ctypes.wintypes
import struct
import sys
import os
import time
import json
import math
from pathlib import Path
from collections import Counter
from datetime import datetime

# 路径
TEMP = Path("/python/MCP/temp/eye")
TEMP.mkdir(parents=True, exist_ok=True)

# ============================================================
# Windows API 定义
# ============================================================
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
dwmapi = ctypes.windll.dwmapi

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
PW_CLIENTONLY = 1
PW_RENDERFULLCONTENT = 2
DWMWA_EXTENDED_FRAME_BOUNDS = 9
GW_CHILD = 5
GW_HWNDNEXT = 2
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_EX_TOOLWINDOW = 0x00000080

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', ctypes.c_uint32),
        ('biWidth', ctypes.c_int32),
        ('biHeight', ctypes.c_int32),
        ('biPlanes', ctypes.c_uint16),
        ('biBitCount', ctypes.c_uint16),
        ('biCompression', ctypes.c_uint32),
        ('biSizeImage', ctypes.c_uint32),
        ('biXPelsPerMeter', ctypes.c_int32),
        ('biYPelsPerMeter', ctypes.c_int32),
        ('biClrUsed', ctypes.c_uint32),
        ('biClrImportant', ctypes.c_uint32),
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', ctypes.c_uint32 * 3),
    ]


# ============================================================
# 窗口查找
# ============================================================
def enum_windows():
    """枚举所有可见窗口"""
    windows = []
    
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        
        if not title.strip():
            return True
        
        # 获取窗口位置和大小
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        
        # 过滤掉不可见的窗口
        if w <= 0 or h <= 0:
            return True
        if rect.left < -10000:
            return True
        
        # 获取类名
        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        
        # 获取PID
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        windows.append({
            'hwnd': hwnd,
            'title': title,
            'class': class_buf.value,
            'pid': pid.value,
            'rect': (rect.left, rect.top, rect.right, rect.bottom),
            'size': (w, h),
            'pos': (rect.left, rect.top),
        })
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return windows


def find_window(title_part):
    """按标题模糊查找窗口"""
    windows = enum_windows()
    matches = [w for w in windows if title_part.lower() in w['title'].lower()]
    return matches


# ============================================================
# 核心：后台窗口截图（不切换焦点）
# ============================================================
def capture_window(hwnd, output=None):
    """后台截取窗口内容，不切换焦点不闪屏"""
    
    # 获取窗口大小
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    
    if w <= 0 or h <= 0:
        return None
    
    # 创建兼容DC和位图
    hwnd_dc = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    old_bitmap = gdi32.SelectObject(mem_dc, bitmap)
    
    # 方法1：PrintWindow（最可靠的后台截图方式）
    result = user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
    
    if not result:
        # 方法2：BitBlt（备选）
        gdi32.BitBlt(mem_dc, 0, 0, w, h, hwnd_dc, 0, 0, SRCCOPY)
    
    # 读取像素数据
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    
    buf_size = w * h * 4
    buf = ctypes.create_string_buffer(buf_size)
    
    gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(bmi), DIB_RGB_COLORS)
    
    # 清理
    gdi32.SelectObject(mem_dc, old_bitmap)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    
    # 保存为BMP
    if output is None:
        output = str(TEMP / f"eye_{hwnd}.bmp")
    
    save_bmp(output, w, h, buf.raw)
    return output


def save_bmp(path, width, height, pixel_data_bgra):
    """保存BGRA像素数据为BMP文件"""
    # 转换为24位BGR
    row_size = ((width * 3) + 3) & ~3
    pixel_size = row_size * height
    file_size = 54 + pixel_size
    
    with open(path, 'wb') as f:
        # BMP header
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(b'\x00\x00\x00\x00')
        f.write(struct.pack('<I', 54))
        
        # DIB header
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<i', width))
        f.write(struct.pack('<i', -height))  # top-down
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 24))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', pixel_size))
        f.write(struct.pack('<i', 0))
        f.write(struct.pack('<i', 0))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', 0))
        
        # 像素数据：BGRA -> BGR + padding
        for y in range(height):
            row = bytearray()
            for x in range(width):
                idx = (y * width + x) * 4
                b = pixel_data_bgra[idx]
                g = pixel_data_bgra[idx + 1]
                r = pixel_data_bgra[idx + 2]
                row.extend([b, g, r])
            while len(row) % 4 != 0:
                row.append(0)
            f.write(row)


def capture_screen_silent(output=None):
    """后台全屏截图（不闪屏）"""
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    
    screen_dc = user32.GetDC(0)
    mem_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, w, h)
    old = gdi32.SelectObject(mem_dc, bitmap)
    
    gdi32.BitBlt(mem_dc, 0, 0, w, h, screen_dc, 0, 0, SRCCOPY)
    
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(bmi), DIB_RGB_COLORS)
    
    gdi32.SelectObject(mem_dc, old)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(0, screen_dc)
    
    if output is None:
        output = str(TEMP / "eye_screen.bmp")
    save_bmp(output, w, h, buf.raw)
    return output


# ============================================================
# 高级功能
# ============================================================

def capture_by_title(title, output=None):
    """按标题后台截取窗口"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return None
    
    win = matches[0]
    if output is None:
        safe_name = "".join(c if c.isalnum() else "_" for c in title[:20])
        output = str(TEMP / f"eye_{safe_name}.bmp")
    
    result = capture_window(win['hwnd'], output)
    if result:
        print(f"captured: {win['title'][:50]} ({win['size'][0]}x{win['size'][1]}) -> {result}")
    return result


def capture_all_windows(output_dir=None):
    """截取所有可见窗口"""
    if output_dir is None:
        output_dir = str(TEMP / "all")
    os.makedirs(output_dir, exist_ok=True)
    
    windows = enum_windows()
    captured = 0
    
    for win in windows:
        if win['size'][0] < 50 or win['size'][1] < 50:
            continue
        
        safe = "".join(c if c.isalnum() else "_" for c in win['title'][:30])
        path = os.path.join(output_dir, f"{safe}.bmp")
        
        try:
            result = capture_window(win['hwnd'], path)
            if result:
                captured += 1
                print(f"  [{captured}] {win['title'][:40]} -> {path}")
        except:
            pass
    
    print(f"\ncaptured {captured} windows to {output_dir}")


def watch_window(title, interval=3, count=10):
    """定时后台截取窗口"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return
    
    win = matches[0]
    watch_dir = str(TEMP / "watch")
    os.makedirs(watch_dir, exist_ok=True)
    
    print(f"watching: {win['title'][:50]} every {interval}s x{count}")
    
    for i in range(count):
        path = os.path.join(watch_dir, f"frame_{i:04d}.bmp")
        capture_window(win['hwnd'], path)
        print(f"  frame {i}: {path}")
        if i < count - 1:
            time.sleep(interval)
    
    print(f"done: {count} frames in {watch_dir}")


def diff_window(title):
    """检测窗口内容变化（截两次对比）"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return
    
    win = matches[0]
    
    path1 = str(TEMP / "diff_a.bmp")
    capture_window(win['hwnd'], path1)
    print("captured frame 1, waiting 2s...")
    time.sleep(2)
    
    path2 = str(TEMP / "diff_b.bmp")
    capture_window(win['hwnd'], path2)
    print("captured frame 2")
    
    # 简单像素对比
    with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
        d1 = f1.read()
        d2 = f2.read()
    
    if len(d1) != len(d2):
        print("size changed!")
        return
    
    diff = sum(1 for a, b in zip(d1[54:], d2[54:]) if abs(a - b) > 10)
    total = len(d1) - 54
    similarity = 1.0 - (diff / total) if total > 0 else 1.0
    
    print(f"diff: {diff} bytes changed, {similarity*100:.1f}% similar")
    if similarity < 0.99:
        print("  -> window content CHANGED")
    else:
        print("  -> window content stable")


def window_info(title):
    """获取窗口详细信息"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return
    
    win = matches[0]
    hwnd = win['hwnd']
    
    # 获取DWM实际边界
    dwm_rect = ctypes.wintypes.RECT()
    dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(dwm_rect), ctypes.sizeof(dwm_rect))
    
    # 获取样式
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    
    # 是否最小化/最大化
    is_minimized = bool(user32.IsIconic(hwnd))
    is_maximized = bool(user32.IsZoomed(hwnd))
    is_focused = (user32.GetForegroundWindow() == hwnd)
    
    info = {
        "title": win['title'],
        "class": win['class'],
        "hwnd": hwnd,
        "pid": win['pid'],
        "rect": win['rect'],
        "size": win['size'],
        "dwm_rect": (dwm_rect.left, dwm_rect.top, dwm_rect.right, dwm_rect.bottom),
        "minimized": is_minimized,
        "maximized": is_maximized,
        "focused": is_focused,
        "style": hex(style),
        "ex_style": hex(ex_style),
    }
    
    print(json.dumps(info, indent=2, ensure_ascii=False, default=str))
    return info


def window_tree(title, max_depth=3):
    """获取窗口的子控件树"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return
    
    hwnd = matches[0]['hwnd']
    
    def enum_children(parent, depth=0):
        if depth >= max_depth:
            return
        
        child = user32.GetWindow(parent, GW_CHILD)
        while child:
            # 获取控件信息
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(child, class_buf, 256)
            
            text_len = user32.GetWindowTextLengthW(child)
            text = ""
            if text_len > 0:
                text_buf = ctypes.create_unicode_buffer(text_len + 1)
                user32.GetWindowTextW(child, text_buf, text_len + 1)
                text = text_buf.value[:50]
            
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(child, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            
            visible = bool(user32.IsWindowVisible(child))
            
            indent = "  " * depth
            vis = "V" if visible else "H"
            print(f"{indent}[{vis}] {class_buf.value} \"{text}\" ({w}x{h} at {rect.left},{rect.top})")
            
            enum_children(child, depth + 1)
            child = user32.GetWindow(child, GW_HWNDNEXT)
    
    print(f"Control tree for: {matches[0]['title'][:50]}")
    print(f"{'='*60}")
    enum_children(hwnd)


def pick_color_bg(title, x, y):
    """后台取色（不切换窗口）"""
    matches = find_window(title)
    if not matches:
        print(f"not found: {title}")
        return None
    
    hwnd = matches[0]['hwnd']
    
    # 后台截取窗口
    path = capture_window(hwnd)
    if not path:
        return None
    
    # 读取像素
    with open(path, 'rb') as f:
        f.seek(18)
        w = struct.unpack('<i', f.read(4))[0]
        h = abs(struct.unpack('<i', f.read(4))[0])
        f.seek(28)
        bpp = struct.unpack('<H', f.read(2))[0]
        f.seek(54)
        
        row_size = ((w * 3) + 3) & ~3
        
        if 0 <= x < w and 0 <= y < h:
            f.seek(54 + y * row_size + x * 3)
            b, g, r = struct.unpack('BBB', f.read(3))
            hex_c = f"#{r:02X}{g:02X}{b:02X}"
            print(f"color at ({x},{y}) in '{title}': {hex_c} rgb({r},{g},{b})")
            return {"hex": hex_c, "rgb": (r, g, b)}
    
    return None


def monitor_windows(*titles, interval=3, count=5):
    """同时监控多个窗口"""
    mon_dir = str(TEMP / "monitor")
    os.makedirs(mon_dir, exist_ok=True)
    
    all_wins = {}
    for title in titles:
        matches = find_window(title)
        if matches:
            all_wins[title] = matches[0]
            print(f"monitoring: {matches[0]['title'][:40]}")
        else:
            print(f"not found: {title}")
    
    if not all_wins:
        return
    
    for i in range(count):
        ts = datetime.now().strftime("%H%M%S")
        for title, win in all_wins.items():
            safe = "".join(c if c.isalnum() else "_" for c in title[:15])
            path = os.path.join(mon_dir, f"{safe}_{ts}.bmp")
            try:
                capture_window(win['hwnd'], path)
                print(f"  [{ts}] {title[:20]} -> {path}")
            except:
                pass
        
        if i < count - 1:
            time.sleep(interval)
    
    print(f"\nmonitored {len(all_wins)} windows, {count} rounds -> {mon_dir}")


def layout_snapshot(output=None):
    """窗口布局快照"""
    windows = enum_windows()
    
    if output is None:
        output = str(TEMP / "layout.json")
    
    layout = {
        "timestamp": datetime.now().isoformat(),
        "screen": {
            "width": user32.GetSystemMetrics(0),
            "height": user32.GetSystemMetrics(1)
        },
        "windows": []
    }
    
    for win in windows:
        if win['size'][0] < 50 or win['size'][1] < 50:
            continue
        layout["windows"].append({
            "title": win['title'][:60],
            "class": win['class'],
            "pos": win['pos'],
            "size": win['size'],
            "pid": win['pid']
        })
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)
    
    print(f"layout: {len(layout['windows'])} windows -> {output}")
    for w in layout['windows']:
        print(f"  {w['title'][:40]:40s} {w['size'][0]:4d}x{w['size'][1]:<4d} at ({w['pos'][0]},{w['pos'][1]})")
    
    return layout


# ============================================================
# CLI
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""Screen Eye MCP - 后台屏幕监视器（不切换窗口）

用法: python screen_eye.py <action> [args...]

动作:
  list                          列出所有窗口
  capture <title>               后台截取窗口
  capture_all                   截取所有窗口
  screen                        后台全屏截图
  watch <title> [interval] [n]  定时后台截取
  diff <title>                  检测窗口变化
  info <title>                  窗口详细信息
  tree <title>                  窗口控件树
  pick <title> <x> <y>          后台取色
  monitor <t1> <t2> ...         同时监控多窗口
  layout                        窗口布局快照""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "list":
        windows = enum_windows()
        print(f"{len(windows)} windows:")
        for w in windows:
            print(f"  [{w['pid']:5d}] {w['title'][:50]:50s} {w['size'][0]:4d}x{w['size'][1]:<4d} at ({w['pos'][0]},{w['pos'][1]})")
    
    elif action == "capture":
        if args:
            capture_by_title(args[0], args[1] if len(args) > 1 else None)
        else:
            print("用法: capture <窗口标题>")
    
    elif action == "capture_all":
        capture_all_windows()
    
    elif action == "screen":
        path = capture_screen_silent(args[0] if args else None)
        print(f"screen: {path}")
    
    elif action == "watch":
        if args:
            interval = int(args[1]) if len(args) > 1 else 3
            count = int(args[2]) if len(args) > 2 else 10
            watch_window(args[0], interval, count)
        else:
            print("用法: watch <窗口标题> [间隔秒] [次数]")
    
    elif action == "diff":
        if args:
            diff_window(args[0])
        else:
            print("用法: diff <窗口标题>")
    
    elif action == "info":
        if args:
            window_info(args[0])
        else:
            print("用法: info <窗口标题>")
    
    elif action == "tree":
        if args:
            window_tree(args[0])
        else:
            print("用法: tree <窗口标题>")
    
    elif action == "pick":
        if len(args) >= 3:
            pick_color_bg(args[0], int(args[1]), int(args[2]))
        else:
            print("用法: pick <窗口标题> <x> <y>")
    
    elif action == "monitor":
        if args:
            monitor_windows(*args)
        else:
            print("用法: monitor <标题1> <标题2> ...")
    
    elif action == "layout":
        layout_snapshot()
    
    else:
        print(f"未知动作: {action}")


if __name__ == '__main__':
    main()
