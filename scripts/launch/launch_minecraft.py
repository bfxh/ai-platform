import json
import os
import subprocess
import sys

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4-Fabric"
JAVA_PATH = r"C:\Program Files\Microsoft\jdk-17.0.12.7-hotspot\bin\javaw.exe"
JAVA_LIB_PATH = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\javaw.exe"

LIBRARIES_DIR = os.path.join(MC_DIR, "libraries")
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)
NATIVES_DIR = os.path.join(VERSION_DIR, "natives")

def read_version_json(version_id):
    vdir = os.path.join(MC_DIR, "versions", version_id)
    json_path = os.path.join(vdir, version_id + ".json")
    if not os.path.exists(json_path):
        for f in os.listdir(vdir):
            if f.endswith(".json"):
                json_path = os.path.join(vdir, f)
                break
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_library_path(lib_name):
    parts = lib_name.split(":")
    group = parts[0].replace(".", os.sep)
    artifact = parts[1]
    version = parts[2]
    filename = f"{artifact}-{version}.jar"
    return os.path.join(LIBRARIES_DIR, group, artifact, version, filename)

def collect_classpath(version_json, visited=None):
    if visited is None:
        visited = set()
    
    cp = []
    vid = version_json.get("id", "")
    if vid in visited:
        return cp
    visited.add(vid)
    
    inherits = version_json.get("inheritsFrom")
    if inherits:
        try:
            parent_json = read_version_json(inherits)
            cp.extend(collect_classpath(parent_json, visited))
        except Exception:
            pass
    
    for lib in version_json.get("libraries", []):
        name = lib.get("name", "")
        
        rules = lib.get("rules", [])
        if rules:
            allowed = True
            for rule in rules:
                action = rule.get("action", "allow")
                os_name = rule.get("os", {}).get("name", "")
                if os_name and os_name != "windows":
                    if action == "allow":
                        allowed = False
                    else:
                        allowed = True
            if not allowed:
                continue
        
        if lib.get("natives"):
            continue
        
        downloads = lib.get("downloads", {})
        artifact = downloads.get("artifact", {})
        
        if artifact.get("path"):
            path = os.path.join(LIBRARIES_DIR, artifact["path"])
            if os.path.exists(path):
                cp.append(path)
                continue
        
        path = get_library_path(name)
        if os.path.exists(path):
            cp.append(path)
    
    jar_name = vid + ".jar"
    jar_path = os.path.join(MC_DIR, "versions", vid, jar_name)
    if os.path.exists(jar_path):
        cp.append(jar_path)
    else:
        for f in os.listdir(os.path.join(MC_DIR, "versions", vid)):
            if f.endswith(".jar") and not f.endswith("-sources.jar"):
                cp.append(os.path.join(MC_DIR, "versions", vid, f))
                break
    
    return cp

def main():
    print("=" * 60)
    print("  Minecraft 直接启动器")
    print("=" * 60)
    
    print("\n[1] 读取版本信息...")
    version_json = read_version_json(VERSION_NAME)
    main_class = version_json.get("mainClass", "net.fabricmc.loader.impl.launch.knot.KnotClient")
    print(f"  主类: {main_class}")
    
    print("\n[2] 构建类路径...")
    classpath = collect_classpath(version_json)
    
    mods_dir = os.path.join(VERSION_DIR, "mods")
    if os.path.exists(mods_dir):
        for f in os.listdir(mods_dir):
            if f.endswith(".jar"):
                classpath.append(os.path.join(mods_dir, f))
    
    existing_cp = [p for p in classpath if os.path.exists(p)]
    print(f"  类路径条目: {len(existing_cp)}/{len(classpath)}")
    
    missing = [p for p in classpath if not os.path.exists(p)]
    if missing:
        print(f"  缺失文件 ({len(missing)}):")
        for m in missing[:10]:
            print(f"    - {os.path.basename(m)}")
    
    print("\n[3] 准备启动参数...")
    
    os.makedirs(NATIVES_DIR, exist_ok=True)
    
    java_exe = JAVA_PATH
    if not os.path.exists(java_exe):
        java_exe = JAVA_LIB_PATH
    if not os.path.exists(java_exe):
        java_exe = "javaw"
    
    cp_str = ";".join(existing_cp)
    
    player_name = "SwarmPlayer"
    
    args = [
        java_exe,
        "-Xmx2G",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+UseG1GC",
        "-XX:G1NewSizePercent=20",
        "-XX:G1ReservePercent=20",
        "-XX:MaxGCPauseMillis=50",
        "-XX:G1HeapRegionSize=32M",
        f"-Djava.library.path={NATIVES_DIR}",
        f"-Dminecraft.launcher.brand=custom",
        f"-Dminecraft.launcher.version=1.0",
        "-cp", cp_str,
        main_class,
        "--username", player_name,
        "--version", VERSION_NAME,
        "--gameDir", MC_DIR,
        "--assetsDir", os.path.join(MC_DIR, "assets"),
        "--assetIndex", "16",
        "--uuid", "00000000-0000-0000-0000-000000000000",
        "--accessToken", "0",
        "--userType", "legacy",
        "--versionType", "release",
    ]
    
    print(f"  Java: {java_exe}")
    print(f"  主类: {main_class}")
    print(f"  玩家名: {player_name}")
    print(f"  游戏目录: {MC_DIR}")
    print(f"  模组数量: {len([f for f in os.listdir(mods_dir) if f.endswith('.jar')])}")
    
    print("\n[4] 启动游戏...")
    
    log_path = os.path.join(VERSION_DIR, "launch_log.txt")
    
    try:
        log_fh = open(log_path, "w")
        proc = subprocess.Popen(
            args,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            cwd=MC_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        print(f"  进程ID: {proc.pid}")
        print(f"  日志文件: {log_path}")
        print("\n  游戏正在启动，请等待...")
        print(f"  如果启动失败，请查看日志: {log_path}")
    except Exception as e:
        print(f"  [错误] 启动失败: {e}")
    finally:
        try:
            log_fh.close()
        except NameError:
            pass

if __name__ == "__main__":
    main()
