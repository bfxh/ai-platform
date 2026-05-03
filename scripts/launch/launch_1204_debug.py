import subprocess
import os
import time
import json
import zipfile

minecraft_dir = r"%GAME_DIR%\.minecraft"
version_name = "我即是虫群-1.20.4"
version_dir = os.path.join(minecraft_dir, "versions", version_name)
libraries_dir = os.path.join(minecraft_dir, "libraries")
natives_dir = os.path.join(version_dir, version_name + "-natives")
game_dir = version_dir
assets_dir = os.path.join(minecraft_dir, "assets")
log_file = os.path.join(version_dir, "launch_output.log")

def lib_name_to_path(name):
    parts = name.split(":")
    group = parts[0].replace(".", os.sep)
    artifact = parts[1]
    version = parts[2] if len(parts) > 2 else ""
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

def merge_version_data(base_path, version_json):
    if "inheritsFrom" in version_json:
        parent_name = version_json["inheritsFrom"]
        parent_path = os.path.join(minecraft_dir, "versions", parent_name, f"{parent_name}.json")
        if os.path.exists(parent_path):
            with open(parent_path, 'r', encoding='utf-8') as f:
                parent_data = json.load(f)
            merged = parent_data.copy()
            for key, value in version_json.items():
                if key == "inheritsFrom":
                    continue
                if key == "libraries":
                    existing_libs = {l["name"]: l for l in merged.get("libraries", [])}
                    for lib in value:
                        existing_libs[lib["name"]] = lib
                    merged["libraries"] = list(existing_libs.values())
                elif key == "arguments":
                    existing_args = merged.get("arguments", {})
                    for arg_type, arg_values in value.items():
                        if arg_type in existing_args:
                            if isinstance(existing_args[arg_type], list):
                                existing_args[arg_type] = existing_args[arg_type] + arg_values
                        else:
                            existing_args[arg_type] = arg_values
                    merged["arguments"] = existing_args
                else:
                    merged[key] = value
            return merge_version_data(base_path, merged)
    return version_json

version_json_path = os.path.join(version_dir, f"{version_name}.json")
with open(version_json_path, 'r', encoding='utf-8') as f:
    version_data = json.load(f)

version_data = merge_version_data(version_dir, version_data)

main_class = version_data.get("mainClass", "")
classpath_parts = []
seen_names = set()
natives_to_extract = []

for lib in version_data.get("libraries", []):
    process_library(lib, classpath_parts, seen_names, natives_to_extract)

version_jar = os.path.join(version_dir, f"{version_name}.jar")
if os.path.exists(version_jar):
    classpath_parts.insert(0, version_jar)

parent_jar = os.path.join(minecraft_dir, "versions", "1.20.4", "1.20.4.jar")
if os.path.exists(parent_jar):
    classpath_parts.insert(0, parent_jar)

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

classpath = ";".join(dict.fromkeys(classpath_parts))

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
    "${assets_index_name}": "12",
    "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
    "${auth_access_token}": "0",
    "${clientid}": "0",
    "${auth_xuid}": "0",
    "${user_type}": "legacy",
    "${version_type}": "NeoForge",
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

jvm_args = resolve_arguments(jvm_args_raw, replacements)
game_args = resolve_arguments(game_args_raw, replacements)

full_args = [
    java_21_path,
    "-Xmx4G", "-Xms1G",
] + jvm_args + [
    main_class,
] + game_args

print(f"Launching {version_name}...")

with open(log_file, 'w', encoding='utf-8') as log:
    log.write("Command:\n")
    log.write(" ".join(full_args) + "\n\n")
    log.write("Output:\n")

process = subprocess.Popen(full_args, cwd=game_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(f"PID: {process.pid}")

try:
    stdout, _ = process.communicate(timeout=120)
    output = stdout.decode('utf-8', errors='replace')
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(output)
    print(f"Game exited with code {process.returncode}")
    if output:
        lines = output.strip().split('\n')
        for line in lines[-30:]:
            print(line)
except subprocess.TimeoutExpired:
    process.kill()
    print("Game still running after 120s - likely started successfully!")
