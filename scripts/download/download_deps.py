import urllib.request
import json
import os
import time
import urllib.parse

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\mods"

def get_mod_versions(slug):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps(["1.20.4"]),
        "loaders": json.dumps(["fabric"])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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
                    if fsize > 5000:
                        print(f"  [OK] {filename} ({fsize:,} bytes)")
                        return True
                    else:
                        os.remove(filepath)
                except Exception as e:
                    print(f"  [ERR] {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
    return False

MISSING_DEPS = [
    ("forgeconfigapiport", "ForgeConfigAPIPort - 配置API"),
    ("puzzles-lib", "PuzzlesLib - Puzzles依赖库"),
    ("library-ferret", "Library Ferret - 地牢依赖"),
    ("glitchcore", "GlitchCore - BOP依赖"),
    ("collective", "Collective - 通用依赖"),
    ("unilib", "UniLib - CraftPresence依赖"),
    ("balm-fabric", "Balm Fabric - Waystones依赖"),
    ("emi", "EMI - 物品管理器"),
    ("resourceful-lib", "ResourcefulLib - Enderman Overhaul依赖"),
    ("resourceful-config", "ResourcefulConfig - Enderman Overhaul依赖"),
    ("formations", "Formations - Nether结构依赖"),
    ("moogs-structure-utilities", "Moogs Structures - MNS依赖"),
    ("azurelib", "AzureLib - Origin Furs依赖"),
    ("supermartijn642-core-lib", "SuperMartijn642 Core - Trash Cans依赖"),
    ("origins-dietary-delights", "Origins Dietary Delights - OriginsTweaks依赖"),
]

print("=" * 60)
print("  下载缺失的依赖库")
print("=" * 60)

added = 0
failed = []
for slug, name in MISSING_DEPS:
    print(f"\n[{slug}] {name}")
    success = download_mod(slug)
    if success:
        added += 1
    else:
        failed.append(slug)
    time.sleep(0.3)

print(f"\n已下载: {added}")
print(f"失败: {len(failed)} - {failed}")

print("\n--- 移除有版本冲突的模组 ---")

REMOVE_CONFLICT = [
    "origins-plus-plus-2.4.jar",
]

for f in REMOVE_CONFLICT:
    fp = os.path.join(MODS_DIR, f)
    if os.path.exists(fp):
        os.remove(fp)
        print(f"  [DEL] {f}")

print("\n--- 下载Origins++兼容版本 ---")
opp_versions = get_mod_versions("origins-plus-plus")
if opp_versions:
    for v in opp_versions:
        vn = v.get("version_number", "")
        deps = v.get("dependencies", [])
        for dep in deps:
            if dep.get("project_id") == "origins" or "origins" in dep.get("slug", ""):
                dep_ver = dep.get("version_id", "")
                print(f"  Origins++ {vn} requires origins: {dep_ver}")
        for f in v.get("files", []):
            fn = f.get("filename", "")
            url = f.get("url", "")
            if url and fn.endswith(".jar"):
                fp = os.path.join(MODS_DIR, fn)
                if not os.path.exists(fp):
                    try:
                        print(f"  [DOWN] {fn}...")
                        urllib.request.urlretrieve(url, fp)
                        fsize = os.path.getsize(fp)
                        print(f"  [OK] {fn} ({fsize:,} bytes)")
                    except Exception as e:
                        print(f"  [ERR] {e}")
                break
        break

mod_count = len([f for f in os.listdir(MODS_DIR) if f.endswith(".jar")])
print(f"\n当前模组总数: {mod_count}")
