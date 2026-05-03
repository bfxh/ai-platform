import subprocess
import os
import time
import json
import zipfile
import tempfile

minecraft_dir = r"%GAME_DIR%\.minecraft"
version_name = "我即是虫群v2.0"
version_dir = os.path.join(minecraft_dir, "versions", version_name)
libraries_dir = os.path.join(minecraft_dir, "libraries")
natives_dir = os.path.join(version_dir, "natives")
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

def check_rules(lib):
    rules = lib.get("rules", [])
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

def extract_natives(lib):
    natives = lib.get("natives", {})
    if not natives:
        return
    native_key = natives.get("windows", "")
    if not native_key:
        return
    native_key_resolved = native_key.replace("${arch}", "64")
    downloads = lib.get("downloads", {})
    classifiers = downloads.get("classifiers", {})
    native_info = classifiers.get(native_key_resolved, {})
    native_path = native_info.get("path", "")
    if not native_path:
        name = lib.get("name", "")
        native_path_calc = lib_name_to_path(name + ":" + native_key_resolved)
        if os.path.exists(native_path_calc):
            full_native_path = native_path_calc
        else:
            return
    else:
        full_native_path = os.path.join(libraries_dir, native_path)
    if os.path.exists(full_native_path):
        os.makedirs(natives_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(full_native_path, 'r') as z:
                exclude = lib.get("extract", {}).get("exclude", [])
                for entry in z.namelist():
                    skip = False
                    for pattern in exclude:
                        if entry.startswith(pattern.replace("*", "")):
                            skip = True
                            break
                    if not skip:
                        z.extract(entry, natives_dir)
        except Exception as e:
            print(f"  Warning: native extraction failed: {e}")

def process_library(lib, classpath_parts, missing_libs, seen_names):
    lib_name = lib.get("name", "")
    if not check_rules(lib):
        return
    parts = lib_name.split(":")
    if len(parts) >= 4 and parts[3] == "installer":
        return
    base_name = ":".join(parts[:3])
    has_natives = bool(lib.get("natives", {}))
    if has_natives:
        extract_natives(lib)
        downloads = lib.get("downloads", {})
        artifact = downloads.get("artifact", {})
        if artifact and base_name not in seen_names:
            lib_path = artifact.get("path", "")
            if lib_path:
                full_path = os.path.join(libraries_dir, lib_path)
            else:
                full_path = lib_name_to_path(base_name)
            if os.path.exists(full_path):
                classpath_parts.append(full_path)
                seen_names.add(base_name)
            else:
                missing_libs.append(base_name)
        return
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
    else:
        missing_libs.append(lib_name)

version_json_path = os.path.join(version_dir, f"{version_name}.json")
with open(version_json_path, 'r', encoding='utf-8') as f:
    version_data = json.load(f)

main_class = version_data.get("mainClass", "net.minecraft.launchwrapper.Launch")
minecraft_args = version_data.get("minecraftArguments", "")

classpath_parts = []
missing_libs = []
seen_names = set()

for lib in version_data.get("libraries", []):
    process_library(lib, classpath_parts, missing_libs, seen_names)

patches = version_data.get("patches", [])
tweak_classes_from_patches = []
for patch in patches:
    for lib in patch.get("libraries", []):
        process_library(lib, classpath_parts, missing_libs, seen_names)
    patch_args = patch.get("arguments", {}).get("game", [])
    i = 0
    while i < len(patch_args):
        if isinstance(patch_args[i], str) and patch_args[i] == "--tweakClass":
            if i + 1 < len(patch_args) and isinstance(patch_args[i + 1], str):
                tweak_classes_from_patches.append(patch_args[i + 1])
                i += 2
                continue
        i += 1

for tc in tweak_classes_from_patches:
    if tc not in minecraft_args:
        if tc == "optifine.OptiFineTweaker" and "optifine.OptiFineForgeTweaker" in minecraft_args:
            continue
        minecraft_args += f" --tweakClass {tc}"

version_jar = os.path.join(version_dir, f"{version_name}.jar")
if os.path.exists(version_jar):
    classpath_parts.insert(0, version_jar)

classpath = ";".join(classpath_parts)

java_exe = r"%GAME_DIR%\文件缓存目录\cache\java\jre-legacy\windows-x64\jre-legacy\bin\java.exe"
if not os.path.exists(java_exe):
    java_exe = "java"

game_args = minecraft_args
game_args = game_args.replace("${auth_player_name}", "Player")
game_args = game_args.replace("${version_name}", version_name)
game_args = game_args.replace("${game_directory}", game_dir)
game_args = game_args.replace("${assets_root}", assets_dir)
game_args = game_args.replace("${assets_index_name}", "1.12")
game_args = game_args.replace("${auth_uuid}", "00000000-0000-0000-0000-000000000000")
game_args = game_args.replace("${auth_access_token}", "0")
game_args = game_args.replace("${user_type}", "legacy")
game_args = game_args.replace("${version_type}", "Forge")

log4j_path = os.path.join(version_dir, "log4j2.xml")

jvm_args = [
    java_exe,
    "-Xmx4G", "-Xms1G",
    "-XX:+UseG1GC",
    "-XX:-UseAdaptiveSizePolicy",
    "-XX:-OmitStackTraceInFastThrow",
    f"-Djava.library.path={natives_dir}",
    "-Dminecraft.launcher.brand=HMCL",
    "-Dminecraft.launcher.version=3.12.4",
    f"-Dlog4j.configurationFile={log4j_path}",
    "-cp", classpath,
    main_class,
] + game_args.split()

print(f"Launching {version_name}...")
print(f"gameDir: {game_dir}")
print(f"scripts dir exists: {os.path.exists(os.path.join(game_dir, 'scripts'))}")
process = subprocess.Popen(jvm_args, cwd=game_dir)
print(f"PID: {process.pid}")

time.sleep(5)
if process.poll() is not None:
    print(f"Game exited with code {process.returncode}")
else:
    print("Game is running! Waiting for it to finish...")
    process.wait()
    print(f"Game exited with code {process.returncode}")
