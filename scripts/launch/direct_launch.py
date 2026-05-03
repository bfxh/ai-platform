import os
import json
import subprocess
import sys

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)

print("=" * 60)
print("  直接启动Minecraft游戏")
print("=" * 60)

java_paths = [
    r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\javaw.exe",
    r"C:\Program Files\Microsoft\jdk-17.0.12.7-hotspot\bin\javaw.exe",
    r"C:\Program Files\Java\jdk-25.0.2\bin\javaw.exe",
    r"%GAME_DIR%\文件缓存目录\cache\java\java-runtime-delta\windows-x64\java-runtime-delta\bin\javaw.exe",
]

java_exe = None
for p in java_paths:
    if os.path.exists(p):
        java_exe = p
        print(f"  Java: {p}")
        break

if not java_exe:
    print("  [ERR] 未找到Java!")
    sys.exit(1)

version_json_path = os.path.join(VERSION_DIR, f"{VERSION_NAME}.json")
with open(version_json_path, "r", encoding="utf-8") as f:
    version_data = json.load(f)

base_version_dir = os.path.join(MC_DIR, "versions", "1.20.4")
base_json_path = os.path.join(base_version_dir, "1.20.4.json")

if not os.path.exists(base_json_path):
    print(f"  [ERR] 基础版本1.20.4的JSON不存在!")
    sys.exit(1)

with open(base_json_path, "r", encoding="utf-8") as f:
    base_data = json.load(f)

main_class = version_data.get("mainClass", base_data.get("mainClass", ""))
print(f"  MainClass: {main_class}")

libraries = base_data.get("libraries", []) + version_data.get("libraries", [])

classpath_parts = []
for lib in libraries:
    name = lib.get("name", "")
    if name:
        parts = name.split(":")
        if len(parts) >= 3:
            group = parts[0].replace(".", os.sep)
            artifact = parts[1]
            version = parts[2]
            lib_path = os.path.join(MC_DIR, "libraries", group, artifact, version, f"{artifact}-{version}.jar")
            if os.path.exists(lib_path):
                classpath_parts.append(lib_path)

mc_jar = os.path.join(base_version_dir, "1.20.4.jar")
if os.path.exists(mc_jar):
    classpath_parts.append(mc_jar)
else:
    for f in os.listdir(base_version_dir):
        if f.endswith(".jar") and "1.20.4" in f:
            classpath_parts.append(os.path.join(base_version_dir, f))
            break

mods_dir = os.path.join(VERSION_DIR, "mods")
for f in os.listdir(mods_dir):
    if f.endswith(".jar"):
        classpath_parts.append(os.path.join(mods_dir, f))

print(f"  Classpath entries: {len(classpath_parts)}")

game_dir = MC_DIR
assets_dir = os.path.join(MC_DIR, "assets")
natives_dir = os.path.join(VERSION_DIR, "natives")

os.makedirs(natives_dir, exist_ok=True)

for lib in libraries:
    if lib.get("natives") and lib.get("extract"):
        name = lib.get("name", "")
        parts = name.split(":")
        if len(parts) >= 3:
            group = parts[0].replace(".", os.sep)
            artifact = parts[1]
            version = parts[2]
            lib_path = os.path.join(MC_DIR, "libraries", group, artifact, version, f"{artifact}-{version}.jar")
            if os.path.exists(lib_path):
                import zipfile
                try:
                    with zipfile.ZipFile(lib_path, "r") as zf:
                        for n in zf.namelist():
                            if n.endswith(".dll"):
                                try:
                                    zf.extract(n, natives_dir)
                                except:
                                    pass
                except:
                    pass

assets_index = base_data.get("assetIndex", {}).get("id", "7")
uuid = "0e09e7a0-2c3f-4b8e-9d1a-5f6e8a0b1c2d"
username = "SwarmPlayer"

jvm_args = [
    f'-Djava.library.path={natives_dir}',
    f'-Dminecraft.launcher.brand=HMCL',
    f'-Dminecraft.launcher.version=3.12.4',
    '-XX:+UnlockExperimentalVMOptions',
    '-XX:+UseG1GC',
    '-XX:G1NewSizePercent=20',
    '-XX:G1ReservePercent=20',
    '-XX:MaxGCPauseMillis=50',
    '-XX:G1HeapRegionSize=32M',
    '-Xmx4096M',
    '-Xms1024M',
]

game_args = [
    '--username', username,
    '--version', VERSION_NAME,
    '--gameDir', game_dir,
    '--assetsDir', assets_dir,
    '--assetIndex', assets_index,
    '--uuid', uuid,
    '--accessToken', '0',
    '--userType', 'legacy',
    '--versionType', 'Fabric',
]

classpath = ";".join(classpath_parts)

full_args = [java_exe] + jvm_args + ['-cp', classpath, main_class] + game_args

print(f"  启动命令已构建")
print(f"  Java: {java_exe}")
print(f"  内存: 4096M")
print(f"  模组: {len([f for f in os.listdir(mods_dir) if f.endswith('.jar')])}")

log_file = os.path.join(VERSION_DIR, "launch_log.txt")
print(f"  日志: {log_file}")

try:
    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"Launch: {' '.join(full_args[:5])}...\n")

    process = subprocess.Popen(
        full_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=game_dir,
    )

    print(f"\n  [OK] 游戏进程已启动! PID: {process.pid}")
    print(f"  等待游戏窗口出现...")

    import time
    time.sleep(10)

    poll = process.poll()
    if poll is None:
        print(f"  [OK] 游戏正在运行!")
    else:
        print(f"  [WARN] 进程已退出，退出码: {poll}")
        print(f"  读取错误日志...")
        try:
            output = process.stdout.read(5000).decode("utf-8", errors="replace")
            print(output[-3000:])
        except:
            pass

except Exception as e:
    print(f"  [ERR] 启动失败: {e}")
    import traceback
    traceback.print_exc()
