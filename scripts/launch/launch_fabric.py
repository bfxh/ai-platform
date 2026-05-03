import os
import json
import subprocess
import time

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4-Fabric"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)

java_exe = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\javaw.exe"

base_json_path = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.json")
with open(base_json_path, "r", encoding="utf-8") as f:
    base_data = json.load(f)

version_json_path = os.path.join(VERSION_DIR, f"{VERSION_NAME}.json")
with open(version_json_path, "r", encoding="utf-8") as f:
    version_data = json.load(f)

main_class = version_data.get("mainClass", "net.fabricmc.loader.impl.launch.knot.KnotClient")

classpath_parts = []
seen = set()

for lib in base_data.get("libraries", []):
    name = lib.get("name", "")
    downloads = lib.get("downloads", {})
    artifact = downloads.get("artifact", {})
    
    if name:
        parts = name.split(":")
        if len(parts) >= 3:
            group = parts[0].replace(".", os.sep)
            art = parts[1]
            ver = parts[2]
            jar_name = f"{art}-{ver}.jar"
            lib_path = os.path.join(MC_DIR, "libraries", group, art, ver, jar_name)
            if os.path.exists(lib_path) and art.lower() not in seen:
                seen.add(art.lower())
                classpath_parts.append(lib_path)
    
    if artifact:
        path = artifact.get("path", "")
        if path:
            full_path = os.path.join(MC_DIR, "libraries", path)
            if os.path.exists(full_path) and full_path not in classpath_parts:
                classpath_parts.append(full_path)

for lib in version_data.get("libraries", []):
    name = lib.get("name", "")
    downloads = lib.get("downloads", {})
    artifact = downloads.get("artifact", {})
    
    if name:
        parts = name.split(":")
        if len(parts) >= 3:
            group = parts[0].replace(".", os.sep)
            art = parts[1]
            ver = parts[2]
            jar_name = f"{art}-{ver}.jar"
            lib_path = os.path.join(MC_DIR, "libraries", group, art, ver, jar_name)
            if os.path.exists(lib_path) and art.lower() not in seen:
                seen.add(art.lower())
                classpath_parts.append(lib_path)
    
    if artifact:
        path = artifact.get("path", "")
        if path:
            full_path = os.path.join(MC_DIR, "libraries", path)
            if os.path.exists(full_path) and full_path not in classpath_parts:
                classpath_parts.append(full_path)

asm_dir = os.path.join(MC_DIR, "libraries", "org", "objectweb", "asm")
if os.path.exists(asm_dir):
    for root, dirs, files in os.walk(asm_dir):
        for f in files:
            if f.endswith(".jar"):
                p = os.path.join(root, f)
                if p not in classpath_parts:
                    classpath_parts.append(p)

mc_jar = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.jar")
if os.path.exists(mc_jar):
    classpath_parts.append(mc_jar)

mods_dir = os.path.join(VERSION_DIR, "mods")
for f in os.listdir(mods_dir):
    if f.endswith(".jar"):
        classpath_parts.append(os.path.join(mods_dir, f))

natives_dir = os.path.join(VERSION_DIR, "natives")
os.makedirs(natives_dir, exist_ok=True)

for lib in base_data.get("libraries", []):
    if lib.get("natives"):
        name = lib.get("name", "")
        parts_n = name.split(":")
        if len(parts_n) >= 3:
            group = parts_n[0].replace(".", os.sep)
            art = parts_n[1]
            ver = parts_n[2]
            nkey = lib["natives"].get("windows", "")
            if nkey:
                nkey = nkey.replace("${arch}", "64")
                jar_name = f"{art}-{ver}-{nkey}.jar"
                lib_path = os.path.join(MC_DIR, "libraries", group, art, ver, jar_name)
                if os.path.exists(lib_path):
                    import zipfile
                    try:
                        with zipfile.ZipFile(lib_path, "r") as zf:
                            for n in zf.namelist():
                                if n.endswith(".dll") and "META-INF" not in n:
                                    try:
                                        zf.extract(n, natives_dir)
                                    except:
                                        pass
                    except:
                        pass

assets_index = base_data.get("assetIndex", {}).get("id", "7")

jvm_args = [
    f'-Djava.library.path={natives_dir}',
    '-Dminecraft.launcher.brand=HMCL',
    '-Dminecraft.launcher.version=3.12.4',
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
    '--username', 'SwarmPlayer',
    '--version', VERSION_NAME,
    '--gameDir', VERSION_DIR,
    '--assetsDir', os.path.join(MC_DIR, "assets"),
    '--assetIndex', assets_index,
    '--uuid', '0e09e7a02c3f4b8e9d1a5f6e8a0b1c2d',
    '--accessToken', '0',
    '--userType', 'legacy',
    '--versionType', 'Fabric',
]

classpath = ";".join(classpath_parts)

full_args = [java_exe] + jvm_args + ['-cp', classpath, main_class] + game_args

mod_count = len([f for f in os.listdir(mods_dir) if f.endswith(".jar")])
print(f"启动 {VERSION_NAME}")
print(f"  MainClass: {main_class}")
print(f"  Classpath: {len(classpath_parts)}")
print(f"  模组: {mod_count}")
print(f"  GameDir: {VERSION_DIR}")

process = subprocess.Popen(
    full_args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=VERSION_DIR,
)

print(f"  PID: {process.pid}")
print(f"  等待30秒...")

time.sleep(30)

poll = process.poll()
if poll is None:
    print(f"\n  [OK] 游戏正在运行!")
    log_path = os.path.join(VERSION_DIR, "logs", "latest.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            fabric_lines = [l for l in content.split("\n") if "Fabric" in l or "fabric" in l.lower() or "mod" in l.lower()]
            print(f"  日志中Fabric相关行: {len(fabric_lines)}")
            for l in fabric_lines[:5]:
                print(f"    {l[:100]}")
else:
    print(f"\n  [WARN] 进程退出码: {poll}")
    output = process.stdout.read(20000).decode("utf-8", errors="replace")
    lines = output.split("\n")
    for l in lines[-30:]:
        if l.strip():
            print(f"  {l[:200]}")
