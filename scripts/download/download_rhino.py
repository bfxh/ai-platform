import os
import json
import urllib.request
import urllib.parse
import hashlib

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"

def search_modrinth_version(slug, game_version, loader):
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
            version = data[0]
            for f in version.get("files", []):
                if f.get("primary", False):
                    return {
                        "filename": f["filename"],
                        "url": f["url"],
                        "sha1": f.get("hashes", {}).get("sha1", ""),
                    }
            if version.get("files"):
                f = version["files"][0]
                return {
                    "filename": f["filename"],
                    "url": f["url"],
                    "sha1": f.get("hashes", {}).get("sha1", ""),
                }
    except Exception as e:
        print(f"  Error: {e}")
    return None

mods_dir = os.path.join(MINECRAFT_DIR, "versions", "我即是虫群-1.20.4", "mods")

print("Searching rhino for 1.20.4 neoforge...")
result = search_modrinth_version("rhino", "1.20.4", "neoforge")
if result:
    dest = os.path.join(mods_dir, result["filename"])
    if os.path.exists(dest):
        print(f"Already exists: {result['filename']}")
    else:
        print(f"Downloading: {result['filename']}")
        req = urllib.request.Request(result["url"], headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"Downloaded: {len(data)//1024}KB")
else:
    print("NOT FOUND on Modrinth!")

print("Done!")
