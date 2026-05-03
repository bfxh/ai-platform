import json
import os
import zipfile
import shutil

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"
NEOFORGE_VERSION = "20.4.237"

installer_path = os.path.join(MINECRAFT_DIR, f"neoforge-{NEOFORGE_VERSION}-installer.jar")
version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)

print(f"Extracting version JSON from NeoForge installer...")

if not os.path.exists(installer_path):
    print(f"ERROR: Installer not found at {installer_path}")
    exit(1)

with zipfile.ZipFile(installer_path, "r") as zf:
    print("Files in installer:")
    for name in zf.namelist():
        if "version" in name.lower() or "install" in name.lower() or "profile" in name.lower():
            print(f"  {name}")

    for target_name in ["version.json", "install_profile.json", "META-INF/neoforge/version.json"]:
        if target_name in zf.namelist():
            print(f"\nFound: {target_name}")
            data = zf.read(target_name)
            try:
                json_data = json.loads(data.decode("utf-8"))
                
                if target_name == "version.json":
                    json_data["id"] = VERSION_NAME
                    json_data["jar"] = VERSION_NAME
                    
                    json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"  Saved version JSON to: {json_path}")
                    print(f"  MainClass: {json_data.get('mainClass', 'N/A')}")
                    print(f"  Libraries: {len(json_data.get('libraries', []))}")
                    
                elif target_name == "install_profile.json":
                    print(f"  Install profile data:")
                    print(f"  - Version: {json_data.get('version', 'N/A')}")
                    print(f"  - Minecraft: {json_data.get('minecraft', 'N/A')}")
                    print(f"  - Libraries: {len(json_data.get('libraries', []))}")
                    print(f"  - Processor count: {len(json_data.get('processors', []))}")
                    
                    if "data" in json_data:
                        for key, val in json_data["data"].items():
                            print(f"  - Data {key}: {val}")
                    
            except json.JSONDecodeError:
                print(f"  Could not parse as JSON, first 200 chars: {data[:200]}")

print("\nDone!")
