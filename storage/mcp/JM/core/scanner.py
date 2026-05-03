from pathlib import Path
from typing import Any, Dict


def analyze_project(project_path: Path) -> Dict[str, Any]:
    result = {
        "path": str(project_path),
        "engine": "unknown",
        "assets": {},
        "convertible": [],
    }

    if (project_path / "Assets").exists() and (project_path / "ProjectSettings").exists():
        result["engine"] = "Unity"
        assets = project_path / "Assets"
        result["assets"] = {
            "scenes": len(list(assets.rglob("*.unity"))),
            "prefabs": len(list(assets.rglob("*.prefab"))),
            "materials": len(list(assets.rglob("*.mat"))),
            "scripts": len(list(assets.rglob("*.cs"))),
            "textures": len([f for f in assets.rglob("*") if f.suffix.lower() in (".png", ".jpg", ".tga", ".psd")]),
            "meshes": len([f for f in assets.rglob("*") if f.suffix.lower() in (".fbx", ".obj", ".gltf")]),
            "audio": len([f for f in assets.rglob("*") if f.suffix.lower() in (".wav", ".mp3", ".ogg")]),
        }
        result["convertible"] = ["godot", "ue5", "blender"]

    elif (project_path / "Content").exists() and list(project_path.glob("*.uproject")):
        result["engine"] = "UE"
        content = project_path / "Content"
        result["assets"] = {
            "uassets": len(list(content.rglob("*.uasset"))),
            "umaps": len(list(content.rglob("*.umap"))),
            "blueprints": len(list(content.rglob("*.uasset"))),
        }
        result["convertible"] = ["godot", "unity", "blender"]

    elif (project_path / "project.godot").exists() or (project_path / ".godot").exists():
        result["engine"] = "Godot"
        result["assets"] = {
            "scenes": len(list(project_path.rglob("*.tscn"))),
            "resources": len(list(project_path.rglob("*.tres"))),
            "scripts": len(list(project_path.rglob("*.gd"))),
        }
        result["convertible"] = ["ue5", "unity", "blender"]

    elif (project_path / "Assets").exists():
        result["engine"] = "Unity (partial)"
        assets = project_path / "Assets"
        result["assets"] = {
            "files": len(list(assets.rglob("*"))),
        }
        result["convertible"] = ["godot", "ue5"]

    else:
        ext_counts = {}
        for f in project_path.rglob("*") if project_path.is_dir() else [project_path]:
            if f.is_file():
                ext = f.suffix.lower()
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
        result["assets"] = {"by_extension": ext_counts}
        if ".fbx" in ext_counts or ".obj" in ext_counts or ".glb" in ext_counts:
            result["convertible"] = ["godot", "ue5"]

    return result
