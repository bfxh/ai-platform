import os
import json
import subprocess
import glob
import time

MC_DIR = r"%GAME_DIR%\.minecraft"
RUN_DIR = r"%GAME_DIR%\运行路径"
VER_DIR = os.path.join(MC_DIR, "versions", "我即是虫群-1.20.4-Fabric")
LIB_DIR = os.path.join(MC_DIR, "libraries")
MODS_DIR = os.path.join(RUN_DIR, "mods")
NATIVES_DIR = os.path.join(VER_DIR, "natives")

JAVA = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\java.exe"

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
    "-Dorg.lwjgl.system.SharedLibraryExtractPath=" + NATIVES_DIR,
    "-Dlwjgl.debug=true",
    "-cp", classpath,
    "net.fabricmc.loader.impl.launch.knot.KnotClient",
    "--username", "Player",
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
print(f"Java: {JAVA}")
print(f"Natives: {NATIVES_DIR}")
print(f"GameDir: {RUN_DIR}")

proc = subprocess.Popen(
    jvm_args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=RUN_DIR,
    text=True,
    encoding="utf-8",
    errors="replace"
)

print(f"PID: {proc.pid}")
print("Reading output...")

start_time = time.time()
output_lines = []
while time.time() - start_time < 120:
    line = proc.stdout.readline()
    if line:
        output_lines.append(line.rstrip())
        if len(output_lines) > 500:
            output_lines = output_lines[-500:]
        if "LWJGL" in line or "OpenGL" in line or "Started" in line or "error" in line.lower() or "exception" in line.lower():
            print(f"  {line.rstrip()}")
    else:
        if proc.poll() is not None:
            print(f"Process exited with code: {proc.returncode}")
            break
        time.sleep(0.1)
    
    if time.time() - start_time > 30 and len(output_lines) < 5:
        print(f"  ... waiting ({int(time.time()-start_time)}s), {len(output_lines)} lines read")

print(f"\nTotal output lines: {len(output_lines)}")
print("\nLast 30 lines:")
for line in output_lines[-30:]:
    print(f"  {line}")
