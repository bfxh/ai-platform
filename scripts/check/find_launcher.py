import os

search_dirs = [r"D:\rj", r"\python", r"%DEV_DIR%", r"%SOFTWARE_INSTALL_DIR%", r"E:\%USERNAME%"]
found = []
for sd in search_dirs:
    if not os.path.exists(sd):
        continue
    for root, dirs, files in os.walk(sd):
        for f in files:
            fl = f.lower()
            if ("hmcl" in fl or "minecraft" in fl) and fl.endswith((".exe", ".jar")):
                found.append(os.path.join(root, f))
        if len(found) > 10:
            break
    if len(found) > 10:
        break

if found:
    print("Found launchers:")
    for p in found:
        print(f"  {p}")
else:
    print("No Minecraft/HMCL launchers found in search directories")
    print("Checking common paths...")
    common = [
        r"C:\Program Files\Minecraft Launcher\MinecraftLauncher.exe",
        r"C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Minecraft Launcher", "MinecraftLauncher.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Minecraft Launcher", "MinecraftLauncher.exe"),
    ]
    for p in common:
        if os.path.exists(p):
            print(f"  Found: {p}")
