import os
import json
import subprocess
import glob
import time
import shutil

MC_DIR = r"%GAME_DIR%\.minecraft"
RUN_DIR = r"%GAME_DIR%\运行路径"
VER_DIR = os.path.join(MC_DIR, "versions", "我即是虫群-1.20.4-Fabric")
LIB_DIR = os.path.join(MC_DIR, "libraries")
MODS_DIR = os.path.join(RUN_DIR, "mods")
NATIVES_DIR = os.path.join(VER_DIR, "natives")

JAVA = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\javaw.exe"

ver_json_path = os.path.join(VER_DIR, "我即是虫群-1.20.4-Fabric.json")
with open(ver_json_path, "r", encoding="utf-8") as f:
    ver_json = json.load(f)

base_json_path = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.json")
with open(base_json_path, "r", encoding="utf-8") as f:
    base_json = json.load(f)

classpath_parts = []

mc_jar = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.jar")
if os.path.exists(mc_jar):
    classpath_parts.append(mc_jar)

def resolve_lib_name(name):
    parts = name.split(":")
    if len(parts) >= 3:
        group = parts[0].replace(".", os.sep)
        artifact = parts[1]
        version = parts[2]
        return os.path.join(group, artifact, version, f"{artifact}-{version}.jar")
    return None

def add_lib(lib):
    name = lib.get("name", "")
    rel_path = resolve_lib_name(name)
    if rel_path:
        abs_path = os.path.join(LIB_DIR, rel_path)
        if os.path.exists(abs_path):
            classpath_parts.append(abs_path)
            return True
    downloads = lib.get("downloads", {})
    artifact = downloads.get("artifact", {})
    path = artifact.get("path", "")
    if path:
        abs_path = os.path.join(LIB_DIR, path)
        if os.path.exists(abs_path):
            classpath_parts.append(abs_path)
            return True
    return False

for lib in ver_json.get("libraries", []):
    add_lib(lib)

for lib in base_json.get("libraries", []):
    add_lib(lib)

mod_jars = sorted(glob.glob(os.path.join(MODS_DIR, "*.jar")))

classpath = ";".join(classpath_parts + mod_jars)

jvm_args = [
    JAVA,
    "-Xmx4G",
    "-Xms1G",
    f"-Djava.library.path={NATIVES_DIR}",
    "-Dminecraft.launcher.brand=HMCL",
    "-Dminecraft.launcher.version=3.12.4",
    "-XX:+UnlockExperimentalVMOptions",
    "-XX:+UseG1GC",
    "-XX:G1NewSizePercent=20",
    "-XX:G1ReservePercent=20",
    "-XX:MaxGCPauseMillis=50",
    "-XX:G1HeapRegionSize=32M",
    "-cp", classpath,
    "net.fabricmc.loader.impl.launch.knot.KnotClient",
    "--username", "SwarmPlayer",
    "--version", "我即是虫群-1.20.4-Fabric",
    "--gameDir", RUN_DIR,
    "--assetsDir", os.path.join(MC_DIR, "assets"),
    "--assetIndex", "12",
    "--uuid", "00000000000000000000000000000000",
    "--accessToken", "0",
    "--userType", "mojang",
    "--versionType", "我即是虫群-1.20.4-Fabric",
]

print(f"Launching with {len(mod_jars)} mods, {len(classpath_parts)} libs")

log_file = open(os.path.join(RUN_DIR, "game_output.log"), "w", encoding="utf-8")

try:
    proc = subprocess.Popen(
        jvm_args,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=RUN_DIR,
    )
except Exception:
    log_file.close()
    raise

print(f"PID: {proc.pid}")
print("Waiting 90 seconds for game to load...")

for i in range(9):
    time.sleep(10)
    mc_log = os.path.join(RUN_DIR, "logs", "latest.log")
    if os.path.exists(mc_log):
        size = os.path.getsize(mc_log)
        print(f"  {(i+1)*10}s: log size = {size} bytes")
        if size > 10000:
            with open(mc_log, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            started = any("Started" in l for l in lines[-30:])
            if started:
                print("\n*** GAME LOADED SUCCESSFULLY! ***")
                break

log_file.close()

mc_log = os.path.join(RUN_DIR, "logs", "latest.log")
if os.path.exists(mc_log):
    with open(mc_log, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print(f"\nLatest log ({len(lines)} lines):")
    for line in lines[-15:]:
        print(f"  {line.rstrip()}")

game_log = os.path.join(RUN_DIR, "game_output.log")
if os.path.exists(game_log):
    with open(game_log, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if content.strip():
        print(f"\nGame output ({len(content)} bytes):")
        print(content[-2000:])
