import ctypes
import time

user32 = ctypes.windll.user32
result = []

def callback(hwnd, _):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        if "minecraft" in title.lower():
            result.append(title)
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
user32.EnumWindows(WNDENUMPROC(callback), 0)

for title in result:
    print(f"Found: {title}")

if not result:
    print("No Minecraft window found")
