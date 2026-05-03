import urllib.request
import os

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"

maven_urls = [
    "https://maven.latvian.dev/dev/latvian/mods/kubejs/kubejs-fabric/2004.1.0-build.50/kubejs-fabric-2004.1.0-build.50.jar",
    "https://maven.latvian.dev/dev/latvian/mods/kubejs/kubejs-fabric/2004.2.0-build.25/kubejs-fabric-2004.2.0-build.25.jar",
    "https://maven.latvian.dev/dev/latvian/mods/kubejs/kubejs-fabric/2004.7.0-build.26/kubejs-fabric-2004.7.0-build.26.jar",
]

for url in maven_urls:
    filename = url.split("/")[-1]
    filepath = os.path.join(MODS_DIR, filename)
    if os.path.exists(filepath):
        print(f"Already exists: {filename}")
        continue
    try:
        print(f"Trying: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read()
        with open(filepath, "wb") as f:
            f.write(content)
        fsize = os.path.getsize(filepath)
        if fsize > 5000:
            print(f"OK! {filename} ({fsize:,} bytes)")
            break
        else:
            os.remove(filepath)
            print(f"Too small ({fsize} bytes)")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"Error: {e}")

print("\nChecking if KubeJS is available...")
kubejs_found = any("kubejs" in f.lower() for f in os.listdir(MODS_DIR) if f.endswith(".jar"))
if kubejs_found:
    print("KubeJS is in the mods folder!")
else:
    print("KubeJS NOT found. It may not be available for Fabric 1.20.4.")
    print("The modpack will still work with Origins datapack for character selection.")
