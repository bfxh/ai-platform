import ctypes
import time
import sys

user32 = ctypes.windll.user32

def find_minecraft_window():
    result = []
    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "minecraft" in buf.value.lower():
                result.append((hwnd, buf.value))
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result

def activate_window(hwnd):
    user32.SetForegroundWindow(hwnd)
    user32.ShowWindow(hwnd, 9)
    time.sleep(1)

def get_window_rect(hwnd):
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

def click(x, y):
    import pyautogui
    pyautogui.click(x, y)
    time.sleep(0.5)

def type_text(text):
    import pyautogui
    pyautogui.write(text, interval=0.1)
    time.sleep(0.5)

def press_key(key):
    import pyautogui
    pyautogui.press(key)
    time.sleep(0.5)

def enter_world():
    windows = find_minecraft_window()
    if not windows:
        print("ERROR: Minecraft窗口未找到!")
        return False

    hwnd, title = windows[0]
    print(f"找到窗口: {title}")

    SW_RESTORE = 9
    SW_SHOW = 5
    SW_MAXIMIZE = 3
    WM_SYSCOMMAND = 0x0112
    SC_RESTORE = 0xF120

    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.5)
    user32.ShowWindow(hwnd, SW_SHOW)
    time.sleep(0.5)
    ctypes.windll.user32.SendMessageW(hwnd, WM_SYSCOMMAND, SC_RESTORE, 0)
    time.sleep(0.5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(2)

    left, top, right, bottom = get_window_rect(hwnd)

    if left < 0 or top < 0 or right - left < 100:
        print(f"窗口仍最小化 ({left},{top})-({right},{bottom})，尝试最大化...")
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        time.sleep(2)
        user32.SetForegroundWindow(hwnd)
        time.sleep(1)
        left, top, right, bottom = get_window_rect(hwnd)

    if left < 0 or top < 0 or right - left < 100:
        print("ERROR: 无法恢复窗口!")
        return False
    width = right - left
    height = bottom - top
    center_x = left + width // 2
    center_y = top + height // 2

    print(f"窗口位置: ({left}, {top}) - ({right}, {bottom})")
    print(f"窗口大小: {width}x{height}")

    print("点击单人游戏...")
    click(center_x, center_y + height // 6)
    time.sleep(3)

    print("点击创建新的世界...")
    click(center_x + width // 4, center_y + height * 2 // 5)
    time.sleep(2)

    print("输入世界名称...")
    press_key('tab')
    time.sleep(0.5)
    press_key('tab')
    time.sleep(0.5)

    for _ in range(20):
        press_key('backspace')
    time.sleep(0.5)

    type_text("ParasiteTest")
    time.sleep(1)

    print("点击创建...")
    click(center_x, center_y + height * 2 // 5)
    time.sleep(2)

    click(center_x, center_y + height // 3)
    time.sleep(2)

    print("等待世界加载...")
    time.sleep(30)

    print("世界进入完成!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  自动进入世界")
    print("=" * 60)

    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3
    except ImportError:
        print("ERROR: pyautogui未安装!")
        print("请运行: pip install pyautogui")
        sys.exit(1)

    result = enter_world()
    print(f"\n结果: {'成功' if result else '失败'}")
