"""测试 blender_run 是否正常返回输出"""
import sys
sys.path.insert(0, "/python/MCP")

# 直接复制 blender_run 逻辑
import subprocess
from pathlib import Path

BLENDER = Path("%SOFTWARE_DIR%/KF/JM/blender/blender.exe")
script = Path("/python/MCP/scripts/test_print.py")
script.write_text("print('HELLO_FROM_BLENDER'); print('ADDONS_TEST_SUCCESS')\n", encoding="utf-8")

cmd = [str(BLENDER), "--background", "--python", str(script)]
print("CMD:", cmd)

try:
    result = subprocess.run(cmd, capture_output=True, timeout=60,
                            encoding="utf-8", errors="replace")
except Exception as e:
    print(f"SUBPROCESS ERROR: {e}")
    sys.exit(1)

print(f"returncode: {result.returncode}")
print(f"stdout length: {len(result.stdout) if result.stdout else 0}")
print(f"stderr length: {len(result.stderr) if result.stderr else 0}")
print("STDOUT:", result.stdout[:500] if result.stdout else "None")
print("STDERR:", result.stderr[:500] if result.stderr else "None")
