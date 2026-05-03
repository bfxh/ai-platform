import os
import subprocess
import json

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)

print("=" * 60)
print("  \u866b\u65cf\u53d8\u5f62\u6574\u5408\u5305\u542f\u52a8")
print(f"  \u7248\u672c: {VERSION_NAME}")
print("=" * 60)

mods_dir = os.path.join(VERSION_DIR, "mods")
jar_count = len([f for f in os.listdir(mods_dir) if f.endswith(".jar")]) if os.path.exists(mods_dir) else 0
print(f"\n  \u6a21\u7ec4\u6570\u91cf: {jar_count}")

swarm_dp = os.path.join(VERSION_DIR, "resourcepacks", "swarm_origins")
if os.path.exists(swarm_dp):
    origins = [f for f in os.listdir(os.path.join(swarm_dp, "data", "swarm_origins", "origins")) if f.endswith(".json") and f != "origin.json"]
    print(f"  \u866b\u65cf\u53d8\u5f62: {len(origins)}\u4e2a")
    powers = [f for f in os.listdir(os.path.join(swarm_dp, "data", "swarm_origins", "powers")) if f.endswith(".json")]
    print(f"  \u80fd\u529b\u6570\u91cf: {len(powers)}\u4e2a")
else:
    print("  \u866b\u65cf\u53d8\u5f62datapack: \u672a\u627e\u5230!")

parasite_dp = os.path.join(VERSION_DIR, "resourcepacks", "parasite_origins")
if os.path.exists(parasite_dp):
    p_origins = [f for f in os.listdir(os.path.join(parasite_dp, "data", "parasite_origins", "origins")) if f.endswith(".json") and f != "origin.json"]
    print(f"  \u5bc4\u751f\u866b\u8d77\u6e90: {len(p_origins)}\u4e2a")

print("\n--- \u67e5\u627e\u542f\u52a8\u5668 ---")

launcher_paths = [
    os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Minecraft Launcher", "MinecraftLauncher.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Minecraft Launcher", "MinecraftLauncher.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Minecraft Launcher", "MinecraftLauncher.exe"),
]

launcher = None
for p in launcher_paths:
    if os.path.exists(p):
        launcher = p
        break

hmcl_jar = None
for root, dirs, files in os.walk(r"%GAME_DIR%"):
    for f in files:
        if "hmcl" in f.lower() and f.lower().endswith(".jar"):
            hmcl_jar = os.path.join(root, f)
            break
    if hmcl_jar:
        break

if not hmcl_jar:
    for root, dirs, files in os.walk(r"D:\rj"):
        for f in files:
            if "hmcl" in f.lower() and f.lower().endswith(".jar"):
                hmcl_jar = os.path.join(root, f)
                break
        if hmcl_jar:
            break

if launcher:
    print(f"  \u5b98\u65b9\u542f\u52a8\u5668: {launcher}")
else:
    print(f"  \u5b98\u65b9\u542f\u52a8\u5668: \u672a\u627e\u5230")

if hmcl_jar:
    print(f"  HMCL: {hmcl_jar}")
else:
    print(f"  HMCL: \u672a\u627e\u5230")

print("\n--- \u542f\u52a8\u6e38\u620f ---")

launched = False

if launcher:
    print(f"  \u4f7f\u7528\u5b98\u65b9\u542f\u52a8\u5668...")
    try:
        subprocess.Popen([launcher])
        print(f"  [\u2713] \u542f\u52a8\u5668\u5df2\u542f\u52a8!")
        launched = True
    except Exception as e:
        print(f"  [\u2717] \u542f\u52a8\u5931\u8d25: {e}")

if not launched and hmcl_jar:
    print(f"  \u4f7f\u7528HMCL...")
    try:
        subprocess.Popen(["javaw", "-jar", hmcl_jar], cwd=os.path.dirname(hmcl_jar))
        print(f"  [\u2713] HMCL\u5df2\u542f\u52a8!")
        launched = True
    except Exception as e:
        print(f"  [\u2717] HMCL\u542f\u52a8\u5931\u8d25: {e}")
        try:
            subprocess.Popen(["java", "-jar", hmcl_jar], cwd=os.path.dirname(hmcl_jar))
            print(f"  [\u2713] HMCL\u5df2\u542f\u52a8(java)!")
            launched = True
        except Exception as e2:
            print(f"  [\u2717] \u4e5f\u5931\u8d25: {e2}")

if not launched:
    print(f"  [\u2717] \u672a\u627e\u5230\u542f\u52a8\u5668\uff0c\u8bf7\u624b\u52a8\u542f\u52a8Minecraft")
    print(f"  \u7248\u672c\u540d: {VERSION_NAME}")

print(f"\n--- \u6e38\u620f\u5185\u64cd\u4f5c\u63d0\u793a ---")
print(f"  1. \u9009\u62e9\u7248\u672c: {VERSION_NAME}")
print(f"  2. \u521b\u5efa\u65b0\u4e16\u754c\u6216\u8fdb\u5165\u5df2\u6709\u4e16\u754c")
print(f"  3. \u9996\u6b21\u8fdb\u5165\u4f1a\u5f39\u51fa\u8d77\u6e90\u9009\u62e9\u754c\u9762")
print(f"  4. \u9009\u62e9\u4f60\u7684\u866b\u65cf\u53d8\u5f62:")
print(f"     \u00a7a\u8718\u86db\u866b\u65cf \u00a7c\u7194\u5ca9\u866b\u65cf \u00a75\u672b\u5f71\u866b\u65cf \u00a72\u83cc\u4e1d\u6bcd\u4f53 \u00a7c\u5b75\u80b2\u6bcd\u866b ...")
print(f"  5. \u5982\u679c\u6ca1\u5f39\u51fa\u9009\u62e9\u754c\u9762\uff0c\u4f7f\u7528\u547d\u4ee4: /origin choose")
print(f"  6. \u83cc\u4e1d\u6bcd\u4f53\u7279\u522b\u63d0\u793a: \u5728\u82b1\u6735\u65c1\u8fb9\u56de\u590d\u751f\u547d\uff0c\u6bcf\u56de\u590d100\u70b9=\u751f\u7269\u8d28+1")
