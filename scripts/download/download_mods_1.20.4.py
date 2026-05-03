import urllib.request
import urllib.parse
import json
import os
import ssl

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4-Fabric"
MODS_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME, "mods")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "ParasiteModpack/1.0 (contact@example.com)"
}

def download_file(url, path):
    if os.path.exists(path):
        print(f"  [OK] 已存在: {os.path.basename(path)}")
        return True
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        print(f"  [OK] 下载完成: {os.path.basename(path)}")
        return True
    except Exception as e:
        print(f"  [错误] 下载失败: {e}")
        return False

def get_mod_versions(slug):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps(["1.20.4"]),
        "loaders": json.dumps(["fabric"])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  [API错误] {slug}: {e}")
        return []

def download_mod(slug, display_name):
    print(f"[下载] {display_name} ({slug})...")
    versions = get_mod_versions(slug)
    if not versions:
        print(f"  [跳过] 无可用版本")
        return False
    
    for v in versions:
        for f in v.get("files", []):
            if f.get("primary", False):
                url = f["url"]
                filename = f["filename"]
                path = os.path.join(MODS_DIR, filename)
                return download_file(url, path)
    
    if versions and versions[0].get("files"):
        f = versions[0]["files"][0]
        url = f["url"]
        filename = f["filename"]
        path = os.path.join(MODS_DIR, filename)
        return download_file(url, path)
    
    return False

def main():
    os.makedirs(MODS_DIR, exist_ok=True)
    
    print("=" * 60)
    print("  下载核心模组 - Fabric 1.20.4")
    print("=" * 60)
    
    mods = [
        ("fabric-api", "Fabric API"),
        ("origins", "Origins"),
        ("apoli", "Apoli"),
        ("calio", "Calio"),
        ("pehkui", "Pehkui"),
        ("modmenu", "Mod Menu"),
        ("cloth-config", "Cloth Config"),
        ("sodium", "Sodium"),
        ("lithium", "Lithium"),
        ("iris", "Iris Shaders"),
        ("indium", "Indium"),
        ("roughly-enough-items", "Roughly Enough Items"),
        ("architectury", "Architectury"),
        ("no-chat-reports", "No Chat Reports"),
        ("ferrite-core", "FerriteCore"),
        ("memoryleakfix", "Memory Leak Fix"),
        ("entityculling", "Entity Culling"),
        ("language-reload", "Language Reload"),
        ("debugify", "Debugify"),
        ("continuity", "Continuity"),
        ("fabric-language-kotlin", "Fabric Language Kotlin"),
    ]
    
    success = 0
    failed = []
    
    for slug, name in mods:
        if download_mod(slug, name):
            success += 1
        else:
            failed.append(name)
    
    print(f"\n[统计] 成功: {success}, 失败: {len(failed)}")
    if failed:
        print(f"[失败列表] {', '.join(failed)}")
    
    print(f"\n模组目录: {MODS_DIR}")
    print(f"模组数量: {len(os.listdir(MODS_DIR))}")

if __name__ == "__main__":
    main()
