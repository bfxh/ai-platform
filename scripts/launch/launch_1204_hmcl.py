import subprocess
import os
import time

hmcl_path = r"%GAME_DIR%\HMCL-3.12.4.exe"
version_name = "我即是虫群-1.20.4"
game_dir = r"%GAME_DIR%\.minecraft"

print(f"Launching {version_name} via HMCL...")
process = subprocess.Popen([hmcl_path, "--width", "854", "--height", "480", "--launch", version_name], cwd=game_dir)
print(f"PID: {process.pid}")

time.sleep(5)
print("Game launched via HMCL!")

time.sleep(30)
if process.poll() is not None:
    print(f"HMCL exited with code {process.returncode}")
else:
    print("Game is running!")
