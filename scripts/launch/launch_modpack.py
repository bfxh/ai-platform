import os
import subprocess
import json

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"

def find_minecraft_launcher():
    possible_paths = [
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Minecraft Launcher", "MinecraftLauncher.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Minecraft Launcher", "MinecraftLauncher.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Minecraft Launcher", "MinecraftLauncher.exe"),
        r"C:\Program Files\WindowsApps\Microsoft.4297127D64EC6_1.0.113.0_x64__8wekyb3d8bbwe\MinecraftLauncher.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def find_hmcl():
    possible_paths = []
    for root, dirs, files in os.walk(r"%GAME_DIR%"):
        for f in files:
            if f.lower().startswith("hmcl") and f.lower().endswith(".jar"):
                possible_paths.append(os.path.join(root, f))
        if len(possible_paths) > 3:
            break
    for root, dirs, files in os.walk(r"D:\rj"):
        for f in files:
            if f.lower().startswith("hmcl") and f.lower().endswith(".jar"):
                possible_paths.append(os.path.join(root, f))
        if len(possible_paths) > 5:
            break
    return possible_paths

print("=" * 60)
print("  Minecraft 整合包启动器")
print(f"  版本: {VERSION_NAME}")
print("=" * 60)

mods_dir = os.path.join(MC_DIR, "versions", VERSION_NAME, "mods")
jar_count = len([f for f in os.listdir(mods_dir) if f.endswith(".jar")]) if os.path.exists(mods_dir) else 0
print(f"\n  模组数量: {jar_count}")
print(f"  模组目录: {mods_dir}")

dp_dir = os.path.join(MC_DIR, "versions", VERSION_NAME, "resourcepacks", "parasite_origins")
if os.path.exists(dp_dir):
    print(f"  起源Datapack: 已安装")
    origins = [f for f in os.listdir(os.path.join(dp_dir, "data", "parasite_origins", "origins")) if f.endswith(".json") and f != "origin.json"]
    print(f"  可选起源: {len(origins)}个")
    for o in origins:
        name = o.replace(".json", "")
        print(f"    - {name}")
else:
    print(f"  起源Datapack: 未找到")

print("\n--- 启动方式 ---")

launcher = find_minecraft_launcher()
if launcher:
    print(f"  官方启动器: {launcher}")
else:
    print(f"  官方启动器: 未找到")

hmcl_paths = find_hmcl()
if hmcl_paths:
    print(f"  HMCL启动器: {hmcl_paths[0]}")
else:
    print(f"  HMCL启动器: 未找到")

print("\n--- 尝试启动 ---")

if launcher:
    print(f"  使用官方启动器启动...")
    try:
        subprocess.Popen([launcher])
        print(f"  [OK] 启动器已启动！")
        print(f"\n  启动后请选择版本: {VERSION_NAME}")
    except Exception as e:
        print(f"  [ERR] 启动失败: {e}")
elif hmcl_paths:
    print(f"  使用HMCL启动器启动...")
    try:
        java_path = "javaw"
        subprocess.Popen([java_path, "-jar", hmcl_paths[0]])
        print(f"  [OK] HMCL已启动！")
    except Exception as e:
        print(f"  [ERR] 启动失败: {e}")
else:
    print(f"  [WARN] 未找到任何启动器")
    print(f"  请手动启动Minecraft并选择版本: {VERSION_NAME}")

print(f"\n--- 游戏内操作 ---")
print(f"  1. 创建新世界或进入已有世界")
print(f"  2. 首次进入会弹出起源选择界面")
print(f"  3. 选择你想要的寄生虫起源:")
print(f"     - \u00a7a\u00a7l\u866b\u7fa4\u5e7c\u866b\u00a7r: \u4f53\u578b\u5c0f\u3001\u6500\u58c1\u3001\u611f\u67d3\u4e4b\u89e6")
print(f"     - \u00a72\u00a7l\u771f\u83cc\u5b62\u5b50\u00a7r: \u5b62\u5b50\u4f20\u64ad\u3001\u771f\u83cc\u996e\u98df\u3001\u9633\u5149\u5f31\u70b9")
print(f"     - \u00a7c\u00a7l\u540c\u5316\u5bbf\u4e3b\u00a7r: \u5f3a\u58ee\u8eab\u4f53\u3001\u5bc4\u751f\u529b\u91cf\u3001\u795e\u5723\u5f31\u70b9")
print(f"     - \u00a75\u00a7l\u539f\u521d\u5bc4\u751f\u866b\u00a7r: \u53d8\u5f02\u89e6\u53d1\u3001\u8fdb\u5316\u5149\u73af\u3001\u602f\u6c34")
print(f"     - \u00a7d\u00a7l\u866b\u7fa4\u610f\u8bc6\u00a7r: \u53ec\u5524\u866b\u7fa4\u3001\u795e\u7ecf\u94fe\u63a5\u3001\u5b64\u7acb\u5f31\u70b9")
print(f"  4. 如果没有弹出选择界面，使用命令: /origin choose")
