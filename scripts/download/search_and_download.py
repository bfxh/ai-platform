import urllib.request
import json
import time
import urllib.parse

MODS_DIR = r"%GAME_DIR%\.minecraft\versions\我即是虫群-1.20.4\mods"

def search_mods(query, limit=10):
    facets = json.dumps([["project_type:mod"], ["versions:1.20.4"], ["categories:fabric"]])
    params = urllib.parse.urlencode({"query": query, "facets": facets, "limit": limit})
    url = f"https://api.modrinth.com/v2/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data.get("hits", [])
    except Exception as e:
        print(f"  Search error for '{query}': {e}")
        return []

def get_mod_versions(slug):
    url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[\"1.20.4\"]&loaders=[\"fabric\"]"
    req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data
    except:
        return None

def download_mod(slug, name):
    versions = get_mod_versions(slug)
    if not versions:
        return False
    for v in versions:
        for f in v.get("files", []):
            filename = f.get("filename", "")
            url = f.get("url", "")
            if url and filename.endswith(".jar"):
                filepath = os.path.join(MODS_DIR, filename)
                if os.path.exists(filepath):
                    print(f"  [SKIP] {filename}")
                    return True
                try:
                    print(f"  [DOWN] {filename}...")
                    urllib.request.urlretrieve(url, filepath)
                    print(f"  [OK] {filename}")
                    return True
                except Exception as e:
                    print(f"  [ERR] {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
    return False

import os

existing = set()
if os.path.exists(MODS_DIR):
    for f in os.listdir(MODS_DIR):
        if f.endswith(".jar"):
            existing.add(f.lower())

print("=" * 60)
print("  Fabric 1.20.4 Mod Search & Download")
print(f"  Current mods: {len(existing)}")
print("=" * 60)

search_queries = [
    ("parasite", "Parasite/Infection"),
    ("fungal", "Fungal/Mushroom"),
    ("spore", "Spore/Infection"),
    ("infection", "Infection/Disease"),
    ("origin", "Origins"),
    ("swarm", "Swarm/Insect"),
    ("magic", "Magic/Spell"),
    ("weapon", "Weapons/Combat"),
    ("dungeon", "Dungeon/Adventure"),
    ("boss", "Boss/Mob"),
    ("food", "Food/Farming"),
    ("storage", "Storage/Backpack"),
    ("curios", "Curios/Accessory"),
    ("kubejs", "KubeJS/Scripting"),
    ("twilight", "Twilight Forest"),
    ("aether", "Aether/Sky"),
    ("vampirism", "Vampirism"),
    ("mowzie", "Mowzie Mobs"),
    ("botania", "Botania/Plant"),
    ("adventure", "Adventure/RPG"),
    ("armor", "Armor/Equipment"),
    ("biome", "Biome/World"),
    ("dimension", "Dimension/Portal"),
    ("dragon", "Dragon/Boss"),
    ("enchant", "Enchant/Magic"),
    ("mob", "Mobs/Creatures"),
    ("nether", "Nether/Hell"),
    ("end", "End/Void"),
    ("tech", "Technology/Machine"),
    ("trinket", "Trinket/Accessory"),
]

all_found = {}
for query, category in search_queries:
    print(f"\n--- {category} ({query}) ---")
    results = search_mods(query, 8)
    for r in results:
        slug = r.get("slug", "")
        title = r.get("title", "")
        downloads = r.get("downloads", 0)
        if slug not in all_found:
            all_found[slug] = {"title": title, "downloads": downloads, "category": category}
            print(f"  {slug} | {title} | {downloads:,}")
    time.sleep(0.3)

print("\n" + "=" * 60)
print(f"  Total unique mods found: {len(all_found)}")
print("=" * 60)

priority_slugs = [
    "kubejs", "vampirism", "the-twilight-forest", "botania", "aether",
    "mowzies-mobs", "bosses-of-mass-destruction", "curios",
    "sophisticated-backpacks", "sophisticated-core", "sophisticated-storage",
    "farmers-delight", "croptopia", "spartan-weaponry", "simply-swords",
    "extra-origins", "mob-origins", "origins-classes",
    "the-bumblezone", "the-graveyard", "when-dungeons-arise",
    "deeper-and-darker", "blue-skies", "undergarden",
    "scaling-health", "3d-skin-layers", "damage-number",
    "creeper-overhaul", "spiders-2", "naturalist",
    "quark", "brewin-and-chewin", "spice-of-life-carrot-edition",
    "ecologics", "promenade", "wilder-wild", "regions-unexplored",
    "cosmetic-armor-reworked", "shoulder-surfing-reloaded",
    "iron-spellbooks", "ars-nouveau", "hexerei", "spectrum",
    "blood-magic", "cataclysm", "apotheosis",
]

print("\n--- Downloading Priority Mods ---")
added = 0
failed_list = []
for slug in priority_slugs:
    name = all_found.get(slug, {}).get("title", slug)
    slug_lower = slug.lower().replace("-", "").replace("_", "")
    skip = False
    for jar in existing:
        if slug_lower in jar.lower().replace("-", "").replace("_", "").replace(" ", ""):
            skip = True
            break
    if skip:
        print(f"  [SKIP] {name} - already exists")
        continue
    print(f"\n  Trying: {slug} ({name})")
    success = download_mod(slug, name)
    if success:
        added += 1
    else:
        failed_list.append(slug)
    time.sleep(0.5)

print("\n--- Downloading Additional Found Mods ---")
for slug, info in sorted(all_found.items(), key=lambda x: -x[1]["downloads"]):
    if slug in priority_slugs or slug in failed_list:
        continue
    slug_lower = slug.lower().replace("-", "").replace("_", "")
    skip = False
    for jar in existing:
        if slug_lower in jar.lower().replace("-", "").replace("_", "").replace(" ", ""):
            skip = True
            break
    if skip:
        continue
    if info["downloads"] < 5000:
        continue
    print(f"\n  Trying: {slug} ({info['title']})")
    success = download_mod(slug, info["title"])
    if success:
        added += 1
    time.sleep(0.5)

final_count = len([f for f in os.listdir(MODS_DIR) if f.endswith(".jar")])
print(f"\n{'=' * 60}")
print(f"  Added: {added}")
print(f"  Failed: {len(failed_list)} - {failed_list}")
print(f"  Total mods now: {final_count}")
print(f"{'=' * 60}")
