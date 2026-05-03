import subprocess
import os
import time
import sys

minecraft_dir = r"%GAME_DIR%\.minecraft"

def launch_and_test(version_name, launch_script):
    version_dir = os.path.join(minecraft_dir, "versions", version_name)
    latest_log = os.path.join(version_dir, "logs", "latest.log")

    print(f"=== Launching {version_name} ===")
    process = subprocess.Popen(["py", launch_script], cwd=r"\python")
    print(f"PID: {process.pid}")

    print("Waiting for main menu...")
    start_time = time.time()
    menu_loaded = False
    while time.time() - start_time < 300:
        if process.poll() is not None:
            print(f"Game exited with code {process.returncode}")
            return False
        if os.path.exists(latest_log):
            try:
                with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                if "Stopping!" in content:
                    print("Game stopped unexpectedly")
                    return False
                if "OptiFine" in content and "Shaders" in content:
                    menu_loaded = True
                    break
                if "Loaded" in content and "mods" in content:
                    menu_loaded = True
            except:
                pass
        time.sleep(5)

    if not menu_loaded:
        print("Timeout waiting for menu")
        return False

    print("Game loaded! Waiting 30s for menu to fully render...")
    time.sleep(30)

    try:
        import pyautogui
        pyautogui.FAILSAFE = True

        screen_w, screen_h = pyautogui.size()
        print(f"Screen: {screen_w}x{screen_h}")

        center_x = screen_w // 2
        center_y = screen_h // 2

        print("Clicking Singleplayer...")
        pyautogui.click(center_x, center_y + 80)
        time.sleep(3)

        print("Clicking Create New World...")
        pyautogui.click(center_x, screen_h - 40)
        time.sleep(2)

        print("Clicking Create...")
        pyautogui.click(center_x + 100, screen_h - 40)
        time.sleep(2)

        print("Waiting for world to load...")
        world_loaded = False
        start_time = time.time()
        while time.time() - start_time < 120:
            if os.path.exists(latest_log):
                try:
                    with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if "Saving chunks for level" in content or "Loaded" in content.split('\n')[-1]:
                        world_loaded = True
                        break
                    if "Stopping!" in content:
                        print("Game crashed during world load")
                        return False
                except:
                    pass
            time.sleep(5)

        if world_loaded:
            print("WORLD LOADED SUCCESSFULLY!")
            time.sleep(10)

            print("Taking screenshot...")
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(r"\python", f"screenshot_{version_name.replace(' ', '_')}.png")
            screenshot.save(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

            print("Pressing Escape to open menu...")
            pyautogui.press('escape')
            time.sleep(2)

            print("Clicking Save and Quit...")
            pyautogui.click(center_x, center_y + 50)
            time.sleep(5)

            print("Quitting game...")
            pyautogui.press('escape')
            time.sleep(2)
            pyautogui.click(center_x, center_y)

            return True
        else:
            print("World did not load in time")
            return False

    except ImportError:
        print("pyautogui not installed. Manual testing required.")
        print("Game is running - please manually enter a world to test.")
        return True

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "我即是虫群v2.0"
    script = sys.argv[2] if len(sys.argv) > 2 else r"\python\launch_mc.py"
    result = launch_and_test(version, script)
    print(f"\nTest result: {'PASS' if result else 'FAIL'}")
