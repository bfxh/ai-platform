import os
import json
import shutil

BASE = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4"
DP = os.path.join(BASE, "resourcepacks", "swarm_origins")
WORLD_DP = os.path.join(BASE, "saves", "新的世界", "datapacks", "swarm_origins")

def wj(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("[1/3] 完善盖亚生物质系统...")

heal_power = {
    "type": "origins:action_over_time",
    "entity_action": {
        "type": "origins:and",
        "actions": [
            {"type": "origins:heal", "amount": 1},
            {"type": "origins:change_resource", "resource": "swarm_origins:biomass_accumulate", "change": 1},
            {"type": "origins:execute_command", "command": "particle minecraft:happy_villager ~ ~1 ~ 0.5 0.5 0.5 0 3"}
        ]
    },
    "interval": 40,
    "condition": {
        "type": "origins:or",
        "conditions": [
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:in_tag", "tag": "minecraft:flowers"}},
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:in_tag", "tag": "minecraft:tall_flowers"}},
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:block", "block": "minecraft:rose_bush"}},
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:block", "block": "minecraft:lilac"}},
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:block", "block": "minecraft:peony"}},
            {"type": "origins:block_in_radius", "radius": 3, "block_condition": {"type": "origins:block", "block": "minecraft:sunflower"}},
        ]
    }
}
wj(os.path.join(DP, "data", "swarm_origins", "powers", "flower_heal.json"), heal_power)

biomass_power = {
    "type": "origins:resource",
    "min": 0,
    "max": 100,
    "start_value": 0,
    "min_action": {},
    "max_action": {
        "type": "origins:and",
        "actions": [
            {"type": "origins:execute_command", "command": "title @s actionbar {\"text\":\"\u00a7a\u00a7l\u751f\u7269\u8d28+1\uff01\u53ef\u7528\u4e8e\u5f3a\u5316\u81ea\u8eab\uff01\",\"color\":\"green\"}"},
            {"type": "origins:execute_command", "command": "particle minecraft:composter ~ ~1 ~ 1 1 1 0 30"},
            {"type": "origins:execute_command", "command": "playsound minecraft:entity.player.levelup master @s"},
            {"type": "origins:change_resource", "resource": "swarm_origins:biomass_accumulate", "change": -100}
        ]
    },
    "hud_render": {
        "should_render": True,
        "sprite_location": "origins:textures/gui/community/spider/resource_bar_01.png",
        "bar_index": 1,
        "bar_width": 64,
        "bar_height": 8
    }
}
wj(os.path.join(DP, "data", "swarm_origins", "powers", "biomass_accumulate.json"), biomass_power)

print("[2/3] 覆盖原有起源为不可选择...")

origins_to_hide = [
    ("origins", "arachnid"),
    ("origins", "blazeborn"),
    ("origins", "enderian"),
    ("origins", "phantom"),
    ("origins", "elytrian"),
    ("origins", "shulk"),
    ("origins", "avian"),
    ("origins", "feline"),
    ("origins", "merling"),
    ("origins-plus-plus", "gaia"),
    ("origins-plus-plus", "broodmother"),
    ("origins-plus-plus", "sporeling"),
    ("origins-plus-plus", "insect"),
    ("origins-plus-plus", "voidling/voidling"),
    ("origins-plus-plus", "blob"),
    ("origins-plus-plus", "withered_fox"),
    ("origins-plus-plus", "glacier"),
    ("origins-plus-plus", "ignisian"),
    ("origins-plus-plus", "shadow"),
    ("origins-plus-plus", "rat"),
    ("origins-plus-plus", "volcanic_dragon"),
    ("origins-plus-plus", "alien_axolotl"),
    ("origins-plus-plus", "fallen_angel"),
    ("origins-plus-plus", "warden"),
    ("origins-plus-plus", "giant"),
    ("toomanyorigins", "swarm"),
    ("toomanyorigins", "dragonborn"),
    ("toomanyorigins", "withered"),
    ("toomanyorigins", "hare"),
    ("toomanyorigins", "hisskin"),
]

for ns, oid in origins_to_hide:
    path = os.path.join(DP, "data", ns, "origins", f"{oid.split('/')[-1]}.json")
    override = {
        "replace": True,
        "unchoosable": True,
        "name": "\u00a78\u5df2\u866b\u65cf\u5316",
        "description": "\u00a77\u6b64\u8d77\u6e90\u5df2\u88ab\u866b\u65cf\u53d8\u5f62\u66ff\u4ee3\uff0c\u8bf7\u9009\u62e9\u5bf9\u5e94\u7684\u866b\u65cf\u53d8\u5f62\u7248\u672c\u3002",
        "icon": "minecraft:barrier",
        "impact": 0,
        "powers": []
    }
    wj(path, override)

print("[3/3] 同步到世界存档...")
if os.path.exists(WORLD_DP):
    shutil.rmtree(WORLD_DP)
shutil.copytree(DP, WORLD_DP)

print("\n" + "=" * 60)
print("  \u5b8c\u5584\u5b8c\u6210!")
print("=" * 60)
print(f"  \u8986\u76d6\u4e86 {len(origins_to_hide)} \u4e2a\u539f\u6709\u8d77\u6e90\u4e3a\u4e0d\u53ef\u9009\u62e9")
print(f"  \u76d6\u4e9a\u751f\u7269\u8d28\u7cfb\u7edf: \u82b1\u65c1\u6bcf\u56de\u8840\u4e00\u6b21+\u751f\u7269\u8d28\u8fdb\u5ea6+1, \u6ee1100\u65f6\u83b7\u5f971\u751f\u7269\u8d28")
print(f"  \u8d44\u6e90\u6761\u663e\u793a\u5728HUD\u4e0a")
