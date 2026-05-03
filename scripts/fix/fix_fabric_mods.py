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
        print(f"  ERR: {e}")
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

SLUG_FIXES = {
    "apoli": ["apoli", "apoli-fabric"],
    "calio": ["calio", "calio-fabric"],
    "kubejs": ["kubejs"],
    "rhino": ["rhino"],
    "curios": ["curios", "curios-fabric", "cullions"],
    "farmers-delight": ["farmers-delight", "farmers-delight-fabric", "farmersdelight"],
    "croptopia": ["croptopia", "croptopia-fabric"],
    "botania": ["botania", "botania-fabric"],
    "aether": ["aether", "the-aether", "aether-fabric"],
    "sophisticated-backpacks": ["sophisticated-backpacks", "sophisticated-backpacks-fabric"],
    "sophisticated-core": ["sophisticated-core", "sophisticated-core-fabric"],
    "sophisticated-storage": ["sophisticated-storage", "sophisticated-storage-fabric"],
    "vampirism": ["vampirism", "vampirism-fabric"],
    "mowzies-mobs": ["mowzies-mobs", "mowzies-mobs-fabric"],
    "alex-mobs": ["alex-mobs", "alex-mobs-fabric"],
    "twilight-forest": ["twilight-forest", "the-twilight-forest"],
    "cataclysm": ["cataclysm", "cataclysm-fabric", "lendercataclysm"],
    "apotheosis": ["apotheosis", "apotheosis-fabric"],
    "placebo": ["placebo", "placebo-fabric"],
    "iron-spellbooks": ["iron-spellbooks", "irons-spells-n-spellbooks", "irons-spells"],
    "ars-nouveau": ["ars-nouveau", "ars-nouveau-fabric"],
    "hexerei": ["hexerei", "hexerei-fabric"],
    "spectrum": ["spectrum", "spectrum-fabric"],
    "3d-skin-layers": ["3d-skin-layers", "skin-layers-3d"],
    "damage-number": ["damage-number", "damage-numbers"],
    "dynamic-crosshair": ["dynamic-crosshair", "dynamiccrosshair"],
    "prism": ["prism", "prism-lib"],
    "bookshelf": ["bookshelf", "bookshelf-lib"],
    "spartan-weaponry": ["spartan-weaponry", "spartan-weaponry-fabric"],
    "extra-origins": ["extra-origins", "extraorigins"],
    "mob-origins": ["mob-origins", "moborigins"],
    "too-many-origins": ["too-many-origins", "toomanyorigins"],
    "creeper-overhaul": ["creeper-overhaul", "creeperoverhaul"],
    "naturalist": ["naturalist", "naturalist-fabric"],
    "ecologics": ["ecologics", "ecologics-fabric"],
    "graveyard": ["the-graveyard", "graveyard"],
    "the-bumblezone": ["the-bumblezone", "bumblezone"],
    "when-dungeons-arise": ["when-dungeons-arise", "dungeons-arise"],
    "repurposed-structures": ["repurposed-structures", "repurposed-structures-fabric"],
    "dungeon-now-loading": ["dungeon-now-loading", "dnl"],
    "spice-of-life": ["spice-of-life", "spice-of-life-fabric", "solcarrot"],
    "brewin-and-chewin": ["brewin-and-chewin", "brewin-and-chewin-fabric"],
    "ferritecore": ["ferrite-core", "ferritecore"],
    "scaling-health": ["scaling-health", "scaling-health-fabric"],
    "silent-lib": ["silent-lib", "silent-lib-fabric"],
    "shoulder-surfing": ["shoulder-surfing", "shoulder-surfing-fabric"],
    "cosmetic-armor-reworked": ["cosmetic-armor-reworked", "cosmetic-armor-fabric"],
    "imblocker": ["imblocker", "imblocker-fabric"],
    "quark": ["quark", "quark-fabric"],
}

if __name__ == "__main__":
    print("=" * 60)
    print("  修复缺失的Fabric 1.20.4 mods")
    print("=" * 60)

    success = 0
    still_missing = []

    for original_slug, alt_slugs in SLUG_FIXES.items():
        found = False
        for slug in alt_slugs:
            result = search_modrinth(slug)
            if result:
                dest = os.path.join(MODS_DIR, result["filename"])
                if download_file(result["url"], dest):
                    success += 1
                    found = True
                    break
        if not found:
            still_missing.append(original_slug)
            print(f"  MISS: {original_slug}")
        time.sleep(0.3)

    print(f"\n  修复完成: {success} 成功, {len(still_missing)} 仍缺失")
    if still_missing:
        print(f"  仍缺失: {', '.join(still_missing)}")

    jar_count = len([f for f in os.listdir(MODS_DIR) if f.endswith('.jar')])
    print(f"\n  当前总mod数: {jar_count}")
