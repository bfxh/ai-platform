import ctypes
import ctypes.wintypes
import time
import subprocess

user32 = ctypes.windll.user32

def find_minecraft_hwnd():
    result = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "minecraft" in buf.value.lower():
                result.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result[0] if result else None

hwnd = find_minecraft_hwnd()
if not hwnd:
    print("No Minecraft window found!")
    exit(1)

print(f"Found HWND: {hwnd}")

SW_RESTORE = 9
SW_SHOWMAXIMIZED = 3
SW_SHOW = 5

print("Method 1: ShowWindow SW_RESTORE...")
user32.ShowWindow(hwnd, SW_RESTORE)
time.sleep(1)

rect = ctypes.wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
print(f"  Rect: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")

if rect.left < 0:
    print("Method 2: ShowWindow SW_SHOWMAXIMIZED...")
    user32.ShowWindow(hwnd, SW_SHOWMAXIMIZED)
    time.sleep(1)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"  Rect: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")

if rect.left < 0:
    print("Method 3: SetWindowPos...")
    user32.SetWindowPos(hwnd, 0, 100, 100, 1280, 720, 0x0040)
    time.sleep(1)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"  Rect: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")

if rect.left < 0:
    print("Method 4: BringWindowToTop + SetForegroundWindow...")
    user32.BringWindowToTop(hwnd)
    time.sleep(0.5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)
    user32.ShowWindow(hwnd, SW_SHOW)
    time.sleep(1)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"  Rect: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")

if rect.left >= 0 and rect.right - rect.left > 100:
    print(f"SUCCESS! Window at ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")
else:
    print("FAILED to restore window")
    print("Trying keyboard shortcut Alt+Tab...")
    import pyautogui
    pyautogui.keyDown('alt')
    time.sleep(0.1)
    pyautogui.press('tab')
    time.sleep(0.1)
    pyautogui.keyUp('alt')
    time.sleep(2)
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    print(f"  After Alt+Tab: ({rect.left}, {rect.top}) - ({rect.right}, {rect.bottom})")
