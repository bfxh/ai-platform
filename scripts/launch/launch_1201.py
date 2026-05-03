import subprocess
import os
import time
import json
import zipfile

minecraft_dir = r"%GAME_DIR%\.minecraft"
version_name = "新起源"
version_dir = os.path.join(minecraft_dir, "versions", version_name)
libraries_dir = os.path.join(minecraft_dir, "libraries")
natives_dir = os.path.join(version_dir, version_name + "-natives")
game_dir = version_dir
assets_dir = os.path.join(minecraft_dir, "assets")

def lib_name_to_path(name):
    parts = name.split(":")
    group = parts[0].replace(".", os.sep)
    artifact = parts[1]
    version = parts[2] if len(parts) > 2 else ""
    classifier = parts[3] if len(parts) > 3 else ""
    if classifier:
        filename = f"{artifact}-{version}-{classifier}.jar"
    else:
        filename = f"{artifact}-{version}.jar"
    return os.path.join(libraries_dir, group, artifact, version, filename)

def check_rules(rules):
    if not rules:
        return True
    allowed = False
    for rule in rules:
        action = rule.get("action", "allow")
        os_name = rule.get("os", {}).get("name", "")
        if action == "allow" and (not os_name or os_name == "windows"):
            allowed = True
        elif action == "disallow" and os_name == "windows":
            allowed = False
    return allowed

def process_library(lib, classpath_parts, seen_names, natives_to_extract):
    lib_name = lib.get("name", "")
    rules = lib.get("rules", None)
    if rules and not check_rules(rules):
        return

    parts = lib_name.split(":")
    if len(parts) >= 4 and parts[3] == "installer":
        return

    is_native = len(parts) >= 4 and "natives" in parts[3]
    if is_native:
        if "windows" not in parts[3]:
            return
        downloads = lib.get("downloads", {})
        artifact = downloads.get("artifact", {})
        lib_path = artifact.get("path", "")
        if lib_path:
            full_path = os.path.join(libraries_dir, lib_path)
        else:
            full_path = lib_name_to_path(lib_name)
        if os.path.exists(full_path):
            natives_to_extract.append(full_path)
        return

    base_name = ":".join(parts[:3])
    if base_name in seen_names:
        return
    seen_names.add(base_name)

    downloads = lib.get("downloads", {})
    artifact = downloads.get("artifact", {})
    lib_path = artifact.get("path", "")

    if lib_path:
        full_path = os.path.join(libraries_dir, lib_path)
    else:
        full_path = lib_name_to_path(lib_name)

    if os.path.exists(full_path):
        classpath_parts.append(full_path)

    natives = lib.get("natives", {})
    if natives:
        native_key = natives.get("windows", "").replace("${arch}", "64")
        if native_key:
            classifiers = downloads.get("classifiers", {})
            native_info = classifiers.get(native_key, {})
            native_path = native_info.get("path", "")
            if native_path:
                natives_to_extract.append(os.path.join(libraries_dir, native_path))

def resolve_arguments(args_list, replacements):
    result = []
    for arg in args_list:
        if isinstance(arg, str):
            for key, val in replacements.items():
                arg = arg.replace(key, val)
            result.append(arg)
        elif isinstance(arg, dict):
            rules = arg.get("rules", [])
            if check_rules(rules):
                values = arg.get("value", [])
                if isinstance(values, str):
                    values = [values]
                for v in values:
                    for key, val in replacements.items():
                        v = v.replace(key, val)
                    result.append(v)
    return result

version_json_path = os.path.join(version_dir, f"{version_name}.json")
with open(version_json_path, 'r', encoding='utf-8') as f:
    version_data = json.load(f)

main_class = version_data.get("mainClass", "")
classpath_parts = []
seen_names = set()
natives_to_extract = []

for lib in version_data.get("libraries", []):
    process_library(lib, classpath_parts, seen_names, natives_to_extract)

for patch in version_data.get("patches", []):
    for lib in patch.get("libraries", []):
        process_library(lib, classpath_parts, seen_names, natives_to_extract)

version_jar = os.path.join(version_dir, f"{version_name}.jar")
if os.path.exists(version_jar):
    classpath_parts.insert(0, version_jar)

os.makedirs(natives_dir, exist_ok=True)
for native_jar in natives_to_extract:
    if os.path.exists(native_jar):
        try:
            with zipfile.ZipFile(native_jar, 'r') as z:
                for entry in z.namelist():
                    if not entry.endswith('/'):
                        z.extract(entry, natives_dir)
        except:
            pass

classpath = ";".join(classpath_parts)

java_21_path = r"%GAME_DIR%\文件缓存目录\cache\java\java-runtime-delta\windows-x64\java-runtime-delta\bin\java.exe"
if not os.path.exists(java_21_path):
    java_21_path = "java"

print(f"Java: {java_21_path}")
print(f"MainClass: {main_class}")
print(f"Classpath: {len(classpath_parts)} libs")

replacements = {
    "${auth_player_name}": "Player",
    "${version_name}": version_name,
    "${game_directory}": game_dir,
    "${assets_root}": assets_dir,
    "${assets_index_name}": "5",
    "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
    "${auth_access_token}": "0",
    "${clientid}": "0",
    "${auth_xuid}": "0",
    "${user_type}": "legacy",
    "${version_type}": "Forge",
    "${quickPlayPath}": "",
    "${quickPlaySingleplayer}": "",
    "${quickPlayMultiplayer}": "",
    "${quickPlayRealms}": "",
    "${natives_directory}": natives_dir,
    "${library_directory}": libraries_dir,
    "${classpath}": classpath,
    "${classpath_separator}": ";",
    "${launcher_name}": "HMCL",
    "${launcher_version}": "3.12.4",
    "${primary_jar_name}": f"{version_name}.jar",
    "${resolution_width}": "854",
    "${resolution_height}": "480",
}

jvm_args_raw = version_data.get("arguments", {}).get("jvm", [])
game_args_raw = version_data.get("arguments", {}).get("game", [])

for patch in version_data.get("patches", []):
    patch_jvm = patch.get("arguments", {}).get("jvm", [])
    patch_game = patch.get("arguments", {}).get("game", [])
    if patch_jvm:
        jvm_args_raw.extend(patch_jvm)
    if patch_game:
        game_args_raw.extend(patch_game)

if not game_args_raw and "minecraftArguments" in version_data:
    game_args_raw = version_data["minecraftArguments"].split()

jvm_args = resolve_arguments(jvm_args_raw, replacements)
game_args = resolve_arguments(game_args_raw, replacements)

seen = set()
deduped = []
skip = False
for i, arg in enumerate(game_args):
    if skip:
        skip = False
        continue
    if arg.startswith("--") and arg in seen:
        if i + 1 < len(game_args) and not game_args[i+1].startswith("--"):
            skip = True
        continue
    if arg.startswith("--"):
        seen.add(arg)
    deduped.append(arg)
game_args = deduped

full_args = [
    java_21_path,
    "-Xmx4G", "-Xms1G",
] + jvm_args + [
    main_class,
] + game_args

print(f"Launching {version_name}...")
process = subprocess.Popen(full_args, cwd=game_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(f"PID: {process.pid}")

time.sleep(30)
if process.poll() is not None:
    stderr = process.stderr.read().decode('utf-8', errors='replace')
    print(f"Game exited with code {process.returncode}")
    if stderr:
        print(stderr[:3000])
else:
    print("Game is running!")
