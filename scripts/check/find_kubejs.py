import urllib.request
import json
import os

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"

url = "https://api.modrinth.com/v2/project/kubejs/version"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

fabric_120 = []
for v in data:
    loaders = [l.lower() for l in v.get("loaders", [])]
    game_versions = v.get("game_versions", [])
    if "fabric" in loaders:
        for gv in game_versions:
            if gv.startswith("1.20"):
                fabric_120.append(v)
                break

print(f"Total KubeJS versions: {len(data)}")
print(f"Fabric 1.20.x versions: {len(fabric_120)}")
for v in fabric_120[:10]:
    vn = v.get("version_number", "N/A")
    gv = v.get("game_versions", [])
    files = v.get("files", [])
    print(f"  {vn} | {gv}")
    for f in files:
        fn = f.get("filename", "")
        fu = f.get("url", "")
        if "fabric" in fn.lower():
            print(f"    {fn}")
            print(f"    {fu}")

if not fabric_120:
    print("\nNo Fabric 1.20.x versions found on Modrinth!")
    print("KubeJS for Fabric 1.20.4 may need to be downloaded from CurseForge")
    print("Trying direct CurseForge CDN URLs...")
    
    cf_urls = [
        ("https://cdn.curseforge.com/api/v1/mods/238086/files/5284864/download", "kubejs-fabric-2004.2.0-build.25.jar"),
        ("https://cdn.curseforge.com/api/v1/mods/238086/files/5237425/download", "kubejs-fabric-2004.1.0-build.50.jar"),
    ]
    
    for url, filename in cf_urls:
        filepath = os.path.join(MODS_DIR, filename)
        if os.path.exists(filepath):
            print(f"  Already exists: {filename}")
            break
        try:
            print(f"  Trying: {url}")
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp = urllib.request.urlopen(req, timeout=30)
            content = resp.read()
            with open(filepath, "wb") as f:
                f.write(content)
            fsize = os.path.getsize(filepath)
            if fsize > 5000:
                print(f"  OK! {filename} ({fsize:,} bytes)")
                break
            else:
                os.remove(filepath)
                print(f"  Too small ({fsize} bytes), might be HTML redirect")
        except Exception as e:
            print(f"  Failed: {e}")
