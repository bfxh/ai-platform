# -*- coding: utf-8 -*-
"""
审美检查器 (Aesthetic Checker)
小龙虾审美标准 v1.0

功能：
- 检查颜色组合是否和谐（禁止棕色木棒+绿色圆圈=树）
- 检查字体搭配
- 检查图标比例
- 生成审美评分报告

集成到：
- IronClaw Observer（AI生成结果自动审查）
- Skill Reviewer（Skill界面质量评估）
- 图像生成（生成前检查）
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import re

# ─── 配色规则 ─────────────────────────────────────────

# 禁止组合（禁止原因）
FORBIDDEN_COMBINATIONS = [
    ("#8B4513", "#228B22", "棕色(#8B4513)+森林绿(#228B22)单独使用不等于自然物体"),
    ("brown", "green", "棕色+绿色=木头的联想，不等于树"),
    ("#8B4513", "#00FF00", "棕色+纯绿=卡通树，审美廉价"),
]

# 允许的配色方案
COLOR_PALETTES = {
    "tech_blue": {
        "name": "科技蓝",
        "primary": "#667eea",
        "secondary": "#764ba2",
        "accent": "#00d4ff",
        "bg": "#0a0e1a",
        "text": "#e2e8f0",
    },
    "nature_green": {
        "name": "自然绿",
        "primary": "#10b981",
        "secondary": "#34d399",
        "accent": "#fbbf24",
        "bg": "#f0fdf4",
        "text": "#1f2937",
    },
    "warm_orange": {
        "name": "暖橙",
        "primary": "#f97316",
        "secondary": "#fb923c",
        "accent": "#fde68a",
        "bg": "#fff7ed",
        "text": "#431407",
    },
    "luxury_gold": {
        "name": "轻奢金",
        "primary": "#d4af37",
        "secondary": "#f5e6c8",
        "accent": "#8b6914",
        "bg": "#1c1917",
        "text": "#fafaf9",
    },
}

# 字体搭配规则
FONT_RULES = {
    "chinese": {
        "title": ["AlimamaShuHeiTi-Bold", "DouyinSansBold", "NotoSansSC-Bold"],
        "body": ["DouyinSansBold", "NotoSansSC", "SourceHanSansCN"],
        "mono": ["JetBrainsMono", "CascadiaCode", "Consolas"],
    },
    "english": {
        "title": ["Montserrat-Bold", "Inter", "Poppins"],
        "body": ["Inter", "NotoSans", "Roboto"],
        "mono": ["JetBrainsMono", "FiraCode"],
    },
}

# 图标规则
ICON_RULES = {
    "min_size_px": 24,
    "max_size_px": 64,
    "preferred_stroke_width": 1.5,
    "forbidden_formats": ["emoji", "pixel_art_above_32px"],
}

# 动画规则
ANIMATION_RULES = {
    "min_duration_ms": 150,
    "max_duration_ms": 800,
    "preferred_easing": [
        "cubic-bezier(0.16, 1, 0.3, 1)",  # 优质缓出
        "cubic-bezier(0.4, 0, 0.2, 1)",    # Material标准
        "spring(damping: 15, stiffness: 150)", # 弹性
    ],
    "forbidden_easing": ["linear", "ease-in-out"],
}


@dataclass
class AestheticIssue:
    severity: str          # error / warn / info
    category: str           # color / font / icon / animation / layout
    message: str
    suggestion: str
    location: Optional[str] = None


@dataclass
class AestheticReport:
    score: float            # 0-100
    grade: str              # S/A/B/C/D
    issues: List[AestheticIssue] = field(default_factory=list)
    palette: Optional[Dict] = None
    passed_rules: List[str] = field(default_factory=list)


def normalize_color(color: str) -> str:
    """将颜色标准化为小写hex"""
    color = color.strip().lower()
    # 颜色名称映射
    name_map = {
        "brown": "#8B4513",
        "red": "#FF0000",
        "green": "#228B22",
        "blue": "#0000FF",
        "white": "#FFFFFF",
        "black": "#000000",
    }
    if color in name_map:
        return name_map[color]
    # hex规范化
    if color.startswith("#"):
        if len(color) == 4:
            return "#" + "".join(c*2 for c in color[1:])
        return color[:7]
    return color


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = normalize_color(hex_color)
    if h.startswith("#") and len(h) == 7:
        return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
    return (0, 0, 0)


def color_distance(c1: str, c2: str) -> float:
    """计算两个颜色的欧几里得距离"""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5


def check_color_combination(colors: List[str]) -> List[AestheticIssue]:
    """检查颜色组合是否合规"""
    issues = []
    norms = [normalize_color(c) for c in colors]

    # 检查禁止组合
    for combo in FORBIDDEN_COMBINATIONS:
        c1_raw, c2_raw, reason = combo
        c1 = normalize_color(c1_raw)
        c2 = normalize_color(c2_raw)
        for n1, r1 in zip(norms, colors):
            for n2, r2 in zip(norms, colors):
                if n1 == c1 and n2 == c2:
                    issues.append(AestheticIssue(
                        severity="error",
                        category="color",
                        message=f"发现禁止的颜色组合: {r1} + {r2}",
                        suggestion=f"{reason}。建议使用 COLOR_PALETTES 中的配色方案",
                        location="整体配色",
                    ))

    # 检查对比度（正文vs背景）
    if len(norms) >= 2:
        bg = norms[0] if norms else "#FFFFFF"
        fg = norms[1] if len(norms) > 1 else "#000000"
        dist = color_distance(bg, fg)
        if dist < 100:
            issues.append(AestheticIssue(
                severity="warn",
                category="color",
                message=f"前景色与背景色对比度不足（距离={dist:.0f}，建议>100）",
                suggestion="增加对比度以保证可读性",
            ))

    # 推荐配色检测
    for palette_name, palette in COLOR_PALETTES.items():
        palette_colors = [palette["primary"], palette["secondary"], palette["accent"]]
        match_count = sum(1 for n in norms if any(color_distance(n, pc) < 30 for pc in palette_colors))
        if match_count >= 2:
            return []  # 命中配色方案，无问题

    return issues


def check_fonts(font_list: List[str]) -> List[AestheticIssue]:
    """检查字体搭配"""
    issues = []
    if len(font_list) > 3:
        issues.append(AestheticIssue(
            severity="warn",
            category="font",
            message=f"字体种类过多（{len(font_list)}种），影响视觉统一",
            suggestion="最多使用2-3种字体（标题/正文/代码）",
        ))

    # 检查中英混排
    has_cn = any(re.search(r'[\u4e00-\u9fff]', f) for f in font_list)
    has_en = any(re.search(r'[a-zA-Z]', f) for f in font_list)
    if has_cn and has_en:
        # 中英混排必须有明确分工
        title_fonts = [f for f in font_list if "Bold" in f or "HeiTi" in f or "Title" in f]
        if not title_fonts:
            issues.append(AestheticIssue(
                severity="info",
                category="font",
                message="中英混排建议使用Bold/HeiTi作为标题字体",
                suggestion="标题: AlimamaShuHeiTi-Bold / Montserrat-Bold | 正文: DouyinSansBold / Inter",
            ))

    return issues


def check_icons(icon_list: List[Dict]) -> List[AestheticIssue]:
    """检查图标规范"""
    issues = []
    for icon in icon_list:
        size = icon.get("size", 24)
        fmt = icon.get("format", "").lower()
        stroke = icon.get("stroke_width", 1.5)

        if size < ICON_RULES["min_size_px"]:
            issues.append(AestheticIssue(
                severity="error",
                category="icon",
                message=f"图标过小（{size}px < {ICON_RULES['min_size_px']}px）",
                suggestion=f"最小使用{ICON_RULES['min_size_px']}px图标",
                location=icon.get("name", ""),
            ))
        if size > ICON_RULES["max_size_px"]:
            issues.append(AestheticIssue(
                severity="warn",
                category="icon",
                message=f"图标过大（{size}px > {ICON_RULES['max_size_px']}px）",
                suggestion=f"最大使用{ICON_RULES['max_size_px']}px图标",
                location=icon.get("name", ""),
            ))
        if fmt == "emoji":
            issues.append(AestheticIssue(
                severity="error",
                category="icon",
                message="禁止使用emoji作为UI图标",
                suggestion="使用Lucide Icons或Font Awesome等SVG图标库",
                location=icon.get("name", ""),
            ))
        if abs(stroke - ICON_RULES["preferred_stroke_width"]) > 1:
            issues.append(AestheticIssue(
                severity="warn",
                category="icon",
                message=f"图标线宽不标准（{stroke}px，建议{ICON_RULES['preferred_stroke_width']}px）",
                suggestion="统一图标线宽以保证视觉一致性",
                location=icon.get("name", ""),
            ))

    return issues


def check_animation(animation_list: List[Dict]) -> List[AestheticIssue]:
    """检查动画规范"""
    issues = []
    for anim in animation_list:
        duration_ms = anim.get("duration_ms", 300)
        easing = anim.get("easing", "ease")

        if duration_ms < ANIMATION_RULES["min_duration_ms"]:
            issues.append(AestheticIssue(
                severity="warn",
                category="animation",
                message=f"动画过短（{duration_ms}ms < 150ms），用户无法感知",
                suggestion="动画至少持续150ms",
            ))
        if duration_ms > ANIMATION_RULES["max_duration_ms"]:
            issues.append(AestheticIssue(
                severity="warn",
                category="animation",
                message=f"动画过长（{duration_ms}ms > 800ms），造成延迟感",
                suggestion="复杂动画最多持续800ms",
            ))
        if easing in ANIMATION_RULES["forbidden_easing"]:
            issues.append(AestheticIssue(
                severity="warn",
                category="animation",
                message=f"禁止使用缓动曲线: {easing}",
                suggestion=f"推荐: {ANIMATION_RULES['preferred_easing'][0]}",
            ))

    return issues


def grade_from_score(score: float) -> str:
    if score >= 95: return "S"
    if score >= 85: return "A"
    if score >= 70: return "B"
    if score >= 50: return "C"
    return "D"


def full_aesthetic_check(
    colors: Optional[List[str]] = None,
    fonts: Optional[List[str]] = None,
    icons: Optional[List[Dict]] = None,
    animations: Optional[List[Dict]] = None,
    style: str = "default",  # tech_blue / nature_green / luxury_gold
) -> AestheticReport:
    """
    完整审美审查
    colors: 颜色列表（hex或名称）
    fonts: 字体列表
    icons: 图标信息列表 [{"name": "...", "size": 24, "format": "svg", "stroke_width": 1.5}]
    animations: 动画信息列表 [{"duration_ms": 300, "easing": "cubic-bezier(...)"}]
    """
    all_issues: List[AestheticIssue] = []
    passed = []

    # 颜色检查
    if colors:
        color_issues = check_color_combination(colors)
        all_issues.extend(color_issues)
        if not color_issues:
            passed.append("配色合规")

    # 字体检查
    if fonts:
        font_issues = check_fonts(fonts)
        all_issues.extend(font_issues)
        if not font_issues:
            passed.append("字体搭配合理")

    # 图标检查
    if icons:
        icon_issues = check_icons(icons)
        all_issues.extend(icon_issues)
        if not icon_issues:
            passed.append("图标规范")

    # 动画检查
    if animations:
        anim_issues = check_animation(animations)
        all_issues.extend(anim_issues)
        if not anim_issues:
            passed.append("动画流畅")

    # 评分
    score = 100.0
    error_count = sum(1 for i in all_issues if i.severity == "error")
    warn_count = sum(1 for i in all_issues if i.severity == "warn")
    info_count = sum(1 for i in all_issues if i.severity == "info")
    score -= error_count * 25
    score -= warn_count * 8
    score -= info_count * 2
    score = max(0, score)

    # 推荐配色
    palette = None
    if colors:
        for name, p in COLOR_PALETTES.items():
            p_colors = [p["primary"], p["secondary"], p["accent"]]
            if any(color_distance(normalize_color(c), pc) < 40 for c in colors for pc in p_colors):
                palette = {"name": name, **p}
                break

    return AestheticReport(
        score=round(score, 1),
        grade=grade_from_score(score),
        issues=all_issues,
        palette=palette,
        passed_rules=passed,
    )


def check_generated_image(description: str, colors_used: List[str]) -> AestheticReport:
    """
    快速审查AI生成的图像描述
    用户说"生成一棵树"但用了棕色+绿色圆圈 → 报错
    """
    keywords_tree = ["树", "tree", "树木", "植物", "plant"]
    keywords_nature = ["自然", "nature", "森林", "forest", "草地", "grass"]

    is_tree_request = any(k in description.lower() for k in keywords_tree)
    norms = [normalize_color(c) for c in colors_used]

    # 基础检查：棕色 + 单独绿色 ≠ 树
    if is_tree_request:
        has_brown = any(color_distance(n, "#8B4513") < 50 for n in norms)
        has_green = any(color_distance(n, "#228B22") < 50 or color_distance(n, "#00FF00") < 50 for n in norms)
        if has_brown and has_green and len(norms) == 2:
            issues = [AestheticIssue(
                severity="error",
                category="color",
                message="禁止的树生成方式：棕色(#8B4513) + 绿色圆圈 = 卡通化假树",
                suggestion="树需要：树干棕色 + 树冠渐变绿色 + 光影层次 + 阴影。参考自然配色：#2d5016树干, #3a7d44树冠, #8fbc8f浅色点缀",
            )]
            return AestheticReport(score=20, grade="D", issues=issues)

    return full_aesthetic_check(colors=colors_used)


# ─── 导出规则为JSON ─────────────────────────────────

def export_palette_json() -> str:
    """导出配色方案为JSON（供前端使用）"""
    import json
    return json.dumps(COLOR_PALETTES, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 演示
    print("=== 审美检查演示 ===\n")

    # 场景1: 正确的树生成
    report1 = check_generated_image(
        description="生成一棵自然风格的树",
        colors_used=["#2d5016", "#3a7d44", "#8fbc8f", "#5a8f3e"]
    )
    print(f"场景1 - 自然树: {report1.score}分 等级:{report1.grade}")
    for i in report1.issues:
        print(f"  [{i.severity}] {i.message}")

    # 场景2: 错误的树生成（棕色木棒+绿圆）
    report2 = check_generated_image(
        description="生成一棵树",
        colors_used=["#8B4513", "#228B22"]
    )
    print(f"\n场景2 - 卡通树: {report2.score}分 等级:{report2.grade}")
    for i in report2.issues:
        print(f"  [{i.severity}] {i.message}")

    # 场景3: 科技蓝界面
    report3 = full_aesthetic_check(
        colors=["#667eea", "#764ba2", "#00d4ff", "#0a0e1a", "#e2e8f0"],
        fonts=["AlimamaShuHeiTi-Bold", "Montserrat"],
        icons=[{"name": "star", "size": 24, "format": "svg", "stroke_width": 1.5}],
        animations=[{"duration_ms": 300, "easing": "cubic-bezier(0.16, 1, 0.3, 1)"}],
    )
    print(f"\n场景3 - 科技蓝界面: {report3.score}分 等级:{report3.grade}")
    for i in report3.issues:
        print(f"  [{i.severity}] {i.message}")
    print(f"通过: {report3.passed_rules}")
    print(f"推荐配色: {report3.palette}")
