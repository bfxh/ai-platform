import os
import json
import zipfile
import shutil
import hashlib
import urllib.request
import subprocess
import time
import sys
import ctypes

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
JAVA_8 = r"%GAME_DIR%\文件缓存目录\cache\java\jre-legacy\windows-x64\jre-legacy\bin\java.exe"
JAVA_17 = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\java.exe"

def find_minecraft_window():
    user32 = ctypes.windll.user32
    result = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "minecraft" in buf.value.lower():
                result.append((hwnd, buf.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result

def activate_window(hwnd):
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    user32.ShowWindow(hwnd, 9)
    time.sleep(1)

def lib_name_to_path(name):
    parts = name.split(":")
    group = parts[0].replace(".", "/")
    artifact = parts[1]
    version = parts[2]
    classifier = parts[3] if len(parts) > 3 else None
    if classifier:
        filename = f"{artifact}-{version}-{classifier}.jar"
    else:
        filename = f"{artifact}-{version}.jar"
    return os.path.join(group, artifact, version, filename)

def build_classpath(version_name):
    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    json_path = os.path.join(version_dir, f"{version_name}.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    libraries = []
    main_class = data.get("mainClass", "")
    mc_args = data.get("minecraftArguments", "")
    asset_index = ""

    all_libs = list(data.get("libraries", []))
    for patch in data.get("patches", []):
        if patch.get("id") == "game":
            if not mc_args:
                mc_args = patch.get("minecraftArguments", "")
            asset_index = patch.get("assetIndex", {}).get("id", "")
        all_libs.extend(patch.get("libraries", []))

    for lib in all_libs:
        name = lib.get("name", "")
        downloads = lib.get("downloads", {})
        rules = lib.get("rules", [])

        skip = False
        for rule in rules:
            action = rule.get("action", "allow")
            os_name = rule.get("os", {}).get("name", "")
            if action == "disallow" and os_name == "windows":
                skip = True
            elif action == "allow" and os_name and os_name != "windows":
                skip = True
        if skip:
            continue

        if "artifact" in downloads:
            path = downloads["artifact"].get("path", "")
            if path:
                lib_path = os.path.join(MINECRAFT_DIR, "libraries", path)
                if os.path.exists(lib_path):
                    libraries.append(lib_path)
        else:
            path = lib_name_to_path(name)
            lib_path = os.path.join(MINECRAFT_DIR, "libraries", path)
            if os.path.exists(lib_path):
                libraries.append(lib_path)

    version_jar = os.path.join(version_dir, f"{version_name}.jar")
    if os.path.exists(version_jar):
        libraries.append(version_jar)

    return ";".join(libraries), main_class, mc_args, asset_index

def extract_natives(version_name):
    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    natives_dir = os.path.join(version_dir, "natives")
    os.makedirs(natives_dir, exist_ok=True)

    json_path = os.path.join(version_dir, f"{version_name}.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_libs = list(data.get("libraries", []))
    for patch in data.get("patches", []):
        all_libs.extend(patch.get("libraries", []))

    for lib in all_libs:
        downloads = lib.get("downloads", {})
        if "classifiers" in downloads:
            for key, classifier_info in downloads["classifiers"].items():
                if "natives-windows" in key or "natives" in key:
                    path = classifier_info.get("path", "")
                    if path:
                        lib_path = os.path.join(MINECRAFT_DIR, "libraries", path)
                        if os.path.exists(lib_path):
                            try:
                                with zipfile.ZipFile(lib_path, "r") as zf:
                                    for member in zf.namelist():
                                        if not member.endswith("/") and "META-INF" not in member:
                                            try:
                                                data_bytes = zf.read(member)
                                                member_name = os.path.basename(member)
                                                with open(os.path.join(natives_dir, member_name), "wb") as out:
                                                    out.write(data_bytes)
                                            except:
                                                pass
                            except:
                                pass

    return natives_dir

def launch_1122(version_name):
    print(f"  启动 {version_name} (1.12.2 Forge)...")

    if not os.path.exists(JAVA_8):
        print(f"  ERROR: Java 8 not found at {JAVA_8}")
        return None

    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    classpath, main_class, mc_args, asset_index = build_classpath(version_name)

    if not classpath or not main_class:
        print("  ERROR: 无法构建classpath!")
        return None

    print(f"  Java: {JAVA_8}")
    print(f"  MainClass: {main_class}")
    print(f"  Classpath条目数: {len(classpath.split(';'))}")

    natives_dir = extract_natives(version_name)
    print(f"  Natives: {natives_dir}")

    replacements = {
        "${auth_player_name}": "Player",
        "${version_name}": version_name,
        "${game_directory}": version_dir,
        "${assets_root}": os.path.join(MINECRAFT_DIR, "assets"),
        "${assets_index_name}": asset_index or "1.12",
        "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
        "${auth_access_token}": "0",
        "${user_type}": "legacy",
        "${version_type}": "Forge",
        "${resolution_width}": "854",
        "${resolution_height}": "480",
    }

    game_args = mc_args
    for key, val in replacements.items():
        game_args = game_args.replace(key, val)

    game_args_list = game_args.split()

    cmd = [
        JAVA_8,
        "-Xmx4G",
        "-Xms2G",
        f"-Djava.library.path={natives_dir}",
        "-Dminecraft.launcher.brand=HMCL",
        "-Dminecraft.launcher.version=3.12.4",
        "-Dfml.ignoreInvalidMinecraftCertificates=true",
        "-Dfml.ignorePatchDiscrepancies=true",
        "-cp", classpath,
        main_class,
    ] + game_args_list

    log_path = os.path.join(version_dir, "launch_test.log")
    print(f"  日志: {log_path}")

    try:
        with open(log_path, "w", encoding="utf-8") as lf:
            process = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=version_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        print(f"  进程已启动: PID={process.pid}")
        return process
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def launch_modern(version_name, mc_version="1.20.1"):
    print(f"  启动 {version_name} ({mc_version} Forge/NeoForge)...")

    if not os.path.exists(JAVA_17):
        print(f"  ERROR: Java 17 not found at {JAVA_17}")
        return None

    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    json_path = os.path.join(version_dir, f"{version_name}.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    libraries = []
    main_class = data.get("mainClass", "")
    asset_index = data.get("assetIndex", {}).get("id", "5")

    if mc_version == "1.20.4":
        asset_index = "12"

    all_libs = list(data.get("libraries", []))
    for patch in data.get("patches", []):
        all_libs.extend(patch.get("libraries", []))

    for lib in all_libs:
        name = lib.get("name", "")
        downloads = lib.get("downloads", {})
        rules = lib.get("rules", [])

        skip = False
        for rule in rules:
            action = rule.get("action", "allow")
            os_name = rule.get("os", {}).get("name", "")
            if action == "disallow" and os_name == "windows":
                skip = True
            elif action == "allow" and os_name and os_name != "windows":
                skip = True
        if skip:
            continue

        if "artifact" in downloads:
            path = downloads["artifact"].get("path", "")
            if path:
                lib_path = os.path.join(MINECRAFT_DIR, "libraries", path)
                if os.path.exists(lib_path):
                    libraries.append(lib_path)
        else:
            path = lib_name_to_path(name)
            lib_path = os.path.join(MINECRAFT_DIR, "libraries", path)
            if os.path.exists(lib_path):
                libraries.append(lib_path)

    version_jar = os.path.join(version_dir, f"{version_name}.jar")
    if os.path.exists(version_jar):
        libraries.append(version_jar)

    seen = set()
    unique_libraries = []
    for lib in libraries:
        if lib not in seen:
            seen.add(lib)
            unique_libraries.append(lib)

    classpath = ";".join(unique_libraries)
    natives_dir = extract_natives(version_name)
    lib_dir = os.path.join(MINECRAFT_DIR, "libraries")

    print(f"  Java: {JAVA_17}")
    print(f"  MainClass: {main_class}")
    print(f"  Classpath条目数: {len(unique_libraries)}")

    neoforge_lib = os.path.join(MINECRAFT_DIR, "libraries", "net", "neoforged", "neoforge")
    is_neoforge = os.path.exists(neoforge_lib) and mc_version == "1.20.4"

    jvm_args_from_json = data.get("arguments", {}).get("jvm", [])
    game_args_from_json = data.get("arguments", {}).get("game", [])

    replacements = {
        "${natives_directory}": natives_dir,
        "${library_directory}": lib_dir,
        "${classpath}": classpath,
        "${classpath_separator}": ";",
        "${version_name}": version_name,
        "${launcher_name}": "HMCL",
        "${launcher_version}": "3.12.4",
        "${auth_player_name}": "Player",
        "${auth_uuid}": "00000000-0000-0000-0000-000000000000",
        "${auth_access_token}": "0",
        "${auth_xuid}": "0",
        "${clientid}": "0",
        "${user_type}": "legacy",
        "${version_type}": "NeoForge" if is_neoforge else "Forge",
        "${game_directory}": version_dir,
        "${assets_root}": os.path.join(MINECRAFT_DIR, "assets"),
        "${assets_index_name}": asset_index,
        "${primary_jar_name}": f"{version_name}.jar",
        "${resolution_width}": "854",
        "${resolution_height}": "480",
        "${classpath_separator}": ";",
    }

    def replace_vars(arg):
        if not isinstance(arg, str):
            return arg
        for key, val in replacements.items():
            arg = arg.replace(key, str(val))
        arg = arg.replace("${classpath_separator}", ";")
        return arg

    resolved_jvm_args = []
    for arg in jvm_args_from_json:
        resolved = replace_vars(arg)
        if isinstance(resolved, str) and resolved.startswith("-"):
            resolved_jvm_args.append(resolved)
        elif isinstance(resolved, str) and resolved:
            resolved_jvm_args.append(resolved)

    resolved_game_args = []
    for arg in game_args_from_json:
        resolved = replace_vars(arg)
        if isinstance(resolved, str) and resolved:
            resolved_game_args.append(resolved)

    if is_neoforge:
        legacy_cp_parts = [
            f"{lib_dir}/net/neoforged/fancymodloader/earlydisplay/2.0.17/earlydisplay-2.0.17.jar",
            f"{lib_dir}/net/neoforged/fancymodloader/loader/2.0.17/loader-2.0.17.jar",
            f"{lib_dir}/net/neoforged/coremods/6.0.4/coremods-6.0.4.jar",
            f"{lib_dir}/net/neoforged/fancymodloader/spi/2.0.17/spi-2.0.17.jar",
            f"{lib_dir}/cpw/mods/modlauncher/10.0.9/modlauncher-10.0.9.jar",
        ]
        legacy_classpath = ";".join(legacy_cp_parts)
        resolved_jvm_args.append(f"-DlegacyClassPath={legacy_classpath}")

        required_game_args = [
            "--username", "Player",
            "--version", version_name,
            "--gameDir", version_dir,
            "--assetsDir", os.path.join(MINECRAFT_DIR, "assets"),
            "--assetIndex", asset_index,
            "--uuid", "00000000-0000-0000-0000-000000000000",
            "--accessToken", "0",
            "--clientId", "0",
            "--xuid", "0",
            "--userType", "legacy",
            "--versionType", "NeoForge",
        ]
        for i in range(0, len(required_game_args), 2):
            key = required_game_args[i]
            val = required_game_args[i+1]
            found = False
            for j, arg in enumerate(resolved_game_args):
                if arg == key:
                    found = True
                    break
            if not found:
                resolved_game_args.append(key)
                resolved_game_args.append(str(val))

    jvm_base_args = [
        JAVA_17,
        "-Xmx4G",
        "-Xms2G",
    ]

    cmd = jvm_base_args + resolved_jvm_args + [main_class] + resolved_game_args

    log_path = os.path.join(version_dir, "launch_test.log")
    print(f"  日志: {log_path}")

    if is_neoforge:
        print(f"\n  NeoForge detected - checking legacyClassPath...")
        legacy_found = False
        for arg in cmd:
            if "legacyClassPath" in str(arg):
                print(f"    Found legacyClassPath in cmd")
                legacy_found = True
        if not legacy_found:
            print("    WARNING: legacyClassPath NOT found in cmd!")

    try:
        with open(log_path, "w", encoding="utf-8") as lf:
            process = subprocess.Popen(
                cmd,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=version_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        print(f"  进程已启动: PID={process.pid}")
        return process
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def wait_for_game(version_name, timeout=300):
    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    latest_log = os.path.join(version_dir, "logs", "latest.log")

    start_time = time.time()
    last_pos = 0

    if os.path.exists(latest_log):
        last_pos = os.path.getsize(latest_log)

    while time.time() - start_time < timeout:
        if os.path.exists(latest_log):
            try:
                size = os.path.getsize(latest_log)
                if size > last_pos:
                    with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(last_pos)
                        new_content = f.read()
                    last_pos = size

                    if "Saving chunks" in new_content or "Preparing spawn area" in new_content:
                        return True, "游戏加载成功"
                    if "Loaded 0 advancements" in new_content:
                        return True, "游戏已加载"
                    if "Starting integrated minecraft server" in new_content:
                        return True, "单人世界已启动"
                    if "Stopping!" in new_content and time.time() - start_time > 30:
                        return False, "游戏崩溃/停止"
            except:
                pass
        time.sleep(5)

    return False, "超时"

def test_modpack(version_name, mc_version="1.12.2"):
    print(f"\n{'='*60}")
    print(f"  测试: {version_name} ({mc_version})")
    print(f"{'='*60}")

    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    if not os.path.exists(version_dir):
        print(f"  ERROR: 版本目录不存在: {version_dir}")
        return False

    for log_name in ["latest.log", "launch_test.log"]:
        if log_name == "latest.log":
            log_path = os.path.join(version_dir, "logs", log_name)
        else:
            log_path = os.path.join(version_dir, log_name)
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except:
                pass

    if mc_version == "1.12.2":
        process = launch_1122(version_name)
    elif mc_version in ("1.20.1", "1.20.4"):
        process = launch_modern(version_name, mc_version)
    else:
        print(f"  ERROR: 不支持的版本 {mc_version}")
        return False

    if not process:
        return False

    print("  等待游戏窗口...")
    for i in range(60):
        time.sleep(3)
        windows = find_minecraft_window()
        if windows:
            hwnd, title = windows[0]
            print(f"  找到窗口: {title}")
            activate_window(hwnd)
            break
        if i % 10 == 0 and i > 0:
            print(f"  等待中... ({i*3}s)")
    else:
        print("  WARNING: 未找到游戏窗口，继续等待日志...")

    print("  等待游戏加载...")
    loaded, detail = wait_for_game(version_name, timeout=300)

    if loaded:
        print(f"  ✓ {detail}")
        return True
    else:
        print(f"  ✗ {detail}")

        for log_name in ["latest.log", "launch_test.log"]:
            if log_name == "latest.log":
                log_path = os.path.join(version_dir, "logs", log_name)
            else:
                log_path = os.path.join(version_dir, log_name)
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    error_lines = [l.strip() for l in lines if "ERROR" in l or "Exception" in l or "FATAL" in l]
                    if error_lines:
                        print(f"  错误日志 ({log_name} 最后5行):")
                        for line in error_lines[-5:]:
                            print(f"    {line[:150]}")
                except:
                    pass
        return False

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "我即是虫群v2.0"
    mc_ver = sys.argv[2] if len(sys.argv) > 2 else "1.12.2"

    print("=" * 60)
    print(f"  Minecraft 整合包自动测试器")
    print(f"  版本: {version} ({mc_ver})")
    print("=" * 60)

    result = test_modpack(version, mc_ver)
    print(f"\n  结果: {'✓ 通过' if result else '✗ 失败'}")
