import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None

_CONFIG_DIR = Path(__file__).resolve().parent.parent
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"

_SCAN_ROOTS = [
    Path("D:/rj"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
]

_SCAN_TARGETS = {
    "blender_path": "blender.exe",
    "godot_path": "Godot*.exe",
    "ue5_path": "UnrealEditor.exe",
}


def _scan_for_executables() -> Dict[str, str]:
    found: Dict[str, str] = {}
    for key, pattern in _SCAN_TARGETS.items():
        for root in _SCAN_ROOTS:
            if not root.exists():
                continue
            for match in root.rglob(pattern):
                found[key] = str(match)
                break
            if key in found:
                break
    return found


def _generate_default_config(found: Dict[str, str]) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "blender_path": found.get("blender_path", ""),
        "godot_path": found.get("godot_path", ""),
        "godot_project": "/python/Temp/VortexTest",
        "ue5_path": found.get("ue5_path", ""),
        "output_dir": "/python/Temp/Converted",
        "material_preset": "default_cyan_metallic",
        "bake_size": 512,
        "supported_formats": [
            ".fbx", ".obj", ".gltf", ".glb", ".dae", ".abc",
            ".usd", ".usda", ".usdc", ".blend", ".unity",
            ".prefab", ".mat", ".tscn", ".tres", ".gd",
            ".cs", ".uasset", ".umap",
        ],
    }
    return data


class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"Config has no attribute '{name}'")

    def get(self, name: str, default: Any = None) -> Any:
        return self._data.get(name, default)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        path = Path(config_path) if config_path else _CONFIG_FILE
        if path.exists():
            if yaml is None:
                raise ImportError("pyyaml is required to load config.yaml. Install with: pip install pyyaml")
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(data)

        found = _scan_for_executables()
        data = _generate_default_config(found)
        auto_path = _CONFIG_FILE
        auto_path.parent.mkdir(parents=True, exist_ok=True)
        if yaml is not None:
            with open(auto_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return cls(data)

    def reload(self) -> "Config":
        return Config.load()

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)
