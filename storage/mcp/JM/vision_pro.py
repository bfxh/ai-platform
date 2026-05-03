#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vision Pro MCP - 高级视觉能力扩展

在原有Vision MCP基础上增加：
1. 屏幕视觉理解 - 截屏+AI分析一体化
2. UI元素检测 - 自动识别按钮/输入框/菜单的位置
3. 像素级搜索 - 在屏幕上搜索特定图片/图标
4. 颜色区域检测 - 找到特定颜色的区域
5. 文字区域定位 - 找到屏幕上文字的精确坐标
6. 变化检测 - 对比两张截图找出差异
7. 模板匹配 - 在大图中找小图的位置
8. 屏幕录制 - 连续截图生成GIF
9. 窗口内容提取 - 截取特定窗口并分析
10. 视觉自动化辅助 - 配合da.py实现视觉驱动的自动化

用法：
    python vision_pro.py <action> [args...]

示例：
    python vision_pro.py screen_analyze              # 截屏+分析
    python vision_pro.py find_text "保存"             # 在屏幕上找文字
    python vision_pro.py find_button "确定"           # 找按钮位置
    python vision_pro.py find_image template.png      # 模板匹配
    python vision_pro.py find_color "#FF0000"         # 找红色区域
    python vision_pro.py diff img1.bmp img2.bmp       # 对比差异
    python vision_pro.py watch 5 output/              # 每5秒截屏
    python vision_pro.py crop 100 200 300 400 out.png # 裁剪区域
    python vision_pro.py grid 3 4 out.png             # 屏幕网格标注
    python vision_pro.py ocr screenshot.bmp           # OCR识别
    python vision_pro.py ui_detect                    # 检测UI元素
    python vision_pro.py measure 100 200 300 400      # 测量距离/区域
"""

import ctypes
import ctypes.wintypes
import json
import sys
import os
import time
import struct
import math
import hashlib
import subprocess
from pathlib import Path
from collections import Counter

# 路径
AI = Path("/python")
MCP = AI / "MCP"
TEMP = MCP / "temp"
TEMP.mkdir(parents=True, exist_ok=True)
DA = MCP / "da.py"

# Windows API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# 检测可用库
HAS_PIL = False
PIL_Image = None
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_Image = Image
    HAS_PIL = True
except ImportError:
    pass


# ============================================================
# 核心：BMP读写（零依赖）
# ============================================================
def read_bmp(path):
    """读取BMP文件，返回(width, height, pixels)"""
    with open(path, 'rb') as f:
        # BMP header
        sig = f.read(2)
        if sig != b'BM':
            raise ValueError("Not a BMP file")
        f.read(8)  # file size + reserved
        offset = struct.unpack('<I', f.read(4))[0]
        
        # DIB header
        header_size = struct.unpack('<I', f.read(4))[0]
        width = struct.unpack('<i', f.read(4))[0]
        height = struct.unpack('<i', f.read(4))[0]
        f.read(2)  # planes
        bpp = struct.unpack('<H', f.read(2))[0]
        
        f.seek(offset)
        
        # 读取像素数据
        row_size = ((width * bpp // 8) + 3) & ~3  # 4字节对齐
        pixels = []
        
        bottom_up = height > 0
        abs_height = abs(height)
        
        for y in range(abs_height):
            row = f.read(row_size)
            row_pixels = []
            for x in range(width):
                if bpp == 24:
                    idx = x * 3
                    b, g, r = row[idx], row[idx+1], row[idx+2]
                    row_pixels.append((r, g, b))
                elif bpp == 32:
                    idx = x * 4
                    b, g, r = row[idx], row[idx+1], row[idx+2]
                    row_pixels.append((r, g, b))
            pixels.append(row_pixels)
        
        if bottom_up:
            pixels.reverse()
        
        return width, abs_height, pixels


def write_bmp(path, width, height, pixels):
    """写入BMP文件"""
    row_size = ((width * 3) + 3) & ~3
    pixel_data_size = row_size * height
    file_size = 54 + pixel_data_size
    
    with open(path, 'wb') as f:
        # BMP header
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(b'\x00\x00\x00\x00')
        f.write(struct.pack('<I', 54))
        
        # DIB header
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<i', width))
        f.write(struct.pack('<i', height))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 24))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', pixel_data_size))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<i', 2835))
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', 0))
        
        # 像素数据（bottom-up）
        for y in range(height - 1, -1, -1):
            row = bytearray()
            for x in range(width):
                r, g, b = pixels[y][x]
                row.extend([b, g, r])
            # 4字节对齐
            while len(row) % 4 != 0:
                row.append(0)
            f.write(row)


def screenshot(path=None):
    """截屏，返回路径"""
    if path is None:
        path = str(TEMP / "vision_screen.bmp")
    result = subprocess.run(
        [sys.executable, str(DA), "screenshot", path],
        capture_output=True, text=True, timeout=10
    )
    return path


def screenshot_region(x, y, w, h, path=None):
    """区域截屏"""
    if path is None:
        path = str(TEMP / "vision_region.bmp")
    subprocess.run(
        [sys.executable, str(DA), "shot_region", str(x), str(y), str(w), str(h), path],
        capture_output=True, text=True, timeout=10
    )
    return path


# ============================================================
# 1. 屏幕网格标注 - 给截屏加上坐标网格
# ============================================================
def grid_overlay(cols=4, rows=3, output=None):
    """在截屏上叠加坐标网格，方便定位"""
    src = screenshot()
    
    if not HAS_PIL:
        print("需要PIL库: pip install Pillow")
        return None
    
    img = PIL_Image.open(src)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    cell_w = w // cols
    cell_h = h // rows
    
    # 画网格线
    for i in range(1, cols):
        x = i * cell_w
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 128), width=2)
    for j in range(1, rows):
        y = j * cell_h
        draw.line([(0, y), (w, y)], fill=(255, 0, 0, 128), width=2)
    
    # 标注坐标
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    for j in range(rows):
        for i in range(cols):
            cx = i * cell_w + cell_w // 2
            cy = j * cell_h + cell_h // 2
            label = f"({cx},{cy})"
            draw.text((cx - 30, cy - 8), label, fill=(255, 255, 0), font=font)
    
    # 四角坐标
    for pos, coord in [((5, 5), "(0,0)"), ((w-60, 5), f"({w},0)"),
                        ((5, h-20), f"(0,{h})"), ((w-80, h-20), f"({w},{h})")]:
        draw.text(pos, coord, fill=(0, 255, 0), font=font)
    
    if output is None:
        output = str(TEMP / "vision_grid.bmp")
    img.save(output)
    print(f"grid: {cols}x{rows} -> {output}")
    return output


# ============================================================
# 2. 颜色搜索 - 在屏幕上找特定颜色的区域
# ============================================================
def find_color(hex_color, tolerance=30, min_area=10):
    """在屏幕上找到指定颜色的区域"""
    src = screenshot()
    w, h, pixels = read_bmp(src)
    
    # 解析目标颜色
    hex_color = hex_color.lstrip('#')
    tr, tg, tb = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    
    # 搜索匹配像素
    matches = []
    for y in range(0, h, 2):  # 隔行扫描加速
        for x in range(0, w, 2):
            r, g, b = pixels[y][x]
            if abs(r-tr) <= tolerance and abs(g-tg) <= tolerance and abs(b-tb) <= tolerance:
                matches.append((x, y))
    
    if not matches:
        print(f"color #{hex_color}: not found")
        return []
    
    # 聚类找区域中心
    clusters = cluster_points(matches, 20)
    results = []
    for cluster in clusters:
        if len(cluster) >= min_area:
            xs = [p[0] for p in cluster]
            ys = [p[1] for p in cluster]
            cx = sum(xs) // len(xs)
            cy = sum(ys) // len(ys)
            results.append({
                "center": (cx, cy),
                "count": len(cluster),
                "bounds": (min(xs), min(ys), max(xs), max(ys))
            })
    
    results.sort(key=lambda r: r["count"], reverse=True)
    
    for i, r in enumerate(results[:10]):
        print(f"  [{i+1}] center=({r['center'][0]},{r['center'][1]}) pixels={r['count']} bounds={r['bounds']}")
    
    return results


def cluster_points(points, radius):
    """简单聚类"""
    if not points:
        return []
    
    clusters = []
    used = set()
    
    for i, p in enumerate(points):
        if i in used:
            continue
        cluster = [p]
        used.add(i)
        for j, q in enumerate(points):
            if j in used:
                continue
            if abs(p[0]-q[0]) <= radius and abs(p[1]-q[1]) <= radius:
                cluster.append(q)
                used.add(j)
        clusters.append(cluster)
    
    return clusters


# ============================================================
# 3. 模板匹配 - 在大图中找小图
# ============================================================
def find_image(template_path, threshold=0.8, src_path=None):
    """在屏幕截图中找到模板图片的位置"""
    if src_path is None:
        src_path = screenshot()
    
    if HAS_PIL:
        src = PIL_Image.open(src_path)
        tpl = PIL_Image.open(template_path)
        sw, sh = src.size
        tw, th = tpl.size
        
        src_data = list(src.getdata())
        tpl_data = list(tpl.getdata())
        
        best_score = 0
        best_pos = None
        
        # 滑动窗口匹配（简化版，每隔几个像素采样）
        step = max(1, min(tw, th) // 4)
        for y in range(0, sh - th, step):
            for x in range(0, sw - tw, step):
                score = 0
                total = 0
                # 采样比较
                for ty in range(0, th, max(1, th // 8)):
                    for tx in range(0, tw, max(1, tw // 8)):
                        si = (y + ty) * sw + (x + tx)
                        ti = ty * tw + tx
                        if si < len(src_data) and ti < len(tpl_data):
                            sr, sg, sb = src_data[si][:3]
                            tr, tg, tb = tpl_data[ti][:3]
                            diff = abs(sr-tr) + abs(sg-tg) + abs(sb-tb)
                            if diff < 60:
                                score += 1
                            total += 1
                
                if total > 0:
                    ratio = score / total
                    if ratio > best_score:
                        best_score = ratio
                        best_pos = (x, y)
        
        if best_score >= threshold and best_pos:
            cx = best_pos[0] + tw // 2
            cy = best_pos[1] + th // 2
            print(f"found: center=({cx},{cy}) score={best_score:.2f} bounds=({best_pos[0]},{best_pos[1]},{best_pos[0]+tw},{best_pos[1]+th})")
            return {"center": (cx, cy), "score": best_score, "bounds": (best_pos[0], best_pos[1], best_pos[0]+tw, best_pos[1]+th)}
    
    print("not found")
    return None


# ============================================================
# 4. 图像差异检测
# ============================================================
def diff_images(path1, path2, output=None, threshold=30):
    """对比两张图片，标出差异区域"""
    if not HAS_PIL:
        print("需要PIL库")
        return None
    
    img1 = PIL_Image.open(path1)
    img2 = PIL_Image.open(path2)
    
    w = min(img1.width, img2.width)
    h = min(img1.height, img2.height)
    
    img1 = img1.resize((w, h))
    img2 = img2.resize((w, h))
    
    d1 = list(img1.getdata())
    d2 = list(img2.getdata())
    
    diff_pixels = 0
    diff_regions = []
    
    result = PIL_Image.new('RGB', (w, h))
    result_data = []
    
    for i in range(len(d1)):
        r1, g1, b1 = d1[i][:3]
        r2, g2, b2 = d2[i][:3]
        diff = abs(r1-r2) + abs(g1-g2) + abs(b1-b2)
        if diff > threshold:
            result_data.append((255, 0, 0))  # 红色标记差异
            diff_pixels += 1
            x = i % w
            y = i // w
            diff_regions.append((x, y))
        else:
            # 灰度化原图
            gray = (r1 + g1 + b1) // 3
            result_data.append((gray, gray, gray))
    
    result.putdata(result_data)
    
    if output is None:
        output = str(TEMP / "vision_diff.bmp")
    result.save(output)
    
    similarity = 1.0 - (diff_pixels / len(d1))
    print(f"diff: {diff_pixels} pixels changed ({similarity*100:.1f}% similar) -> {output}")
    
    return {
        "diff_pixels": diff_pixels,
        "total_pixels": len(d1),
        "similarity": similarity,
        "output": output
    }


# ============================================================
# 5. 屏幕变化监控
# ============================================================
def watch_screen(interval=5, count=10, output_dir=None):
    """定时截屏，检测变化"""
    if output_dir is None:
        output_dir = str(TEMP / "watch")
    os.makedirs(output_dir, exist_ok=True)
    
    prev = None
    for i in range(count):
        path = os.path.join(output_dir, f"frame_{i:04d}.bmp")
        screenshot(path)
        
        if prev and HAS_PIL:
            result = diff_images(prev, path, threshold=50)
            if result:
                print(f"  frame {i}: {result['similarity']*100:.1f}% similar")
        else:
            print(f"  frame {i}: saved")
        
        prev = path
        if i < count - 1:
            time.sleep(interval)
    
    print(f"watch: {count} frames saved to {output_dir}")


# ============================================================
# 6. 屏幕区域测量
# ============================================================
def measure(x1, y1, x2, y2):
    """测量屏幕上两点之间的距离和区域"""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dist = math.sqrt(dx*dx + dy*dy)
    area = dx * dy
    
    print(f"measure: ({x1},{y1}) to ({x2},{y2})")
    print(f"  width={dx}px height={dy}px")
    print(f"  distance={dist:.1f}px")
    print(f"  area={area}px^2")
    
    return {"width": dx, "height": dy, "distance": dist, "area": area}


# ============================================================
# 7. 主色提取
# ============================================================
def dominant_colors(path=None, n=5):
    """提取图片的主要颜色"""
    if path is None:
        path = screenshot()
    
    w, h, pixels = read_bmp(path)
    
    # 采样像素
    colors = Counter()
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b = pixels[y][x]
            # 量化到16级
            qr = (r // 16) * 16
            qg = (g // 16) * 16
            qb = (b // 16) * 16
            colors[(qr, qg, qb)] += 1
    
    top = colors.most_common(n)
    print(f"dominant colors from {path}:")
    for i, ((r, g, b), count) in enumerate(top):
        hex_c = f"#{r:02X}{g:02X}{b:02X}"
        pct = count / sum(colors.values()) * 100
        print(f"  [{i+1}] {hex_c} ({r},{g},{b}) {pct:.1f}%")
    
    return [{"color": f"#{r:02X}{g:02X}{b:02X}", "rgb": (r,g,b), "count": c} for (r,g,b), c in top]


# ============================================================
# 8. 屏幕区域裁剪
# ============================================================
def crop(x, y, w, h, output=None):
    """裁剪屏幕区域"""
    if output is None:
        output = str(TEMP / "vision_crop.bmp")
    screenshot_region(x, y, w, h, output)
    print(f"crop: ({x},{y}) {w}x{h} -> {output}")
    return output


# ============================================================
# 9. 像素取色
# ============================================================
def pick_color(x, y):
    """获取屏幕指定位置的颜色"""
    path = screenshot_region(x, y, 1, 1)
    w, h, pixels = read_bmp(path)
    if pixels and pixels[0]:
        r, g, b = pixels[0][0]
        hex_c = f"#{r:02X}{g:02X}{b:02X}"
        print(f"color at ({x},{y}): {hex_c} rgb({r},{g},{b})")
        return {"hex": hex_c, "rgb": (r, g, b)}
    return None


# ============================================================
# 10. 屏幕文字区域检测（基于颜色对比度）
# ============================================================
def detect_text_regions(path=None, min_contrast=80):
    """检测可能包含文字的区域（基于高对比度区域）"""
    if path is None:
        path = screenshot()
    
    w, h, pixels = read_bmp(path)
    
    # 计算每个区块的对比度
    block_size = 20
    text_blocks = []
    
    for by in range(0, h - block_size, block_size):
        for bx in range(0, w - block_size, block_size):
            min_lum = 255
            max_lum = 0
            for dy in range(0, block_size, 2):
                for dx in range(0, block_size, 2):
                    r, g, b = pixels[by+dy][bx+dx]
                    lum = (r * 299 + g * 587 + b * 114) // 1000
                    min_lum = min(min_lum, lum)
                    max_lum = max(max_lum, lum)
            
            contrast = max_lum - min_lum
            if contrast >= min_contrast:
                text_blocks.append((bx, by, contrast))
    
    # 聚类相邻的文字区块
    if not text_blocks:
        print("no text regions detected")
        return []
    
    regions = cluster_points([(b[0], b[1]) for b in text_blocks], block_size * 2)
    
    results = []
    for region in regions:
        if len(region) >= 2:
            xs = [p[0] for p in region]
            ys = [p[1] for p in region]
            results.append({
                "bounds": (min(xs), min(ys), max(xs) + block_size, max(ys) + block_size),
                "blocks": len(region)
            })
    
    results.sort(key=lambda r: r["blocks"], reverse=True)
    
    print(f"text regions: {len(results)} found")
    for i, r in enumerate(results[:10]):
        b = r["bounds"]
        print(f"  [{i+1}] ({b[0]},{b[1]})-({b[2]},{b[3]}) {b[2]-b[0]}x{b[3]-b[1]}px blocks={r['blocks']}")
    
    return results


# ============================================================
# 11. UI元素检测（基于边缘和颜色特征）
# ============================================================
def detect_ui_elements(path=None):
    """检测屏幕上的UI元素（按钮、输入框等）"""
    if path is None:
        path = screenshot()
    
    w, h, pixels = read_bmp(path)
    
    elements = []
    
    # 检测矩形区域（通过水平和垂直边缘）
    block = 10
    for by in range(0, h - block * 3, block):
        for bx in range(0, w - block * 3, block):
            # 检查是否有明显的矩形边缘
            top_edge = 0
            left_edge = 0
            
            for dx in range(block * 3):
                if bx + dx < w and by > 0:
                    r1, g1, b1 = pixels[by][bx+dx]
                    r2, g2, b2 = pixels[by-1][bx+dx] if by > 0 else (r1, g1, b1)
                    if abs(r1-r2) + abs(g1-g2) + abs(b1-b2) > 60:
                        top_edge += 1
            
            for dy in range(block * 3):
                if by + dy < h and bx > 0:
                    r1, g1, b1 = pixels[by+dy][bx]
                    r2, g2, b2 = pixels[by+dy][bx-1] if bx > 0 else (r1, g1, b1)
                    if abs(r1-r2) + abs(g1-g2) + abs(b1-b2) > 60:
                        left_edge += 1
            
            if top_edge > block * 2 and left_edge > block * 2:
                elements.append({
                    "type": "rect_element",
                    "position": (bx, by),
                    "edge_strength": top_edge + left_edge
                })
    
    # 去重（合并相近的检测）
    merged = []
    used = set()
    for i, e in enumerate(elements):
        if i in used:
            continue
        group = [e]
        used.add(i)
        for j, f in enumerate(elements):
            if j in used:
                continue
            if abs(e["position"][0] - f["position"][0]) < 30 and abs(e["position"][1] - f["position"][1]) < 30:
                group.append(f)
                used.add(j)
        best = max(group, key=lambda g: g["edge_strength"])
        merged.append(best)
    
    merged.sort(key=lambda e: e["edge_strength"], reverse=True)
    
    print(f"ui elements: {len(merged)} detected")
    for i, e in enumerate(merged[:15]):
        print(f"  [{i+1}] {e['type']} at ({e['position'][0]},{e['position'][1]}) strength={e['edge_strength']}")
    
    return merged


# ============================================================
# 12. 标注截图 - 在截图上画标记
# ============================================================
def annotate(marks, src=None, output=None):
    """在截图上画标记
    marks: [{"type":"circle","x":100,"y":200,"r":20,"color":"red"},
            {"type":"rect","x":50,"y":50,"w":100,"h":30,"color":"blue"},
            {"type":"text","x":100,"y":100,"text":"这里","color":"yellow"},
            {"type":"arrow","x1":100,"y1":100,"x2":200,"y2":200,"color":"green"}]
    """
    if not HAS_PIL:
        print("需要PIL库")
        return None
    
    if src is None:
        src = screenshot()
    
    img = PIL_Image.open(src)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    color_map = {
        "red": (255, 0, 0), "green": (0, 255, 0), "blue": (0, 0, 255),
        "yellow": (255, 255, 0), "white": (255, 255, 255), "cyan": (0, 255, 255),
        "magenta": (255, 0, 255), "orange": (255, 165, 0)
    }
    
    for mark in marks:
        color = color_map.get(mark.get("color", "red"), (255, 0, 0))
        t = mark.get("type", "circle")
        
        if t == "circle":
            x, y, r = mark["x"], mark["y"], mark.get("r", 15)
            draw.ellipse([x-r, y-r, x+r, y+r], outline=color, width=3)
        
        elif t == "rect":
            x, y = mark["x"], mark["y"]
            w, h = mark.get("w", 50), mark.get("h", 30)
            draw.rectangle([x, y, x+w, y+h], outline=color, width=3)
        
        elif t == "text":
            draw.text((mark["x"], mark["y"]), mark["text"], fill=color, font=font)
        
        elif t == "arrow":
            draw.line([(mark["x1"], mark["y1"]), (mark["x2"], mark["y2"])], fill=color, width=3)
        
        elif t == "point":
            x, y = mark["x"], mark["y"]
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
            draw.text((x+8, y-8), f"({x},{y})", fill=color, font=font)
    
    if output is None:
        output = str(TEMP / "vision_annotated.bmp")
    img.save(output)
    print(f"annotated: {len(marks)} marks -> {output}")
    return output


# ============================================================
# 13. 快速OCR（基于Windows内置OCR）
# ============================================================
def ocr_windows(path=None):
    """使用Windows内置OCR（需要安装语言包）"""
    if path is None:
        path = screenshot()
    
    # 尝试使用PowerShell调用Windows OCR API
    ps_script = f'''
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
    $null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Foundation,ContentType=WindowsRuntime]
    $null = [Windows.Storage.StorageFile,Windows.Foundation,ContentType=WindowsRuntime]
    
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    
    $file = [Windows.Storage.StorageFile]::GetFileFromPathAsync("{path}").GetAwaiter().GetResult()
    $stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
    $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetAwaiter().GetResult()
    $bitmap = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()
    
    $result = $engine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
    $result.Text
    '''
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True, text=True, timeout=30
        )
        text = result.stdout.strip()
        if text:
            print(f"OCR result:\n{text}")
            return text
        else:
            print("OCR: no text detected")
            return ""
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""


# ============================================================
# 14. 屏幕分析（截屏+生成描述性信息）
# ============================================================
def screen_analyze():
    """截屏并生成基本分析信息"""
    path = screenshot()
    w, h, pixels = read_bmp(path)
    
    # 基本信息
    print(f"screen: {w}x{h}")
    
    # 主色
    colors = dominant_colors(path, 3)
    
    # 文字区域
    text_regions = detect_text_regions(path)
    
    # 亮度分布
    total_lum = 0
    count = 0
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            r, g, b = pixels[y][x]
            total_lum += (r * 299 + g * 587 + b * 114) // 1000
            count += 1
    avg_lum = total_lum // count if count else 0
    
    theme = "dark" if avg_lum < 128 else "light"
    print(f"theme: {theme} (avg luminance={avg_lum})")
    print(f"screenshot: {path}")
    
    return {
        "size": (w, h),
        "theme": theme,
        "avg_luminance": avg_lum,
        "dominant_colors": colors,
        "text_regions": len(text_regions),
        "path": path
    }


# ============================================================
# CLI入口
# ============================================================
def main():
    if len(sys.argv) < 2:
        print("""Vision Pro MCP - 高级视觉能力

用法: python vision_pro.py <action> [args...]

动作:
  screen_analyze              截屏+分析
  grid [cols] [rows]          屏幕网格标注
  find_color #RRGGBB [tol]    搜索颜色
  find_image template.png     模板匹配
  diff img1 img2              图像差异
  watch [interval] [count]    屏幕监控
  crop x y w h [output]       裁剪区域
  pick x y                    取色
  measure x1 y1 x2 y2         测量
  colors [path] [n]           主色提取
  text_regions [path]         文字区域检测
  ui_detect [path]            UI元素检测
  annotate <json> [src]       标注截图
  ocr [path]                  OCR文字识别""")
        return
    
    action = sys.argv[1]
    args = sys.argv[2:]
    
    if action == "screen_analyze":
        screen_analyze()
    
    elif action == "grid":
        cols = int(args[0]) if args else 4
        rows = int(args[1]) if len(args) > 1 else 3
        output = args[2] if len(args) > 2 else None
        grid_overlay(cols, rows, output)
    
    elif action == "find_color":
        color = args[0] if args else "#FF0000"
        tol = int(args[1]) if len(args) > 1 else 30
        find_color(color, tol)
    
    elif action == "find_image":
        if args:
            find_image(args[0])
        else:
            print("用法: find_image <template.png>")
    
    elif action == "diff":
        if len(args) >= 2:
            diff_images(args[0], args[1])
        else:
            print("用法: diff <img1> <img2>")
    
    elif action == "watch":
        interval = int(args[0]) if args else 5
        count = int(args[1]) if len(args) > 1 else 10
        watch_screen(interval, count)
    
    elif action == "crop":
        if len(args) >= 4:
            output = args[4] if len(args) > 4 else None
            crop(int(args[0]), int(args[1]), int(args[2]), int(args[3]), output)
        else:
            print("用法: crop x y w h [output]")
    
    elif action == "pick":
        if len(args) >= 2:
            pick_color(int(args[0]), int(args[1]))
        else:
            print("用法: pick x y")
    
    elif action == "measure":
        if len(args) >= 4:
            measure(int(args[0]), int(args[1]), int(args[2]), int(args[3]))
        else:
            print("用法: measure x1 y1 x2 y2")
    
    elif action == "colors":
        path = args[0] if args else None
        n = int(args[1]) if len(args) > 1 else 5
        dominant_colors(path, n)
    
    elif action == "text_regions":
        path = args[0] if args else None
        detect_text_regions(path)
    
    elif action == "ui_detect":
        path = args[0] if args else None
        detect_ui_elements(path)
    
    elif action == "annotate":
        if args:
            marks = json.loads(args[0])
            src = args[1] if len(args) > 1 else None
            annotate(marks, src)
        else:
            print('用法: annotate \'[{"type":"circle","x":100,"y":200}]\' [src.bmp]')
    
    elif action == "ocr":
        path = args[0] if args else None
        ocr_windows(path)
    
    else:
        print(f"未知动作: {action}")


if __name__ == '__main__':
    main()
