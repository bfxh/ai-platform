import urllib.request
import json
import urllib.parse
import os

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"

params = urllib.parse.urlencode({
    "game_versions": json.dumps(["1.20.4"]),
    "loaders": json.dumps(["fabric"])
})
url = f"https://api.modrinth.com/v2/project/kubejs/version?{params}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print(f"Found {len(data)} versions for KubeJS Fabric 1.20.4")
    for v in data[:5]:
        print(f"  {v['version_number']}")
        for f in v.get("files", []):
            print(f"    {f['filename']} - {f.get('url', 'N/A')[:80]}")
except Exception as e:
    print(f"Error: {e}")
    print("KubeJS may not be on Modrinth for Fabric 1.20.4")
    print("Trying CurseForge API...")

    search_url = "https://api.curseforge.com/v1/mods/search?gameId=432&searchFilter=kubejs&modLoaderType=4&gameVersion=1.20.4"
    print(f"Note: CurseForge requires API key, trying direct download...")

    kubejs_urls = [
        "https://mediafilez.forgecdn.net/files/5284/864/kubejs-fabric-2004.2.0-build.25.jar",
        "https://mediafilez.forgecdn.net/files/5237/425/kubejs-fabric-2004.1.0-build.50.jar",
        "https://edge.forgecdn.net/files/5284/864/kubejs-fabric-2004.2.0-build.25.jar",
        "https://edge.forgecdn.net/files/5237/425/kubejs-fabric-2004.1.0-build.50.jar",
    ]

    for url in kubejs_urls:
        filename = url.split("/")[-1]
        filepath = os.path.join(MODS_DIR, filename)
        if os.path.exists(filepath):
            print(f"  Already exists: {filename}")
            break
        try:
            print(f"  Trying: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=30)
            with open(filepath, "wb") as f:
                f.write(resp.read())
            fsize = os.path.getsize(filepath)
            if fsize > 1000:
                print(f"  OK! Downloaded {filename} ({fsize:,} bytes)")
                break
            else:
                os.remove(filepath)
                print(f"  File too small, removing")
        except Exception as e2:
            print(f"  Failed: {e2}")
