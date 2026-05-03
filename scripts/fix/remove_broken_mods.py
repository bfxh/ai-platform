import os

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\mods"

REMOVE_MISSING_DEPS = [
    "advancementplaques-1.6.1-fabric.jar",
    "trashcans-1.0.18-fabric.jar",
    "mns-moogs-nether-structures-2.0.3-fabric.jar",
    "craftpresence-2.7.1-fabric.jar",
    "netherportalfix-15.0.1-fabric.jar",
    "waystones-16.0.5-fabric.jar",
    "awesomedungeonocean-3.3.0-fabric.jar",
]

removed = 0
for f in REMOVE_MISSING_DEPS:
    fp = os.path.join(MODS_DIR, f)
    if os.path.exists(fp):
        os.remove(fp)
        print(f"  [DEL] {f}")
        removed += 1

mod_count = len([f for f in os.listdir(MODS_DIR) if f.endswith(".jar")])
print(f"\n移除: {removed}")
print(f"剩余模组: {mod_count}")
