import subprocess
import os
import time
import json
import sys

minecraft_dir = r"%GAME_DIR%\.minecraft"
versions = [
    {"name": "我即是虫群v2.0", "java_version": "1.8", "launch_script": "launch_mc.py"},
    {"name": "新起源", "java_version": "17+", "launch_script": "launch_1201.py"},
]

def check_scripts_loaded(version_name, timeout=120):
    version_dir = os.path.join(minecraft_dir, "versions", version_name)
    ct_log = os.path.join(version_dir, "crafttweaker.log")
    latest_log = os.path.join(version_dir, "logs", "latest.log")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if version_name == "新起源":
            if os.path.exists(latest_log):
                try:
                    with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if "KubeJS Server/" in content or "Server resource reload complete" in content:
                        if "startup script errors" in content.lower():
                            errors = [line for line in content.split('\n') if 'error' in line.lower() and 'kubejs' in line.lower()]
                            return True, f"KubeJS loaded with {len(errors)} errors"
                        return True, "KubeJS loaded successfully"
                except:
                    pass
        else:
            if os.path.exists(ct_log):
                try:
                    with open(ct_log, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if "parasite_recipes" in content.lower() or "parasite_events" in content.lower():
                        return True, "CraftTweaker loaded parasite scripts"
                    if "Completed script loading" in content:
                        loaded_scripts = [line for line in content.split('\n') if 'Loading Script' in line]
                        return True, f"CraftTweaker loaded {len(loaded_scripts)} scripts (check for parasite scripts)"
                except:
                    pass
            if os.path.exists(latest_log):
                try:
                    with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    if "Stopping!" in content or "net.minecraft.client.Minecraft" in content:
                        return True, "Game loaded and closed"
                except:
                    pass
        time.sleep(5)

    return False, "Timeout waiting for game to load"

def launch_game(launch_script):
    script_path = os.path.join(r"\python", launch_script)
    if not os.path.exists(script_path):
        return False, f"Launch script not found: {script_path}"

    process = subprocess.Popen(
        ["py", script_path],
        cwd=r"\python",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return True, f"Launched with PID {process.pid}"

if __name__ == "__main__":
    version_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    if version_idx >= len(versions):
        print(f"Invalid version index. Available: 0-{len(versions)-1}")
        sys.exit(1)

    version = versions[version_idx]
    print(f"=== Verifying {version['name']} ===")

    success, msg = launch_game(version["launch_script"])
    print(f"Launch: {msg}")

    if success:
        print("Waiting for game to load scripts...")
        loaded, result = check_scripts_loaded(version["name"])
        print(f"Result: {result}")

        if not loaded:
            print("WARNING: Scripts may not have loaded correctly")
    else:
        print(f"Failed to launch: {msg}")
