import urllib.request
import os

wrong = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods\rhino-2004.2.3-build.4.jar"
if os.path.exists(wrong):
    os.remove(wrong)
    print("Removed wrong version")

dest = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods\rhino-neoforge-2004.2.3-build.4.jar"

urls = [
    "https://maven.latvian.dev/releases/dev/latvian/mods/rhino-neoforge/2004.2.3-build.4/rhino-neoforge-2004.2.3-build.4.jar",
    "https://maven.latvian.dev/releases/dev/latvian/mods/rhino/2004.2.3-build.4/rhino-neoforge-2004.2.3-build.4.jar",
]

for url in urls:
    try:
        print(f"Trying: {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"Downloaded: {len(data)//1024}KB")
        break
    except Exception as e:
        print(f"Error: {e}")
else:
    print("All URLs failed. Trying Modrinth with different slug...")
    import json
    for slug in ["rhino", "rhino-kubejs"]:
        try:
            api_url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[\"1.20.4\"]&loaders=[\"neoforge\"]"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            if data:
                for f in data[0].get("files", []):
                    if f.get("primary", False) or True:
                        dl_url = f["url"]
                        filename = f["filename"]
                        print(f"Found on Modrinth: {filename}")
                        req2 = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req2, timeout=120) as resp2:
                            jar_data = resp2.read()
                        dest2 = os.path.join(os.path.dirname(dest), filename)
                        with open(dest2, "wb") as out:
                            out.write(jar_data)
                        print(f"Downloaded: {len(jar_data)//1024}KB")
                        break
                break
        except Exception as e:
            print(f"Modrinth {slug}: {e}")

print("Done!")
