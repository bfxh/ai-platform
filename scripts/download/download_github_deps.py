import urllib.request
import os
import ssl

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\mods"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {"User-Agent": "ParasiteModpack/1.0"}

downloads = {
    "Calio-1.14.0-alpha.2+mc.1.20.4.jar": "https://github.com/apace100/calio/releases/download/1.14.0-alpha.2%2Bmc.1.20.4/Calio-1.14.0-alpha.2%2Bmc.1.20.4.jar",
    "Apoli-2.12.0-alpha.6+mc.1.20.4.jar": "https://github.com/apace100/apoli/releases/download/2.12.0-alpha.6%2Bmc.1.20.4/Apoli-2.12.0-alpha.6%2Bmc.1.20.4.jar",
}

os.makedirs(MODS_DIR, exist_ok=True)

for name, url in downloads.items():
    path = os.path.join(MODS_DIR, name)
    if os.path.exists(path):
        print(f"[OK] 已存在: {name}")
        continue
    print(f"[下载] {name}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        size = os.path.getsize(path)
        print(f"[OK] 下载完成: {name} ({size} bytes)")
    except Exception as e:
        print(f"[错误] 下载失败: {e}")

print(f"\n模组目录: {MODS_DIR}")
print(f"模组数量: {len(os.listdir(MODS_DIR))}")
for f in sorted(os.listdir(MODS_DIR)):
    print(f"  - {f}")
