import os
import json
import urllib.request
import urllib.parse
import hashlib

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, "versions")

def download_file(url, path, expected_sha1=""):
    if os.path.exists(path):
        if expected_sha1:
            sha1 = hashlib.sha1(open(path, "rb").read()).hexdigest()
            if sha1 == expected_sha1:
                print(f"  Already exists: {os.path.basename(path)}")
                return True
        else:
            print(f"  Already exists: {os.path.basename(path)}")
            return True

    try:
        print(f"  Downloading: {os.path.basename(path)}")
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        if expected_sha1:
            sha1 = hashlib.sha1(data).hexdigest()
            if sha1 != expected_sha1:
                print(f"  SHA1 mismatch!")
                os.remove(path)
                return False
        print(f"  Downloaded: {len(data)//1024}KB")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

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

def fix_missing_deps():
    print("=== Fixing missing dependencies ===")

    version_dir = os.path.join(VERSIONS_DIR, "真菌起源")
    mods_dir = os.path.join(version_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    missing_mods = {
        "glitchcore": {"version": "1.20.1", "loader": "forge"},
        "terrablender": {"version": "1.20.1", "loader": "forge"},
        "silentlib": {"version": "1.20.1", "loader": "forge"},
    }

    for slug, info in missing_mods.items():
        print(f"\nSearching {slug}...")
        result = search_modrinth_version(slug, info["version"], info["loader"])
        if result:
            dest = os.path.join(mods_dir, result["filename"])
            if download_file(result["url"], dest, result["sha1"]):
                print(f"  Placed: {result['filename']}")
        else:
            print(f"  NOT FOUND on Modrinth - trying alternative...")
            if slug == "silentlib":
                result = search_modrinth_version("silent-lib", info["version"], info["loader"])
                if result:
                    dest = os.path.join(mods_dir, result["filename"])
                    if download_file(result["url"], dest, result["sha1"]):
                        print(f"  Placed: {result['filename']}")

if __name__ == "__main__":
    fix_missing_deps()
    print("\nDone!")
