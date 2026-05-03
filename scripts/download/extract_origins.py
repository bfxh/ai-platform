import zipfile
import json
import os

MODS = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"
OUT = r"\python\origins_data.json"

JARS = [
    "origins-plus-plus-2.4.jar",
    "TooManyOrigins-1.2.0+1.20.4-fabric.jar",
    "Origins-1.13.0-alpha.4+mc.1.20.4.jar",
    "RPG Origins 1.4.4.jar",
    "origins-player-scale-3.jar",
    "originstweaks-1.18.3.jar",
    "volcanic-dragon-origin-2.0.1.jar",
]

all_origins = []
all_powers = {}

for jn in JARS:
    jp = os.path.join(MODS, jn)
    if not os.path.exists(jp):
        print(f"[SKIP] {jn}")
        continue
    print(f"Scanning: {jn}")
    with zipfile.ZipFile(jp, "r") as zf:
        names = zf.namelist()
        for n in names:
            p = n.split("/")
            if len(p) >= 4 and p[0] == "data" and p[2] == "origins" and n.endswith(".json"):
                ns = p[1]
                oid = ns + ":" + "/".join(p[3:]).replace(".json", "")
                try:
                    d = json.load(zf.open(n))
                    if d.get("unchoosable", False):
                        continue
                    all_origins.append({
                        "origin_id": oid,
                        "source_jar": jn,
                        "name": d.get("name", "N/A"),
                        "description": d.get("description", "N/A")[:200] if d.get("description") else "N/A",
                        "icon": d.get("icon", "N/A"),
                        "impact": d.get("impact", "N/A"),
                        "powers": d.get("powers", []),
                        "order": d.get("order", None),
                    })
                except Exception as e:
                    pass

        for n in names:
            p = n.split("/")
            if len(p) >= 4 and p[0] == "data" and p[2] == "powers" and n.endswith(".json"):
                ns = p[1]
                pid = ns + ":" + "/".join(p[3:]).replace(".json", "")
                try:
                    d = json.load(zf.open(n))
                    all_powers[pid] = {
                        "type": d.get("type", "N/A"),
                        "source_jar": jn,
                    }
                except:
                    pass

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"origins": all_origins, "power_count": len(all_powers)}, f, ensure_ascii=False, indent=2)

print(f"\nTotal choosable origins: {len(all_origins)}")
print(f"Total powers found: {len(all_powers)}")
print(f"\n--- All Origins ---")
for o in sorted(all_origins, key=lambda x: (x["source_jar"], x.get("order") or 999)):
    print(f"  [{o['source_jar'][:20]}] {o['origin_id']}")
    print(f"    Name: {o['name']}")
    print(f"    Icon: {o['icon']} | Impact: {o['impact']}")
    print(f"    Powers: {len(o['powers'])}")
    print()
