import urllib.request
import json
import os
import time
import zipfile
import io

MC_DIR = r"%GAME_DIR%\.minecraft"
VER_DIR = os.path.join(MC_DIR, "versions", "我即是虫群-1.20.4-Fabric")
MODS_DIR = os.path.join(VER_DIR, "mods")
RP_DIR = os.path.join(VER_DIR, "resourcepacks")
DATAPACK_DIR = os.path.join(VER_DIR, "datapacks")

os.makedirs(MODS_DIR, exist_ok=True)
os.makedirs(RP_DIR, exist_ok=True)
os.makedirs(DATAPACK_DIR, exist_ok=True)

def download_file(url, path, desc=""):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
        print(f"  [OK] {desc or os.path.basename(path)} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  [FAIL] {desc or os.path.basename(path)}: {e}")
        return False

def modrinth_search(query, limit=10):
    url = f"https://api.modrinth.com/v2/search?query={urllib.parse.quote(query)}&facets=[[%22project_type:mod%22],[%22versions:1.20.4%22],[%22categories:fabric%22]]&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())["hits"]
    except:
        return []

def modrinth_get_versions(slug):
    url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[%221.20.4%22]&loaders=[%22fabric%22]"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except:
        return []

def download_mod(slug, name=""):
    versions = modrinth_get_versions(slug)
    if not versions:
        print(f"  [SKIP] {name or slug}: no Fabric 1.20.4 version found")
        return False
    ver = versions[0]
    for f in ver.get("files", []):
        fn = f["filename"]
        if fn.endswith(".jar"):
            existing = [x for x in os.listdir(MODS_DIR) if slug.replace("-", "") in x.replace("-", "").lower() or name.replace(" ", "").lower() in x.replace(" ", "").lower() if x.endswith(".jar")]
            if existing:
                print(f"  [EXISTS] {name or slug}")
                return True
            return download_file(f["url"], os.path.join(MODS_DIR, fn), name or slug)
    print(f"  [SKIP] {name or slug}: no jar file found")
    return False

import urllib.parse

print("=" * 60)
print("  我即是虫群 - 完整修复脚本")
print("=" * 60)

print("\n[1/5] 修复版本JSON - 添加正确的assetIndex...")
ver_json_path = os.path.join(VER_DIR, "我即是虫群-1.20.4-Fabric.json")
with open(ver_json_path, "r", encoding="utf-8") as f:
    ver_json = json.load(f)

ver_json["assetIndex"] = {
    "id": "12",
    "sha1": "6f83c5a3e7a488af2550a68eeec834c46138366d",
    "size": 437292,
    "totalSize": 644854662,
    "url": "https://piston-meta.mojang.com/v1/packages/6f83c5a3e7a488af2550a68eeec834c46138366d/12.json"
}
ver_json["assets"] = "12"

with open(ver_json_path, "w", encoding="utf-8") as f:
    json.dump(ver_json, f, indent=2, ensure_ascii=False)
print("  [OK] assetIndex 已修复为 12")

print("\n[2/5] 下载虫族/寄生虫主题模组...")
MODS_TO_DOWNLOAD = [
    ("origins", "Origins"),
    ("apoli", "Apoli"),
    ("calio", "Calio"),
    ("pehkui", "Pehkui"),
    ("fabric-api", "Fabric API"),
    ("geckolib", "GeckoLib"),
    ("moborigins", "Mob Origins"),
    ("additional-origins", "Additional Origins"),
    ("origins-classes", "Origins Classes"),
    ("expand-origin", "Expand Origin"),
    ("origins-umbra", "Origins Umbra"),
    ("bewitchment", "Bewitchment"),
    ("spectrum", "Spectrum"),
    ("conjuring", "Conjuring"),
    ("mythic-mounts", "Mythic Mounts"),
    ("mowzies-mobs", "Mowzie's Mobs"),
    ("enderman-overhaul", "Enderman Overhaul"),
    ("friends-and-foes", "Friends and Foes"),
    ("naturalist", "Naturalist"),
    ("ecologics", "Ecologics"),
    ("environmental", "Environmental"),
    ("autumnity", "Autumnity"),
    ("atmospheric", "Atmospheric"),
    ("bayou-blues", "Bayou Blues"),
    ("swampier-swamps", "Swampier Swamps"),
    ("creeper-overhaul", "Creeper Overhaul"),
    ("zombie-horses", "Zombie Horses"),
    ("illager-invasion", "Illager Invasion"),
    ("mutant-monsters", "Mutant Monsters"),
    ("spider-queen", "Spider Queen"),
    ("insectify", "Insectify"),
    ("better-combat", "Better Combat"),
    ("cloth-config", "Cloth Config"),
    ("architectury", "Architectury"),
    ("modmenu", "Mod Menu"),
    ("roughly-enough-items", "REI"),
    ("sodium", "Sodium"),
    ("lithium", "Lithium"),
    ("iris", "Iris"),
    ("indium", "Indium"),
    ("ferritecore", "FerriteCore"),
    ("entityculling", "Entity Culling"),
    ("memoryleakfix", "Memory Leak Fix"),
    ("no-chat-reports", "No Chat Reports"),
    ("debugify", "Debugify"),
    ("language-reload", "Language Reload"),
    ("continuity", "Continuity"),
    ("not-enough-animations", "Not Enough Animations"),
    ("3d-skin-layers", "3D Skin Layers"),
    ("visuality", "Visuality"),
    ("ambientsounds", "Ambient Sounds"),
    ("sound-physics-remastered", "Sound Physics Remastered"),
    ("drip-sounds", "Drip Sounds"),
    ("presence-footsteps", "Presence Footsteps"),
    ("first-person-model", "First Person Model"),
    ("customizable-crosshair", "Customizable Crosshair"),
    ("better-third-person", "Better Third Person"),
    ("cameraoverhaul", "Camera Overhaul"),
    ("wavey-capes", "Wavey Capes"),
    ("cull-leaves", "Cull Leaves"),
    ("falling-leaves", "Falling Leaves"),
    ("particle-rain", "Particle Rain"),
    ("dynamic-fps", "Dynamic FPS"),
    ("faster-random", "Faster Random"),
    ("starlight", "Starlight"),
    ("modernfix", "ModernFix"),
    ("immediatelyfast", "ImmediatelyFast"),
    ("ferritecore", "FerriteCore"),
    ("netherportalfix", "Nether Portal Fix"),
    ("inventory-profiles-next", "Inventory Profiles Next"),
    ("libipn", "libIPN"),
    ("sortify", "Sortify"),
    ("carpet", "Carpet Mod"),
    ("litematica", "Litematica"),
    ("malilib", "MaLiLib"),
    ("minihud", "MiniHUD"),
    ("tweakeroo", "Tweakeroo"),
    ("itemscroller", "Item Scroller"),
    ("syncmatica", "Syncmatica"),
    ("voice-chat", "Simple Voice Chat"),
    ("plasmo-voice", "Plasmo Voice"),
    ("create", "Create"),
    ("create-fabric", "Create Fabric"),
    ("terralith", "Terralith"),
    ("tectonic", "Tectonic"),
    ("geophilic", "Geophilic"),
    ("structory", "Structory"),
    ("towns-and-towers", "Towns and Towers"),
    ("yungs-better-desert-temples", "YUNG's Better Desert Temples"),
    ("yungs-better-dungeons", "YUNG's Better Dungeons"),
    ("yungs-better-end-island", "YUNG's Better End Island"),
    ("yungs-better-mineshafts", "YUNG's Better Mineshafts"),
    ("yungs-better-nether-fortresses", "YUNG's Better Nether Fortresses"),
    ("yungs-better-ocean-monuments", "YUNG's Better Ocean Monuments"),
    ("yungs-better-strongholds", "YUNG's Better Strongholds"),
    ("yungs-better-witch-huts", "YUNG's Better Witch Huts"),
    ("yungs-bridges", "YUNG's Bridges"),
    ("yungs-extras", "YUNG's Extras"),
    ("fabric-language-kotlin", "Fabric Language Kotlin"),
    ("cardinal-components-api", "Cardinal Components API"),
    ("additionalentityattributes", "Additional Entity Attributes"),
    ("reach-entity-attributes", "Reach Entity Attributes"),
    ("playerabilitylib", "PlayerAbilityLib"),
    ("codec-config-api", "Codec Config API"),
    ("gui-wrapper", "GUI Wrapper"),
    ("midnightlib", "MidnightLib"),
    ("spark", "Spark"),
    ("lazydfu", "LazyDFU"),
    ("fabricloader", "Fabric Loader"),
]

downloaded = 0
failed = 0
skipped = 0
for slug, name in MODS_TO_DOWNLOAD:
    existing = [x for x in os.listdir(MODS_DIR) if x.endswith(".jar")]
    already = False
    for ex in existing:
        ex_lower = ex.lower().replace("-", "").replace(" ", "")
        slug_clean = slug.replace("-", "").replace(" ", "").lower()
        name_clean = name.replace("-", "").replace(" ", "").lower()
        if slug_clean in ex_lower or name_clean in ex_lower:
            already = True
            break
    if already:
        skipped += 1
        continue
    
    print(f"  下载 {name} ({slug})...")
    if download_mod(slug, name):
        downloaded += 1
    else:
        failed += 1
    time.sleep(0.5)

print(f"\n  模组下载完成: {downloaded}个新下载, {skipped}个已存在, {failed}个失败")

print("\n[3/5] 创建虫族起源数据包...")

def create_swarm_datapack():
    dp_dir = os.path.join(DATAPACK_DIR, "swarm_origins")
    data_dir = os.path.join(dp_dir, "data", "swarm_origins", "origins")
    os.makedirs(data_dir, exist_ok=True)
    
    mcmeta = os.path.join(dp_dir, "pack.mcmeta")
    with open(mcmeta, "w", encoding="utf-8") as f:
        json.dump({
            "pack": {
                "pack_format": 26,
                "description": "\u00a7a\u866b\u65cf\u8d77\u6e90 - \u6211\u5373\u662f\u866b\u7fa4"
            }
        }, f, ensure_ascii=False, indent=2)
    
    origins_list = {
        "origins": [
            "swarm_origins:larva",
            "swarm_origins:spitter",
            "swarm_origins:burrower",
            "swarm_origins:flyer",
            "swarm_origins:brood_mother",
            "swarm_origins:stalker",
            "swarm_origins:devourer",
            "swarm_origins:hivemind",
            "swarm_origins:spore_carrier",
            "swarm_origins:changeling",
            "swarm_origins:parasite_lord"
        ]
    }
    with open(os.path.join(data_dir, "origins.json"), "w", encoding="utf-8") as f:
        json.dump(origins_list, f, ensure_ascii=False, indent=2)
    
    powers_dir = os.path.join(dp_dir, "data", "swarm_origins", "powers")
    os.makedirs(powers_dir, exist_ok=True)
    
    origins_data = {
        "larva": {
            "name": "\u00a7a\u5e7c\u866b",
            "description": "\u866b\u65cf\u7684\u6700\u521d\u5f62\u6001\uff0c\u5f31\u5c0f\u4f46\u5145\u6ee1\u6f5c\u529b\u3002\u53ef\u4ee5\u7f29\u5c0f\u8eab\u4f53\u7a7f\u8fc7\u72ed\u7a84\u7a7a\u95f4\uff0c\u5403\u4efb\u4f55\u4e1c\u897f\u6062\u590d\u9965\u997f\u3002",
            "icon": "minecraft:slime_ball",
            "powers": [
                "swarm_origins:small_body",
                "swarm_origins:eat_anything",
                "swarm_origins:fragile",
                "swarm_origins:crawl_speed",
                "swarm_origins:dark_vision"
            ],
            "impact": 1,
            "unchoosable": False
        },
        "spitter": {
            "name": "\u00a72\u55b7\u5c04\u866b",
            "description": "\u8fdc\u7a0b\u653b\u51fb\u578b\u866b\u65cf\uff0c\u80fd\u55b7\u5c04\u9178\u6db2\u548c\u6bd2\u7d20\u3002\u53ef\u4ee5\u53d1\u5c04\u8fdc\u7a0b\u6295\u5c04\u7269\uff0c\u4f46\u8fd1\u6218\u80fd\u529b\u8f83\u5f31\u3002",
            "icon": "minecraft:arrow",
            "powers": [
                "swarm_origins:acid_spit",
                "swarm_origins:weak_melee",
                "swarm_origins:poison_immune",
                "swarm_origins:range_boost"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "burrower": {
            "name": "\u00a76\u6316\u6398\u866b",
            "description": "\u5730\u4e0b\u4f5c\u6218\u578b\u866b\u65cf\uff0c\u80fd\u5728\u571f\u5730\u4e2d\u5feb\u901f\u6316\u6398\u548c\u79fb\u52a8\u3002\u5728\u5730\u4e0b\u83b7\u5f97\u589e\u76ca\uff0c\u4f46\u5728\u5149\u7167\u4e0b\u53d7\u5230\u51cf\u76ca\u3002",
            "icon": "minecraft:diamond_shovel",
            "powers": [
                "swarm_origins:burrow_speed",
                "swarm_origins:underground_boost",
                "swarm_origins:sun_weakness",
                "swarm_origins:dark_vision",
                "swarm_origins:mine_speed"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "flyer": {
            "name": "\u00a7b\u98de\u884c\u866b",
            "description": "\u7a7a\u4e2d\u4f5c\u6218\u578b\u866b\u65cf\uff0c\u62e5\u6709\u7fc5\u8180\u53ef\u4ee5\u6ed1\u7fd4\u548c\u98de\u884c\u3002\u5728\u7a7a\u4e2d\u83b7\u5f97\u589e\u76ca\uff0c\u4f46\u8840\u91cf\u8f83\u4f4e\u3002",
            "icon": "minecraft:elytra",
            "powers": [
                "swarm_origins:winged_flight",
                "swarm_origins:air_boost",
                "swarm_origins:light_body",
                "swarm_origins:fall_resistance"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "brood_mother": {
            "name": "\u00a7d\u6bcd\u866b",
            "description": "\u866b\u65cf\u7684\u7e41\u6b96\u8005\uff0c\u80fd\u53ec\u5524\u5e7c\u866b\u4f5c\u6218\u3002\u751f\u547d\u503c\u9ad8\u4f46\u79fb\u52a8\u901f\u5ea6\u6162\uff0c\u53ef\u4ee5\u901a\u8fc7\u98df\u7269\u7e41\u6b96\u65b0\u7684\u5e7c\u866b\u3002",
            "icon": "minecraft:spawner",
            "powers": [
                "swarm_origins:summon_larva",
                "swarm_origins:high_health",
                "swarm_origins:slow_movement",
                "swarm_origins:regen_near_allies",
                "swarm_origins:eat_anything"
            ],
            "impact": 3,
            "unchoosable": False
        },
        "stalker": {
            "name": "\u00a75\u6f5c\u884c\u866b",
            "description": "\u9690\u533f\u523a\u6740\u578b\u866b\u65cf\uff0c\u80fd\u5728\u9634\u5f71\u4e2d\u9690\u8eab\u5e76\u83b7\u5f97\u901f\u5ea6\u589e\u76ca\u3002\u653b\u51fb\u80fd\u529b\u5f3a\u4f46\u8840\u91cf\u4f4e\u3002",
            "icon": "minecraft:iron_sword",
            "powers": [
                "swarm_origins:shadow_cloak",
                "swarm_origins:shadow_speed",
                "swarm_origins:backstab",
                "swarm_origins:low_health",
                "swarm_origins:dark_vision"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "devourer": {
            "name": "\u00a7c\u541e\u566c\u866b",
            "description": "\u8d2a\u98df\u578b\u866b\u65cf\uff0c\u5403\u4e0b\u7684\u4e1c\u897f\u80fd\u8f6c\u5316\u4e3a\u751f\u547d\u548c\u529b\u91cf\u3002\u9965\u997f\u503c\u6d88\u8017\u6781\u5feb\uff0c\u4f46\u53ef\u4ee5\u5403\u4efb\u4f55\u4e1c\u897f\u3002",
            "icon": "minecraft:golden_apple",
            "powers": [
                "swarm_origins:devour_heal",
                "swarm_origins:eat_anything",
                "swarm_origins:fast_hunger",
                "swarm_origins:strength_when_fed",
                "swarm_origins:weak_when_hungry"
            ],
            "impact": 3,
            "unchoosable": False
        },
        "hivemind": {
            "name": "\u00a73\u8702\u7fa4\u610f\u8bc6",
            "description": "\u96c6\u4f53\u610f\u8bc6\u578b\u866b\u65cf\uff0c\u80fd\u611f\u77e5\u5468\u56f4\u751f\u7269\u5e76\u4e0e\u5176\u4ed6\u866b\u65cf\u5171\u4eab\u89c6\u91ce\u3002\u5355\u72ec\u4f5c\u6218\u80fd\u529b\u5f31\uff0c\u4f46\u5728\u866b\u65cf\u9644\u8fd1\u65f6\u83b7\u5f97\u5f3a\u5927\u589e\u76ca\u3002",
            "icon": "minecraft:ender_eye",
            "powers": [
                "swarm_origins:swarm_sense",
                "swarm_origins:herd_boost",
                "swarm_origins:weak_alone",
                "swarm_origins:dark_vision",
                "swarm_origins:shared_vision"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "spore_carrier": {
            "name": "\u00a7e\u5b62\u5b50\u643a\u5e26\u8005",
            "description": "\u771f\u83cc\u878d\u5408\u578b\u866b\u65cf\uff0c\u80fd\u91ca\u653e\u5b62\u5b50\u611f\u67d3\u654c\u4eba\u3002\u5728\u83cc\u4e1d\u4f53\u65c1\u53ef\u4ee5\u6062\u590d\u751f\u547d\uff0c\u501f\u52a9\u82b1\u6735\u79ef\u7d2f\u751f\u7269\u8d28\u3002",
            "icon": "minecraft:red_mushroom",
            "powers": [
                "swarm_origins:spore_infection",
                "swarm_origins:mycelium_heal",
                "swarm_origins:biomass_from_flowers",
                "swarm_origins:poison_immune",
                "swarm_origins:dark_vision"
            ],
            "impact": 3,
            "unchoosable": False
        },
        "changeling": {
            "name": "\u00a7f\u53d8\u5f62\u8005",
            "description": "\u53d8\u5f62\u4eff\u522b\u578b\u866b\u65cf\uff0c\u80fd\u6a21\u4eff\u5176\u4ed6\u751f\u7269\u7684\u5916\u8c8c\u548c\u80fd\u529b\u3002\u53ef\u4ee5\u53d8\u6210\u4e0d\u540c\u5f62\u6001\uff0c\u4f46\u6bcf\u79cd\u5f62\u6001\u90fd\u6709\u5c40\u9650\u6027\u3002",
            "icon": "minecraft:spawn_egg",
            "powers": [
                "swarm_origins:mimic_form",
                "swarm_origins:adaptive_resistance",
                "swarm_origins:no_natural_armor",
                "swarm_origins:dark_vision"
            ],
            "impact": 2,
            "unchoosable": False
        },
        "parasite_lord": {
            "name": "\u00a74\u5bc4\u751f\u866b\u738b",
            "description": "\u866b\u65cf\u7684\u6700\u7ec8\u5f62\u6001\uff0c\u638c\u63a7\u6240\u6709\u5bc4\u751f\u866b\u7684\u529b\u91cf\u3002\u80fd\u5438\u9644\u751f\u7269\u83b7\u5f97\u5176\u80fd\u529b\uff0c\u4f46\u9700\u8981\u4e0d\u65ad\u5438\u98df\u751f\u547d\u529b\u3002",
            "icon": "minecraft:nether_star",
            "powers": [
                "swarm_origins:life_drain",
                "swarm_origins:parasitic_strength",
                "swarm_origins:summon_parasites",
                "swarm_origins:constant_hunger",
                "swarm_origins:dark_vision",
                "swarm_origins:regen_on_kill"
            ],
            "impact": 3,
            "unchoosable": False
        }
    }
    
    for origin_id, origin_data in origins_data.items():
        with open(os.path.join(data_dir, f"{origin_id}.json"), "w", encoding="utf-8") as f:
            json.dump(origin_data, f, ensure_ascii=False, indent=2)
    
    powers_data = {
        "small_body": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Small body",
                "attribute": "minecraft:generic.scale",
                "value": 0.5,
                "operation": "add_value"
            }
        },
        "eat_anything": {
            "type": "apoli:modify_food",
            "item_condition": {"type": "apoli:ingredient", "ingredient": {"type": "apoli:everything"}},
            "food_modifier": {"operation": "add_value", "value": 2.0, "resource_location": "apoli:food"},
            "saturation_modifier": {"operation": "add_value", "value": 0.5, "resource_location": "apoli:saturation"}
        },
        "fragile": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Fragile",
                "attribute": "minecraft:generic.max_health",
                "value": -6.0,
                "operation": "add_value"
            }
        },
        "crawl_speed": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Crawl speed",
                "attribute": "minecraft:generic.movement_speed",
                "value": 0.02,
                "operation": "add_value"
            },
            "condition": {"type": "apoli:sneaking"}
        },
        "dark_vision": {
            "type": "apoli:night_vision",
            "strength": 0.5,
            "condition": {"type": "apoli:exposed_to", "dimension": "minecraft:overworld"}
        },
        "acid_spit": {
            "type": "apoli:fire_projectile",
            "entity_type": "minecraft:llama_spit",
            "cooldown": 40,
            "count": 1,
            "speed": 1.5,
            "divergence": 0.1,
            "sound": "minecraft:entity.llama.spit",
            "key": {"key": "key.origins.primary_active", "continuous": false}
        },
        "weak_melee": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Weak melee",
                "attribute": "minecraft:generic.attack_damage",
                "value": -2.0,
                "operation": "add_value"
            }
        },
        "poison_immune": {
            "type": "apoli:effect_immunity",
            "effect": "minecraft:poison"
        },
        "range_boost": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Range boost",
                "attribute": "minecraft:generic.attack_range",
                "value": 2.0,
                "operation": "add_value"
            }
        },
        "burrow_speed": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Burrow speed",
                "attribute": "minecraft:generic.movement_speed",
                "value": 0.03,
                "operation": "add_value"
            },
            "condition": {"type": "apoli:sneaking"}
        },
        "underground_boost": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Underground strength",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": 2.0,
                    "operation": "add_value"
                },
                {
                    "name": "Underground speed",
                    "attribute": "minecraft:generic.movement_speed",
                    "value": 0.02,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:height", "comparison": "<=", "compare_to": 40}
        },
        "sun_weakness": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Sun weakness",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": -2.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:exposed_to_sun"}
        },
        "mine_speed": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Mine speed",
                "attribute": "minecraft:generic.mining_speed",
                "value": 0.5,
                "operation": "add_value"
            }
        },
        "winged_flight": {
            "type": "origins:elytra_flight",
            "render_elytra": true
        },
        "air_boost": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Air boost",
                "attribute": "minecraft:generic.attack_damage",
                "value": 1.0,
                "operation": "add_value"
            },
            "condition": {"type": "apoli:in_block", "block_condition": {"type": "apoli:in_tag", "tag": "minecraft:air"}}
        },
        "light_body": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Light body",
                "attribute": "minecraft:generic.max_health",
                "value": -4.0,
                "operation": "add_value"
            }
        },
        "fall_resistance": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Fall resistance",
                "attribute": "minecraft:generic.safe_fall_distance",
                "value": 10.0,
                "operation": "add_value"
            }
        },
        "summon_larva": {
            "type": "apoli:launch_projectile",
            "entity_type": "minecraft:slime",
            "tag": "{Size:0,CustomName:'{\"text\":\"\\u00a7a\\u5e7c\\u866b\"}'}",
            "cooldown": 600,
            "count": 2,
            "speed": 0.5,
            "key": {"key": "key.origins.primary_active", "continuous": false}
        },
        "high_health": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "High health",
                "attribute": "minecraft:generic.max_health",
                "value": 10.0,
                "operation": "add_value"
            }
        },
        "slow_movement": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Slow movement",
                "attribute": "minecraft:generic.movement_speed",
                "value": -0.02,
                "operation": "add_value"
            }
        },
        "regen_near_allies": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Regen near allies",
                    "attribute": "minecraft:generic.max_health",
                    "value": 2.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:entity_in_radius", "entity_condition": {"type": "apoli:entity_type", "entity_type": "minecraft:slime"}, "radius": 10}
        },
        "shadow_cloak": {
            "type": "apoli:invisibility",
            "condition": {"type": "apoli:exposed_to_sun", "inverted": true}
        },
        "shadow_speed": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Shadow speed",
                    "attribute": "minecraft:generic.movement_speed",
                    "value": 0.04,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:light_level", "comparison": "<=", "compare_to": 4}
        },
        "backstab": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Backstab damage",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": 4.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:sneaking"}
        },
        "low_health": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Low health",
                "attribute": "minecraft:generic.max_health",
                "value": -8.0,
                "operation": "add_value"
            }
        },
        "devour_heal": {
            "type": "apoli:action_on_item_use",
            "item_condition": {"type": "apoli:food"},
            "entity_action": {"type": "apoli:heal", "amount": 2.0}
        },
        "fast_hunger": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Fast hunger",
                "attribute": "minecraft:generic.movement_speed",
                "value": 0.01,
                "operation": "add_value"
            }
        },
        "strength_when_fed": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Strength when fed",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": 3.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:food_level", "comparison": ">=", "compare_to": 16}
        },
        "weak_when_hungry": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Weak when hungry",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": -3.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:food_level", "comparison": "<=", "compare_to": 6}
        },
        "swarm_sense": {
            "type": "apoli:entity_glow",
            "entity_condition": {"type": "apoli:entity_type", "entity_type": "minecraft:player"},
            "bientity_condition": {"type": "apoli:distance", "comparison": "<=", "compare_to": 30}
        },
        "herd_boost": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Herd boost damage",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": 2.0,
                    "operation": "add_value"
                },
                {
                    "name": "Herd boost speed",
                    "attribute": "minecraft:generic.movement_speed",
                    "value": 0.02,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:entity_in_radius", "entity_condition": {"type": "apoli:entity_type", "entity_type": "minecraft:slime"}, "radius": 15}
        },
        "weak_alone": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Weak alone",
                    "attribute": "minecraft:generic.attack_damage",
                    "value": -2.0,
                    "operation": "add_value"
                }
            ],
            "condition": {
                "type": "apoli:invert",
                "condition": {"type": "apoli:entity_in_radius", "entity_condition": {"type": "apoli:entity_type", "entity_type": "minecraft:slime"}, "radius": 15}
            }
        },
        "shared_vision": {
            "type": "apoli:night_vision",
            "strength": 0.4
        },
        "spore_infection": {
            "type": "apoli:action_on_hit",
            "bientity_condition": {"type": "apoli:distance", "comparison": "<=", "compare_to": 3},
            "target_action": {"type": "apoli:apply_effect", "effect": {"effect": "minecraft:poison", "duration": 100, "amplifier": 1}},
            "cooldown": 200
        },
        "mycelium_heal": {
            "type": "apoli:action_over_time",
            "entity_action": {"type": "apoli:heal", "amount": 1.0},
            "interval": 40,
            "condition": {
                "type": "apoli:in_block",
                "block_condition": {"type": "apoli:in_tag", "tag": "minecraft:mycelium"}
            }
        },
        "biomass_from_flowers": {
            "type": "apoli:action_over_time",
            "entity_action": {
                "type": "apoli:and",
                "actions": [
                    {"type": "apoli:heal", "amount": 1.0},
                    {"type": "apoli:execute_command", "command": "title @s actionbar {\"text\":\"\\u00a7a\\u751f\\u7269\\u8d28\\u79ef\\u7d2f\\u4e2d...\", \"color\": \"green\"}"}
                ]
            },
            "interval": 60,
            "condition": {
                "type": "apoli:in_block_any",
                "blocks": ["minecraft:rose_bush", "minecraft:lilac", "minecraft:peony", "minecraft:sunflower", "minecraft:poppy", "minecraft:dandelion", "minecraft:blue_orchid", "minecraft:allium", "minecraft:azure_bluet", "minecraft:red_tulip", "minecraft:orange_tulip", "minecraft:white_tulip", "minecraft:pink_tulip", "minecraft:oxeye_daisy", "minecraft:cornflower", "minecraft:lily_of_the_valley", "minecraft:wither_rose"]
            }
        },
        "mimic_form": {
            "type": "apoli:toggle",
            "key": {"key": "key.origins.primary_active", "continuous": false},
            "active_by_default": false
        },
        "adaptive_resistance": {
            "type": "apoli:conditioned_attribute",
            "modifiers": [
                {
                    "name": "Adaptive resistance",
                    "attribute": "minecraft:generic.armor",
                    "value": 6.0,
                    "operation": "add_value"
                }
            ],
            "condition": {"type": "apoli:power_active", "power": "swarm_origins:mimic_form"}
        },
        "no_natural_armor": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "No natural armor",
                "attribute": "minecraft:generic.armor",
                "value": -4.0,
                "operation": "add_value"
            }
        },
        "life_drain": {
            "type": "apoli:action_on_hit",
            "bientity_condition": {"type": "apoli:distance", "comparison": "<=", "compare_to": 3},
            "self_action": {"type": "apoli:heal", "amount": 2.0},
            "target_action": {"type": "apoli:damage", "amount": 2.0, "source": "minecraft:magic"},
            "cooldown": 100
        },
        "parasitic_strength": {
            "type": "apoli:attribute",
            "modifier": {
                "name": "Parasitic strength",
                "attribute": "minecraft:generic.attack_damage",
                "value": 4.0,
                "operation": "add_value"
            }
        },
        "summon_parasites": {
            "type": "apoli:launch_projectile",
            "entity_type": "minecraft:slime",
            "tag": "{Size:0,CustomName:'{\"text\":\"\\u00a7c\\u5bc4\\u751f\\u866b\"}'}",
            "cooldown": 400,
            "count": 3,
            "speed": 0.5,
            "key": {"key": "key.origins.primary_active", "continuous": false}
        },
        "constant_hunger": {
            "type": "apoli:action_over_time",
            "entity_action": {"type": "apoli:apply_effect", "effect": {"effect": "minecraft:hunger", "duration": 40, "amplifier": 0}},
            "interval": 200
        },
        "regen_on_kill": {
            "type": "apoli:action_on_kill",
            "bientity_condition": {"type": "apoli:distance", "comparison": "<=", "compare_to": 5},
            "self_action": {"type": "apoli:heal", "amount": 4.0}
        }
    }
    
    for power_id, power_data in powers_data.items():
        with open(os.path.join(powers_dir, f"{power_id}.json"), "w", encoding="utf-8") as f:
            json.dump(power_data, f, ensure_ascii=False, indent=2)
    
    origin_layer = {
        "replace": false,
        "origins": [
            {"origin": "swarm_origins:larva", "icon": "minecraft:slime_ball", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:spitter", "icon": "minecraft:arrow", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:burrower", "icon": "minecraft:diamond_shovel", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:flyer", "icon": "minecraft:elytra", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:brood_mother", "icon": "minecraft:spawner", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:stalker", "icon": "minecraft:iron_sword", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:devourer", "icon": "minecraft:golden_apple", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:hivemind", "icon": "minecraft:ender_eye", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:spore_carrier", "icon": "minecraft:red_mushroom", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:changeling", "icon": "minecraft:spawn_egg", "condition": {"type": "apoli:or", "conditions": []}},
            {"origin": "swarm_origins:parasite_lord", "icon": "minecraft:nether_star", "condition": {"type": "apoli:or", "conditions": []}}
        ],
        "name": "\u866b\u65cf\u8d77\u6e90",
        "description": "\u9009\u62e9\u4f60\u7684\u866b\u65cf\u5f62\u6001",
        "order": 0,
        "missing_name": "\u672a\u9009\u62e9\u8d77\u6e90",
        "missing_description": "\u4f60\u8fd8\u6ca1\u6709\u9009\u62e9\u4f60\u7684\u866b\u65cf\u5f62\u6001\u3002"
    }
    
    layer_dir = os.path.join(dp_dir, "data", "origins", "origin_layers")
    os.makedirs(layer_dir, exist_ok=True)
    with open(os.path.join(layer_dir, "origin.json"), "w", encoding="utf-8") as f:
        json.dump(origin_layer, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] 虫族起源数据包已创建: 11个虫族起源, {len(powers_data)}个能力")
    return dp_dir

create_swarm_datapack()

print("\n[4/5] 配置options.txt - 启用中文和资源包...")
options_path = os.path.join(MC_DIR, "options.txt")
if os.path.exists(options_path):
    with open(options_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if line.startswith("lang:"):
            new_lines.append("lang:zh_cn")
        elif line.startswith("resourcePacks:"):
            new_lines.append('resourcePacks:["fabric","swarm_origins"]')
        else:
            new_lines.append(line)
    
    with open(options_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print("  [OK] options.txt 已更新: 中文语言 + 虫族资源包")
else:
    print("  [WARN] options.txt 不存在，将在游戏首次运行后配置")

print("\n[5/5] 统计最终模组数量...")
mod_files = [f for f in os.listdir(MODS_DIR) if f.endswith(".jar")]
print(f"  当前模组数量: {len(mod_files)}")
print(f"  模组列表:")
for mf in sorted(mod_files):
    print(f"    - {mf}")

print("\n" + "=" * 60)
print("  修复完成!")
print("  - assetIndex 已修复 (16 -> 12)")
print("  - 虫族起源数据包已创建 (11个起源)")
print("  - 中文语言已配置")
print("  - 模组已下载")
print("=" * 60)
