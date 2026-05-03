import urllib.request
import hashlib
import os
import json
import shutil

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群v2.0"

version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)
json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

game_patch = None
for patch in data.get("patches", []):
    if patch.get("id") == "game":
        game_patch = patch
        break

if not game_patch:
    print("ERROR: No game patch found!")
    exit(1)

downloads = game_patch.get("downloads", {})
client_download = downloads.get("client", {})

url = client_download.get("url", "")
sha1 = client_download.get("sha1", "")
size = client_download.get("size", 0)

print(f"Original Minecraft 1.12.2 JAR:")
print(f"  URL: {url}")
print(f"  SHA1: {sha1}")
print(f"  Size: {size}")

if not url:
    url = "https://piston-data.mojang.com/v1/objects/953bcdb9e3b3a0e4b2803533288a665a6a7c7e9a/server.jar"
    print(f"  Using fallback URL")

target_jar = os.path.join(version_dir, f"{VERSION_NAME}.jar")
backup_jar = os.path.join(version_dir, f"{VERSION_NAME}.jar.backup")

if os.path.exists(backup_jar):
    print(f"Backup already exists: {backup_jar}")
else:
    shutil.copy2(target_jar, backup_jar)
    print(f"Backed up current JAR to: {backup_jar}")

print(f"\nDownloading original Minecraft 1.12.2 JAR...")

try:
    req = urllib.request.Request(url, headers={"User-Agent": "MinecraftLauncher/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data_bytes = resp.read()

    print(f"Downloaded: {len(data_bytes)} bytes")

    if sha1:
        actual_sha1 = hashlib.sha1(data_bytes).hexdigest()
        if actual_sha1 == sha1:
            print(f"SHA1 verified: {actual_sha1}")
        else:
            print(f"SHA1 mismatch! Expected: {sha1}, Got: {actual_sha1}")
            print("NOT replacing JAR due to SHA1 mismatch")
            exit(1)

    with open(target_jar, "wb") as f:
        f.write(data_bytes)

    print(f"Replaced: {target_jar}")
    print(f"New size: {len(data_bytes)//1024}KB")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
