import os
import json
import subprocess

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)
VERSION_JSON = os.path.join(VERSION_DIR, f"{VERSION_NAME}.json")

print("检查当前版本配置...")
with open(VERSION_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

main_class = data.get("mainClass", "")
print(f"  mainClass: {main_class}")

is_neoforge = "bootstraplauncher" in main_class.lower() or "neoforge" in main_class.lower() or "fml" in str(data.get("arguments", {}).get("game", []))
is_fabric = "fabric" in main_class.lower() or "launch" in main_class.lower()

print(f"  NeoForge: {is_neoforge}")
print(f"  Fabric: {is_fabric}")

mods_dir = os.path.join(VERSION_DIR, "mods")
fabric_mods = []
neoforge_mods = []
for f in os.listdir(mods_dir):
    if not f.endswith(".jar"):
        continue
    fl = f.lower()
    if "fabric" in fl or "fabric-api" in fl:
        fabric_mods.append(f)
    if "neoforge" in fl or "neoforge" in fl:
        neoforge_mods.append(f)

print(f"\n  Fabric模组: {len(fabric_mods)}")
for m in fabric_mods[:5]:
    print(f"    {m}")
print(f"  NeoForge模组: {len(neoforge_mods)}")
for m in neoforge_mods[:5]:
    print(f"    {m}")

total_mods = len([f for f in os.listdir(mods_dir) if f.endswith(".jar")])
print(f"\n  总模组数: {total_mods}")

if is_neoforge and len(fabric_mods) > len(neoforge_mods):
    print("\n  [问题] 版本是NeoForge但大部分模组是Fabric的!")
    print("  [解决] 需要将版本JSON改为Fabric加载器")
elif is_fabric:
    print("\n  [OK] 版本已经是Fabric")
else:
    print("\n  [INFO] 需要确认加载器类型")

print("\n--- 检查HMCL配置 ---")
hmcl_json = os.path.join(MC_DIR, "..", "hmcl.json")
if os.path.exists(hmcl_json):
    with open(hmcl_json, "r", encoding="utf-8") as f:
        hmcl = json.load(f)
    print(f"  HMCL配置: {hmcl_json}")
else:
    hmcl_json_alt = os.path.join(r"%GAME_DIR%", "hmcl.json")
    if os.path.exists(hmcl_json_alt):
        with open(hmcl_json_alt, "r", encoding="utf-8") as f:
            hmcl = json.load(f)
        print(f"  HMCL配置: {hmcl_json_alt}")

print("\n--- 检查Fabric加载器是否已安装 ---")
fabric_versions = [d for d in os.listdir(os.path.join(MC_DIR, "versions")) if "fabric" in d.lower()]
print(f"  Fabric版本目录: {fabric_versions}")

fabric_loader_dir = os.path.join(MC_DIR, "libraries", "net", "fabricmc")
if os.path.exists(fabric_loader_dir):
    print(f"  Fabric Loader库: 存在")
    for root, dirs, files in os.walk(fabric_loader_dir):
        for f in files:
            if f.endswith(".jar"):
                print(f"    {os.path.join(root, f)}")
else:
    print(f"  Fabric Loader库: 不存在!")

print("\n--- 检查1.20.4基础版本 ---")
base_version_dir = os.path.join(MC_DIR, "versions", "1.20.4")
if os.path.exists(base_version_dir):
    print(f"  1.20.4基础版本: 存在")
    base_json = os.path.join(base_version_dir, "1.20.4.json")
    if os.path.exists(base_json):
        print(f"  1.20.4.json: 存在")
else:
    print(f"  1.20.4基础版本: 不存在!")
