import time
import os
import ctypes

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"

def find_window(title_part):
    user32 = ctypes.windll.user32
    result = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_part.lower() in buf.value.lower():
                result.append((hwnd, buf.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result

print("Waiting for NeoForge installer to complete...")

for i in range(120):
    windows = find_window("neoforge")
    if not windows:
        print("Installer window closed - installation likely complete!")
        break
    
    hwnd, title = windows[0]
    if "success" in title.lower() or "complete" in title.lower():
        print("Installation successful!")
        break
    
    if i % 12 == 0:
        print(f"  Still running... ({i*5}s) - Window: {title}")
    
    time.sleep(5)

print("\nChecking installation results...")

neoforge_versions = []
for d in os.listdir(os.path.join(MINECRAFT_DIR, "versions")):
    if "neoforge" in d.lower() or "20.4" in d:
        neoforge_versions.append(d)

print(f"NeoForge-related versions: {neoforge_versions}")

neoforge_lib = os.path.join(MINECRAFT_DIR, "libraries", "net", "neoforged", "neoforge", "20.4.237")
if os.path.exists(neoforge_lib):
    print(f"NeoForge 20.4.237 libraries:")
    for f in os.listdir(neoforge_lib):
        fpath = os.path.join(neoforge_lib, f)
        print(f"  {f} ({os.path.getsize(fpath)//1024}KB)")
else:
    print("NeoForge 20.4.237 libraries NOT found")

client_jar = os.path.join(MINECRAFT_DIR, "libraries", "net", "neoforged", "neoforge", "20.4.237", "neoforge-20.4.237-client.jar")
if os.path.exists(client_jar):
    print(f"NeoForge client JAR exists: {os.path.getsize(client_jar)//1024}KB")
else:
    print("NeoForge client JAR NOT found - processor may not have run")
