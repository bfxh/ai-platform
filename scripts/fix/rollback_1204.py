import json
import os
import shutil
import requests
import time
import zipfile
import hashlib

MODRINTH_API = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "MCModUpdater/2.0", "Accept": "application/json"}
BACKUP_DIR = r"\python\mod_backups"
MODS_DIR = r"%GAME_DIR%\.minecraft\versions\新起源\mods"
RESULT_FILE = r"\python\mod_results\mod_update_1.20.4.json"

def download_file(url, dest_path):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        if resp.status_code == 200:
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def validate_jar(path):
    if not os.path.exists(path):
        return False
    if os.path.getsize(path) < 1024:
        return False
    try:
        with zipfile.ZipFile(path, 'r') as z:
            return len(z.namelist()) > 0
    except:
        return False

def get_latest_forge_version(project_id, game_version="1.20.1"):
    try:
        resp = requests.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params={"loaders": json.dumps(["forge"]), "game_versions": json.dumps([game_version])},
            headers=HEADERS,
            timeout=15
        )
        if resp.status_code == 200:
            versions = resp.json()
            for v in versions:
                for f in v.get("files", []):
                    if f.get("primary", False) or f.get("filename", "").endswith(".jar"):
                        return {
                            "version_number": v.get("version_number", ""),
                            "filename": f["filename"],
                            "url": f["url"],
                            "sha1": f.get("hashes", {}).get("sha1", ""),
                        }
        return None
    except:
        return None

with open(RESULT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

exact = [r for r in data['results'] if r.get('status') == 'update_available']

print("Step 1: Rollback incompatible 1.20.4 NeoForge mods...")
rolled_back = 0
for r in exact:
    latest = r.get('latest', {})
    new_fn = latest.get('filename', '')
    new_path = os.path.join(MODS_DIR, new_fn)

    if not os.path.exists(new_path):
        continue

    if 'neoforge' in new_fn.lower() or '1.20.4' in new_fn:
        if not validate_jar(new_path):
            print(f"  Removing corrupt: {new_fn}")
            os.remove(new_path)
            continue

        backup_path = os.path.join(BACKUP_DIR, f"1.20.4_{r['file']}")
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, os.path.join(MODS_DIR, r['file']))
            print(f"  Restored: {r['file']}")
            os.remove(new_path)
            rolled_back += 1
        else:
            print(f"  No backup for: {r['file']} (keeping new version)")

print(f"\nRolled back {rolled_back} mods")

print("\nStep 2: Find correct 1.20.1 Forge versions...")
correct_updates = []
for r in exact:
    project_id = r.get('latest', {}).get('project_id', '')
    if not project_id:
        slug = r.get('slug', '')
        if slug:
            try:
                resp = requests.get(f"{MODRINTH_API}/project/{slug}", headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    project_id = resp.json()['id']
            except:
                pass
    if not project_id:
        continue

    forge_ver = get_latest_forge_version(project_id, "1.20.1")
    if forge_ver:
        fn = forge_ver['filename']
        if 'neoforge' not in fn.lower() and '1.20.4' not in fn:
            correct_updates.append({
                'title': r.get('title', '?'),
                'old_file': r['file'],
                'forge_version': forge_ver,
                'project_id': project_id,
            })
            print(f"  {r.get('title', '?')}: {forge_ver['filename']} ({forge_ver['version_number']})")
    time.sleep(0.3)

print(f"\nStep 3: Download correct 1.20.1 Forge versions...")
downloaded = 0
for upd in correct_updates:
    old_fn = upd['old_file']
    new_fn = upd['forge_version']['filename']
    new_path = os.path.join(MODS_DIR, new_fn)
    old_path = os.path.join(MODS_DIR, old_fn)

    if os.path.exists(new_path):
        print(f"  Already exists: {new_fn}")
        continue

    print(f"  Downloading: {new_fn}...", end=" ", flush=True)
    if download_file(upd['forge_version']['url'], new_path):
        if validate_jar(new_path):
            print("OK")
            downloaded += 1
            if os.path.exists(old_path) and old_fn != new_fn:
                backup_path = os.path.join(BACKUP_DIR, f"1.20.1_{old_fn}")
                if not os.path.exists(backup_path):
                    shutil.move(old_path, backup_path)
        else:
            print("CORRUPT")
            os.remove(new_path)
    else:
        print("FAIL")
    time.sleep(0.3)

print(f"\nDone: rolled back {rolled_back}, downloaded {downloaded} correct 1.20.1 Forge versions")
