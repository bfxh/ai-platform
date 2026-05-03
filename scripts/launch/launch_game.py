import os
import json
import subprocess
import sys

MC_DIR = r"%GAME_DIR%\.minecraft"
VER_DIR = os.path.join(MC_DIR, "versions", "我即是虫群-1.20.4-Fabric")
LIB_DIR = os.path.join(MC_DIR, "libraries")
MODS_DIR = os.path.join(VER_DIR, "mods")
NATIVES_DIR = os.path.join(VER_DIR, "natives")

JAVA = r"%USERPROFILE%\AppData\Roaming\.hmcl\java\windows-x86_64\mojang-java-runtime-beta\bin\javaw.exe"
if not os.path.exists(JAVA):
    JAVA = r"C:\Program Files\Microsoft\jdk-17.0.12.7-hotspot\bin\javaw.exe"
if not os.path.exists(JAVA):
    JAVA = r"C:\Program Files\Java\jdk-25.0.2\bin\javaw.exe"

print(f"Java: {JAVA}")
print(f"Java exists: {os.path.exists(JAVA)}")

os.makedirs(NATIVES_DIR, exist_ok=True)

ver_json_path = os.path.join(VER_DIR, "我即是虫群-1.20.4-Fabric.json")
with open(ver_json_path, "r", encoding="utf-8") as f:
    ver_json = json.load(f)

base_json_path = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.json")
with open(base_json_path, "r", encoding="utf-8") as f:
    base_json = json.load(f)

classpath_parts = []

mc_jar = os.path.join(MC_DIR, "versions", "1.20.4", "1.20.4.jar")
classpath_parts.append(mc_jar)

def add_lib(lib):
    name = lib.get("name", "")
    url = lib.get("url", "")
    parts = name.split(":")
    if len(parts) >= 3:
        group = parts[0].replace(".", os.sep)
        artifact = parts[1]
        version = parts[2]
        filename = f"{artifact}-{version}.jar"
        if url and "maven.fabricmc.net" in url:
            lib_path = os.path.join(LIB_DIR, group, artifact, version, filename)
        else:
            lib_path = os.path.join(LIB_DIR, group, artifact, version, filename)
        if os.path.exists(lib_path):
            classpath_parts.append(lib_path)
            return True
        else:
            for root, dirs, files in os.walk(LIB_DIR):
                for fn in files:
                    if fn == filename:
                        classpath_parts.append(os.path.join(root, fn))
                        return True
            return False
    return False

for lib in ver_json.get("libraries", []):
    add_lib(lib)

for lib in base_json.get("libraries", []):
    name = lib.get("name", "")
    if "lwjgl" in name or "net.minecraft" in name or "logging" in name or "guava" in name or "gson" in name or "commons" in name or "jopt" in name or "netty" in name or "authlib" in name or "brigadier" in name or "datafixerupper" in name or "log4j" in name or "slf4j" in name:
        add_lib(lib)

for root, dirs, files in os.walk(LIB_DIR):
    for fn in files:
        if fn.endswith(".jar"):
            fp = os.path.join(root, fn)
            if fp not in classpath_parts:
                rn = fn.lower()
                if any(x in rn for x in ["fabric-loader", "fabric-api", "sponge-mixin", "asm-", "intermediary", "mixinextras"]):
                    classpath_parts.append(fp)

mod_jars = [os.path.join(MODS_DIR, f) for f in os.listdir(MODS_DIR) if f.endswith(".jar")]

print(f"Classpath entries: {len(classpath_parts)}")
print(f"Mod jars: {len(mod_jars)}")

classpath = ";".join(classpath_parts + mod_jars)

jvm_args = [
    JAVA,
    f"-Xmx4G",
    f"-Xms1G",
    f"-Djava.library.path={NATIVES_DIR}",
    f"-Dminecraft.launcher.brand=HMCL",
    f"-Dminecraft.launcher.version=3.12.4",
    f"-cp", classpath,
    "net.fabricmc.loader.impl.launch.knot.KnotClient",
    "--username", "SwarmPlayer",
    "--version", "我即是虫群-1.20.4-Fabric",
    "--gameDir", MC_DIR,
    "--assetsDir", os.path.join(MC_DIR, "assets"),
    "--assetIndex", "12",
    "--uuid", "00000000000000000000000000000000",
    "--accessToken", "0",
    "--userType", "mojang",
    "--versionType", "我即是虫群-1.20.4-Fabric",
]

print(f"\nLaunching Minecraft...")
print(f"  Version: 我即是虫群-1.20.4-Fabric")
print(f"  Mods: {len(mod_jars)}")
print(f"  Java: {JAVA}")
print(f"  Memory: 4GB")

log_path = os.path.join(VER_DIR, "launch_log.txt")
with open(log_path, "w", encoding="utf-8") as log:
    log.write(f"Launch command:\n")
    log.write(f"Java: {JAVA}\n")
    log.write(f"Mods: {len(mod_jars)}\n")
    log.write(f"Classpath entries: {len(classpath_parts)}\n\n")

proc = subprocess.Popen(
    jvm_args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    cwd=MC_DIR,
    text=True,
    encoding="utf-8",
    errors="replace"
)

print(f"Game process started! PID: {proc.pid}")
print(f"Log file: {log_path}")
