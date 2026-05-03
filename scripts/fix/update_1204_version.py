import json
import os
import shutil

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"

neoforge_json_path = os.path.join(MINECRAFT_DIR, "versions", "neoforge-20.4.237", "neoforge-20.4.237.json")
version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)

with open(neoforge_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["id"] = VERSION_NAME

json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated version JSON: {json_path}")
print(f"  MainClass: {data.get('mainClass')}")
print(f"  Libraries: {len(data.get('libraries', []))}")
print(f"  InheritsFrom: {data.get('inheritsFrom')}")

version_jar = os.path.join(version_dir, f"{VERSION_NAME}.jar")
if not os.path.exists(version_jar):
    base_jar = os.path.join(MINECRAFT_DIR, "versions", "1.20.4", "1.20.4.jar")
    if os.path.exists(base_jar):
        shutil.copy2(base_jar, version_jar)
        print(f"Copied base JAR to: {version_jar}")
    else:
        print(f"WARNING: Base JAR not found at {base_jar}")
else:
    print(f"Version JAR already exists: {version_jar}")

print("\nDone! Ready to test.")
