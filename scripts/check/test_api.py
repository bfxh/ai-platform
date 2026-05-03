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
    except Exception as e:
        print(f"  API error for {slug}: {e}")
        return None

def download_from_version(slug, name):
    versions = get_mod_versions(slug)
    if not versions:
        print(f"  No versions found for {slug}")
        return False
    for v in versions[:3]:
        for f in v.get("files", []):
            filename = f.get("filename", "")
            url = f.get("url", "")
            primary = f.get("primary", True)
            if url and filename.endswith(".jar") and primary:
                filepath = os.path.join(MODS_DIR, filename)
                if os.path.exists(filepath):
                    print(f"  [SKIP] {filename} already exists")
                    return True
                try:
                    print(f"  [DOWN] {filename}...")
                    urllib.request.urlretrieve(url, filepath)
                    fsize = os.path.getsize(filepath)
                    if fsize < 1000:
                        print(f"  [ERR] File too small ({fsize} bytes), removing")
                        os.remove(filepath)
                        continue
                    print(f"  [OK] {filename} ({fsize:,} bytes)")
                    return True
                except Exception as e:
                    print(f"  [ERR] Download failed: {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
    return False

print("Testing API with known mods...")
test_slugs = ["kubejs", "trinkets", "bosses-of-mass-destruction", "betterend", "betternether"]
for slug in test_slugs:
    print(f"\n--- {slug} ---")
    versions = get_mod_versions(slug)
    if versions:
        print(f"  Found {len(versions)} versions")
        v = versions[0]
        print(f"  Version: {v.get('version_number', 'N/A')}")
        for f in v.get("files", []):
            print(f"  File: {f.get('filename', 'N/A')} (primary: {f.get('primary', False)})")
    else:
        print(f"  No versions found")
    time.sleep(0.3)
