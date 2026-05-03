import subprocess
import os
import time
import ctypes
import pyautogui

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
JAVA_21 = r"%GAME_DIR%\文件缓存目录\cache\java\java-runtime-delta\windows-x64\java-runtime-delta\bin\java.exe"
NEOFORGE_VERSION = "20.4.237"

installer_path = os.path.join(MINECRAFT_DIR, f"neoforge-{NEOFORGE_VERSION}-installer.jar")

print(f"Running NeoForge installer GUI...")
print(f"  Java: {JAVA_21}")
print(f"  Installer: {installer_path}")

cmd = [
    JAVA_21,
    "-jar", installer_path,
]

process = subprocess.Popen(
    cmd,
    cwd=MINECRAFT_DIR,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)
print(f"  Process started: PID={process.pid}")

time.sleep(10)

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

windows = find_window("neoforge")
if not windows:
    windows = find_window("installer")
if not windows:
    windows = find_window("forge")

if windows:
    hwnd, title = windows[0]
    print(f"  Found window: {title}")
    
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    user32.ShowWindow(hwnd, 9)
    time.sleep(2)
    
    import ctypes.wintypes
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"  Window: ({rect.left},{rect.top})-({rect.right},{rect.bottom})")
    
    center_x = (rect.left + rect.right) // 2
    center_y = (rect.top + rect.bottom) // 2
    
    print("  Clicking OK/Install button...")
    pyautogui.click(center_x, rect.bottom - 60)
    time.sleep(5)
    
    print("  Waiting for installation to complete...")
    for i in range(120):
        time.sleep(5)
        
        new_windows = find_window("success")
        if new_windows:
            print("  Installation successful!")
            break
        
        new_windows = find_window("failed")
        if new_windows:
            print("  Installation failed!")
            break
        
        if i % 6 == 0:
            print(f"  Waiting... ({i*5}s)")
else:
    print("  No installer window found!")

print("\nDone!")
