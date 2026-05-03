import json
import os

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"

version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)
json_path = os.path.join(version_dir, f"{VERSION_NAME}.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

lib_dir = os.path.join(MINECRAFT_DIR, "libraries")
natives_dir = os.path.join(version_dir, "natives")

replacements = {
    "${natives_directory}": natives_dir,
    "${library_directory}": lib_dir,
    "${version_name}": VERSION_NAME,
    "${launcher_name}": "HMCL",
    "${launcher_version}": "3.12.4",
    "${auth_player_name}": "Player",
    "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
    "${auth_access_token}": "0",
    "${auth_xuid}": "0",
    "${clientid}": "0",
    "${user_type}": "legacy",
    "${version_type}": "NeoForge",
    "${game_directory}": version_dir,
    "${assets_root}": os.path.join(MINECRAFT_DIR, "assets"),
    "${assets_index_name}": "12",
    "${primary_jar_name}": f"{VERSION_NAME}.jar",
}

jvm_args_from_json = data.get("arguments", {}).get("jvm", [])

print("Resolved JVM arguments:")
for arg in jvm_args_from_json:
    if isinstance(arg, str):
        for key, val in replacements.items():
            arg = arg.replace(key, str(val))
        print(f"  {arg}")

legacy_cp_parts = [
    f"{lib_dir}/net/neoforged/fancymodloader/earlydisplay/2.0.17/earlydisplay-2.0.17.jar",
    f"{lib_dir}/net/neoforged/fancymodloader/loader/2.0.17/loader-2.0.17.jar",
    f"{lib_dir}/net/neoforged/coremods/6.0.4/coremods-6.0.4.jar",
    f"{lib_dir}/net/neoforged/fancymodloader/spi/2.0.17/spi-2.0.17.jar",
    f"{lib_dir}/cpw/mods/modlauncher/10.0.9/modlauncher-10.0.9.jar",
]
legacy_classpath = ";".join(legacy_cp_parts)

print(f"\nlegacyClassPath argument:")
print(f"  -DlegacyClassPath={legacy_classpath[:200]}...")

print("\nChecking if log4j2 module is needed...")
log4j_path = os.path.join(lib_dir, "org/apache/logging/log4j")
if os.path.exists(log4j_path):
    print(f"  log4j found at: {log4j_path}")
    for root, dirs, files in os.walk(log4j_path):
        for f in files:
            if f.endswith(".jar"):
                print(f"    {os.path.join(root, f)}")
else:
    print(f"  log4j NOT found at: {log4j_path}")
