import requests, json
HEADERS = {"User-Agent": "MCModUpdater/2.0", "Accept": "application/json"}

for slug in ["embeddiumplus", "chloride"]:
    print(f"\n=== {slug} ===")
    resp = requests.get(
        f"https://api.modrinth.com/v2/project/{slug}/version",
        params={"loaders": json.dumps(["forge"]), "game_versions": json.dumps(["1.20.1"])},
        headers=HEADERS, timeout=15
    )
    if resp.status_code == 200:
        versions = resp.json()
        for v in versions[:5]:
            deps = v.get("dependencies", [])
            forge_req = [d for d in deps if d.get("slug") == "forge" or d.get("mod_id") == "forge"]
            forge_ver = forge_req[0].get("version", "?") if forge_req else "none"
            for f in v.get("files", []):
                if f.get("primary"):
                    print(f"  {v['version_number']}: {f['filename']} (forge req: {forge_ver})")
    else:
        print(f"  Not found: {resp.status_code}")
