import os
import json
import urllib.request
import urllib.parse
import hashlib
import shutil

MINECRAFT_DIR = r"%GAME_DIR%\.minecraft"
LIB_DIR = os.path.join(MINECRAFT_DIR, "libraries")
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, "versions")

def download_file(url, path, expected_sha1=""):
    if os.path.exists(path):
        if expected_sha1:
            sha1 = hashlib.sha1(open(path, "rb").read()).hexdigest()
            if sha1 == expected_sha1:
                print(f"  Already exists: {os.path.basename(path)}")
                return True
        else:
            print(f"  Already exists: {os.path.basename(path)}")
            return True

    try:
        print(f"  Downloading: {os.path.basename(path)}")
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        if expected_sha1:
            sha1 = hashlib.sha1(data).hexdigest()
            if sha1 != expected_sha1:
                print(f"  SHA1 mismatch!")
                os.remove(path)
                return False
        print(f"  Downloaded: {len(data)//1024}KB")
        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False

def lib_name_to_path(name):
    parts = name.split(":")
    if len(parts) == 3:
        group, artifact, version = parts
        classifier = parts[2].split("@")[0] if "@" in parts[2] else ""
        ext = "jar"
        if classifier:
            version_with_class = f"{version}-{classifier}"
        else:
            version_with_class = version
        path = f"{group.replace('.', '/')}/{artifact}/{version_with_class}.{ext}"
    else:
        group, artifact = parts[0], parts[1]
        version = parts[2] if len(parts) > 2 else ""
        ext = "jar"
        path = f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}.{ext}"
    return path

def search_modrinth_version(slug, game_version, loader):
    params = urllib.parse.urlencode({
        "game_versions": json.dumps([game_version]),
        "loaders": json.dumps([loader])
    })
    url = f"https://api.modrinth.com/v2/project/{slug}/version?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ModpackBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        if data:
            version = data[0]
            for f in version.get("files", []):
                if f.get("primary", False):
                    return {
                        "filename": f["filename"],
                        "url": f["url"],
                        "sha1": f.get("hashes", {}).get("sha1", ""),
                    }
            if version.get("files"):
                f = version["files"][0]
                return {
                    "filename": f["filename"],
                    "url": f["url"],
                    "sha1": f.get("hashes", {}).get("sha1", ""),
                }
    except Exception as e:
        print(f"  Error: {e}")
    return None

def fix_mods_1204():
    print("\n=== Fixing 1.20.4 mods ===")
    version_dir = os.path.join(VERSIONS_DIR, "我即是虫群-1.20.4")
    mods_dir = os.path.join(version_dir, "mods")

    mods_to_fix = {
        "architectury-api": "neoforge",
        "rhino": "neoforge",
    }

    for slug, loader in mods_to_fix.items():
        print(f"\nSearching {slug} for 1.20.4...")
        result = search_modrinth_version(slug, "1.20.4", loader)
        if result:
            dest = os.path.join(mods_dir, result["filename"])
            if download_file(result["url"], dest, result["sha1"]):
                print(f"  Placed: {result['filename']}")
        else:
            print(f"  NOT FOUND on Modrinth")

def fix_mods_1201():
    print("\n=== Fixing 1.20.1 mods ===")
    version_dir = os.path.join(VERSIONS_DIR, "真菌起源")
    mods_dir = os.path.join(version_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    mods_to_download = {
        "architectury-api": "forge",
        "effective": "forge",
        "rhino": "forge",
    }

    for slug, loader in mods_to_download.items():
        print(f"\nSearching {slug} for 1.20.1...")
        result = search_modrinth_version(slug, "1.20.1", loader)
        if result:
            dest = os.path.join(mods_dir, result["filename"])
            if download_file(result["url"], dest, result["sha1"]):
                print(f"  Placed: {result['filename']}")
        else:
            print(f"  NOT FOUND on Modrinth")

def create_version_json_1201():
    print("\n=== Creating 1.20.1 Forge version json ===")
    version_name = "真菌起源"
    version_dir = os.path.join(VERSIONS_DIR, version_name)
    os.makedirs(version_dir, exist_ok=True)

    json_path = os.path.join(version_dir, f"{version_name}.json")

    version_json = {
        "id": version_name,
        "inheritsFrom": "1.20.1",
        "releaseTime": "2024-01-01T00:00:00+08:00",
        "time": "2024-01-01T00:00:00+08:00",
        "type": "release",
        "mainClass": "cpw.mods.bootstraplauncher.BootstrapLauncher",
        "arguments": {
            "game": [
                "--launchTarget",
                "forgeclient",
                "--fml.forgeVersion",
                "47.3.0",
                "--fml.mcVersion",
                "1.20.1",
                "--fml.forgeGroup",
                "net.minecraftforge"
            ],
            "jvm": [
                "-Djava.net.preferIPv6Addresses=system",
                "-DignoreList=bootstraplauncher,securejarhandler,asm-commons,asm-util,asm-analysis,asm-tree,asm,JarJarFileSystems,client-extra,fmlcore,javafmllanguage,lowcodelanguage,mclanguage,forge-,${version_name}.jar",
                "-DmergeModules=jna-5.10.0.jar,jna-platform-5.10.0.jar",
                "-DlibraryDirectory=${library_directory}",
                "-p",
                "${library_directory}/cpw/mods/bootstraplauncher/1.1.2/bootstraplauncher-1.1.2.jar${classpath_separator}${library_directory}/cpw/mods/securejarhandler/2.1.10/securejarhandler-2.1.10.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-commons/9.7/asm-commons-9.7.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-util/9.7/asm-util-9.7.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-analysis/9.7/asm-analysis-9.7.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-tree/9.7/asm-tree-9.7.jar${classpath_separator}${library_directory}/org/ow2/asm/asm/9.7/asm-9.7.jar${classpath_separator}${library_directory}/net/minecraftforge/JarJarFileSystems/0.3.19/JarJarFileSystems-0.3.19.jar",
                "--add-modules",
                "ALL-MODULE-PATH",
                "--add-opens",
                "java.base/java.util.jar=cw.mods.securejarhandler",
                "--add-opens",
                "java.base/java.lang.invoke=cw.mods.securejarhandler",
                "--add-exports",
                "java.base/sun.security.util=cw.mods.securejarhandler",
                "--add-exports",
                "jdk.naming.dns/com.sun.jndi.dns=java.naming"
            ]
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(version_json, f, indent=2)

    print(f"  Created: {json_path}")

def remove_fabric_mods_from_1204():
    print("\n=== Removing Fabric mods from 1.20.4 ===")
    version_dir = os.path.join(VERSIONS_DIR, "我即是虫群-1.20.4")
    mods_dir = os.path.join(version_dir, "mods")

    fabric_mods = []
    for f in os.listdir(mods_dir):
        if "fabric" in f.lower() or f.startswith("Contagion"):
            fabric_mods.append(f)

    for mod in fabric_mods:
        path = os.path.join(mods_dir, mod)
        try:
            os.remove(path)
            print(f"  Removed: {mod}")
        except Exception as e:
            print(f"  Error removing {mod}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("  修复虫群整合包")
    print("=" * 60)

    create_version_json_1201()
    fix_mods_1201()
    remove_fabric_mods_from_1204()
    fix_mods_1204()

    print("\n" + "=" * 60)
    print("  完成!")
    print("=" * 60)
