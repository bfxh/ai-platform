import json
import os

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"

version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)
json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("JVM arguments from version JSON:")
for arg in data.get("arguments", {}).get("jvm", []):
    if isinstance(arg, str):
        print(f"  {arg}")

print("\nGame arguments from version JSON:")
for arg in data.get("arguments", {}).get("game", []):
    if isinstance(arg, str):
        print(f"  {arg}")
