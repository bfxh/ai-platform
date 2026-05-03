import subprocess
import time
import os
import ctypes

HMCL_PATH = r"%GAME_DIR%\HMCL-3.12.4.exe"
MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"

def find_minecraft_window():
    user32 = ctypes.windll.user32
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
    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    user32.ShowWindow(hwnd, 9)
    time.sleep(1)

def wait_for_game(version_name, timeout=300):
    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    latest_log = os.path.join(version_dir, "logs", "latest.log")

    start_time = time.time()
    last_pos = 0

    if os.path.exists(latest_log):
        last_pos = os.path.getsize(latest_log)

    while time.time() - start_time < timeout:
        if os.path.exists(latest_log):
            try:
                size = os.path.getsize(latest_log)
                if size > last_pos:
                    with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(last_pos)
                        new_content = f.read()
                    last_pos = size

                    if "Saving chunks" in new_content or "Preparing spawn area" in new_content:
                        return True, "游戏加载成功"
                    if "Loaded 0 advancements" in new_content:
                        return True, "游戏已加载"
                    if "Starting integrated minecraft server" in new_content:
                        return True, "单人世界已启动"
                    if "Stopping!" in new_content and time.time() - start_time > 30:
                        return False, "游戏崩溃/停止"
            except:
                pass
        time.sleep(5)

    return False, "超时"

def launch_hmcl(version_name):
    print(f"  通过HMCL启动 {version_name}...")

    cmd = [HMCL_PATH, "--launch", version_name]

    try:
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(HMCL_PATH),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        print(f"  HMCL进程已启动: PID={process.pid}")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_modpack(version_name):
    print(f"\n{'='*60}")
    print(f"  测试: {version_name}")
    print(f"{'='*60}")

    version_dir = os.path.join(MINECRAFT_DIR, "versions", version_name)
    if not os.path.exists(version_dir):
        print(f"  ERROR: 版本目录不存在: {version_dir}")
        return False

    log_file = os.path.join(version_dir, "logs", "latest.log")
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except:
            pass

    success = launch_hmcl(version_name)
    if not success:
        return False

    print("  等待游戏窗口...")
    for i in range(60):
        time.sleep(3)
        windows = find_minecraft_window()
        if windows:
            hwnd, title = windows[0]
            if "Hello Minecraft" not in title:
                print(f"  找到游戏窗口: {title}")
                activate_window(hwnd)
                break
        if i % 10 == 0 and i > 0:
            print(f"  等待中... ({i*3}s)")
    else:
        print("  WARNING: 未找到游戏窗口，继续等待日志...")

    print("  等待游戏加载...")
    loaded, detail = wait_for_game(version_name, timeout=300)

    if loaded:
        print(f"  ✓ {detail}")
        return True
    else:
        print(f"  ✗ {detail}")
        return False

if __name__ == "__main__":
    import sys
    version = sys.argv[1] if len(sys.argv) > 1 else "我即是虫群v2.0"

    print("=" * 60)
    print(f"  Minecraft 整合包自动测试器 (HMCL)")
    print(f"  版本: {version}")
    print("=" * 60)

    result = test_modpack(version)
    print(f"\n  结果: {'✓ 通过' if result else '✗ 失败'}")
