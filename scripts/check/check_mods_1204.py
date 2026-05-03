import urllib.request
import json

def check_mod(slug, game_version="1.20.4", loader="neoforge"):
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
            v = data[0]
            return {
                "slug": slug,
                "version": v["version_number"],
                "filename": v["files"][0]["filename"] if v.get("files") else "N/A",
                "available": True
            }
        return {"slug": slug, "available": False}
    except Exception as e:
        return {"slug": slug, "available": False, "error": str(e)}

import urllib.parse

mods_to_check = [
    "origins", "apoli", "pehkui",
    "origins-forge", "apoli-forge",
    "kubejs", "rhino",
    "jei", "appleskin", "journeymap",
    "curios", "geckolib", "architectury-api",
    "cloth-config", "entityculling", "ferrite-core",
    "mouse-tweaks", "carry-on", "embeddium",
    "modernfix", "effective",
    "vampirism", "mowzies-mobs",
    "spore", "srparasites", "infection",
    "biomes-o-plenty", "scaling-health",
    "patchouli", "neoforge",
]

print("=" * 70)
print(f"  Modrinth 1.20.4 NeoForge 兼容性检查")
print("=" * 70)

available = []
unavailable = []

for slug in mods_to_check:
    result = check_mod(slug)
    status = "OK" if result.get("available") else "MISSING"
    if result.get("available"):
        available.append(slug)
        print(f"  [{status}] {slug}: {result.get('version', 'N/A')}")
    else:
        unavailable.append(slug)
        err = result.get("error", "")
        print(f"  [{status}] {slug}" + (f" ({err})" if err else ""))

print(f"\n  可用: {len(available)}, 不可用: {len(unavailable)}")
print(f"  不可用列表: {', '.join(unavailable)}")
