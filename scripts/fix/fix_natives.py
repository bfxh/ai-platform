import os
import zipfile
import glob

NATIVES_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\natives"
LIB_DIR = r"%GAME_DIR%\.minecraft\libraries"

for old_dll in glob.glob(os.path.join(NATIVES_DIR, "*.dll")):
    os.remove(old_dll)
    print(f"  Removed old: {os.path.basename(old_dll)}")

natives_jars = glob.glob(os.path.join(LIB_DIR, "org", "lwjgl", "**", "*3.3.3*natives-windows.jar"), recursive=True)
natives_jars += glob.glob(os.path.join(LIB_DIR, "org", "lwjgl", "**", "*3.3.2*natives-windows.jar"), recursive=True)

extracted = 0
for nj in natives_jars:
    if "arm64" in nj or "x86" in nj:
        continue
    try:
        with zipfile.ZipFile(nj, 'r') as zf:
            for name in zf.namelist():
                if name.endswith(".dll") and not name.endswith("32.dll"):
                    data = zf.read(name)
                    basename = os.path.basename(name)
                    out_path = os.path.join(NATIVES_DIR, basename)
                    with open(out_path, "wb") as f:
                        f.write(data)
                    print(f"  Extracted: {basename} ({len(data)//1024}KB) from {os.path.basename(nj)}")
                    extracted += 1
    except Exception as e:
        print(f"  Error with {os.path.basename(nj)}: {e}")

print(f"\nTotal DLLs extracted: {extracted}")
print(f"Files in natives dir:")
for f in os.listdir(NATIVES_DIR):
    fp = os.path.join(NATIVES_DIR, f)
    if os.path.isfile(fp):
        print(f"  {f} - {os.path.getsize(fp)//1024}KB")
