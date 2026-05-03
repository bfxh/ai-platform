import os
import sys
import json
import time
import zipfile
import hashlib
import requests
from pathlib import Path

MODRINTH_API = "https://api.modrinth.com/v2"

HEADERS = {
    "User-Agent": "MCModUpdater/2.0 (modpack-manager)",
    "Accept": "application/json"
}

MODPACKS = {
    "1.12.2": {
        "name": "我即是虫群v2.0",
        "path": r"%GAME_DIR%\.minecraft\versions\我即是虫群v2.0\mods",
        "loader": "forge",
        "game_version": "1.12.2",
    },
    "1.20.4": {
        "name": "新起源",
        "path": r"%GAME_DIR%\.minecraft\versions\新起源\mods",
        "loader": "forge",
        "game_version": "1.20.4",
    }
}

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mod_backups")
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mod_results")


def sha1_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def get_mod_info_from_jar(jar_path):
    info = {"file": os.path.basename(jar_path), "mod_id": None, "version": None, "name": None}
    try:
        with zipfile.ZipFile(jar_path, 'r') as z:
            names = z.namelist()

            fmj = [n for n in names if n == 'fabric.mod.json']
            if fmj:
                with z.open(fmj[0]) as f:
                    data = json.load(f)
                    info['mod_id'] = data.get('id', None)
                    info['name'] = data.get('name', None)
                    info['version'] = data.get('version', None)

            mods_toml = [n for n in names if n.endswith('mods.toml') and 'META-INF' not in n]
            if mods_toml and not info['mod_id']:
                with z.open(mods_toml[0]) as f:
                    content = f.read().decode('utf-8', errors='replace')
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('modId='):
                            info['mod_id'] = line.split('=', 1)[1].strip('" ')
                        elif line.startswith('version='):
                            v = line.split('=', 1)[1].strip('" ')
                            if v != '${file.jarVersion}':
                                info['version'] = v
                        elif line.startswith('displayName='):
                            info['name'] = line.split('=', 1)[1].strip('" ')

            mcmod = [n for n in names if n.endswith('mcmod.info')]
            if mcmod and not info['mod_id']:
                with z.open(mcmod[0]) as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, list) and data:
                            d = data[0]
                        elif isinstance(data, dict) and 'modList' in data:
                            d = data['modList'][0] if data['modList'] else {}
                        elif isinstance(data, dict):
                            d = data
                        else:
                            d = {}
                        info['mod_id'] = d.get('modid', None)
                        info['name'] = d.get('name', None)
                        info['version'] = d.get('version', None)
                    except Exception:
                        pass

            if not info['mod_id']:
                fn = os.path.basename(jar_path)
                import re
                m = re.match(r'\[.*?\]\s*', fn)
                if m:
                    fn = fn[m.end():]
                m = re.match(r'([a-zA-Z0-9_\-]+)', fn)
                if m:
                    info['mod_id'] = m.group(1).lower()
                    info['name'] = info['mod_id']
    except Exception:
        pass
    return info


def lookup_by_hash(sha1_hash):
    try:
        resp = requests.get(
            f"{MODRINTH_API}/version_file/{sha1_hash}",
            params={"algorithm": "sha1"},
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "project_id": data.get("project_id", ""),
                "version_id": data.get("id", ""),
                "version_number": data.get("version_number", ""),
                "filename": data.get("filename", ""),
                "date": data.get("date_published", ""),
            }
    except Exception:
        pass
    return None


def get_project_info(project_id):
    try:
        resp = requests.get(
            f"{MODRINTH_API}/project/{project_id}",
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "slug": data.get("slug", ""),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "source_url": data.get("source_url", ""),
            }
    except Exception:
        pass
    return None


def get_latest_version(project_id, game_version, loader="forge"):
    loaders = [loader]
    if loader == "forge":
        loaders.append("neoforge")

    try:
        resp = requests.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params={"loaders": json.dumps(loaders), "game_versions": json.dumps([game_version])},
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            versions = resp.json()
            for v in versions:
                vnum = v.get("version_number", "")
                for f in v.get("files", []):
                    if f.get("primary", False):
                        return {
                            "version_number": vnum,
                            "version_id": v.get("id", ""),
                            "filename": f["filename"],
                            "url": f["url"],
                            "sha1": f.get("hashes", {}).get("sha1", ""),
                            "size": f.get("size", 0),
                            "date": v.get("date_published", ""),
                        }
            if versions:
                v = versions[0]
                for f in v.get("files", []):
                    if f.get("filename", "").endswith(".jar"):
                        return {
                            "version_number": v.get("version_number", ""),
                            "version_id": v.get("id", ""),
                            "filename": f["filename"],
                            "url": f["url"],
                            "sha1": f.get("hashes", {}).get("sha1", ""),
                            "size": f.get("size", 0),
                            "date": v.get("date_published", ""),
                        }
        return None
    except Exception:
        return None


def search_modrinth_by_name(query, game_version, loader="forge"):
    try:
        facets = json.dumps([["project_type:mod"], [f"versions:{game_version}"], [f"categories:{loader}"]])
        resp = requests.get(
            f"{MODRINTH_API}/search",
            params={"query": query, "limit": 3, "facets": facets},
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            if hits:
                return hits[0]["project_id"], hits[0].get("slug", "")
    except Exception:
        pass
    return None, None


def download_file(url, dest_path):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        if resp.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception:
        pass
    return False


def scan_mods(version_key):
    config = MODPACKS[version_key]
    mods_dir = config["path"]
    if not os.path.exists(mods_dir):
        print(f"  ⚠ 模组目录不存在: {mods_dir}")
        return []

    mods = []
    for f in sorted(os.listdir(mods_dir)):
        if f.endswith(".jar"):
            jar_path = os.path.join(mods_dir, f)
            info = get_mod_info_from_jar(jar_path)
            info["jar_path"] = jar_path
            info["jar_size"] = os.path.getsize(jar_path)
            info["sha1"] = sha1_file(jar_path)
            mods.append(info)
    return mods


def check_updates(version_key, mods):
    config = MODPACKS[version_key]
    game_version = config["game_version"]
    loader = config["loader"]

    results = []
    total = len(mods)

    for i, mod in enumerate(mods):
        mod_id = mod.get("mod_id") or ""
        mod_name = mod.get("name") or mod["file"]
        sha1 = mod.get("sha1", "")

        print(f"  [{i+1}/{total}] {mod_name[:40]}...", end=" ", flush=True)

        if mod_id in ("minecraft", "forge", "fml", "mcp", "optifine", "neoforge"):
            print("核心跳过")
            results.append({**mod, "status": "skipped_core"})
            continue

        hash_info = lookup_by_hash(sha1) if sha1 else None
        if hash_info:
            project_id = hash_info["project_id"]
            current_version = hash_info["version_number"]
            proj_info = get_project_info(project_id)
            slug = proj_info["slug"] if proj_info else ""
            title = proj_info["title"] if proj_info else ""

            latest = get_latest_version(project_id, game_version, loader)
            if latest:
                if latest["sha1"] == sha1:
                    print(f"✅ {title} 已是最新 ({current_version})")
                    results.append({**mod, "status": "up_to_date", "slug": slug, "title": title,
                                    "current_version": current_version, "latest_version": latest["version_number"]})
                else:
                    print(f"⬆ {title}: {current_version} -> {latest['version_number']}")
                    results.append({**mod, "status": "update_available", "slug": slug, "title": title,
                                    "current_version": current_version, "latest": latest})
            else:
                print(f"⚠ {title}: 当前 {current_version}, 无 {game_version} 版本")
                results.append({**mod, "status": "no_target_version", "slug": slug, "title": title,
                                "current_version": current_version})
            time.sleep(0.3)
            continue

        print(f"❌ SHA1未命中")
        results.append({**mod, "status": "not_found"})

        time.sleep(0.3)

    return results


def apply_updates(version_key, results, dry_run=True):
    config = MODPACKS[version_key]
    mods_dir = config["path"]
    os.makedirs(BACKUP_DIR, exist_ok=True)

    updated = 0
    for r in results:
        if r.get("status") not in ("update_available", "update_fuzzy"):
            continue

        latest = r["latest"]
        old_path = r["jar_path"]
        new_filename = latest["filename"]
        new_path = os.path.join(mods_dir, new_filename)

        if os.path.exists(new_path):
            print(f"  ⏭ {new_filename} 已存在")
            continue

        if dry_run:
            print(f"  📋 {r['file']} -> {new_filename}")
            continue

        backup_path = os.path.join(BACKUP_DIR, f"{version_key}_{r['file']}")
        if not os.path.exists(backup_path) and os.path.exists(old_path):
            os.rename(old_path, backup_path)
            print(f"  📦 备份: {r['file']}")

        print(f"  ⬇ 下载: {new_filename}...", end=" ", flush=True)
        if download_file(latest["url"], new_path):
            print("✅")
            updated += 1
        else:
            print("❌")
            if os.path.exists(backup_path) and not os.path.exists(old_path):
                os.rename(backup_path, old_path)

        time.sleep(0.5)

    return updated


def main():
    print("=" * 70)
    print("Minecraft 模组更新器 v2 (SHA1精确匹配)")
    print("=" * 70)

    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    os.makedirs(RESULTS_DIR, exist_ok=True)

    for version_key in ["1.12.2", "1.20.4"]:
        config = MODPACKS[version_key]
        print(f"\n{'='*60}")
        print(f"整合包: {config['name']} (MC {version_key}, {config['loader']})")
        print(f"{'='*60}")

        print(f"\n[1/3] 扫描模组...")
        mods = scan_mods(version_key)
        print(f"  发现 {len(mods)} 个模组")

        print(f"\n[2/3] 检查更新 (SHA1精确匹配优先)...")
        results = check_updates(version_key, mods)

        up_to_date = len([r for r in results if r.get("status") == "up_to_date"])
        available = len([r for r in results if r.get("status") == "update_available"])
        fuzzy = len([r for r in results if r.get("status") == "update_fuzzy"])
        not_found = len([r for r in results if r.get("status") == "not_found"])
        no_version = len([r for r in results if r.get("status") == "no_target_version"])
        skipped = len([r for r in results if r.get("status") == "skipped_core"])

        print(f"\n  📊 统计:")
        print(f"     已是最新: {up_to_date}")
        print(f"     可更新(精确): {available}")
        print(f"     可更新(模糊): {fuzzy}")
        print(f"     无目标版本: {no_version}")
        print(f"     未找到: {not_found}")
        print(f"     核心跳过: {skipped}")

        if mode == "update" and (available or fuzzy):
            print(f"\n[3/3] 应用更新...")
            updated = apply_updates(version_key, results, dry_run=False)
            print(f"  ✅ 已更新 {updated} 个模组")
        elif available or fuzzy:
            print(f"\n[3/3] 预览更新 (使用 'update' 参数执行)...")
            apply_updates(version_key, results, dry_run=True)

        cache = {
            "version_key": version_key,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": [{k: v for k, v in r.items() if k != 'jar_path'} for r in results]
        }
        result_file = os.path.join(RESULTS_DIR, f"mod_update_{version_key}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"\n  结果已保存: {result_file}")


if __name__ == "__main__":
    main()
