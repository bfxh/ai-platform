import zipfile
import os

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
NEOFORGE_VERSION = "20.4.237"

installer_path = os.path.join(MINECRAFT_DIR, f"neoforge-{NEOFORGE_VERSION}-installer.jar")

print(f"Extracting NeoForge installer args...")

with zipfile.ZipFile(installer_path, "r") as zf:
    win_args_path = None
    for name in zf.namelist():
        if "win_args" in name.lower():
            print(f"Found: {name}")
            win_args_path = name

    if win_args_path:
        content = zf.read(win_args_path).decode("utf-8")
        print(f"\nContent of {win_args_path}:")
        print(content[:2000])

        lines = content.split("\n")
        for line in lines:
            if "java" in line.lower() or "cp" in line.lower() or "classpath" in line.lower():
                print(f"  ARG: {line[:200]}")
