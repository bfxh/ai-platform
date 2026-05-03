import os
import shutil

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群v2.0"

version_dir = os.path.join(MINECRAFT_DIR, "versions", VERSION_NAME)
mods_dir = os.path.join(version_dir, "mods")

ASM_MODS = [
    "EntityCulling",
    "BetterFps",
    "SmoothFont",
    "OptiFine",
    "surge",
    "phosphor",
    "Hodgepodge",
]

disabled_count = 0
enabled_count = 0

for f in os.listdir(mods_dir):
    if f.endswith(".jar.disabled"):
        mod_name = f.replace(".jar.disabled", "")
        should_stay_disabled = False
        for asm_mod in ASM_MODS:
            if asm_mod.lower() in f.lower():
                should_stay_disabled = True
                break
        if not should_stay_disabled:
            new_name = f.replace(".disabled", "")
            shutil.move(os.path.join(mods_dir, f), os.path.join(mods_dir, new_name))
            enabled_count += 1
            print(f"  Re-enabled: {new_name}")
    elif f.endswith(".jar"):
        should_disable = False
        for asm_mod in ASM_MODS:
            if asm_mod.lower() in f.lower():
                should_disable = True
                break
        if should_disable:
            shutil.move(os.path.join(mods_dir, f), os.path.join(mods_dir, f + ".disabled"))
            disabled_count += 1
            print(f"  Disabled: {f}")
        else:
            enabled_count += 1

print(f"\nDisabled {disabled_count} ASM mods")
print(f"Active mods: {enabled_count}")
