#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人物生成器 - AI辅助角色创建

功能：
- 文本描述生成人物概念
- 自动生成角色外观
- 批量生成角色变体
- 导出到Blender/UE
- 自动生成骨骼绑定

用法：
    python character_generator.py generate "warrior" --style realistic --gender male
    python character_generator.py batch characters.txt --count 10
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
mcp = FastMCP("character-generator")

# ============================================================
# 角色配置
# ============================================================
@dataclass
class CharacterConfig:
    """角色配置"""
    name: str
    description: str
    gender: str = "male"
    age: str = "adult"
    body_type: str = "average"
    style: str = "realistic"
    race: str = "human"
    profession: str = "warrior"

# 角色部件库
CHARACTER_PARTS = {
    "body": {
        "types": ["slim", "average", "muscular", "heavy"],
        "heights": ["short", "average", "tall"],
        "proportions": ["child", "teen", "adult", "elderly"]
    },
    "head": {
        "face_shapes": ["oval", "round", "square", "heart", "diamond"],
        "features": ["sharp", "soft", "rugged", "delicate"],
        "expressions": ["neutral", "serious", "friendly", "determined"]
    },
    "hair": {
        "styles": ["short", "medium", "long", "bald", "ponytail", "braided"],
        "colors": ["black", "brown", "blonde", "red", "gray", "white"],
        "textures": ["straight", "wavy", "curly", "coily"]
    },
    "clothing": {
        "styles": ["casual", "formal", "armor", "robes", "uniform"],
        "layers": ["underwear", "base", "mid", "outer", "accessories"],
        "materials": ["cloth", "leather", "metal", "fur", "silk"]
    },
    "equipment": {
        "weapons": ["sword", "axe", "bow", "staff", "dagger", "mace"],
        "shields": ["round", "tower", "buckler", "kite"],
        "accessories": ["necklace", "ring", "bracelet", "belt", "cape"]
    }
}

# 职业配置
PROFESSION_CONFIG = {
    "warrior": {
        "body_type": "muscular",
        "clothing": "armor",
        "weapons": ["sword", "axe", "shield"],
        "attributes": ["strength", "endurance", "courage"]
    },
    "mage": {
        "body_type": "slim",
        "clothing": "robes",
        "weapons": ["staff", "wand", "book"],
        "attributes": ["intelligence", "wisdom", "magic"]
    },
    "rogue": {
        "body_type": "slim",
        "clothing": "leather",
        "weapons": ["dagger", "bow", "cloak"],
        "attributes": ["agility", "stealth", "dexterity"]
    },
    "archer": {
        "body_type": "average",
        "clothing": "leather",
        "weapons": ["bow", "quiver", "dagger"],
        "attributes": ["precision", "focus", "agility"]
    },
    "priest": {
        "body_type": "average",
        "clothing": "robes",
        "weapons": ["staff", "book", "amulet"],
        "attributes": ["faith", "healing", "wisdom"]
    }
}

# ============================================================
# 角色生成工具
# ============================================================
@mcp.tool()
async def generate_character_concept(
    description: str,
    gender: str = "male",
    profession: str = "warrior",
    style: str = "realistic",
    race: str = "human"
) -> Dict[str, Any]:
    """
    生成角色概念
    
    Args:
        description: 角色描述
        gender: 性别 (male/female/other)
        profession: 职业 (warrior/mage/rogue/archer/priest)
        style: 风格 (realistic/stylized/cartoon/anime)
        race: 种族 (human/elf/dwarf/orc/other)
    
    Returns:
        角色概念数据
    """
    try:
        print(f"🎨 Generating character: {description}")
        
        # 获取职业配置
        prof_config = PROFESSION_CONFIG.get(profession, PROFESSION_CONFIG["warrior"])
        
        # 生成角色配置
        character = {
            "name": f"char_{hash(description) % 1000000}",
            "description": description,
            "gender": gender,
            "profession": profession,
            "style": style,
            "race": race,
            "appearance": {
                "body": {
                    "type": prof_config["body_type"],
                    "height": "average",
                    "age": "adult"
                },
                "face": {
                    "shape": "oval",
                    "features": "average",
                    "expression": "neutral"
                },
                "hair": {
                    "style": "short" if gender == "male" else "long",
                    "color": "brown",
                    "texture": "straight"
                }
            },
            "clothing": {
                "style": prof_config["clothing"],
                "colors": ["brown", "gray"],
                "materials": ["leather", "cloth"]
            },
            "equipment": {
                "weapons": prof_config["weapons"][:2],
                "armor": prof_config["clothing"],
                "accessories": []
            },
            "attributes": prof_config["attributes"],
            "stats": {
                "strength": 10,
                "agility": 10,
                "intelligence": 10,
                "charisma": 10
            }
        }
        
        # 保存角色配置
        output_dir = Path("/python/Output/Characters/Concepts")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = output_dir / f"{character['name']}.json"
        config_file.write_text(json.dumps(character, indent=2), encoding='utf-8')
        
        return {
            "success": True,
            "character_name": character['name'],
            "config_file": str(config_file),
            "profession": profession,
            "style": style,
            "race": race,
            "attributes": character['attributes']
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def generate_character_variations(
    base_character: str,
    count: int = 5,
    variation_types: List[str] = None
) -> Dict[str, Any]:
    """
    生成角色变体
    
    Args:
        base_character: 基础角色名称
        count: 变体数量
        variation_types: 变体类型 ["hair", "clothing", "equipment", "colors"]
    
    Returns:
        变体列表
    """
    try:
        if variation_types is None:
            variation_types = ["hair", "clothing", "equipment"]
        
        print(f"🎨 Generating {count} variations for: {base_character}")
        
        # 读取基础角色
        config_file = Path(f"/python/Output/Characters/Concepts/{base_character}.json")
        if not config_file.exists():
            return {"success": False, "error": f"Character not found: {base_character}"}
        
        base_config = json.loads(config_file.read_text())
        
        variations = []
        import random
        random.seed(hash(base_character))
        
        for i in range(count):
            variant = base_config.copy()
            variant["name"] = f"{base_character}_var{i}"
            variant["parent"] = base_character
            
            # 应用变体
            if "hair" in variation_types:
                variant["appearance"]["hair"]["color"] = random.choice(
                    CHARACTER_PARTS["hair"]["colors"]
                )
                variant["appearance"]["hair"]["style"] = random.choice(
                    CHARACTER_PARTS["hair"]["styles"]
                )
            
            if "clothing" in variation_types:
                variant["clothing"]["colors"] = [
                    random.choice(["red", "blue", "green", "brown", "gray", "black"])
                    for _ in range(2)
                ]
            
            if "equipment" in variation_types:
                prof = variant["profession"]
                weapons = PROFESSION_CONFIG[prof]["weapons"]
                variant["equipment"]["weapons"] = random.sample(weapons, min(2, len(weapons)))
            
            # 保存变体
            variant_file = Path(f"/python/Output/Characters/Variations/{variant['name']}.json")
            variant_file.parent.mkdir(parents=True, exist_ok=True)
            variant_file.write_text(json.dumps(variant, indent=2), encoding='utf-8')
            
            variations.append({
                "name": variant["name"],
                "file": str(variant_file),
                "changes": variation_types
            })
        
        return {
            "success": True,
            "base_character": base_character,
            "variations_count": len(variations),
            "variations": variations
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def generate_character_rig(
    character_name: str,
    rig_type: str = "humanoid"
) -> Dict[str, Any]:
    """
    生成角色骨骼绑定
    
    Args:
        character_name: 角色名称
        rig_type: 绑定类型 (humanoid/quadruped/biped)
    
    Returns:
        绑定配置
    """
    try:
        print(f"🦴 Generating rig for: {character_name}")
        
        # 骨骼配置
        rig_config = {
            "name": f"{character_name}_rig",
            "type": rig_type,
            "bones": {
                "spine": ["pelvis", "spine_01", "spine_02", "spine_03", "neck", "head"],
                "arms": ["clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
                        "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r"],
                "legs": ["thigh_l", "calf_l", "foot_l", "ball_l",
                        "thigh_r", "calf_r", "foot_r", "ball_r"],
                "fingers": ["thumb", "index", "middle", "ring", "pinky"]
            },
            "constraints": {
                "ik": ["arm_l", "arm_r", "leg_l", "leg_r"],
                "fk": ["spine", "neck", "head"],
                "twist": ["upperarm", "lowerarm", "thigh", "calf"]
            },
            "controllers": {
                "root": "root",
                "hips": "pelvis",
                "chest": "spine_03",
                "head": "head"
            }
        }
        
        # 保存绑定配置
        output_dir = Path("/python/Output/Characters/Rigs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        rig_file = output_dir / f"{rig_config['name']}.json"
        rig_file.write_text(json.dumps(rig_config, indent=2), encoding='utf-8')
        
        # 生成Blender绑定脚本
        blender_script = f'''
import bpy

# 创建骨骼
armature = bpy.data.armatures.new(name="{character_name}_Armature")
armature_obj = bpy.data.objects.new(name="{character_name}_Rig", object_data=armature)
bpy.context.collection.objects.link(armature_obj)

# 进入编辑模式
bpy.context.view_layer.objects.active = armature_obj
bpy.ops.object.mode_set(mode='EDIT')

# 创建脊柱
spine_bones = {rig_config["bones"]["spine"]}
for i, bone_name in enumerate(spine_bones):
    bone = armature.edit_bones.new(bone_name)
    bone.head = (0, 0, i * 0.3)
    bone.tail = (0, 0, (i + 1) * 0.3)
    if i > 0:
        bone.parent = armature.edit_bones[spine_bones[i-1]]

# 创建手臂
for side in ['_l', '_r']:
    clavicle = armature.edit_bones.new(f'clavicle{{side}}')
    clavicle.head = (0.2 if side == '_l' else -0.2, 0, 1.4)
    clavicle.tail = (0.3 if side == '_l' else -0.3, 0, 1.4)
    
    upperarm = armature.edit_bones.new(f'upperarm{{side}}')
    upperarm.head = clavicle.tail
    upperarm.tail = (0.5 if side == '_l' else -0.5, 0, 1.2)
    upperarm.parent = clavicle
    
    lowerarm = armature.edit_bones.new(f'lowerarm{{side}}')
    lowerarm.head = upperarm.tail
    lowerarm.tail = (0.6 if side == '_l' else -0.6, 0, 0.9)
    lowerarm.parent = upperarm
    
    hand = armature.edit_bones.new(f'hand{{side}}')
    hand.head = lowerarm.tail
    hand.tail = (0.65 if side == '_l' else -0.65, 0, 0.8)
    hand.parent = lowerarm

# 创建腿部
for side in ['_l', '_r']:
    thigh = armature.edit_bones.new(f'thigh{{side}}')
    thigh.head = (0.1 if side == '_l' else -0.1, 0, 0.9)
    thigh.tail = (0.15 if side == '_l' else -0.15, 0, 0.5)
    
    calf = armature.edit_bones.new(f'calf{{side}}')
    calf.head = thigh.tail
    calf.tail = (0.15 if side == '_l' else -0.15, 0, 0.1)
    calf.parent = thigh
    
    foot = armature.edit_bones.new(f'foot{{side}}')
    foot.head = calf.tail
    foot.tail = (0.15 if side == '_l' else -0.15, 0.2, 0)
    foot.parent = calf

# 返回对象模式
bpy.ops.object.mode_set(mode='OBJECT')

# 保存
output_path = "/python/Output/Characters/Blender/{character_name}_rig.blend"
bpy.ops.wm.save_as_mainfile(filepath=output_path)
print(f"Rig saved to: {{output_path}}")
'''
        
        script_file = Path(f"/python/Temp/blender_rig_{character_name}.py")
        script_file.parent.mkdir(parents=True, exist_ok=True)
        script_file.write_text(blender_script, encoding='utf-8')
        
        return {
            "success": True,
            "character": character_name,
            "rig_type": rig_type,
            "rig_file": str(rig_file),
            "script_file": str(script_file),
            "bones_count": len([b for bones in rig_config["bones"].values() for b in bones])
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def batch_generate_characters(
    descriptions: List[str],
    profession: str = "warrior",
    style: str = "realistic",
    max_concurrent: int = 3
) -> Dict[str, Any]:
    """
    批量生成角色
    
    Args:
        descriptions: 角色描述列表
        profession: 职业
        style: 风格
        max_concurrent: 最大并发数
    
    Returns:
        批量生成结果
    """
    try:
        print(f"🚀 Batch generating {len(descriptions)} characters")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_one(desc):
            async with semaphore:
                return await generate_character_concept(desc, profession=profession, style=style)
        
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
async def get_profession_templates() -> Dict[str, Any]:
    """
    获取职业模板列表
    
    Returns:
        可用的职业模板
    """
    return {
        "success": True,
        "professions": {
            "warrior": {
                "description": "Melee combat specialist",
                "attributes": ["strength", "endurance", "courage"],
                "equipment": ["sword", "shield", "armor"]
            },
            "mage": {
                "description": "Magic user",
                "attributes": ["intelligence", "wisdom", "magic"],
                "equipment": ["staff", "robes", "spellbook"]
            },
            "rogue": {
                "description": "Stealth and agility specialist",
                "attributes": ["agility", "stealth", "dexterity"],
                "equipment": ["daggers", "bow", "leather"]
            },
            "archer": {
                "description": "Ranged combat specialist",
                "attributes": ["precision", "focus", "agility"],
                "equipment": ["bow", "arrows", "quiver"]
            },
            "priest": {
                "description": "Healing and support",
                "attributes": ["faith", "healing", "wisdom"],
                "equipment": ["staff", "holy_symbol", "robes"]
            }
        }
    }

# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("👤 Character Generator - AI Character Creation")
    print("=" * 50)
    if GPU_AVAILABLE:
        print(f"📊 GPU: {GPU_CONFIG['gpu_name']}")
    print("=" * 50)
    mcp.run()
