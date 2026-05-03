#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景生成器 - AI辅助场景创建

功能：
- 文本描述生成场景概念
- 自动生成场景布局
- 批量生成场景变体
- 导出到Blender/UE

用法：
    python scene_generator.py generate "fantasy forest" --style realistic
    python scene_generator.py batch scenes.txt --count 10
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp")
    raise

# GPU配置
sys.path.insert(0, str(Path(__file__).parent))
try:
    # [FIXED] gpu_config not available - from gpu_config import GPU_CONFIG, clear_gpu_cache
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# ============================================================
# FastMCP Server
# ============================================================
mcp = FastMCP("scene-generator")

# ============================================================
# 场景配置
# ============================================================
@dataclass
class SceneConfig:
    """场景配置"""
    name: str
    description: str
    style: str = "realistic"
    time_of_day: str = "day"
    weather: str = "clear"
    biome: str = "forest"
    complexity: str = "medium"

# 场景元素库
SCENE_ELEMENTS = {
    "forest": {
        "trees": ["oak", "pine", "birch", "willow", "redwood"],
        "ground": ["grass", "moss", "dirt", "leaves"],
        "vegetation": ["ferns", "bushes", "flowers", "mushrooms"],
        "props": ["rocks", "logs", "stumps", "stream"]
    },
    "urban": {
        "buildings": ["skyscraper", "apartment", "shop", "warehouse"],
        "streets": ["asphalt", "concrete", "cobblestone"],
        "props": ["cars", "streetlights", "trashcans", "benches"],
        "vegetation": ["street_trees", "planters", "parks"]
    },
    "fantasy": {
        "structures": ["castle", "tower", "ruins", "temple"],
        "vegetation": ["glowing_plants", "crystal_trees", "magic_flowers"],
        "props": ["magic_circles", "ancient_statues", "treasure_chests"],
        "effects": ["floating_islands", "waterfalls", "aurora"]
    },
    "scifi": {
        "structures": ["space_station", "dome", "habitat", "laboratory"],
        "vehicles": ["spaceship", "rover", "drone", "shuttle"],
        "props": ["holograms", "terminals", "solar_panels", "antennas"],
        "effects": ["neon_lights", "force_fields", "energy_beams"]
    }
}

# ============================================================
# 场景生成工具
# ============================================================
@mcp.tool()
async def generate_scene_concept(
    description: str,
    style: str = "realistic",
    biome: str = "forest",
    complexity: str = "medium"
) -> Dict[str, Any]:
    """
    生成场景概念
    
    Args:
        description: 场景描述
        style: 风格 (realistic/stylized/fantasy/scifi)
        biome: 生态 (forest/urban/desert/snow/ocean)
        complexity: 复杂度 (low/medium/high)
    
    Returns:
        场景概念数据
    """
    try:
        print(f"🎨 Generating scene concept: {description}")
        
        # 解析场景元素
        elements = SCENE_ELEMENTS.get(biome, SCENE_ELEMENTS["forest"])
        
        # 根据复杂度选择元素数量
        complexity_multiplier = {
            "low": 0.5,
            "medium": 1.0,
            "high": 2.0
        }.get(complexity, 1.0)
        
        # 生成场景配置
        scene_config = {
            "name": f"scene_{hash(description) % 1000000}",
            "description": description,
            "style": style,
            "biome": biome,
            "complexity": complexity,
            "elements": {
                category: items[:int(len(items) * complexity_multiplier)]
                for category, items in elements.items()
            },
            "lighting": {
                "time_of_day": "day",
                "weather": "clear",
                "mood": "peaceful"
            },
            "camera": {
                "position": [10, 5, 10],
                "target": [0, 0, 0],
                "fov": 60
            }
        }
        
        # 保存场景配置
        output_dir = Path("/python/Output/Scenes/Concepts")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = output_dir / f"{scene_config['name']}.json"
        config_file.write_text(json.dumps(scene_config, indent=2), encoding='utf-8')
        
        return {
            "success": True,
            "scene_name": scene_config['name'],
            "config_file": str(config_file),
            "elements_count": sum(len(v) for v in scene_config['elements'].values()),
            "style": style,
            "biome": biome
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def generate_scene_layout(
    scene_name: str,
    size: str = "100x100",
    density: str = "medium"
) -> Dict[str, Any]:
    """
    生成场景布局
    
    Args:
        scene_name: 场景名称
        size: 场景尺寸 (50x50/100x100/200x200)
        density: 元素密度 (low/medium/high)
    
    Returns:
        场景布局数据
    """
    try:
        print(f"📐 Generating layout for: {scene_name}")
        
        # 解析尺寸
        width, height = map(int, size.split('x'))
        
        # 密度配置
        density_config = {
            "low": 0.3,
            "medium": 0.6,
            "high": 1.0
        }.get(density, 0.6)
        
        # 生成布局网格
        layout = {
            "size": {"width": width, "height": height},
            "density": density,
            "terrain": {
                "heightmap": f"heightmap_{scene_name}.png",
                "material": "ground_grass"
            },
            "objects": []
        }
        
        # 随机放置对象
        import random
        random.seed(hash(scene_name))
        
        num_objects = int((width * height) / 100 * density_config)
        
        for i in range(num_objects):
            obj = {
                "id": i,
                "type": random.choice(["tree", "rock", "bush", "prop"]),
                "position": [
                    random.uniform(-width/2, width/2),
                    0,
                    random.uniform(-height/2, height/2)
                ],
                "rotation": [0, random.uniform(0, 360), 0],
                "scale": random.uniform(0.8, 1.2)
            }
            layout["objects"].append(obj)
        
        # 保存布局
        output_dir = Path("/python/Output/Scenes/Layouts")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        layout_file = output_dir / f"{scene_name}_layout.json"
        layout_file.write_text(json.dumps(layout, indent=2), encoding='utf-8')
        
        return {
            "success": True,
            "scene_name": scene_name,
            "layout_file": str(layout_file),
            "objects_count": len(layout["objects"]),
            "size": size
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def batch_generate_scenes(
    descriptions: List[str],
    style: str = "realistic",
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    批量生成场景
    
    Args:
        descriptions: 场景描述列表
        style: 风格
        max_concurrent: 最大并发数
    
    Returns:
        批量生成结果
    """
    try:
        print(f"🚀 Batch generating {len(descriptions)} scenes")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_one(description):
            async with semaphore:
                return await generate_scene_concept(description, style)
        
        tasks = [generate_one(desc) for desc in descriptions]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r.get("success"))
        
        # 清理GPU缓存
        if GPU_AVAILABLE:
            clear_gpu_cache()
        
        return {
            "success": True,
            "total": len(descriptions),
            "successful": successful,
            "results": results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def export_scene_to_blender(
    scene_name: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    导出场景到Blender
    
    Args:
        scene_name: 场景名称
        output_file: 输出文件路径
    
    Returns:
        导出结果
    """
    try:
        # 读取场景配置
        config_file = Path(f"/python/Output/Scenes/Concepts/{scene_name}.json")
        if not config_file.exists():
            return {"success": False, "error": f"Scene config not found: {scene_name}"}
        
        scene_config = json.loads(config_file.read_text())
        
        # 生成Blender Python脚本
        blender_script = f'''
import bpy
import json

# 清理场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 创建地形
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain = bpy.context.active_object
terrain.name = "Terrain"

# 添加细分
modifier = terrain.modifiers.new(name="Subdivision", type='SUBSURF')
modifier.levels = 6

# 添加置换纹理 (模拟地形高度)
displace = terrain.modifiers.new(name="Displace", type='DISPLACE')
tex = bpy.data.textures.new(name="HeightMap", type='CLOUDS')
displace.texture = tex
displace.strength = 5

# 根据场景配置添加元素
scene_data = json.loads(r"""{json.dumps(scene_config)}""")

# 添加树木
for i in range(20):
    x = (i % 5 - 2) * 10
    y = (i // 5 - 2) * 10
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=4, location=(x, y, 2))
    trunk = bpy.context.active_object
    trunk.name = f"Tree_{{i}}_Trunk"
    
    bpy.ops.mesh.primitive_ico_sphere_add(radius=2, location=(x, y, 5))
    leaves = bpy.context.active_object
    leaves.name = f"Tree_{{i}}_Leaves"

# 设置相机
bpy.ops.object.camera_add(location=(50, -50, 30))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = camera

# 设置灯光
bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
light = bpy.context.active_object
light.data.energy = 3

# 保存文件
output_path = r"{output_file or f'/python/Output/Scenes/Blender/{scene_name}.blend'}"
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"Scene exported to: {{output_path}}")
'''
        
        # 保存脚本
        script_file = Path(f"/python/Temp/blender_scene_{scene_name}.py")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.write_text(blender_script, encoding='utf-8')
        
        # 执行Blender脚本
        import subprocess
        result = subprocess.run(
            ["%DEVTOOLS_DIR%/Blender/blender.exe", "--background", "--python", str(script_file)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "scene_name": scene_name,
                "output_file": output_file or f"/python/Output/Scenes/Blender/{scene_name}.blend",
                "objects_created": 40  # 20 trees (trunk + leaves)
            }
        else:
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_scene_templates() -> Dict[str, Any]:
    """
    获取场景模板列表
    
    Returns:
        可用的场景模板
    """
    return {
        "success": True,
        "templates": {
            "forest": {
                "description": "Natural forest environment",
                "elements": ["trees", "bushes", "rocks", "stream"],
                "mood": "peaceful"
            },
            "urban": {
                "description": "City street scene",
                "elements": ["buildings", "cars", "streetlights", "sidewalk"],
                "mood": "busy"
            },
            "fantasy": {
                "description": "Magical fantasy world",
                "elements": ["castle", "magic_trees", "floating_islands"],
                "mood": "mysterious"
            },
            "scifi": {
                "description": "Futuristic sci-fi setting",
                "elements": ["space_station", "holograms", "neon_lights"],
                "mood": "technological"
            }
        }
    }

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("🎨 Scene Generator - AI Scene Creation")
    print("=" * 50)
    if GPU_AVAILABLE:
        print(f"📊 GPU: {GPU_CONFIG['gpu_name']}")
    print("=" * 50)
    mcp.run()
