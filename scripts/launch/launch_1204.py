import subprocess
import os
import time
import json
import zipfile
import ctypes

minecraft_dir = r"%GAME_DIR%\.minecraft"
version_name = "我即是虫群-1.20.4"
version_dir = os.path.join(minecraft_dir, "versions", version_name)
libraries_dir = os.path.join(minecraft_dir, "libraries")
natives_dir = os.path.join(version_dir, version_name + "-natives")
game_dir = version_dir
assets_dir = os.path.join(minecraft_dir, "assets")

user32 = ctypes.windll.user32


def find_window(title_keyword: str) -> bool:
    """检测窗口是否存在"""
    result = False
    
    def callback(hwnd, _):
        nonlocal result
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_keyword.lower() in buf.value.lower():
                result = True
        return True
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result


def wait_for_window(title_keyword: str, timeout: float = 120) -> bool:
    """等待窗口出现"""
    start = time.time()
    while time.time() - start < timeout:
        if find_window(title_keyword):
            return True
        time.sleep(1)
    return False

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

game_args = [a for a in game_args if a != "--demo"]

full_args = [
    java_21_path,
    "-Xmx4G", "-Xms1G",
] + jvm_args + [
    main_class,
] + game_args

print(f"Launching {version_name}...")
process = subprocess.Popen(full_args, cwd=game_dir)
print(f"PID: {process.pid}")

print("等待 Minecraft 窗口出现...")
if wait_for_window("Minecraft", timeout=180):
    print("✅ Minecraft 窗口已出现！")
    # 窗口出现后再等待 10 秒确保完全加载
    time.sleep(10)
    if process.poll() is not None:
        print(f"❌ 游戏已退出，代码: {process.returncode}")
    else:
        print("🎮 游戏正在运行中！")
else:
    print("❌ 超时：Minecraft 窗口未出现")
    if process.poll() is not None:
        print(f"游戏已退出，代码: {process.returncode}")
    else:
        print("进程仍在运行，但窗口未出现")
