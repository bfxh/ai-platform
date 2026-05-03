import os
import shutil

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"
BACKUP_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods_backup"

REMOVE_MODS = [
    "more_mobs-v1.5.9-mc1.14-26.1.9-mod.jar",
    "dynamiclights-v1.9.2-mc1.17-26.1.1-mod.jar",
    "sorted_enchantments-2.0.0+1.19.3+fabric.jar",
    "rhino-2004.2.3-build.4.jar",
    "Patchouli-1.20.4-85-FABRIC.jar",
    "DungeonsAriseSevenSeas-1.21.x-1.0.4-fabric.jar",
    "fantasy_weapons-fabric-0.3.1-1.20.1.jar",
]

os.makedirs(BACKUP_DIR, exist_ok=True)

removed = 0
for mod in REMOVE_MODS:
    src = os.path.join(MODS_DIR, mod)
    dst = os.path.join(BACKUP_DIR, mod)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"  [MOVED] {mod}")
        removed += 1
    else:
        print(f"  [NOT FOUND] {mod}")

jars = [f for f in os.listdir(MODS_DIR) if f.endswith(".jar")]
print(f"\nRemoved: {removed}")
print(f"Remaining mods: {len(jars)}")
