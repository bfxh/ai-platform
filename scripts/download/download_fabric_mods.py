import urllib.request
import json
import os
import time
import urllib.parse

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"

def get_mod_versions(slug):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps(["1.20.4"]),
        "loaders": json.dumps(["fabric"])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data
    except:
        return None

def download_mod(slug):
    versions = get_mod_versions(slug)
    if not versions:
        return False
    for v in versions[:3]:
        for f in v.get("files", []):
            filename = f.get("filename", "")
            url = f.get("url", "")
            primary = f.get("primary", True)
            if url and filename.endswith(".jar") and primary:
                filepath = os.path.join(MODS_DIR, filename)
                if os.path.exists(filepath):
                    print(f"  [SKIP] {filename}")
                    return True
                try:
                    print(f"  [DOWN] {filename}...")
                    urllib.request.urlretrieve(url, filepath)
                    fsize = os.path.getsize(filepath)
                    if fsize < 1000:
                        os.remove(filepath)
                        continue
                    print(f"  [OK] {filename} ({fsize:,} bytes)")
                    return True
                except Exception as e:
                    print(f"  [ERR] {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
    return False

existing = set()
if os.path.exists(MODS_DIR):
    for f in os.listdir(MODS_DIR):
        if f.endswith(".jar"):
            existing.add(f.lower())

def already_have(slug):
    s = slug.lower().replace("-", "").replace("_", "")
    for jar in existing:
        j = jar.lower().replace("-", "").replace("_", "").replace(" ", "")
        if s in j:
            return True
    return False

MODS_TO_DOWNLOAD = [
    ("trinkets", "Trinkets - 饰品栏(Fabric版Curios替代)"),
    ("betterend", "BetterEnd - 更好的末地"),
    ("betternether", "BetterNether - 更好的下界"),
    ("incendium", "Incendium - 下界增强"),
    ("nullscape", "Nullscape - 末地增强"),
    ("dungeons-and-taverns", "Dungeons and Taverns - 地牢与酒馆"),
    ("toms-storage", "Tom's Simple Storage - 简易存储"),
    ("endrem", "End Remastered - 末影重制"),
    ("true-ending", "True Ending - 末影龙重做"),
    ("enchanting-infuser", "Enchanting Infuser - 附魔灌注器"),
    ("grind-enchantments", "Grind Enchantments - 研磨附魔"),
    ("more-armor-trims", "More Armor Trims - 更多盔甲纹饰"),
    ("azurelib-armor", "AzureLib Armor - 盔甲库"),
    ("detail-armor-bar", "Detail Armor Bar - 详细护甲条"),
    ("weaponmaster", "YDM's Weapon Master - 武器大师"),
    ("spellbound-weapons", "Spellbound Weapons - 魔法武器"),
    ("basicweapons", "Basic Weapons - 基础武器"),
    ("fantasy_weapons", "Fantasy Weapons - 奇幻武器"),
    ("more-mob-variants", "More Mob Variants - 更多生物变种"),
    ("mob-lassos", "Mob Lassos - 生物套索"),
    ("caracal_mob", "Caracal - 狞猫"),
    ("just-mob-heads", "Just Mob Heads - 生物头颅"),
    ("mob-captains", "Mob Captains - 生物队长"),
    ("more-mobs", "More Mobs - 更多生物"),
    ("3d-placeable-food", "3D Placeable Food - 3D食物"),
    ("foodeffecttooltips", "Food Effect Tooltips - 食物效果提示"),
    ("golden-foods", "Golden Foods - 金色食物"),
    ("storage-delight", "Storage Delight - 存储乐事"),
    ("nether-chested", "Nether Chested - 下界箱子"),
    ("formations-nether", "Formations Nether - 下界结构"),
    ("mns-moogs-nether-structures", "MNS - 下界结构"),
    ("amplified-nether", "Amplified Nether - 放大下界"),
    ("mes-moogs-end-structures", "MES - 末地结构"),
    ("better-end-sky", "Better End Sky - 更好末地天空"),
    ("bigger-better-end-cities", "Bigger Better End Cities - 更大末地城"),
    ("medieval-buildings-end-edition", "Medieval Buildings End - 中世纪末地"),
    ("structory-towers", "Structory Towers - 结构塔"),
    ("structory", "Structory - 结构"),
    ("contagion", "Contagion - 丧尸感染"),
    ("infection-overwritten", "Infection Overwritten - 感染覆写"),
    ("party-spores", "Party Spores - 孢子装饰"),
    ("rpg-origins", "RPG Origins - RPG起源"),
    ("originstweaks", "OriginsTweaks - 起源调整"),
    ("origins-player-scale", "Origins Player Scale - 起源体型"),
    ("origin-furs", "Origin Furs - 起源皮毛"),
    ("paradise-lost", "Paradise Lost - 失乐园(天境替代)"),
    ("aetherial-islands", "Aetherial Islands - 天空岛屿"),
    ("dragon-drops-elytra", "Dragon Drops Elytra - 龙掉鞘翅"),
    ("edf-remastered", "Ender Dragon Fight Remastered - 末影龙重制"),
    ("axes-are-weapons", "Axes Are Weapons - 斧是武器"),
    ("mob-sunscreen", "Mob Sunscreen - 生物防晒"),
    ("armor-statues", "Armor Statues - 盔甲架"),
    ("armor-chroma-for-fabric", "Armor Chroma - 盔甲色彩"),
    ("armor-stand-arms", "Armor Stand Arms - 盔甲架手臂"),
    ("horse-armor-stand", "Horse Armor Stand - 马铠架"),
    ("floral-enchantment", "Floral Enchantment - 花卉附魔"),
    ("sorted-enchantments", "Sorted Enchantments - 排序附魔"),
    ("biome_particle_weather", "Biome Particle Weather - 生物群系天气"),
    ("biome-spawn-point", "Biome Spawn Point - 群系出生点"),
    ("biome-moss", "Biome Moss - 群系苔藓"),
    ("biome-golems", "Biome Golems - 群系傀儡"),
    ("biome-dither", "Biome Dither - 群系过渡"),
    ("botany-trees", "Botany Trees - 植物树"),
    ("magic-mirror", "Magic Mirror - 魔法镜"),
    ("dungeons-plus", "Dungeons+ - 地牢+"),
    ("awesome-dungeon-edition-ocean", "Awesome Dungeon Ocean - 海洋地牢"),
    ("fishingparadise", "Fishing Paradise - 钓鱼天堂"),
    ("elytra_trinket", "Elytra Trinket - 鞘翅饰品"),
    ("usefulfood-reborn", "UsefulFood Reborn - 实用食物"),
    ("volcanic-dragon-origin", "Volcanic Dragon Origin - 火山龙起源"),
    ("extra-trinkets", "Extra Trinkets - 额外饰品"),
    ("techreborn", "Tech Reborn - 科技重生"),
    ("daycounter", "Day Counter - 天数计数器"),
    ("bbrb", "Better Biome Reblend - 更好群系混合"),
    ("when-dungeons-arise-seven-seas", "When Dungeons Arise: Seven Seas - 海洋地牢"),
    ("dungeons-and-taverns-stronghold-overhaul", "Dungeons Taverns Stronghold - 要塞重做"),
    ("dungeons-and-taverns-swamp-hut-overhaul", "Dungeons Taverns Swamp Hut - 沼泽小屋"),
    ("epic-dungeons-a-roguelike-minecraft", "Epic Dungeons Roguelike - 史诗地牢"),
    ("nether-portal-spread", "Nether Portal Spread - 下界传送门扩散"),
    ("emized-botany-pots", "EMIzed Botany Pots - EMI植物盆"),
    ("botany-pots-ore-planting", "Botany Pots Ore Planting - 矿物种植"),
    ("terralith-biome-saplings", "Custom Biome Saplings - 群系树苗"),
    ("heaven-dimension-fabric", "Heaven Dimension - 天堂维度"),
    ("pocket-dimension", "Pocket Dimension - 口袋维度"),
]

print("=" * 60)
print("  Fabric 1.20.4 Mod Downloader v2")
print(f"  Current mods: {len(existing)}")
print("=" * 60)

added = 0
skipped = 0
failed = 0
failed_list = []

for slug, name in MODS_TO_DOWNLOAD:
    if already_have(slug):
        print(f"[SKIP] {name} - already exists")
        skipped += 1
        continue
    print(f"\n[{slug}] {name}")
    success = download_mod(slug)
    if success:
        added += 1
    else:
        failed += 1
        failed_list.append(slug)
    time.sleep(0.3)

print("\n" + "=" * 60)
print(f"  Added: {added}")
print(f"  Skipped: {skipped}")
print(f"  Failed: {failed}")
if failed_list:
    print(f"  Failed slugs: {failed_list}")
final_count = len([f for f in os.listdir(MODS_DIR) if f.endswith(".jar")])
print(f"  Total mods now: {final_count}")
print("=" * 60)

print("\n[INFO] Downloading KubeJS from Maven...")
kubejs_url = "https://maven.latvian.dev/dev/latvian/mods/kubejs/kubejs-fabric/2004.2.0-build.25/kubejs-fabric-2004.2.0-build.25.jar"
kubejs_path = os.path.join(MODS_DIR, "kubejs-fabric-2004.2.0-build.25.jar")
if not os.path.exists(kubejs_path):
    try:
        print(f"  [DOWN] kubejs-fabric from Maven...")
        urllib.request.urlretrieve(kubejs_url, kubejs_path)
        fsize = os.path.getsize(kubejs_path)
        if fsize < 1000:
            os.remove(kubejs_path)
            print(f"  [FAIL] KubeJS file too small, trying alternative...")
            kubejs_url2 = "https://maven.latvian.dev/dev/latvian/mods/kubejs/kubejs-fabric/2004.1.0-build.50/kubejs-fabric-2004.1.0-build.50.jar"
            kubejs_path2 = os.path.join(MODS_DIR, "kubejs-fabric-2004.1.0-build.50.jar")
            urllib.request.urlretrieve(kubejs_url2, kubejs_path2)
            fsize2 = os.path.getsize(kubejs_path2)
            print(f"  [OK] KubeJS downloaded ({fsize2:,} bytes)")
        else:
            print(f"  [OK] KubeJS downloaded ({fsize:,} bytes)")
    except Exception as e:
        print(f"  [ERR] KubeJS Maven download failed: {e}")
        print(f"  Trying GitHub releases...")
        try:
            gh_url = "https://github.com/KubeJS-Mods/KubeJS/releases/download/2004.2.0-build.25/kubejs-fabric-2004.2.0-build.25.jar"
            urllib.request.urlretrieve(gh_url, kubejs_path)
            fsize = os.path.getsize(kubejs_path)
            print(f"  [OK] KubeJS from GitHub ({fsize:,} bytes)")
        except Exception as e2:
            print(f"  [ERR] GitHub also failed: {e2}")
else:
    print(f"  [SKIP] KubeJS already exists")

final_count = len([f for f in os.listdir(MODS_DIR) if f.endswith(".jar")])
print(f"\n  FINAL TOTAL: {final_count} mods")
