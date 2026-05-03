import urllib.request
import os
import ssl
import time

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\mods"
APOLI_URL = "https://github.com/apace100/apoli/releases/download/2.12.0-alpha.6%2Bmc.1.20.4/Apoli-2.12.0-alpha.6%2Bmc.1.20.4.jar"
APOLI_PATH = os.path.join(MODS_DIR, "Apoli-2.12.0-alpha.6+mc.1.20.4.jar")

if os.path.exists(APOLI_PATH) and os.path.getsize(APOLI_PATH) > 1000000:
    print(f"[OK] Apoli已存在且大小正常: {os.path.getsize(APOLI_PATH)} bytes")
else:
    if os.path.exists(APOLI_PATH):
        os.remove(APOLI_PATH)
    
    for attempt in range(3):
        print(f"[尝试 {attempt+1}/3] 下载Apoli...")
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(APOLI_URL, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/octet-stream",
            })
            
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                data = resp.read()
                with open(APOLI_PATH, "wb") as f:
                    f.write(data)
            
            size = os.path.getsize(APOLI_PATH)
            if size > 1000000:
                print(f"[OK] 下载成功: {size} bytes")
                break
            else:
                print(f"[警告] 文件太小: {size} bytes，可能下载不完整")
                os.remove(APOLI_PATH)
        except Exception as e:
            print(f"[错误] 尝试 {attempt+1} 失败: {e}")
            if os.path.exists(APOLI_PATH):
                os.remove(APOLI_PATH)
        time.sleep(2)

print(f"\n模组列表:")
for f in sorted(os.listdir(MODS_DIR)):
    size = os.path.getsize(os.path.join(MODS_DIR, f))
    print(f"  {f} ({size//1024}KB)")
