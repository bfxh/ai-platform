import os
import json
import urllib.request
import urllib.parse

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群v2.0\mods"

def get_mod_info_from_jar(jar_path):
    try:
        import zipfile
        with zipfile.ZipFile(jar_path, 'r') as z:
            for name in z.namelist():
                if name.endswith('mcmod.info'):
                    with z.open(name) as f:
                        try:
                            data = json.loads(f.read().decode('utf-8', errors='replace'))
                            if isinstance(data, list) and data:
                                info = data[0]
                                return {
                                    'modid': info.get('modid', ''),
                                    'name': info.get('name', ''),
                                    'version': info.get('version', '')
                                }
                            elif isinstance(data, dict):
                                modlist = data.get('modList', [])
                                if modlist:
                                    info = modlist[0]
                                    return {
                                        'modid': info.get('modid', ''),
                                        'name': info.get('name', ''),
                                        'version': info.get('version', '')
                                    }
                        except:
                            pass
    except:
        pass
    return None

def search_modrinth(slug, game_version="1.12.2", loader="forge"):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps([game_version]),
        "loaders": json.dumps([loader])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data:
            return data[0]["version_number"]
    except:
        pass
    return None

KNOWN_SLUGS = {
    "SRParasites": "srparasites",
    "srpcotesia": "srpcotesia",
    "jei": "jei",
    "BiomesOPlenty": "biomes-o-plenty",
    "ScalingHealth": "scaling-health",
    "Quark": "quark",
    "geckolib": "geckolib",
    "SpartanWeaponry": "spartan-weaponry",
    "SpartanShields": "spartan-shields",
    "DynamicSurroundings": "dynamic-surroundings",
    "FTBQuests": "ftb-quests-forge",
    "FTBLib": "ftb-library-forge",
    "EntityCulling": "entityculling",
    "FallingTree": "fallingtree",
    "VeinMiner": "veinminer",
    "xaerominimap": "xaeros-minimap",
    "theoneprobe": "the-one-probe",
    "corpse": "corpse",
    "SilentLib": "silent-lib",
    "OreLib": "ore-lib",
    "EpicSiegeMod": "epic-siege-mod",
    "VanillaFix": "vanillafix",
    "BetterPlacement": "better-placement",
    "MouseTweaks": "mouse-tweaks",
    "FpsReducer": "fps-reducer",
    "I18nUpdateMod": "i18nupdatemod",
    "AttributeFix": "attributefix",
    "crafttweaker": "crafttweaker",
    "Neat": "neat",
    "ItemPhysic": "itemphysic",
    "phosphor": "phosphor",
    "foamfix": "foamfix-optimization-mod",
    "AutoRegLib": "autoreglib",
    "RedstoneFlux": "redstone-flux",
    "curios": "curios",
    "carry-on": "carry-on",
}

if __name__ == "__main__":
    print("=" * 60)
    print("  1.12.2 整合包更新兼容检查")
    print("=" * 60)

    jars = [f for f in os.listdir(MODS_DIR) if f.endswith('.jar') and not f.endswith('.disabled') and not f.endswith('.old')]

    print(f"\n  已启用mod数量: {len(jars)}")

    update_available = []
    not_on_modrinth = []

    for jar in jars:
        jar_path = os.path.join(MODS_DIR, jar)
        info = get_mod_info_from_jar(jar_path)

        mod_name = jar.replace('.jar', '')
        mod_version = ""
        slug = ""

        if info:
            mod_name = info.get('name', mod_name) or mod_name
            mod_version = info.get('version', '')
            slug = KNOWN_SLUGS.get(info.get('modid', ''), '')

        if not slug:
            for key, val in KNOWN_SLUGS.items():
                if key.lower() in jar.lower():
                    slug = val
                    break

        if slug:
            latest = search_modrinth(slug)
            if latest:
                status = "UP TO DATE" if mod_version and mod_version in latest else f"UPDATE: {latest}"
                print(f"  {mod_name}: {mod_version} -> {latest}")
                if mod_version and mod_version not in latest:
                    update_available.append((mod_name, mod_version, latest, slug))
            else:
                not_on_modrinth.append(mod_name)
        else:
            not_on_modrinth.append(mod_name)

    print(f"\n{'=' * 60}")
    print(f"  可更新: {len(update_available)}")
    print(f"  Modrinth上未找到: {len(not_on_modrinth)}")
    print(f"{'=' * 60}")

    if update_available:
        print("\n  可更新的mod:")
        for name, old, new, slug in update_available:
            print(f"    {name}: {old} -> {new}")

    if not_on_modrinth:
        print(f"\n  Modrinth上未找到的mod ({len(not_on_modrinth)}):")
        for name in not_on_modrinth[:20]:
            print(f"    {name}")
