"""全自动游戏测试系统 - 自动启动Godot -> 运行游戏 -> 截图 -> E2E测试"""
import subprocess
import time
import os
import sys
from pathlib import Path

GODOT = r"D:\rj\KF\JM\Godot_v4.6.1-stable_win64.exe"
PROJECT = r"D:\rj\KF\JM\GodotProject"
OUTPUT_DIR = r"\MCP_3D\test_output"

def run_headless_test():
    """headless运行GUT单元测试"""
    print("[GUT] Running unit tests...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    result = subprocess.run(
        [GODOT, "--headless", "--path", PROJECT, 
         "-s", "addons/gut/gut_cmdln.gd", "-gexit"],
        capture_output=True, text=True, timeout=120
    )
    
    log_path = os.path.join(OUTPUT_DIR, "gut_output.txt")
    with open(log_path, "w") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\n=== STDERR ===\n")
            f.write(result.stderr)
    
    print(f"  Output saved to {log_path}")
    print(f"  Return code: {result.returncode}")
    return result.returncode == 0

def launch_game_and_screenshot():
    """启动Godot游戏，运行指定时长后截图"""
    print("[GAME] Launching game...")
    
    proc = subprocess.Popen(
        [GODOT, "--path", PROJECT],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    
    print("  Game running for 10 seconds...")
    time.sleep(10)
    
    # 截图（用Python原生方式）
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        ss_path = os.path.join(OUTPUT_DIR, f"screenshot_{int(time.time())}.png")
        screenshot.save(ss_path)
        print(f"  Screenshot saved: {ss_path}")
    except ImportError:
        print("  PIL not installed, skipping screenshot. pip install pillow")
    
    proc.terminate()
    proc.wait(timeout=10)
    print("  Game closed")

def run_e2e_tests():
    """运行pytest E2E测试"""
    print("[E2E] Running end-to-end tests...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         r"\MCP_3D\Testing\godot-e2e\tests", "-v", "--tb=short"],
        capture_output=True, text=True, timeout=120
    )
    
    log_path = os.path.join(OUTPUT_DIR, "e2e_output.txt")
    with open(log_path, "w") as f:
        f.write(result.stdout)
    
    print(f"  Output saved to {log_path}")
    return result.returncode == 0

def auto_game_world_test():
    """全自动游戏世界测试主流程"""
    print("=" * 50)
    print("  AUTO GAME WORLD TESTING SYSTEM")
    print("=" * 50)
    
    results = {}
    
    # 1. 单元测试
    print("\n--- Step 1: Unit Tests ---")
    results["unit"] = run_headless_test()
    
    # 2. 启动游戏+截图
    print("\n--- Step 2: Game Launch + Screenshot ---")
    try:
        launch_game_and_screenshot()
        results["game_launch"] = True
    except Exception as e:
        print(f"  Game launch failed: {e}")
        results["game_launch"] = False
    
    # 3. E2E测试
    print("\n--- Step 3: E2E Tests ---")
    try:
        results["e2e"] = run_e2e_tests()
    except Exception as e:
        print(f"  E2E failed: {e}")
        results["e2e"] = False
    
    # 汇总
    print("\n" + "=" * 50)
    print("  TEST RESULTS")
    print("=" * 50)
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        sym = "+" if passed else "-"
        print(f"  [{sym}] {name}: {status}")
    
    all_passed = all(results.values())
    print(f"\n  OVERALL: {'ALL PASSED!' if all_passed else 'SOME FAILED'}")
    return all_passed

if __name__ == "__main__":
    auto_game_world_test()
