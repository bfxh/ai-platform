import os
import json
import urllib.request
import urllib.parse
import hashlib
import time

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
MODS_DIR = os.path.join(MINECRAFT_DIR, "versions", "我即是虫群-1.20.4", "mods")

def download_file(url, path):
    if os.path.exists(path):
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        print(f"  + {os.path.basename(path)} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  ERR {os.path.basename(path)}: {e}")
        return False

def search_modrinth(slug, game_version="1.20.4", loader="fabric"):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps([game_version]),
        "loaders": json.dumps([loader])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if data:
            for f in data[0].get("files", []):
                if f.get("primary", False):
                    return {"filename": f["filename"], "url": f["url"]}
            if data[0].get("files"):
                f = data[0]["files"][0]
                return {"filename": f["filename"], "url": f["url"]}
    except:
        pass
    return None

EXTRA_MODS = [
    ("calio", "Calio - Origins依赖"),
    ("playerabilitylib", "PAL - Origins依赖"),
    ("cardinal-components-api", "Cardinal Components API"),
    ("modmenu", "Mod Menu - 模组菜单"),
    ("roughly-enough-items", "REI - 配方查看(备用)"),
    ("roughly-enough-loot-tables", "REI Loot Tables"),
    ("better-fps", "Better FPS"),
    ("clumps", "Clumps - 经验球合并"),
    ("fast-furnace-for-fabric", "Fast Furnace"),
    ("ferritecore", "FerriteCore - 内存优化"),
    ("lithium", "Lithium - 逻辑优化"),
    ("starlight", "Starlight - 光照优化"),
    ("noisium", "Noisium - 世界生成优化"),
    ("netherportalfix", "Nether Portal Fix"),
    ("enchanting-table", "Enchanting Table"),
    ("darker-depths", "Darker Depths"),
    ("caverns-and-chasms", "Caverns and Chasms"),
    ("yungs-better-ocean-monuments", "YUNG's Better Ocean Monuments"),
    ("yungs-better-desert-temples", "YUNG's Better Desert Temples"),
    ("yungs-better-nether-fortresses", "YUNG's Better Nether Fortresses"),
    ("yungs-better-end-island", "YUNG's Better End Island"),
    ("the-twilight-forest", "Twilight Forest"),
    ("botania-fabric", "Botania Fabric"),
    ("farmers-delight-fabric", "Farmer's Delight Fabric"),
    ("curios-fabric", "Curios Fabric"),
    ("skin-layers-3d", "3D Skin Layers"),
    ("damage-tilt", "Damage Tilt"),
    ("better-third-person", "Better Third Person"),
    ("not-enough-crashes", "Not Enough Crashes"),
    ("farsight", "Farsight"),
    ("balm-fabric", "Balm Fabric"),
    ("cloth-config", "Cloth Config"),
    ("craftpresence", "CraftPresence"),
    ("wthit", "WTHIT - 信息显示"),
    ("badpackets", "Bad Packets"),
    ("architectury", "Architectury"),
    ("indium", "Indium"),
    ("sodium-extra", "Sodium Extra"),
    ("reeses-sodium-options", "Reese's Sodium Options"),
    ("phosphor", "Phosphor"),
    ("dashloader", "DashLoader"),
    ("enhanced-block-entities", "Enhanced Block Entities"),
    ("animatica", "Animatica"),
    ("puzzle", "Puzzle"),
    ("entitytexturefeatures", "Entity Texture Features"),
    ("lambdynamiclights", "LambDynamicLights"),
    ("cull-leaves", "Cull Leaves"),
    ("moreculling", "More Culling"),
    ("fabric-language-kotlin", "Fabric Language Kotlin"),
    ("roughly-enough-items", "REI"),
    ("default-options", "Default Options"),
    ("better-mount-hud", "Better Mount HUD"),
    ("cameraoverhaul", "Camera Overhaul"),
    ("better-weather", "Better Weather"),
    ("cave-dust", "Cave Dust"),
    ("ambient-sounds", "Ambient Sounds"),
    ("sound-physics-remastered", "Sound Physics Remastered"),
    ("presence-footsteps", "Presence Footsteps"),
    ("sodium-shadowy-path-blocks", "Sodium Shadowy Path Blocks"),
    ("sodium-options-mod-compat", "Sodium Options Mod Compat"),
    ("drip-sounds", "Drip Sounds"),
]

if __name__ == "__main__":
    print("=" * 60)
    print("  补充Fabric 1.20.4 mods")
    print("=" * 60)

    success = 0
    fail = 0

    for slug, name in EXTRA_MODS:
        result = search_modrinth(slug)
        if result:
            dest = os.path.join(MODS_DIR, result["filename"])
            if download_file(result["url"], dest):
                success += 1
        else:
            print(f"  MISS: {name} ({slug})")
            fail += 1
        time.sleep(0.3)

    print(f"\n  补充完成: {success} 成功, {fail} 失败")

    jar_count = len([f for f in os.listdir(MODS_DIR) if f.endswith('.jar')])
    print(f"  当前总mod数: {jar_count}")

    print("\n下载KubeJS Fabric...")
    kubejs_url = "https://maven.latvian.dev/releases/dev/latvian/mods/kubejs-fabric/2004.7.0-build.26/kubejs-fabric-2004.7.0-build.26.jar"
    rhino_url = "https://maven.latvian.dev/releases/dev/latvian/mods/rhino/2004.2.3-build.4/rhino-2004.2.3-build.4.jar"

    for url in [kubejs_url, rhino_url]:
        filename = url.split("/")[-1]
        dest = os.path.join(MODS_DIR, filename)
        if download_file(url, dest):
            success += 1

    jar_count = len([f for f in os.listdir(MODS_DIR) if f.endswith('.jar')])
    print(f"\n  最终总mod数: {jar_count}")
