import urllib.request
import urllib.parse
import json
import os
import ssl

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4-Fabric\mods"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "ParasiteModpack/1.0 (contact@example.com)"
}

def search_modrinth(query):
    params = urllib.parse.urlencode({
        "query": query,
        "facets": json.dumps([["project_type:mod"], ["versions:1.20.4"], ["categories:fabric"]]),
        "limit": 5
    })
    url = f"https://api.modrinth.com/v2/search?{params}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        return data.get("hits", [])
    except Exception as e:
        print(f"  [搜索错误] {e}")
        return []

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
                return download_file(f["url"], os.path.join(MODS_DIR, f["filename"]))
    
    if versions and versions[0].get("files"):
        f = versions[0]["files"][0]
        return download_file(f["url"], os.path.join(MODS_DIR, f["filename"]))
    
    return False

def main():
    os.makedirs(MODS_DIR, exist_ok=True)
    
    print("=" * 60)
    print("  搜索并下载缺失模组")
    print("=" * 60)
    
    search_terms = ["apoli", "calio", "architectury", "roughly enough items"]
    
    for term in search_terms:
        print(f"\n[搜索] '{term}'...")
        results = search_modrinth(term)
        for r in results[:3]:
            slug = r.get("slug", "?")
            title = r.get("title", "?")
            print(f"  - {title} (slug: {slug})")
    
    print("\n" + "=" * 60)
    print("  尝试使用搜索到的slug下载")
    print("=" * 60)
    
    alt_slugs = {
        "apoli": ["apoli", "apoli-fabric", "apoli-api"],
        "calio": ["calio", "calio-fabric", "calio-api"],
        "architectury": ["architectury-api", "architectury-fabric", "architectury"],
        "rei": ["rei", "roughly-enough-items", "roughly-enough-items-fabric"]
    }
    
    for mod_name, slugs in alt_slugs.items():
        found = False
        for slug in slugs:
            versions = get_mod_versions(slug)
            if versions:
                print(f"[找到] {mod_name} -> slug: {slug}")
                for v in versions:
                    for f in v.get("files", []):
                        if f.get("primary", False):
                            download_file(f["url"], os.path.join(MODS_DIR, f["filename"]))
                            found = True
                            break
                    if found:
                        break
                break
        if not found:
            print(f"[失败] {mod_name}: 所有slug均无结果")
    
    print(f"\n模组数量: {len(os.listdir(MODS_DIR))}")
    for f in sorted(os.listdir(MODS_DIR)):
        print(f"  - {f}")

if __name__ == "__main__":
    main()
