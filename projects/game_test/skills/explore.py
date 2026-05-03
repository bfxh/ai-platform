#!/usr/bin/env python3
"""
游戏探索技能 - 以玩家视角操控游戏角色
支持：移动、跳跃、攻击、交互、截图验证
"""
import ctypes
import sys
import time
from pathlib import Path

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.2
except ImportError:
    pyautogui = None

try:
    from PIL import Image
except ImportError:
    Image = None

SCREENSHOT_DIR = Path("/python/projects/game_test/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

DIRECTION_KEYS = {
    "forward": "w",
    "backward": "s",
    "left": "a",
    "right": "d",
    "up": "space",
    "down": "shift",
}


def _screenshot(name: str):
    if pyautogui is None:
        return
    ts = int(time.time())
    path = SCREENSHOT_DIR / f"explore_{name}_{ts}.png"
    try:
        pyautogui.screenshot().save(str(path))
    except Exception:
        pass


def _activate_game_window(title: str = ""):
    if not title:
        return
    user32 = ctypes.windll.user32
    result = []

    def callback(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title.lower() in buf.value.lower():
                result.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    if result:
        user32.SetForegroundWindow(result[0])
        user32.ShowWindow(result[0], 9)
        time.sleep(0.5)
        return True
    return False


def move(direction: str = "forward", duration: float = 2.0, verify: bool = True):
    key = DIRECTION_KEYS.get(direction, "w")
    if verify:
        _screenshot(f"move_{direction}_before")
    if pyautogui:
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)
    else:
        time.sleep(duration)
    if verify:
        _screenshot(f"move_{direction}_after")
    print(f"[explore] moved {direction} for {duration}s")


def jump(count: int = 1, interval: float = 0.5):
    for i in range(count):
        _screenshot(f"jump_{i}_before")
        if pyautogui:
            pyautogui.press("space")
        time.sleep(interval)
        _screenshot(f"jump_{i}_after")
    print(f"[explore] jumped {count} times")


def attack(duration: float = 0.5):
    _screenshot("attack_before")
    if pyautogui:
        pyautogui.mouseDown(button="left")
        time.sleep(duration)
        pyautogui.mouseUp(button="left")
    else:
        time.sleep(duration)
    _screenshot("attack_after")
    print(f"[explore] attacked for {duration}s")


def interact(key: str = "e", wait: float = 2.0):
    _screenshot("interact_before")
    if pyautogui:
        pyautogui.press(key)
    time.sleep(wait)
    _screenshot("interact_after")
    print(f"[explore] interacted with key={key}")


def look_around(angle: float = 200, directions: list = None):
    if directions is None:
        directions = ["right", "left", "up", "down"]
    move_map = {
        "right": (angle, 0),
        "left": (-angle, 0),
        "up": (0, -angle),
        "down": (0, angle),
    }
    for d in directions:
        dx, dy = move_map.get(d, (angle, 0))
        _screenshot(f"look_{d}_before")
        if pyautogui:
            pyautogui.moveRel(dx, dy, duration=0.5)
        time.sleep(0.5)
        _screenshot(f"look_{d}_after")
    print(f"[explore] looked around: {directions}")


def full_explore(move_duration: float = 2.0):
    print("[explore] === 开始完整探索 ===")
    _screenshot("explore_start")

    print("[explore] 1. 移动测试")
    for d in ["forward", "backward", "left", "right"]:
        move(d, move_duration)

    print("[explore] 2. 跳跃测试")
    jump(3)

    print("[explore] 3. 视角测试")
    look_around()

    print("[explore] 4. 攻击测试")
    attack()

    print("[explore] 5. 交互测试")
    interact()

    print("[explore] 6. 综合移动")
    move("forward", 3.0, verify=False)
    jump(1)
    move("left", 1.0, verify=False)
    move("forward", 2.0, verify=False)
    attack()
    move("right", 1.0, verify=False)

    _screenshot("explore_end")
    print("[explore] === 探索完成 ===")


def record_result(success: bool = True, details: str = ""):
    status = "PASS" if success else "FAIL"
    _screenshot(f"result_{status}")
    print(f"[explore] result: {status} - {details}")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "full_explore"

    if action == "move":
        d = sys.argv[2] if len(sys.argv) > 2 else "forward"
        dur = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
        move(d, dur)
    elif action == "jump":
        cnt = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        jump(cnt)
    elif action == "attack":
        attack()
    elif action == "interact":
        k = sys.argv[2] if len(sys.argv) > 2 else "e"
        interact(k)
    elif action == "look_around":
        look_around()
    elif action == "full_explore":
        full_explore()
    elif action == "record_result":
        record_result()
    else:
        print(f"[explore] unknown action: {action}")
        print("available: move, jump, attack, interact, look_around, full_explore, record_result")
