import json
import os

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"

version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)
json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Version JSON analysis:")
print(f"  ID: {data.get('id')}")
print(f"  MainClass: {data.get('mainClass')}")
print(f"  InheritsFrom: {data.get('inheritsFrom')}")

print(f"\nLibraries in version JSON: {len(data.get('libraries', []))}")

missing_libs = []
for lib in data.get("libraries", []):
    name = lib.get("name", "")
    downloads = lib.get("downloads", {})
    if "artifact" in downloads:
        path = downloads["artifact"].get("path", "")
        if path:
            full_path = os.path.join(MINECRAFT_DIR, "libraries", path)
            if not os.path.exists(full_path):
                missing_libs.append((name, path))
            else:
                pass
    else:
        parts = name.split(":")
        if len(parts) >= 3:
            group = parts[0].replace(".", "/")
            artifact = parts[1]
            version = parts[2]
            classifier = parts[3] if len(parts) > 3 and "@" not in parts[3] else None
            if classifier:
                filename = f"{artifact}-{version}-{classifier}.jar"
            else:
                filename = f"{artifact}-{version}.jar"
            path = os.path.join(group, artifact, version, filename)
            full_path = os.path.join(MINECRAFT_DIR, "libraries", path)
            if not os.path.exists(full_path):
                missing_libs.append((name, path))

print(f"\nMissing libraries: {len(missing_libs)}")
if missing_libs:
    for name, path in missing_libs[:10]:
        print(f"  MISSING: {name}")
        print(f"    Path: {path}")

print(f"\nChecking key libraries:")

key_libs = [
    "net.neoforged.fancymodloader:earlydisplay:2.0.17@jar",
    "net.neoforged.fancymodloader:loader:2.0.17@jar",
    "net.neoforged.fancymodloader:spi:2.0.17@jar",
    "cpw.mods:modlauncher:10.0.9@jar",
    "cpw.mods:securejarhandler:2.1.24@jar",
]

for lib_name in key_libs:
    parts = lib_name.split(":")
    group = parts[0].replace(".", "/")
    artifact = parts[1]
    version = parts[2]
    classifier = parts[3] if len(parts) > 3 and "@" not in parts[3] else None
    if classifier:
        filename = f"{artifact}-{version}-{classifier}.jar"
    else:
        filename = f"{artifact}-{version}.jar"
    path = os.path.join(group, artifact, version, filename)
    full_path = os.path.join(MINECRAFT_DIR, "libraries", path)
    status = "OK" if os.path.exists(full_path) else "MISSING"
    print(f"  [{status}] {lib_name}")
    print(f"         {full_path}")
