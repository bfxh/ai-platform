import os
import json
import shutil

MC_DIR = r"%GAME_DIR%\.minecraft"
VERSION_NAME = "我即是虫群-1.20.4"
VERSION_DIR = os.path.join(MC_DIR, "versions", VERSION_NAME)
VERSION_JSON = os.path.join(VERSION_DIR, f"{VERSION_NAME}.json")

shutil.copy2(VERSION_JSON, VERSION_JSON + ".neoforge_backup")
print(f"备份: {VERSION_JSON}.neoforge_backup")

with open(VERSION_JSON, "r", encoding="utf-8") as f:
    old_data = json.load(f)

FABRIC_JSON = {
    "id": VERSION_NAME,
    "inheritsFrom": "1.20.4",
    "releaseTime": old_data.get("releaseTime", "2024-06-08T10:44:23"),
    "time": old_data.get("time", "2024-06-08T10:44:23"),
    "type": "release",
    "mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient",
    "arguments": {
        "game": [],
        "jvm": [
            "-Djava.net.preferIPv6Addresses=system"
        ]
    },
    "libraries": [
        {
            "name": "net.fabricmc:fabric-loader:0.16.14",
            "downloads": {
                "artifact": {
                    "url": "https://maven.fabricmc.net/net/fabricmc/fabric-loader/0.16.14/fabric-loader-0.16.14.jar",
                    "sha1": "",
                    "size": 0,
                    "path": "net/fabricmc/fabric-loader/0.16.14/fabric-loader-0.16.14.jar"
                }
            }
        },
        {
            "name": "net.fabricmc:intermediary:1.20.4",
            "downloads": {
                "artifact": {
                    "url": "https://maven.fabricmc.net/net/fabricmc/intermediary/1.20.4/intermediary-1.20.4.jar",
                    "sha1": "",
                    "size": 0,
                    "path": "net/fabricmc/intermediary/1.20.4/intermediary-1.20.4.jar"
                }
            }
        },
        {
            "name": "net.fabricmc:sponge-mixin:0.15.5+mixin.0.8.7",
            "downloads": {
                "artifact": {
                    "url": "",
                    "sha1": "",
                    "size": 0,
                    "path": "net/fabricmc/sponge-mixin/0.15.5+mixin.0.8.7/sponge-mixin-0.15.5+mixin.0.8.7.jar"
                }
            }
        }
    ]
}

with open(VERSION_JSON, "w", encoding="utf-8") as f:
    json.dump(FABRIC_JSON, f, ensure_ascii=False, indent=2)

print(f"已将版本JSON改为Fabric加载器!")
print(f"  mainClass: {FABRIC_JSON['mainClass']}")
print(f"  Fabric Loader: 0.16.14")
print(f"  Intermediary: 1.20.4")

fabric_loader_jar = os.path.join(MC_DIR, "libraries", "net", "fabricmc", "fabric-loader", "0.16.14", "fabric-loader-0.16.14.jar")
intermediary_jar = os.path.join(MC_DIR, "libraries", "net", "fabricmc", "intermediary", "1.20.4", "intermediary-1.20.4.jar")
print(f"\n关键库文件检查:")
print(f"  Fabric Loader: {'存在' if os.path.exists(fabric_loader_jar) else '缺失!'}")
print(f"  Intermediary: {'存在' if os.path.exists(intermediary_jar) else '缺失!'}")

if not os.path.exists(fabric_loader_jar):
    print("  需要下载Fabric Loader!")
if not os.path.exists(intermediary_jar):
    print("  需要下载Intermediary!")

print(f"\n现在可以用HMCL启动游戏了!")
print(f"  版本: {VERSION_NAME}")
print(f"  加载器: Fabric 0.16.14")
